"""
Literature Search Test - Test academic paper search functionality.
Tests multiple research topics and saves results to file.

Usage:
    python test_literature_search.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from skills.literature_search import LiteratureSearchSkill


# Define multiple research topics to test
TEST_TOPICS = [
    {
        "name": "Artificial Intelligence",
        "topic": "artificial intelligence machine learning",
        "keywords": ["deep learning", "neural networks", "AI"]
    },
    {
        "name": "Climate Change",
        "topic": "climate change global warming",
        "keywords": ["carbon emissions", "renewable energy", "sustainability"]
    },
    {
        "name": "Quantum Computing",
        "topic": "quantum computing quantum mechanics",
        "keywords": ["qubits", "quantum algorithms", "superposition"]
    },
    {
        "name": "Cancer Research",
        "topic": "cancer oncology treatment",
        "keywords": ["immunotherapy", "tumor", "biomarkers"]
    },
    {
        "name": "Blockchain Technology",
        "topic": "blockchain cryptocurrency",
        "keywords": ["distributed ledger", "smart contracts", "decentralization"]
    },
    {
        "name": "Natural Language Processing",
        "topic": "natural language processing NLP",
        "keywords": ["transformer", "BERT", "text generation"]
    }
]


async def test_single_topic(skill: LiteratureSearchSkill, topic_config: dict) -> dict:
    """Test literature search for a single topic."""
    print(f"\n{'='*60}")
    print(f"Testing: {topic_config['name']}")
    print(f"Topic: {topic_config['topic']}")
    print(f"Keywords: {', '.join(topic_config['keywords'])}")
    print('='*60)

    start_time = asyncio.get_event_loop().time()

    try:
        # Search for papers (direct async call)
        papers = await skill._search_all_sources(
            query=topic_config['topic'] + " " + " ".join(topic_config['keywords'][:3]),
            max_results=5
        )
        papers = [skill._paper_to_dict(p) for p in papers]

        elapsed = asyncio.get_event_loop().time() - start_time

        print(f"\n[OK] Found {len(papers)} papers in {elapsed:.2f}s")

        # Display results
        for i, paper in enumerate(papers[:3], 1):
            print(f"\n  {i}. {paper['title'][:60]}...")
            print(f"     Authors: {paper['authors']}")
            print(f"     Year: {paper['year']}")
            print(f"     Source: {paper['source']}")

        return {
            "topic_name": topic_config['name'],
            "query": topic_config['topic'],
            "keywords": topic_config['keywords'],
            "status": "success",
            "papers_found": len(papers),
            "elapsed_time": round(elapsed, 2),
            "papers": papers
        }

    except Exception as e:
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"\n[ERROR] {e}")
        return {
            "topic_name": topic_config['name'],
            "query": topic_config['topic'],
            "keywords": topic_config['keywords'],
            "status": "error",
            "error": str(e),
            "elapsed_time": round(elapsed, 2),
            "papers": []
        }


async def main():
    """Run literature search tests for multiple topics."""
    print("\n" + "="*70)
    print("LITERATURE SEARCH TEST SUITE")
    print("="*70)
    print(f"\nTest Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Topics: {len(TEST_TOPICS)}")
    print()

    # Initialize skill
    skill = LiteratureSearchSkill()

    # Test all topics
    results = []
    for topic_config in TEST_TOPICS:
        result = await test_single_topic(skill, topic_config)
        results.append(result)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    successful = sum(1 for r in results if r['status'] == 'success')
    total_papers = sum(r['papers_found'] for r in results)

    for result in results:
        status_icon = "[OK]" if result['status'] == 'success' else "[FAIL]"
        print(f"{status_icon} {result['topic_name']}: {result['papers_found']} papers ({result['elapsed_time']}s)")

    print(f"\nTotal: {successful}/{len(results)} topics successful")
    print(f"Total papers found: {total_papers}")

    # Save results to file
    output_data = {
        "test_info": {
            "test_time": datetime.now().isoformat(),
            "total_topics": len(TEST_TOPICS),
            "successful_topics": successful,
            "total_papers": total_papers
        },
        "results": results
    }

    # Create output directory
    output_dir = Path("output/test_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as JSON
    json_file = output_dir / f"literature_search_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON results saved: {json_file}")

    # Save as formatted text
    txt_file = output_dir / f"literature_search_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("LITERATURE SEARCH TEST RESULTS\n")
        f.write("="*70 + "\n")
        f.write(f"Test Time: {output_data['test_info']['test_time']}\n")
        f.write(f"Total Topics: {output_data['test_info']['total_topics']}\n")
        f.write(f"Successful: {output_data['test_info']['successful_topics']}\n")
        f.write(f"Total Papers: {output_data['test_info']['total_papers']}\n")
        f.write("="*70 + "\n\n")

        for result in results:
            f.write(f"\n{'='*70}\n")
            f.write(f"TOPIC: {result['topic_name']}\n")
            f.write(f"Status: {result['status']}\n")
            f.write(f"Query: {result['query']}\n")
            f.write(f"Keywords: {', '.join(result['keywords'])}\n")
            f.write(f"Papers Found: {result['papers_found']}\n")
            f.write(f"Time: {result['elapsed_time']}s\n")
            f.write('='*70 + "\n")

            if result['papers']:
                for i, paper in enumerate(result['papers'], 1):
                    f.write(f"\n[{i}] {paper['title']}\n")
                    f.write(f"    Authors: {paper['authors']}\n")
                    f.write(f"    Year: {paper['year']}\n")
                    f.write(f"    Source: {paper['source']}\n")
                    f.write(f"    Citation: {paper['citation']}\n")
                    if paper.get('url'):
                        f.write(f"    URL: {paper['url']}\n")
                    f.write(f"    Abstract: {paper['abstract'][:200]}...\n")
            else:
                f.write("\nNo papers found.\n")

    print(f"[OK] Text report saved: {txt_file}")

    # Close skill
    await skill.close()

    print("\n" + "="*70)
    print("TEST COMPLETED")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
