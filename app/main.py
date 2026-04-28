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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
