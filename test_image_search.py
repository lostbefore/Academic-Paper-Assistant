"""
Test script for domain-specific image search.
Tests searching images across different academic domains.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from skills.image_search import ImageSearchSkill


async def test_domain_specific_search():
    """Test image search for specific academic domains."""
    print("\n" + "=" * 70)
    print("DOMAIN-SPECIFIC IMAGE SEARCH TEST")
    print("=" * 70)

    skill = ImageSearchSkill(output_dir="output/test_images")

    # Show which search sources are configured
    print("\n[Configured Search Sources]")
    print(f"   [OK] Serper API:     {'Yes' if skill.serper_api_key else 'No'}")
    print(f"   [OK] Bing API:       {'Yes' if skill.bing_api_key else 'No'}")
    print(f"   [OK] Unsplash API:   {'Yes' if skill.unsplash_access_key else 'No'}")
    print(f"   [OK] DuckDuckGo:     {'Yes' if skill.enable_duckduckgo else 'No'}")

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
        print(f"\n{'─' * 70}")
        print(f"[Domain: {domain}]")
        print('─' * 70)

        domain_results = []
        for keyword in keywords:
            print(f"\n   Searching: '{keyword}'")
            try:
                results = await skill.search_images(keyword, num_results=3)
                print(f"   [OK] Found {len(results)} images")

                for i, img in enumerate(results[:2], 1):
                    title = img.get('title', 'No title')[:45]
                    url = img.get('url', 'No URL')[:55]
                    source = img.get('source', 'Unknown')[:35]
                    width = img.get('width', 0)
                    height = img.get('height', 0)
                    print(f"      {i}. [IMG] {title}...")
                    print(f"         Source: {source}...")
                    print(f"         URL: {url}...")
                    print(f"         Dimensions: {width}x{height}px")

                domain_results.extend(results)
            except Exception as e:
                print(f"   [ERROR] {e}")

        all_results[domain] = domain_results
        print(f"\n   [Domain Summary] {len(domain_results)} total images found")

    # Final Summary
    print("\n" + "=" * 70)
    print("SEARCH SUMMARY")
    print("=" * 70)
    total_images = 0
    for domain, results in all_results.items():
        count = len(results)
        total_images += count
        print(f"   {domain}: {count} images")
    print(f"\n   TOTAL: {total_images} images across all domains")

    await skill.close()
    print("\n[OK] Domain-specific image search test completed")
    return all_results


async def test_single_keyword_search():
    """Test searching for a specific keyword provided by user."""
    print("\n" + "=" * 70)
    print("SINGLE KEYWORD SEARCH TEST")
    print("=" * 70)

    skill = ImageSearchSkill(output_dir="output/test_images")

    # You can change this keyword to test different searches
    test_keywords = [
        "machine learning workflow diagram",
        "neural network layers visualization",
        "academic research methodology flowchart"
    ]

    for keyword in test_keywords:
        print(f"\n[Searching for: '{keyword}']")
        try:
            results = await skill.search_images(keyword, num_results=5)
            print(f"[OK] Found {len(results)} images:\n")

            for i, img in enumerate(results, 1):
                title = img.get('title', 'No title')
                url = img.get('url', 'No URL')
                source = img.get('source', 'Unknown')
                width = img.get('width', 0)
                height = img.get('height', 0)

                print(f"   ----------------------------------------")
                print(f"   Image {i}:")
                print(f"   Title: {title}")
                print(f"   Source: {source}")
                print(f"   URL: {url}")
                print(f"   Dimensions: {width}x{height}px")
                print()
        except Exception as e:
            print(f"[ERROR] {e}")

    await skill.close()
    print("[OK] Single keyword search test completed")


async def main():
    """Run image search tests."""
    print("\n" + "=" * 70)
    print("IMAGE SEARCH TEST SUITE")
    print("=" * 70)

    try:
        # Run domain-specific search
        await test_domain_specific_search()

        # Run single keyword search
        await test_single_keyword_search()

        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
