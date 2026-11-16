"""Pipeline helpers: length budgets, outline normalisation, text cleanup."""

from __future__ import annotations

from app.services import pipeline


def test_word_count_counts_cjk_characters_and_latin_words():
    assert pipeline.word_count("人工智能") == 4
    assert pipeline.word_count("hello world") == 2
    # "AI" is one latin token, each Chinese character counts as one word
    assert pipeline.word_count("AI 赋能 教育") == 1 + 2 + 2


def test_default_outline_has_six_ordered_sections():
    outline = pipeline._default_outline("T", "zh", 6000)
    keys = [s["key"] for s in outline["sections"]]
    assert keys == ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]
    total = sum(s["words"] for s in outline["sections"])
    assert 5600 <= total <= 6400


def test_outline_is_rescaled_to_the_requested_length():
    model_outline = {
        "title": "A title",
        "sections": [
            {"key": "introduction", "title": "Intro", "goal": "g", "words": 800},
            {"key": "literature_review", "title": "LR", "goal": "g", "words": 1400},
            {"key": "methodology", "title": "M", "goal": "g", "words": 1000},
            {"key": "results", "title": "R", "goal": "g", "words": 1100},
            {"key": "discussion", "title": "D", "goal": "g", "words": 1000},
            {"key": "conclusion", "title": "C", "goal": "g", "words": 500},
        ],
    }
    outline = pipeline._normalise_outline(model_outline, "fallback", "en", 3000)
    total = sum(s["words"] for s in outline["sections"])
    assert abs(total - 3000) <= 300, f"expected ~3000, got {total}"


def test_missing_sections_are_filled_from_defaults():
    outline = pipeline._normalise_outline({"sections": [{"key": "introduction", "words": 500}]}, "T", "en", 2000)
    assert len(outline["sections"]) == 6
    assert all(s["title"] for s in outline["sections"])


def test_clean_section_removes_leading_heading_and_extra_blank_lines():
    raw = "## Introduction\n\n\nThis is the body.\n\n\n\nSecond paragraph."
    cleaned = pipeline._clean_section(raw)
    assert cleaned.startswith("This is the body.")
    assert "\n\n\n" not in cleaned


def test_clean_section_strips_bold_label():
    assert pipeline._clean_section("**Introduction**\nBody text.") == "Body text."


def test_token_budget_is_language_aware():
    zh = pipeline._max_tokens(800, "zh")
    en = pipeline._max_tokens(800, "en")
    assert zh < en, "Chinese needs fewer tokens for the same character budget"
    assert pipeline._max_tokens(100, "zh") >= 300
    assert pipeline._max_tokens(100000, "en") <= 6000
