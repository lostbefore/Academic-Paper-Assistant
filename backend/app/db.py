"""SQLite persistence layer.

The application keeps a single SQLite database in ``DATA_DIR``.  A connection
is opened per operation (SQLite handles this cheaply, and it keeps the code
thread-safe without a connection pool); WAL mode is enabled for concurrency.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from .config import get_settings

_init_lock = threading.Lock()
_initialised = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',
    created_at    TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS papers (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,
    title          TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'queued',
    stage          TEXT NOT NULL DEFAULT '',
    progress       INTEGER NOT NULL DEFAULT 0,
    request_json   TEXT NOT NULL DEFAULT '{}',
    outline_json   TEXT NOT NULL DEFAULT '{}',
    sections_json  TEXT NOT NULL DEFAULT '{}',
    refs_json      TEXT NOT NULL DEFAULT '[]',
    meta_json      TEXT NOT NULL DEFAULT '{}',
    error          TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL,
    finished_at    TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_papers_user ON papers(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);

CREATE TABLE IF NOT EXISTS events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    ts       TEXT NOT NULL,
    stage    TEXT NOT NULL DEFAULT '',
    level    TEXT NOT NULL DEFAULT 'info',
    message  TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_paper ON events(paper_id, id);

CREATE TABLE IF NOT EXISTS literature_cache (
    key        TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _db_path() -> Path:
    return get_settings().DB_PATH


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """Yield a connection with row access by name and foreign keys enabled."""
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    global _initialised
    with _init_lock:
        with connect() as conn:
            conn.executescript(SCHEMA)
        _initialised = True


def fetch_one(sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    with connect() as conn:
        return conn.execute(sql, tuple(params)).fetchone()


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    with connect() as conn:
        return list(conn.execute(sql, tuple(params)).fetchall())


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """Run a write statement and return ``lastrowid`` (or rowcount)."""
    with connect() as conn:
        cur = conn.execute(sql, tuple(params))
        return int(cur.lastrowid or cur.rowcount or 0)


def executemany(sql: str, rows: Iterable[Iterable[Any]]) -> None:
    with connect() as conn:
        conn.executemany(sql, [tuple(r) for r in rows])


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default if default is not None else {}
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default if default is not None else {}
