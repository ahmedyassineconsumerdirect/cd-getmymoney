import os
from pathlib import Path
from app.db import get_connection, ensure_schema

def test_ensure_schema_creates_tables(tmp_path):
    db_path = tmp_path / "test.duckdb"
    conn = get_connection(str(db_path))
    ensure_schema(conn)
    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    assert "ca_unclaimed" in tables
    assert "ingest_runs" in tables
    conn.close()

def test_ensure_schema_idempotent(tmp_path):
    db_path = tmp_path / "test.duckdb"
    conn = get_connection(str(db_path))
    ensure_schema(conn)
    ensure_schema(conn)  # second call must not error
    conn.close()
