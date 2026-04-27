from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="CD Funds Finder")

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>CD Funds Finder — alive</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
