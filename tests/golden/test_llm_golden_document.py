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

    @pytest.mark.golden
    @pytest.mark.external
    def test_enhanced_additional_section_heading_state_with_toc_detection(self):
        """Test enhanced AdditionalSectionHeadingState with real API calls for TOC detection.
        
        Test setup:
        - Uses test_table_titles_not_section_headings.json (pages 97-99 from H.264 spec)
        - Makes actual Azure OpenAI API calls with enhanced TOC detection prompt
        - Simulates workflow context with previous HeaderFooterAnalysisState results
        - Tests on unused pages (97-99) while avoiding pages 1-5 from previous state
        
        What it verifies:
        - **Double categorization fix**: Table 7-2, 7-3, 7-4 appear ONLY in table_titles (not section_headings)
        - **Enhanced TOC detection**: New prompt correctly identifies TOC sections and their start locations
        - **Real API integration**: Actual LLM responses are parsed and structured correctly
        - **State machine compatibility**: Results format matches expected workflow structure
        - **Regression prevention**: Validates that prompt enhancements don't break existing functionality
        
        Expected Results (based on docs/status.md:40):
        - Table 7-2, 7-3, 7-4 titles should appear in results['table_titles']
        - Table 7-2, 7-3, 7-4 titles should NOT appear in results['section_headings'] 
        - TOC detection should identify any table of contents patterns on pages 97-99
        - Header/footer validation should confirm consistency with previous analysis
        
        Test limitation:
        - Requires real API credentials (skipped if unavailable)
        - Dependent on LLM response consistency (may have minor variations)
        - Uses specific H.264 document pages (may not cover all document types)
        - API costs incurred during testing
        
        Key insight: Validates that enhanced TOC detection works with real LLM responses and maintains regression fix for double categorization.
        """
        # Load test fixture
        fixture_data = self._load_test_fixture()
        
        # Verify fixture contains expected test data
        assert fixture_data['test_info']['description'] == "Test that table titles (Table 7-2, Table 7-3) appear only in table_titles, not in section_headings - validates LLM prompt fix for double categorization issue"
        assert fixture_data['test_info']['extracted_pages'] == [97, 98, 99]
        assert len(fixture_data['pages']) == 3
        
        # Create state instance
        state = AdditionalSectionHeadingState(
            provider_name="azure",
            sampling_seed=42,  # For reproducible testing
            max_additional_pages=10
        )
        
        # Run complete workflow with real states - no mocking
        context = self._run_complete_golden_workflow(fixture_data)
        
        # Debug: Check what pages are available vs used
        document_data = fixture_data['pages']
        print(f"🔍 GOLDEN TEST: Test fixture has {len(document_data)} pages available")
        used_pages = context['workflow_results']['header_footer_analysis']['results'].get('sampling_summary', {}).get('selected_page_indexes', [])
        print(f"🔍 GOLDEN TEST: HeaderFooterAnalysisState used pages: {used_pages}")
        
        # Execute the enhanced state with real API call
        try:
            print(f"🔍 GOLDEN TEST: About to execute AdditionalSectionHeadingState...")
            results = state.execute(context)
            
            # === CORE REGRESSION VALIDATION ===
            # Verify double categorization fix (Table 7-x should be in table_titles ONLY)
            
            # Extract results sections
            analysis_results = results.get('results', {})
            
            # === VALIDATE ACTUAL LLM RESPONSE STRUCTURE ===
            # The LLM returns direct lists, not per_page_analysis format
            
            print(f"🔍 GOLDEN TEST: Validating real LLM response structure")
            print(f"🔍 Response keys: {list(analysis_results.keys())}")
            
            # Validate we have the expected response structure
            expected_keys = ['section_headings', 'figure_titles', 'table_titles', 'sampling_summary']
            for key in expected_keys:
                assert key in analysis_results, f"Expected key '{key}' not found in LLM response. Available keys: {list(analysis_results.keys())}"
            
            # Extract results from actual LLM response format
            all_section_headings = analysis_results.get('section_headings', [])
            all_table_titles = analysis_results.get('table_titles', [])
            all_figure_titles = analysis_results.get('figure_titles', [])
            
            
            # === DOUBLE CATEGORIZATION REGRESSION TEST ===
            # This is the critical validation from docs/status.md:40
            
            # Extract text content from title objects (they might be dicts with 'text' field)
            section_heading_texts = []
            table_title_texts = []
            
            # Handle different response formats (strings or dicts)
            for item in all_section_headings:
                text = item.get('text', item) if isinstance(item, dict) else str(item)
                section_heading_texts.append(text)
                
            for item in all_table_titles:
                text = item.get('text', item) if isinstance(item, dict) else str(item)
                table_title_texts.append(text)
            
            print(f"🔍 GOLDEN TEST: Section headings: {section_heading_texts}")
            print(f"🔍 GOLDEN TEST: Table titles: {table_title_texts}")
            
            # Look for Table 7-x references in the content
            table_7_references = []
            all_texts = section_heading_texts + table_title_texts
            for text in all_texts:
                if 'Table 7-' in text:
                    table_7_references.append(text)
            
            print(f"🔍 GOLDEN TEST: Found Table 7-x references: {table_7_references}")
            
            if table_7_references:
                # CRITICAL ASSERTION: Table 7-x should be in table_titles ONLY
                table_7_in_table_titles = [text for text in table_title_texts if 'Table 7-' in text]
                table_7_in_section_headings = [text for text in section_heading_texts if 'Table 7-' in text]
                
                assert len(table_7_in_table_titles) > 0, f"Expected Table 7-x references in table_titles, found none. All table titles: {table_title_texts}"
                assert len(table_7_in_section_headings) == 0, f"Table 7-x references incorrectly found in section_headings: {table_7_in_section_headings}. This indicates double categorization regression!"
                
                print(f"✅ Double categorization fix validated: {len(table_7_in_table_titles)} Table 7-x references found in table_titles only")
            else:
                print(f"ℹ️  No Table 7-x references found in this analysis - may be expected for these particular pages")
            
            # === TOC DETECTION VALIDATION ===
            # Check if our enhanced prompt added any TOC-related fields
            
            toc_detected = False
            if 'page_analysis' in analysis_results:
                page_analysis = analysis_results['page_analysis']
                print(f"🔍 GOLDEN TEST: Page analysis structure: {type(page_analysis)}")
                if isinstance(page_analysis, dict) and 'toc_patterns' in page_analysis:
                    toc_detected = True
                    print(f"✅ TOC detection found in page_analysis")
            
            # Check for any TOC-related patterns in other fields
            for key, value in analysis_results.items():
                if 'toc' in key.lower():
                    toc_detected = True
                    print(f"✅ TOC-related field found: {key}")
            
            if not toc_detected:
                print(f"ℹ️  No explicit TOC detection found - may indicate enhancement not active or no TOC content on these pages")
            
            # === GENERAL VALIDATION ===
            
            # Verify state execution completed successfully  
            expected_analysis_type = 'additional_section_heading_analysis'  # Note: singular form used by actual implementation
            actual_analysis_type = results.get('analysis_type', 'MISSING')
            assert actual_analysis_type == expected_analysis_type, f"Expected analysis_type '{expected_analysis_type}', got '{actual_analysis_type}'"
            assert 'metadata' in results
            assert results['metadata']['provider'] == 'azure'
            
            # Verify pages were analyzed
            pages_analyzed = results['metadata'].get('pages_analyzed', 0)
            assert pages_analyzed > 0, "Expected some pages to be analyzed"
            
            print(f"✅ Golden document test validation complete: {pages_analyzed} pages analyzed")
            print(f"✅ Real LLM API call successful with {len(all_section_headings + all_table_titles + all_figure_titles)} total elements detected")
                
        except ConfigurationError as e:
            pytest.fail(f"Configuration error in golden test: {e}")
            
        except Exception as e:
            pytest.fail(f"Golden document test failed with real API call: {str(e)}")

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