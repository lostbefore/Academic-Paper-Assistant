"""Paper CRUD, generation control, event streaming and exports."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from .. import db
from ..config import get_settings
from ..deps import current_user, owned_paper
from ..schemas import (
    PaperCreateRequest,
    PaperPatchRequest,
    RegenerateSectionRequest,
    SectionUpdateRequest,
    StatsOut,
)
from ..services import export as exporter
from ..services import pipeline
from ..services.llm import LLMError

router = APIRouter(prefix="/api", tags=["papers"])

TERMINAL = {"completed", "failed", "cancelled"}


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

def _word_count(sections: Dict[str, str]) -> int:
    return sum(
        pipeline.word_count(value)
        for key, value in sections.items()
        if key not in ("references", "title")
    )


def _summary(row: Dict[str, Any]) -> Dict[str, Any]:
    request = db.loads(row.get("request_json"), {})
    sections = db.loads(row.get("sections_json"), {})
    meta = db.loads(row.get("meta_json"), {})
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "stage": row["stage"],
        "progress": row["progress"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "language": request.get("language", "en"),
        "citation_style": request.get("citation_style", "gbt7714"),
        "word_count": int(meta.get("word_count") or _word_count(sections)),
        "error": row.get("error") or "",
    }


def _detail(row: Dict[str, Any]) -> Dict[str, Any]:
    request = db.loads(row.get("request_json"), {})
    sections = db.loads(row.get("sections_json"), {})
    meta = db.loads(row.get("meta_json"), {})
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "stage": row["stage"],
        "progress": row["progress"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "finished_at": row.get("finished_at"),
        "error": row.get("error") or "",
        "request": request,
        "outline": db.loads(row.get("outline_json"), {}),
        "sections": sections,
        "references": db.loads(row.get("refs_json"), []),
        "meta": meta,
        "images": meta.get("images", []),
        "word_count": int(meta.get("word_count") or _word_count(sections)),
    }


def _load(paper_id: str, user: dict) -> Dict[str, Any]:
    return _detail(owned_paper(paper_id, user))


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get("/papers")
def list_papers(
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    user: dict = Depends(current_user),
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM papers WHERE user_id = ?"
    params: List[Any] = [user["id"]]
    if status:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND title LIKE ?"
        params.append(f"%{q}%")
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return [_summary(dict(row)) for row in db.fetch_all(sql, params)]


@router.post("/papers", status_code=202)
async def create_paper(payload: PaperCreateRequest, user: dict = Depends(current_user)) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.llm_configured:
        raise HTTPException(
            status_code=503,
            detail="The language model is not configured on this server. Set LLM_API_KEY in .env.",
        )
    count = db.fetch_one("SELECT COUNT(*) AS c FROM papers WHERE user_id = ?", (user["id"],))
    if count and count["c"] >= settings.MAX_PAPERS_PER_USER:
        raise HTTPException(status_code=429, detail="Paper limit reached for this account")

    paper_id = f"p_{uuid.uuid4().hex[:12]}"
    request = payload.model_dump()
    now = db.utcnow()
    db.execute(
        """INSERT INTO papers
           (id, user_id, title, status, stage, progress, request_json, outline_json,
            sections_json, refs_json, meta_json, error, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            paper_id, user["id"], payload.title.strip(), "queued", "queued", 0,
            db.dumps(request), "{}", "{}", "[]", "{}", "", now, now,
        ),
    )
    pipeline.log_event(paper_id, "queued", "Queued for generation", progress=0)
    pipeline.job_manager.start(paper_id)
    row = dict(db.fetch_one("SELECT * FROM papers WHERE id = ?", (paper_id,)))
    return _detail(row)


@router.get("/papers/{paper_id}")
def get_paper(paper_id: str, user: dict = Depends(current_user)) -> Dict[str, Any]:
    return _load(paper_id, user)


@router.patch("/papers/{paper_id}")
def patch_paper(
    paper_id: str, payload: PaperPatchRequest, user: dict = Depends(current_user)
) -> Dict[str, Any]:
    row = owned_paper(paper_id, user)
    fields: Dict[str, Any] = {}
    if payload.title:
        fields["title"] = payload.title.strip()
    if payload.sections is not None:
        current = db.loads(row["sections_json"], {})
        current.update({k: v for k, v in payload.sections.items() if isinstance(v, str)})
        fields["sections_json"] = db.dumps(current)
    if not fields:
        return _detail(dict(row))
    fields["updated_at"] = db.utcnow()
    columns = ", ".join(f"{name} = ?" for name in fields)
    db.execute(f"UPDATE papers SET {columns} WHERE id = ?", (*fields.values(), paper_id))
    pipeline.log_event(paper_id, "edit", "Paper updated manually")
    return _load(paper_id, user)


@router.delete("/papers/{paper_id}", status_code=204)
def delete_paper(paper_id: str, user: dict = Depends(current_user)) -> None:
    owned_paper(paper_id, user)
    pipeline.job_manager.cancel(paper_id)
    db.execute("DELETE FROM events WHERE paper_id = ?", (paper_id,))
    db.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    for suffix in (".docx", ".pdf", ".md", ".bib"):
        cached = get_settings().DATA_DIR / "exports" / f"{paper_id}{suffix}"
        cached.unlink(missing_ok=True)


@router.post("/papers/{paper_id}/cancel")
def cancel_paper(paper_id: str, user: dict = Depends(current_user)) -> Dict[str, Any]:
    row = owned_paper(paper_id, user)
    if row["status"] in TERMINAL:
        raise HTTPException(status_code=409, detail="Paper is already finished")
    pipeline.job_manager.cancel(paper_id)
    return _load(paper_id, user)


@router.post("/papers/{paper_id}/retry")
async def retry_paper(paper_id: str, user: dict = Depends(current_user)) -> Dict[str, Any]:
    row = owned_paper(paper_id, user)
    if row["status"] not in TERMINAL:
        raise HTTPException(status_code=409, detail="Paper is still running")
    db.execute(
        "UPDATE papers SET status='queued', stage='queued', progress=0, error='', updated_at=? WHERE id=?",
        (db.utcnow(), paper_id),
    )
    db.execute("DELETE FROM events WHERE paper_id = ?", (paper_id,))
    pipeline.log_event(paper_id, "queued", "Retrying generation", progress=0)
    pipeline.job_manager.start(paper_id)
    return _load(paper_id, user)


@router.put("/papers/{paper_id}/sections/{section_key}")
def update_section(
    paper_id: str,
    section_key: str,
    payload: SectionUpdateRequest,
    user: dict = Depends(current_user),
) -> Dict[str, Any]:
    row = owned_paper(paper_id, user)
    sections = db.loads(row["sections_json"], {})
    sections[section_key] = payload.content
    db.execute(
        "UPDATE papers SET sections_json = ?, updated_at = ? WHERE id = ?",
        (db.dumps(sections), db.utcnow(), paper_id),
    )
    pipeline.log_event(paper_id, "edit", f"Edited section: {section_key}", data={"section": section_key})
    return _load(paper_id, user)


@router.post("/papers/{paper_id}/sections/{section_key}/regenerate")
async def regenerate_section(
    paper_id: str,
    section_key: str,
    payload: Optional[RegenerateSectionRequest] = None,
    user: dict = Depends(current_user),
) -> Dict[str, Any]:
    row = owned_paper(paper_id, user)
    if row["status"] not in TERMINAL:
        raise HTTPException(status_code=409, detail="Wait for generation to finish first")
    try:
        text = await pipeline.regenerate_section(
            paper_id, section_key, (payload.instructions if payload else "") or ""
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"section": section_key, "content": text, "paper": _load(paper_id, user)}


# ---------------------------------------------------------------------------
# Events (Server-Sent Events)
# ---------------------------------------------------------------------------

def _event_payload(row: Any) -> str:
    return json.dumps(
        {
            "id": row["id"],
            "ts": row["ts"],
            "stage": row["stage"],
            "level": row["level"],
            "message": row["message"],
            "data": db.loads(row["data_json"], {}),
        },
        ensure_ascii=False,
    )


def _sse(data: str, event: str = "message", event_id: Optional[int] = None) -> str:
    prefix = f"id: {event_id}\n" if event_id is not None else ""
    return f"{prefix}event: {event}\ndata: {data}\n\n"


@router.get("/papers/{paper_id}/events")
async def paper_events(
    paper_id: str,
    request: Request,
    after: int = Query(default=0, ge=0),
    token: Optional[str] = None,
) -> StreamingResponse:
    # Accept a token query parameter because EventSource cannot send headers.
    user: Optional[dict] = None
    if token:
        from ..security import decode_access_token

        try:
            payload = decode_access_token(token)
            row = db.fetch_one("SELECT * FROM users WHERE id = ?", (payload.get("sub"),))
            if row:
                user = dict(row)
        except Exception:
            user = None
    if user is None:
        from ..deps import bearer as _bearer

        creds = await _bearer(request)
        if creds and creds.credentials:
            from ..security import decode_access_token as _decode

            try:
                payload = _decode(creds.credentials)
                row = db.fetch_one("SELECT * FROM users WHERE id = ?", (payload.get("sub"),))
                if row:
                    user = dict(row)
            except Exception:
                user = None
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    owned_paper(paper_id, user)

    async def generator():
        last_id = after
        idle = 0
        while True:
            if await request.is_disconnected():
                break
            rows = db.fetch_all(
                "SELECT * FROM events WHERE paper_id = ? AND id > ? ORDER BY id LIMIT 100",
                (paper_id, last_id),
            )
            for row in rows:
                last_id = row["id"]
                yield _sse(_event_payload(row), event="progress", event_id=row["id"])
                idle = 0
            status_row = db.fetch_one("SELECT status FROM papers WHERE id = ?", (paper_id,))
            status = status_row["status"] if status_row else "deleted"
            if status in TERMINAL and not rows:
                yield _sse(json.dumps({"status": status}), event="done")
                break
            idle += 1
            if idle % 20 == 0:
                yield ": ping\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/papers/{paper_id}/log")
def paper_log(paper_id: str, user: dict = Depends(current_user)) -> List[Dict[str, Any]]:
    owned_paper(paper_id, user)
    rows = db.fetch_all(
        "SELECT id, ts, stage, level, message FROM events WHERE paper_id = ? ORDER BY id DESC LIMIT 200",
        (paper_id,),
    )
    return [dict(row) for row in reversed(rows)]


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

def _export_payload(row: Dict[str, Any], user: dict) -> Dict[str, Any]:
    detail = _detail(row)
    detail["author_name"] = user.get("name") or ""
    return detail


@router.get("/papers/{paper_id}/export/{fmt}")
def export_paper(
    paper_id: str, fmt: str, user: dict = Depends(current_user)
) -> FileResponse:
    row = owned_paper(paper_id, user)
    if row["status"] != "completed":
        raise HTTPException(status_code=409, detail="Only completed papers can be exported")
    paper = _export_payload(row, user)
    exports_dir = get_settings().DATA_DIR / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    stem = paper.get("title") or paper_id
    try:
        if fmt in ("md", "markdown"):
            path = exports_dir / f"{paper_id}.md"
            path.write_text(exporter.paper_to_markdown(paper), encoding="utf-8")
            return FileResponse(
                path,
                filename=exporter.safe_filename(stem, ".md"),
                media_type="text/markdown; charset=utf-8",
            )
        if fmt == "bib":
            path = exports_dir / f"{paper_id}.bib"
            path.write_text(exporter.paper_to_bibtex(paper), encoding="utf-8")
            return FileResponse(
                path,
                filename=exporter.safe_filename(stem, ".bib"),
                media_type="application/x-bibtex",
            )
        if fmt == "docx":
            path = exporter.build_docx(paper, exports_dir / f"{paper_id}.docx")
            return FileResponse(
                path,
                filename=exporter.safe_filename(stem, ".docx"),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        if fmt == "pdf":
            path = exporter.build_pdf(paper, exports_dir / f"{paper_id}.pdf")
            return FileResponse(path, filename=exporter.safe_filename(stem, ".pdf"), media_type="application/pdf")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}") from exc
    raise HTTPException(status_code=400, detail="Unsupported export format")


@router.get("/stats", response_model=StatsOut)
def stats(user: dict = Depends(current_user)) -> StatsOut:
    rows = db.fetch_all(
        "SELECT status, request_json, meta_json FROM papers WHERE user_id = ?", (user["id"],)
    )
    total = len(rows)
    completed = sum(1 for r in rows if r["status"] == "completed")
    running = sum(1 for r in rows if r["status"] not in TERMINAL)
    failed = sum(1 for r in rows if r["status"] == "failed")
    words = 0
    by_style: Dict[str, int] = {}
    for row in rows:
        meta = db.loads(row["meta_json"], {})
        words += int(meta.get("word_count") or 0)
        style = db.loads(row["request_json"], {}).get("citation_style", "gbt7714")
        by_style[style] = by_style.get(style, 0) + 1
    return StatsOut(
        total=total,
        completed=completed,
        running=running,
        failed=failed,
        words=words,
        by_style=by_style,
    )
