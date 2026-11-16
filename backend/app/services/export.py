"""Export a generated paper to Markdown, DOCX, PDF and BibTeX."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

from .pipeline import word_count

SECTION_LABELS = {
    "en": {
        "abstract": "Abstract",
        "keywords": "Keywords",
        "introduction": "1. Introduction",
        "literature_review": "2. Literature Review",
        "methodology": "3. Methodology",
        "results": "4. Results",
        "discussion": "5. Discussion",
        "conclusion": "6. Conclusion",
        "references": "References",
    },
    "zh": {
        "abstract": "摘要",
        "keywords": "关键词",
        "introduction": "一、引言",
        "literature_review": "二、文献综述",
        "methodology": "三、研究方法",
        "results": "四、研究结果",
        "discussion": "五、讨论",
        "conclusion": "六、结论",
        "references": "参考文献",
    },
}

ORDER = ["introduction", "literature_review", "methodology", "results", "discussion", "conclusion"]


def _labels(language: str) -> Dict[str, str]:
    return SECTION_LABELS.get(language, SECTION_LABELS["en"])


def paper_to_markdown(paper: Dict[str, Any]) -> str:
    request = paper.get("request") or {}
    sections = paper.get("sections") or {}
    labels = _labels(request.get("language", "en"))
    lines: List[str] = [f"# {paper.get('title') or request.get('title', 'Untitled')}", ""]
    author = paper.get("author_name")
    if author:
        lines.append(f"**{author}**")
        lines.append("")
    if request.get("field"):
        lines.append(f"*{request['field']}*")
        lines.append("")
    lines.append(f"> {' '.join(request.get('keywords') or [])}")
    lines.append("")
    lines.append(f"## {labels['abstract']}")
    lines.append("")
    lines.append(sections.get("abstract", ""))
    lines.append("")
    for key in ORDER:
        if sections.get(key):
            lines.append(f"## {labels[key]}")
            lines.append("")
            lines.append(sections[key])
            lines.append("")
    if sections.get("references"):
        lines.append(f"## {labels['references']}")
        lines.append("")
        lines.append(sections["references"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _bibtex_key(ref: Dict[str, Any], index: int) -> str:
    authors = ref.get("authors") or []
    family = "".join(ch for ch in (authors[0].split()[-1] if authors else "anon") if ch.isalnum())
    year = ref.get("year") or "nd"
    first_word = "".join(ch for ch in (ref.get("title") or "").split(" ")[:1].__str__() if ch.isalnum())
    return f"{family.lower()}{year}{first_word.lower() or index}"


def paper_to_bibtex(paper: Dict[str, Any]) -> str:
    entries: List[str] = []
    for i, ref in enumerate(paper.get("references") or [], start=1):
        authors = " and ".join(ref.get("authors") or []) or "Unknown"
        fields = [
            f"  title = {{{ref.get('title', '')}}}",
            f"  author = {{{authors}}}",
            f"  year = {{{ref.get('year', '')}}}",
        ]
        if ref.get("venue"):
            fields.append(f"  journal = {{{ref['venue']}}}")
        if ref.get("doi"):
            fields.append(f"  doi = {{{ref['doi']}}}")
        if ref.get("url"):
            fields.append(f"  url = {{{ref['url']}}}")
        entries.append(
            "@article{" + _bibtex_key(ref, i) + ",\n" + ",\n".join(fields) + "\n}"
        )
    return "\n\n".join(entries) + ("\n" if entries else "")


# ---------------------------------------------------------------------------
# DOCX
# ---------------------------------------------------------------------------

def _set_run_font(run, latin: str, east_asia: str, size: float, bold: bool = False) -> None:
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east_asia)


def _docx_paragraph(doc: Document, text: str, *, east_asia: str, latin: str, size: float,
                    first_line_indent: bool = True, justify: bool = True) -> None:
    for chunk in [c for c in re.split(r"\n+", text) if c.strip()]:
        paragraph = doc.add_paragraph()
        fmt = paragraph.paragraph_format
        fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        fmt.space_after = Pt(6)
        if first_line_indent:
            fmt.first_line_indent = Cm(0.74)
        if justify:
            fmt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = paragraph.add_run(chunk.strip())
        _set_run_font(run, latin, east_asia, size)


def build_docx(paper: Dict[str, Any], path: Path) -> Path:
    request = paper.get("request") or {}
    sections = paper.get("sections") or {}
    language = request.get("language", "en")
    labels = _labels(language)
    east = "宋体" if language == "zh" else "Times New Roman"

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        from docx.oxml import OxmlElement

        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:eastAsia"), east)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(12)
    run = title.add_run(paper.get("title") or request.get("title", ""))
    _set_run_font(run, "Times New Roman", "黑体", 18, bold=True)

    author_name = paper.get("author_name")
    if author_name:
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = meta.add_run(author_name)
        _set_run_font(run, "Times New Roman", east, 12)
    if request.get("field"):
        meta = doc.add_paragraph()
        meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = meta.add_run(request["field"])
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
        _set_run_font(run, "Times New Roman", east, 10.5)

    def heading(text: str) -> None:
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(12)
        paragraph.paragraph_format.space_after = Pt(6)
        run = paragraph.add_run(text)
        _set_run_font(run, "Times New Roman", "黑体", 14, bold=True)

    heading(labels["abstract"])
    _docx_paragraph(doc, sections.get("abstract", ""), east_asia=east, latin="Times New Roman", size=10.5)
    if request.get("keywords"):
        paragraph = doc.add_paragraph()
        run = paragraph.add_run(f"{labels['keywords']}: {'; '.join(request['keywords'])}")
        _set_run_font(run, "Times New Roman", east, 10.5, bold=False)

    for key in ORDER:
        if not sections.get(key):
            continue
        heading(labels[key])
        _docx_paragraph(doc, sections[key], east_asia=east, latin="Times New Roman", size=12)

    if sections.get("references"):
        heading(labels["references"])
        for entry in [line for line in sections["references"].split("\n") if line.strip()]:
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Cm(0.74)
            paragraph.paragraph_format.first_line_indent = Cm(-0.74)
            paragraph.paragraph_format.space_after = Pt(3)
            paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            run = paragraph.add_run(entry.strip())
            _set_run_font(run, "Times New Roman", east, 10.5)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))
    return path


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------

def _register_pdf_font(language: str) -> str:
    if language == "zh":
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            return "STSong-Light"
        except Exception:
            pass
    return "Helvetica"


def build_pdf(paper: Dict[str, Any], path: Path) -> Path:
    request = paper.get("request") or {}
    sections = paper.get("sections") or {}
    language = request.get("language", "en")
    labels = _labels(language)
    font = _register_pdf_font(language)
    base = ParagraphStyle("base", fontName=font, fontSize=11, leading=18, spaceAfter=8,
                          firstLineIndent=22, alignment=4)
    title_style = ParagraphStyle("title", fontName=font, fontSize=18, leading=26,
                                 alignment=1, spaceAfter=14)
    author_style = ParagraphStyle("author", fontName=font, fontSize=11, leading=18, alignment=1)
    heading_style = ParagraphStyle("heading", fontName=font, fontSize=14, leading=22,
                                   spaceBefore=14, spaceAfter=8, spaceIndent=0)
    ref_style = ParagraphStyle("ref", fontName=font, fontSize=9.5, leading=15,
                               leftIndent=18, firstLineIndent=-18, spaceAfter=4)

    def esc(text: str) -> str:
        return (
            (text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    story: List[Any] = [Paragraph(esc(paper.get("title") or request.get("title", "")), title_style)]
    if paper.get("author_name"):
        story.append(Paragraph(esc(paper["author_name"]), author_style))
    if request.get("field"):
        story.append(Paragraph(esc(request["field"]), author_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph(esc(labels["abstract"]), heading_style))
    for chunk in (sections.get("abstract", "") or "").split("\n"):
        if chunk.strip():
            story.append(Paragraph(esc(chunk.strip()), base))
    if request.get("keywords"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>{esc(labels['keywords'])}:</b> {esc('; '.join(request['keywords']))}", base))

    for key in ORDER:
        if not sections.get(key):
            continue
        story.append(Paragraph(esc(labels[key]), heading_style))
        for chunk in sections[key].split("\n"):
            if chunk.strip():
                story.append(Paragraph(esc(chunk.strip()), base))

    if sections.get("references"):
        story.append(PageBreak())
        story.append(Paragraph(esc(labels["references"]), heading_style))
        for entry in [line for line in sections["references"].split("\n") if line.strip()]:
            story.append(Paragraph(esc(entry.strip()), ref_style))

    path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=3.0 * cm,
        rightMargin=3.0 * cm,
        topMargin=2.54 * cm,
        bottomMargin=2.54 * cm,
        title=paper.get("title") or "",
        author=paper.get("author_name") or "",
    )
    doc.build(story)
    return path


def safe_filename(title: str, suffix: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|\r\n]+", " ", title or "paper").strip()
    cleaned = re.sub(r"\s+", "_", cleaned)[:60] or "paper"
    return f"{cleaned}{suffix}"
