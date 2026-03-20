"""
FormattingSkill - Reusable skill for formatting academic papers.

Handles citation formatting, section formatting, and template application
for different academic styles (APA, MLA, IEEE, GB/T7714).
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Reference:
    """Represents a bibliographic reference."""
    authors: List[str]
    year: Optional[int]
    title: str
    source: str
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None


class FormattingSkill:
    """
    Skill for formatting academic papers.

    Supports:
    - APA (7th Edition)
    - MLA (9th Edition)
    - IEEE
    - GB/T7714 (Chinese Standard)
    """

    # Citation style identifiers
    STYLES = ["apa", "mla", "ieee", "gbt7714"]

    def __init__(self):
        """Initialize the formatting skill."""
        self.current_style = "apa"

    def format_references(
        self,
        references: List[Dict[str, Any]],
        style: str = "apa"
    ) -> str:
        """
        Format references according to citation style.

        Args:
            references: List of reference dictionaries
            style: Citation style (apa, mla, ieee, gbt7714)

        Returns:
            Formatted reference list as string
        """
        style = style.lower()
        if style not in self.STYLES:
            print(f"Unknown style '{style}', defaulting to APA")
            style = "apa"

        formatted_refs = []

        for i, ref in enumerate(references, 1):
            formatted = self._format_single_reference(ref, style, i)
            formatted_refs.append(formatted)

        return "\n\n".join(formatted_refs)

    def _format_single_reference(
        self,
        ref: Dict[str, Any],
        style: str,
        index: int
    ) -> str:
        """Format a single reference."""
        authors = ref.get("authors", "Unknown")
        year = ref.get("year")
        title = ref.get("title", "Untitled")
        citation = ref.get("citation", "")

        # Parse authors if string
        if isinstance(authors, str):
            author_list = [a.strip() for a in authors.split(",")]
        else:
            author_list = authors

        if style == "apa":
            return self._format_apa(author_list, year, title, citation, ref)
        elif style == "mla":
            return self._format_mla(author_list, year, title, citation, ref)
        elif style == "ieee":
            return self._format_ieee(author_list, year, title, citation, ref, index)
        elif style == "gbt7714":
            return self._format_gbt7714(author_list, year, title, citation, ref, index)

        return f"{authors}. ({year}). {title}. {citation}"

    def _format_apa(
        self,
        authors: List[str],
        year: Optional[int],
        title: str,
        citation: str,
        ref: Dict[str, Any]
    ) -> str:
        """Format reference in APA style."""
        # Format authors
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]} & {authors[1]}"
        elif len(authors) > 2:
            author_str = f"{authors[0]} et al."
        else:
            author_str = authors[0] if authors else "Unknown"

        year_str = str(year) if year else "n.d."

        # Format based on source type (simplified)
        formatted = f"{author_str} ({year_str}). {title}"

        if citation:
            formatted += f". {citation}"

        # Add DOI if available
        doi = ref.get("doi")
        if doi:
            formatted += f". https://doi.org/{doi}"
        elif ref.get("url"):
            formatted += f". {ref['url']}"

        return formatted

    def _format_mla(
        self,
        authors: List[str],
        year: Optional[int],
        title: str,
        citation: str,
        ref: Dict[str, Any]
    ) -> str:
        """Format reference in MLA style."""
        # Format authors
        if len(authors) == 1:
            author_str = authors[0]
        elif len(authors) == 2:
            author_str = f"{authors[0]}, and {authors[1]}"
        elif len(authors) > 2:
            author_str = f"{authors[0]}, et al."
        else:
            author_str = authors[0] if authors else "Unknown"

        year_str = str(year) if year else "n.d."

        # MLA: Author. "Title." Source, Year, pp. pages.
        formatted = f'{author_str}. "{title}."'

        if citation:
            formatted += f" {citation},"

        formatted += f" {year}"

        # Add URL if available
        if ref.get("url"):
            formatted += f". {ref['url']}"

        return formatted

    def _format_ieee(
        self,
        authors: List[str],
        year: Optional[int],
        title: str,
        citation: str,
        ref: Dict[str, Any],
        index: int
    ) -> str:
        """Format reference in IEEE style."""
        # Format authors (initials only)
        author_strs = []
        for author in authors[:6]:  # IEEE allows up to 6 authors
            parts = author.split()
            if parts:
                initials = "".join([p[0] + "." for p in parts[:-1]])
                surname = parts[-1]
                author_strs.append(f"{initials} {surname}")

        if len(authors) > 6:
            author_strs.append("et al.")

        author_str = ", ".join(author_strs) if author_strs else "Unknown"

        year_str = str(year) if year else "n.d."

        # IEEE: [#] A. Author, "Title," Source, vol. x, pp. xx-xx, Year.
        formatted = f"[{index}] {author_str}, \"{title},\""

        if citation:
            formatted += f" {citation},"

        formatted += f" {year_str}"

        return formatted

    def _format_gbt7714(
        self,
        authors: List[str],
        year: Optional[int],
        title: str,
        citation: str,
        ref: Dict[str, Any],
        index: int
    ) -> str:
        """Format reference in GB/T7714 style."""
        # Format authors
        if len(authors) <= 3:
            author_str = ", ".join(authors)
        else:
            author_str = f"{authors[0]} 等"

        year_str = str(year) if year else "n.d."

        # GB/T7714: [序号] 作者. 题名[J]. 刊名, 年份, 卷(期): 页码.
        formatted = f"[{index}] {author_str}. {title}[J]."

        if citation:
            formatted += f" {citation},"

        formatted += f" {year_str}"

        return formatted

    def format_sections(
        self,
        paper: Dict[str, str],
        style: str = "apa"
    ) -> str:
        """
        Format all paper sections into a complete document.

        Args:
            paper: Dictionary with paper sections
            style: Citation style

        Returns:
            Complete formatted paper as string
        """
        output = []

        # Title
        if "title" in paper:
            output.append(paper["title"])
            output.append("=" * len(paper["title"]))
            output.append("")

        # Abstract
        if "abstract" in paper:
            output.append("Abstract")
            output.append("-" * 40)
            output.append(paper["abstract"])
            output.append("")

        # Body sections
        sections = [
            ("introduction", "1. Introduction"),
            ("literature_review", "2. Literature Review"),
            ("methodology", "3. Methodology"),
            ("results", "4. Results"),
            ("discussion", "5. Discussion"),
            ("conclusion", "6. Conclusion"),
        ]

        for key, header in sections:
            if key in paper and paper[key]:
                output.append(header)
                output.append("-" * 40)
                output.append(paper[key])
                output.append("")

        # References
        if "references" in paper:
            output.append("References")
            output.append("-" * 40)
            output.append(paper["references"])

        return "\n".join(output)

    def apply_template(
        self,
        paper_content: Dict[str, str],
        template_type: str = "default"
    ) -> str:
        """
        Apply a formatting template to the paper.

        Args:
            paper_content: Dictionary with paper sections
            template_type: Template to apply

        Returns:
            Formatted paper as string
        """
        templates = {
            "default": self._default_template,
            "minimal": self._minimal_template,
            "academic": self._academic_template,
        }

        template_func = templates.get(template_type, self._default_template)
        return template_func(paper_content)

    def _default_template(self, paper: Dict[str, str]) -> str:
        """Default paper template."""
        lines = [
            "# " + paper.get("title", "Untitled"),
            "",
            "## Abstract",
            paper.get("abstract", ""),
            "",
            "## Introduction",
            paper.get("introduction", ""),
            "",
            "## Literature Review",
            paper.get("literature_review", ""),
            "",
            "## Methodology",
            paper.get("methodology", ""),
            "",
            "## Results",
            paper.get("results", ""),
            "",
            "## Discussion",
            paper.get("discussion", ""),
            "",
            "## Conclusion",
            paper.get("conclusion", ""),
            "",
            "## References",
            paper.get("references", ""),
        ]
        return "\n\n".join(lines)

    def _minimal_template(self, paper: Dict[str, str]) -> str:
        """Minimal paper template."""
        lines = [
            paper.get("title", "Untitled"),
            "",
            paper.get("abstract", ""),
            "",
            paper.get("introduction", ""),
            "",
            paper.get("conclusion", ""),
            "",
            paper.get("references", ""),
        ]
        return "\n\n".join(lines)

    def _academic_template(self, paper: Dict[str, str]) -> str:
        """Academic paper template with proper formatting."""
        lines = [
            "=" * 80,
            paper.get("title", "Untitled").center(80),
            "=" * 80,
            "",
            "ABSTRACT",
            "-" * 80,
            paper.get("abstract", ""),
            "",
            "=" * 80,
            "",
            "1. INTRODUCTION",
            "-" * 40,
            paper.get("introduction", ""),
            "",
            "2. LITERATURE REVIEW",
            "-" * 40,
            paper.get("literature_review", ""),
            "",
            "3. METHODOLOGY",
            "-" * 40,
            paper.get("methodology", ""),
            "",
            "4. RESULTS",
            "-" * 40,
            paper.get("results", ""),
            "",
            "5. DISCUSSION",
            "-" * 40,
            paper.get("discussion", ""),
            "",
            "6. CONCLUSION",
            "-" * 40,
            paper.get("conclusion", ""),
            "",
            "REFERENCES",
            "-" * 40,
            paper.get("references", ""),
            "",
            "=" * 80,
        ]
        return "\n".join(lines)

    def save_to_file(
        self,
        paper: Dict[str, str],
        filename: str,
        format_type: str = "markdown"
    ) -> str:
        """
        Save formatted paper to file.

        Args:
            paper: Paper content dictionary
            filename: Output filename
            format_type: Output format (markdown, txt, html)

        Returns:
            Path to saved file
        """
        from pathlib import Path

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / filename

        if format_type == "markdown":
            content = self.apply_template(paper, "academic")
            if not filename.endswith(".md"):
                filepath = filepath.with_suffix(".md")
        elif format_type == "html":
            content = self._convert_to_html(paper)
            if not filename.endswith(".html"):
                filepath = filepath.with_suffix(".html")
        else:
            content = self.apply_template(paper, "default")
            if not filename.endswith(".txt"):
                filepath = filepath.with_suffix(".txt")

        filepath.write_text(content, encoding="utf-8")
        return str(filepath)

    def _convert_to_html(self, paper: Dict[str, str]) -> str:
        """Convert paper to HTML format."""
        html = ["<!DOCTYPE html>", "<html>", "<head>",
                "<title>" + paper.get("title", "Paper") + "</title>",
                "<style>",
                "body { font-family: Georgia, serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
                "h1 { text-align: center; }",
                "h2 { border-bottom: 1px solid #ccc; }",
                "</style>",
                "</head>", "<body>"]

        html.append("<h1>" + paper.get("title", "Untitled") + "</h1>")

        sections = [
            ("abstract", "Abstract"),
            ("introduction", "Introduction"),
            ("literature_review", "Literature Review"),
            ("methodology", "Methodology"),
            ("results", "Results"),
            ("discussion", "Discussion"),
            ("conclusion", "Conclusion"),
            ("references", "References"),
        ]

        for key, title in sections:
            if key in paper and paper[key]:
                html.append(f"<h2>{title}</h2>")
                # Convert newlines to paragraphs
                paragraphs = paper[key].split("\n\n")
                for para in paragraphs:
                    if para.strip():
                        html.append(f"<p>{para}</p>")

        html.extend(["</body>", "</html>"])

        return "\n".join(html)
