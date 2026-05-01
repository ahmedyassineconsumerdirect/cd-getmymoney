"""Customer match with NAME + CITY filter.

Same methodology as customer_match_fast.py, but adds an equality
join on city to cut common-name false positives. CA's
last_known_city column is uppercase-normalized; SmartCredit's
CUSTOMER_ADDRESS_CITY is already uppercase in the source file.

Usage:
    python scripts/customer_match_with_city.py
"""
import json
import time
from pathlib import Path

import duckdb

CUSTOMERS_CSV = "/Users/ahmedyassine/Downloads/Customers_by_State.csv"
DB_PATH = "/tmp/ca_unclaimed.duckdb"  # read-only copy (server holds prod lock)
OUT_JSON = "/tmp/customer_match_city_results.json"


def main() -> None:
    print(f"[{time.strftime('%H:%M:%S')}] Connecting to {DB_PATH}")
    conn = duckdb.connect(DB_PATH, read_only=True)

    # --- Load customers (token-aware, name+city dedupe for join) ----------
    conn.execute("DROP TABLE IF EXISTS sc_customers_full")
    conn.execute(f"""
        CREATE TEMP TABLE sc_customers_full AS
        SELECT
            CUSTOMERTOKEN AS customer_token,
            UPPER(TRIM(REGEXP_REPLACE(FIRST_NAME, '\\s+', ' ', 'g'))) AS first_norm,
            UPPER(TRIM(REGEXP_REPLACE(LAST_NAME,  '\\s+', ' ', 'g'))) AS last_norm,
            UPPER(TRIM(REGEXP_REPLACE(CUSTOMER_ADDRESS_CITY, '\\s+', ' ', 'g'))) AS city_norm
        FROM read_csv_auto('{CUSTOMERS_CSV}', header=true)
        WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL
          AND TRIM(FIRST_NAME) <> '' AND TRIM(LAST_NAME) <> ''
          AND CUSTOMER_ADDRESS_CITY IS NOT NULL AND TRIM(CUSTOMER_ADDRESS_CITY) <> ''
    """)
    conn.execute("DROP TABLE IF EXISTS sc_customers_namecity")
    conn.execute("""
        CREATE TEMP TABLE sc_customers_namecity AS
        SELECT DISTINCT first_norm, last_norm, city_norm FROM sc_customers_full
    """)
    n_csv_rows = conn.execute("SELECT COUNT(*) FROM sc_customers_full").fetchone()[0]
    n_tokens = conn.execute("SELECT COUNT(DISTINCT customer_token) FROM sc_customers_full").fetchone()[0]
    n_keys = conn.execute("SELECT COUNT(*) FROM sc_customers_namecity").fetchone()[0]
    print(f"[{time.strftime('%H:%M:%S')}] CSV rows w/ city: {n_csv_rows:,}  "
          f"customer tokens: {n_tokens:,}  distinct (name,city) keys: {n_keys:,}")

    # --- Match: LAST FIRST + city ----------------------------------------
    # Index ix_owner_normalized handles the name equality; city equality
    # is an extra filter on the matched rows.
    print(f"[{time.strftime('%H:%M:%S')}] Running NAME + CITY match...")
    t0 = time.time()
    conn.execute("DROP TABLE IF EXISTS namecity_matches")
    conn.execute("""
        CREATE TEMP TABLE namecity_matches AS
        SELECT
            c.first_norm, c.last_norm, c.city_norm,
            u.record_id, u.amount_max, u.source_file
        FROM sc_customers_namecity c
        JOIN ca_unclaimed u
          ON u.owner_name_normalized = c.last_norm || ' ' || c.first_norm
         AND UPPER(TRIM(u.last_known_city)) = c.city_norm
    """)
    elapsed = time.time() - t0
    print(f"[{time.strftime('%H:%M:%S')}] Match done in {elapsed:.1f}s.")

    # --- Headline numbers -------------------------------------------------
    matched_names, total_records, total_value = conn.execute("""
        SELECT
            COUNT(DISTINCT first_norm || '|' || last_norm || '|' || city_norm),
            COUNT(*),
            COALESCE(SUM(amount_max), 0)
        FROM namecity_matches
    """).fetchone()

    matched_tokens = conn.execute("""
        SELECT COUNT(DISTINCT f.customer_token)
        FROM sc_customers_full f
        JOIN namecity_matches m
          ON m.first_norm = f.first_norm
         AND m.last_norm  = f.last_norm
         AND m.city_norm  = f.city_norm
    """).fetchone()[0]

    match_rate = 100.0 * matched_tokens / n_tokens

    # --- Bucket: records returned per (name+city) ------------------------
    dist = conn.execute("""
        WITH per_key AS (
            SELECT first_norm, last_norm, city_norm,
                   COUNT(*) AS records, SUM(amount_max) AS val
            FROM namecity_matches GROUP BY 1,2,3
        ),
        per_key_tokens AS (
            SELECT pk.*,
                   (SELECT COUNT(DISTINCT f.customer_token)
                      FROM sc_customers_full f
                     WHERE f.first_norm = pk.first_norm
                       AND f.last_norm  = pk.last_norm
                       AND f.city_norm  = pk.city_norm) AS tokens
            FROM per_key pk
        )
        SELECT
            CASE
                WHEN records = 1 THEN '1 record'
                WHEN records BETWEEN 2 AND 5 THEN '2-5 records'
                WHEN records BETWEEN 6 AND 20 THEN '6-20 records'
                ELSE '20+ records'
            END AS bucket,
            SUM(tokens)        AS customers,
            SUM(val)           AS bucket_value
        FROM per_key_tokens
        GROUP BY 1
        ORDER BY MIN(records)
    """).fetchall()

    # --- Bucket: total $ owed per (name+city) ----------------------------
    owed = conn.execute("""
        WITH per_key AS (
            SELECT first_norm, last_norm, city_norm,
                   SUM(amount_max) AS total
            FROM namecity_matches GROUP BY 1,2,3
        ),
        per_key_tokens AS (
            SELECT pk.*,
                   (SELECT COUNT(DISTINCT f.customer_token)
                      FROM sc_customers_full f
                     WHERE f.first_norm = pk.first_norm
                       AND f.last_norm  = pk.last_norm
                       AND f.city_norm  = pk.city_norm) AS tokens
            FROM per_key pk
        )
        SELECT
            CASE
                WHEN total < 10  THEN '$0-$9.99'
                WHEN total < 100 THEN '$10-$99.99'
                WHEN total < 500 THEN '$100-$499.99'
                ELSE '$500+'
            END AS bucket,
            SUM(tokens) AS customers,
            SUM(total)  AS bucket_total
        FROM per_key_tokens
        GROUP BY 1
        ORDER BY MIN(total)
    """).fetchall()

    print()
    print("=" * 70)
    print("NAME + CITY MATCH SUMMARY")
    print("=" * 70)
    print(f"Active CA customers (with city):  {n_tokens:,}")
    print(f"Customers w/ a name+city match:   {matched_tokens:,}  ({match_rate:.1f}%)")
    print(f"Distinct (name,city) keys hit:    {matched_names:,}")
    print(f"Property records:                 {total_records:,}")
    print(f"Estimated $ owed:                 ${float(total_value):,.2f}")
    print()
    print("Records-returned distribution:")
    for b, custs, val in dist:
        avg = float(val) / int(custs) if custs else 0
        print(f"  {b:<14} customers: {int(custs):>6,}   $: {float(val):>14,.2f}  ${avg:>10,.2f}/cust")
    print()
    print("Customers by total owed:")
    for b, custs, total in owed:
        avg = float(total) / int(custs) if custs else 0
        print(f"  {b:<14} customers: {int(custs):>6,}   $: {float(total):>14,.2f}  ${avg:>10,.2f}/cust")

    out = {
        "active_ca_customers_with_city": n_tokens,
        "matched_customers": matched_tokens,
        "match_rate_pct": round(match_rate, 2),
        "distinct_namecity_keys_matched": matched_names,
        "total_record_matches": total_records,
        "total_value_usd": float(total_value),
        "records_distribution": [
            {"bucket": b, "customers": int(c), "value_usd": float(v)} for b, c, v in dist
        ],
        "owed_buckets": [
            {"bucket": b, "customers": int(c), "value_usd": float(v)} for b, c, v in owed
        ],
    }
    Path(OUT_JSON).write_text(json.dumps(out, indent=2))
    print(f"\n[{time.strftime('%H:%M:%S')}] Wrote {OUT_JSON}")
    conn.close()


if __name__ == "__main__":
    main()
