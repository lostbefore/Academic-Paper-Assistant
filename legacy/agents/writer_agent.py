"""
WriterAgent - Specialized agent for writing academic papers.

Generates complete academic papers based on research information.
Responsible for maintaining academic tone and logical structure.
"""

from typing import Dict, Any, List, Optional
import re

import anthropic

from skills.academic_rules import AcademicRulesSkill
from skills.chart_generator import ChartGeneratorSkill

try:
    from config import Config
except ImportError:
    class Config:
        ENABLE_IMAGES = True
        MAX_IMAGES_PER_PAPER = 3
        IMAGE_SOURCES = ['ai_generate', 'pdf_extract', 'web_search']
        ENABLE_PDF_IMAGE_EXTRACTION = True
        ENABLE_AI_CHARTS = True


class WriterAgent:
    """
    Writer Agent responsible for:
    - Writing academic paper sections
    - Maintaining academic tone
    - Ensuring logical structure
    - Avoiding repetitive AI patterns
    """

    def __init__(
        self,
        api_key: Optional[str],
        academic_rules_skill: AcademicRulesSkill,
        chart_skill: Optional[ChartGeneratorSkill] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        enable_images: bool = True
    ):
        """
        Initialize the Writer Agent.

        Args:
            api_key: Anthropic API key
            academic_rules_skill: Academic rules skill instance
            chart_skill: Optional chart generator skill instance
            api_base: Optional custom API base URL for third-party providers
            model: Optional custom model name
            enable_images: Whether to include images in the paper
        """
        self.api_key = api_key
        self.academic_rules = academic_rules_skill
        self.chart_skill = chart_skill
        self.enable_images = enable_images
        self.model = model or "claude-sonnet-4-6-20251001"

        # Debug: print configuration
        print(f"[WriterAgent] API Key configured: {bool(api_key)}")
        print(f"[WriterAgent] API Base: {api_base or 'default (anthropic)'}")
        print(f"[WriterAgent] Model: {self.model}")

        # Initialize client with optional custom base URL
        if api_key:
            client_kwargs = {"api_key": api_key}
            if api_base:
                client_kwargs["base_url"] = api_base
                print(f"[WriterAgent] Using custom API base: {api_base}")
            else:
                print(f"[WriterAgent] Using default Anthropic API")
            self.client = anthropic.Anthropic(**client_kwargs)
            print(f"[WriterAgent] Client initialized successfully")
        else:
            print(f"[WriterAgent] No API key, client set to None")
            self.client = None

        # AI pattern phrases to avoid
        self.ai_patterns = [
            "in the ever-evolving landscape of",
            "it is important to note that",
            "delve into",
            "tapestry of",
            "multifaceted",
            " underscores the importance of",
            "as we navigate",
            "it is worth noting",
            "in conclusion",
            "furthermore",
            "moreover",
            "however",
            "therefore",
            "consequently",
            "nevertheless",
            "in summary",
            "to conclude",
            "in this essay",
            "this paper will explore",
        ]

    def write_paper(
        self,
        research_info: Dict[str, Any],
        length: str = "medium",
        citation_style: str = "apa",
        language: str = "english"
    ) -> Dict[str, str]:
        """
        Write a complete academic paper.

        Args:
            research_info: Research information from ResearchAgent
            length: Paper length (short/medium/long)
            citation_style: Citation style to use
            language: Language for the paper (english/chinese)

        Returns:
            Dictionary with paper sections
        """
        print(f"Writing {length} paper with {citation_style} citation style in {language}...")

        self.language = language
        self.section_titles = self._get_section_titles(language)

        paper = {}
        structure = self.academic_rules.get_structure()

        # Generate each section
        paper["title"] = research_info["title"]
        paper["abstract"] = self._write_abstract(research_info, length)
        paper["introduction"] = self._write_introduction(research_info, length)
        paper["literature_review"] = self._write_literature_review(research_info, length)

        # Generate figures for methodology and results sections
        figures = []
        paper_id = research_info.get('paper_id', 'default')
        if self.enable_images:
            figures = self._generate_figures(research_info, length, paper_id)

        paper["methodology"] = self._write_methodology(research_info, length, figures)
        paper["results"] = self._write_results(research_info, length, figures)
        paper["discussion"] = self._write_discussion(research_info, length)
        paper["conclusion"] = self._write_conclusion(research_info, length)
        paper["references"] = self._format_references(
            research_info.get("literature", []),
            citation_style,
            research_info
        )
        paper["figures"] = figures

        return paper

    def _get_section_titles(self, language: str) -> Dict[str, str]:
        """Get section titles in the specified language."""
        if language == "chinese":
            return {
                "abstract": "摘要",
                "introduction": "引言",
                "literature_review": "文献综述",
                "methodology": "研究方法",
                "results": "研究结果",
                "discussion": "讨论",
                "conclusion": "结论",
                "references": "参考文献"
            }
        return {
            "abstract": "Abstract",
            "introduction": "Introduction",
            "literature_review": "Literature Review",
            "methodology": "Methodology",
            "results": "Results",
            "discussion": "Discussion",
            "conclusion": "Conclusion",
            "references": "References"
        }

    def _write_abstract(self, research_info: Dict[str, Any], length: str) -> str:
        """Write the abstract section."""
        word_count = {"short": 150, "medium": 250, "long": 350}.get(length, 250)

        prompt = self._build_section_prompt(
            section="Abstract",
            research_info=research_info,
            guidelines=f"Write a concise abstract of approximately {word_count} words. "
                      f"Include: background, purpose, methods, key findings, and significance. "
                      f"Use formal academic language."
        )

        return self._generate_text(prompt, max_tokens=500)

    def _write_introduction(self, research_info: Dict[str, Any], length: str) -> str:
        """Write the introduction section."""
        word_count = {"short": 400, "medium": 800, "long": 1500}.get(length, 800)

        prompt = self._build_section_prompt(
            section="Introduction",
            research_info=research_info,
            guidelines=f"Write an introduction of approximately {word_count} words. "
                      f"Structure: 1) Hook and context, 2) Problem statement, "
                      f"3) Research questions, 4) Significance, 5) Paper overview. "
                      f"Avoid phrases like 'This paper will explore' or 'In this essay'."
        )

        return self._generate_text(prompt, max_tokens=2000)

    def _write_literature_review(self, research_info: Dict[str, Any], length: str) -> str:
        """Write the literature review section."""
        word_count = {"short": 500, "medium": 1000, "long": 2000}.get(length, 1000)
        literature = research_info.get("literature", [])

        lit_context = "\n".join([
            f"- {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')}): "
            f"{paper.get('abstract', 'No abstract')[:200]}..."
            for paper in literature[:5]
        ])

        prompt = self._build_section_prompt(
            section="Literature Review",
            research_info=research_info,
            guidelines=f"Write a literature review of approximately {word_count} words. "
                      f"Synthesize the existing research thematically, not just summarize. "
                      f"Identify gaps that this research addresses.\n\n"
                      f"Available Literature:\n{lit_context}",
            additional_context=lit_context
        )

        return self._generate_text(prompt, max_tokens=2500)

    def _generate_figures(
        self,
        research_info: Dict[str, Any],
        length: str,
        paper_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Generate figures for the paper using multiple sources.

        Sources (in priority order from Config.IMAGE_SOURCES):
        1. ai_generate - AI-generated charts and diagrams
        2. pdf_extract - Extract images from literature PDFs
        3. web_search - Search and download web images
        """
        figures = []

        # Get configuration
        max_images = getattr(Config, 'MAX_IMAGES_PER_PAPER', 3)
        image_sources = getattr(Config, 'IMAGE_SOURCES', ['ai_generate', 'pdf_extract', 'web_search'])
        enable_pdf = getattr(Config, 'ENABLE_PDF_IMAGE_EXTRACTION', True)
        enable_ai = getattr(Config, 'ENABLE_AI_CHARTS', True)

        print(f"\n[Figure Generation] Max images: {max_images}, Sources: {image_sources}")

        # Track figure number
        fig_num = 1

        # Source 1: AI-generated charts
        if 'ai_generate' in image_sources and enable_ai and self.chart_skill and fig_num <= max_images:
            print("\n[Figure Generation] Trying AI-generated charts...")
            ai_figures = self._generate_ai_figures(research_info, length, start_num=fig_num, max_figures=max_images)
            figures.extend(ai_figures)
            fig_num = len(figures) + 1

        # Source 2: Extract from literature PDFs
        if 'pdf_extract' in image_sources and enable_pdf and fig_num <= max_images:
            print("\n[Figure Generation] Trying PDF extraction...")
            literature = research_info.get('literature', [])
            if literature:
                try:
                    from skills.pdf_image_extractor import extract_images_from_literature

                    pdf_images = extract_images_from_literature(
                        literature=literature,
                        paper_id=paper_id,
                        max_total_images=max_images - len(figures)
                    )

                    for img in pdf_images:
                        if fig_num > max_images:
                            break

                        figures.append({
                            'number': fig_num,
                            'type': 'extracted',
                            'title': f"Illustration from related research",
                            'description': f"Extracted from {img.get('source_paper', 'Unknown')}",
                            'content': str(img['filepath']),
                            'content_type': 'file_path',
                            'section': 'literature_review',
                            'filepath': img['filepath']
                        })
                        fig_num += 1

                except Exception as e:
                    print(f"  PDF extraction failed: {e}")

        # Source 3: Web search
        if 'web_search' in image_sources and fig_num <= max_images:
            print("\n[Figure Generation] Trying web image search...")
            try:
                from skills.image_search import ImageSearchSkill

                image_skill = ImageSearchSkill(output_dir=f"output/images/{paper_id}")
                import asyncio

                # Search for relevant images
                search_query = f"{research_info['title']} {research_info['field']} diagram"

                async def search_and_download():
                    results = await image_skill.search_images(search_query, num_results=5)
                    downloaded = []

                    for result in results[:max_images - len(figures)]:
                        filepath = await image_skill.download_image(
                            result['url'],
                            paper_id,
                            fig_num + len(downloaded)
                        )
                        if filepath:
                            downloaded.append({
                                'filepath': filepath,
                                'title': result.get('title', 'Related image')
                            })
                    return downloaded

                web_images = asyncio.run(search_and_download())

                for img in web_images:
                    if fig_num > max_images:
                        break

                    figures.append({
                        'number': fig_num,
                        'type': 'web_image',
                        'title': img['title'],
                        'description': 'Related illustration from web search',
                        'content': str(img['filepath']),
                        'content_type': 'file_path',
                        'section': 'introduction',
                        'filepath': img['filepath']
                    })
                    fig_num += 1

                asyncio.run(image_skill.close())

            except Exception as e:
                print(f"  Web search failed: {e}")

        print(f"\n[Figure Generation] Total figures: {len(figures)}")
        return figures

    def _generate_ai_figures(
        self,
        research_info: Dict[str, Any],
        length: str,
        start_num: int = 1,
        max_figures: int = 2
    ) -> List[Dict[str, Any]]:
        """Generate AI-generated figures."""
        figures = []

        if not self.chart_skill:
            return figures

        # Figure 1: Research framework or methodology overview
        methodology_prompt = f"""Research methodology for: {research_info['title']}
Field: {research_info['field']}
Keywords: {', '.join(research_info.get('keywords', []))}"""

        suggestions = self.chart_skill.suggest_charts(
            section_name="methodology",
            section_content=methodology_prompt,
            paper_title=research_info['title'],
            max_charts=1
        )

        for i, suggestion in enumerate(suggestions, start_num):
            if i > max_figures:
                break

            chart_type = suggestion.get('type', 'flowchart')
            title = suggestion.get('title', f'Figure {i}')
            description = suggestion.get('description', '')
            complexity = suggestion.get('complexity', 'detailed')

            if chart_type in ['flowchart', 'architecture', 'hierarchy', 'timeline']:
                mermaid_code = self.chart_skill.generate_mermaid_code(
                    chart_type=chart_type,
                    title=title,
                    description=description,
                    section_context=methodology_prompt,
                    complexity=complexity
                )

                if mermaid_code:
                    figures.append({
                        'number': i,
                        'type': chart_type,
                        'title': title,
                        'description': description,
                        'content': mermaid_code,
                        'content_type': 'mermaid',
                        'section': 'methodology'
                    })

        # Figure 2: Results/data visualization
        if length != 'short' and len(figures) < max_figures - start_num + 1:
            results_prompt = f"""Expected results for: {research_info['title']}
Field: {research_info['field']}"""

            data_suggestions = self.chart_skill.suggest_charts(
                section_name="results",
                section_content=results_prompt,
                paper_title=research_info['title'],
                max_charts=1
            )

            for j, suggestion in enumerate(data_suggestions, len(figures) + start_num):
                if j > max_figures:
                    break

                chart_type = suggestion.get('type', 'bar_chart')
                title = suggestion.get('title', f'Figure {j}')
                description = suggestion.get('description', '')

                if chart_type in ['bar_chart', 'line_chart', 'pie_chart']:
                    chart_data = self.chart_skill.generate_chart_data(
                        chart_type=chart_type,
                        description=description,
                        section_context=results_prompt
                    )

                    if chart_data:
                        figures.append({
                            'number': j,
                            'type': chart_type,
                            'title': title,
                            'description': description,
                            'content': chart_data,
                            'content_type': 'chart_data',
                            'section': 'results'
                        })

        return figures

    def _write_methodology(self, research_info: Dict[str, Any], length: str, figures: List[Dict] = None) -> str:
        """Write the methodology section."""
        word_count = {"short": 400, "medium": 800, "long": 1500}.get(length, 800)

        # Check if there's a methodology figure to include
        figure_marker = ""
        if figures:
            method_figures = [f for f in figures if f.get('section') == 'methodology']
            for fig in method_figures:
                figure_marker += f"\n\n[FIGURE:{fig['number']}:{fig['type']}:{fig['title']}]\n\n"

        prompt = self._build_section_prompt(
            section="Methodology",
            research_info=research_info,
            guidelines=f"Write a methodology section of approximately {word_count} words. "
                      f"Describe: 1) Research design, 2) Data collection methods, "
                      f"3) Analysis approach, 4) Justification of chosen methods. "
                      f"Use specific, technical language appropriate for the field."
        )

        text = self._generate_text(prompt, max_tokens=2000)

        # Insert figure marker after the first paragraph or at appropriate location
        if figure_marker:
            paragraphs = text.split('\n\n')
            if len(paragraphs) >= 2:
                # Insert after second paragraph
                insert_pos = 2
                paragraphs.insert(insert_pos, figure_marker.strip())
                text = '\n\n'.join(paragraphs)
            else:
                text = text + figure_marker

        return text

    def _write_results(self, research_info: Dict[str, Any], length: str, figures: List[Dict] = None) -> str:
        """Write the results section."""
        word_count = {"short": 400, "medium": 800, "long": 1500}.get(length, 800)

        # Check if there's a results figure to include
        figure_marker = ""
        if figures:
            results_figures = [f for f in figures if f.get('section') == 'results']
            for fig in results_figures:
                figure_marker += f"\n\n[FIGURE:{fig['number']}:{fig['type']}:{fig['title']}]\n\n"

        prompt = self._build_section_prompt(
            section="Results",
            research_info=research_info,
            guidelines=f"Write a results section of approximately {word_count} words. "
                      f"Present findings objectively. Use subsections if appropriate. "
                      f"Describe patterns, relationships, and key observations. "
                      f"Note: This is a hypothetical/draft paper, so describe expected results."
        )

        text = self._generate_text(prompt, max_tokens=2000)

        # Insert figure marker in the middle or after first paragraph
        if figure_marker:
            paragraphs = text.split('\n\n')
            if len(paragraphs) >= 3:
                # Insert after second paragraph
                insert_pos = min(2, len(paragraphs) - 1)
                paragraphs.insert(insert_pos, figure_marker.strip())
                text = '\n\n'.join(paragraphs)
            else:
                text = text + figure_marker

        return text

    def _write_discussion(self, research_info: Dict[str, Any], length: str) -> str:
        """Write the discussion section."""
        word_count = {"short": 400, "medium": 800, "long": 1500}.get(length, 800)

        prompt = self._build_section_prompt(
            section="Discussion",
            research_info=research_info,
            guidelines=f"Write a discussion section of approximately {word_count} words. "
                      f"Interpret the results, connect to literature, discuss implications, "
                      f"acknowledge limitations, and suggest future research directions."
        )

        return self._generate_text(prompt, max_tokens=2000)

    def _write_conclusion(self, research_info: Dict[str, Any], length: str) -> str:
        """Write the conclusion section."""
        word_count = {"short": 200, "medium": 400, "long": 800}.get(length, 400)

        prompt = self._build_section_prompt(
            section="Conclusion",
            research_info=research_info,
            guidelines=f"Write a conclusion of approximately {word_count} words. "
                      f"Summarize key findings without repetition. Emphasize significance. "
                      f"Avoid phrases like 'In conclusion' or 'To sum up'. "
                      f"End with a strong, forward-looking statement."
        )

        return self._generate_text(prompt, max_tokens=1000)

    def _format_references(
        self,
        literature: List[Dict[str, Any]],
        style: str,
        research_info: Dict[str, Any] = None
    ) -> str:
        """Format references according to citation style."""
        if literature:
            # Use real literature if available
            formatted = []
            for i, paper in enumerate(literature, 1):
                ref = self._format_single_reference(paper, style, i)
                formatted.append(ref)
            return "\n\n".join(formatted)

        # If no real literature, generate realistic references using AI
        print("  - Generating realistic references...")
        return self._generate_references(research_info, style)

    def _generate_references(
        self,
        research_info: Dict[str, Any],
        style: str
    ) -> str:
        """Generate realistic academic references using AI."""
        if not research_info:
            return "References not available."

        field = research_info.get('field', 'General')
        keywords = research_info.get('keywords', [])
        title = research_info.get('title', 'Research Topic')
        language = getattr(self, 'language', 'english')

        style_guide = {
            "apa": "APA 7th Edition (Author, Year. Title. Journal, Volume(Issue), Pages.)",
            "mla": "MLA 9th Edition (Author. \"Title.\" Journal, Year, Pages.)",
            "ieee": "IEEE ([Number] Author, \"Title,\" Journal, Year.)",
            "gbt7714": "GB/T7714 ([Number] Author. Title[J]. Journal, Year, Vol(Issue): Pages.)"
        }

        if language == "chinese":
            prompt = f"""为题为"{title}"的论文生成5-8条 realistic 学术参考文献，领域为{field}。

关键词：{', '.join(keywords)}

引用格式要求：{style_guide.get(style, 'APA')}

要求：
1. 创建 realistic 但虚构的学术引用
2. 包含多种来源类型：期刊文章、会议论文和书籍
3. 使用 realistic 的作者姓名（中英文混合，根据内容需要）和发表年份（2018-2024）
4. 使用 realistic 的期刊/会议名称
5. 严格按照上述{style.upper()}格式要求
6. 标题应与以下内容相关：{', '.join(keywords[:3])}
7. 如果是中文引用，使用中文标题和期刊名；英文引用使用英文

只提供格式化的参考文献，每行一条。不要包含编号、项目符号或任何其他文本。"""
        else:
            prompt = f"""Generate 5-8 realistic academic references for a paper titled "{title}" in the field of {field}.

Keywords: {', '.join(keywords)}

Citation Style Required: {style_guide.get(style, 'APA')}

Requirements:
1. Create realistic but fictional academic citations
2. Include diverse source types: journal articles, conference papers, and books
3. Use realistic author names and publication years (2018-2024)
4. Use realistic journal/conference names for the field
5. Format EXACTLY according to the {style.upper()} style specified above
6. Make titles relevant to: {', '.join(keywords[:3])}

Provide ONLY the formatted references, one per line. Do not include numbering, bullet points, or any other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            references = response.content[0].text.strip()

            # Clean up the response
            lines = [line.strip() for line in references.split('\n') if line.strip()]

            # Add numbering for IEEE and GB/T7714 if needed
            if style in ['ieee', 'gbt7714']:
                formatted_lines = []
                for i, line in enumerate(lines, 1):
                    # Remove existing numbering if present
                    line = line.lstrip('0123456789.[] ').strip()
                    if style == 'ieee':
                        line = f"[{i}] {line}"
                    else:  # gbt7714
                        line = f"[{i}] {line}"
                    formatted_lines.append(line)
                return '\n\n'.join(formatted_lines)

            return '\n\n'.join(lines)

        except Exception as e:
            print(f"Warning: Could not generate references: {e}")
            return "References generation failed."

    def _format_single_reference(
        self,
        paper: Dict[str, Any],
        style: str,
        index: int
    ) -> str:
        """Format a single reference."""
        authors = paper.get('authors', 'Unknown')
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Untitled')
        citation = paper.get('citation', '')

        if style == "apa":
            return f"{authors} ({year}). {title}. {citation}"
        elif style == "mla":
            return f"{authors}. \"{title}.\" {citation}, {year}."
        elif style == "ieee":
            return f"[{index}] {authors}, \"{title},\" {citation}, {year}."
        elif style == "gbt7714":
            return f"[{index}] {authors}. {title}[J]. {citation}, {year}."
        else:
            return f"{authors} ({year}). {title}. {citation}"

    def _build_section_prompt(
        self,
        section: str,
        research_info: Dict[str, Any],
        guidelines: str,
        additional_context: str = ""
    ) -> str:
        """Build a prompt for a specific section."""
        language = getattr(self, 'language', 'english')

        if language == "chinese":
            language_instruction = """重要写作规则：
1. 使用正式的学术中文写作风格
2. 使用规范的学术术语
3. 避免口语化表达
4. 使用被动语态（中文学术论文常见）
5. 使用正确的标点符号（中文标点）
6. 确保语句通顺，逻辑清晰
7. 不要直译英文表达，使用地道的中文学术表达
8. 直接开始写作，不要添加元评论"""
        else:
            language_instruction = """Important Writing Rules:
1. Use formal academic tone but avoid overly flowery language
2. Write in active voice when possible
3. Avoid repetitive transitions and clichés
4. Vary sentence structure
5. Be specific, not vague
6. Use discipline-appropriate terminology
7. DO NOT use phrases like: {', '.join(self.ai_patterns[:10])}
8. Start sections directly without meta-commentary""".format(ai_patterns=self.ai_patterns[:10])

        return f"""You are an expert academic writer specializing in {research_info.get('field', 'academic research')}.

Paper Title: {research_info.get('title', 'Untitled')}
Keywords: {', '.join(research_info.get('keywords', []))}

Research Background:
{research_info.get('background', 'No background available')}

Research Questions:
{chr(10).join(research_info.get('research_questions', []))}

{additional_context}

Task: Write the {section} section.

Guidelines:
{guidelines}

Language Requirement: Write in {language.upper()}. The entire output must be in {language}.

{language_instruction}

Write only the {section} content, no headers or labels."""

    def _generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using Claude API."""
        if not self.client:
            return self._fallback_text(prompt)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text
            return self._post_process_text(text)

        except Exception as e:
            print(f"Warning: AI generation failed: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_text(prompt)

    def _post_process_text(self, text: str) -> str:
        """Post-process text to reduce AI patterns."""
        language = getattr(self, 'language', 'english')

        if language == "chinese":
            # For Chinese text, only clean up excessive whitespace
            # Don't modify Chinese punctuation or characters
            text = re.sub(r' +', ' ', text)  # Only collapse multiple spaces
            text = re.sub(r'\n\n\n+', '\n\n', text)  # Limit consecutive newlines
            return text.strip()

        # For English text, apply full processing
        # Remove common AI phrases
        for pattern in self.ai_patterns:
            text = re.sub(
                rf'\b{re.escape(pattern)}\b',
                '',
                text,
                flags=re.IGNORECASE
            )

        # Clean up double spaces
        text = re.sub(r'\s+', ' ', text)

        # Fix sentences that start with lowercase
        text = re.sub(r'\. ([a-z])', lambda m: f'. {m.group(1).upper()}', text)

        return text.strip()

    def _fallback_text(self, prompt: str) -> str:
        """Generate fallback text when AI is unavailable."""
        # Extract section from prompt
        section_match = re.search(r'Write the (\w+) section', prompt)
        section = section_match.group(1) if section_match else "section"

        return f"[{section.upper()} PLACEHOLDER - AI generation unavailable]\n\n" \
               f"This section would contain academic content about the research topic. " \
               f"Please ensure the Anthropic API key is configured."

    def improve_section(self, section_text: str, improvement_notes: str) -> str:
        """
        Improve a section based on review feedback.

        Args:
            section_text: Original section text
            improvement_notes: Notes on what to improve

        Returns:
            Improved section text
        """
        if not self.client:
            return section_text

        prompt = f"""Improve the following academic text based on the feedback provided.

Original Text:
{section_text}

Improvement Notes:
{improvement_notes}

Rules:
1. Maintain academic tone
2. Preserve the original meaning
3. Implement all suggested improvements
4. Ensure smooth transitions
5. Remove any AI-generated patterns or clichés

Provide the improved text only:"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except Exception as e:
            print(f"Warning: Improvement failed: {e}")
            return section_text
