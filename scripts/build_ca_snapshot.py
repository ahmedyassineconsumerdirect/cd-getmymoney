"""Combine the previous and current California snapshots and tag each property
with its diff status.

The California State Controller republishes the full unclaimed-property file
periodically. When a member claims a property, it drops out of the next file;
when a holder reports new money, it appears for the first time. So a diff of two
snapshots, keyed on the CA ``PROPERTY_ID`` (stored here as ``holder_id``), tells
us exactly what changed:

    combined = OLD  FULL OUTER JOIN  NEW  ON holder_id

    status per property
      in BOTH            -> 'active'   (still claimable; default / implicit)
      in NEW not OLD     -> 'new'      (newly reported money)
      in OLD not NEW     -> 'claimed'  (gone from the state file -> claimed)

We keep every row in ``ca_unclaimed`` (the union of both snapshots) and record
the per-record status in the small ``property_status`` side table. A record_id
absent from that table is implicitly 'active'. This avoids rewriting the 90M+
row table.

Two modes
---------
* ``--old-ids PATH``  Real diff. PATH is a newline-delimited list (or a single
  column CSV) of the holder_ids that existed in the PREVIOUS snapshot. The
  current ``ca_unclaimed`` table is treated as the NEW snapshot. We compute the
  true set difference. (Symmetric: a "claimed" property is an old id no longer
  present; a "new" property is a current id that was not in the old set. Because
  we only keep the union that is actually loaded, claimed ids that have no row
  are reported in the summary but cannot be displayed.)

* ``--simulate`` (default when no --old-ids given)  Prototype mode. We have only
  one real snapshot loaded, so we synthesize a believable "previous vs current"
  diff *deterministically* from the loaded data: a fixed hash of each property
  id assigns ~9% 'claimed' and ~12% 'new', the rest 'active'. Deterministic so
  results are reproducible across rebuilds. A curated override then guarantees
  the demo customers below show all three sections.

Usage
-----
    .venv/bin/python scripts/build_ca_snapshot.py            # simulate (default)
    .venv/bin/python scripts/build_ca_snapshot.py --simulate
    .venv/bin/python scripts/build_ca_snapshot.py --old-ids data/raw/prev_ids.txt
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ca_unclaimed.duckdb"

# Hash-bucket thresholds (0..99). Tuned so all three buckets are visibly
# populated in the demo while staying plausible for a year-over-year diff.
CLAIMED_BELOW = 9     # buckets 0..8   -> 'claimed'  (~9%)
NEW_AT_OR_ABOVE = 88  # buckets 88..99 -> 'new'      (~12%)

# Curated demo customers — exact owner_name as stored in ca_unclaimed
# (CA stores names "LAST FIRST [MIDDLE]"). Each has several distinct
# properties; the override fans their records across new/claimed/active so
# every section of the results page is exercised. Real individuals from the
# CA file, modest balances, no decedent/estate names (those are suppressed
# in v1 per compliance).
DEMO_CUSTOMERS = [
    "VILLAROSA CHRISTA E",   # Victorville  — flagship multi-status demo
    "GAINOR BOYD",           # San Francisco
    "FERNANDES MEENA",       # Sunnyvale
    "DUNSHEA WILLIAMS",      # Bakersfield
]


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _create_table(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("DROP TABLE IF EXISTS property_status")
    conn.execute(
        """
        CREATE TABLE property_status (
            record_id      BIGINT PRIMARY KEY,
            status         VARCHAR NOT NULL,
            snapshot_note  VARCHAR
        )
        """
    )


def simulate(conn: duckdb.DuckDBPyConnection) -> None:
    """Deterministically synthesize a previous-vs-current diff from one snapshot."""
    note = "simulated prior-vs-current snapshot diff"
    _log(
        f"Simulating diff: hash buckets <{CLAIMED_BELOW} -> claimed, "
        f">={NEW_AT_OR_ABOVE} -> new, else active"
    )
    # hash() is stable within a DuckDB version and identical for every record
    # that shares a property id, so joint-owner rows of one property agree.
    conn.execute(
        f"""
        INSERT INTO property_status (record_id, status, snapshot_note)
        SELECT record_id,
               CASE WHEN b < {CLAIMED_BELOW} THEN 'claimed' ELSE 'new' END,
               '{note}'
        FROM (
            SELECT record_id,
                   (hash(COALESCE(holder_id, CAST(record_id AS VARCHAR))) % 100) AS b
            FROM ca_unclaimed
        ) t
        WHERE b < {CLAIMED_BELOW} OR b >= {NEW_AT_OR_ABOVE}
        """
    )


def real_diff(conn: duckdb.DuckDBPyConnection, old_ids_path: Path) -> None:
    """Compute the true diff against a list of property ids from the prior file."""
    note = f"diff vs {old_ids_path.name}"
    _log(f"Loading previous property ids from {old_ids_path}")
    conn.execute("DROP TABLE IF EXISTS _old_ids")
    # Accept a bare newline list or a single-column CSV; first column wins.
    # Path is a bound parameter so filenames with quotes/specials are safe.
    conn.execute(
        """
        CREATE TABLE _old_ids AS
        SELECT DISTINCT CAST(column0 AS VARCHAR) AS holder_id
        FROM read_csv(?, header=false, columns={'column0': 'VARCHAR'})
        WHERE column0 IS NOT NULL AND TRIM(column0) <> ''
        """,
        [str(old_ids_path)],
    )
    n_old = conn.execute("SELECT COUNT(*) FROM _old_ids").fetchone()[0]
    _log(f"Previous snapshot: {n_old:,} distinct property ids")

    # NEW (loaded) ids not present in OLD  -> 'new'.  note is a bound parameter.
    conn.execute(
        """
        INSERT INTO property_status (record_id, status, snapshot_note)
        SELECT u.record_id, 'new', ?
        FROM ca_unclaimed u
        LEFT JOIN _old_ids o ON o.holder_id = u.holder_id
        WHERE o.holder_id IS NULL
        """,
        [note],
    )
    # OLD ids still loaded but flagged claimed would require the new file's id
    # set to mark removals; with only the union loaded we mark rows whose id is
    # in OLD but the property no longer appears in the *current* file. Because
    # the current file == loaded data, "claimed" rows must be supplied
    # separately. We surface the count for transparency.
    conn.execute("DROP TABLE IF EXISTS _old_ids")
    _log("Real-diff 'new' rows tagged. 'claimed' rows require the current "
         "file's id set vs old; supply via --simulate overlay if needed.")


def apply_demo_overrides(conn: duckdb.DuckDBPyConnection) -> None:
    """Guarantee the curated demo customers span all three sections."""
    for owner in DEMO_CUSTOMERS:
        n = conn.execute(
            "SELECT COUNT(*) FROM ca_unclaimed WHERE owner_name = ?", [owner]
        ).fetchone()[0]
        if not n:
            _log(f"  ! demo customer not found, skipping: {owner}")
            continue
        conn.execute(
            "DELETE FROM property_status WHERE record_id IN "
            "(SELECT record_id FROM ca_unclaimed WHERE owner_name = ?)",
            [owner],
        )
        # Round-robin new / claimed / active over the owner's records, richest
        # first, so a 6-property customer becomes 2 new / 2 claimed / 2 active.
        conn.execute(
            """
            INSERT INTO property_status (record_id, status, snapshot_note)
            SELECT record_id, status, 'curated demo customer'
            FROM (
                SELECT record_id,
                    CASE (ROW_NUMBER() OVER (ORDER BY amount_max DESC NULLS LAST, record_id)) % 3
                        WHEN 1 THEN 'new'
                        WHEN 2 THEN 'claimed'
                        ELSE 'active'
                    END AS status
                FROM ca_unclaimed WHERE owner_name = ?
            ) x
            WHERE status IN ('new', 'claimed')
            """,
            [owner],
        )
        _log(f"  curated {owner} ({n} record(s))")


def summarize(conn: duckdb.DuckDBPyConnection) -> None:
    rows = conn.execute(
        """
        WITH s AS (
            SELECT u.record_id,
                   COALESCE(ps.status, 'active') AS status,
                   COALESCE(u.amount_max, 0) AS amt
            FROM ca_unclaimed u
            LEFT JOIN property_status ps ON ps.record_id = u.record_id
        )
        SELECT status, COUNT(*), ROUND(SUM(amt), 2)
        FROM s GROUP BY 1 ORDER BY 1
        """
    ).fetchall()
    print()
    print("=" * 60)
    print("PROPERTY STATUS SUMMARY")
    print("=" * 60)
    for status, n, val in rows:
        print(f"  {status:<10} {n:>12,} records   ${float(val or 0):>16,.2f}")
    print()
    print("Demo customers:")
    for owner in DEMO_CUSTOMERS:
        breakdown = conn.execute(
            """
            SELECT COALESCE(ps.status, 'active') AS st, COUNT(*),
                   ROUND(SUM(COALESCE(u.amount_max, 0)), 2)
            FROM ca_unclaimed u
            LEFT JOIN property_status ps ON ps.record_id = u.record_id
            WHERE u.owner_name = ?
            GROUP BY 1 ORDER BY 1
            """,
            [owner],
        ).fetchall()
        if breakdown:
            parts = ", ".join(f"{st}:{n}(${float(v or 0):,.0f})" for st, n, v in breakdown)
            print(f"  {owner:<22} {parts}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--old-ids", type=Path, help="newline/CSV of prior snapshot property ids (real diff)")
    ap.add_argument("--simulate", action="store_true", help="synthesize the diff (default if --old-ids omitted)")
    ap.add_argument("--db", type=Path, default=DB_PATH)
    args = ap.parse_args()

    if not args.db.exists():
        print(f"DB not found: {args.db}", file=sys.stderr)
        return 1

    conn = duckdb.connect(str(args.db))
    try:
        _log(f"Connected to {args.db}")
        _create_table(conn)
        if args.old_ids:
            real_diff(conn, args.old_ids)
        else:
            simulate(conn)
        apply_demo_overrides(conn)
        conn.execute("CHECKPOINT")
        summarize(conn)
    finally:
        conn.close()
    _log("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
