"""
Test script for the complete image generation system.
Tests all three image sources: AI generate, PDF extract, web search.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config


def test_config():
    """Test configuration loading."""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    print(f"\n[CONFIG] Configuration Values:")
    config_dict = Config.to_dict()
    for key, value in config_dict.items():
        print(f"   {key}: {value}")

    # Validate
    status = Config.validate()
    print(f"\n[OK] Configuration valid: {status['valid']}")
    if status['warnings']:
        print("[WARN]  Warnings:")
        for w in status['warnings']:
            print(f"   - {w}")

    return status['valid']


def test_ai_chart_generation():
    """Test AI chart generation."""
    print("\n" + "=" * 60)
    print("Testing AI Chart Generation")
    print("=" * 60)

    if not Config.ENABLE_AI_CHARTS:
        print("[FAIL] AI charts disabled in config")
        return []

    from skills.chart_generator import ChartGeneratorSkill

    skill = ChartGeneratorSkill(
        api_key=Config.ANTHROPIC_API_KEY,
        api_base=Config.ANTHROPIC_API_BASE or None,
        model=Config.ANTHROPIC_MODEL or None
    )

    if not skill.client:
        print("[FAIL] No API client available")
        return []

    # Test suggest charts
    print("\n[TEST] Testing chart suggestion...")
    suggestions = skill.suggest_charts(
        section_name="methodology",
        section_content="Deep learning approach for natural language processing using transformer architecture",
        paper_title="Transformer Models in NLP",
        max_charts=2
    )

    print(f"   Suggested {len(suggestions)} charts:")
    for s in suggestions:
        print(f"   - {s.get('type')}: {s.get('title')}")

    figures = []
    for i, suggestion in enumerate(suggestions, 1):
        chart_type = suggestion.get('type', 'flowchart')

        if chart_type in ['flowchart', 'architecture']:
            print(f"\n[DRAW] Generating {chart_type} diagram...")
            mermaid_code = skill.generate_mermaid_code(
                chart_type=chart_type,
                title=suggestion['title'],
                description=suggestion['description'],
                section_context="Test content",
                complexity='simple'
            )

            if mermaid_code:
                print(f"   [OK] Generated Mermaid code ({len(mermaid_code)} chars)")
                figures.append({
                    'number': i,
                    'type': chart_type,
                    'title': suggestion['title'],
                    'content': mermaid_code,
                    'content_type': 'mermaid'
                })
            else:
                print(f"   [FAIL] Failed to generate Mermaid code")

    return figures


def test_pdf_extraction():
    """Test PDF image extraction."""
    print("\n" + "=" * 60)
    print("Testing PDF Image Extraction")
    print("=" * 60)

    if not Config.ENABLE_PDF_IMAGE_EXTRACTION:
        print("[FAIL] PDF extraction disabled in config")
        return []

    from skills.pdf_image_extractor import PDFImageExtractor

    extractor = PDFImageExtractor()

    # Test with a known arXiv paper
    test_url = "https://arxiv.org/pdf/1706.03762.pdf"  # Attention Is All You Need

    print(f"\n[PDF] Downloading and extracting from arXiv paper...")
    print(f"   URL: {test_url}")

    try:
        images = extractor.extract_images_from_url(
            url=test_url,
            paper_id="test_extraction",
            max_images=2
        )

        print(f"\n   [OK] Extracted {len(images)} images:")
        for img in images:
            print(f"   - {img['filename']}: {img['width']}x{img['height']}")

        return images

    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return []


def test_web_search():
    """Test web image search."""
    print("\n" + "=" * 60)
    print("Testing Web Image Search")
    print("=" * 60)

    import asyncio

    from skills.image_search import ImageSearchSkill

    skill = ImageSearchSkill(output_dir="output/images/test_search")

    async def do_search():
        print("\n[SEARCH] Searching for 'machine learning workflow diagram'...")

        results = await skill.search_images(
            query="machine learning workflow diagram",
            num_results=3
        )

        print(f"   Found {len(results)} images")

        downloaded = []
        for i, result in enumerate(results, 1):
            print(f"\n   [{i}] {result.get('title', 'No title')[:50]}")
            print(f"       Source: {result.get('source', 'Unknown')[:40]}")

            # Try to download
            filepath = await skill.download_image(
                result['url'],
                "test_search",
                i
            )

            if filepath:
                print(f"       [OK] Downloaded: {filepath.name}")
                downloaded.append(filepath)
            else:
                print(f"       [FAIL] Download failed")

        await skill.close()
        return downloaded

    return asyncio.run(do_search())


def test_docx_generation(figures):
    """Test DOCX generation with images."""
    print("\n" + "=" * 60)
    print("Testing DOCX Generation with Images")
    print("=" * 60)

    from backend.docx_generator import DocxGenerator

    sections = {
        'title': 'Test Paper with Images',
        'abstract': 'This is a test paper to verify image integration.',
        'introduction': 'Introduction text here.\n\n' + '[FIGURE:1:architecture:Test Diagram]\n\nMore introduction.',
        'methodology': 'Methodology description.',
        'results': 'Results section.',
        'discussion': 'Discussion section.',
        'conclusion': 'Conclusion.',
        'references': 'References here.',
        'figures': figures
    }

    metadata = {
        'title': 'Test Paper',
        'keywords': ['test', 'images'],
        'field': 'Computer Science',
        'citation_style': 'apa',
        'language': 'english'
    }

    generator = DocxGenerator()

    try:
        output_path = generator.generate_paper(
            sections=sections,
            metadata=metadata,
            output_path=Path("output/test_images.docx"),
            figures=figures,
            paper_id="test_images"
        )

        print(f"\n[OK] DOCX generated: {output_path}")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error generating DOCX: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n[TEST] Academic Paper Assistant - Image System Test")
    print("=" * 60)

    # Test 1: Configuration
    if not test_config():
        print("\n[FAIL] Configuration test failed. Please check your .env file.")
        return

    all_figures = []

    # Test 2: AI Chart Generation
    if Config.ENABLE_AI_CHARTS:
        ai_figures = test_ai_chart_generation()
        all_figures.extend(ai_figures)
    else:
        print("\n[SKIP]  Skipping AI chart generation (disabled in config)")

    # Test 3: PDF Extraction
    if Config.ENABLE_PDF_IMAGE_EXTRACTION and False:  # Disabled by default (slow)
        pdf_images = test_pdf_extraction()
        for i, img in enumerate(pdf_images, len(all_figures) + 1):
            all_figures.append({
                'number': i,
                'type': 'extracted',
                'title': f'Extracted Image {i}',
                'content': str(img['filepath']),
                'content_type': 'file_path',
                'section': 'results'
            })
    else:
        print("\n[SKIP]  Skipping PDF extraction (disabled or slow)")

    # Test 4: Web Search
    if 'web_search' in Config.IMAGE_SOURCES and False:  # Disabled by default (rate limits)
        web_images = test_web_search()
        for i, filepath in enumerate(web_images, len(all_figures) + 1):
            all_figures.append({
                'number': i,
                'type': 'web_image',
                'title': f'Web Image {i}',
                'content': str(filepath),
                'content_type': 'file_path',
                'section': 'introduction'
            })
    else:
        print("\n[SKIP]  Skipping web search (disabled or rate limits)")

    # Test 5: DOCX Generation
    if all_figures:
        print(f"\n[DATA] Total figures to include: {len(all_figures)}")
        test_docx_generation(all_figures)
    else:
        print("\n[WARN]  No figures to test DOCX generation")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
