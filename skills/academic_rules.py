"""
AcademicRulesSkill - Reusable skill for academic writing rules.

Provides knowledge about academic paper structure, section guidelines,
and writing best practices.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path


class AcademicRulesSkill:
    """
    Skill for managing academic writing rules and structure.

    Provides:
    - Paper structure templates
    - Section-specific guidelines
    - Writing best practices
    """

    def __init__(self, knowledge_dir: Optional[str] = None):
        """
        Initialize the academic rules skill.

        Args:
            knowledge_dir: Directory containing knowledge base files
        """
        if knowledge_dir is None:
            knowledge_dir = Path(__file__).parent.parent / "knowledge"
        self.knowledge_dir = Path(knowledge_dir)

        # Load knowledge base
        self.structure = self._load_structure()
        self.citation_rules = self._load_citation_rules()

    def get_structure(self) -> Dict[str, Any]:
        """
        Get the standard academic paper structure.

        Returns:
            Dictionary with section information
        """
        return self.structure

    def get_section_guidelines(self, section_name: str) -> Dict[str, Any]:
        """
        Get guidelines for a specific section.

        Args:
            section_name: Name of the section

        Returns:
            Dictionary with section guidelines
        """
        section_key = section_name.lower().replace(" ", "_")
        return self.structure.get("sections", {}).get(section_key, {})

    def get_all_sections(self) -> List[str]:
        """Get list of all standard sections."""
        return self.structure.get("section_order", [])

    def _load_structure(self) -> Dict[str, Any]:
        """Load paper structure from knowledge base or defaults."""
        structure_file = self.knowledge_dir / "paper_structure.md"

        if structure_file.exists():
            return self._parse_structure_file(structure_file)

        return self._default_structure()

    def _load_citation_rules(self) -> Dict[str, Any]:
        """Load citation rules from knowledge base."""
        rules_file = self.knowledge_dir / "citation_rules.md"

        if rules_file.exists():
            return self._parse_citation_file(rules_file)

        return self._default_citation_rules()

    def _parse_structure_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse structure markdown file."""
        content = file_path.read_text(encoding="utf-8")

        # Basic parsing - in production, use proper markdown parser
        structure = self._default_structure()

        # Extract sections if defined in file
        if "# Sections" in content:
            # Simple extraction logic
            pass

        return structure

    def _parse_citation_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse citation rules markdown file."""
        content = file_path.read_text(encoding="utf-8")

        # Basic parsing
        rules = self._default_citation_rules()

        return rules

    def _default_structure(self) -> Dict[str, Any]:
        """Default paper structure."""
        return {
            "title": "Standard Academic Paper Structure",
            "description": "IMRaD structure commonly used in academic papers",
            "section_order": [
                "abstract",
                "introduction",
                "literature_review",
                "methodology",
                "results",
                "discussion",
                "conclusion",
                "references"
            ],
            "sections": {
                "abstract": {
                    "name": "Abstract",
                    "purpose": "Summarize the entire paper",
                    "typical_length": "150-350 words",
                    "components": [
                        "Background/context",
                        "Purpose/objective",
                        "Methods",
                        "Key findings",
                        "Significance/implications"
                    ],
                    "guidelines": [
                        "Write last, but place first",
                        "Be concise and informative",
                        "Avoid citations",
                        "Use active voice when possible",
                        "Stand alone - should make sense without the full paper"
                    ]
                },
                "introduction": {
                    "name": "Introduction",
                    "purpose": "Introduce the research problem and context",
                    "typical_length": "10-15% of paper",
                    "components": [
                        "Hook - engaging opening",
                        "Context/background",
                        "Problem statement",
                        "Research questions or hypotheses",
                        "Significance of the study",
                        "Overview of paper structure"
                    ],
                    "guidelines": [
                        "Move from general to specific",
                        "Establish the research territory",
                        "Identify the gap in knowledge",
                        "State purpose clearly",
                        "Engage the reader"
                    ]
                },
                "literature_review": {
                    "name": "Literature Review",
                    "purpose": "Survey and synthesize existing research",
                    "typical_length": "15-25% of paper",
                    "components": [
                        "Thematic organization",
                        "Key studies and findings",
                        "Theoretical frameworks",
                        "Research gaps",
                        "Justification for current study"
                    ],
                    "guidelines": [
                        "Synthesize, don't just summarize",
                        "Identify patterns and trends",
                        "Critically evaluate sources",
                        "Show how your study fits in",
                        "Use recent and relevant sources"
                    ]
                },
                "methodology": {
                    "name": "Methodology",
                    "purpose": "Describe how the research was conducted",
                    "typical_length": "10-15% of paper",
                    "components": [
                        "Research design",
                        "Participants/subjects",
                        "Materials/instruments",
                        "Procedure",
                        "Data analysis methods",
                        "Ethical considerations"
                    ],
                    "guidelines": [
                        "Be precise and detailed",
                        "Allow replication",
                        "Justify methodological choices",
                        "Describe materials clearly",
                        "Explain analysis approach"
                    ]
                },
                "results": {
                    "name": "Results",
                    "purpose": "Present findings without interpretation",
                    "typical_length": "20-25% of paper",
                    "components": [
                        "Descriptive statistics",
                        "Inferential statistics",
                        "Visual presentations",
                        "Qualitative findings"
                    ],
                    "guidelines": [
                        "Present objectively",
                        "Use tables and figures effectively",
                        "Report all relevant results",
                        "Organize logically",
                        "Save interpretation for Discussion"
                    ]
                },
                "discussion": {
                    "name": "Discussion",
                    "purpose": "Interpret results and connect to literature",
                    "typical_length": "20-25% of paper",
                    "components": [
                        "Summary of key findings",
                        "Interpretation of results",
                        "Comparison with previous research",
                        "Theoretical implications",
                        "Practical applications",
                        "Limitations",
                        "Future research directions"
                    ],
                    "guidelines": [
                        "Connect to introduction",
                        "Explain what results mean",
                        "Acknowledge limitations honestly",
                        "Discuss implications broadly",
                        "Support claims with evidence"
                    ]
                },
                "conclusion": {
                    "name": "Conclusion",
                    "purpose": "Summarize and provide closing thoughts",
                    "typical_length": "5-10% of paper",
                    "components": [
                        "Restatement of main findings",
                        "Key contributions",
                        "Broader implications",
                        "Final statement"
                    ],
                    "guidelines": [
                        "Don't introduce new information",
                        "Synthesize, don't repeat",
                        "End with impact",
                        "Be concise",
                        "Connect to opening"
                    ]
                },
                "references": {
                    "name": "References",
                    "purpose": "List all cited sources",
                    "typical_length": "Variable",
                    "components": [
                        "Complete bibliographic information",
                        "Consistent formatting",
                        "Alphabetical order"
                    ],
                    "guidelines": [
                        "Follow chosen style guide strictly",
                        "Include only cited sources",
                        "Verify all details",
                        "Use reference management tools"
                    ]
                }
            }
        }

    def _default_citation_rules(self) -> Dict[str, Any]:
        """Default citation rules for major styles."""
        return {
            "apa": {
                "name": "APA (7th Edition)",
                "in_text": "(Author, Year)",
                "multiple_authors": "(Author1 & Author2, Year)",
                "three_plus_authors": "(Author et al., Year)",
                "reference_format": "Author, A. A. (Year). Title. Source.",
                "notes": [
                    "Use & in parentheses, 'and' in text",
                    "Include DOI when available",
                    "Italicize journal names and volume numbers"
                ]
            },
            "mla": {
                "name": "MLA (9th Edition)",
                "in_text": "(Author Page)",
                "multiple_authors": "(Author1 and Author2 Page)",
                "three_plus_authors": "(Author et al. Page)",
                "reference_format": 'Author. "Title." Source, Year, pp. xx-xx.',
                "notes": [
                    "Include medium of publication",
                    "Use hanging indents",
                    "Cite page numbers in-text"
                ]
            },
            "ieee": {
                "name": "IEEE",
                "in_text": "[1]",
                "multiple_authors": "[1]",
                "reference_format": "[#] A. Author, \"Title,\" Source, vol. x, pp. xx-xx, Year.",
                "notes": [
                    "Number references consecutively",
                    "Use square brackets",
                    "Abbreviate journal names"
                ]
            },
            "gbt7714": {
                "name": "GB/T 7714 (Chinese Standard)",
                "in_text": "[1]",
                "multiple_authors": "[1]",
                "reference_format": "[序号] 主要责任者. 题名[文献类型标识]. 出版信息, 年份.",
                "notes": [
                    "按文中出现顺序编号",
                    "使用中文标点",
                    "注明文献类型标识"
                ]
            }
        }

    def get_citation_style_rules(self, style: str) -> Dict[str, Any]:
        """
        Get rules for a specific citation style.

        Args:
            style: Citation style (apa, mla, ieee, gbt7714)

        Returns:
            Dictionary with style rules
        """
        return self.citation_rules.get(style.lower(), self.citation_rules["apa"])

    def validate_section_content(
        self,
        section_name: str,
        content: str
    ) -> List[str]:
        """
        Validate section content against rules.

        Args:
            section_name: Name of the section
            content: Section content to validate

        Returns:
            List of validation messages
        """
        issues = []
        guidelines = self.get_section_guidelines(section_name)

        # Basic length check
        word_count = len(content.split())
        typical_length = guidelines.get("typical_length", "")

        if "words" in typical_length:
            try:
                # Extract word range
                range_part = typical_length.split(" ")[0]
                if "-" in range_part:
                    min_words, max_words = map(int, range_part.split("-"))
                    if word_count < min_words:
                        issues.append(f"Section may be too short ({word_count} words)")
                    elif word_count > max_words * 1.5:
                        issues.append(f"Section may be too long ({word_count} words)")
            except (ValueError, IndexError):
                pass

        # Check for required components
        components = guidelines.get("components", [])
        content_lower = content.lower()

        # Abstract-specific checks
        if section_name == "abstract":
            if len(content.split()) > 400:
                issues.append("Abstract may be too long")
            if "?" in content:
                issues.append("Abstract should not contain questions")

        # Conclusion-specific checks
        if section_name == "conclusion":
            conclusion_phrases = ["in conclusion", "to conclude", "in summary", "to sum up"]
            if any(phrase in content_lower for phrase in conclusion_phrases):
                issues.append("Avoid cliché opening phrases in conclusion")

        return issues
