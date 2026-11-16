"""
Test script for image search and generation functionality.

This script tests:
1. Image search using DuckDuckGo
2. Mermaid diagram generation
3. Matplotlib chart generation
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from skills.image_search import ImageSearchSkill, ChartGenerator
from skills.chart_generator import ChartGeneratorSkill


async def test_pdf_image_extraction():
    """Test PDF image extraction from academic papers."""
    print("=" * 60)
    print("TEST 1: PDF Image Extraction (from Literature)")
    print("=" * 60)

    from skills.pdf_image_extractor import PDFImageExtractor

    extractor = PDFImageExtractor(output_dir="output/test_images")

    # Test 1: Download and extract from arXiv paper
    print("\nTest 1.1: Extract from arXiv Paper")
    test_paper = {
        "title": "Attention Is All You Need",
        "url": "https://arxiv.org/abs/1706.03762",
        "authors": "Vaswani et al.",
        "year": "2017"
    }

    print(f"Paper: {test_paper['title']}")
    try:
        images = await extractor.extract_images_from_paper(
            test_paper,
            paper_id="test_attention",
            max_images=3
        )
        print(f"[OK] Extracted {len(images)} images")
        for img in images:
            print(f"  - {img.name}")
    except Exception as e:
        print(f"[WARN] Extraction failed: {e}")
        print("  (This is normal if PyMuPDF is not installed or paper is not accessible)")

    # Test 2: Search and extract
    print("\nTest 1.2: Search and Extract from Multiple Papers")
    try:
        results = await extractor.search_and_extract_images(
            query="machine learning",
            paper_id="test_search",
            max_papers=1,
            max_images_per_paper=2
        )
        print(f"[OK] Found and extracted {len(results)} images from literature")
        for r in results:
            print(f"  - {r['path'].name} from '{r['source_title'][:40]}...'")
    except Exception as e:
        print(f"[WARN] Search extraction failed: {e}")

    await extractor.close()
    print("\n[OK] PDF image extraction test completed")


async def test_image_search():
    """Test image search functionality."""
    print("\n" + "=" * 60)
    print("TEST 2: Image Search (Multiple Sources)")
    print("=" * 60)

    skill = ImageSearchSkill(output_dir="output/test_images")

    # Show which search sources are configured
    print("\nConfigured Search Sources:")
    print(f"  - Serper API: {'✓' if skill.serper_api_key else '✗'}")
    print(f"  - Bing API: {'✓' if skill.bing_api_key else '✗'}")
    print(f"  - Unsplash API: {'✓' if skill.unsplash_access_key else '✗'}")
    print(f"  - DuckDuckGo: {'✓' if skill.enable_duckduckgo else '✗'}")

    test_queries = [
        "machine learning concept diagram",
        "neural network architecture",
        "data visualization chart"
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        try:
            results = await skill.search_images(query, num_results=3)
            print(f"  Found {len(results)} images:")
            for i, img in enumerate(results[:2], 1):
                print(f"    {i}. {img.get('title', 'No title')[:50]}...")
                print(f"       URL: {img.get('url', 'No URL')[:60]}...")
                print(f"       Size: {img.get('width')}x{img.get('height')}")
        except Exception as e:
            print(f"  Error: {e}")

    await skill.close()
    print("\n[OK] Image search test completed")


async def test_domain_specific_image_search():
    """Test image search for specific academic domains."""
    print("\n" + "=" * 60)
    print("TEST: Domain-Specific Image Search")
    print("=" * 60)

    skill = ImageSearchSkill(output_dir="output/test_images")

    # Define domains and their search keywords
    domains = {
        "Computer Science / AI": [
            "transformer architecture diagram",
            "deep learning neural network visualization",
            "attention mechanism illustration"
        ],
        "Medicine / Healthcare": [
            "human anatomy medical illustration",
            "cell structure microscope",
            "medical imaging MRI scan"
        ],
        "Physics": [
            "quantum mechanics wave function",
            "particle collision CERN",
            "electromagnetic field lines"
        ],
        "Biology": [
            "DNA double helix structure",
            "protein folding 3D model",
            "ecosystem food web diagram"
        ],
        "Economics / Business": [
            "supply demand curve graph",
            "market trend analysis chart",
            "global trade flow diagram"
        ]
    }

    all_results = {}

    for domain, keywords in domains.items():
        print(f"\n{'─' * 50}")
        print(f"Domain: {domain}")
        print('─' * 50)

        domain_results = []
        for keyword in keywords:
            print(f"\n  Searching: '{keyword}'")
            try:
                results = await skill.search_images(keyword, num_results=3)
                print(f"    Found {len(results)} images")

                for i, img in enumerate(results[:2], 1):
                    title = img.get('title', 'No title')[:40]
                    url = img.get('url', 'No URL')[:50]
                    source = img.get('source', 'Unknown')[:30]
                    width = img.get('width', 0)
                    height = img.get('height', 0)
                    print(f"      {i}. {title}...")
                    print(f"         Source: {source}...")
                    print(f"         URL: {url}...")
                    print(f"         Dimensions: {width}x{height}")

                domain_results.extend(results)
            except Exception as e:
                print(f"    Error: {e}")

        all_results[domain] = domain_results
        print(f"\n  [Domain Summary] {domain}: {len(domain_results)} total images found")

    # Summary
    print("\n" + "=" * 60)
    print("SEARCH SUMMARY")
    print("=" * 60)
    total_images = 0
    for domain, results in all_results.items():
        count = len(results)
        total_images += count
        print(f"  {domain}: {count} images")
    print(f"\n  TOTAL: {total_images} images across all domains")

    await skill.close()
    print("\n[OK] Domain-specific image search completed")


def test_mermaid_generation():
    """Test Mermaid diagram generation."""
    print("\n" + "=" * 60)
    print("TEST 2: Mermaid Diagram Generation")
    print("=" * 60)

    generator = ChartGenerator(output_dir="output/test_images")

    # Test 1: Simple flowchart
    mermaid_code_1 = """flowchart LR
    A[Start] --> B[Process Data]
    B --> C[Analyze Results]
    C --> D[Generate Report]
    D --> E[End]"""

    print("\nTest 2.1: Simple Flowchart")
    print("Mermaid code:")
    print(mermaid_code_1)
    result = generator.generate_mermaid_diagram(
        mermaid_code=mermaid_code_1,
        paper_id="test_paper",
        figure_num=1
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate diagram")

    # Test 2: Architecture diagram
    mermaid_code_2 = """graph TB
    subgraph Input
        A[Raw Data]
    end
    subgraph Processing
        B[Preprocessing]
        C[Feature Extraction]
        D[Model Training]
    end
    subgraph Output
        E[Predictions]
    end
    A --> B
    B --> C
    C --> D
    D --> E"""

    print("\nTest 2.2: Architecture Diagram")
    result = generator.generate_mermaid_diagram(
        mermaid_code=mermaid_code_2,
        paper_id="test_paper",
        figure_num=2
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate diagram")

    # Test 3: Invalid/empty code (should use fallback)
    print("\nTest 2.3: Invalid Code (Fallback Test)")
    result = generator.generate_mermaid_diagram(
        mermaid_code="invalid code here",
        paper_id="test_paper",
        figure_num=3
    )
    if result:
        print(f"[OK] Generated (fallback): {result}")
    else:
        print("[FAIL] Failed to generate diagram")

    print("\n[OK] Mermaid generation test completed")


def test_matplotlib_charts():
    """Test Matplotlib chart generation."""
    print("\n" + "=" * 60)
    print("TEST 3: Matplotlib Chart Generation")
    print("=" * 60)

    generator = ChartGenerator(output_dir="output/test_images")

    # Test 1: Bar chart
    print("\nTest 3.1: Bar Chart")
    bar_data = {
        "x": ["Method A", "Method B", "Method C", "Method D"],
        "y": [85, 92, 78, 95],
        "xlabel": "Methods",
        "ylabel": "Accuracy (%)"
    }
    result = generator.generate_matplotlib_chart(
        data=bar_data,
        chart_type="bar",
        title="Comparison of Methods",
        paper_id="test_paper",
        figure_num=4
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate chart")

    # Test 2: Line chart
    print("\nTest 3.2: Line Chart")
    line_data = {
        "x": ["2019", "2020", "2021", "2022", "2023"],
        "y": [45, 58, 72, 85, 94],
        "xlabel": "Year",
        "ylabel": "Performance Score"
    }
    result = generator.generate_matplotlib_chart(
        data=line_data,
        chart_type="line",
        title="Performance Over Time",
        paper_id="test_paper",
        figure_num=5
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate chart")

    # Test 3: Pie chart
    print("\nTest 3.3: Pie Chart")
    pie_data = {
        "values": [30, 25, 25, 20],
        "labels": ["Group A", "Group B", "Group C", "Group D"]
    }
    result = generator.generate_matplotlib_chart(
        data=pie_data,
        chart_type="pie",
        title="Distribution of Categories",
        paper_id="test_paper",
        figure_num=6
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate chart")

    # Test 4: Scatter plot
    print("\nTest 3.4: Scatter Plot")
    scatter_data = {
        "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "y": [2.3, 3.5, 4.1, 5.8, 6.2, 7.1, 8.5, 9.2, 9.8, 11.5],
        "xlabel": "Input Variable",
        "ylabel": "Output Variable"
    }
    result = generator.generate_matplotlib_chart(
        data=scatter_data,
        chart_type="scatter",
        title="Correlation Analysis",
        paper_id="test_paper",
        figure_num=7
    )
    if result:
        print(f"[OK] Generated: {result}")
    else:
        print("[FAIL] Failed to generate chart")

    print("\n[OK] Matplotlib chart test completed")


def test_chart_generator_skill():
    """Test ChartGeneratorSkill with AI suggestions."""
    print("\n" + "=" * 60)
    print("TEST 4: Chart Generator Skill (AI-powered)")
    print("=" * 60)

    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("[WARN] Skipping AI tests - no API key found")
        print("  Set ANTHROPIC_API_KEY environment variable to run these tests")
        return

    skill = ChartGeneratorSkill(api_key=api_key)

    # Test 1: Suggest charts for methodology section
    print("\nTest 4.1: Suggest Charts for Methodology")
    section_content = """
    This research uses a mixed-methods approach combining qualitative interviews
    with quantitative surveys. Data was collected from 500 participants over
    a period of 6 months. The analysis involves statistical testing and
    thematic coding of interview transcripts.
    """

    suggestions = skill.suggest_charts(
        section_name="methodology",
        section_content=section_content,
        paper_title="Mixed Methods Research in Education",
        max_charts=2
    )

    print(f"  Suggested {len(suggestions)} charts:")
    for i, s in enumerate(suggestions, 1):
        print(f"    {i}. {s.get('type')}: {s.get('title')}")
        print(f"       Description: {s.get('description', 'N/A')[:60]}...")

    # Test 2: Generate Mermaid code
    if suggestions:
        print("\nTest 4.2: Generate Mermaid Code")
        first_suggestion = suggestions[0]
        mermaid_code = skill.generate_mermaid_code(
            chart_type=first_suggestion.get('type', 'flowchart'),
            title=first_suggestion.get('title', 'Research Flow'),
            description=first_suggestion.get('description', ''),
            section_context=section_content,
            complexity='detailed'
        )

        if mermaid_code:
            print("  Generated Mermaid code:")
            print("  " + "\n  ".join(mermaid_code.split('\n')[:5]))
            print("  ...")

            # Now generate the actual diagram
            generator = ChartGenerator(output_dir="output/test_images")
            result = generator.generate_mermaid_diagram(
                mermaid_code=mermaid_code,
                paper_id="test_paper",
                figure_num=8
            )
            if result:
                print(f"  [OK] Generated diagram: {result}")
            else:
                print("  [FAIL] Failed to generate diagram")
        else:
            print("  [FAIL] Failed to generate Mermaid code")

    # Test 3: Generate chart data
    print("\nTest 4.3: Generate Chart Data")
    chart_data = skill.generate_chart_data(
        chart_type="bar_chart",
        description="Comparison of student performance across different teaching methods",
        section_context="The study compares traditional lecture vs interactive learning"
    )

    if chart_data:
        print("  Generated chart data:")
        print(f"    X: {chart_data.get('x', [])}")
        print(f"    Y: {chart_data.get('y', [])}")
        if 'xlabel' in chart_data:
            print(f"    X Label: {chart_data['xlabel']}")
        if 'ylabel' in chart_data:
            print(f"    Y Label: {chart_data['ylabel']}")

        # Generate the chart
        generator = ChartGenerator(output_dir="output/test_images")
        result = generator.generate_matplotlib_chart(
            data=chart_data,
            chart_type="bar",
            title="Student Performance Comparison",
            paper_id="test_paper",
            figure_num=9
        )
        if result:
            print(f"  [OK] Generated chart: {result}")
        else:
            print("  [FAIL] Failed to generate chart")
    else:
        print("  [FAIL] Failed to generate chart data")

    print("\n[OK] Chart generator skill test completed")


def cleanup():
    """Clean up test files."""
    print("\n" + "=" * 60)
    print("CLEANUP")
    print("=" * 60)

    test_dir = Path("output/test_images")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)
        print(f"[OK] Removed test directory: {test_dir}")
    else:
        print("No cleanup needed")


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("IMAGE SEARCH AND GENERATION TEST SUITE")
    print("=" * 60)
    print()

    try:
        # Run tests
        await test_pdf_image_extraction()
        await test_image_search()
        await test_domain_specific_image_search()  # New domain-specific search test
        test_mermaid_generation()
        test_matplotlib_charts()
        test_chart_generator_skill()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nGenerated files are in: output/test_images/")

        # Ask if user wants to cleanup
        print("\nPress Enter to clean up test files, or type 'keep' to keep them:")
        response = input("> ").strip().lower()
        if response != 'keep':
            cleanup()
        else:
            print("Test files kept in output/test_images/")

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
