"""Prompt construction for the generation pipeline.

Kept in one module so prompt behaviour can be reviewed and tuned in isolation.
All prompts explicitly forbid fabricating data, citations or results.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .citations import citation_examples

LANGUAGE_NAME = {"en": "English", "zh": "Simplified Chinese (简体中文)"}

SECTION_ORDER = [
    "introduction",
    "literature_review",
    "methodology",
    "results",
    "discussion",
    "conclusion",
]

SECTION_TITLES = {
    "en": {
        "introduction": "Introduction",
        "literature_review": "Literature Review",
        "methodology": "Methodology",
        "results": "Results",
        "discussion": "Discussion",
        "conclusion": "Conclusion",
    },
    "zh": {
        "introduction": "引言",
        "literature_review": "文献综述",
        "methodology": "研究方法",
        "results": "研究结果",
        "discussion": "讨论",
        "conclusion": "结论",
    },
}

LENGTH_WORDS = {"short": 3000, "medium": 6000, "long": 9000}

SECTION_SHARE = {
    "introduction": 0.13,
    "literature_review": 0.24,
    "methodology": 0.17,
    "results": 0.19,
    "discussion": 0.17,
    "conclusion": 0.10,
}


def section_titles(language: str) -> Dict[str, str]:
    return SECTION_TITLES.get(language, SECTION_TITLES["en"])


def references_block(refs: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for i, ref in enumerate(refs, start=1):
        authors = ", ".join((ref.get("authors") or [])[:4]) or "Unknown authors"
        year = ref.get("year") or "n.d."
        venue = (ref.get("venue") or "").strip()
        abstract = (ref.get("abstract") or "").strip()
        snippet = (abstract[:420] + "...") if len(abstract) > 420 else abstract
        lines.append(
            f"[{i}] {authors} ({year}). {ref.get('title', '')}. {venue}.\n    Summary: {snippet or 'n/a'}"
        )
    return "\n".join(lines) if lines else "(no external references were retrieved)"


def system_prompt(language: str, citation_style: str) -> str:
    lang = LANGUAGE_NAME.get(language, "English")
    return (
        "You are a senior academic researcher and scientific writing assistant.\n"
        f"Write in {lang}. Use formal academic register, precise terminology and "
        "coherent argumentation.\n"
        "Hard rules:\n"
        "1. Never fabricate empirical data, statistics, experimental results, or citations. "
        "When a number is not given, describe the method or expected pattern qualitatively instead.\n"
        "2. Cite only the references supplied in the prompt. Never invent a reference.\n"
        f"3. {citation_examples(citation_style)}\n"
        "4. Output plain academic prose. Do not add markdown headings, bullet lists or "
        "'Here is the section' meta commentary.\n"
        "5. Remain consistent with the previously written sections that are summarised for you."
    )


def outline_messages(
    *,
    title: str,
    field: str,
    keywords: List[str],
    language: str,
    target_words: int,
    refs: List[Dict[str, Any]],
    instructions: str,
) -> List[Dict[str, str]]:
    lang = LANGUAGE_NAME.get(language, "English")
    prompt = f"""Design a complete academic paper outline.

Topic / working title: {title}
Research field: {field or "general"}
Keywords: {", ".join(keywords) or "(none)"}
Target length: about {target_words} words
Language: {lang}
Extra requirements from the author: {instructions or "(none)"}

Retrieved literature that MUST be the basis for citations (use their numbers):
{references_block(refs)}

Produce strict JSON with this shape:
{{
  "title": "a polished academic title",
  "abstract_brief": "2-3 sentence summary of the argument",
  "research_questions": ["RQ1", "RQ2"],
  "theoretical_framework": "one sentence",
  "method": "the research design you will describe",
  "sections": [
    {{"key": "introduction", "title": "...", "goal": "what this section must accomplish", "words": 800}},
    {{"key": "literature_review", "title": "...", "goal": "...", "words": 1400}},
    {{"key": "methodology", "title": "...", "goal": "...", "words": 1000}},
    {{"key": "results", "title": "...", "goal": "...", "words": 1100}},
    {{"key": "discussion", "title": "...", "goal": "...", "words": 1000}},
    {{"key": "conclusion", "title": "...", "goal": "...", "words": 500}}
  ]
}}
The six keys are mandatory and must keep that exact order. Distribute the word
budget so the total is close to {target_words}. Do not add other top-level keys."""
    return [
        {"role": "system", "content": system_prompt(language, "gbt7714")},
        {"role": "user", "content": prompt},
    ]


def length_phrase(words: int, language: str) -> str:
    """Describe a length budget in the unit the model should actually count."""
    if language == "zh":
        return f"approximately {words} Chinese characters (汉字), and never fewer than {int(words * 0.8)} or more than {int(words * 1.2)}"
    return f"approximately {words} words, and never fewer than {int(words * 0.8)} or more than {int(words * 1.2)}"


def section_messages(
    *,
    section_key: str,
    section_title: str,
    goal: str,
    words: int,
    outline: Dict[str, Any],
    refs: List[Dict[str, Any]],
    language: str,
    citation_style: str,
    previous: List[Dict[str, str]],
    instructions: str = "",
) -> List[Dict[str, str]]:
    lang = LANGUAGE_NAME.get(language, "English")
    prior = "\n".join(
        f"- {item['title']}: {item['summary']}" for item in previous if item.get("summary")
    ) or "(this is the first section)"
    prompt = f"""Write the section "{section_title}" of an academic paper.

Paper title: {outline.get('title')}
Research questions: {"; ".join(outline.get('research_questions') or [])}
Theoretical framework: {outline.get('theoretical_framework', '')}
Method: {outline.get('method', '')}
This section's goal: {goal}
Target length: {length_phrase(words, language)}
Language: {lang}

Sections already written (summaries, stay consistent with them):
{prior}

Available references (cite by their number):
{references_block(refs)}

Requirements:
- Write continuous academic prose of {length_phrase(words, language)}. Do not pad or repeat to reach the length.
- Ground every claim that needs support in the numbered references above.
- Do not fabricate statistics or claim experiments that were not described in the method.
- No headings, no bullet lists, no "In this section..." filler opening.
- {citation_examples(citation_style)}
{("- Extra instruction from the author: " + instructions) if instructions else ""}"""
    return [
        {"role": "system", "content": system_prompt(language, citation_style)},
        {"role": "user", "content": prompt},
    ]


def abstract_messages(
    *,
    title: str,
    sections: Dict[str, str],
    keywords: List[str],
    language: str,
    citation_style: str,
) -> List[Dict[str, str]]:
    lang = LANGUAGE_NAME.get(language, "English")
    body = "\n\n".join(
        f"## {key}\n{value[:1800]}" for key, value in sections.items() if value
    )
    prompt = f"""Write the abstract for the paper "{title}" in {lang}.

Paper body (truncated):
{body}

Requirements:
- {"300-400 Chinese characters (汉字)" if language == "zh" else "200-280 words"}, single paragraph, no citations, no headings.
- State the problem, approach, main argument/findings and contribution.
- Do not invent numeric results that do not appear in the body.
Return ONLY the abstract text."""
    return [
        {"role": "system", "content": system_prompt(language, citation_style)},
        {"role": "user", "content": prompt},
    ]


def keywords_messages(
    *, title: str, abstract: str, language: str, citation_style: str
) -> List[Dict[str, str]]:
    prompt = f"""From this paper title and abstract, produce 4-6 academic keywords.

Title: {title}
Abstract: {abstract[:1200]}

Return ONLY a JSON array of strings, in {LANGUAGE_NAME.get(language, 'English')}."""
    return [
        {"role": "system", "content": system_prompt(language, citation_style)},
        {"role": "user", "content": prompt},
    ]
