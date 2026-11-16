"""
ResearchAgent - Specialized agent for research tasks.

Analyzes paper topics, generates research questions,
retrieves literature, and summarizes research background.
"""

from typing import List, Dict, Any, Optional
import json

import anthropic

from skills.literature_search import LiteratureSearchSkill
from skills.image_search import ImageSearchSkill
from skills.pdf_image_extractor import PDFImageExtractor


class ResearchAgent:
    """
    Research Agent responsible for:
    - Analyzing paper topics
    - Generating research questions
    - Retrieving literature
    - Summarizing research background
    """

    def __init__(
        self,
        api_key: Optional[str],
        literature_skill: LiteratureSearchSkill,
        image_skill: Optional[ImageSearchSkill] = None,
        pdf_extractor: Optional[PDFImageExtractor] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the Research Agent.

        Args:
            api_key: Anthropic API key
            literature_skill: Literature search skill instance
            image_skill: Optional image search skill instance
            pdf_extractor: Optional PDF image extractor instance
            api_base: Optional custom API base URL for third-party providers
            model: Optional custom model name
        """
        self.api_key = api_key
        self.literature_skill = literature_skill
        self.image_skill = image_skill
        self.pdf_extractor = pdf_extractor
        self.model = model or "claude-sonnet-4-6-20251001"

        # Initialize client with optional custom base URL
        if api_key:
            client_kwargs = {"api_key": api_key}
            if api_base:
                client_kwargs["base_url"] = api_base
            self.client = anthropic.Anthropic(**client_kwargs)
        else:
            self.client = None

    def analyze_topic(
        self,
        paper_title: str,
        keywords: List[str],
        research_field: str,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Analyze the paper topic and generate research context.

        Args:
            paper_title: Title of the paper
            keywords: List of research keywords
            research_field: Research field/domain
            language: Language for the research content (english/chinese)

        Returns:
            Dictionary containing research analysis
        """
        print(f"Analyzing topic: {paper_title} in {language}")

        self.language = language

        # Generate research questions using Claude
        research_questions = self._generate_research_questions(
            paper_title, keywords, research_field
        )

        # Search for relevant literature
        print("Searching academic literature...")
        literature = self.literature_skill.search_papers(
            topic=paper_title,
            keywords=keywords
        )

        # Summarize research background
        background = self._summarize_background(
            paper_title, keywords, research_field, literature
        )

        # Search for relevant images (concepts, diagrams, etc.)
        images = self._search_related_images(
            paper_title, keywords, research_field
        )

        # Extract images from found literature (PDF papers)
        literature_images = self._extract_images_from_literature(
            literature, paper_title, keywords, research_field
        )
        images.extend(literature_images)

        return {
            "title": paper_title,
            "keywords": keywords,
            "field": research_field,
            "research_questions": research_questions,
            "background": background,
            "literature": literature,
            "literature_count": len(literature),
            "images": images,
            "image_count": len(images),
            "language": language
        }

    def _generate_research_questions(
        self,
        paper_title: str,
        keywords: List[str],
        research_field: str
    ) -> List[str]:
        """
        Generate relevant research questions using AI.

        Args:
            paper_title: Title of the paper
            keywords: List of research keywords
            research_field: Research field/domain

        Returns:
            List of research questions
        """
        if not self.client:
            return self._fallback_research_questions(paper_title, keywords)

        language = getattr(self, 'language', 'english')

        if language == "chinese":
            prompt = f"""你是{research_field}领域的学术研究专家。

根据以下论文标题和关键词，生成3-5个本论文应该回答的研究问题。

论文标题：{paper_title}
关键词：{', '.join(keywords)}

要求：
- 具体且可研究
- 与领域相关
- 能够在学术论文中得到解决
- 用中文表述

以JSON数组格式返回研究问题。"""
        else:
            prompt = f"""You are an academic research expert in {research_field}.

Given the following paper title and keywords, generate 3-5 focused research questions
that this paper should address.

Paper Title: {paper_title}
Keywords: {', '.join(keywords)}

Provide the research questions as a numbered list. Each question should be:
- Specific and researchable
- Relevant to the field
- Capable of being addressed in an academic paper

Format your response as a JSON array of strings."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            # Extract JSON from response
            questions = self._extract_json_from_text(content)
            if questions and isinstance(questions, list):
                return questions

        except Exception as e:
            print(f"Warning: Could not generate research questions with AI: {e}")

        return self._fallback_research_questions(paper_title, keywords, language)

    def _summarize_background(
        self,
        paper_title: str,
        keywords: List[str],
        research_field: str,
        literature: List[Dict[str, Any]]
    ) -> str:
        """
        Summarize research background based on literature.

        Args:
            paper_title: Title of the paper
            keywords: List of research keywords
            research_field: Research field
            literature: List of literature items

        Returns:
            Background summary text
        """
        if not self.client:
            return self._fallback_background(literature)

        language = getattr(self, 'language', 'english')

        # Prepare literature summary for the prompt
        lit_summary = "\n".join([
            f"{i+1}. {paper['title']} ({paper.get('year', 'N/A')}) - {paper.get('authors', 'Unknown')}\n"
            f"   Abstract: {paper.get('abstract', 'N/A')[:300]}..."
            for i, paper in enumerate(literature[:5])
        ])

        if language == "chinese":
            prompt = f"""你是{research_field}领域的学术研究专家。

根据以下文献，为题为"{paper_title}"的论文撰写研究背景综述（300-500字）。

关键词：{', '.join(keywords)}

相关文献：
{lit_summary}

你的综述应该：
1. 确定该领域的研究现状
2. 强调现有工作中的空白或挑战
3. 确立研究主题的重要性
4. 自然地引出研究问题

使用适合大学水平论文的学术语气，用中文写作。"""
        else:
            prompt = f"""You are an academic research expert in {research_field}.

Based on the following literature, write a research background summary (300-500 words)
for a paper titled "{paper_title}".

Keywords: {', '.join(keywords)}

Literature Found:
{lit_summary}

Your summary should:
1. Identify the current state of research in this area
2. Highlight gaps or challenges in existing work
3. Establish the significance of the research topic
4. Lead naturally to the research questions

Write in an academic tone suitable for a university-level paper."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        except Exception as e:
            print(f"Warning: Could not generate background with AI: {e}")
            return self._fallback_background(literature, language)

    def _fallback_research_questions(
        self,
        paper_title: str,
        keywords: List[str],
        language: str = "english"
    ) -> List[str]:
        """Generate fallback research questions."""
        if language == "chinese":
            return [
                f"{keywords[0] if keywords else '该领域'}的关键挑战和机遇是什么？",
                f"{paper_title}如何为现有知识体系做出贡献？",
                "哪些方法最适合解决该领域的研究问题？",
                f"这项研究对{keywords[0] if keywords else '该领域'}的实际意义是什么？"
            ]
        return [
            f"What are the key challenges and opportunities in {keywords[0] if keywords else 'this field'}?",
            f"How does {paper_title.lower()} contribute to the existing body of knowledge?",
            f"What methodologies are most effective for addressing research questions in this area?",
            f"What are the practical implications of this research for {keywords[0] if keywords else 'the field'}?"
        ]

    def _fallback_background(self, literature: List[Dict[str, Any]], language: str = "english") -> str:
        """Generate fallback background."""
        if language == "chinese":
            if not literature:
                return "该领域的研究近年来受到广泛关注。"

            background = "该领域的近期研究包括：\n\n"
            for paper in literature[:3]:
                background += f"- {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})\n"
                if paper.get('abstract'):
                    background += f"  {paper['abstract'][:200]}...\n\n"

            return background

        if not literature:
            return "Research in this area has gained significant attention in recent years."

        background = "Recent research in this field includes:\n\n"
        for paper in literature[:3]:
            background += f"- {paper.get('title', 'Unknown')} ({paper.get('year', 'N/A')})\n"
            if paper.get('abstract'):
                background += f"  {paper['abstract'][:200]}...\n\n"

        return background

    def _extract_json_from_text(self, text: str) -> Optional[Any]:
        """Extract JSON from text response."""
        import re

        # Try to find JSON array or object
        patterns = [
            r'\[.*?\]',  # JSON array
            r'\{.*?\}',  # JSON object
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    continue

        return None

    def _search_related_images(
        self,
        paper_title: str,
        keywords: List[str],
        research_field: str
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant images for the paper.

        Args:
            paper_title: Title of the paper
            keywords: List of research keywords
            research_field: Research field

        Returns:
            List of image information dicts
        """
        if not self.image_skill:
            return []

        print("Searching for relevant images...")
        images = []

        # Define search queries for different image types
        search_queries = [
            (f"{research_field} concept diagram", "concept"),
            (f"{keywords[0] if keywords else research_field} illustration", "illustration"),
        ]

        # Add keyword-specific searches
        for keyword in keywords[:2]:
            search_queries.append((f"{keyword} {research_field}", "related"))

        # Search for images (synchronously for now)
        import asyncio

        async def do_searches():
            results = []
            for query, img_type in search_queries[:3]:
                try:
                    found = await self.image_skill.search_images(
                        query, num_results=3, image_type="photo"
                    )
                    for img in found:
                        img["search_type"] = img_type
                        img["search_query"] = query
                        results.append(img)
                except Exception as e:
                    print(f"Image search failed for '{query}': {e}")
            return results

        try:
            # Run async searches
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            images = loop.run_until_complete(do_searches())
            loop.close()

            # Limit to top 5 results
            images = images[:5]
            print(f"Found {len(images)} relevant images")

        except Exception as e:
            print(f"Image search failed: {e}")

        return images

    def _extract_images_from_literature(
        self,
        literature: List[Dict[str, Any]],
        paper_title: str,
        keywords: List[str],
        research_field: str
    ) -> List[Dict[str, Any]]:
        """
        Extract images from found literature (PDF papers).

        Args:
            literature: List of literature items from search
            paper_title: Current paper title (for context)
            keywords: Research keywords
            research_field: Research field

        Returns:
            List of extracted image information
        """
        if not self.pdf_extractor or not literature:
            return []

        print("Extracting images from literature...")
        extracted_images = []

        import asyncio

        async def extract_from_papers():
            results = []

            # Process up to 2 papers with PDF links
            papers_with_pdf = [
                p for p in literature
                if p.get('pdf_url') or p.get('url', '').startswith('http')
            ][:2]

            for i, paper in enumerate(papers_with_pdf):
                try:
                    paper_id = f"lit_{i}_{paper.get('year', 'unknown')}"
                    images = await self.pdf_extractor.extract_images_from_paper(
                        paper,
                        paper_id=paper_id,
                        max_images=2
                    )

                    for img_path in images:
                        results.append({
                            "path": str(img_path),
                            "source_title": paper.get("title", "Unknown"),
                            "source_authors": paper.get("authors", "Unknown"),
                            "source_year": paper.get("year", "Unknown"),
                            "type": "literature"
                        })

                except Exception as e:
                    print(f"Failed to extract from paper {i}: {e}")
                    continue

            return results

        try:
            # Run async extraction
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            extracted_images = loop.run_until_complete(extract_from_papers())
            loop.close()

            print(f"Extracted {len(extracted_images)} images from literature")

        except Exception as e:
            print(f"Literature image extraction failed: {e}")

        return extracted_images

    def get_related_work_summary(self, literature: List[Dict[str, Any]]) -> str:
        """
        Generate a related work section from literature.

        Args:
            literature: List of literature items

        Returns:
            Related work summary text
        """
        if not literature:
            return "Related work in this area is extensive and continues to evolve."

        summary = "## Related Work\n\n"

        for paper in literature[:5]:
            authors = paper.get('authors', 'Unknown')
            year = paper.get('year', 'N/A')
            title = paper.get('title', 'Untitled')
            abstract = paper.get('abstract', '')

            summary += f"**{authors} ({year})** investigated {title}. "
            if abstract:
                summary += f"Their work {abstract[:200]}...\n\n"
            else:
                summary += "\n\n"

        return summary
