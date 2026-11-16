# 附录 C · 数据库结构（SQLite）

> 由 `sqlite_master` 直接导出，与实际运行库一致。

## TABLE `events`

```sql
CREATE TABLE events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL,
    ts       TEXT NOT NULL,
    stage    TEXT NOT NULL DEFAULT '',
    level    TEXT NOT NULL DEFAULT 'info',
    message  TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}'
);
```

## TABLE `literature_cache`

```sql
CREATE TABLE literature_cache (
    key        TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
```

## TABLE `papers`

```sql
CREATE TABLE papers (
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
```

## TABLE `sqlite_sequence`

```sql
CREATE TABLE sqlite_sequence(name,seq);
```

## TABLE `users`

```sql
CREATE TABLE users (
    id            TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',
    created_at    TEXT NOT NULL,
    last_login_at TEXT
);
```

## INDEX `idx_events_paper`

```sql
CREATE INDEX idx_events_paper ON events(paper_id, id);
```

## INDEX `idx_papers_status`

```sql
CREATE INDEX idx_papers_status ON papers(status);
```

## INDEX `idx_papers_user`

```sql
CREATE INDEX idx_papers_user ON papers(user_id, created_at DESC);
```

