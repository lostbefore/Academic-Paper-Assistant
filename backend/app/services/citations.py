"""Reference list formatting for APA / MLA / IEEE / GB-T 7714."""

from __future__ import annotations

import re
from typing import Any, Dict, List

CJK = re.compile(r"[\u4e00-\u9fff]")


def _is_cjk(text: str) -> bool:
    return bool(CJK.search(text or ""))


def _split_name(name: str) -> tuple[str, str]:
    """Return (family, given) for a display name; CJK names stay whole.

    Handles both "Given Family" and "Family, Given" forms.  For CJK names the
    whole string is treated as the family name because the concept of a
    separated given name does not apply in the same way.
    """
    name = (name or "").strip()
    if not name:
        return "", ""
    if _is_cjk(name):
        return name, ""
    if "," in name:
        family, given = name.split(",", 1)
        return family.strip(), given.strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def _initials(given: str) -> str:
    pieces = re.split(r"[\s\-]+", given)
    return " ".join(f"{p[0]}." for p in pieces if p)


def _apa_authors(authors: List[str]) -> str:
    if not authors:
        return ""
    formatted = []
    for name in authors[:20]:
        family, given = _split_name(name)
        if _is_cjk(name):
            formatted.append(name)
        else:
            formatted.append(f"{family}, {_initials(given)}".strip().rstrip(","))
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    return ", ".join(formatted[:19]) + ", ... " + formatted[-1]


def _ieee_authors(authors: List[str]) -> str:
    if not authors:
        return ""
    out = []
    for name in authors[:6]:
        family, given = _split_name(name)
        out.append(name if _is_cjk(name) else f"{_initials(given)} {family}".strip())
    if len(authors) > 6:
        out.append("et al.")
    if len(out) == 1:
        return out[0]
    return ", ".join(out[:-1]) + " and " + out[-1]


def _mla_authors(authors: List[str]) -> str:
    if not authors:
        return ""
    family, given = _split_name(authors[0])
    first = authors[0] if _is_cjk(authors[0]) else f"{family}, {given}".strip().rstrip(",")
    if len(authors) == 1:
        return first
    if len(authors) == 2:
        return f"{first}, and {authors[1]}"
    return f"{first}, et al"


def _gbt_authors(authors: List[str]) -> str:
    if not authors:
        return ""
    out = []
    for name in authors[:3]:
        if _is_cjk(name):
            out.append(name)
        else:
            family, given = _split_name(name)
            out.append(f"{family.upper()} {''.join(p[0] for p in given.split())}".strip())
    text = ", ".join(out)
    if len(authors) > 3:
        text += ", 等"
    return text


def _year(ref: Dict[str, Any]) -> str:
    year = ref.get("year")
    return str(year) if year else "n.d."


def _venue(ref: Dict[str, Any]) -> str:
    return (ref.get("venue") or "").strip().rstrip(".")


def _link(ref: Dict[str, Any]) -> str:
    doi = (ref.get("doi") or "").strip()
    if doi:
        return f"https://doi.org/{doi}"
    return (ref.get("url") or "").strip()


def format_reference(ref: Dict[str, Any], style: str, index: int) -> str:
    title = (ref.get("title") or "Untitled").strip().rstrip(".")
    authors = ref.get("authors") or []
    venue = _venue(ref)
    year = _year(ref)
    link = _link(ref)
    style = (style or "gbt7714").lower()

    if style == "apa":
        parts = [f"{_apa_authors(authors)} ({year})." if authors else f"({year})."]
        parts.append(f"{title}.")
        if venue:
            parts.append(f"*{venue}*.")
        if link:
            parts.append(link)
        return " ".join(p for p in parts if p)
    if style == "mla":
        parts = []
        if authors:
            parts.append(f"{_mla_authors(authors)}.")
        parts.append(f'"{title}."')
        if venue:
            parts.append(f"*{venue}*,")
        parts.append(f"{year}.")
        if link:
            parts.append(link + ".")
        return " ".join(p for p in parts if p)
    if style == "ieee":
        text = f"[{index}] {_ieee_authors(authors)}, " if authors else f"[{index}] "
        text += f'"{title},"'
        if venue:
            text += f" *{venue}*,"
        text += f" {year}."
        if link:
            text += f" doi: {link}."
        return text
    # GB/T 7714-2015
    type_code = "[J]" if (ref.get("type") in ("article", "journal-article", None)) else "[C]"
    text = f"[{index}] {_gbt_authors(authors)}. {title}{type_code}."
    if venue:
        text += f" {venue},"
    text += f" {year}."
    if link:
        text += f" DOI: {link}."
    return re.sub(r"\s+", " ", text).strip()


def build_reference_list(refs: List[Dict[str, Any]], style: str) -> List[str]:
    return [format_reference(ref, style, i + 1) for i, ref in enumerate(refs)]


def citation_examples(style: str) -> str:
    if style in ("ieee", "gbt7714"):
        return (
            "Use numeric citations like [1], [2] that map to the numbered reference list. "
            "Every cited number MUST exist in the list; never invent a number."
        )
    return (
        "Use author-year citations like (Smith, 2023) or (Smith & Lee, 2022). "
        "Only cite authors that appear in the provided reference list; never invent sources."
    )
