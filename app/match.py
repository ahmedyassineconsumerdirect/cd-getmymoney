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


class MatchService(Protocol):
    def find_matches(
        self,
        first_name: str = "",
        last_name: str = "",
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
        state: str | None = None,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]:
        tokens = _tokenize_query(first_name, last_name)
        if not tokens:
            return []

        # Each token must appear as a substring (case-insensitive after normalize).
        where_clauses = " AND ".join(["owner_name_normalized LIKE ?"] * len(tokens))
        like_params = [f"%{t}%" for t in tokens]

        # Optional state filter — restrict to the chosen state (e.g. "CA")
        state_clause = ""
        params_extra: list = []
        if state:
            state_clause = " AND last_known_state = ?"
            params_extra.append(state.upper())

        # Tier 1: exact full-name match
        # Tier 2: starts-with for the first token
        # Tier 3: contains-all-tokens
        full = " ".join(tokens)
        first_tok = tokens[0]

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
            WHERE {where_clauses}{state_clause}
            ORDER BY match_tier ASC, COALESCE(amount_max, 0) DESC
            LIMIT 100
        """
        params = [full, f"{first_tok}%", *like_params, *params_extra]
        rows = self.conn.execute(sql, params).fetchall()
        # Strip the match_tier column before constructing Match
        from app import presentation as _p
        results: list[Match] = []
        for r in rows:
            m = Match(*r[:-1])
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
            results.append(m)
        return results


# Backward-compat alias kept so legacy imports don't break.
DemoExactMatcher = DemoFuzzyMatcher
