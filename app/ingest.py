"""Download and load California unclaimed property data into DuckDB."""
from __future__ import annotations
import csv
import io
import logging
import re
import uuid
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import duckdb
import httpx

from app.db import ensure_schema, get_connection

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CA_BASE_URL = "https://claimit.ca.gov/upd-property-records/"
TIERS = [
    "04_From_500_To_Beyond.zip",   # high-value first
    "03_From_100_To_Below_500.zip",
    "02_From_10_To_Below_100.zip",
]

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def normalize_owner_name(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().upper()


def parse_amount(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    cleaned = re.sub(r"[^\d.\-]", "", str(value))
    if not cleaned or cleaned in {".", "-"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_reported_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def download_tier(tier_filename: str, dest_dir: Path) -> tuple[Path, str]:
    """Download a tier zip; returns (local_path, etag)."""
    url = CA_BASE_URL + tier_filename
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / tier_filename
    log.info(f"Downloading {url}")
    with httpx.stream("GET", url, follow_redirects=True, timeout=300.0) as resp:
        resp.raise_for_status()
        etag = resp.headers.get("etag", "")
        with open(local_path, "wb") as f:
            for chunk in resp.iter_bytes(chunk_size=1 << 20):
                f.write(chunk)
    log.info(f"Downloaded {local_path} ({local_path.stat().st_size:,} bytes)")
    return local_path, etag


def iter_csv_rows(zip_path: Path) -> Iterable[dict]:
    """Yield rows from the (single) CSV inside the zip as dicts keyed by header."""
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError(f"No CSV inside {zip_path}")
        csv_name = csv_names[0]
        log.info(f"Reading {csv_name} from {zip_path.name}")
        with zf.open(csv_name) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8", errors="replace", newline="")
            reader = csv.DictReader(text)
            yield from reader


# Best-effort header mapping. CA SCO does not document the schema; we
# tolerate variations and fall back to None for unknown columns.
HEADER_ALIASES = {
    "owner_name":         ["OWNER_NAME", "OWNER", "OWNERNAME", "OWNERLASTNAME"],
    "owner_first":        ["OWNER_FIRST", "FIRSTNAME", "OWNERFIRSTNAME"],
    "owner_last":         ["OWNER_LAST", "LASTNAME", "OWNERLASTNAME"],
    "holder_name":        ["HOLDER_NAME", "HOLDER", "REPORTING_HOLDER"],
    # CA SCO uses PROPERTY_ID as the unique property identifier (no holder_id column)
    "holder_id":          ["PROPERTY_ID", "HOLDER_ID", "HOLDERID"],
    # CA SCO uses OWNER_STREET_1 for the primary street address
    "address":            ["OWNER_STREET_1", "OWNER_ADDRESS", "ADDRESS", "STREET"],
    "city":               ["OWNER_CITY", "CITY"],
    "state":              ["OWNER_STATE", "STATE"],
    "zip":                ["OWNER_ZIP", "ZIP", "ZIPCODE", "POSTAL_CODE"],
    "amount_min":         ["CASH_REPORTED", "AMOUNT", "MIN_AMOUNT"],
    "amount_max":         ["CURRENT_CASH_BALANCE", "MAX_AMOUNT"],
    "property_type":      ["PROPERTY_TYPE", "PROPERTYTYPE", "PROP_TYPE"],
    # CA SCO CSVs do not include a reported date column; field will be NULL
    "reported_date":      ["REPORTED_DATE", "DATE_OF_LAST_CONTACT", "REPORT_DATE"],
}


def map_row(raw: dict) -> dict:
    upper = {k.upper().replace(" ", "_"): v for k, v in raw.items() if k}

    def pick(key_options):
        for k in key_options:
            if k in upper and upper[k] != "":
                return upper[k]
        return None

    full_name = pick(HEADER_ALIASES["owner_name"])
    if not full_name:
        first = pick(HEADER_ALIASES["owner_first"]) or ""
        last = pick(HEADER_ALIASES["owner_last"]) or ""
        full_name = f"{first} {last}".strip()

    return {
        "holder_name": pick(HEADER_ALIASES["holder_name"]),
        "holder_id": pick(HEADER_ALIASES["holder_id"]),
        "owner_name": full_name,
        "owner_name_normalized": normalize_owner_name(full_name),
        "last_known_address": pick(HEADER_ALIASES["address"]),
        "last_known_city": pick(HEADER_ALIASES["city"]),
        "last_known_state": pick(HEADER_ALIASES["state"]),
        "last_known_zip": pick(HEADER_ALIASES["zip"]),
        "amount_min": parse_amount(pick(HEADER_ALIASES["amount_min"])),
        "amount_max": parse_amount(pick(HEADER_ALIASES["amount_max"])),
        "property_type": pick(HEADER_ALIASES["property_type"]),
        "reported_date": parse_reported_date(pick(HEADER_ALIASES["reported_date"])),
    }


def load_tier_into_duckdb(
    conn: duckdb.DuckDBPyConnection,
    zip_path: Path,
    source_file: str,
    batch_size: int = 50_000,
) -> int:
    """Stream rows from zip_path into ca_unclaimed. Returns rows loaded."""
    inserted = 0
    next_id_row = conn.execute("SELECT COALESCE(MAX(record_id), 0) FROM ca_unclaimed").fetchone()
    next_id = (next_id_row[0] if next_id_row else 0) + 1
    batch = []

    insert_sql = """
        INSERT INTO ca_unclaimed VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
        )
    """

    for raw in iter_csv_rows(zip_path):
        m = map_row(raw)
        batch.append((
            next_id,
            m["holder_name"], m["holder_id"],
            m["owner_name"], m["owner_name_normalized"],
            m["last_known_address"], m["last_known_city"],
            m["last_known_state"], m["last_known_zip"],
            m["amount_min"], m["amount_max"],
            m["property_type"], m["reported_date"],
            source_file,
        ))
        next_id += 1
        if len(batch) >= batch_size:
            conn.executemany(insert_sql, batch)
            inserted += len(batch)
            log.info(f"  loaded {inserted:,} rows")
            batch = []

    if batch:
        conn.executemany(insert_sql, batch)
        inserted += len(batch)

    log.info(f"Total rows from {source_file}: {inserted:,}")
    return inserted


def run(tiers: list[str] = None) -> None:
    """Entry point: download configured tiers and load them into DuckDB."""
    tiers = tiers or TIERS
    conn = get_connection()
    ensure_schema(conn)

    for tier in tiers:
        run_id = str(uuid.uuid4())
        started = datetime.utcnow()
        try:
            zip_path, etag = download_tier(tier, DATA_DIR)
            rows = load_tier_into_duckdb(conn, zip_path, source_file=tier)
            conn.execute("""
                INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [run_id, started, datetime.utcnow(), tier, etag, rows, "completed"])
        except Exception as e:
            log.exception(f"Failed to ingest {tier}")
            conn.execute("""
                INSERT INTO ingest_runs VALUES (?, ?, ?, ?, ?, ?, ?)
            """, [run_id, started, datetime.utcnow(), tier, "", 0, f"failed: {e}"])
            raise

    conn.close()


if __name__ == "__main__":
    run()
