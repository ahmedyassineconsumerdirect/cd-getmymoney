"""Fast bulk-load helper: ingest a directory of pre-extracted CA SCO CSVs
into ca_unclaimed using DuckDB's native read_csv_auto.

Much faster than the Python row-by-row ingest (~30x speedup for tier 02).
The trade-off: less header-alias flexibility — assumes CA SCO column names.

Usage:
    python scripts/fast_load_directory.py /path/to/csv_dir SOURCE_LABEL
"""
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_connection, ensure_schema


def fast_load(csv_dir: Path, source_label: str) -> int:
    """Load all CSVs in csv_dir into ca_unclaimed via bulk SQL. Returns rows loaded."""
    if not csv_dir.exists() or not csv_dir.is_dir():
        raise SystemExit(f"Not a directory: {csv_dir}")

    csv_glob = str(csv_dir / "*.csv")
    print(f"[{datetime.now():%H:%M:%S}] Loading from glob: {csv_glob}")

    conn = get_connection()
    ensure_schema(conn)

    # Get the next record_id
    next_id_row = conn.execute(
        "SELECT COALESCE(MAX(record_id), 0) FROM ca_unclaimed"
    ).fetchone()
    base_id = next_id_row[0] if next_id_row else 0
    print(f"[{datetime.now():%H:%M:%S}] Starting from record_id: {base_id + 1}")

    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)

    sql = f"""
        INSERT INTO ca_unclaimed
        SELECT
            {base_id} + ROW_NUMBER() OVER ()                                 AS record_id,
            HOLDER_NAME                                                      AS holder_name,
            CAST(PROPERTY_ID AS VARCHAR)                                     AS holder_id,
            OWNER_NAME                                                       AS owner_name,
            UPPER(TRIM(REGEXP_REPLACE(OWNER_NAME, '\\s+', ' ', 'g')))        AS owner_name_normalized,
            OWNER_STREET_1                                                   AS last_known_address,
            OWNER_CITY                                                       AS last_known_city,
            OWNER_STATE                                                      AS last_known_state,
            CAST(OWNER_ZIP AS VARCHAR)                                       AS last_known_zip,
            TRY_CAST(CASH_REPORTED AS DECIMAL(14,2))                         AS amount_min,
            TRY_CAST(CURRENT_CASH_BALANCE AS DECIMAL(14,2))                  AS amount_max,
            PROPERTY_TYPE                                                    AS property_type,
            NULL::DATE                                                       AS reported_date,
            ?                                                                AS source_file,
            CURRENT_TIMESTAMP                                                AS ingested_at
        FROM read_csv_auto(?, header=true, ignore_errors=true)
    """

    t0 = time.time()
    print(f"[{datetime.now():%H:%M:%S}] Starting bulk INSERT (this is the slow step)...")
    try:
        conn.execute(sql, [source_label, csv_glob])
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[{datetime.now():%H:%M:%S}] FAILED after {elapsed:.0f}s: {e}")
        conn.execute(
            "INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            [run_id, started, datetime.now(timezone.utc), source_label, "", 0, f"failed: {e}"],
        )
        conn.close()
        raise

    elapsed = time.time() - t0
    inserted = conn.execute(
        "SELECT COUNT(*) FROM ca_unclaimed WHERE source_file = ?", [source_label]
    ).fetchone()[0]
    total_rows_for_source = inserted

    print(f"[{datetime.now():%H:%M:%S}] Done in {elapsed:.0f}s. Inserted {total_rows_for_source:,} rows.")

    conn.execute(
        "INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [run_id, started, datetime.now(timezone.utc), source_label, "", total_rows_for_source, "completed"],
    )
    conn.close()
    return total_rows_for_source


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/fast_load_directory.py /path/to/csv_dir SOURCE_LABEL")
        sys.exit(1)
    fast_load(Path(sys.argv[1]), sys.argv[2])
