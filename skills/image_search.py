"""
ImageSearchSkill - Search and download academic images.

Supports:
- Web image search via DuckDuckGo, Serper, Bing
- Wikipedia image extraction
- Image validation and processing
"""

import asyncio
import hashlib
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, unquote

import aiohttp
from PIL import Image

try:
    from config import Config
except ImportError:
    class Config:
        MIN_IMAGE_WIDTH = 400
        MIN_IMAGE_HEIGHT = 300
        MAX_IMAGE_SIZE_MB = 5
        ENABLE_DUCKDUCKGO_SEARCH = True
        SERPER_API_KEY = ""
        BING_IMAGE_API_KEY = ""
        UNSPLASH_ACCESS_KEY = ""


class ImageSearchSkill:
    """Skill for searching and downloading academic images."""

    def __init__(self, output_dir: str = "output/images"):
        """Initialize the image search skill."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None

        # Load config values
        self.min_width = getattr(Config, 'MIN_IMAGE_WIDTH', 400)
        self.min_height = getattr(Config, 'MIN_IMAGE_HEIGHT', 300)
        self.max_file_size = getattr(Config, 'MAX_IMAGE_SIZE_MB', 5) * 1024 * 1024

        # API keys
        self.serper_api_key = getattr(Config, 'SERPER_API_KEY', '')
        self.bing_api_key = getattr(Config, 'BING_IMAGE_API_KEY', '')
        self.unsplash_access_key = getattr(Config, 'UNSPLASH_ACCESS_KEY', '')
        self.enable_duckduckgo = getattr(Config, 'ENABLE_DUCKDUCKGO_SEARCH', True)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session

    async def search_images(
        self,
        query: str,
        num_results: int = 5,
        image_type: str = "photo"
    ) -> List[Dict[str, str]]:
        """
        Search for images using available search providers.
        Tries multiple sources in priority order.

        Args:
            query: Search query
            num_results: Number of results to return
            image_type: Type of image (photo, clipart, gif, transparent)

        Returns:
            List of image info dicts with url, title, source
        """
        results = []

        # Try Serper API first if available (more reliable)
        if self.serper_api_key:
            results = await self._search_serper(query, num_results)
            if results:
                return results

        # Try Bing API if available
        if self.bing_api_key:
            results = await self._search_bing(query, num_results)
            if results:
                return results

        # Try Unsplash API if available (free, high quality images)
        if self.unsplash_access_key:
            results = await self._search_unsplash(query, num_results)
            if results:
                return results

        # Fall back to DuckDuckGo
        if self.enable_duckduckgo:
            results = await self._search_duckduckgo(query, num_results, image_type)

        return results

    async def _search_serper(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search images using Serper API (Google)."""
        try:
            import requests

            url = "https://google.serper.dev/images"
            headers = {'X-API-KEY': self.serper_api_key}
            payload = {'q': query, 'num': num_results}

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            data = response.json()

            results = []
            for image in data.get('images', []):
                results.append({
                    "url": image.get('imageUrl'),
                    "title": image.get('title', ''),
                    "source": image.get('source', ''),
                    "width": image.get('imageWidth', 0),
                    "height": image.get('imageHeight', 0),
                })
            return results
        except Exception as e:
            print(f"Serper search failed: {e}")
            return []

    async def _search_bing(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search images using Bing API."""
        try:
            import requests

            url = "https://api.bing.microsoft.com/v7.0/images/search"
            headers = {'Ocp-Apim-Subscription-Key': self.bing_api_key}
            params = {'q': query, 'count': num_results}

            response = requests.get(url, headers=headers, params=params, timeout=30)
            data = response.json()

            results = []
            for image in data.get('value', []):
                results.append({
                    "url": image.get('contentUrl'),
                    "title": image.get('name', ''),
                    "source": image.get('hostPageUrl', ''),
                    "width": image.get('width', 0),
                    "height": image.get('height', 0),
                })
            return results
        except Exception as e:
            print(f"Bing search failed: {e}")
            return []

    async def _search_unsplash(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Search images using Unsplash API (free, high quality)."""
        try:
            session = await self._get_session()
            url = "https://api.unsplash.com/search/photos"
            headers = {'Authorization': f'Client-ID {self.unsplash_access_key}'}
            params = {
                'query': query,
                'per_page': min(num_results, 30),  # Unsplash max is 30
                'orientation': 'landscape'  # Better for academic papers
            }

            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Unsplash API error: {response.status} - {error_text}")
                    return []

                data = await response.json()
                results = []
                for photo in data.get('results', []):
                    results.append({
                        "url": photo.get('urls', {}).get('regular', photo.get('urls', {}).get('small')),
                        "title": photo.get('description', '') or photo.get('alt_description', 'Unsplash Image'),
                        "source": photo.get('links', {}).get('html', 'https://unsplash.com'),
                        "width": photo.get('width', 0),
                        "height": photo.get('height', 0),
                    })
                return results
        except Exception as e:
            print(f"Unsplash search failed: {e}")
            return []

    async def _search_duckduckgo(
        self,
        query: str,
        num_results: int = 5,
        image_type: str = "photo"
    ) -> List[Dict[str, str]]:
        """Search for images using DuckDuckGo."""
        try:
            from ddgs import DDGS

            results = []
            # Use proxies if configured in environment
            proxies = None
            if os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY'):
                proxies = {
                    'http': os.getenv('HTTP_PROXY'),
                    'https': os.getenv('HTTPS_PROXY')
                }

            with DDGS(proxies=proxies, timeout=30) as ddgs:
                ddgs_images = ddgs.images(
                    query,
                    max_results=num_results,
                    type_image=image_type
                )
                for result in ddgs_images:
                    results.append({
                        "url": result.get("image"),
                        "title": result.get("title", ""),
                        "source": result.get("source", ""),
                        "width": result.get("width", 0),
                        "height": result.get("height", 0),
                    })
            return results
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            # Don't print full URL to avoid cluttering output
            if "ConnectError" in str(e):
                print("  (Network connection failed - check your internet connection or proxy settings)")
            return []

    async def download_image(
        self,
        url: str,
        paper_id: str,
        figure_num: int
    ) -> Optional[Path]:
        """
        Download and validate an image.

        Args:
            url: Image URL
            paper_id: Paper ID for organizing files
            figure_num: Figure number for naming

        Returns:
            Path to downloaded image or None if failed
        """
        try:
            session = await self._get_session()

            async with session.get(url) as response:
                if response.status != 200:
                    return None

                content = await response.read()

                # Check file size
                if len(content) > self.max_file_size:
                    print(f"Image too large: {len(content)} bytes")
                    return None

                # Validate image
                img = Image.open(io.BytesIO(content))

                # Check dimensions
                if img.width < self.min_width or img.height < self.min_height:
                    print(f"Image too small: {img.width}x{img.height}")
                    return None

                # Convert to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Create paper-specific directory
                paper_dir = self.output_dir / paper_id
                paper_dir.mkdir(exist_ok=True)

                # Save image
                ext = self._get_extension(url, img.format)
                filename = f"figure_{figure_num:02d}{ext}"
                filepath = paper_dir / filename

                img.save(filepath, quality=85, optimize=True)

                return filepath

        except Exception as e:
            print(f"Failed to download image from {url}: {e}")
            return None

    def _get_extension(self, url: str, format_name: Optional[str]) -> str:
        """Get file extension from URL or format."""
        # Try to get from URL
        parsed = urlparse(url)
        path = unquote(parsed.path)
        if '.' in path:
            ext = path.split('.')[-1].lower()
            if ext in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                return f'.{ext}'

        # Fall back to format
        format_map = {
            'JPEG': '.jpg',
            'PNG': '.png',
            'GIF': '.gif',
            'WEBP': '.webp',
        }
        return format_map.get(format_name, '.jpg')

    async def search_and_download(
        self,
        query: str,
        paper_id: str,
        figure_num: int,
        num_search: int = 5
    ) -> Optional[Path]:
        """
        Search for images and download the first valid one.

        Args:
            query: Search query
            paper_id: Paper ID
            figure_num: Figure number
            num_search: Number of search results to try

        Returns:
            Path to downloaded image or None
        """
        results = await self.search_images(query, num_results=num_search)

        for result in results:
            url = result.get("url")
            if not url:
                continue

            filepath = await self.download_image(url, paper_id, figure_num)
            if filepath:
                return filepath

        return None

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


class ChartGenerator:
    """Generate charts and diagrams using code."""

    def __init__(self, output_dir: str = "output/images"):
        """Initialize chart generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_mermaid_diagram(
        self,
        mermaid_code: str,
        paper_id: str,
        figure_num: int
    ) -> Optional[Path]:
        """
        Generate diagram from Mermaid code.

        Args:
            mermaid_code: Mermaid diagram code
            paper_id: Paper ID
            figure_num: Figure number

        Returns:
            Path to generated PNG
        """
        try:
            import subprocess

            # Create paper directory
            paper_dir = self.output_dir / paper_id
            paper_dir.mkdir(exist_ok=True, parents=True)

            output_path = paper_dir / f"figure_{figure_num:02d}.png"

            # Use mermaid-cli (mmdc) if available
            # Save mermaid code to temp file
            temp_mmd = paper_dir / f"temp_{figure_num}.mmd"
            temp_mmd.write_text(mermaid_code, encoding="utf-8")

            try:
                result = subprocess.run([
                    "mmdc",
                    "-i", str(temp_mmd),
                    "-o", str(output_path),
                    "-b", "transparent",
                    "-s", "2"
                ], check=True, capture_output=True, timeout=30)

                temp_mmd.unlink()
                if output_path.exists():
                    print(f"Generated mermaid diagram: {output_path}")
                    return output_path
                else:
                    print(f"mmdc ran but output file not found")

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                # mmdc not available, use alternative method
                print(f"mmdc not available ({e}), trying online method...")
                temp_mmd.unlink()
                online_result = self._generate_mermaid_online(mermaid_code, output_path)
                if online_result:
                    return online_result

            # If we get here, both methods failed - use matplotlib fallback
            print(f"Mermaid methods failed, using matplotlib fallback...")
            return self._generate_diagram_fallback(mermaid_code, output_path)

        except Exception as e:
            print(f"Failed to generate mermaid diagram: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _generate_mermaid_online(
        self,
        mermaid_code: str,
        output_path: Path
    ) -> Optional[Path]:
        """Generate diagram using mermaid.ink online service."""
        try:
            import base64
            import requests

            # Encode mermaid code (use url-safe base64)
            encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
            url = f"https://mermaid.ink/img/{encoded}?type=png&bgColor=white"

            print(f"Trying mermaid.ink API...")
            response = requests.get(url, timeout=30)
            print(f"mermaid.ink response: {response.status_code}")

            if response.status_code == 200:
                output_path.write_bytes(response.content)
                print(f"Downloaded from mermaid.ink: {output_path}")
                return output_path
            else:
                print(f"mermaid.ink failed: {response.status_code}")

        except Exception as e:
            print(f"Online mermaid generation failed: {e}")

        return None

    def _generate_diagram_fallback(
        self,
        mermaid_code: str,
        output_path: Path
    ) -> Optional[Path]:
        """
        Create a simple diagram using matplotlib as fallback.
        Parses basic mermaid flowchart syntax.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
            import re

            print("Using matplotlib fallback for diagram generation...")

            # Create figure
            fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 10)
            ax.axis('off')

            # Parse mermaid code to extract nodes and connections
            lines = mermaid_code.strip().split('\n')

            # Extract title if present
            title = "Diagram"
            for line in lines:
                if line.strip().startswith('title'):
                    title = line.split('title', 1)[1].strip()
                    break

            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

            # Simple parsing for flowchart nodes
            nodes = []
            connections = []

            node_pattern = r'([\w\s]+)\[(.+?)\]|([\w\s]+)\{(.+?)\}|([\w\s]+)\((.+?)\)'

            y_pos = 8
            x_positions = {}

            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith(('graph', 'flowchart', 'title')):
                    continue

                # Check for connections
                if '-->' in line:
                    parts = line.split('-->')
                    if len(parts) == 2:
                        source = parts[0].strip().split('[')[0].strip()
                        target = parts[1].strip().split('[')[0].strip()
                        connections.append((source, target))

                # Extract node labels
                matches = re.findall(r'([A-Za-z_]+)(?:\[([^\]]+)\]|\{([^}]+)\}|\(([^)]+)\))', line)
                for match in matches:
                    node_id = match[0]
                    label = match[1] or match[2] or match[3] or node_id
                    if node_id not in x_positions:
                        x_positions[node_id] = len(x_positions) % 3 * 3 + 1
                        nodes.append({'id': node_id, 'label': label, 'x': x_positions[node_id], 'y': y_pos})

                if y_pos > 2:
                    y_pos -= 1.5

            # Draw nodes
            node_positions = {}
            for i, node in enumerate(nodes[:8]):  # Limit to 8 nodes
                x = (i % 3) * 3 + 1
                y = 8 - (i // 3) * 2.5
                node_positions[node['id']] = (x, y)

                # Draw box
                box = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6,
                                     boxstyle="round,pad=0.05",
                                     facecolor='lightblue',
                                     edgecolor='navy',
                                     linewidth=2)
                ax.add_patch(box)

                # Add text
                label = node['label'][:20]  # Truncate long labels
                ax.text(x, y, label, ha='center', va='center',
                       fontsize=9, fontweight='bold', wrap=True)

            # Draw arrows between connected nodes
            for source, target in connections:
                if source in node_positions and target in node_positions:
                    x1, y1 = node_positions[source]
                    x2, y2 = node_positions[target]
                    arrow = FancyArrowPatch((x1, y1-0.3), (x2, y2+0.3),
                                          arrowstyle='->', mutation_scale=20,
                                          linewidth=2, color='navy')
                    ax.add_patch(arrow)

            # If no nodes parsed, show a placeholder message
            if not nodes:
                ax.text(5, 5, "Research Methodology Flow",
                       ha='center', va='center', fontsize=14, fontweight='bold')
                ax.text(5, 4, "(Diagram visualization)",
                       ha='center', va='center', fontsize=10, style='italic')

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()

            print(f"Generated matplotlib fallback diagram: {output_path}")
            return output_path

        except Exception as e:
            print(f"Matplotlib fallback failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def generate_matplotlib_chart(
        self,
        data: Dict,
        chart_type: str,
        title: str,
        paper_id: str,
        figure_num: int
    ) -> Optional[Path]:
        """
        Generate data visualization using matplotlib.

        Args:
            data: Chart data (x, y values)
            chart_type: Type of chart (line, bar, scatter, etc.)
            title: Chart title
            paper_id: Paper ID
            figure_num: Figure number

        Returns:
            Path to generated chart
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt

            # Create paper directory
            paper_dir = self.output_dir / paper_id
            paper_dir.mkdir(exist_ok=True)

            output_path = paper_dir / f"figure_{figure_num:02d}.png"

            fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

            if chart_type == "line":
                ax.plot(data.get("x", []), data.get("y", []), linewidth=2)
            elif chart_type == "bar":
                ax.bar(data.get("x", []), data.get("y", []))
            elif chart_type == "scatter":
                ax.scatter(data.get("x", []), data.get("y", []), alpha=0.6)
            elif chart_type == "pie":
                ax.pie(data.get("values", []), labels=data.get("labels", []))

            ax.set_title(title, fontsize=14, fontweight='bold')

            if "xlabel" in data:
                ax.set_xlabel(data["xlabel"])
            if "ylabel" in data:
                ax.set_ylabel(data["ylabel"])

            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            plt.close()

            return output_path

        except Exception as e:
            print(f"Failed to generate matplotlib chart: {e}")
            return None
