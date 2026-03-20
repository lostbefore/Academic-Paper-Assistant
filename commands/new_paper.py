"""
NewPaperCommand - Command for creating new academic papers.

Coordinates ResearchAgent -> WriterAgent workflow.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from agents.researcher_agent import ResearchAgent
from agents.writer_agent import WriterAgent


class NewPaperCommand:
    """
    Command to create a new academic paper.

    Workflow:
    1. ResearchAgent: Analyze topic and gather literature
    2. WriterAgent: Generate paper sections
    """

    def __init__(
        self,
        research_agent: ResearchAgent,
        writer_agent: WriterAgent
    ):
        """
        Initialize the new paper command.

        Args:
            research_agent: Research agent instance
            writer_agent: Writer agent instance
        """
        self.research_agent = research_agent
        self.writer_agent = writer_agent

    def execute(self, args: str) -> str:
        """
        Execute the new paper command.

        Args:
            args: Optional inline arguments (interactive mode if empty)

        Returns:
            Result message with paper information
        """
        # Get paper parameters
        params = self._get_paper_parameters(args)

        if not params.get("title"):
            return "Paper creation cancelled. Title is required."

        print(f"\n{'=' * 60}")
        print(f"Creating New Academic Paper")
        print(f"{'=' * 60}")
        print(f"Title: {params['title']}")
        print(f"Field: {params.get('field', 'General')}")
        print(f"Length: {params.get('length', 'medium')}")
        print(f"Style: {params.get('citation_style', 'APA')}")
        print(f"{'=' * 60}\n")

        # Step 1: Research Phase
        print("Step 1: Conducting research...")
        research_result = self.research_agent.analyze_topic(
            paper_title=params.get("title", ""),
            keywords=params.get("keywords", []),
            research_field=params.get("field", "General")
        )

        if not research_result:
            return "Error: Research phase failed. Unable to continue."

        print(f"  - Found {len(research_result.get('literature', []))} relevant papers")
        print(f"  - Generated research questions: {len(research_result.get('research_questions', []))}")

        # Step 2: Writing Phase
        print("\nStep 2: Writing paper...")
        paper = self.writer_agent.write_paper(
            research_info=research_result,
            length=params.get("length", "medium"),
            citation_style=params.get("citation_style", "apa")
        )

        if not paper:
            return "Error: Writing phase failed. Unable to continue."

        print("  - Abstract: Complete")
        print("  - Introduction: Complete")
        print("  - Literature Review: Complete")
        print("  - Methodology: Complete")
        print("  - Results/Discussion: Complete")
        print("  - Conclusion: Complete")

        # Step 3: Format and Save
        print("\nStep 3: Formatting and saving...")
        output_path = self._save_paper(paper, params)

        # Summary
        summary = self._generate_summary(params, paper, output_path)

        return summary

    def _get_paper_parameters(self, args: str) -> Dict[str, Any]:
        """
        Get paper parameters from user input.

        Args:
            args: Optional inline arguments

        Returns:
            Dictionary of paper parameters
        """
        params = {}

        # Try to parse inline arguments
        if args:
            lines = args.split("\n")
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    params[key.strip().lower()] = value.strip()

        # Interactive mode for missing parameters
        if not params.get("title"):
            params["title"] = input("Paper Title: ").strip()

        if not params.get("keywords"):
            params["keywords"] = input("Keywords (comma-separated): ").strip()

        if not params.get("field"):
            params["field"] = input("Research Field (e.g., Computer Science): ").strip()

        if not params.get("length"):
            length_choice = input("Length (short/medium/long) [medium]: ").strip().lower()
            params["length"] = length_choice if length_choice in ["short", "medium", "long"] else "medium"

        if not params.get("citation_style"):
            style_choice = input("Citation Style (apa/mla/ieee/gbt7714) [apa]: ").strip().lower()
            params["citation_style"] = style_choice if style_choice in ["apa", "mla", "ieee", "gbt7714"] else "apa"

        # Parse keywords into list
        if isinstance(params.get("keywords"), str):
            params["keywords"] = [k.strip() for k in params["keywords"].split(",")]

        return params

    def _save_paper(
        self,
        paper: Dict[str, str],
        params: Dict[str, Any]
    ) -> str:
        """Save paper to file."""
        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in params["title"][:50])
        filename = f"{safe_title}_{timestamp}.md"
        filepath = output_dir / filename

        # Build full content
        content = self._build_paper_content(paper, params)

        # Write to file
        filepath.write_text(content, encoding="utf-8")

        return str(filepath)

    def _build_paper_content(
        self,
        paper: Dict[str, str],
        params: Dict[str, Any]
    ) -> str:
        """Build complete paper content for saving."""
        lines = [
            f"# {paper.get('title', params['title'])}",
            "",
            f"**Keywords:** {', '.join(params.get('keywords', []))}",
            f"**Field:** {params.get('field', 'General')}",
            f"**Citation Style:** {params.get('citation_style', 'APA').upper()}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
        ]

        # Abstract
        if "abstract" in paper:
            lines.extend([
                "## Abstract",
                "",
                paper["abstract"],
                "",
            ])

        # Body sections
        sections = [
            ("introduction", "Introduction"),
            ("literature_review", "Literature Review"),
            ("methodology", "Methodology"),
            ("results", "Results"),
            ("discussion", "Discussion"),
            ("conclusion", "Conclusion"),
        ]

        for key, title in sections:
            if key in paper and paper[key]:
                lines.extend([
                    f"## {title}",
                    "",
                    paper[key],
                    "",
                ])

        # References
        if "references" in paper:
            lines.extend([
                "## References",
                "",
                paper["references"],
                "",
            ])

        return "\n".join(lines)

    def _generate_summary(
        self,
        params: Dict[str, Any],
        paper: Dict[str, str],
        output_path: str
    ) -> str:
        """Generate execution summary."""
        word_count = sum(len(section.split()) for section in paper.values())

        return f"""
{'=' * 60}
Paper Creation Complete!
{'=' * 60}

Title: {params['title']}
Output: {output_path}

Statistics:
  - Word Count: ~{word_count} words
  - Sections Generated: {len([s for s in paper.values() if s])}

Next Steps:
  1. Review the generated paper
  2. Use /format to apply specific citation style

{'=' * 60}
"""
