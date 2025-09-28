#!/usr/bin/env python3
"""
Simple CLI wrapper for prompt testing utility.

This script provides a convenient interface to run prompt prototype tests
using existing test data from the performance testing framework.
"""

import asyncio
import argparse
from pathlib import Path
import shutil
import json

from prompt_tester import PromptTester


def create_test_data_from_performance_fixtures():
    """Create test data files from existing performance test fixtures."""
    # Path to existing test fixtures
    fixture_dir = Path(__file__).parent.parent.parent / "tests" / "performance" / "fixtures"
    test_data_dir = Path(__file__).parent / "test_data"

    # Ensure test data directory exists
    test_data_dir.mkdir(exist_ok=True)

    # Copy existing fixtures to test data directory
    if fixture_dir.exists():
        for fixture_file in fixture_dir.glob("*.json"):
            dest_file = test_data_dir / fixture_file.name
            if not dest_file.exists():
                shutil.copy2(fixture_file, dest_file)
                print(f"Copied {fixture_file.name} to test data directory")

    # Create single-page test data if multi-page exists
    multi_page_file = test_data_dir / "h264_pages_6_7.json"
    single_page_file = test_data_dir / "h264_page_6_only.json"

    if multi_page_file.exists() and not single_page_file.exists():
        with open(multi_page_file, 'r') as f:
            multi_page_data = json.load(f)

        # Extract only the first page
        if 'pages' in multi_page_data and len(multi_page_data['pages']) > 0:
            single_page_data = {
                'pages': [multi_page_data['pages'][0]]
            }

            with open(single_page_file, 'w') as f:
                json.dump(single_page_data, f, indent=2)
            print(f"Created single-page test data: {single_page_file.name}")


def run_quick_test():
    """Run a quick test with default settings."""
    # Set up paths
    script_dir = Path(__file__).parent
    template_dir = script_dir / "templates"
    test_data_dir = script_dir / "test_data"
    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    # Create test data if needed
    create_test_data_from_performance_fixtures()

    # Check if we have the necessary files
    if not template_dir.exists() or not list(template_dir.glob("*.txt")):
        print("❌ No template files found. Please ensure templates exist in templates/ directory.")
        return

    if not test_data_dir.exists() or not list(test_data_dir.glob("*.json")):
        print("❌ No test data files found. Please ensure test data exists in test_data/ directory.")
        return

    # Initialize tester
    tester = PromptTester()

    # Run test matrix
    print("🚀 Running prompt prototype test matrix...")
    print(f"📁 Templates: {template_dir}")
    print(f"📊 Test data: {test_data_dir}")

    try:
        summary = tester.run_test_matrix(template_dir, test_data_dir)

        # Print results
        tester.print_summary(summary)

        # Save results
        results_file = results_dir / "prompt_test_results.json"
        tester.save_results(summary, results_file)
        print(f"\n💾 Results saved to: {results_file}")

        # Quick analysis
        print(f"\n📈 QUICK ANALYSIS")
        print(f"{'='*60}")

        successful_results = [r for r in summary.results if r.success]
        if successful_results:
            # Find fastest and most efficient
            fastest = min(successful_results, key=lambda x: x.execution_time)
            smallest_request = min(successful_results, key=lambda x: x.request_size)

            print(f"⚡ Fastest: {fastest.template_name} ({fastest.execution_time:.2f}s)")
            print(f"📦 Smallest request: {smallest_request.template_name} ({smallest_request.request_size:,} bytes)")

            # Check for timeout indicators (long execution times)
            slow_results = [r for r in successful_results if r.execution_time > 60]
            if slow_results:
                print(f"⚠️  Slow results (>60s): {len(slow_results)} tests may be approaching timeout")

    except Exception as e:
        print(f"❌ Error running tests: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run prompt prototype tests")
    parser.add_argument("--quick", action="store_true", help="Run quick test with default settings")
    parser.add_argument("--templates", type=Path, help="Custom template directory")
    parser.add_argument("--data", type=Path, help="Custom test data directory")
    parser.add_argument("--output", type=Path, help="Output results file")

    args = parser.parse_args()

    if args.quick or (not args.templates and not args.data):
        run_quick_test()
    else:
        # Custom test run
        if not args.templates or not args.data:
            print("❌ Both --templates and --data are required for custom runs")
            return

        tester = PromptTester()
        summary = tester.run_test_matrix(args.templates, args.data)
        tester.print_summary(summary)

        if args.output:
            tester.save_results(summary, args.output)
            print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()