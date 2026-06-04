from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db import get_connection
from app.match import DemoExactMatcher
from app import presentation
from app.pine import assistant, PineError
from app.assistant_kb import KB as _ASSISTANT_KB

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

# Presentation filters — decode raw NAUPA codes / ALL-CAPS strings into
# member-facing labels. Used heavily in _results.html.
templates.env.filters["friendly_property"] = presentation.friendly_property
templates.env.filters["pretty_holder"] = presentation.pretty_holder
templates.env.filters["pretty_name"] = presentation.pretty_name
templates.env.filters["pretty_city"] = presentation.pretty_city
templates.env.globals["render_icon"] = presentation.render_icon
# Assistant boot data for the popout/page (static greeting + starter chips).
templates.env.globals["assistant_greeting"] = _ASSISTANT_KB["greeting"]
# Lead with a search starter so members discover the live lookup.
templates.env.globals["assistant_prompts"] = [
    "Find unclaimed property in my name",
    *_ASSISTANT_KB["suggested_prompts"],
]

app = FastAPI(title="CD Funds Finder")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

DECK_DIR = BASE.parent / "deck"
app.mount("/deck", StaticFiles(directory=str(DECK_DIR), html=True), name="deck")


_conn = None
def _get_match_service():
    global _conn
    if _conn is None:
        # The app only reads; a read-only connection allows concurrent readers
        # and lets refresh/snapshot scripts hold the write lock independently.
        # The production DB already carries the schema (see scripts/).
        _conn = get_connection(read_only=True)
    return DemoExactMatcher(_conn)


@app.on_event("startup")
def _warm_cache():
    """Page the owner-name column into OS cache in the background so the first
    real search isn't a cold ~30s full scan. Non-blocking; own connection."""
    import threading

    def _warm():
        try:
            c = get_connection(read_only=True)
            c.execute(
                "SELECT COUNT(*) FROM ca_unclaimed "
                "WHERE owner_name_normalized LIKE '%zzqx%'"
            ).fetchone()
            c.close()
        except Exception:
            pass

    threading.Thread(target=_warm, daemon=True).start()


@app.on_event("startup")
def _maxai_status():
    import logging
    st = assistant.status()
    logging.getLogger("maxai").info(
        "MaxAI ready — mode=%s, saved confirmation code=%s. "
        "Live Pine relay activates with a valid access token; if the code expires you'll be prompted here.",
        st["mode"], "yes" if st.get("has_code") else "no",
    )


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/search", response_class=HTMLResponse)
def search(
    request: Request,
    first_name: str = Form(""),
    last_name: str = Form(""),
    city: str = Form(""),
    state: str = Form(""),
):
    state_code = state.strip().upper()
    # Only treat known US state codes as a state selection. Unknown/crafted
    # values are ignored (never reflected into the handoff template, which would
    # otherwise be an injection vector) — we just run a normal name search.
    known_state = state_code in presentation.ALL_STATE_CODES

    # A known state we don't yet index -> hand the member off to that state's
    # official portal with filing steps, rather than running an empty search.
    if known_state and state_code not in presentation.SUPPORTED_STATES:
        return templates.TemplateResponse(
            "_state_unsupported.html",
            {"request": request, "state": presentation.state_info(state_code)},
        )

    matcher = _get_match_service()
    matches = matcher.find_matches(
        first_name=first_name,
        last_name=last_name,
        city=city.strip() or None,
        state=state_code if known_state else None,
    )

    # Bucket by snapshot-diff status into the three result sections. Totals are
    # derived from the buckets so the headline can never disagree with what is
    # rendered.
    # All claimable rows are "potential matches" (new + active), kept in the
    # matcher's closeness order (like the state portal). Claimed = history.
    potential_matches = [m for m in matches if m.claimable]
    claimed_matches = [m for m in matches if not m.claimable]
    claimable_total = sum((m.amount_max or 0) for m in potential_matches)  # never counts claimed
    has_input = any(v.strip() for v in (first_name, last_name, city, state))
    return templates.TemplateResponse(
        "_results.html",
        {
            "request": request,
            "matches": matches,
            "potential_matches": potential_matches,
            "claimed_matches": claimed_matches,
            "claimable_total": claimable_total,
            "claimable_count": len(potential_matches),
            "has_input": has_input,
        },
    )


@app.get("/assistant", response_class=HTMLResponse)
def assistant_page(request: Request):
    return templates.TemplateResponse(
        "assistant.html",
        {"request": request, "status": assistant.status()},
    )


class _MsgIn(BaseModel):
    message: str = ""


class _EmailIn(BaseModel):
    email: str = ""


class _VerifyIn(BaseModel):
    email: str = ""
    code: str = ""


@app.get("/assistant/status")
def assistant_status():
    return assistant.status()


@app.post("/assistant/message")
def assistant_message(body: _MsgIn):
    return assistant.reply(body.message)


@app.post("/assistant/connect/request")
def assistant_connect_request(body: _EmailIn):
    try:
        return assistant.connect_request(body.email)
    except PineError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception:
        return JSONResponse(
            {"ok": False, "error": "Couldn't reach Pine right now. Local search still works."},
            status_code=502,
        )


@app.post("/assistant/connect/verify")
def assistant_connect_verify(body: _VerifyIn):
    try:
        return assistant.connect_verify(body.email, body.code)
    except PineError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
    except Exception:
        return JSONResponse({"ok": False, "error": "Verification failed. Please try again."}, status_code=502)


@app.post("/assistant/disconnect")
def assistant_disconnect():
    return assistant.disconnect()


def _fmt_dt(dt) -> str | None:
    if dt is None:
        return None
    try:
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except AttributeError:
        return str(dt)


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    conn = get_connection(read_only=True)
    try:
        total_rows = conn.execute("SELECT COUNT(*) FROM ca_unclaimed").fetchone()[0]
        total_value_row = conn.execute(
            "SELECT COALESCE(SUM(amount_max), 0) FROM ca_unclaimed"
        ).fetchone()
        total_value = float(total_value_row[0]) if total_value_row else 0.0
        last_refresh_row = conn.execute(
            "SELECT MAX(completed_at) FROM ingest_runs WHERE status = 'completed'"
        ).fetchone()
        last_refresh = _fmt_dt(last_refresh_row[0]) if last_refresh_row else None
        runs = conn.execute(
            """
            SELECT file_name, rows_loaded, completed_at, status
            FROM ingest_runs
            ORDER BY started_at DESC
            LIMIT 20
            """
        ).fetchall()
        runs_dicts = [
            {
                "file_name": r[0],
                "rows_loaded": r[1],
                "completed_at": _fmt_dt(r[2]),
                "status": r[3],
            }
            for r in runs
        ]
    finally:
        conn.close()
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


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
