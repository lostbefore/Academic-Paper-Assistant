"""Academic literature search across free, key-less sources.

OpenAlex is the primary source (broad coverage, no API key), Crossref adds DOI
metadata, arXiv covers preprints and Semantic Scholar is used when an API key is
configured.  Results are normalised, de-duplicated and cached in SQLite.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

import httpx

from ..config import get_settings
from .. import db

USER_AGENT = "AcademicPaperAssistant/2.0 (mailto:apa@example.org)"
ATOM = "{http://www.w3.org/2005/Atom}"

_NON_WORD = re.compile(r"[^a-z0-9]+")


def _norm_title(title: str) -> str:
    return _NON_WORD.sub(" ", (title or "").lower()).strip()


def _clean(text: Optional[str], limit: int = 1200) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _abstract_from_inverted(index: Optional[Dict[str, List[int]]]) -> str:
    if not index:
        return ""
    positions: List[tuple[int, str]] = []
    for word, places in index.items():
        for place in places:
            positions.append((place, word))
    positions.sort()
    return _clean(" ".join(word for _, word in positions), 1600)


async def _get_json(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Any:
    response = await client.get(url, params=params, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.json()


async def search_openalex(query: str, limit: int, year_from: Optional[int]) -> List[Dict[str, Any]]:
    settings = get_settings()
    params = {
        "search": query,
        "per_page": min(limit, 50),
        "sort": "relevance_score:desc",
        "select": "id,doi,title,publication_year,authorships,primary_location,cited_by_count,abstract_inverted_index,type",
    }
    if year_from:
        params["filter"] = f"from_publication_date:{year_from}-01-01"
    if settings.OPENALEX_EMAIL:
        params["mailto"] = settings.OPENALEX_EMAIL
    async with httpx.AsyncClient(timeout=settings.LITERATURE_TIMEOUT_SECONDS) as client:
        data = await _get_json(client, "https://api.openalex.org/works", params)
    results: List[Dict[str, Any]] = []
    for work in data.get("results", []):
        authors = [
            (a.get("author") or {}).get("display_name", "")
            for a in work.get("authorships", [])[:8]
        ]
        source = ((work.get("primary_location") or {}).get("source") or {}).get("display_name", "")
        results.append(
            {
                "title": _clean(work.get("title"), 400),
                "authors": [a for a in authors if a],
                "year": work.get("publication_year"),
                "venue": source or "",
                "doi": (work.get("doi") or "").replace("https://doi.org/", ""),
                "url": work.get("doi") or work.get("id") or "",
                "abstract": _abstract_from_inverted(work.get("abstract_inverted_index")),
                "citations": int(work.get("cited_by_count") or 0),
                "type": work.get("type") or "article",
                "source": "openalex",
            }
        )
    return results


async def search_crossref(query: str, limit: int, year_from: Optional[int]) -> List[Dict[str, Any]]:
    settings = get_settings()
    params: Dict[str, Any] = {
        "query.bibliographic": query,
        "rows": min(limit, 50),
        "select": "DOI,title,author,issued,container-title,is-referenced-by-count,abstract,type",
        "mailto": settings.OPENALEX_EMAIL or "apa@example.org",
    }
    if year_from:
        params["filter"] = f"from-pub-date:{year_from}-01-01"
    async with httpx.AsyncClient(timeout=settings.LITERATURE_TIMEOUT_SECONDS) as client:
        data = await _get_json(client, "https://api.crossref.org/works", params)
    results: List[Dict[str, Any]] = []
    for item in (data.get("message") or {}).get("items", []):
        authors = []
        for author in item.get("author", [])[:8]:
            name = " ".join(filter(None, [author.get("given"), author.get("family")]))
            if name:
                authors.append(name)
        issued = ((item.get("issued") or {}).get("date-parts") or [[None]])[0]
        titles = item.get("title") or []
        containers = item.get("container-title") or []
        results.append(
            {
                "title": _clean(titles[0] if titles else "", 400),
                "authors": authors,
                "year": issued[0] if issued else None,
                "venue": _clean(containers[0] if containers else "", 200),
                "doi": item.get("DOI") or "",
                "url": f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else "",
                "abstract": _clean(item.get("abstract"), 1600),
                "citations": int(item.get("is-referenced-by-count") or 0),
                "type": item.get("type") or "article",
                "source": "crossref",
            }
        )
    return results


async def search_arxiv(query: str, limit: int, year_from: Optional[int]) -> List[Dict[str, Any]]:
    settings = get_settings()
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(limit, 50),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    async with httpx.AsyncClient(timeout=settings.LITERATURE_TIMEOUT_SECONDS) as client:
        response = await client.get(
            "https://export.arxiv.org/api/query",
            params=params,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
        xml_text = response.text
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    results: List[Dict[str, Any]] = []
    for entry in root.findall(f"{ATOM}entry"):
        title = _clean((entry.findtext(f"{ATOM}title") or ""), 400)
        abstract = _clean(entry.findtext(f"{ATOM}summary"), 1600)
        published = entry.findtext(f"{ATOM}published") or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        if year_from and year and year < year_from:
            continue
        authors = [
            _clean(a.findtext(f"{ATOM}name"), 120)
            for a in entry.findall(f"{ATOM}author")
        ][:8]
        link = ""
        for link_el in entry.findall(f"{ATOM}link"):
            if link_el.get("rel") == "alternate":
                link = link_el.get("href", "")
        results.append(
            {
                "title": title,
                "authors": [a for a in authors if a],
                "year": year,
                "venue": "arXiv",
                "doi": "",
                "url": link,
                "abstract": abstract,
                "citations": 0,
                "type": "preprint",
                "source": "arxiv",
            }
        )
    return results


async def search_semantic_scholar(
    query: str, limit: int, year_from: Optional[int]
) -> List[Dict[str, Any]]:
    settings = get_settings()
    if not settings.SEMANTIC_SCHOLAR_API_KEY:
        return []
    params: Dict[str, Any] = {
        "query": query,
        "limit": min(limit, 50),
        "fields": "title,authors,year,venue,abstract,externalIds,citationCount,url,publicationTypes",
    }
    if year_from:
        params["year"] = f"{year_from}-"
    headers = {
        "x-api-key": settings.SEMANTIC_SCHOLAR_API_KEY,
        "User-Agent": USER_AGENT,
    }
    async with httpx.AsyncClient(timeout=settings.LITERATURE_TIMEOUT_SECONDS) as client:
        response = await client.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    results: List[Dict[str, Any]] = []
    for paper in data.get("data", []):
        ext = paper.get("externalIds") or {}
        results.append(
            {
                "title": _clean(paper.get("title"), 400),
                "authors": [a.get("name", "") for a in (paper.get("authors") or [])[:8]],
                "year": paper.get("year"),
                "venue": _clean(paper.get("venue"), 200),
                "doi": ext.get("DOI", ""),
                "url": paper.get("url") or "",
                "abstract": _clean(paper.get("abstract"), 1600),
                "citations": int(paper.get("citationCount") or 0),
                "type": "article",
                "source": "semantic_scholar",
            }
        )
    return results


async def _guarded(coro, source: str) -> tuple[str, List[Dict[str, Any]]]:
    try:
        return source, await coro
    except Exception:  # a single failing source must never break a search
        return source, []


async def search_literature(
    query: str,
    limit: int = 15,
    year_from: Optional[int] = None,
    sources: Optional[Iterable[str]] = None,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    """Search several sources concurrently and merge the results."""
    settings = get_settings()
    query = (query or "").strip()
    if not query:
        return []
    wanted = set(sources or ["openalex", "crossref", "arxiv"])
    if settings.SEMANTIC_SCHOLAR_API_KEY:
        wanted.add("semantic_scholar")

    cache_key = hashlib.sha256(
        db.dumps({"q": query.lower(), "limit": limit, "y": year_from, "s": sorted(wanted)}).encode()
    ).hexdigest()
    if use_cache:
        row = db.fetch_one(
            "SELECT payload, expires_at FROM literature_cache WHERE key = ?", (cache_key,)
        )
        if row and row["expires_at"] > db.utcnow():
            return db.loads(row["payload"], [])

    per_source = max(limit, 10)
    tasks = []
    if "openalex" in wanted:
        tasks.append(_guarded(search_openalex(query, per_source, year_from), "openalex"))
    if "crossref" in wanted:
        tasks.append(_guarded(search_crossref(query, per_source, year_from), "crossref"))
    if "arxiv" in wanted:
        tasks.append(_guarded(search_arxiv(query, per_source, year_from), "arxiv"))
    if "semantic_scholar" in wanted:
        tasks.append(
            _guarded(search_semantic_scholar(query, per_source, year_from), "semantic_scholar")
        )
    gathered = await asyncio.gather(*tasks)

    merged: List[Dict[str, Any]] = []
    seen: Dict[str, Dict[str, Any]] = {}
    for _source, items in gathered:
        for rank, item in enumerate(items):
            key = _norm_title(item["title"]) or item.get("doi") or ""
            if len(key) < 8:
                continue
            existing = seen.get(key)
            if existing is None:
                item["_hits"] = 1
                item["_rank"] = rank
                seen[key] = item
                merged.append(item)
            else:
                # Merge complementary metadata from the second source.
                existing["_hits"] += 1
                existing["_rank"] = min(existing["_rank"], rank)
                for field in ("doi", "url", "venue", "year"):
                    if not existing.get(field) and item.get(field):
                        existing[field] = item[field]
                if len(item.get("abstract", "")) > len(existing.get("abstract", "")):
                    existing["abstract"] = item["abstract"]
                existing["citations"] = max(
                    int(existing.get("citations") or 0), int(item.get("citations") or 0)
                )

    # Rank by relevance order within each source (a paper found high in two
    # sources wins), then by citation count as a tie-breaker.
    merged.sort(
        key=lambda r: (
            -int(r.pop("_hits", 1)),
            int(r.pop("_rank", 99)),
            -(r.get("citations") or 0),
        )
    )
    merged = merged[:limit]

    expires = (
        datetime.now(timezone.utc) + timedelta(hours=settings.LITERATURE_CACHE_TTL_HOURS)
    ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    db.execute(
        "INSERT OR REPLACE INTO literature_cache (key, payload, created_at, expires_at) VALUES (?,?,?,?)",
        (cache_key, db.dumps(merged), db.utcnow(), expires),
    )
    return merged
