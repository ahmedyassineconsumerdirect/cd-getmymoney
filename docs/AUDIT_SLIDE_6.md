# Audit instructions — Slide 6 customer-match statistics

> **2026-04-29 update — Codex caught two real bugs in the v1 numbers:**
> 1. Customer rows must be **DISTINCT-ed on (first_norm, last_norm) before the join**. The CSV has 30,862 rows but only 29,405 unique normalized name pairs; the 1,457 duplicate-name rows were each joining to the same set of CA records, multiplying counts and dollars by ~1.83×.
> 2. The two name orderings must be combined with **`UNION`** (not `UNION ALL`) so customers whose first==last don't generate 321 self-doubled match rows.
>
> The numbers below are the **corrected** (deduped) values. The script `scripts/customer_match_fast.py` was updated to produce these.

You are auditing the customer-match numbers on slide 6 of `myReclaim-Exec-Deck.pptx` in this repo. Reproduce the analysis from scratch, then report any discrepancies between your computed numbers and the claimed numbers below.

## Inputs

Two source files. Both must already exist on the auditor's machine.

| File | Purpose |
|---|---|
| `/Users/ahmedyassine/Downloads/Active_SC_Customers_CA.csv` | 30,862 active SmartCredit customers in CA |
| `data/ca_unclaimed.duckdb` (gitignored, in this worktree) | All 4 California tiers of unclaimed-property records loaded from sco.ca.gov |

**Customer CSV columns** (header row):
```
FIRST_NAME,LAST_NAME,MIDDLE_NAME,CUSTOMER_ADDRESS_STATE,CUSTOMER_ADDRESS_CITY,CUSTOMER_ADDRESS_ZIPCODE,CUSTOMERPRODUCTID,CUSTOMERS
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

1. **Load customers** into a DuckDB temp table. Normalize first/last names with `UPPER(TRIM(REGEXP_REPLACE(name, '\s+', ' ', 'g')))`. Skip rows where `FIRST_NAME` or `LAST_NAME` is null/empty. **Use `SELECT DISTINCT` so duplicate normalized names collapse to one row before the join** (caught by the Codex audit — duplicate rows otherwise multiply per-customer totals).

2. **Build match keys** per customer — both orderings:
   - `key_fl = first_norm || ' ' || last_norm`
   - `key_lf = last_norm || ' ' || first_norm`

3. **Equality join** against `ca_unclaimed.owner_name_normalized`. **Combine the two keys with `UNION` (not `UNION ALL`)** so customers whose first_name == last_name don't generate self-doubled match rows. **Do not use `OR` in the join clause** (the `OR` form does not use the index and runs >100× slower).

4. **No address, DOB, or middle-name filtering.** Name-only match.

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

## The audit query (canonical form, deduped)

```sql
WITH cust AS (
    SELECT DISTINCT  -- ← critical: dedupe before the join
        UPPER(TRIM(REGEXP_REPLACE(FIRST_NAME, '\s+', ' ', 'g'))) AS f,
        UPPER(TRIM(REGEXP_REPLACE(LAST_NAME,  '\s+', ' ', 'g'))) AS l
    FROM read_csv_auto(
        '/Users/ahmedyassine/Downloads/Active_SC_Customers_CA.csv',
        header=true
    )
    WHERE FIRST_NAME IS NOT NULL AND LAST_NAME IS NOT NULL
),
all_keys AS (
    SELECT f, l, f || ' ' || l AS k FROM cust
    UNION  -- ← UNION (not UNION ALL) so first==last names don't double-count
    SELECT f, l, l || ' ' || f AS k FROM cust
),
matches AS (
    SELECT ak.f, ak.l, u.record_id, u.amount_max, u.source_file
    FROM all_keys ak
    JOIN ca_unclaimed u ON u.owner_name_normalized = ak.k
)
SELECT * FROM matches;
```

Materialize `matches` to a temp table; downstream aggregates run off it.

## Claims to verify (slide 6)

### Claim 1 — Headline cards (post-Apr 29 dedupe fix)

| Metric | Claimed |
|---|---|
| CSV rows in active CA cohort | **30,862** |
| Distinct normalized names | **29,405** |
| Names with ≥1 match | **21,864** |
| Match rate (vs distinct) | **74.4%** |
| Records matched | **2,414,471** |
| Estimated value across all matches | **$178,343,939** |

Audit query:
```sql
SELECT
  COUNT(DISTINCT f || '|' || l) AS matched_customers,
  SUM(amount_max)               AS total_value
FROM matches;
```

### Claim 2 — Match distribution (records returned per customer, deduped)

Each distinct customer name falls in exactly one bucket based on **how many records returned** when that name was searched. Customer counts should sum to 21,864.

| Records returned | Customers | $ total in bucket | $/customer |
|---|---|---|---|
| 1 record | 3,278 | $239K | $73 |
| 2–5 records | 5,798 | $1.22M | $210 |
| 6–20 records | 4,402 | $3.52M | $800 |
| 20+ records | 8,386 | $173M | $20,673 |
| **TOTAL** | **21,864** | **$178M** | — |

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

### Claim 3 — Customers by total owed (each customer in exactly one bucket, deduped)

Customer counts sum to 21,864. Bucket totals sum to $178M.

| Total owed | Customers | Bucket total | $/customer |
|---|---|---|---|
| $0–$9.99 | 2,707 | $8K | $3 |
| $10–$99.99 | 4,571 | $200K | $44 |
| $100–$499.99 | 4,297 | $1.06M | $246 |
| $500+ | 10,289 | $177M | $17,211 |
| **TOTAL** | **21,864** | **$178,343,938.87** | — |

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
