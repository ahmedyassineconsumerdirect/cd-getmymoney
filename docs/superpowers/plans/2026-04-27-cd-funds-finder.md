# CD Funds Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Local prototype of an unclaimed-property finder for SmartCredit, with a SmartCredit-styled web app over real California State Controller data and a 9-slide reveal.js executive deck. Runs end-to-end on a laptop with one command.

**Architecture:** FastAPI + Jinja2 + htmx for the web app, DuckDB for the local analytical store (Snowflake-shaped SQL), Tailwind via Play CDN for styling, reveal.js via CDN for the deck. A `MatchService` interface abstracts name matching so Consumer Direct's existing matcher can swap in later.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, DuckDB, Jinja2, htmx, Tailwind CSS (Play CDN), reveal.js (CDN), httpx, pytest

**Reference:** [`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](../specs/2026-04-27-cd-funds-finder-design.md)

---

## File Structure

```
cd-funds-finder/
├── .gitignore                  # Ignore venv, data/, __pycache__, .superpowers/
├── pyproject.toml              # Project metadata, deps via tool.uv (or skip if pip)
├── requirements.txt            # Pinned deps for one-line install
├── README.md                   # Run instructions + 30-sec demo script
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, routes, startup
│   ├── db.py                   # DuckDB connection helper + schema init
│   ├── ingest.py               # CA download → unzip → COPY INTO ca_unclaimed
│   ├── match.py                # MatchService protocol + DemoExactMatcher
│   ├── templates/
│   │   ├── base.html           # SmartCredit-styled layout (nav, footer)
│   │   ├── home.html           # Hero + search form
│   │   ├── _results.html       # htmx fragment, lists matches
│   │   └── admin.html          # Pipeline status page
│   └── static/
│       └── img/
│           └── (favicon)
├── deck/
│   ├── index.html              # reveal.js deck, 9 slides
│   └── assets/
├── data/                       # DuckDB file lives here (gitignored)
├── scripts/
│   └── refresh_data.py         # CLI re-trigger ingest
├── tests/
│   ├── test_match.py
│   └── test_ingest.py
└── docs/
    └── superpowers/
        ├── specs/
        └── plans/
```

**Boundaries:**
- `db.py` owns DuckDB lifecycle (connection, schema bootstrap). One responsibility.
- `ingest.py` owns I/O (HTTP, zip, CSV → table). Pure data motion.
- `match.py` owns the search interface. Pluggable.
- `main.py` owns HTTP routing and template rendering only. No business logic.
- Tests cover `match.py` and `ingest.py`'s normalization helpers — UI is smoke-tested manually.

---

## Task 1: Project scaffold + FastAPI hello-world

**Files:**
- Create: `pyproject.toml`, `requirements.txt`, `.gitignore`, `README.md`
- Create: `app/__init__.py`, `app/main.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `.gitignore`**

```
.venv/
__pycache__/
*.pyc
data/
.superpowers/
.pytest_cache/
.DS_Store
*.duckdb
*.duckdb.wal
```

- [ ] **Step 2: Create `requirements.txt`**

```
fastapi==0.115.4
uvicorn[standard]==0.32.0
jinja2==3.1.4
duckdb==1.1.3
httpx==0.27.2
python-multipart==0.0.17
pytest==8.3.3
```

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[project]
name = "cd-funds-finder"
version = "0.1.0"
description = "Unclaimed property finder prototype for SmartCredit"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Create `app/__init__.py` and `app/main.py`**

`app/__init__.py`: empty file.

`app/main.py`:
```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="CD Funds Finder")

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>CD Funds Finder — alive</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
```

- [ ] **Step 5: Create venv, install, smoke-test**

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.main &
sleep 2
curl -s http://127.0.0.1:8000/ | head -1
kill %1
```

Expected: `<h1>CD Funds Finder — alive</h1>`

- [ ] **Step 6: Create `README.md` skeleton**

```markdown
# CD Funds Finder

Local prototype: unclaimed-property search for SmartCredit members against California State Controller data + a 9-slide executive deck.

## Quick start

\`\`\`bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.ingest          # one-time, ~3-5 min
python -m app.main            # serves at http://127.0.0.1:8000
\`\`\`

- App: http://127.0.0.1:8000
- Deck: http://127.0.0.1:8000/deck
- Admin: http://127.0.0.1:8000/admin

## Design

See [`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md).
```

- [ ] **Step 7: Commit**

```bash
git add .gitignore pyproject.toml requirements.txt README.md app/__init__.py app/main.py tests/__init__.py
git commit -m "scaffold FastAPI app with hello-world route"
```

---

## Task 2: DuckDB connection helper + schema bootstrap

**Files:**
- Create: `app/db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Write the failing test**

`tests/test_db.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db'`

- [ ] **Step 3: Implement `app/db.py`**

```python
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
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_db.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/db.py tests/test_db.py
git commit -m "add DuckDB connection helper and schema bootstrap"
```

---

## Task 3: California data ingestion

**Files:**
- Create: `app/ingest.py`
- Create: `tests/test_ingest.py`

This task downloads the highest-value tier (`04_From_500_To_Beyond.zip`), inspects its CSV header, and loads the data into `ca_unclaimed`. Lower-value tiers reuse the same code path.

- [ ] **Step 1: Write failing tests for the normalization helpers**

`tests/test_ingest.py`:
```python
from datetime import date
from app.ingest import normalize_owner_name, parse_amount, parse_reported_date

def test_normalize_owner_name():
    assert normalize_owner_name("  John  Smith ") == "JOHN SMITH"
    assert normalize_owner_name("Maria O'Brien") == "MARIA O'BRIEN"
    assert normalize_owner_name("") == ""
    assert normalize_owner_name(None) == ""

def test_parse_amount():
    assert parse_amount("$1,234.56") == 1234.56
    assert parse_amount("1234.56") == 1234.56
    assert parse_amount("") is None
    assert parse_amount(None) is None
    assert parse_amount("garbage") is None

def test_parse_reported_date():
    assert parse_reported_date("2021-06-15") == date(2021, 6, 15)
    assert parse_reported_date("06/15/2021") == date(2021, 6, 15)
    assert parse_reported_date("") is None
    assert parse_reported_date(None) is None
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `pytest tests/test_ingest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.ingest'`

- [ ] **Step 3: Implement `app/ingest.py`**

```python
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
    "holder_id":          ["HOLDER_ID", "HOLDERID"],
    "address":            ["OWNER_ADDRESS", "ADDRESS", "STREET"],
    "city":               ["OWNER_CITY", "CITY"],
    "state":              ["OWNER_STATE", "STATE"],
    "zip":                ["OWNER_ZIP", "ZIP", "ZIPCODE", "POSTAL_CODE"],
    "amount_min":         ["CASH_REPORTED", "AMOUNT", "MIN_AMOUNT"],
    "amount_max":         ["CURRENT_CASH_BALANCE", "MAX_AMOUNT"],
    "property_type":      ["PROPERTY_TYPE", "PROPERTYTYPE", "PROP_TYPE"],
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
```

- [ ] **Step 4: Run unit tests, verify they pass**

Run: `pytest tests/test_ingest.py -v`
Expected: 3 passed

- [ ] **Step 5: Smoke-test with real download (highest-value tier only first)**

Run:
```bash
python -c "from app.ingest import run; run(['04_From_500_To_Beyond.zip'])"
```

Expected: log lines showing download progress and row counts. Final state: `data/ca_unclaimed.duckdb` exists with `>0` rows in `ca_unclaimed`. Verify:
```bash
python -c "
import duckdb
c = duckdb.connect('data/ca_unclaimed.duckdb')
print(c.execute('SELECT COUNT(*) FROM ca_unclaimed').fetchone())
print(c.execute('SELECT * FROM ca_unclaimed LIMIT 3').fetchall())
"
```

If header mapping returns mostly `None` values, inspect the actual CSV headers and update `HEADER_ALIASES`:
```bash
python -c "
import zipfile, io, csv
z = zipfile.ZipFile('data/raw/04_From_500_To_Beyond.zip')
name = [n for n in z.namelist() if n.endswith('.csv')][0]
with z.open(name) as f:
    text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
    print(next(csv.reader(text)))
"
```

Update `HEADER_ALIASES` in `app/ingest.py` to include the actual column names, drop `data/ca_unclaimed.duckdb`, and re-run the smoke test.

- [ ] **Step 6: Commit**

```bash
git add app/ingest.py tests/test_ingest.py
git commit -m "add California unclaimed property ingestion pipeline"
```

---

## Task 4: MatchService interface + DemoExactMatcher

**Files:**
- Create: `app/match.py`
- Create: `tests/test_match.py`

- [ ] **Step 1: Write failing tests**

`tests/test_match.py`:
```python
from datetime import datetime
from app.db import get_connection, ensure_schema
from app.match import DemoExactMatcher

def _seed(conn):
    conn.execute("""
        INSERT INTO ca_unclaimed VALUES
        (1, 'WELLS FARGO', 'WF1', 'JOHN SMITH', 'JOHN SMITH',
         '123 Main St', 'San Francisco', 'CA', '94102',
         2150.00, 2150.00, 'Savings Account', '2021-06-15',
         'test', CURRENT_TIMESTAMP),
        (2, 'CHARLES SCHWAB', 'SCHWAB', 'JOHN SMITH', 'JOHN SMITH',
         '456 Oak Ave', 'San Jose', 'CA', '95110',
         1580.50, 1580.50, 'Brokerage', '2020-03-10',
         'test', CURRENT_TIMESTAMP),
        (3, 'BANK OF AMERICA', 'BOA1', 'JANE DOE', 'JANE DOE',
         '789 Pine St', 'Los Angeles', 'CA', '90001',
         50.00, 50.00, 'Checking', '2022-01-20',
         'test', CURRENT_TIMESTAMP)
    """)

def test_exact_match_finds_records(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="John", last_name="Smith")
    assert len(matches) == 2
    assert all(m.owner_name == "JOHN SMITH" for m in matches)
    assert matches[0].amount_max >= matches[1].amount_max  # ordered desc
    conn.close()

def test_exact_match_no_results(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="Nobody", last_name="Findme")
    assert matches == []
    conn.close()

def test_exact_match_normalizes_input(tmp_path):
    conn = get_connection(str(tmp_path / "t.duckdb"))
    ensure_schema(conn)
    _seed(conn)
    matcher = DemoExactMatcher(conn)
    matches = matcher.find_matches(first_name="  john  ", last_name="smith")
    assert len(matches) == 2
    conn.close()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `pytest tests/test_match.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.match'`

- [ ] **Step 3: Implement `app/match.py`**

```python
"""Match service interface + demo exact-match implementation.

Production swaps DemoExactMatcher for Consumer Direct's existing
data-broker matching service by implementing the MatchService protocol.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Protocol

import duckdb

from app.ingest import normalize_owner_name


@dataclass
class Match:
    record_id: int
    holder_name: str
    owner_name: str
    last_known_address: str | None
    last_known_city: str | None
    last_known_state: str | None
    last_known_zip: str | None
    amount_min: float | None
    amount_max: float | None
    property_type: str | None
    reported_date: date | None


class MatchService(Protocol):
    def find_matches(
        self,
        first_name: str,
        last_name: str,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]: ...


class DemoExactMatcher:
    """Exact match on UPPER(TRIM(first + ' ' + last)).

    Sufficient for the prototype; production uses CD's existing matcher.
    """

    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self.conn = conn

    def find_matches(
        self,
        first_name: str,
        last_name: str,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]:
        normalized = normalize_owner_name(f"{first_name} {last_name}")
        if not normalized:
            return []
        rows = self.conn.execute(
            """
            SELECT record_id, holder_name, owner_name,
                   last_known_address, last_known_city,
                   last_known_state, last_known_zip,
                   amount_min, amount_max,
                   property_type, reported_date
            FROM ca_unclaimed
            WHERE owner_name_normalized = ?
            ORDER BY COALESCE(amount_max, 0) DESC
            LIMIT 100
            """,
            [normalized],
        ).fetchall()
        return [Match(*r) for r in rows]
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `pytest tests/test_match.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add app/match.py tests/test_match.py
git commit -m "add MatchService interface and DemoExactMatcher"
```

---

## Task 5: Extract SmartCredit brand cues

**Files:**
- Create: `app/static/img/branding-notes.md` (reference doc, not user-facing)

This task fetches smartcredit.com to extract the visual cues we'll mirror in the templates. We do this BEFORE writing templates so we get it right the first time.

- [ ] **Step 1: Fetch smartcredit.com homepage**

Use the WebFetch tool:
```
URL: https://www.smartcredit.com/
Prompt: "Extract the visual brand cues: primary brand color (hex if visible),
secondary/accent colors, the font-family used in headings and body, the
header/nav structure (what's left, center, right), the style of buttons
(rounded corners? shadow? color), and the card/section pattern used on
the homepage. Focus on what a designer would need to mimic the look."
```

- [ ] **Step 2: Capture findings to a notes file**

Create `app/static/img/branding-notes.md`:
```markdown
# SmartCredit visual cues (extracted YYYY-MM-DD)

- Primary color: #XXXXXX
- Secondary color: #XXXXXX
- Font (headings): ...
- Font (body): ...
- Nav structure: ...
- Button style: ...
- Card pattern: ...
- Source: https://www.smartcredit.com/

Used to guide Tailwind config in `app/templates/base.html`.
```

If WebFetch returns insufficient detail, take a screenshot manually and note observations. Anything reasonable that *feels* like SmartCredit is acceptable for the prototype — fidelity matters less than coherence.

- [ ] **Step 3: Commit**

```bash
git add app/static/img/branding-notes.md
git commit -m "capture SmartCredit brand cues for prototype styling"
```

---

## Task 6: Base template + home page with search form

**Files:**
- Create: `app/templates/base.html`
- Create: `app/templates/home.html`
- Modify: `app/main.py`

- [ ] **Step 1: Create `app/templates/base.html`**

Use the brand cues from Task 5 to fill in the actual primary color hex value. If unknown, use `#0066CC` (a common credit-product blue) as a placeholder.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}SmartCredit Funds Finder{% endblock %}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/htmx.org@2.0.3"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: {
              DEFAULT: '#0066CC',  // replace with actual SmartCredit primary
              dark: '#004C99',
              light: '#E6F0FA',
            },
          },
          fontFamily: {
            sans: ['Inter', 'system-ui', 'sans-serif'],
          },
        },
      },
    };
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</head>
<body class="bg-gray-50 font-sans text-gray-900">
  <header class="bg-white border-b border-gray-200">
    <div class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-brand rounded"></div>
        <span class="font-bold text-xl">SmartCredit</span>
      </div>
      <nav class="flex items-center gap-6 text-sm font-medium">
        <a href="/" class="text-gray-600 hover:text-brand">Dashboard</a>
        <a href="/" class="text-gray-600 hover:text-brand">Score</a>
        <a href="/" class="text-brand border-b-2 border-brand pb-1">Funds Finder</a>
        <a href="/admin" class="text-gray-400 hover:text-brand text-xs">Admin</a>
      </nav>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-6 py-10">
    {% block content %}{% endblock %}
  </main>

  <footer class="max-w-6xl mx-auto px-6 py-8 text-xs text-gray-400 border-t border-gray-200 mt-20">
    Prototype — data sourced from California State Controller's Office.
    Claims must be filed at <a href="https://claimit.ca.gov" class="underline">claimit.ca.gov</a>.
  </footer>
</body>
</html>
```

- [ ] **Step 2: Create `app/templates/home.html`**

```html
{% extends "base.html" %}
{% block content %}

<section class="text-center py-10">
  <h1 class="text-4xl font-bold text-gray-900">Find money the state owes you.</h1>
  <p class="mt-3 text-lg text-gray-600 max-w-2xl mx-auto">
    We check California's unclaimed property database for funds in your name.
    Free. Takes 10 seconds.
  </p>
</section>

<section class="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-2xl mx-auto">
  <form
    hx-post="/search"
    hx-target="#results"
    hx-swap="innerHTML"
    class="grid grid-cols-2 gap-4"
  >
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">First name</label>
      <input name="first_name" required class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent">
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Last name</label>
      <input name="last_name" required class="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent">
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Date of birth</label>
      <input name="dob" type="date" class="w-full border border-gray-300 rounded-md px-3 py-2">
    </div>
    <div>
      <label class="block text-sm font-medium text-gray-700 mb-1">Current ZIP</label>
      <input name="zip" class="w-full border border-gray-300 rounded-md px-3 py-2">
    </div>
    <div class="col-span-2">
      <button type="submit" class="w-full bg-brand text-white font-semibold py-3 rounded-md hover:bg-brand-dark transition">
        Search California records
      </button>
    </div>
  </form>
</section>

<section id="results" class="mt-10"></section>

{% endblock %}
```

- [ ] **Step 3: Wire route in `app/main.py`**

Replace `app/main.py`:
```python
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="CD Funds Finder")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
```

- [ ] **Step 4: Smoke-test in browser**

Run:
```bash
python -m app.main
```
Open `http://127.0.0.1:8000/`. Expected: SmartCredit-styled page with hero text, search form (first/last/dob/zip), submit button. Form does not yet submit successfully — that's Task 7.

Press Ctrl+C to stop.

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/templates/base.html app/templates/home.html
git commit -m "add SmartCredit-styled base layout and home page with search form"
```

---

## Task 7: Search results endpoint + htmx fragment

**Files:**
- Create: `app/templates/_results.html`
- Modify: `app/main.py`

- [ ] **Step 1: Create `app/templates/_results.html`**

```html
{% if matches %}
  <div class="text-center mb-6">
    <p class="text-2xl font-bold text-gray-900">
      We found {{ matches|length }} match{{ "es" if matches|length != 1 else "" }}
      totaling ${{ "{:,.2f}".format(total) }} in your name.
    </p>
    <p class="text-sm text-gray-500 mt-1">All amounts are estimates from the California State Controller.</p>
  </div>

  <div class="space-y-3 max-w-3xl mx-auto">
    {% for m in matches %}
    <div class="bg-white rounded-lg border border-gray-200 p-5 flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-baseline gap-3">
          <span class="text-2xl font-bold text-brand">${{ "{:,.2f}".format(m.amount_max or 0) }}</span>
          <span class="text-sm text-gray-500 uppercase tracking-wide">{{ m.holder_name or "Unknown holder" }}</span>
        </div>
        <p class="mt-1 text-sm text-gray-700">
          <strong>{{ m.property_type or "Unclaimed property" }}</strong>
          {% if m.reported_date %} · Reported {{ m.reported_date }}{% endif %}
        </p>
        {% if m.last_known_address %}
        <p class="mt-1 text-xs text-gray-500">
          Last known address: {{ m.last_known_address }}{% if m.last_known_city %}, {{ m.last_known_city }}{% endif %}{% if m.last_known_state %} {{ m.last_known_state }}{% endif %}{% if m.last_known_zip %} {{ m.last_known_zip }}{% endif %}
        </p>
        {% endif %}
      </div>
      <a href="https://claimit.ca.gov" target="_blank" class="ml-4 text-sm bg-brand text-white px-4 py-2 rounded-md font-medium hover:bg-brand-dark whitespace-nowrap">
        Claim at claimit.ca.gov →
      </a>
    </div>
    {% endfor %}
  </div>
{% else %}
  <div class="text-center py-10 max-w-xl mx-auto">
    <p class="text-lg font-semibold text-gray-900">No matches found in California.</p>
    <p class="mt-2 text-gray-600">
      We're expanding to all 50 states soon — we'll notify you when there's a match in another state.
      In the meantime, you can also search directly at
      <a href="https://claimit.ca.gov" class="text-brand underline">claimit.ca.gov</a>.
    </p>
  </div>
{% endif %}
```

- [ ] **Step 2: Add the `/search` route to `app/main.py`**

Modify `app/main.py` — add these imports and route:

```python
from fastapi import Form
from app.db import get_connection, ensure_schema
from app.match import DemoExactMatcher

# ... existing code ...

# Initialize DB connection once at startup
_conn = None
def _get_match_service():
    global _conn
    if _conn is None:
        _conn = get_connection()
        ensure_schema(_conn)
    return DemoExactMatcher(_conn)


@app.post("/search", response_class=HTMLResponse)
def search(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    dob: str = Form(""),
    zip: str = Form(""),
):
    matcher = _get_match_service()
    matches = matcher.find_matches(first_name=first_name, last_name=last_name)
    total = sum((m.amount_max or 0) for m in matches)
    return templates.TemplateResponse(
        "_results.html",
        {"request": request, "matches": matches, "total": total},
    )
```

- [ ] **Step 3: Smoke-test in browser**

Run:
```bash
python -m app.main
```

Open `http://127.0.0.1:8000/`. Submit the form with a name you expect to NOT match (e.g., "Zzz Nobody") — should show empty state. Submit a name you can verify has matches in `ca_unclaimed`:

```bash
python -c "
import duckdb
c = duckdb.connect('data/ca_unclaimed.duckdb')
print(c.execute(\"SELECT owner_name, COUNT(*) FROM ca_unclaimed GROUP BY 1 HAVING COUNT(*) > 1 LIMIT 5\").fetchall())
"
```

Use one of those names in the form. Expected: results list rendered with amount, holder, claim link.

- [ ] **Step 4: Commit**

```bash
git add app/main.py app/templates/_results.html
git commit -m "add /search endpoint with htmx-rendered results"
```

---

## Task 8: Admin / pipeline status page

**Files:**
- Create: `app/templates/admin.html`
- Modify: `app/main.py`

- [ ] **Step 1: Create `app/templates/admin.html`**

```html
{% extends "base.html" %}
{% block title %}Admin — Funds Finder{% endblock %}
{% block content %}

<h1 class="text-2xl font-bold mb-6">California unclaimed property pipeline</h1>

<div class="bg-white rounded-xl border border-gray-200 p-6 max-w-3xl">
  <dl class="grid grid-cols-2 gap-y-3 text-sm">
    <dt class="text-gray-500">Records loaded</dt>
    <dd class="font-mono text-right">{{ "{:,}".format(total_rows) }}</dd>

    <dt class="text-gray-500">Total value indexed</dt>
    <dd class="font-mono text-right">${{ "{:,.0f}".format(total_value) }}</dd>

    <dt class="text-gray-500">Last refresh</dt>
    <dd class="font-mono text-right">{{ last_refresh or "(never)" }}</dd>
  </dl>
</div>

<h2 class="text-lg font-semibold mt-10 mb-3">Source files</h2>
<table class="w-full max-w-3xl text-sm bg-white rounded-xl border border-gray-200 overflow-hidden">
  <thead class="bg-gray-100 text-left">
    <tr>
      <th class="px-4 py-2">File</th>
      <th class="px-4 py-2 text-right">Rows</th>
      <th class="px-4 py-2 text-right">Loaded at</th>
      <th class="px-4 py-2">Status</th>
    </tr>
  </thead>
  <tbody>
    {% for run in runs %}
    <tr class="border-t border-gray-100">
      <td class="px-4 py-2 font-mono text-xs">{{ run.file_name }}</td>
      <td class="px-4 py-2 text-right font-mono">{{ "{:,}".format(run.rows_loaded or 0) }}</td>
      <td class="px-4 py-2 text-right text-gray-500">{{ run.completed_at }}</td>
      <td class="px-4 py-2">
        {% if run.status == 'completed' %}
          <span class="text-green-700">✓ {{ run.status }}</span>
        {% else %}
          <span class="text-red-700">✗ {{ run.status }}</span>
        {% endif %}
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<p class="mt-6 text-xs text-gray-400">
  Source: <a href="https://www.sco.ca.gov/upd_download_property_records.html" class="underline">California State Controller's Office</a> · Refresh: weekly (Thursdays)
</p>

{% endblock %}
```

- [ ] **Step 2: Add `/admin` route to `app/main.py`**

```python
@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    conn = get_connection()
    ensure_schema(conn)
    total_rows = conn.execute("SELECT COUNT(*) FROM ca_unclaimed").fetchone()[0]
    total_value_row = conn.execute(
        "SELECT COALESCE(SUM(amount_max), 0) FROM ca_unclaimed"
    ).fetchone()
    total_value = float(total_value_row[0]) if total_value_row else 0.0
    last_refresh_row = conn.execute(
        "SELECT MAX(completed_at) FROM ingest_runs WHERE status = 'completed'"
    ).fetchone()
    last_refresh = last_refresh_row[0] if last_refresh_row else None
    runs = conn.execute(
        """
        SELECT file_name, rows_loaded, completed_at, status
        FROM ingest_runs
        ORDER BY started_at DESC
        LIMIT 20
        """
    ).fetchall()
    runs_dicts = [
        {"file_name": r[0], "rows_loaded": r[1], "completed_at": r[2], "status": r[3]}
        for r in runs
    ]
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "total_rows": total_rows,
            "total_value": total_value,
            "last_refresh": last_refresh,
            "runs": runs_dicts,
        },
    )
```

- [ ] **Step 3: Smoke-test**

Run `python -m app.main`, open `http://127.0.0.1:8000/admin`. Expected: stats page with row count, total value, list of ingest runs.

- [ ] **Step 4: Commit**

```bash
git add app/main.py app/templates/admin.html
git commit -m "add /admin pipeline status page"
```

---

## Task 9: Executive deck (reveal.js, 9 slides)

**Files:**
- Create: `deck/index.html`
- Modify: `app/main.py` to serve the deck

- [ ] **Step 1: Create `deck/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SmartCredit Funds Finder — Executive Pitch</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reset.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css">
  <style>
    :root {
      --r-main-color: #0F172A;
      --r-heading-color: #0F172A;
      --r-link-color: #0066CC;
      --r-main-font: Inter, system-ui, sans-serif;
      --r-heading-font: Inter, system-ui, sans-serif;
    }
    .reveal h1, .reveal h2, .reveal h3 { font-weight: 700; }
    .reveal .big-number { font-size: 7rem; font-weight: 800; color: #0066CC; }
    .reveal .accent { color: #0066CC; }
    .reveal .muted { color: #64748B; }
    .reveal table { width: 100%; font-size: 0.7em; }
    .reveal table th, .reveal table td { padding: 8px 12px; border-bottom: 1px solid #E2E8F0; text-align: left; }
    .reveal .demo-frame { width: 100%; height: 70vh; border: 1px solid #E2E8F0; border-radius: 8px; }
    .reveal blockquote.callout { border-left: 4px solid #0066CC; padding: 0.5em 1em; background: #F1F5F9; font-style: normal; }
  </style>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
<div class="reveal"><div class="slides">

  <!-- 1. Title -->
  <section>
    <h1>Found Funds for SmartCredit Members</h1>
    <p class="muted">A new free feature that finds money the state owes them.</p>
    <aside class="notes">Open with a hook: "On average, every American household has $200+ they don't know about. Today I'll show you why we're uniquely positioned to give it back to them — and what it costs us to build."</aside>
  </section>

  <!-- 2. The problem -->
  <section>
    <h2>The problem</h2>
    <p class="big-number">$70B</p>
    <p>in unclaimed property sits with U.S. states.</p>
    <p class="muted">The average American household has ~$200 in unclaimed funds they don't know about. SmartCredit members trust us with their financial picture — they expect us to find this.</p>
    <aside class="notes">$70B is the official NAUPA-cited figure. Average $200 per household is a conservative estimate from state-level data.</aside>
  </section>

  <!-- 3. The opportunity -->
  <section>
    <h2>What's available today</h2>
    <table>
      <thead><tr><th></th><th>MissingMoney.com</th><th>BlueNavy</th><th class="accent">SmartCredit (us)</th></tr></thead>
      <tbody>
        <tr><td>Coverage</td><td>49 states (search only)</td><td>2 states</td><td class="accent">All 50 + federal (planned)</td></tr>
        <tr><td>Knows the user?</td><td>No</td><td>No (skip-trace required)</td><td class="accent">Yes — they're members</td></tr>
        <tr><td>User effort</td><td>Manual search</td><td>Sales outreach</td><td class="accent">Automatic</td></tr>
        <tr><td>Cost to user</td><td>Free</td><td>10–25% of recovered</td><td class="accent">Free</td></tr>
      </tbody>
    </table>
    <aside class="notes">We're not competing with MissingMoney's coverage on day 1; we're competing on user experience: MissingMoney makes you search, BlueNavy charges 10-25%, we just tell our members.</aside>
  </section>

  <!-- 4. Live demo -->
  <section>
    <h2>Live demo</h2>
    <iframe class="demo-frame" src="http://127.0.0.1:8000/"></iframe>
    <p class="muted" style="font-size:0.6em">Real California data — 1.8M+ records loaded from sco.ca.gov.</p>
    <aside class="notes">Walk through: enter a name, show the result list, click a claim link to claimit.ca.gov. If you have time, open /admin to show real ingestion stats.</aside>
  </section>

  <!-- 5. How it works -->
  <section>
    <h2>How it works</h2>
    <pre style="background:#F8FAFC; padding:1em; border-radius:8px; font-size:0.8em; line-height:1.6">
State data sources (CA, TX, NY, FL, …)
        │
        ▼
   Snowflake ingestion (weekly)
        │
        ▼
   Match against SmartCredit member roster
        │
        ▼
   Notify member in dashboard
        │
        ▼
   Deep-link to state claim portal
    </pre>
    <p class="muted">We don't handle claims — the state does. We surface the match.</p>
    <aside class="notes">Critical line: "we don't handle claims, the state does." That's what keeps us out of finder-service regulation.</aside>
  </section>

  <!-- 6. Why hard for others -->
  <section>
    <h2>Why this is hard for everyone else</h2>
    <blockquote class="callout">There is no MissingMoney API.</blockquote>
    <ul>
      <li>NAUPA is a government association, not a data vendor</li>
      <li>Kelmar Associates runs MissingMoney for the states — they don't license the data</li>
      <li>Only path: ingest state-by-state. ~50 distinct integrations.</li>
    </ul>
    <p class="accent">We already have the warehouse (Snowflake). We already have the user (members). The infrastructure cost is incremental, not greenfield.</p>
    <aside class="notes">This is the moat slide. Anyone could try to build this; we're advantaged because we already have the two hardest parts.</aside>
  </section>

  <!-- 7. Compliance moat -->
  <section>
    <h2>Compliance posture</h2>
    <ul style="font-size: 0.85em">
      <li>✓ <strong>FCRA-safe</strong> — unclaimed property search is not a credit-reporting activity</li>
      <li>✓ <strong>No finder license needed</strong> — we don't take a fee on claims (~30 states cap finder fees at 10%)</li>
      <li>✓ <strong>No new PII surface</strong> — reuses SmartCredit member identity controls</li>
      <li>✓ <strong>State data ToS</strong> — bulk file is publicly published by sco.ca.gov; we link claims back to the state portal</li>
    </ul>
    <p class="accent" style="margin-top: 1em">Free + deep-link = no new regulatory exposure.</p>
    <aside class="notes">Pre-empt the legal question. Free + deep-link is the structural choice that keeps this clean.</aside>
  </section>

  <!-- 8. Roadmap -->
  <section>
    <h2>Roadmap</h2>
    <table>
      <tbody>
        <tr><td><strong>Q3 2026</strong></td><td>CA + TX live (~25% of US population)</td></tr>
        <tr><td><strong>Q4 2026</strong></td><td>Top 10 states by population (~70% coverage)</td></tr>
        <tr><td><strong>Q1 2027</strong></td><td>Federal sources: Treasury, PBGC, FDIC, HUD, DOL</td></tr>
        <tr><td><strong>Q2 2027</strong></td><td>50-state coverage + member notification engine</td></tr>
      </tbody>
    </table>
    <aside class="notes">Each milestone gates the next. Q3 proves the pipeline; Q4 scales it; 2027 is breadth + activation.</aside>
  </section>

  <!-- 9. The ask -->
  <section>
    <h2>The ask</h2>
    <p style="font-size:1.2em; margin-bottom:1em">
      <span class="accent">1 data engineer</span> + <span class="accent">1 product engineer</span> · <span class="accent">~6 months to first live state</span>
    </p>
    <p><strong>Outcomes</strong></p>
    <ul>
      <li>A feature unique in the credit-monitoring market</li>
      <li>Measurable retention lift (every found-money notification is a "wow" moment)</li>
      <li>A reason for non-members to sign up</li>
    </ul>
    <aside class="notes">Land on the ask. Be specific: 2 engineers, 6 months, this is what we get. Don't end on hand-waving.</aside>
  </section>

</div></div>

<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/notes/notes.js"></script>
<script>
  Reveal.initialize({
    hash: true,
    transition: 'slide',
    plugins: [ RevealNotes ],
  });
</script>
</body>
</html>
```

- [ ] **Step 2: Mount the deck in `app/main.py`**

Add to `app/main.py`:
```python
DECK_DIR = BASE.parent / "deck"
app.mount("/deck", StaticFiles(directory=str(DECK_DIR), html=True), name="deck")
```

- [ ] **Step 3: Smoke-test the deck**

Run `python -m app.main`. Open `http://127.0.0.1:8000/deck/`. Expected:
- Slide 1 renders with title
- Arrow keys advance slides
- Slide 4 shows the live app inside the iframe
- Press `S` to open speaker-notes window

- [ ] **Step 4: Commit**

```bash
git add deck/index.html app/main.py
git commit -m "add 9-slide reveal.js executive deck with embedded live demo"
```

---

## Task 10: README runbook + final smoke test

**Files:**
- Modify: `README.md`
- Create: `scripts/refresh_data.py`

- [ ] **Step 1: Create `scripts/refresh_data.py`**

```python
"""CLI: refresh CA unclaimed property data.

Usage:
    python scripts/refresh_data.py
    python scripts/refresh_data.py --tier 04_From_500_To_Beyond.zip
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingest import TIERS, run

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", action="append", help="Specific tier zip filename (repeatable)")
    args = parser.parse_args()
    tiers = args.tier if args.tier else TIERS
    run(tiers)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Replace `README.md` with the full runbook**

```markdown
# CD Funds Finder

Local prototype: unclaimed-property search for SmartCredit members against California State Controller data, plus a 9-slide reveal.js executive deck with embedded live demo.

## Quick start

\`\`\`bash
# 1. Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Load California data (~3-5 min, downloads ~2-4 GB)
python -m app.ingest

# 3. Run the app + deck
python -m app.main
\`\`\`

- App: http://127.0.0.1:8000/
- Deck: http://127.0.0.1:8000/deck/
- Admin: http://127.0.0.1:8000/admin

## Demoing to execs

1. `python -m app.main` (leave it running in another terminal)
2. Open `http://127.0.0.1:8000/deck/` — full-screen
3. Slide 4 (Live Demo) embeds the search UI; type any name and run a search
4. Press `S` for speaker notes

## Refresh data

\`\`\`bash
python scripts/refresh_data.py
\`\`\`

## Architecture

- **App**: FastAPI + Jinja2 + htmx + Tailwind
- **Data**: DuckDB local file at `data/ca_unclaimed.duckdb` (Snowflake-shaped SQL)
- **Source**: California SCO bulk CSVs from <https://www.sco.ca.gov/upd_download_property_records.html>
- **Match**: `app/match.py` exposes a `MatchService` interface. Production swaps in Consumer Direct's existing matcher.

## Design

[`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md)

## Tests

\`\`\`bash
pytest -v
\`\`\`

## License

Internal — Consumer Direct.
```

- [ ] **Step 3: End-to-end smoke test**

```bash
# Fresh-clone simulation
deactivate 2>/dev/null || true
rm -rf .venv data/ca_unclaimed.duckdb
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v        # all tests should pass
python -m app.ingest  # full load (long-running)
python -m app.main &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/      # expect 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/admin # expect 200
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/deck/ # expect 200
kill %1
```

All four checks should pass: tests green, three HTTP 200s.

- [ ] **Step 4: Commit**

```bash
git add scripts/refresh_data.py README.md
git commit -m "add refresh_data CLI and full README runbook"
```

- [ ] **Step 5: Push**

```bash
git push -u origin main
```

---

## Out of scope (deferred to production)

- Snowflake migration — DuckDB queries port directly with minor dialect changes
- dbt models for canonical schema
- Production matcher integration — replace `DemoExactMatcher` with CD's existing service
- Tier 1 (`01_From_0_To_Below_10.zip`) — low signal-to-noise, skipped
- Other states — TX, NY, FL etc. follow the same pattern (download → unzip → COPY)
- Federal sources — Treasury, PBGC, FDIC, HUD, DOL, NCUA
- User auth / member identity pre-fill
- Notification engine
- Automated UI tests (manual smoke tests only for prototype)
