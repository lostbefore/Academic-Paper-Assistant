"""Reference formatting for the four supported citation styles."""

from __future__ import annotations

from app.services.citations import (
    build_reference_list,
    format_reference,
)

EN = {
    "title": "Attention is all you need",
    "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
    "year": 2017,
    "venue": "Advances in Neural Information Processing Systems",
    "doi": "10.5555/3295222.3295349",
    "type": "article",
}

CN = {
    "title": "生成式人工智能赋能研究生学术写作的机理与边界",
    "authors": ["李明", "王芳"],
    "year": 2025,
    "venue": "学位与研究生教育",
    "doi": "",
    "type": "article",
}


def test_apa_keeps_author_year_and_doi():
    text = format_reference(EN, "apa", 1)
    assert "Vaswani, A." in text
    assert "(2017)" in text
    assert "10.5555/3295222.3295349" in text


def test_ieee_is_numbered_with_initials_first():
    text = format_reference(EN, "ieee", 3)
    assert text.startswith("[3] A. Vaswani")
    assert '"Attention is all you need,"' in text


def test_gbt7714_uses_type_marker_and_chinese_names():
    text = format_reference(CN, "gbt7714", 1)
    assert text.startswith("[1] 李明, 王芳.")
    assert "[J]" in text
    assert "学位与研究生教育" in text


def test_mla_quotes_the_title():
    text = format_reference(EN, "mla", 1)
    assert '"Attention is all you need."' in text
    assert "2017." in text


def test_missing_year_and_authors_do_not_crash():
    text = format_reference({"title": "Untitled work"}, "apa", 1)
    assert "n.d." in text


def test_reference_list_is_numbered_in_order():
    entries = build_reference_list([EN, CN], "gbt7714")
    assert entries[0].startswith("[1]")
    assert entries[1].startswith("[2]")
    assert len(entries) == 2
