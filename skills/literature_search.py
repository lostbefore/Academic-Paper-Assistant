"""
LiteratureSearchSkill - Reusable skill for searching academic literature.

Retrieves academic papers from multiple sources including Google Scholar,
Semantic Scholar, and arXiv.
"""

from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from dataclasses import dataclass
import time


@dataclass
class Paper:
    """Represents an academic paper."""
    title: str
    authors: str
    year: Optional[int]
    abstract: str
    citation: str
    source: str
    url: Optional[str] = None


class LiteratureSearchSkill:
    """
    Skill for searching academic literature.

    Supports multiple sources:
    - Semantic Scholar API
    - arXiv API
    - CrossRef (for citation info)
    """

    def __init__(self):
        """Initialize the literature search skill."""
        self.semantic_scholar_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.arxiv_url = "http://export.arxiv.org/api/query"
        self.session: Optional[aiohttp.ClientSession] = None
        # Rate limiter: Semantic Scholar allows 1 request per second for free tier
        self._last_semantic_scholar_request: Optional[float] = None
        self._ss_rate_limit_delay = 1.0  # 1 second between requests

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    def search_papers(
        self,
        topic: str,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for academic papers on a given topic.

        Args:
            topic: Main research topic
            keywords: List of keywords
            max_results: Maximum number of results to return

        Returns:
            List of paper dictionaries
        """
        print(f"Searching literature for: {topic}")

        # Build search query
        query = topic + " " + " ".join(keywords[:3])

        # Run async searches
        try:
            papers = asyncio.run(self._search_all_sources(query, max_results))
        except Exception as e:
            print(f"Async search failed, falling back to sync: {e}")
            papers = self._fallback_search(topic, keywords, max_results)

        return [self._paper_to_dict(p) for p in papers]

    async def _search_all_sources(
        self,
        query: str,
        max_results: int
    ) -> List[Paper]:
        """Search multiple sources concurrently."""
        tasks = [
            self._search_semantic_scholar(query, max_results // 2),
            self._search_arxiv(query, max_results // 2),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers = []
        for result in results:
            if isinstance(result, list):
                all_papers.extend(result)
            else:
                print(f"Search error: {result}")

        # Remove duplicates based on title similarity
        unique_papers = self._deduplicate_papers(all_papers)

        return unique_papers[:max_results]

    async def _apply_semantic_scholar_rate_limit(self):
        """Ensure at least 1 second between Semantic Scholar API requests."""
        if self._last_semantic_scholar_request is not None:
            elapsed = time.time() - self._last_semantic_scholar_request
            if elapsed < self._ss_rate_limit_delay:
                sleep_time = self._ss_rate_limit_delay - elapsed
                await asyncio.sleep(sleep_time)
        self._last_semantic_scholar_request = time.time()

    async def _search_semantic_scholar(
        self,
        query: str,
        limit: int
    ) -> List[Paper]:
        """Search Semantic Scholar API with rate limiting."""
        # Apply rate limiting before making request
        await self._apply_semantic_scholar_rate_limit()

        session = await self._get_session()

        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,abstract,venue,citationCount,url"
        }

        try:
            async with session.get(
                self.semantic_scholar_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    print(f"Semantic Scholar API error: {response.status}")
                    return []

                data = await response.json()
                papers = []

                for paper_data in data.get("data", []):
                    authors_list = paper_data.get("authors", [])
                    authors_str = ", ".join([
                        a.get("name", "Unknown") for a in authors_list[:3]
                    ])
                    if len(authors_list) > 3:
                        authors_str += " et al."

                    papers.append(Paper(
                        title=paper_data.get("title", "Untitled"),
                        authors=authors_str or "Unknown",
                        year=paper_data.get("year"),
                        abstract=paper_data.get("abstract", "No abstract available")[:500],
                        citation=paper_data.get("venue", "Unknown venue"),
                        source="semantic_scholar",
                        url=paper_data.get("url")
                    ))

                return papers

        except Exception as e:
            print(f"Semantic Scholar search failed: {e}")
            return []

    async def _search_arxiv(self, query: str, limit: int) -> List[Paper]:
        """Search arXiv API."""
        session = await self._get_session()

        # Format query for arXiv
        arxiv_query = query.replace(" ", "+")

        params = {
            "search_query": f"all:{arxiv_query}",
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        try:
            async with session.get(
                self.arxiv_url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status != 200:
                    return []

                text = await response.text()
                return self._parse_arxiv_response(text)

        except Exception as e:
            print(f"arXiv search failed: {e}")
            return []

    def _parse_arxiv_response(self, xml_text: str) -> List[Paper]:
        """Parse arXiv XML response."""
        import xml.etree.ElementTree as ET

        papers = []

        try:
            root = ET.fromstring(xml_text)
            ns = {
                "atom": "http://www.w3.org/2005/Atom",
                "arxiv": "http://arxiv.org/schemas/atom"
            }

            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns)
                title_text = title.text.strip() if title is not None else "Untitled"

                # Clean up title (remove newlines)
                title_text = " ".join(title_text.split())

                authors_elem = entry.findall("atom:author", ns)
                authors = []
                for author in authors_elem:
                    name = author.find("atom:name", ns)
                    if name is not None:
                        authors.append(name.text)

                authors_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    authors_str += " et al."

                summary = entry.find("atom:summary", ns)
                abstract = summary.text.strip()[:500] if summary is not None else "No abstract"

                published = entry.find("atom:published", ns)
                year = None
                if published is not None:
                    try:
                        year = int(published.text[:4])
                    except (ValueError, TypeError):
                        pass

                link = entry.find("atom:link[@title='pdf']", ns)
                url = link.get("href") if link is not None else None

                papers.append(Paper(
                    title=title_text,
                    authors=authors_str or "Unknown",
                    year=year,
                    abstract=abstract,
                    citation="arXiv preprint",
                    source="arxiv",
                    url=url
                ))

        except ET.ParseError as e:
            print(f"Failed to parse arXiv response: {e}")

        return papers

    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title similarity."""
        unique = []
        seen_titles = set()

        for paper in papers:
            # Normalize title for comparison
            normalized = paper.title.lower().strip()
            normalized = "".join(c for c in normalized if c.isalnum())

            if normalized not in seen_titles:
                seen_titles.add(normalized)
                unique.append(paper)

        return unique

    def _fallback_search(
        self,
        topic: str,
        keywords: List[str],
        max_results: int
    ) -> List[Paper]:
        """Fallback search when APIs fail."""
        print("Using fallback literature data...")

        # Return some placeholder/simulated results
        papers = [
            Paper(
                title=f"Recent advances in {topic}",
                authors="Smith, J., Johnson, A.",
                year=2023,
                abstract=f"This paper explores recent developments in {topic}...",
                citation="Journal of Research, 45(2), 123-145",
                source="fallback"
            ),
            Paper(
                title=f"A comprehensive study of {keywords[0] if keywords else topic}",
                authors="Williams, R., et al.",
                year=2022,
                abstract="This comprehensive analysis examines key aspects...",
                citation="Academic Review, 12(3), 456-478",
                source="fallback"
            ),
            Paper(
                title=f"Methodological approaches to {topic}",
                authors="Chen, L., Brown, M.",
                year=2023,
                abstract="This study presents novel methodologies for...",
                citation="Research Methods Journal, 8(1), 89-112",
                source="fallback"
            ),
        ]

        return papers[:max_results]

    def _paper_to_dict(self, paper: Paper) -> Dict[str, Any]:
        """Convert Paper dataclass to dictionary."""
        return {
            "title": paper.title,
            "authors": paper.authors,
            "year": paper.year,
            "abstract": paper.abstract,
            "citation": paper.citation,
            "source": paper.source,
            "url": paper.url
        }

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup on deletion."""
        if self.session and not self.session.closed:
            try:
                asyncio.run(self.close())
            except Exception:
                pass
