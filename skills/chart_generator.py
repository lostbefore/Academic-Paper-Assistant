"""
ChartGeneratorSkill - Generate academic charts and diagrams using AI + code.

Converts text descriptions into:
- Mermaid diagrams (flowcharts, sequence diagrams, etc.)
- Matplotlib data visualizations
"""

import json
import re
from typing import Dict, List, Optional
from pathlib import Path

import anthropic


class ChartGeneratorSkill:
    """Generate charts from text descriptions using AI."""

    # Chart type definitions for prompts
    CHART_TYPES = {
        "flowchart": "Flowchart showing processes, steps, or workflows",
        "architecture": "System architecture or component diagram",
        "timeline": "Timeline or sequence of events",
        "comparison": "Comparison table or diagram",
        "hierarchy": "Hierarchical structure (org chart, taxonomy)",
        "relationship": "Entity relationship or network diagram",
        "cycle": "Circular or cyclic process",
        "bar_chart": "Bar chart for comparing quantities",
        "line_chart": "Line chart showing trends over time",
        "pie_chart": "Pie chart showing proportions",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the chart generator skill."""
        self.api_key = api_key
        self.api_base = api_base
        self.model = model or "claude-sonnet-4-6-20251001"

        if api_key:
            client_kwargs = {"api_key": api_key}
            if api_base:
                client_kwargs["base_url"] = api_base
            self.client = anthropic.Anthropic(**client_kwargs)
        else:
            self.client = None

    def suggest_charts(
        self,
        section_name: str,
        section_content: str,
        paper_title: str,
        max_charts: int = 2
    ) -> List[Dict[str, str]]:
        """
        Analyze section content and suggest appropriate charts.

        Args:
            section_name: Name of the section
            section_content: Content of the section
            paper_title: Title of the paper
            max_charts: Maximum number of charts to suggest

        Returns:
            List of chart suggestions with type and description
        """
        if not self.client:
            return self._fallback_suggestions(section_name)

        prompt = f"""Analyze this academic paper section and suggest appropriate visualizations.

Paper Title: {paper_title}
Section: {section_name}

Section Content:
{section_content[:1500]}...

Available chart types:
{chr(10).join(f"- {k}: {v}" for k, v in self.CHART_TYPES.items())}

Task: Suggest up to {max_charts} charts that would enhance this section.

For each chart, provide:
1. type: The chart type from the list above
2. title: A concise, academic title
3. description: What the chart should show (2-3 sentences)
4. complexity: "simple" or "detailed"

Respond ONLY with a JSON array:
[
  {{
    "type": "flowchart",
    "title": "Research Methodology Flow",
    "description": "Shows the step-by-step process of data collection and analysis",
    "complexity": "detailed"
  }}
]

If no charts are appropriate, return an empty array []."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Extract JSON from response
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions[:max_charts]

            return []

        except Exception as e:
            print(f"Chart suggestion failed: {e}")
            return self._fallback_suggestions(section_name)

    def _fallback_suggestions(self, section_name: str) -> List[Dict[str, str]]:
        """Fallback chart suggestions based on section name."""
        defaults = {
            "methodology": [
                {"type": "flowchart", "title": "Research Methodology", "description": "Overview of research steps", "complexity": "detailed"}
            ],
            "results": [
                {"type": "bar_chart", "title": "Key Findings", "description": "Comparison of main results", "complexity": "simple"}
            ],
            "introduction": [
                {"type": "hierarchy", "title": "Research Framework", "description": "Structure of the research approach", "complexity": "simple"}
            ],
        }
        return defaults.get(section_name.lower(), [])

    def generate_mermaid_code(
        self,
        chart_type: str,
        title: str,
        description: str,
        section_context: str,
        complexity: str = "detailed"
    ) -> Optional[str]:
        """
        Generate Mermaid diagram code from description.

        Args:
            chart_type: Type of chart
            title: Chart title
            description: What the chart should show
            section_context: Context from the paper section
            complexity: "simple" or "detailed"

        Returns:
            Mermaid code string or None
        """
        if not self.client:
            return None

        complexity_guide = {
            "simple": "5-8 nodes, clear and straightforward",
            "detailed": "8-15 nodes, comprehensive but readable"
        }

        prompt = f"""Generate Mermaid diagram code for an academic paper figure.

Chart Type: {chart_type}
Title: {title}
Description: {description}
Complexity: {complexity_guide.get(complexity, complexity_guide["detailed"])}

Section Context:
{section_context[:1000]}...

Requirements:
1. Use appropriate Mermaid syntax for the chart type
2. Include clear labels for all nodes/elements
3. Use academic, professional styling
4. Ensure the diagram is self-contained and understandable
5. For flowcharts: use LR (left-to-right) direction for better layout

Mermaid Syntax Examples:

Flowchart:
```mermaid
flowchart LR
    A[Start] --> B[Process 1]
    B --> C[Process 2]
    C --> D[End]
```

Architecture:
```mermaid
graph TB
    subgraph System
        A[Component A] --> B[Component B]
        B --> C[Component C]
    end
```

Timeline:
```mermaid
timeline
    title Project Timeline
    Phase 1 : Task 1 : Task 2
    Phase 2 : Task 3 : Task 4
```

Respond ONLY with the Mermaid code (no ```mermaid fences, no explanations).
Start directly with the diagram type (e.g., "flowchart LR", "graph TB", etc.)."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            code = response.content[0].text.strip()

            # Clean up the code
            code = re.sub(r'```mermaid\s*', '', code)
            code = re.sub(r'```\s*$', '', code)
            code = code.strip()

            # Basic validation
            if not code or len(code) < 20:
                return None

            return code

        except Exception as e:
            print(f"Mermaid code generation failed: {e}")
            return None

    def generate_chart_data(
        self,
        chart_type: str,
        description: str,
        section_context: str
    ) -> Optional[Dict]:
        """
        Generate data for matplotlib charts.

        Args:
            chart_type: Type of chart (bar_chart, line_chart, pie_chart)
            description: What the chart should show
            section_context: Context from the paper

        Returns:
            Dictionary with chart data or None
        """
        if not self.client:
            return None

        prompt = f"""Generate realistic data for an academic chart.

Chart Type: {chart_type}
Description: {description}

Section Context:
{section_context[:1000]}...

Task: Generate appropriate data for a {chart_type} that matches the research context.

Respond with ONLY a JSON object:

For bar_chart/line_chart:
{{
    "x": ["Category1", "Category2", "Category3"],
    "y": [45, 67, 89],
    "xlabel": "X Axis Label",
    "ylabel": "Y Axis Label"
}}

For pie_chart:
{{
    "values": [30, 45, 25],
    "labels": ["Group A", "Group B", "Group C"]
}}

Guidelines:
1. Use realistic, believable numbers
2. Labels should be academic and relevant
3. Include 3-6 data points
4. Axis labels should be descriptive"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=800,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return None

        except Exception as e:
            print(f"Chart data generation failed: {e}")
            return None

    def create_figure_placeholder(
        self,
        figure_num: int,
        title: str,
        chart_type: str,
        content: str
    ) -> str:
        """
        Create a placeholder marker for DOCX insertion.

        Args:
            figure_num: Figure number
            title: Figure title
            chart_type: Type of chart
            content: Mermaid code or data description

        Returns:
            Placeholder string for DOCX processing
        """
        return f"[FIGURE:{figure_num}:{chart_type}:{title}:{content}]"

    def parse_figure_marker(self, marker: str) -> Optional[Dict]:
        """
        Parse a figure marker back into components.

        Args:
            marker: The marker string

        Returns:
            Dictionary with figure info or None
        """
        pattern = r'\[FIGURE:(\d+):([^:]+):([^:]+):(.+)\]'
        match = re.match(pattern, marker)

        if match:
            return {
                "number": int(match.group(1)),
                "type": match.group(2),
                "title": match.group(3),
                "content": match.group(4)
            }

        return None
