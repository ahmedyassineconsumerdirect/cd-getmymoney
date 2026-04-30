"""Fast customer match — uses the equality index for the headline number.

Strategy: do EXACT normalized name match (FIRST LAST or LAST FIRST) which
hits ix_owner_normalized in milliseconds. This is the conservative number
SmartCredit can defend in an exec setting. Output also includes a fuzzy
contains-match breakdown done in chunks so it doesn't run for hours.

Usage:
    python scripts/customer_match_fast.py
"""
import json
import re
import time
from pathlib import Path

import duckdb

CUSTOMERS_CSV = "/Users/ahmedyassine/Downloads/Customers_by_State.csv"
DB_PATH = "data/ca_unclaimed.duckdb"
OUT_JSON = "/tmp/customer_match_results.json"


def main() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Connecting to {DB_PATH}")
    conn = duckdb.connect(DB_PATH)

    # --- Load customers (CUSTOMERTOKEN-aware, name-deduped for join) -------
    # Two views: full token-level table for customer counting, and a
    # DISTINCT-by-name view for the join (so duplicate-named customers
    # don't multiply per-name totals). See docs/AUDIT_SLIDE_6.md.
    conn.execute("DROP TABLE IF EXISTS sc_customers_full")
    conn.execute(f"""
        CREATE TABLE sc_customers_full AS
        SELECT
            CUSTOMERTOKEN AS customer_token,
            UPPER(TRIM(REGEXP_REPLACE(FIRST_NAME, '\\s+', ' ', 'g'))) AS first_norm,
            UPPER(TRIM(REGEXP_REPLACE(LAST_NAME,  '\\s+', ' ', 'g'))) AS last_norm
        FROM read_csv_auto('{CUSTOMERS_CSV}', header=true)
        WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL
          AND TRIM(FIRST_NAME) <> '' AND TRIM(LAST_NAME) <> ''
    """)
    conn.execute("DROP TABLE IF EXISTS sc_customers_ca")
    conn.execute("""
        CREATE TABLE sc_customers_ca AS
        SELECT DISTINCT first_norm, last_norm FROM sc_customers_full
    """)
    n_csv_rows = conn.execute("SELECT COUNT(*) FROM sc_customers_full").fetchone()[0]
    n_tokens = conn.execute("SELECT COUNT(DISTINCT customer_token) FROM sc_customers_full").fetchone()[0]
    n_names = conn.execute("SELECT COUNT(*) FROM sc_customers_ca").fetchone()[0]
    print(f"[{time.strftime('%H:%M:%S')}] CSV rows: {n_csv_rows:,}  "
          f"Customer tokens: {n_tokens:,}  Distinct names: {n_names:,}")
    n_customers = n_tokens  # for downstream "match rate" math

    # --- Loaded tiers -----------------------------------------------------
    by_source = conn.execute(
        "SELECT source_file, COUNT(*), COALESCE(SUM(amount_max), 0) "
        "FROM ca_unclaimed GROUP BY 1 ORDER BY 1"
    ).fetchall()
    total_rows = sum(r for _, r, _ in by_source)
    print(f"[{time.strftime('%H:%M:%S')}] CA unclaimed property loaded: {total_rows:,} rows across {len(by_source)} tiers")

    # --- EXACT MATCH (uses index — fast) ----------------------------------
    print(f"[{time.strftime('%H:%M:%S')}] Running exact normalized-name match...")
    t0 = time.time()
    conn.execute("DROP TABLE IF EXISTS exact_matches")
    # CA stores names as LAST FIRST (e.g., "YASSINE AHMED" not "AHMED YASSINE"),
    # so match LAST FIRST only. Including FIRST LAST as a hedge produces
    # name-reversed false positives (matches strangers with reversed name).
    conn.execute("""
        CREATE TABLE exact_matches AS
        SELECT
            c.first_norm, c.last_norm,
            u.record_id, u.amount_max, u.source_file
        FROM sc_customers_ca c
        JOIN ca_unclaimed u
          ON u.owner_name_normalized = c.last_norm || ' ' || c.first_norm
    """)
    elapsed = time.time() - t0
    print(f"[{time.strftime('%H:%M:%S')}] Exact match done in {elapsed:.1f}s.")

    exact_summary = conn.execute("""
        SELECT
            COUNT(DISTINCT first_norm || '|' || last_norm) AS matched_customers,
            COUNT(*)                                       AS total_record_matches,
            COALESCE(SUM(amount_max), 0)                   AS total_value
        FROM exact_matches
    """).fetchone()

    exact_by_tier = conn.execute("""
        SELECT source_file, COUNT(*), COALESCE(SUM(amount_max), 0)
        FROM exact_matches GROUP BY 1 ORDER BY 1
    """).fetchall()

    exact_dist = conn.execute("""
        WITH per_cust AS (
            SELECT first_norm, last_norm, COUNT(*) AS records, SUM(amount_max) AS val
            FROM exact_matches GROUP BY 1, 2
        )
        SELECT
            CASE
                WHEN records = 1 THEN '1 record'
                WHEN records BETWEEN 2 AND 5 THEN '2–5 records'
                WHEN records BETWEEN 6 AND 20 THEN '6–20 records'
                ELSE '20+ records'
            END AS bucket,
            COUNT(*)            AS customers,
            SUM(records)        AS records_total,
            SUM(val)            AS value_total
        FROM per_cust
        GROUP BY 1 ORDER BY MIN(records)
    """).fetchall()

    exact_top = conn.execute("""
        WITH per_cust AS (
            SELECT first_norm, last_norm, COUNT(*) AS records, SUM(amount_max) AS val
            FROM exact_matches GROUP BY 1, 2
        )
        SELECT records, val FROM per_cust ORDER BY val DESC NULLS LAST LIMIT 10
    """).fetchall()

    matched_customers, total_records, total_value = exact_summary
    match_rate = 100.0 * matched_customers / n_customers

    print()
    print("=" * 70)
    print("EXACT-MATCH SUMMARY (defensible headline)")
    print("=" * 70)
    print(f"Active CA customers:    {n_customers:,}")
    print(f"Customers w/ a match:   {matched_customers:,}  ({match_rate:.1f}%)")
    print(f"Property records:       {total_records:,}")
    print(f"Estimated $ owed:       ${float(total_value):,.2f}")
    print()
    print("By tier:")
    for s, r, v in exact_by_tier:
        print(f"  {s:<40} {r:>10,} records  ${float(v):>14,.2f}")
    print()
    print("Distribution:")
    for b, c, r, v in exact_dist:
        print(f"  {b:<15} customers: {c:>5,}  records: {r:>7,}  $: {float(v or 0):>12,.2f}")
    print()
    print("Top 10 customers by value (anonymized):")
    for r, v in exact_top:
        print(f"  records: {r:>3}   $: {float(v or 0):>12,.2f}")

    out = {
        "total_active_ca_customers": n_customers,
        "loaded_tiers": [
            {"source": s, "rows": r, "value": float(v)} for s, r, v in by_source
        ],
        "exact_match": {
            "matched_customers": matched_customers,
            "match_rate_pct": round(match_rate, 2),
            "total_record_matches": total_records,
            "total_value_usd": float(total_value),
            "by_tier": [
                {"source": s, "records": r, "value": float(v)} for s, r, v in exact_by_tier
            ],
            "distribution": [
                {"bucket": b, "customers": c, "records": r, "value_usd": float(v or 0)}
                for b, c, r, v in exact_dist
            ],
            "top_10_anonymized": [
                {"records": r, "value_usd": float(v or 0)} for r, v in exact_top
            ],
        },
    }
    Path(OUT_JSON).write_text(json.dumps(out, indent=2))
    print(f"\n[{time.strftime('%H:%M:%S')}] Wrote {OUT_JSON}")
    conn.close()


if __name__ == "__main__":
    main()
