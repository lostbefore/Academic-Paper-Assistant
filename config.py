"""
Unified configuration module for Academic Paper Assistant.
All settings are loaded from environment variables (typically from .env file).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Application configuration."""

    # Anthropic API Configuration
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    ANTHROPIC_API_BASE = os.getenv('ANTHROPIC_API_BASE', '')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6-20251001')

    # Semantic Scholar API
    SEMANTIC_SCHOLAR_API_KEY = os.getenv('SEMANTIC_SCHOLAR_API_KEY', '')

    # Default Settings
    DEFAULT_CITATION_STYLE = os.getenv('DEFAULT_CITATION_STYLE', 'apa')
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './output'))

    # Image Generation Settings
    ENABLE_IMAGES = os.getenv('ENABLE_IMAGES', 'true').lower() == 'true'
    MAX_IMAGES_PER_PAPER = int(os.getenv('MAX_IMAGES_PER_PAPER', '3'))
    IMAGE_SOURCES = [s.strip() for s in os.getenv('IMAGE_SOURCES', 'ai_generate,pdf_extract,web_search').split(',')]

    # Image Quality Settings
    MIN_IMAGE_WIDTH = int(os.getenv('MIN_IMAGE_WIDTH', '400'))
    MIN_IMAGE_HEIGHT = int(os.getenv('MIN_IMAGE_HEIGHT', '300'))
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', '5'))

    # Web Search Settings
    ENABLE_DUCKDUCKGO_SEARCH = os.getenv('ENABLE_DUCKDUCKGO_SEARCH', 'true').lower() == 'true'
    SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
    BING_IMAGE_API_KEY = os.getenv('BING_IMAGE_API_KEY', '')

    # PDF Extraction Settings
    ENABLE_PDF_IMAGE_EXTRACTION = os.getenv('ENABLE_PDF_IMAGE_EXTRACTION', 'true').lower() == 'true'
    PDF_MIN_IMAGE_DPI = int(os.getenv('PDF_MIN_IMAGE_DPI', '150'))

    # AI Chart Generation Settings
    ENABLE_AI_CHARTS = os.getenv('ENABLE_AI_CHARTS', 'true').lower() == 'true'
    MERMAID_GENERATION_METHOD = os.getenv('MERMAID_GENERATION_METHOD', 'online')
    PREFERRED_CHART_TYPES = [s.strip() for s in os.getenv('PREFERRED_CHART_TYPES', 'flowchart,architecture,bar_chart').split(',')]

    # Unsplash API
    UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY', '')
    UNSPLASH_SECRET_KEY = os.getenv('UNSPLASH_SECRET_KEY', '')

    @classmethod
    def validate(cls) -> dict:
        """Validate configuration and return status."""
        issues = []
        warnings = []

        # Critical: API Key
        if not cls.ANTHROPIC_API_KEY:
            issues.append("ANTHROPIC_API_KEY is required for paper generation")

        # Image-related validations
        if cls.ENABLE_IMAGES:
            if 'web_search' in cls.IMAGE_SOURCES and not cls.ENABLE_DUCKDUCKGO_SEARCH:
                if not cls.SERPER_API_KEY and not cls.BING_IMAGE_API_KEY:
                    warnings.append("Web search enabled but no search API configured (DuckDuckGo disabled, no Serper/Bing API keys)")

            if cls.MERMAID_GENERATION_METHOD == 'cli':
                import shutil
                if not shutil.which('mmdc'):
                    warnings.append("MERMAID_GENERATION_METHOD is 'cli' but mermaid-cli (mmdc) not found in PATH")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

    @classmethod
    def to_dict(cls) -> dict:
        """Export configuration as dictionary (excluding sensitive values)."""
        return {
            'anthropic_api_configured': bool(cls.ANTHROPIC_API_KEY),
            'anthropic_api_base': cls.ANTHROPIC_API_BASE or 'default',
            'anthropic_model': cls.ANTHROPIC_MODEL,
            'default_citation_style': cls.DEFAULT_CITATION_STYLE,
            'output_dir': str(cls.OUTPUT_DIR),
            'enable_images': cls.ENABLE_IMAGES,
            'max_images_per_paper': cls.MAX_IMAGES_PER_PAPER,
            'image_sources': cls.IMAGE_SOURCES,
            'min_image_dimensions': f"{cls.MIN_IMAGE_WIDTH}x{cls.MIN_IMAGE_HEIGHT}",
            'enable_pdf_extraction': cls.ENABLE_PDF_IMAGE_EXTRACTION,
            'enable_ai_charts': cls.ENABLE_AI_CHARTS,
            'mermaid_method': cls.MERMAID_GENERATION_METHOD,
            'preferred_chart_types': cls.PREFERRED_CHART_TYPES,
            'web_search_configured': cls.ENABLE_DUCKDUCKGO_SEARCH or bool(cls.SERPER_API_KEY) or bool(cls.BING_IMAGE_API_KEY),
        }


# Create output directory if it doesn't exist
Config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
