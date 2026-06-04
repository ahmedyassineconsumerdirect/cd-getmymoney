"""Match service interface + matcher implementations.

Production swaps DemoFuzzyMatcher for Consumer Direct's existing
data-broker matching service by implementing the MatchService protocol.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import duckdb

from app.ingest import normalize_owner_name


@dataclass
class Match:
    record_id: int
    holder_name: str
    owner_name: str
    last_known_address: str | None
    last_known_city: str | None
    last_known_state: str | None
    last_known_zip: str | None
    amount_min: float | None
    amount_max: float | None
    property_type: str | None
    reported_date: date | None
    # Display fields populated by the matcher post-construction. They are
    # the template-ready strings derived from raw columns above. See
    # docs/handoff/2026-04-28-match-result-row.md §11.
    icon_key: str = "file-text"
    property_type_display: str = ""
    source_display: str = ""
    address_display: str = ""
    amount_display: str = ""
    has_range: bool = False
    claim_url: str = ""
    # Snapshot-diff status: 'active' (in both snapshots, claimable),
    # 'new' (newly reported), 'claimed' (gone from latest state file).
    status: str = "active"
    status_label: str = "Potential match"
    status_badge_class: str = ""
    status_dot: str = ""
    claimable: bool = True
    relevance: int = 0


class MatchService(Protocol):
    def find_matches(
        self,
        first_name: str = "",
        last_name: str = "",
        city: str | None = None,
        state: str | None = None,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]: ...


def _tokenize_query(*parts: str) -> list[str]:
    """Split inputs into normalized tokens — every word must appear in match."""
    tokens: list[str] = []
    for p in parts:
        if not p:
            continue
        normalized = normalize_owner_name(p)
        for tok in normalized.split():
            if len(tok) >= 2 and tok not in tokens:
                tokens.append(tok)
    return tokens


def _name_parts(*parts: str) -> list[str]:
    """All normalized name tokens INCLUDING single-letter middle initials,
    used for relevance ranking (the filter still uses >=2-char tokens)."""
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        for tok in normalize_owner_name(p).split():
            if tok and tok not in out:
                out.append(tok)
    return out


def relevance_score(owner_normalized: str, q_parts: list[str], last_norm: str) -> int:
    """How closely a stored owner name matches the searched name — higher is
    closer. Mirrors how state portals rank by name, not by dollar amount:
    exact same name parts first, then partial overlaps, with extra/different
    given names (e.g. a co-owner's name) pushed down."""
    cand = owner_normalized.split()
    if not cand:
        return -999
    cset, qset = set(cand), set(q_parts)
    inter = qset & cset
    score = len(inter) * 10 - len(qset - cset) * 8 - len(cset - qset) * 5
    if cset == qset:                 # exact same set of name parts (any order)
        score += 60
        if cand == q_parts:          # exact same order too
            score += 15
    if last_norm and cand[0] == last_norm:  # canonical "LAST FIRST ..." form
        score += 6
    return score


class DemoFuzzyMatcher:
    """Token-substring matcher: every input token must appear as a substring
    of the owner_name. Demonstrates fuzzy/contains matching.

    Production swaps this with Consumer Direct's data-broker matcher
    (Soundex + Metaphone + Levenshtein etc).

    Ranking: exact name = highest, starts-with = next, all-tokens-substring
    = third tier. Within a tier, ORDER BY amount_max DESC.
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def find_matches(
        self,
        first_name: str = "",
        last_name: str = "",
        city: str | None = None,
        state: str | None = None,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]:
        tokens = _tokenize_query(first_name, last_name)
        if not tokens:
            return []

        # Each token must appear as a substring (case-insensitive after
        # normalize). A leading-wildcard LIKE can't use the owner-name index, so
        # this is a full scan — but on warm cache it's ~0.2s over 90M rows, and
        # crucially it preserves full recall (finds joint/co-owner rows such as
        # "PHILIP AND JUDY EVANS" where the surname is not the leading token).
        # The first query after a cold start pages the column into cache (slow
        # once); _warm_cache() in app.main pre-warms it on startup.
        where_clauses = " AND ".join(["owner_name_normalized LIKE ?"] * len(tokens))
        like_params = [f"%{t}%" for t in tokens]

        extra_clause = ""
        params_extra: list = []
        if city:
            # Collapse interior whitespace on BOTH sides so "San  Francisco"
            # (double space in the source) still matches "San Francisco".
            extra_clause += " AND REGEXP_REPLACE(UPPER(TRIM(last_known_city)), '\\s+', ' ', 'g') = ?"
            params_extra.append(normalize_owner_name(city))
        if state:
            extra_clause += " AND last_known_state = ?"
            params_extra.append(state.upper())

        # Tier 1: exact full-name match
        # Tier 2: starts-with for the first token
        # Tier 3: contains-all-tokens
        full = " ".join(tokens)
        first_tok = tokens[0]

        # Ranking inputs (include middle initials). The final order is by name
        # closeness (see relevance_score), like the state portal — not by amount.
        q_parts = _name_parts(first_name, last_name)
        last_toks = normalize_owner_name(last_name).split()
        last_norm = last_toks[-1] if last_toks else ""

        # Fetch a generous candidate set biased toward tight names (shorter
        # owner strings contain fewer extra tokens), then re-rank in Python.
        sql = f"""
            SELECT record_id, holder_name, owner_name,
                   last_known_address, last_known_city,
                   last_known_state, last_known_zip,
                   amount_min, amount_max,
                   property_type, reported_date,
                   CASE
                       WHEN owner_name_normalized = ? THEN 1
                       WHEN owner_name_normalized LIKE ? THEN 2
                       ELSE 3
                   END AS match_tier
            FROM ca_unclaimed
            WHERE {where_clauses}{extra_clause}
            ORDER BY match_tier ASC, LENGTH(owner_name_normalized) ASC,
                     COALESCE(amount_max, 0) DESC
            LIMIT 250
        """
        params = [full, f"{first_tok}%", *like_params, *params_extra]
        rows = self.conn.execute(sql, params).fetchall()

        # Resolve snapshot-diff status in a second, index-driven lookup keyed on
        # the (<=100) matched record ids — far cheaper than joining the 19M-row
        # property_status table against a full-table LIKE scan. Tolerate a
        # missing table (fresh DB / pre-snapshot) by defaulting to 'active'.
        record_ids = [r[0] for r in rows]
        status_map: dict[int, str] = {}
        if record_ids:
            placeholders = ",".join("?" * len(record_ids))
            try:
                for rid, st in self.conn.execute(
                    f"SELECT record_id, status FROM property_status WHERE record_id IN ({placeholders})",
                    record_ids,
                ).fetchall():
                    status_map[rid] = st
            except Exception:
                pass

        # Columns 0..10 map positionally to the Match required fields; the last
        # column is match_tier (ranking only — not stored on Match).
        from app import presentation as _p
        results: list[Match] = []
        for r in rows:
            m = Match(*r[:11])
            status = status_map.get(r[0], "active")
            if status not in ("new", "active", "claimed"):
                status = "active"
            disp = _p.property_type_display(m.property_type)
            m.icon_key = disp["icon_key"]
            m.property_type_display = disp["label"]
            m.source_display = _p.source_display(m.last_known_state)
            m.address_display = _p.address_display(
                m.last_known_address, m.last_known_city,
                m.last_known_state, m.last_known_zip,
            )
            m.amount_display, m.has_range = _p.amount_display(m.amount_min, m.amount_max)
            m.claim_url = _p.claim_url(m.last_known_state)
            sd = _p.status_display(status)
            m.status = status
            m.status_label = sd["label"]
            m.status_badge_class = sd["badge_class"]
            m.status_dot = sd["dot"]
            m.claimable = sd["claimable"]
            m.relevance = relevance_score(normalize_owner_name(m.owner_name), q_parts, last_norm)
            results.append(m)

        # Order by name closeness first (like the state portal), then by zip
        # code (records without a zip sort last), amount as a final tiebreak.
        def _sort_key(m: "Match"):
            z = (m.last_known_zip or "").strip()
            return (-m.relevance, z == "", z, -(m.amount_max or 0))

        results.sort(key=_sort_key)
        return results[:100]


# Backward-compat alias kept so legacy imports don't break.
DemoExactMatcher = DemoFuzzyMatcher
