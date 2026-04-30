# Audit instructions — Slide 6 customer-match statistics

> **2026-04-30 update — input swapped to Customers_by_State.csv (now contains CUSTOMERTOKEN):**
> Customer counts on the slide are now real-customer counts (distinct customertoken), not distinct-name counts. The match logic still operates at the name level (we don't know how to disambiguate same-named customers from CA's name-only records), but for reporting we count actual customers via customertoken.
>
> **All four corrections applied since v1:**
> 1. **Use Customers_by_State.csv** as the input (has CUSTOMERTOKEN). 30,931 active CA customers (was Active_SC_Customers_CA.csv with 30,862 rows; the new file is the same SQL output with the customertoken column added).
> 2. **Dedupe by name for the join** so duplicate-named customers don't multiply per-name records/totals (~1.83× inflation otherwise — Codex finding).
> 3. **Count customers via DISTINCT customertoken**, not distinct names. A name like "Maria Garcia" can map to multiple real customers; each gets credit for the matched name.
> 4. **Use LAST FIRST only** as the match key. CA stores names as `LAST FIRST` (e.g., `YASSINE AHMED`); the reverse ordering pulls in name-reversed strangers.
>
> The numbers below reflect all four corrections. The script `scripts/customer_match_fast.py` produces these.

You are auditing the customer-match numbers on slide 6 of `myReclaim-Exec-Deck.pptx` in this repo. Reproduce the analysis from scratch, then report any discrepancies between your computed numbers and the claimed numbers below.

## Inputs

Two source files. Both must already exist on the auditor's machine.

| File | Purpose |
|---|---|
| `/Users/ahmedyassine/Downloads/Customers_by_State.csv` | 30,931 active SmartCredit customers in CA (with CUSTOMERTOKEN) |
| `data/ca_unclaimed.duckdb` (gitignored, in this worktree) | All 4 California tiers of unclaimed-property records loaded from sco.ca.gov |

**Customer CSV columns** (header row):
```
CUSTOMERTOKEN,FIRST_NAME,LAST_NAME,MIDDLE_NAME,CUSTOMER_ADDRESS_STATE,CUSTOMER_ADDRESS_CITY,CUSTOMER_ADDRESS_ZIPCODE,PRODUCT,CUSTOMERS
```

**DuckDB table** (`ca_unclaimed`) — relevant columns:
```
record_id              BIGINT
owner_name             VARCHAR
owner_name_normalized  VARCHAR   -- already UPPER-trimmed at ingest
amount_max             DECIMAL(14,2)
source_file            VARCHAR   -- one of:
                                   01_From_0_To_Below_10.zip
                                   02_From_10_To_Below_100.zip
                                   03_From_100_To_Below_500.zip
                                   04_From_500_To_Beyond.zip
```

There is an index `ix_owner_normalized` on `owner_name_normalized` — your queries should use equality joins to leverage it.

## Methodology to reproduce

1. **Load customers** into a DuckDB temp table. Normalize first/last names with `UPPER(TRIM(REGEXP_REPLACE(name, '\s+', ' ', 'g')))`. Skip rows where `FIRST_NAME` or `LAST_NAME` is null/empty. **Use `SELECT DISTINCT` so duplicate normalized names collapse to one row before the join** (Codex finding — duplicate rows otherwise multiply per-customer totals ~1.83×).

2. **Build a single match key per customer**: `last_norm || ' ' || first_norm`. CA stores names as LAST FIRST. Do **not** also try the reverse ordering — that pulls in name-reversed strangers as false positives.

3. **Equality join** against `ca_unclaimed.owner_name_normalized` using the index. **Do not use `OR` or `LIKE`** in the join clause — both prevent index usage and run >100× slower.

4. **No address, DOB, or middle-name filtering.** Name-only match. Records with middle names or extra tokens (`AL SHEKHLY YASSINE AHMED`) won't be caught by exact equality — that's a known conservative trade-off; the prototype's substring matcher catches those at the cost of broader false-positive risk.

## Sanity checks before running queries

Run these first; confirm they hold.

```sql
-- Should return 4 source files and ~92.4M total
SELECT source_file, COUNT(*) FROM ca_unclaimed GROUP BY 1 ORDER BY 1;

-- Should return 30,862
SELECT COUNT(*) FROM read_csv_auto(
  '/Users/ahmedyassine/Downloads/Active_SC_Customers_CA.csv', header=true
) WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL;
```

Expected:
| source_file | rows |
|---|---|
| 01_From_0_To_Below_10.zip | 43,357,501 |
| 02_From_10_To_Below_100.zip | 34,515,649 |
| 03_From_100_To_Below_500.zip | 10,727,108 |
| 04_From_500_To_Beyond.zip | 3,800,852 |
| **total** | **92,401,110** |

## The audit query (canonical form — LAST FIRST only, deduped)

```sql
WITH cust AS (
    SELECT DISTINCT  -- ← dedupe before the join
        UPPER(TRIM(REGEXP_REPLACE(FIRST_NAME, '\s+', ' ', 'g'))) AS f,
        UPPER(TRIM(REGEXP_REPLACE(LAST_NAME,  '\s+', ' ', 'g'))) AS l
    FROM read_csv_auto(
        '/Users/ahmedyassine/Downloads/Active_SC_Customers_CA.csv',
        header=true
    )
    WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL
),
matches AS (
    SELECT cust.f, cust.l, u.record_id, u.amount_max, u.source_file
    FROM cust
    JOIN ca_unclaimed u
      ON u.owner_name_normalized = cust.l || ' ' || cust.f  -- LAST FIRST only
)
SELECT * FROM matches;
```

Materialize `matches` to a temp table; downstream aggregates run off it.

## Claims to verify (slide 6)

### Claim 1 — Headline cards (v3, customertoken-aware)

| Metric | Claimed |
|---|---|
| Active CA customers (DISTINCT customertoken) | **30,931** |
| Distinct normalized names | **29,435** |
| Names with ≥1 match | **21,676** |
| **Customers (real people) with ≥1 match** | **23,166** |
| **Match rate (customers / cohort)** | **74.9%** |
| Records matched | **2,313,185** |
| Estimated value across all matches | **$172,354,594** |

Audit query:
```sql
SELECT
  COUNT(DISTINCT f || '|' || l) AS matched_customers,
  SUM(amount_max)               AS total_value
FROM matches;
```

### Claim 2 — Match distribution (records returned per name, v3)

Each customer's name produces a record-count when searched; we bucket customers by that count. Customer counts use distinct customertoken; bucket $ values are summed once per name (not per customer). Customer counts sum to 23,166.

| Records returned | Customers | $ total in bucket | $/customer |
|---|---|---|---|
| 1 record | 3,331 | $219K | $66 |
| 2–5 records | 5,790 | $1.19M | $205 |
| 6–20 records | 4,388 | $3.47M | $792 |
| 20+ records | 9,657 | $167M | $17,329 |
| **TOTAL** | **23,166** | **$172M** | — |

Audit query:
```sql
WITH per_cust AS (
  SELECT f, l, COUNT(*) AS records, SUM(amount_max) AS total
  FROM matches GROUP BY f, l
)
SELECT
  CASE
    WHEN records = 1 THEN '1 record'
    WHEN records BETWEEN 2 AND 5 THEN '2-5 records'
    WHEN records BETWEEN 6 AND 20 THEN '6-20 records'
    ELSE '20+ records'
  END AS bucket,
  COUNT(*)         AS customers,
  SUM(total)       AS bucket_total,
  AVG(total)       AS avg_per_customer
FROM per_cust
GROUP BY 1
ORDER BY MIN(records);
```

### Claim 3 — Customers by total owed (v3)

Each customer assigned to one bucket by the SUM of records under their normalized name. Customer counts use customertoken; bucket totals are summed once per name. Counts sum to 23,166. Bucket totals sum to $172.35M.

| Total owed | Customers | Bucket total | $/customer |
|---|---|---|---|
| $0–$9.99 | 2,774 | $9K | $3 |
| $10–$99.99 | 4,526 | $198K | $44 |
| $100–$499.99 | 4,317 | $1.06M | $245 |
| $500+ | 11,549 | $171M | $14,814 |
| **TOTAL** | **23,166** | **$172,354,593.63** | — |

Audit query:
```sql
WITH per_cust AS (
  SELECT f, l, SUM(amount_max) AS total_owed
  FROM matches GROUP BY f, l
)
SELECT
  CASE
    WHEN total_owed < 10  THEN '$0-$9.99'
    WHEN total_owed < 100 THEN '$10-$99.99'
    WHEN total_owed < 500 THEN '$100-$499.99'
    ELSE '$500+'
  END AS bucket,
  COUNT(*)        AS customers,
  SUM(total_owed) AS bucket_total,
  AVG(total_owed) AS avg_per_customer
FROM per_cust
GROUP BY 1
ORDER BY MIN(total_owed);
```

## What to report back

For each claim above:

1. The numbers you computed.
2. Whether they match the claimed numbers exactly. (Penny-level differences from `DECIMAL(14,2)` rounding are OK.)
3. If anything diverges, paste your query and your output, and identify which step in the methodology produced the discrepancy.

Also flag:

- **Customers in the input CSV with empty / null first or last name.** The methodology drops them. Confirm count.
- **Anywhere `OR` is used in a join.** This is the slow-and-incomplete pattern; flag if seen.
- **Any record where `amount_max` is NULL.** `SUM(amount_max)` ignores NULL, but `AVG` semantics differ — confirm what the analysis does.
- **Customers whose name-key produces zero matches.** They should not appear in any bucket; verify `30,862 - 21,864 = 8,998` had no name match anywhere.

## Methodology disclaimers (already in slide 6)

- This is **name-only** matching. Same logic the prototype uses, run via the indexed equality path. The state determines actual eligibility per record.
- 70.8% is the **upper bound** — name-only matching multi-counts common names. Production PII matching (phonetic + middle-name + last-4 SSN + DOB) would tighten this dramatically. The realistic match rate is closer to NAUPA's population baseline of ~14%.
- The $/customer column in the records-returned distribution exposes the false-positive issue: $73 (distinct names) vs $37,898 (common-name collisions like "John Smith") — the latter clearly inflated.
- The customers-by-total-owed table is the cleanest accounting view: each customer counted exactly once, totals reconcile.

## Source script (for reference)

The actual analysis script is at:

```
scripts/customer_match_fast.py
```

Codex can run it directly:

```bash
.venv/bin/python scripts/customer_match_fast.py
```

That writes `/tmp/customer_match_results.json` with the raw aggregates. Comparing those JSON values to the slide is the fastest end-to-end audit.
