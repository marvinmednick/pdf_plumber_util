#!/usr/bin/env python3
"""Flexible script to run TOC analysis and generate review files for manual verification."""

import subprocess
import sys
import json
import argparse
from pathlib import Path


def create_test_fixture(pages, output_name):
    """Create test fixture from H.264 data with specified pages.

    Args:
        pages: List of page numbers to include (e.g., [6] or [6, 7])
        output_name: Name for the output file (e.g., "single_page_6" or "pages_6_7")

    Returns:
        Path to created fixture file
    """
    h264_blocks_path = Path("output/h264_100pages_blocks.json")

    with open(h264_blocks_path, 'r') as f:
        full_data = json.load(f)

    all_pages = full_data.get('pages', [])

    # Find requested pages
    selected_pages = []
    for page_num in pages:
        page_data = next((p for p in all_pages if p.get('page') == page_num), None)
        if not page_data:
            raise ValueError(f"Page {page_num} not found in H.264 data")
        selected_pages.append(page_data)

    # Create fixture
    fixture = {"pages": selected_pages}

    # Save to temp location
    fixture_path = Path(f"output/temp_{output_name}.json")
    with open(fixture_path, 'w') as f:
        json.dump(fixture, f, indent=2)

    return fixture_path


def run_analysis(fixture_path, test_name, expected_toc_count=None):
    """Run LLM analysis and return results summary."""

    # Run the LLM analysis
    cmd = [
        "uv", "run", "pdf-plumb", "llm-analyze",
        str(fixture_path),
        "--focus", "headers-footers",
        "--sampling-seed", "42",
        "--output-dir", "output/"
    ]

    print(f"🔧 Running: {' '.join(cmd)}")
    print("⏱️  This will take 1-2 minutes...")
    print()

    result = subprocess.run(cmd, check=False, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Analysis failed:")
        print(result.stderr)
        return None

    print("✅ Analysis completed successfully!")
    print()

    # Find the generated review files
    output_dir = Path("output")

    # Find most recent files
    review_files = list(output_dir.glob("llm_optimized_format_*.txt"))
    results_files = list(output_dir.glob("llm_headers_footers_*_results.json"))

    analysis_summary = {
        'test_name': test_name,
        'toc_found': 0,
        'expected': expected_toc_count,
        'review_file': None,
        'results_file': None
    }

    if review_files:
        latest_review = max(review_files, key=lambda p: p.stat().st_mtime)
        analysis_summary['review_file'] = latest_review
        print(f"📋 Manual Review File: {latest_review}")

    if results_files:
        latest_results = max(results_files, key=lambda p: p.stat().st_mtime)
        analysis_summary['results_file'] = latest_results

        # Count TOC entries in results
        with open(latest_results, 'r') as f:
            data = json.load(f)
            results_str = json.dumps(data)
            toc_count = results_str.count('"toc_entry_title"')

        analysis_summary['toc_found'] = toc_count
        print(f"🎯 LLM Found: {toc_count} TOC entries")

        if expected_toc_count:
            accuracy = (toc_count / expected_toc_count) * 100
            print(f"📊 Accuracy: {accuracy:.1f}% ({toc_count}/{expected_toc_count})")

        print(f"📊 Results File: {latest_results}")

    return analysis_summary


def main():
    """Run TOC analysis with flexible test scenarios."""
    parser = argparse.ArgumentParser(description="Run TOC extraction analysis and generate review files")
    parser.add_argument('--test', choices=['single', 'two-page', 'comparison'], default='single',
                        help='Test scenario to run')
    parser.add_argument('--pages', nargs='+', type=int, default=[6],
                        help='Page numbers to analyze (default: [6])')
    parser.add_argument('--expected', type=int,
                        help='Expected TOC count for accuracy calculation')

    args = parser.parse_args()

    # Test scenarios with known expectations
    scenarios = {
        'single': {'pages': [6], 'expected': 55, 'name': 'Single-Page (Page 6)'},
        'two-page': {'pages': [6, 7], 'expected': 117, 'name': 'Two-Page (Pages 6-7)'},
        'comparison': {'run_both': True}
    }

    # Check if H.264 data exists
    h264_data = Path("output/h264_100pages_blocks.json")
    if not h264_data.exists():
        print(f"❌ H.264 blocks data not found: {h264_data}")
        print("💡 Generate with: uv run pdf-plumb process h264_spec.pdf --output-dir output")
        return 1

    if args.test == 'comparison':
        # Run both single and two-page tests for comparison
        print("🔍 TOC Accuracy Review - Performance Comparison")
        print("="*60)

        results = []

        # Single-page test
        print("\n1️⃣  SINGLE-PAGE TEST")
        print("-" * 30)
        single_fixture = create_test_fixture([6], "single_page_6")
        single_result = run_analysis(single_fixture, "Single-Page", 55)
        if single_result:
            results.append(single_result)

        # Two-page test
        print("\n2️⃣  TWO-PAGE TEST")
        print("-" * 30)
        two_fixture = create_test_fixture([6, 7], "pages_6_7")
        two_result = run_analysis(two_fixture, "Two-Page", 117)
        if two_result:
            results.append(two_result)

        # Comparison summary
        if len(results) == 2:
            print("\n📊 PERFORMANCE COMPARISON")
            print("="*40)
            for result in results:
                accuracy = (result['toc_found'] / result['expected']) * 100 if result['expected'] else 0
                print(f"{result['test_name']}: {result['toc_found']}/{result['expected']} ({accuracy:.1f}%)")

            if results[0]['expected'] and results[1]['expected']:
                single_accuracy = (results[0]['toc_found'] / results[0]['expected']) * 100
                two_page_accuracy = (results[1]['toc_found'] / results[1]['expected']) * 100
                efficiency = (two_page_accuracy / single_accuracy) * 100 if single_accuracy > 0 else 0

                print(f"\n🎯 Multi-page efficiency: {efficiency:.1f}% of single-page performance")
                print(f"📈 Historical baseline: 29.7% efficiency (30.2% vs 101.9%)")

                if efficiency >= 70:
                    print("✅ IMPROVEMENT: Multi-page efficiency meets target (≥70%)!")
                else:
                    print("❌ Below target: Multi-page efficiency needs improvement")

    else:
        # Single test scenario
        if args.test in scenarios:
            scenario = scenarios[args.test]
            pages = scenario['pages']
            expected = scenario['expected']
            test_name = scenario['name']
        else:
            # Custom scenario
            pages = args.pages
            expected = args.expected
            test_name = f"Custom-Pages-{'-'.join(map(str, pages))}"

        print(f"🔍 TOC Accuracy Review - {test_name}")
        print("="*60)

        # Create fixture and run analysis
        fixture_name = f"pages_{'_'.join(map(str, pages))}"
        fixture_path = create_test_fixture(pages, fixture_name)
        print(f"📄 Using fixture: {fixture_path}")

        result = run_analysis(fixture_path, test_name, expected)

        if result:
            print("\n🔬 Manual Verification Steps:")
            print("1. Open the review file (.txt) to see LLM input data")
            print("2. Count TOC entries marked with [TOC]")
            print("3. Compare with LLM results count")
            print("4. Look for any missed or incorrect entries")

    return 0


if __name__ == "__main__":
    sys.exit(main())