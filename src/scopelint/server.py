from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from scopelint.checker import ScopeFinding
from scopelint.dashboard import render_html, summarize
from scopelint.db import Team, get_team_by_api_key, insert_check, list_checks
from scopelint.history import HistoryEntry


def _authenticate(db_path: str, api_key: str | None) -> Team:
    team = get_team_by_api_key(db_path, api_key) if api_key else None
    if team is None:
        raise HTTPException(status_code=401, detail="invalid or missing API key")
    return team


def create_app(db_path: str) -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/ingest", status_code=201)
    def ingest(entry: HistoryEntry, x_api_key: str | None = Header(default=None)) -> dict:
        team = _authenticate(db_path, x_api_key)
        insert_check(db_path, team.id, entry)
        return {"status": "recorded"}

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(x_api_key: str | None = Header(default=None)) -> str:
        team = _authenticate(db_path, x_api_key)
        entries = list_checks(db_path, team.id)
        return render_html(summarize(entries))

    return app
