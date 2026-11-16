"""Literature search endpoints (also usable standalone from the UI)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from ..config import get_settings
from ..deps import current_user
from ..services import literature

router = APIRouter(prefix="/api/literature", tags=["literature"])


@router.get("/search")
async def search(
    q: str = Query(min_length=2, max_length=300),
    limit: int = Query(default=12, ge=1, le=50),
    year_from: Optional[int] = Query(default=None, ge=1900, le=2100),
    user: dict = Depends(current_user),
) -> List[Dict[str, Any]]:
    return await literature.search_literature(q, limit=limit, year_from=year_from)


@router.get("/sources")
def sources() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "openalex": {"enabled": True, "requires_key": False},
        "crossref": {"enabled": True, "requires_key": False},
        "arxiv": {"enabled": True, "requires_key": False},
        "semantic_scholar": {
            "enabled": bool(settings.SEMANTIC_SCHOLAR_API_KEY),
            "requires_key": True,
        },
    }
