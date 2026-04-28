from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.db import get_connection, ensure_schema
from app.match import DemoExactMatcher

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))

app = FastAPI(title="CD Funds Finder")
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


_conn = None
def _get_match_service():
    global _conn
    if _conn is None:
        _conn = get_connection()
        ensure_schema(_conn)
    return DemoExactMatcher(_conn)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


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


def _fmt_dt(dt) -> str | None:
    if dt is None:
        return None
    try:
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except AttributeError:
        return str(dt)


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    conn = get_connection()
    try:
        ensure_schema(conn)
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
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
