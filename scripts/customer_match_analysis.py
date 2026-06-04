"""Match SmartCredit's active CA customers against loaded CA unclaimed property.

Uses the same token-substring matcher logic as the prototype (DemoFuzzyMatcher).
Reports total matched customers, records, and dollar value owed.

Output: /tmp/customer_match_results.json + console summary.

Usage:
    python scripts/customer_match_analysis.py
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

import duckdb

CUSTOMERS_CSV = "/Users/ahmedyassine/Downloads/Active_SC_Customers_CA.csv"
DB_PATH = "data/ca_unclaimed.duckdb"
OUT_JSON = "/tmp/customer_match_results.json"


def normalize(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().upper()


def main() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Loading customers from {CUSTOMERS_CSV}")
    conn = duckdb.connect(DB_PATH)

    # Surface what we have loaded
    by_source = conn.execute(
        "SELECT source_file, COUNT(*), COALESCE(SUM(amount_max), 0) "
        "FROM ca_unclaimed GROUP BY 1 ORDER BY 1"
    ).fetchall()
    print("\nLoaded CA unclaimed property tiers:")
    for src, cnt, val in by_source:
        print(f"  {src:<35} {cnt:>12,} rows  ${float(val):>15,.2f}")

    # Load customer CSV into DuckDB and normalize names
    conn.execute("DROP TABLE IF EXISTS sc_customers_ca")
    conn.execute(f"""
        CREATE TABLE sc_customers_ca AS
        SELECT
            FIRST_NAME       AS first_name,
            LAST_NAME        AS last_name,
            MIDDLE_NAME      AS middle_name,
            CUSTOMER_ADDRESS_CITY    AS city,
            CUSTOMER_ADDRESS_ZIPCODE AS zip,
            CAST(CUSTOMERS AS BIGINT) AS customers,
            UPPER(TRIM(REGEXP_REPLACE(FIRST_NAME, '\\s+', ' ', 'g'))) AS first_norm,
            UPPER(TRIM(REGEXP_REPLACE(LAST_NAME, '\\s+', ' ', 'g')))  AS last_norm
        FROM read_csv_auto('{CUSTOMERS_CSV}', header=true)
        WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL
    """)

    total_customers = conn.execute(
        "SELECT COUNT(*), SUM(customers) FROM sc_customers_ca"
    ).fetchone()
    print(f"\n[{time.strftime('%H:%M:%S')}] Customer rows: {total_customers[0]:,} "
          f"(sum of CUSTOMERS column: {int(total_customers[1] or 0):,})")

    # MATCH: token-substring on owner_name_normalized
    # Same logic as DemoFuzzyMatcher: each token must appear in owner_name_normalized.
    # We use first_norm AND last_norm both as substrings (case-insensitive after normalize).
    print(f"[{time.strftime('%H:%M:%S')}] Running substring match (this may take a few minutes)...")
    t0 = time.time()
    matches_sql = """
        WITH customer_matches AS (
            SELECT
                c.first_name,
                c.last_name,
                c.first_norm,
                c.last_norm,
                u.record_id,
                u.amount_max,
                u.source_file
            FROM sc_customers_ca c
            JOIN ca_unclaimed u
              ON u.owner_name_normalized LIKE '%' || c.first_norm || '%'
             AND u.owner_name_normalized LIKE '%' || c.last_norm  || '%'
        )
        SELECT * FROM customer_matches
    """
    # Cache as table
    conn.execute("DROP TABLE IF EXISTS match_results")
    conn.execute(f"CREATE TABLE match_results AS {matches_sql}")
    elapsed = time.time() - t0
    print(f"[{time.strftime('%H:%M:%S')}] Match join finished in {elapsed:.0f}s.")

    # Headline numbers
    summary = conn.execute(
        """
        SELECT
            COUNT(DISTINCT first_norm || '|' || last_norm) AS matched_customers,
            COUNT(*)                                       AS total_record_matches,
            COALESCE(SUM(amount_max), 0)                   AS total_value
        FROM match_results
        """
    ).fetchone()
    matched_customers, total_record_matches, total_value = summary

    # Per-tier breakdown
    by_tier = conn.execute(
        """
        SELECT source_file, COUNT(*) AS records, COALESCE(SUM(amount_max), 0) AS value
        FROM match_results GROUP BY 1 ORDER BY 1
        """
    ).fetchall()

    # Per-customer aggregates (top 10 by value)
    top_customers = conn.execute(
        """
        SELECT
            ANY_VALUE(first_name) AS first_name,
            ANY_VALUE(last_name)  AS last_name,
            COUNT(record_id)      AS records,
            SUM(amount_max)       AS total
        FROM match_results
        GROUP BY first_norm, last_norm
        ORDER BY total DESC NULLS LAST
        LIMIT 10
        """
    ).fetchall()

    # Distribution: how many records per customer
    distribution = conn.execute(
        """
        WITH per_cust AS (
            SELECT first_norm, last_norm, COUNT(*) AS records
            FROM match_results GROUP BY 1, 2
        )
        SELECT
            CASE
                WHEN records = 1 THEN '1 record'
                WHEN records BETWEEN 2 AND 5 THEN '2-5 records'
                WHEN records BETWEEN 6 AND 20 THEN '6-20 records'
                ELSE '20+ records'
            END AS bucket,
            COUNT(*) AS customers,
            SUM(records) AS total_records
        FROM per_cust
        GROUP BY 1 ORDER BY MIN(records)
        """
    ).fetchall()

    # Caveat: many false positives possible from token-substring
    # (e.g., "JOHN SMITH" customer matches "MARTHA JOHN SMITHSON-TRUST"). For
    # an exec-facing number we report a more conservative figure as well:
    # exact normalized name match (FIRST LAST or LAST FIRST).
    exact_summary = conn.execute(
        """
        WITH cust AS (
            SELECT
                first_norm || ' ' || last_norm AS fl,
                last_norm  || ' ' || first_norm AS lf
            FROM sc_customers_ca
        ),
        joined AS (
            SELECT u.record_id, u.amount_max
            FROM cust c
            JOIN ca_unclaimed u
              ON u.owner_name_normalized = c.fl
              OR u.owner_name_normalized = c.lf
        )
        SELECT COUNT(*), COALESCE(SUM(amount_max), 0) FROM joined
        """
    ).fetchone()

    out = {
        "total_active_ca_customers": total_customers[0],
        "loaded_tiers": [
            {"source": s, "rows": r, "value": float(v)} for s, r, v in by_source
        ],
        "missing_tier": "03_From_100_To_Below_500.zip — NOT LOADED",
        "fuzzy_substring_match": {
            "matched_customers": matched_customers,
            "match_rate_pct": round(100.0 * matched_customers / total_customers[0], 2),
            "total_record_matches": total_record_matches,
            "total_value_usd": float(total_value),
            "by_tier": [
                {"source": s, "records": r, "value": float(v)} for s, r, v in by_tier
            ],
        },
        "exact_match_only": {
            "total_record_matches": exact_summary[0],
            "total_value_usd": float(exact_summary[1]),
        },
        "top_10_customers_by_value": [
            {"first_name": fn, "last_name": ln, "records": r, "total": float(t or 0)}
            for fn, ln, r, t in top_customers
        ],
        "match_distribution": [
            {"bucket": b, "customers": c, "total_records": tr}
            for b, c, tr in distribution
        ],
    }

    Path(OUT_JSON).write_text(json.dumps(out, indent=2))
    print(f"\n[{time.strftime('%H:%M:%S')}] Wrote {OUT_JSON}")

    # Console summary
    print()
    print("=" * 70)
    print("CUSTOMER MATCH SUMMARY")
    print("=" * 70)
    print(f"Active CA SmartCredit customers: {total_customers[0]:,}")
    print(f"Tiers loaded:                    01, 02, 04 (tier 03 NOT LOADED)")
    print()
    print("FUZZY (token substring — matches anywhere in owner_name):")
    print(f"  Matched customers:    {matched_customers:,} "
          f"({100.0*matched_customers/total_customers[0]:.1f}% of base)")
    print(f"  Property records:     {total_record_matches:,}")
    print(f"  Estimated $ value:    ${float(total_value):,.2f}")
    print()
    print("EXACT (normalized FIRST LAST or LAST FIRST only — conservative):")
    print(f"  Property records:     {exact_summary[0]:,}")
    print(f"  Estimated $ value:    ${float(exact_summary[1]):,.2f}")
    print()
    print("BY TIER (fuzzy):")
    for s, r, v in by_tier:
        print(f"  {s:<40} {r:>10,} records  ${float(v):>14,.2f}")
    print()
    print("MATCH DISTRIBUTION:")
    for b, c, tr in distribution:
        print(f"  {b:<15} customers: {c:>6,}   total records: {tr:>10,}")
    print()
    print("TOP 10 by total value:")
    for fn, ln, r, t in top_customers:
        print(f"  {fn} {ln}: {r} records, ${float(t or 0):,.2f}")

    conn.close()


if __name__ == "__main__":
    main()
