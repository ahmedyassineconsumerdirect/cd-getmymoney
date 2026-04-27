# CD Funds Finder

Local prototype: unclaimed-property search for SmartCredit members against California State Controller data + a 9-slide executive deck.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.ingest          # one-time, ~2-5 min
python -m app.main            # serves at http://127.0.0.1:8000
```

- App: http://127.0.0.1:8000
- Deck: http://127.0.0.1:8000/deck
- Admin: http://127.0.0.1:8000/admin

## Design

See [`docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md`](docs/superpowers/specs/2026-04-27-cd-funds-finder-design.md).
