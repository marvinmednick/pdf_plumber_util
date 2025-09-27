"""Performance tests for TOC extraction comparing single-page vs multi-page accuracy.

These tests measure the LLM's ability to extract TOC entries in different scenarios:
- Single-page analysis (should work well)
- Multi-page analysis (historically showed degradation)

The tests use real H.264 spec data and actual LLM API calls to measure performance.
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from pdf_plumb.core.exceptions import ConfigurationError


@dataclass
class TOCPerformanceResult:
    """Results from a TOC extraction performance test."""
    test_name: str
    pages_analyzed: int
    toc_entries_found: int
    expected_entries: int
    accuracy_percent: float
    execution_time_seconds: float

    def __str__(self):
        return f"{self.test_name}: {self.toc_entries_found}/{self.expected_entries} ({self.accuracy_percent:.1f}%) in {self.execution_time_seconds:.1f}s"


class TOCPerformanceTestSuite:
    """Test suite for measuring TOC extraction performance across different scenarios."""

    def __init__(self):
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        self.performance_dir = Path(__file__).parent
        self.results: List[TOCPerformanceResult] = []

    def setup_method(self):
        """Set up test environment."""
        # Check if LLM credentials are available
        try:
            from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState
            state = HeaderFooterAnalysisState()
            # This will raise ConfigurationError if credentials missing
        except ConfigurationError:
            pytest.skip("LLM credentials not configured - skipping performance tests")

    def create_test_fixture(self, pages: List[int], fixture_name: str) -> Path:
        """Create test fixture from H.264 data with specified pages.

        Args:
            pages: List of page numbers to include
            fixture_name: Name for the fixture file

        Returns:
            Path to created fixture file
        """
        h264_blocks_path = Path("output/h264_100pages_blocks.json")

        if not h264_blocks_path.exists():
            pytest.skip(f"H.264 blocks data not found: {h264_blocks_path}")

        with open(h264_blocks_path, 'r') as f:
            full_data = json.load(f)

        all_pages = full_data.get('pages', [])

        # Find requested pages
        selected_pages = []
        for page_num in pages:
            page_data = next((p for p in all_pages if p.get('page') == page_num), None)
            if not page_data:
                pytest.skip(f"Page {page_num} not found in H.264 data")
            selected_pages.append(page_data)

        # Create fixture
        fixture = {"pages": selected_pages}

        # Save fixture
        fixture_path = self.performance_dir / "fixtures" / f"{fixture_name}.json"
        fixture_path.parent.mkdir(exist_ok=True)

        with open(fixture_path, 'w') as f:
            json.dump(fixture, f, indent=2)

        return fixture_path

    def count_expected_toc_entries(self, document_path: Path) -> int:
        """Count expected TOC entries from the document data."""
        with open(document_path, 'r') as f:
            data = json.load(f)

        total_entries = 0
        for page_data in data.get('pages', []):
            for block in page_data.get('blocks', []):
                # Handle current PDF extraction format with lines array
                lines = block.get('lines', [])
                if lines:
                    for line_data in lines:
                        # Get text from line data structure
                        line_text = line_data.get('text', '').strip()
                        # Count TOC-like entries (lines with dots leading to page numbers)
                        if '...' in line_text and line_text.split()[-1].isdigit():
                            total_entries += 1
                else:
                    # Handle older format with text_lines array (if still exists)
                    text_lines = block.get('text_lines', [])
                    if text_lines:
                        for line in text_lines:
                            line = line.strip()
                            if '...' in line and line.split()[-1].isdigit():
                                total_entries += 1
                    else:
                        # Handle oldest format with concatenated text
                        text = block.get('text', '')
                        if text:
                            for line in text.split('\n'):
                                line = line.strip()
                                if '...' in line and line.split()[-1].isdigit():
                                    total_entries += 1

        return total_entries

    def run_llm_analysis(self, document_path: Path, test_name: str, expected_toc_count: int = None) -> TOCPerformanceResult:
        """Run LLM analysis using state machine orchestrator and measure performance."""
        import time

        start_time = time.time()

        # Load document data (same format as CLI)
        with open(document_path, 'r') as f:
            document_data = json.load(f)
        pages = document_data.get('pages', [])

        # Import orchestrator components (same as CLI)
        from pdf_plumb.workflow.orchestrator import AnalysisOrchestrator
        from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState
        from pdf_plumb.workflow.registry import STATE_REGISTRY

        # Create seeded state (same as CLI when sampling_seed provided)
        sampling_seed = 42  # For reproducible results

        class SeededHeaderFooterAnalysisState(HeaderFooterAnalysisState):
            def __init__(self):
                super().__init__(
                    provider_name='azure',
                    sampling_seed=sampling_seed
                )

        # Temporarily register seeded state (same as CLI)
        original_state = STATE_REGISTRY['header_footer_analysis']
        STATE_REGISTRY['header_footer_analysis'] = SeededHeaderFooterAnalysisState

        try:
            # Create orchestrator and run workflow (same as CLI)
            orchestrator = AnalysisOrchestrator(validate_on_init=True)

            # Enable saving so we can read the results from files
            output_dir = Path("output")
            workflow_results = orchestrator.run_workflow(
                document_data=document_data,
                initial_state='header_footer_analysis',
                save_context=True,
                output_dir=output_dir
            )

        finally:
            # Restore original state registration (same as CLI)
            STATE_REGISTRY['header_footer_analysis'] = original_state

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"✅ Orchestrator analysis completed in {execution_time:.1f}s")

        # Read results from saved JSON file (same as standalone script)
        output_dir = Path("output")
        results_files = list(output_dir.glob("llm_headers_footers_*_results.json"))

        toc_entries_found = 0

        if results_files:
            # Get the most recent results file
            latest_results = max(results_files, key=lambda p: p.stat().st_mtime)
            print(f"📊 Reading results from: {latest_results}")

            # Count TOC entries in results file (same as standalone script)
            with open(latest_results, 'r') as f:
                data = json.load(f)
                results_str = json.dumps(data)
                toc_entries_found = results_str.count('"toc_entry_title"')

            print(f"🔍 Found {toc_entries_found} TOC entries in saved results file")
        else:
            print(f"🔍 No results files found in {output_dir}")

        # Count expected entries
        if expected_toc_count is not None:
            expected_entries = expected_toc_count
        else:
            expected_entries = self.count_expected_toc_entries(document_path)

        # Calculate accuracy
        accuracy = (toc_entries_found / expected_entries * 100) if expected_entries > 0 else 0

        return TOCPerformanceResult(
            test_name=test_name,
            pages_analyzed=len(pages),
            toc_entries_found=toc_entries_found,
            expected_entries=expected_entries,
            accuracy_percent=accuracy,
            execution_time_seconds=execution_time
        )

    def run_toc_test(self, pages: List[int], expected_toc_count: int, test_name: str, min_accuracy: float = 50.0):
        """Run TOC extraction test with specified parameters.

        Args:
            pages: List of page numbers to analyze
            expected_toc_count: Expected number of TOC entries
            test_name: Name for the test
            min_accuracy: Minimum acceptable accuracy percentage

        Returns:
            TOCPerformanceResult with test results
        """
        # Create fixture
        fixture_name = f"test_pages_{'_'.join(map(str, pages))}"
        fixture_path = self.create_test_fixture(pages, fixture_name)

        # Run analysis
        result = self.run_llm_analysis(fixture_path, test_name, expected_toc_count)
        self.results.append(result)

        print(f"\n📊 {result}")

        # Basic assertions
        assert result.toc_entries_found > 0, f"{test_name} should find at least some TOC entries"
        assert result.accuracy_percent >= min_accuracy, f"{test_name} accuracy too low: {result.accuracy_percent:.1f}% (expected ≥{min_accuracy}%)"

        return result

    def test_single_page_toc_extraction(self):
        """Test TOC extraction performance on single page (baseline test)."""
        self.run_toc_test(
            pages=[6],
            expected_toc_count=55,
            test_name="Single-Page (Page 6)",
            min_accuracy=80.0  # Should be high for single page
        )

    def test_multi_page_toc_extraction(self):
        """Test TOC extraction performance on multiple pages (regression test)."""
        self.run_toc_test(
            pages=[6, 7],
            expected_toc_count=117,
            test_name="Multi-Page (Pages 6-7)",
            min_accuracy=60.0  # Lower threshold, but should be much better than historical 30.2%
        )

    def test_performance_comparison(self):
        """Compare single-page vs multi-page performance."""
        # Run both tests to get comparative results
        self.test_single_page_toc_extraction()
        self.test_multi_page_toc_extraction()

        single_result = next(r for r in self.results if "Single-Page" in r.test_name)
        multi_result = next(r for r in self.results if "Multi-Page" in r.test_name)

        print(f"\n🔍 PERFORMANCE COMPARISON:")
        print(f"{'='*50}")
        print(f"📄 Single-page: {single_result}")
        print(f"📄 Multi-page:  {multi_result}")

        # Calculate performance ratio
        if single_result.accuracy_percent > 0:
            ratio = multi_result.accuracy_percent / single_result.accuracy_percent
            print(f"📊 Multi-page efficiency: {ratio:.1%} of single-page performance")

            # With the array format fix, multi-page should be much closer to single-page
            # We expect at least 70% of single-page performance (vs previous 30%)
            expected_ratio = 0.70
            print(f"🎯 Target: ≥{expected_ratio:.0%} efficiency")

            if ratio >= expected_ratio:
                print(f"✅ IMPROVEMENT: Multi-page efficiency meets target!")
            else:
                print(f"❌ REGRESSION: Multi-page efficiency below target ({ratio:.1%} < {expected_ratio:.0%})")

        # Historical comparison
        print(f"\n📈 Historical Baseline:")
        print(f"   Previous single-page: 101.9% (55/54 entries)")
        print(f"   Previous multi-page:  30.2% (35/116 entries)")
        print(f"   Previous efficiency:  29.7%")

    def teardown_method(self):
        """Clean up after tests."""
        # Print summary
        if self.results:
            print(f"\n🏁 Test Summary:")
            for result in self.results:
                print(f"   {result}")


@pytest.mark.performance
class TestTOCExtractionPerformance:
    """Performance tests for TOC extraction - requires LLM API credentials."""

    def setup_method(self):
        """Set up test environment."""
        self.suite = TOCPerformanceTestSuite()
        self.suite.setup_method()

    def test_single_page_toc_extraction(self):
        """Test TOC extraction performance on single page (baseline test)."""
        self.suite.test_single_page_toc_extraction()

    def test_multi_page_toc_extraction(self):
        """Test TOC extraction performance on multiple pages (regression test)."""
        self.suite.test_multi_page_toc_extraction()

    def test_performance_comparison(self):
        """Compare single-page vs multi-page performance."""
        self.suite.test_performance_comparison()


if __name__ == "__main__":
    # Allow running as standalone script for development
    suite = TOCPerformanceTestSuite()
    suite.setup_method()
    suite.test_performance_comparison()