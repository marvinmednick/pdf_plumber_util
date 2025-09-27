#!/usr/bin/env python3
"""Manual test runner for TOC performance tests using pytest infrastructure."""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tests.performance.test_toc_extraction_performance import TOCPerformanceTestSuite


def main():
    """Run TOC tests manually with proper error handling."""

    print("🔬 Manual TOC Performance Test Runner")
    print("="*50)

    try:
        suite = TOCPerformanceTestSuite()
        suite.setup_method()

        print("✅ Test suite initialized")

        # Test 1: Single page (known to work)
        print("\n1️⃣  Testing Single Page (Page 6)")
        print("-" * 30)

        single_result = suite.run_toc_test(
            pages=[6],
            expected_toc_count=55,
            test_name="Single-Page (Page 6)",
            min_accuracy=80.0
        )

        print(f"✅ Single-page result: {single_result}")

        # Test 2: Two pages (the critical test)
        print("\n2️⃣  Testing Two Pages (Pages 6-7)")
        print("-" * 30)

        two_page_result = suite.run_toc_test(
            pages=[6, 7],
            expected_toc_count=117,
            test_name="Multi-Page (Pages 6-7)",
            min_accuracy=60.0
        )

        print(f"✅ Two-page result: {two_page_result}")

        # Comparison
        print("\n📊 PERFORMANCE COMPARISON")
        print("="*40)

        single_accuracy = single_result.accuracy_percent
        two_page_accuracy = two_page_result.accuracy_percent
        efficiency = (two_page_accuracy / single_accuracy) * 100 if single_accuracy > 0 else 0

        print(f"Single-page: {single_result.toc_entries_found}/{single_result.expected_entries} ({single_accuracy:.1f}%)")
        print(f"Two-page: {two_page_result.toc_entries_found}/{two_page_result.expected_entries} ({two_page_accuracy:.1f}%)")
        print(f"Multi-page efficiency: {efficiency:.1f}% of single-page performance")
        print(f"Historical baseline: 29.7% efficiency (30.2% vs 101.9%)")

        if efficiency >= 70:
            print("✅ IMPROVEMENT: Multi-page efficiency meets target (≥70%)!")
        else:
            print("❌ Below target: Multi-page efficiency needs improvement")

        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())