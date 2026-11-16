"""Instance status, citation styles and health endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from .. import db
from ..config import get_settings
from ..deps import current_user
from ..schemas import ApiStatus
from ..services.llm import get_llm

router = APIRouter(prefix="/api", tags=["meta"])

STYLES = {
    "apa": {
        "name": "APA 7th",
        "description": "American Psychological Association, author-date",
        "example": "Smith, J. (2023). Title of article. Journal Name, 45(2), 123-145.",
    },
    "mla": {
        "name": "MLA 9th",
        "description": "Modern Language Association, humanities",
        "example": 'Smith, John. "Title of Article." Journal Name, vol. 45, no. 2, 2023, pp. 123-145.',
    },
    "ieee": {
        "name": "IEEE",
        "description": "Institute of Electrical and Electronics Engineers, numeric",
        "example": '[1] J. Smith, "Title of article," Journal Name, vol. 45, no. 2, pp. 123-145, 2023.',
    },
    "gbt7714": {
        "name": "GB/T 7714-2015",
        "description": "中国国家标准，顺序编码制（中文论文常用）",
        "example": "[1] 作者. 题名[J]. 期刊名, 2023, 45(2): 123-145.",
    },
}


@router.get("/status", response_model=ApiStatus)
def status() -> ApiStatus:
    settings = get_settings()
    sources = ["openalex", "crossref", "arxiv"]
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        sources.append("semantic_scholar")
    return ApiStatus(
        version=settings.APP_VERSION,
        environment=settings.ENV,
        llm_configured=settings.llm_configured,
        provider=settings.LLM_PROVIDER,
        model=settings.LLM_MODEL,
        model_fast=settings.LLM_MODEL_FAST,
        literature_sources=sources,
        citation_styles=list(STYLES.keys()),
        length_options=["short", "medium", "long"],
        language_options={"en": "English", "zh": "中文"},
        max_concurrent_jobs=settings.MAX_CONCURRENT_JOBS,
        allow_registration=settings.ALLOW_REGISTRATION,
    )


@router.get("/styles")
def styles() -> dict:
    return STYLES


@router.get("/health")
def health() -> dict:
    db_ok = True
    try:
        db.fetch_one("SELECT 1")
    except Exception:
        db_ok = False
    settings = get_settings()
    return {
        "status": "ok" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "llm_configured": settings.llm_configured,
        "version": settings.APP_VERSION,
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/llm/test")
async def llm_test(user: dict = Depends(current_user)) -> dict:
    llm = get_llm()
    if not llm.configured:
        return {"ok": False, "message": "LLM_API_KEY is not configured"}
    try:
        answer = await llm.ping()
        return {"ok": True, "message": answer, "model": llm.model}
    except Exception as exc:
        return {"ok": False, "message": str(exc)[:300]}
