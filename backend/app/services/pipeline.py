"""Paper generation pipeline.

A paper is produced in explicit stages so progress can be reported and partial
content survives a failure:

    researching -> outlining -> writing (one LLM call per section) -> abstract
    -> references -> completed

The pipeline runs in an asyncio task owned by :class:`JobManager`.  All state is
persisted in SQLite, so a restart never leaves a paper silently "running".
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from .. import db
from ..config import get_settings
from . import citations, literature, prompts
from .llm import LLMError, LLMNotConfigured, get_llm

log = logging.getLogger("apa.pipeline")

CANCELLED = "cancelled"
TERMINAL = {"completed", "failed", CANCELLED}


def word_count(text: str) -> int:
    """Count CJK characters as words and latin tokens separately."""
    if not text:
        return 0
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z0-9]+", text))
    return cjk + latin


def _paper(paper_id: str) -> Optional[Any]:
    return db.fetch_one("SELECT * FROM papers WHERE id = ?", (paper_id,))


def _update(paper_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = db.utcnow()
    columns = ", ".join(f"{name} = ?" for name in fields)
    db.execute(f"UPDATE papers SET {columns} WHERE id = ?", (*fields.values(), paper_id))


def log_event(
    paper_id: str,
    stage: str,
    message: str,
    *,
    level: str = "info",
    data: Optional[Dict[str, Any]] = None,
    progress: Optional[int] = None,
) -> None:
    db.execute(
        "INSERT INTO events (paper_id, ts, stage, level, message, data_json) VALUES (?,?,?,?,?,?)",
        (paper_id, db.utcnow(), stage, level, message[:500], db.dumps(data or {})),
    )
    if progress is not None:
        _update(paper_id, progress=progress, stage=stage)
    # Keep the event table bounded.
    db.execute(
        "DELETE FROM events WHERE paper_id = ? AND id < (SELECT MAX(id) - 800 FROM events WHERE paper_id = ?)",
        (paper_id, paper_id),
    )


def is_cancelled(paper_id: str) -> bool:
    row = db.fetch_one("SELECT status FROM papers WHERE id = ?", (paper_id,))
    return bool(row and row["status"] == CANCELLED)


def _target_words(request: Dict[str, Any]) -> int:
    explicit = request.get("target_words")
    if explicit:
        return int(explicit)
    return prompts.LENGTH_WORDS.get(request.get("length", "medium"), 6000)


def _max_tokens(words: int, language: str) -> int:
    """Token ceiling for one section.

    Chinese text is far denser per token (~5 characters/token with modern
    tokenizers) than English, so the two languages need different ceilings to
    avoid the model overshooting the requested length.
    """
    if language == "zh":
        return max(300, min(4000, int(words * 0.55) + 120))
    return max(500, min(6000, int(words * 2.0) + 200))


def _default_outline(title: str, language: str, target_words: int) -> Dict[str, Any]:
    titles = prompts.section_titles(language)
    sections = []
    for key in prompts.SECTION_ORDER:
        sections.append(
            {
                "key": key,
                "title": titles[key],
                "goal": f"Write the {titles[key].lower()} of the study.",
                "words": int(target_words * prompts.SECTION_SHARE[key]),
            }
        )
    return {
        "title": title,
        "abstract_brief": "",
        "research_questions": [],
        "theoretical_framework": "",
        "method": "",
        "sections": sections,
    }


def _normalise_outline(outline: Dict[str, Any], title: str, language: str, target_words: int) -> Dict[str, Any]:
    default = _default_outline(title, language, target_words)
    if not isinstance(outline, dict):
        return default
    by_key = {
        item.get("key"): item
        for item in outline.get("sections", [])
        if isinstance(item, dict) and item.get("key")
    }
    sections = []
    for key in prompts.SECTION_ORDER:
        base = next(s for s in default["sections"] if s["key"] == key)
        item = by_key.get(key) or {}
        sections.append(
            {
                "key": key,
                "title": str(item.get("title") or base["title"])[:80],
                "goal": str(item.get("goal") or base["goal"])[:400],
                "words": int(item.get("words") or base["words"]),
            }
        )
    merged = {**default, **{k: v for k, v in outline.items() if k != "sections"}}
    merged["sections"] = sections
    merged["title"] = str(merged.get("title") or title)[:300]

    # The model often copies the example word counts from the prompt, so the
    # section budgets are rescaled to the user's actual target length.
    current_total = sum(s["words"] for s in sections) or 1
    scale = target_words / current_total
    for spec in sections:
        spec["words"] = max(180, int(round(spec["words"] * scale)))
    return merged


async def _research(paper_id: str, request: Dict[str, Any], reference_count: int) -> List[Dict[str, Any]]:
    title = request.get("title", "")
    keywords = request.get("keywords") or []
    field = request.get("field") or ""
    query = " ".join([title, *keywords[:4]])
    if field and field.lower() not in query.lower():
        query = f"{query} {field}"
    log_event(paper_id, "researching", f"Searching literature for: {query[:120]}", progress=4)
    try:
        refs = await literature.search_literature(query, limit=max(reference_count, 8))
    except Exception as exc:  # network failure must not kill the paper
        log_event(
            paper_id,
            "researching",
            f"Literature search failed, continuing without external references: {exc}",
            level="warning",
        )
        refs = []
    if not refs:
        log_event(
            paper_id,
            "researching",
            "No external references were retrieved; the paper will avoid citing sources.",
            level="warning",
            progress=12,
        )
    else:
        log_event(
            paper_id,
            "researching",
            f"Retrieved {len(refs)} candidate references",
            progress=12,
            data={"count": len(refs)},
        )
    _update(paper_id, refs_json=db.dumps(refs))
    return refs


async def _outline(
    paper_id: str,
    request: Dict[str, Any],
    refs: List[Dict[str, Any]],
    target_words: int,
) -> Dict[str, Any]:
    language = request.get("language", "en")
    log_event(paper_id, "outlining", "Designing the paper outline", progress=15)
    llm = get_llm()
    try:
        data, result = await llm.complete_json(
            prompts.outline_messages(
                title=request["title"],
                field=request.get("field", ""),
                keywords=request.get("keywords") or [],
                language=language,
                target_words=target_words,
                refs=refs,
                instructions=request.get("instructions", ""),
            ),
            max_tokens=2000,
            temperature=0.4,
        )
        outline = _normalise_outline(data, request["title"], language, target_words)
        _add_usage(paper_id, result.tokens_in, result.tokens_out)
    except (LLMError, LLMNotConfigured):
        raise
    except Exception as exc:
        log_event(paper_id, "outlining", f"Outline parse failed, using default structure: {exc}", level="warning")
        outline = _default_outline(request["title"], language, target_words)

    _update(paper_id, outline_json=db.dumps(outline))
    log_event(
        paper_id,
        "outlining",
        f"Outline ready with {len(outline['sections'])} sections",
        progress=24,
    )
    return outline


def _add_usage(paper_id: str, tokens_in: int, tokens_out: int) -> None:
    row = db.fetch_one("SELECT meta_json FROM papers WHERE id = ?", (paper_id,))
    meta = db.loads(row["meta_json"], {}) if row else {}
    meta["tokens_in"] = int(meta.get("tokens_in", 0)) + int(tokens_in or 0)
    meta["tokens_out"] = int(meta.get("tokens_out", 0)) + int(tokens_out or 0)
    _update(paper_id, meta_json=db.dumps(meta))


def _content_stats(text: str) -> Dict[str, Any]:
    paragraphs = [p for p in text.split("\n") if p.strip()]
    return {"words": word_count(text), "paragraphs": len(paragraphs)}


async def _write_sections(
    paper_id: str,
    request: Dict[str, Any],
    outline: Dict[str, Any],
    refs: List[Dict[str, Any]],
) -> Dict[str, str]:
    language = request.get("language", "en")
    style = request.get("citation_style", "gbt7714")
    llm = get_llm()
    sections: Dict[str, str] = {}
    previous: List[Dict[str, str]] = []
    total = len(outline["sections"])
    start, end = 26, 90

    for index, spec in enumerate(outline["sections"]):
        if is_cancelled(paper_id):
            raise asyncio.CancelledError()
        key = spec["key"]
        progress = start + int((end - start) * index / max(total, 1))
        log_event(
            paper_id,
            "writing",
            f"Writing section {index + 1}/{total}: {spec['title']}",
            progress=progress,
            data={"section": key},
        )
        try:
            result = await llm.complete(
                prompts.section_messages(
                    section_key=key,
                    section_title=spec["title"],
                    goal=spec.get("goal", ""),
                    words=spec.get("words", 700),
                    outline=outline,
                    refs=refs,
                    language=language,
                    citation_style=style,
                    previous=previous,
                ),
                max_tokens=_max_tokens(spec.get("words", 700), language),
                temperature=0.65,
            )
        except LLMError:
            raise
        text = _clean_section(result.text)
        if not text:
            raise LLMError(f"model returned an empty {spec['title']} section")
        sections[key] = text
        previous.append({"title": spec["title"], "summary": text[:600]})
        _add_usage(paper_id, result.tokens_in, result.tokens_out)

        _update(paper_id, sections_json=db.dumps(sections))
        log_event(
            paper_id,
            "writing",
            f"Finished {spec['title']} ({word_count(text)} words)",
            progress=progress + max(1, int((end - start) / max(total, 1) * 0.9)),
            data={"section": key, **_content_stats(text)},
        )
    return sections


def _clean_section(text: str) -> str:
    text = text.strip()
    # Drop a leading markdown heading the model may have added.
    text = re.sub(r"^#{1,3}\s+[^\n]+\n+", "", text)
    # Drop bold section labels at the very start.
    text = re.sub(r"^\*\*[^*]{2,60}\*\*\s*\n+", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def _abstract(
    paper_id: str,
    request: Dict[str, Any],
    outline: Dict[str, Any],
    sections: Dict[str, str],
) -> str:
    language = request.get("language", "en")
    style = request.get("citation_style", "gbt7714")
    llm = get_llm()
    log_event(paper_id, "abstract", "Writing the abstract", progress=92)
    try:
        result = await llm.complete(
            prompts.abstract_messages(
                title=outline.get("title", request["title"]),
                sections=sections,
                keywords=request.get("keywords") or [],
                language=language,
                citation_style=style,
            ),
            max_tokens=500 if language == "zh" else 700,
            temperature=0.5,
        )
        _add_usage(paper_id, result.tokens_in, result.tokens_out)
        abstract = _clean_section(result.text)
        if abstract:
            return abstract
    except LLMError as exc:
        log_event(paper_id, "abstract", f"Abstract generation failed: {exc}", level="warning")
    # Deterministic fallback built from the outline so export never breaks.
    brief = outline.get("abstract_brief") or ""
    if brief:
        return brief
    body = " ".join(sections.get(key, "")[:200] for key in ("introduction", "methodology") if sections.get(key))
    return body[:600]


def _finalise(
    paper_id: str,
    request: Dict[str, Any],
    outline: Dict[str, Any],
    sections: Dict[str, str],
    refs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    style = request.get("citation_style", "gbt7714")
    entries = citations.build_reference_list(refs, style)
    heading = "参考文献" if request.get("language") == "zh" else "References"
    sections["references"] = "\n\n".join(entries) if entries else f"（{heading}：检索阶段未获取到可引用的外部文献）" if request.get("language") == "zh" else "(No external references were available for this draft.)"
    sections["title"] = outline.get("title") or request["title"]

    total_words = sum(
        word_count(value) for key, value in sections.items() if key not in ("references", "title")
    )
    meta = {
        "word_count": total_words,
        "reference_count": len(refs),
        "model": get_settings().LLM_MODEL,
        "finished_at": db.utcnow(),
    }
    row = db.fetch_one("SELECT meta_json FROM papers WHERE id = ?", (paper_id,))
    merged = {**db.loads(row["meta_json"], {}), **meta}
    _update(
        paper_id,
        status="completed",
        stage="completed",
        progress=100,
        sections_json=db.dumps(sections),
        meta_json=db.dumps(merged),
        finished_at=db.utcnow(),
        error="",
    )
    return merged


async def generate_paper(paper_id: str) -> None:
    row = _paper(paper_id)
    if not row:
        return
    request = db.loads(row["request_json"], {})
    reference_count = int(request.get("reference_count") or get_settings().DEFAULT_REFERENCE_COUNT)
    target_words = _target_words(request)
    try:
        _update(paper_id, status="running", stage="researching", progress=2, error="")
        log_event(paper_id, "queued", "Generation started", progress=2)
        refs = await _research(paper_id, request, reference_count)
        outline = await _outline(paper_id, request, refs, target_words)
        sections = await _write_sections(paper_id, request, outline, refs)
        if is_cancelled(paper_id):
            raise asyncio.CancelledError()
        sections["abstract"] = await _abstract(paper_id, request, outline, sections)
        log_event(paper_id, "references", "Formatting references", progress=96)
        meta = _finalise(paper_id, request, outline, sections, refs)
        log_event(
            paper_id,
            "completed",
            f"Paper completed: {meta['word_count']} words, {meta['reference_count']} references",
            progress=100,
        )
    except asyncio.CancelledError:
        _update(paper_id, status=CANCELLED, stage="cancelled")
        log_event(paper_id, "cancelled", "Generation cancelled by user", level="warning")
        raise
    except LLMNotConfigured as exc:
        _fail(paper_id, str(exc))
    except LLMError as exc:
        _fail(paper_id, f"Model error: {exc}")
    except Exception as exc:  # pragma: no cover - defensive
        log.exception("paper generation crashed")
        _fail(paper_id, f"Unexpected error: {exc}")


def _fail(paper_id: str, message: str) -> None:
    _update(paper_id, status="failed", stage="failed", error=message[:1000])
    log_event(paper_id, "failed", message, level="error")
    log.error("paper %s failed: %s", paper_id, message)


# ---------------------------------------------------------------------------
# Single-section operations
# ---------------------------------------------------------------------------

async def regenerate_section(paper_id: str, key: str, instructions: str = "") -> str:
    row = _paper(paper_id)
    if not row:
        raise ValueError("paper not found")
    request = db.loads(row["request_json"], {})
    outline = db.loads(row["outline_json"], {})
    sections = db.loads(row["sections_json"], {})
    refs = db.loads(row["refs_json"], [])
    if not outline.get("sections"):
        raise ValueError("paper has no outline yet")
    spec = next((s for s in outline["sections"] if s["key"] == key), None)
    if not spec:
        raise ValueError(f"unknown section: {key}")
    previous = [
        {"title": s["title"], "summary": sections.get(s["key"], "")[:600]}
        for s in outline["sections"]
        if s["key"] != key and sections.get(s["key"])
    ]
    result = await get_llm().complete(
        prompts.section_messages(
            section_key=key,
            section_title=spec["title"],
            goal=spec.get("goal", ""),
            words=spec.get("words", 700),
            outline=outline,
            refs=refs,
            language=request.get("language", "en"),
            citation_style=request.get("citation_style", "gbt7714"),
            previous=previous,
            instructions=instructions,
        ),
        max_tokens=_max_tokens(spec.get("words", 700), request.get("language", "en")),
        temperature=0.7,
    )
    text = _clean_section(result.text)
    if not text:
        raise LLMError("model returned an empty section")
    sections[key] = text
    _add_usage(paper_id, result.tokens_in, result.tokens_out)
    _update(paper_id, sections_json=db.dumps(sections))
    log_event(paper_id, "edit", f"Regenerated section: {spec['title']}", data={"section": key})
    return text


class JobManager:
    """Owns background generation tasks and enforces the concurrency limit."""

    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task] = {}
        self._semaphore: Optional[asyncio.Semaphore] = None

    def _sem(self) -> asyncio.Semaphore:
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(max(1, get_settings().MAX_CONCURRENT_JOBS))
        return self._semaphore

    def is_running(self, paper_id: str) -> bool:
        task = self._tasks.get(paper_id)
        return bool(task and not task.done())

    async def _run(self, paper_id: str) -> None:
        async with self._sem():
            try:
                await generate_paper(paper_id)
            finally:
                self._tasks.pop(paper_id, None)

    def start(self, paper_id: str) -> None:
        if self.is_running(paper_id):
            return
        task = asyncio.create_task(self._run(paper_id), name=f"paper-{paper_id}")
        self._tasks[paper_id] = task

    def cancel(self, paper_id: str) -> None:
        task = self._tasks.get(paper_id)
        _update(paper_id, status=CANCELLED, stage="cancelled")
        if task and not task.done():
            task.cancel()

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    def running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if not t.done())


job_manager = JobManager()
