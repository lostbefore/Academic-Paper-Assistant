"""
FormatCommand - Command for formatting papers.

Applies citation styles and formatting templates to papers.
"""

from typing import Optional
from pathlib import Path

from skills.formatting import FormattingSkill


class FormatCommand:
    """
    Command to format academic papers.

    Supports:
    - Citation style formatting (APA, MLA, IEEE, GB/T7714)
    - Template application
    - Output to different formats (Markdown, HTML, TXT)
    """

    def __init__(self, formatting_skill: FormattingSkill):
        """
        Initialize the format command.

        Args:
            formatting_skill: Formatting skill instance
        """
        self.formatting_skill = formatting_skill

    def execute(self, args: str) -> str:
        """
        Execute the format command.

        Args:
            args: Style and optional file path

        Returns:
            Result message
        """
        # Parse arguments
        parts = args.split(maxsplit=1)

        if not parts:
            return self._show_usage()

        style = parts[0].lower()
        filepath = parts[1].strip() if len(parts) > 1 else None

        # Validate style
        if style not in self.formatting_skill.STYLES:
            return f"Error: Unknown style '{style}'.\nSupported styles: {', '.join(self.formatting_skill.STYLES)}"

        # Get file path if not provided
        if not filepath:
            filepath = input("Enter path to paper file (or press Enter to use example): ").strip()

        if filepath:
            # Load and format existing paper
            return self._format_existing_paper(filepath, style)
        else:
            # Show example formatting
            return self._show_example_formatting(style)

    def _show_usage(self) -> str:
        """Show command usage information."""
        return """
Usage: /format <style> [<filepath>]

Available styles:
  apa      - APA 7th Edition
  mla      - MLA 9th Edition
  ieee     - IEEE style
  gbt7714  - GB/T7714 (Chinese Standard)

Examples:
  /format apa mypaper.md
  /format ieee paper.txt
  /format mla

If no filepath is provided, an example will be shown.
"""

    def _format_existing_paper(self, filepath: str, style: str) -> str:
        """Format an existing paper file."""
        path = Path(filepath)

        if not path.exists():
            return f"Error: File not found: {filepath}"

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

        # Parse paper sections
        paper = self._parse_paper(content)

        print(f"Formatting paper with {style.upper()} style...")

        # Reformat references
        if "references" in paper:
            # Parse references into structured format
            refs = self._parse_references(paper["references"])
            paper["references"] = self.formatting_skill.format_references(refs, style)

        # Apply formatting template
        formatted = self.formatting_skill.apply_template(paper, "academic")

        # Save formatted version
        output_filename = f"{path.stem}_{style}{path.suffix}"
        output_path = path.parent / output_filename

        # Ensure output directory exists
        if not output_path.parent.exists():
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / output_filename

        output_path.write_text(formatted, encoding="utf-8")

        return f"""
Paper formatted successfully!

Style: {style.upper()}
Output: {output_path}

The formatted paper includes:
- {style.upper()} citation formatting
- Standard academic structure
- Consistent section headings

You can now use this formatted version for submission.
"""

    def _parse_paper(self, content: str) -> dict:
        """Parse paper content into sections."""
        paper = {}
        lines = content.split("\n")

        # Extract title
        if lines and lines[0].startswith("# "):
            paper["title"] = lines[0][2:].strip()
        else:
            paper["title"] = "Untitled"

        # Extract sections
        current_section = None
        section_content = []

        section_map = {
            "abstract": ["abstract"],
            "introduction": ["introduction", "1. introduction"],
            "literature_review": ["literature review", "related work", "2. literature review"],
            "methodology": ["methodology", "methods", "3. methodology"],
            "results": ["results", "findings", "4. results"],
            "discussion": ["discussion", "5. discussion"],
            "conclusion": ["conclusion", "conclusions", "6. conclusion"],
            "references": ["references", "bibliography"],
        }

        for line in lines[1:]:
            line_lower = line.lower().strip()

            if line_lower.startswith("## ") or line_lower.startswith("# "):
                if current_section and section_content:
                    paper[current_section] = "\n".join(section_content).strip()

                header_text = line_lower.lstrip("# ").strip()
                current_section = None

                for section_key, headers in section_map.items():
                    if any(h in header_text for h in headers):
                        current_section = section_key
                        break

                section_content = []
            else:
                if current_section:
                    section_content.append(line)

        if current_section and section_content:
            paper[current_section] = "\n".join(section_content).strip()

        return paper

    def _parse_references(self, references_text: str) -> list:
        """Parse references text into structured format."""
        refs = []

        for line in references_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Simple parsing - in production, use proper citation parsing
            ref = {
                "title": line,
                "authors": "Unknown",
                "year": None,
                "citation": "Unknown"
            }

            # Try to extract year
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match:
                ref["year"] = int(year_match.group())

            refs.append(ref)

        return refs

    def _show_example_formatting(self, style: str) -> str:
        """Show example of citation formatting."""
        example_refs = [
            {
                "title": "Example Paper on Machine Learning",
                "authors": "Smith, John A., Doe, Jane B.",
                "year": 2023,
                "citation": "Journal of AI Research, 45(2), 123-145"
            },
            {
                "title": "Deep Learning in Academic Research",
                "authors": "Johnson, Robert C.",
                "year": 2022,
                "citation": "IEEE Transactions on Education, 15(4), 78-92"
            },
            {
                "title": "AI Applications in Higher Education",
                "authors": "Williams, Sarah, Brown, Michael, Davis, Lisa",
                "year": 2024,
                "citation": "Computers & Education, 189, 104785"
            }
        ]

        formatted = self.formatting_skill.format_references(example_refs, style)

        return f"""
{'=' * 60}
Example {style.upper()} Formatting
{'=' * 60}

Sample References:

{formatted}

{'=' * 60}
In-Text Citation Examples:

{self._get_intext_examples(style)}
{'=' * 60}
"""

    def _get_intext_examples(self, style: str) -> str:
        """Get in-text citation examples for a style."""
        examples = {
            "apa": """According to Smith (2023), machine learning has...
Recent studies (Smith, 2023; Johnson, 2022) indicate...
Research shows significant improvement (Williams et al., 2024).""",

            "mla": """According to Smith and Doe, machine learning has...
Recent studies indicate significant progress (Smith and Doe 145).
Research shows improvement (Williams et al. 89).""",

            "ieee": """According to [1], machine learning has...
Recent studies [1], [2] indicate significant progress.
Research shows improvement [3].""",

            "gbt7714": """Smith等[1]指出机器学习已经...
近期研究表明显著进展[1,2]。
研究显示改进[3]。"""
        }

        return examples.get(style, "Examples not available for this style.")
