"""Literature merging, ranking and failure isolation (network is stubbed)."""

from __future__ import annotations

import asyncio

import pytest

from app.services import literature


def _paper(title, authors, year, citations=0, venue="Journal", doi=""):
    return {
        "title": title,
        "authors": authors,
        "year": year,
        "venue": venue,
        "doi": doi,
        "url": "",
        "abstract": "abstract " * 20,
        "citations": citations,
        "type": "article",
        "source": "test",
    }


@pytest.mark.asyncio
async def test_duplicate_titles_are_merged(monkeypatch):
    first = [_paper("Deep learning for text classification", ["A One"], 2020, 5)]
    second = [_paper("Deep   learning for TEXT classification", ["A One"], 2020, 99, doi="10.1/x")]

    async def fake_openalex(q, limit, year_from):
        return first

    async def fake_crossref(q, limit, year_from):
        return second

    monkeypatch.setattr(literature, "search_openalex", fake_openalex)
    monkeypatch.setattr(literature, "search_crossref", fake_crossref)
    monkeypatch.setattr(literature, "search_arxiv", lambda *a, **k: asyncio.sleep(0, result=[]))

    results = await literature.search_literature(
        "unittest-dedup", limit=5, sources=["openalex", "crossref"], use_cache=False
    )
    assert len(results) == 1
    assert results[0]["doi"] == "10.1/x", "metadata from the second source must be merged"
    assert results[0]["citations"] == 99


@pytest.mark.asyncio
async def test_failing_source_does_not_break_search(monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("upstream 503")

    async def ok(*args, **kwargs):
        return [_paper("Reliable source result for testing", ["B Two"], 2021)]

    monkeypatch.setattr(literature, "search_openalex", boom)
    monkeypatch.setattr(literature, "search_crossref", ok)
    monkeypatch.setattr(literature, "search_arxiv", lambda *a, **k: asyncio.sleep(0, result=[]))

    results = await literature.search_literature(
        "unittest-failure", limit=5, sources=["openalex", "crossref"], use_cache=False
    )
    assert len(results) == 1
    assert results[0]["title"].startswith("Reliable source")


@pytest.mark.asyncio
async def test_short_or_empty_titles_are_dropped(monkeypatch):
    async def ok(*args, **kwargs):
        return [_paper("AI", ["C"], 2020), _paper("", [], 2020)]

    monkeypatch.setattr(literature, "search_openalex", ok)
    monkeypatch.setattr(literature, "search_crossref", lambda *a, **k: asyncio.sleep(0, result=[]))
    monkeypatch.setattr(literature, "search_arxiv", lambda *a, **k: asyncio.sleep(0, result=[]))

    results = await literature.search_literature(
        "unittest-short", limit=5, sources=["openalex"], use_cache=False
    )
    assert results == []


@pytest.mark.asyncio
async def test_results_are_cached(monkeypatch):
    calls = {"n": 0}

    async def counted(*args, **kwargs):
        calls["n"] += 1
        return [_paper("Cache behaviour of the literature service", ["D"], 2022)]

    monkeypatch.setattr(literature, "search_openalex", counted)
    monkeypatch.setattr(literature, "search_crossref", lambda *a, **k: asyncio.sleep(0, result=[]))
    monkeypatch.setattr(literature, "search_arxiv", lambda *a, **k: asyncio.sleep(0, result=[]))

    await literature.search_literature("unittest-cache", limit=3, sources=["openalex"])
    await literature.search_literature("unittest-cache", limit=3, sources=["openalex"])
    assert calls["n"] == 1, "second identical query must be served from SQLite cache"
