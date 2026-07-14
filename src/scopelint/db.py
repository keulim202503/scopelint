import json
import secrets
import sqlite3
from contextlib import closing
from dataclasses import asdict, dataclass

from scopelint.checker import ScopeFinding
from scopelint.history import HistoryEntry

_SCHEMA = """
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    timestamp TEXT NOT NULL,
    task TEXT NOT NULL,
    ok INTEGER NOT NULL,
    findings TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class Team:
    id: int
    name: str
    api_key: str


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA)
    return conn


def create_team(db_path: str, name: str) -> Team:
    api_key = secrets.token_urlsafe(32)
    with closing(_connect(db_path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO teams (name, api_key) VALUES (?, ?)", (name, api_key)
        )
        team_id = cursor.lastrowid
    return Team(id=team_id, name=name, api_key=api_key)


def get_team_by_api_key(db_path: str, api_key: str) -> Team | None:
    with closing(_connect(db_path)) as conn:
        row = conn.execute(
            "SELECT id, name, api_key FROM teams WHERE api_key = ?", (api_key,)
        ).fetchone()
    if row is None:
        return None
    return Team(id=row[0], name=row[1], api_key=row[2])


def insert_check(db_path: str, team_id: int, entry: HistoryEntry) -> None:
    findings_json = json.dumps([asdict(f) for f in entry.findings], ensure_ascii=False)
    with closing(_connect(db_path)) as conn, conn:
        conn.execute(
            "INSERT INTO checks (team_id, timestamp, task, ok, findings) VALUES (?, ?, ?, ?, ?)",
            (team_id, entry.timestamp, entry.task, int(entry.ok), findings_json),
        )


def list_checks(db_path: str, team_id: int) -> list[HistoryEntry]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT timestamp, task, ok, findings FROM checks WHERE team_id = ? ORDER BY id",
            (team_id,),
        ).fetchall()
    return [
        HistoryEntry(
            timestamp=row[0],
            task=row[1],
            ok=bool(row[2]),
            findings=[ScopeFinding(path=f["path"], reason=f["reason"]) for f in json.loads(row[3])],
        )
        for row in rows
    ]
