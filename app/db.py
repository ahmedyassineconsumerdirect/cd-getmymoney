"""DuckDB connection lifecycle and schema bootstrap."""
from pathlib import Path
import duckdb

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "ca_unclaimed.duckdb"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ca_unclaimed (
    record_id              BIGINT,
    holder_name            VARCHAR,
    holder_id              VARCHAR,
    owner_name             VARCHAR,
    owner_name_normalized  VARCHAR,
    last_known_address     VARCHAR,
    last_known_city        VARCHAR,
    last_known_state       VARCHAR,
    last_known_zip         VARCHAR,
    amount_min             DECIMAL(14,2),
    amount_max             DECIMAL(14,2),
    property_type          VARCHAR,
    reported_date          DATE,
    source_file            VARCHAR,
    ingested_at            TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_owner_normalized
    ON ca_unclaimed(owner_name_normalized);

CREATE TABLE IF NOT EXISTS ingest_runs (
    run_id        VARCHAR PRIMARY KEY,
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    file_name     VARCHAR,
    etag          VARCHAR,
    rows_loaded   BIGINT,
    status        VARCHAR
);
"""


def get_connection(db_path: str | Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))


def ensure_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute(SCHEMA_SQL)
