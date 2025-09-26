"""Golden document tests for LLM analysis using real API calls.

These tests use actual Azure OpenAI API calls with prepared test fixtures
to validate LLM analysis capabilities and prompt effectiveness. Tests are
skipped when API credentials are not available.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from pdf_plumb.workflow.states.additional_section_headings import AdditionalSectionHeadingState
from pdf_plumb.core.exceptions import ConfigurationError


class TestLLMGoldenDocument:
    """Golden document tests using real LLM API calls with test fixtures.
    
    These tests validate the enhanced AdditionalSectionHeadingState with
    TOC detection capabilities using prepared test fixtures and real
    Azure OpenAI API responses.
    """
    
    def setup_method(self):
        """Set up test environment for golden document testing."""
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        self.test_fixture_path = self.fixtures_dir / "test_table_titles_not_section_headings.json"

        # Initialize collect_or_assert infrastructure
        self.generate_expected = False  # Set to True to generate expected data, False to test
        self.expected_data = {}
        self.collected_data = {}

        # Verify API credentials are available (fails if missing)
        self._check_api_credentials()
        
    def _check_api_credentials(self) -> None:
        """Check if Azure OpenAI credentials are available for testing.
        
        Raises:
            pytest.fail: If required credentials are missing (golden tests must have real API access)
        """
        # Load .env file if it exists
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT', 
            'AZURE_OPENAI_DEPLOYMENT'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            pytest.fail(
                f"Golden test FAILED: Missing required Azure OpenAI credentials: {missing_vars}. "
                f"Golden tests require real API access and cannot be skipped. "
                f"Set environment variables in .env file or skip golden tests with: pytest -m 'not golden'"
            )
    
    def _load_test_fixture(self) -> Dict[str, Any]:
        """Load the golden test fixture data."""
        if not self.test_fixture_path.exists():
            pytest.skip(f"Test fixture not found: {self.test_fixture_path}")
            
        with open(self.test_fixture_path, 'r') as f:
            return json.load(f)
    
    def _run_complete_golden_workflow(self, fixture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run complete workflow with real states - no mocking.
        
        This executes HeaderFooterAnalysisState first, then uses its real results
        to drive AdditionalSectionHeadingState - a true end-to-end golden test.
        """
        from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState
        
        # Step 1: Run HeaderFooterAnalysisState with real LLM API call
        print(f"🔍 GOLDEN TEST: Running HeaderFooterAnalysisState first...")
        header_footer_state = HeaderFooterAnalysisState(
            provider_name="azure",
            sampling_seed=42
        )
        
        initial_context = {
            'document_data': fixture_data['pages'],
            'workflow_results': {},
            'save_results': False,
            'output_dir': None
        }
        
        # Execute first state
        header_footer_results = header_footer_state.execute(initial_context)
        print(f"🔍 GOLDEN TEST: HeaderFooterAnalysisState completed, found {len(header_footer_results.get('results', {}).get('section_headings', []))} section headings")
        
        # Step 2: Create real workflow context with actual results
        workflow_context = {
            'document_data': fixture_data['pages'],
            'workflow_results': {
                'header_footer_analysis': header_footer_results
            },
            'save_results': False,
            'output_dir': None
        }
        
        return workflow_context


    def collect_or_assert(self, name: str, actual_value, expected_value=None, message: str = ""):
        """Either collect expected data (generate mode) or assert against it (test mode)."""
        if self.generate_expected:
            self.collected_data[name] = actual_value
            print(f"📝 Collected {name}: {actual_value}")
        else:
            if expected_value is None:
                expected_value = self.expected_data.get(name)
            assert actual_value == expected_value, f"{message or name}: expected {expected_value}, got {actual_value}"
            print(f"✅ Verified {name}: {actual_value}")

    def _save_expected_data(self, fixture_name: str):
        """Save collected data to expected results file."""
        expected_file = Path(__file__).parent / f"expected_{fixture_name.replace('.json', '')}.json"
        with open(expected_file, 'w') as f:
            json.dump(self.collected_data, f, indent=2)
        print(f"📁 Saved expected data to {expected_file}")

    def _load_expected_data(self, fixture_name: str):
        """Load expected data from file."""
        expected_file = Path(__file__).parent / f"expected_{fixture_name.replace('.json', '')}.json"
        if expected_file.exists():
            with open(expected_file, 'r') as f:
                self.expected_data = json.load(f)
            print(f"📁 Loaded expected data from {expected_file}")
        else:
            self.expected_data = {}
            print(f"📁 No expected data file found: {expected_file}")

    @pytest.mark.golden
    @pytest.mark.external
    def test_enhanced_additional_section_heading_state_with_toc_detection(self):
        """Test enhanced AdditionalSectionHeadingState with collect_or_assert pattern.

        This test can run in two modes:
        1. Generate mode (self.generate_expected = True): Collects expected results and saves to file
        2. Test mode (self.generate_expected = False): Validates against saved expected results

        What it verifies:
        - **Double categorization fix**: No overlap between section_headings and table_titles
        - **Workflow integration**: Both states process expected number of pages
        - **Content validation**: First/last items in each category match expectations
        """
        # Initialize for collect_or_assert pattern
        fixture_data = self._load_test_fixture()
        fixture_name = self.test_fixture_path.name
        self._load_expected_data(fixture_name)

        # Basic fixture validation
        total_fixture_pages = len(fixture_data['pages'])
        self.collect_or_assert("total_fixture_pages", total_fixture_pages)

        # Run complete workflow with real states - no mocking
        context = self._run_complete_golden_workflow(fixture_data)

        # Get pages used by HeaderFooterAnalysisState
        sampling_summary = context['workflow_results']['header_footer_analysis']['results'].get('sampling_summary', {})
        used_pages_analyzed = sampling_summary.get('page_indexes_analyzed', [])
        header_footer_pages_processed = len(used_pages_analyzed)
        self.collect_or_assert("header_footer_pages_processed", header_footer_pages_processed)

        # Execute AdditionalSectionHeadingState
        state = AdditionalSectionHeadingState(provider_name="azure", sampling_seed=42, max_additional_pages=10)
        results = state.execute(context)

        # Get pages processed by AdditionalSectionHeadingState
        additional_pages_processed = results['metadata'].get('pages_analyzed', 0)
        self.collect_or_assert("additional_pages_processed", additional_pages_processed)

        # Extract content from results
        analysis_results = results.get('results', {})
        all_section_headings = analysis_results.get('section_headings', [])
        all_table_titles = analysis_results.get('table_titles', [])
        all_figure_titles = analysis_results.get('figure_titles', [])

        def extract_text(item):
            """Extract text from item (handle both strings and dicts)"""
            return item.get('text', item) if isinstance(item, dict) else str(item)

        section_texts = [extract_text(item) for item in all_section_headings]
        table_texts = [extract_text(item) for item in all_table_titles]
        figure_texts = [extract_text(item) for item in all_figure_titles]

        # Collect/assert content counts
        self.collect_or_assert("total_sections_found", len(section_texts))
        self.collect_or_assert("total_tables_found", len(table_texts))
        self.collect_or_assert("total_figures_found", len(figure_texts))

        # Collect/assert first and last items for sanity checking
        if section_texts:
            self.collect_or_assert("first_section", section_texts[0])
            self.collect_or_assert("last_section", section_texts[-1])

        if table_texts:
            self.collect_or_assert("first_table", table_texts[0])
            self.collect_or_assert("last_table", table_texts[-1])

        if figure_texts:
            self.collect_or_assert("first_figure", figure_texts[0])
            self.collect_or_assert("last_figure", figure_texts[-1])

        # === UNIVERSAL DOUBLE CATEGORIZATION TEST (always run) ===
        section_table_overlap = set(section_texts) & set(table_texts)
        section_figure_overlap = set(section_texts) & set(figure_texts)
        table_figure_overlap = set(table_texts) & set(figure_texts)

        assert len(section_table_overlap) == 0, f"Double categorization: sections/tables overlap: {section_table_overlap}"
        assert len(section_figure_overlap) == 0, f"Double categorization: sections/figures overlap: {section_figure_overlap}"
        assert len(table_figure_overlap) == 0, f"Double categorization: tables/figures overlap: {table_figure_overlap}"

        print(f"✅ No double categorization: {len(section_texts)} sections, {len(table_texts)} tables, {len(figure_texts)} figures")
        print(f"✅ Workflow processed {header_footer_pages_processed + additional_pages_processed} total pages")

        # Save collected data if in generate mode
        if self.generate_expected:
            self._save_expected_data(fixture_name)
            print("📝 Generated expected data - set generate_expected=False to run actual test")

    def test_golden_test_fixture_integrity(self):
        """Test that the golden test fixture has expected structure and content.
        
        Test setup:
        - Loads test_table_titles_not_section_headings.json fixture
        - Validates fixture structure matches expected format
        - Checks for presence of known Table 7-x references
        
        What it verifies:
        - Fixture file exists and is readable
        - Contains expected pages 97-99 from H.264 specification
        - Has proper test_info metadata with description
        - Contains actual document blocks with Table 7-x references
        - Document structure suitable for LLM analysis
        
        Test limitation:
        - Only validates fixture structure, not LLM analysis results
        - Doesn't verify fixture content correctness against original document
        - May not catch subtle content corruption issues
        
        Key insight: Ensures test fixture integrity before running expensive API-based golden tests.
        """
        fixture_data = self._load_test_fixture()
        
        # Validate fixture metadata
        assert 'test_info' in fixture_data
        assert 'pages' in fixture_data
        
        test_info = fixture_data['test_info']
        assert test_info['extracted_pages'] == [97, 98, 99]
        assert test_info['total_pages'] == 3
        assert 'Table 7-2, Table 7-3' in test_info['description']
        
        # Validate document pages structure
        pages = fixture_data['pages']
        assert len(pages) == 3
        
        # Check for Table 7-x references in the actual content
        table_7_references_found = False
        total_blocks = 0
        
        for page in pages:
            assert 'blocks' in page
            assert 'page' in page or 'page_number' in page
            
            for block in page['blocks']:
                total_blocks += 1
                assert 'lines' in block
                
                for line in block['lines']:
                    assert 'text' in line
                    if 'Table 7-' in line['text']:
                        table_7_references_found = True
        
        # Verify we have actual content
        assert total_blocks > 0, "Fixture should contain actual document blocks"
        assert table_7_references_found, "Fixture should contain Table 7-x references for testing"
        
        print(f"✅ Fixture integrity validated: {len(pages)} pages, {total_blocks} blocks, Table 7-x references present")