# CD Funds Finder

Local prototype: unclaimed-property search for SmartCredit members against California State Controller data, plus a 9-slide reveal.js executive deck with embedded live demo.

## Quick start

```bash
# 1. Install (Python 3.11+ required; 3.13 recommended)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Load California data (one-time)
#    Takes 20–40 minutes; downloads ~1 GB; final DuckDB file is ~3-5 GB after all tiers load
python -m app.ingest

# 3. Run the app + deck
python -m app.main
```

- App: http://127.0.0.1:8000/
- Deck: http://127.0.0.1:8000/deck/
- Admin: http://127.0.0.1:8000/admin

## Demoing to execs

1. `python -m app.main` (leave it running in another terminal)
2. Open `http://127.0.0.1:8000/deck/` — full-screen
3. Slide 4 (Live Demo) embeds the search UI; type any name and run a search
4. Press `S` for speaker notes

## Refresh data

```bash
python scripts/refresh_data.py
# Or, just one tier:
python scripts/refresh_data.py --tier 04_From_500_To_Beyond.zip
```

## Architecture

- **App**: FastAPI + Jinja2 + htmx + Tailwind (Play CDN)
- **Data**: DuckDB local file at `data/ca_unclaimed.duckdb` (Snowflake-shaped SQL)
- **Source**: California SCO bulk CSVs from <https://www.sco.ca.gov/upd_download_property_records.html>
- **Match**: `app/match.py` exposes a `MatchService` interface. Production swaps in Consumer Direct's existing matcher.

## Design

[`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md)

## Tests

```bash
pytest -v
```

## License

Internal — Consumer Direct.
