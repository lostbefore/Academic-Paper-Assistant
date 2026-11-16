"""Generate appendix data (code stats, API list, schema, file inventory).

Run from the repository root:
    python docs/build_appendix.py
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DATA_DIR", str(ROOT / "data"))

DOCS_ROOT = ROOT / "docs"
OUT = DOCS_ROOT / "appendix"
OUT.mkdir(parents=True, exist_ok=True)

SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", ".venv", "data", "shots"}
LANG = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript (React)",
    ".css": "CSS",
    ".md": "Markdown",
    ".json": "JSON",
    ".sh": "Shell",
    ".html": "HTML",
    ".yml": "YAML",
    ".service": "systemd",
}


def iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix not in LANG:  # skip binaries, images and secrets
            continue
        if path.name.startswith(".env"):
            continue
        if path.name in {"package-lock.json", "pnpm-lock.yaml"}:
            continue
        yield path


def line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except OSError:
        return 0


def code_stats() -> None:
    rows = []
    totals = {}
    for path in iter_files(ROOT):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == "legacy":
            group = "legacy（v1 归档）"
        elif rel.parts[0] in ("backend", "frontend", "docs", "deploy"):
            group = rel.parts[0]
        else:
            group = "根目录"
        lang = LANG.get(path.suffix, "其他")
        lines = line_count(path)
        totals[group] = totals.get(group, 0) + lines
        rows.append((str(rel).replace("\\", "/"), lang, path.stat().st_size, lines))

    with (OUT / "A-代码统计.md").open("w", encoding="utf-8") as fh:
        fh.write("# 附录 A · 代码与文件统计\n\n")
        fh.write(f"> 统计时间：2026-11-16　统计范围：仓库工作区（不含 .git / node_modules / dist / data）\n\n")
        fh.write("## A.1 按模块汇总\n\n| 模块 | 行数 |\n|---|---:|\n")
        for group, lines in sorted(totals.items(), key=lambda kv: -kv[1]):
            fh.write(f"| {group} | {lines} |\n")
        fh.write(f"| **合计** | **{sum(totals.values())}** |\n\n")
        fh.write("## A.2 文件明细\n\n| 文件 | 类型 | 字节 | 行数 |\n|---|---|---:|---:|\n")
        for rel, lang, size, lines in sorted(rows):
            fh.write(f"| `{rel}` | {lang} | {size} | {lines} |\n")
    print("wrote", OUT / "A-代码统计.md", "files:", len(rows))


def api_list() -> None:
    from app.main import app  # noqa: WPS433

    schema = app.openapi()
    entries = []
    for path, operations in schema.get("paths", {}).items():
        for method, operation in operations.items():
            if method.upper() in {"HEAD", "OPTIONS", "PARAMETERS"}:
                continue
            entries.append(
                (path, method.upper(), (operation.get("summary") or "").strip())
            )
    entries.sort(key=lambda row: (row[0], row[1]))
    with (OUT / "B-接口清单.md").open("w", encoding="utf-8") as fh:
        fh.write("# 附录 B · HTTP 接口清单\n\n")
        fh.write(f"> 由 FastAPI 自动生成的 OpenAPI 文档导出，共 {len(entries)} 个接口。交互式文档见部署实例 `/api/docs`。\n\n")
        fh.write("| 方法 | 路径 | 说明 |\n|---|---|---|\n")
        for path, method, summary in entries:
            fh.write(f"| {method} | `{path}` | {summary or '—'} |\n")
    print("wrote", OUT / "B-接口清单.md", "routes:", len(entries))


def schema_dump() -> None:
    from app import db  # noqa: WPS433

    db.init_db()
    conn = sqlite3.connect(db.get_settings().DB_PATH)
    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type DESC, name"
    ).fetchall()
    with (OUT / "C-数据库结构.md").open("w", encoding="utf-8") as fh:
        fh.write("# 附录 C · 数据库结构（SQLite）\n\n")
        fh.write("> 由 `sqlite_master` 直接导出，与实际运行库一致。\n\n")
        for kind, name, sql in rows:
            fh.write(f"## {kind.upper()} `{name}`\n\n```sql\n{sql.strip()};\n```\n\n")
    print("wrote", OUT / "C-数据库结构.md", "objects:", len(rows))


def git_log() -> None:
    try:
        log = subprocess.run(
            ["git", "log", "--reverse", "--date=iso", "--format=%h|%ad|%an|%s"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:  # pragma: no cover
        log = f"(git unavailable: {exc})"
    with (OUT / "D-提交历史.md").open("w", encoding="utf-8") as fh:
        fh.write("# 附录 D · 版本库提交历史\n\n")
        fh.write("> 由 `git log` 导出，用于核对开发时间线。\n\n")
        fh.write("| 提交 | 时间 | 作者 | 说明 |\n|---|---|---|---|\n")
        for line in log.splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                fh.write(f"| `{parts[0]}` | {parts[1]} | {parts[2]} | {parts[3]} |\n")
    print("wrote", OUT / "D-提交历史.md")


def doc_inventory() -> None:
    """List every documentation file with size, hash and mtime.

    This is the literal "file record" of the documentation set: it lets a
    reviewer verify that the compiled PDF was produced from exactly these
    files.
    """
    import hashlib
    from datetime import datetime

    rows = []
    for path in sorted(DOCS_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in {".md", ".py", ".txt", ".png", ".jpg"}:
            continue
        if path.name in {"docs-bundle.html"}:
            continue
        rel = path.relative_to(DOCS_ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        if path.suffix in {".md", ".py", ".txt"}:
            lines = len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
        else:
            lines = 0
        rows.append((rel, path.suffix.lstrip(".").upper(), lines, path.stat().st_size, digest, mtime))

    total_bytes = sum(r[3] for r in rows)
    text_files = [r for r in rows if r[1] in {"MD", "PY", "TXT"}]
    images = [r for r in rows if r[1] in {"PNG", "JPG"}]

    with (OUT / "F-文档清单.md").open("w", encoding="utf-8") as fh:
        fh.write("# 附录 F · 文档文件清单\n\n")
        fh.write(
            "> 本清单由脚本扫描 `docs/` 目录自动生成，记录每个文档文件的类型、行数、字节数、"
            "SHA-256 前 16 位与最后修改时间，用于核对本 PDF 的汇编来源。\n\n"
        )
        fh.write(
            f"合计 {len(rows)} 个文件（文档 {len(text_files)} 个、图片 {len(images)} 个），"
            f"共 {total_bytes / 1024:.1f} KB。\n\n"
        )
        fh.write("| 文件 | 类型 | 行数 | 字节 | SHA-256 | 修改时间 |\n")
        fh.write("|---|---|---:|---:|---|---|\n")
        for rel, kind, lines, size, digest, mtime in rows:
            line_cell = str(lines) if lines else "—"
            fh.write(f"| `{rel}` | {kind} | {line_cell} | {size} | `{digest}` | {mtime} |\n")
        fh.write(
            "\n> 说明：编译生成的 PDF 与 HTML 不列入本表（避免自引用）；"
            "表中哈希值取 SHA-256 前 16 位，足以判断文件是否被改动。\n"
        )
    print("wrote", OUT / "F-文档清单.md", "files:", len(rows))


if __name__ == "__main__":
    code_stats()
    api_list()
    schema_dump()
    git_log()
    doc_inventory()
