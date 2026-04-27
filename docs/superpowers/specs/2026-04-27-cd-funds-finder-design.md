# CD Funds Finder — Design Spec

**Date**: 2026-04-27
**Author**: Ahmed Yassine (Consumer Direct)
**Status**: Approved for implementation

## Overview

Local prototype + executive presentation for a proposed SmartCredit feature that surfaces unclaimed property matches to members from California's State Controller database. Demonstrates the data ingestion pipeline, the search UX, and the productionization roadmap. Built to support an internal exec-team pitch for a multi-quarter program.

## Goals

- Run end-to-end on a single laptop with one command after `pip install`
- Use **real California unclaimed property data** (not synthetic) — millions of records pulled from sco.ca.gov (exact count surfaced on the admin page after first ingest)
- Visually resemble SmartCredit so execs see the feature in context
- Bundle a 9-slide reveal.js deck with embedded live demo for the exec pitch
- Code structure that translates directly to production (Snowflake + dbt + FastAPI)

## Non-goals

- Production-grade infrastructure (no Snowflake, no S3, no auth, no observability)
- Full 50-state coverage (CA only for the prototype)
- Phonetic / fuzzy name matching (Consumer Direct already has a matching service for data-broker workflows; the prototype uses an exact-match `MatchService` interface designed to be swapped)
- Claim filing automation (deep-link to claimit.ca.gov; the state handles claims)
- User authentication / member identification (the user fills in the form themselves; in production the form is pre-populated from member profile)

## Architecture

### Repository layout

```
cd-funds-finder/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry, routes, Jinja2 setup
│   ├── ingest.py            # Download CA zips, unzip, load into DuckDB
│   ├── match.py             # MatchService interface + DemoExactMatcher
│   ├── db.py                # DuckDB connection helper
│   ├── templates/
│   │   ├── base.html        # SmartCredit-styled layout (nav, footer)
│   │   ├── home.html        # Search form
│   │   ├── results.html     # Match results (htmx fragment)
│   │   └── admin.html       # Pipeline status page
│   └── static/
│       ├── css/             # Tailwind compiled
│       └── img/             # Logo, icons
├── deck/
│   ├── index.html           # reveal.js deck (CDN-served reveal)
│   └── assets/              # Slide images, charts
├── data/                    # Local DuckDB file (gitignored)
├── scripts/
│   └── refresh_data.py      # CLI re-download trigger
├── docs/
│   └── superpowers/specs/
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── README.md
```

### Tech stack

- **FastAPI** + **Uvicorn** — server
- **DuckDB** — local analytical store. SQL syntax aligns with Snowflake; same queries port directly.
- **Jinja2** templates + **htmx** for partial updates (no SPA framework needed)
- **Tailwind CSS** — compiled once, included as static asset (no npm pipeline at runtime)
- **reveal.js** via CDN — no build step for the deck
- **httpx** — CA file download
- **Python 3.11+**

### Why DuckDB

Local file-based, no external service. SQL syntax close enough to Snowflake that the queries used here port to production with minor changes (mainly date functions and dialect quirks). This makes the prototype a stepping-stone, not throwaway code.

## Data layer

### Source

California State Controller's Office publishes 5 ZIP files at `https://claimit.ca.gov/upd-property-records/`. Refreshed every Thursday. We ingest the high-value tiers:

| File | Coverage | Phase |
|---|---|---|
| `04_From_500_To_Beyond.zip` | $500+ | Load first (highest-value, smallest) |
| `03_From_100_To_Below_500.zip` | $100–$499.99 | Load second |
| `02_From_10_To_Below_100.zip` | $10–$99.99 | Load third |
| `01_From_0_To_Below_10.zip` | <$10 | Skip (low signal) |
| `00_All_Records.zip` | All tiers | Not used (we union the tiers above) |

The actual CSV column schema is not documented on the source page; `app/ingest.py` will inspect headers on first run and adapt.

### DuckDB schema (canonical)

```sql
CREATE TABLE ca_unclaimed (
    record_id            BIGINT PRIMARY KEY,
    holder_name          VARCHAR,
    holder_id            VARCHAR,
    owner_name           VARCHAR,
    owner_name_normalized VARCHAR,  -- UPPER + trimmed for matching
    last_known_address   VARCHAR,
    last_known_city      VARCHAR,
    last_known_state     VARCHAR,
    last_known_zip       VARCHAR,
    amount_min           DECIMAL(12,2),
    amount_max           DECIMAL(12,2),
    property_type        VARCHAR,
    reported_date        DATE,
    source_file          VARCHAR,
    ingested_at          TIMESTAMP
);

CREATE INDEX ix_owner_normalized ON ca_unclaimed(owner_name_normalized);

CREATE TABLE ingest_runs (
    run_id        VARCHAR PRIMARY KEY,
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    file_name     VARCHAR,
    etag          VARCHAR,
    rows_loaded   BIGINT,
    status        VARCHAR
);
```

### Ingestion flow

`python -m app.ingest` runs once on first install:

1. HEAD each tier URL, compare ETag against `ingest_runs` (skip if unchanged)
2. Download to `data/raw/{tier}/{yyyy-mm-dd}/data.zip`
3. Unzip, detect CSV schema from header row, write to staging
4. INSERT INTO `ca_unclaimed` with normalized columns
5. Record run in `ingest_runs`

Total time: ~2-5 minutes on a broadband connection.

## Match service

```python
# app/match.py

class MatchService(Protocol):
    def find_matches(
        self,
        first_name: str,
        last_name: str,
        dob: date | None = None,
        addresses: list[str] | None = None,
    ) -> list[Match]: ...

class DemoExactMatcher:
    """Exact match on UPPER(TRIM(owner_name)). Production swaps this
    out with Consumer Direct's existing data-broker matching service."""

    def find_matches(self, first_name, last_name, dob=None, addresses=None):
        normalized = f"{first_name} {last_name}".upper().strip()
        return self.db.execute(
            "SELECT * FROM ca_unclaimed WHERE owner_name_normalized = ? ORDER BY amount_max DESC",
            [normalized],
        ).fetchall()
```

Single interface. Production-ready replacement is a one-file change.

## UI / UX

### Page 1 — `GET /` Home + search

SmartCredit-styled layout. Hero text, search form (first name, last name, DOB, current ZIP, optional prior addresses), submit button. Visual language matches smartcredit.com (brand colors, font, nav structure extracted at build time).

### Page 2 — `POST /search` Results

htmx fragment loaded into the home page below the form. Lists matches with: holder name, property type, amount range, last-known address, "Claim at claimit.ca.gov" CTA. Empty state ("We didn't find anything in California — we're expanding to all 50 states") captures the no-match case gracefully.

### Page 3 — `GET /admin` Pipeline status

Read-only credibility page: last refresh timestamp, rows loaded, total value indexed, file ETags, per-tier load status. Exists so a curious exec can verify "is this real?" with concrete numbers.

### Visual styling

Tailwind CSS, brand alignment with smartcredit.com extracted during implementation:
- WebFetch smartcredit.com homepage during build to extract: primary brand color hex, font-family, header pattern, card border radius/shadow style
- Mirror nav structure (logo left, account menu right)
- Mirror card pattern from the existing member dashboard
- Fall back to Inter / system font stack if web font isn't easily reusable

## Executive deck

reveal.js deck at `GET /deck` (or `deck/index.html` standalone). 9 slides:

| # | Slide | Purpose |
|---|---|---|
| 1 | Title | Set context |
| 2 | The problem | $70B in unclaimed property; member trust expectation |
| 3 | The opportunity | Comparison vs. MissingMoney / BlueNavy |
| 4 | **Live Demo** | iframe of `localhost:8000/` — interact in-deck |
| 5 | How it works | Architecture diagram |
| 6 | Why hard for others | No public API; only path is state ingestion |
| 7 | Compliance moat | Free → no finder regulation; deep-links → no claim handling |
| 8 | Roadmap | Q3 2026 CA+TX live → Q4 top 10 states → 2027 federal sources + 50-state coverage |
| 9 | The ask | 1 data + 1 product engineer, ~6 months |

Speaker notes for each slide (reveal.js `S` shortcut). reveal.js loaded from CDN — no build step.

## Local dev experience

```bash
# First-time setup
git clone https://github.com/ahmedyassineconsumerdirect/cd-missing-funds-finder.git
cd cd-funds-finder
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# One-time data load (~2-5 min)
python -m app.ingest

# Run app + deck
python -m app.main
# → app at http://localhost:8000/
# → deck at http://localhost:8000/deck
```

`README.md` includes this runbook plus a 30-second demo script for the exec meeting.

## Error handling

- Ingest failures: log, mark run as `failed` in `ingest_runs`, exit non-zero
- Empty search: render empty-state template, no error
- DuckDB locked / not initialized: render friendly 503 page with "run `python -m app.ingest` first"
- Network failure during download: retry 3× with exponential backoff, then fail with clear error

## Testing

Manual smoke test only for the prototype:
1. `python -m app.ingest` succeeds, reports >1M rows loaded
2. `/admin` shows correct counts
3. Searching a name with no CA records → empty-state message
4. Searching a name that matches → results render with claim deep-link
5. Deck loads at `/deck`, slide 4 iframe shows the live app

No automated test suite — the prototype's lifespan ends when production work begins. Production version gets full pytest coverage.

## Out of scope (deferred to production)

- Snowflake migration (DuckDB → Snowflake stage + COPY INTO)
- dbt models for canonical schema
- Production matching (CD's existing service plugged into `MatchService`)
- All states beyond California
- Federal sources (Treasury, PBGC, FDIC, HUD, DOL, NCUA)
- User auth / member identification
- Member notification engine (email/SMS when new matches found)
- Claim assistance flow

## Open questions / future work

- Specific SmartCredit brand assets (logo file, exact hex codes) — extract from smartcredit.com during build
- Whether to embed the live demo via iframe in slide 4 or via Playwright screenshot if the laptop network blocks localhost in the meeting room
- Data refresh cadence in prototype (probably weekly via manual `python -m app.ingest`; production uses scheduled task)
