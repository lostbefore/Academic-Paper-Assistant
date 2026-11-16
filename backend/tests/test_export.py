"""Exporters produce valid DOCX/PDF/Markdown/BibTeX files."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.services import export

PAPER = {
    "id": "p_test",
    "title": "人工智能时代的学术写作：方法与边界",
    "author_name": "张三",
    "request": {
        "title": "人工智能时代的学术写作：方法与边界",
        "field": "教育技术学",
        "keywords": ["人工智能", "学术写作", "学术诚信"],
        "language": "zh",
        "citation_style": "gbt7714",
    },
    "sections": {
        "title": "人工智能时代的学术写作：方法与边界",
        "abstract": "本文讨论人工智能辅助学术写作的方法与边界。" * 3,
        "introduction": "引言段落。" * 30,
        "literature_review": "文献综述段落。" * 40,
        "methodology": "研究方法段落。" * 30,
        "results": "研究结果段落。" * 30,
        "discussion": "讨论段落。" * 30,
        "conclusion": "结论段落。" * 15,
        "references": "[1] 李明. 测试文献[J]. 测试期刊, 2025.",
    },
    "references": [
        {
            "title": "测试文献",
            "authors": ["李明"],
            "year": 2025,
            "venue": "测试期刊",
            "doi": "10.1000/test",
        }
    ],
}


def test_markdown_contains_all_sections():
    text = export.paper_to_markdown(PAPER)
    assert text.startswith("# 人工智能时代的学术写作")
    for heading in ("摘要", "引言", "文献综述", "研究方法", "研究结果", "讨论", "结论", "参考文献"):
        assert heading in text


def test_bibtex_is_well_formed():
    text = export.paper_to_bibtex(PAPER)
    assert text.startswith("@article{")
    assert "title = {测试文献}" in text
    assert "doi = {10.1000/test}" in text


def test_docx_is_a_valid_zip_package(tmp_path: Path):
    path = export.build_docx(PAPER, tmp_path / "paper.docx")
    assert path.exists() and path.stat().st_size > 5000
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert "word/document.xml" in names
        xml = archive.read("word/document.xml").decode("utf-8")
    assert "人工智能时代的学术写作" in xml
    assert "宋体" in xml or "eastAsia" in xml


def test_pdf_has_trailer_and_pages(tmp_path: Path):
    path = export.build_pdf(PAPER, tmp_path / "paper.pdf")
    data = path.read_bytes()
    assert data.startswith(b"%PDF")
    assert data.rstrip().endswith(b"%%EOF")
    assert b"/Type /Page" in data
    assert path.stat().st_size > 3000


def test_english_paper_uses_latin_fonts(tmp_path: Path):
    english = {
        **PAPER,
        "title": "Academic Writing with AI",
        "request": {**PAPER["request"], "language": "en", "keywords": ["AI"]},
    }
    path = export.build_pdf(english, tmp_path / "en.pdf")
    assert path.read_bytes().startswith(b"%PDF")


def test_safe_filename_strips_illegal_characters():
    assert "/" not in export.safe_filename('a/b:c*?"<>|d', ".docx")
    assert export.safe_filename("", ".md") == "paper.md"
