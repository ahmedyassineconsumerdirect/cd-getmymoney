# Get My Money Back

A SmartCredit feature (internal codename *myReclaim*) that finds unclaimed money
owed to members. It cross-checks a member's identity against official state
unclaimed-property records, surfaces **potential matches**, and guides the member
to file for free directly with the state — SmartCredit never holds funds or
charges a finder's fee.

This repo is the working prototype: a FastAPI + htmx app over California State
Controller data, a snapshot-diff that tracks new vs. already-claimed property,
**MaxAI** (an in-app assistant that can run live searches in other states), an
executive deck, and a proposed production-ingestion guide.

## Quick start

```bash
# 1. Install (Python 3.11+; 3.13 recommended)
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Load California data (one-time; downloads ~1 GB, final DuckDB ~12 GB)
python -m app.ingest

# 3. Build the snapshot-diff status table (tags each property new/claimed/active)
python scripts/build_ca_snapshot.py

# 4. Run the app (port 8000 conflicts with dbt; use 8088)
PORT=8088 python -m app.main
```

- App:   http://127.0.0.1:8088/
- MaxAI:  http://127.0.0.1:8088/assistant
- Admin:  http://127.0.0.1:8088/admin
- Deck:   http://127.0.0.1:8088/deck/

## How it works (member flow)

1. **Run your search** — a top-right popout: enter a name (a city narrows it).
2. **Review** — results are grouped into **Potential matches** (claimable, newest
   first with a ✦ New tag) and **Claimed history**, ranked by name closeness then
   ZIP. Long lists paginate 10 per page.
3. **Claim** — each match deep-links to the state's official portal; California
   claims typically process in ~30–180 days. A "step-by-step filing guide" link
   opens MaxAI's walkthrough.
4. **Monitor** — as states publish new records, new matches in your name surface
   automatically.

## Features

### Snapshot diff — match history
State files are republished periodically; comparing two dated snapshots on the
CA `PROPERTY_ID` classifies every property:

| status    | meaning                               | shown as            |
|-----------|---------------------------------------|---------------------|
| `active`  | in both snapshots, still claimable    | Potential matches   |
| `new`     | in the new file only (newly reported) | Potential + ✦ New   |
| `claimed` | in the old file only (gone → claimed) | Claimed history     |

Status lives in a small `property_status` table (`scripts/build_ca_snapshot.py`);
a record absent from it is implicitly `active`, so the 90M-row table is never
rewritten. The headline `$` counts claimable money only (new + active).

> Prototype note: with one loaded snapshot, the diff is synthesized
> deterministically so all sections demo. For a real diff, pass a prior id list:
> `python scripts/build_ca_snapshot.py --old-ids data/raw/prev_ids.txt`

### MaxAI assistant
A chat assistant as a **popout** (the "Ask Max" button, every page) and a full
**`/assistant`** page (`app/pine.py`, `app/assistant_kb.py`,
`app/static/js/assistant.js`):

- **Runs real California searches** inline — extracts a name, queries the local
  corpus, and returns ranked result cards.
- **Answers questions** (what is unclaimed property, how to file, is it free…)
  from a compliant knowledge base.
- **Other states:** by default it hands off to that state's official portal with
  filing steps. If a member **Connects MaxAI** (Pine's email-code auth, wired in
  the chat), MaxAI runs a *live* search of that state's portal in-chat — including
  auto-filling the portal's forms. Config via env: `PINE_ACCESS_TOKEN`,
  `PINE_USER_ID`, `PINE_BASE_URL`, `PINE_DEVICE_ID`; or connect from the UI.

### Unsupported-state handoff
Selecting a state we don't index yet returns a compliant, display-only handoff —
the state's official portal link + step-by-step filing instructions, from
`app/state_data.py` (50 states + DC).

## Demo customers (California, multi-status)
Curated so each spans both result sections — search first + last name:

- **Christa Villarosa** (Victorville) · **Boyd Gainor** (San Francisco)
- **Meena Fernandes** (Sunnyvale) · **Williams Dunshea** (Bakersfield)

Any name works (e.g. `David B Coulter` shows closest-match-then-ZIP ordering).

## Architecture

- **App:** FastAPI + Jinja2 + htmx + Tailwind (Play CDN); the assistant and
  search popout are vanilla JS.
- **Data:** DuckDB at `data/ca_unclaimed.duckdb` (Snowflake-shaped schema).
- **Source:** California SCO bulk CSVs (claimit.ca.gov).
- **Match:** `app/match.py` — `DemoFuzzyMatcher` behind a `MatchService` interface;
  full-recall contains scan ranked by name closeness (`relevance_score`), ZIP as
  tiebreak. Production swaps in Consumer Direct's Privacy Master engine.
- **Production target:** see `implementation-guideline/s3-data-ingestion.html`
  for the proposed S3 + Snowflake (dbt) ingestion design.

## Refresh data

```bash
python scripts/refresh_data.py        # all tiers
python scripts/build_ca_snapshot.py   # re-tag statuses after a refresh
```

Stop the app first — it holds a read-only lock; the refresh/snapshot scripts need
the write lock.

## Repo layout

```
app/                    FastAPI app (routes, matcher, presentation, MaxAI)
scripts/                ingest, snapshot diff, exec deck, MaxAI login
implementation-guideline/  S3 ingestion guide (HTML) + GetMyMoney exec deck
deck/                   reveal.js live demo deck
docs/                   spec, plan, compliance handoff
tests/                  pytest suite
```

## Tests

```bash
pytest -v
```

## License

Internal — Consumer Direct, Inc.
