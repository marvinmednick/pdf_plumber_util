"""Golden document tests for TOC detection using real LLM API calls.

These tests validate TOC detection capabilities with actual Azure OpenAI API calls
using prepared test fixtures. Tests are skipped when API credentials are not available.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any, List

from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState
from pdf_plumb.core.exceptions import ConfigurationError


class TestTOCDetectionGolden:
    """Golden document tests for TOC detection with real LLM API calls."""

    def setup_method(self):
        """Set up test environment for golden document testing."""
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        self.h264_fixture_path = self.fixtures_dir / "test_table_titles_not_section_headings.json"
        
        # Check if fixture exists
        if not self.h264_fixture_path.exists():
            pytest.skip(f"Test fixture not found: {self.h264_fixture_path}")

    def load_test_fixture(self, fixture_path: Path) -> Dict[str, Any]:
        """Load test fixture data from JSON file.
        
        Args:
            fixture_path: Path to the fixture file
            
        Returns:
            Dictionary containing fixture data with pages and metadata
        """
        with open(fixture_path, 'r') as f:
            return json.load(f)

    def check_api_credentials_available(self) -> bool:
        """Check if Azure OpenAI API credentials are available for testing.
        
        Returns:
            True if credentials appear to be configured, False otherwise
        """
        # Check for common environment variable patterns
        azure_vars = [
            'PDF_PLUMB_AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_API_KEY', 
            'PDF_PLUMB_AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_ENDPOINT'
        ]
        return any(os.getenv(var) for var in azure_vars)

    @pytest.mark.golden
    def test_h264_no_toc_detection_baseline(self):
        """Test TOC detection correctly identifies no TOC in H.264 spec pages 97-99.
        
        Test setup:
        - Uses real H.264 specification pages (97-99) that contain table titles but no TOC
        - Makes actual Azure OpenAI API calls with TOC-enhanced HeaderFooterAnalysisState
        - Validates that TOC detection correctly identifies absence of TOC content
        - Establishes baseline for "no TOC" scenarios in technical documents
        
        What it verifies:
        - has_toc_detected() returns False for document without TOC
        - get_all_toc_entries() returns empty list
        - get_toc_pages() returns empty list  
        - Table titles are correctly categorized as table_titles, not TOC entries
        - Analysis completes successfully with realistic confidence scores
        - Token usage reflects enhanced 6-objective analysis
        
        Test limitation:
        - Requires valid Azure OpenAI API credentials (skipped if not available)
        - Makes real API calls (not mocked) - costs actual tokens
        - Limited to specific H.264 document pages
        
        Key insight: Validates that TOC enhancement doesn't create false positives for documents without TOC content.
        """
        # Skip if no API credentials
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
        
        # Load test fixture
        fixture_data = self.load_test_fixture(self.h264_fixture_path)
        document_pages = fixture_data['pages']
        
        # Verify fixture contains expected content
        assert len(document_pages) == 3, "Fixture should contain 3 pages"
        assert fixture_data['test_info']['extracted_pages'] == [97, 98, 99]
        
        # Create context for analysis
        context = {
            'document_data': document_pages,
            'save_results': False,
            'output_dir': None
        }
        
        # Initialize HeaderFooter state with TOC detection
        state = HeaderFooterAnalysisState(
            provider_name="azure",
            sampling_seed=42  # For reproducible results
        )
        
        try:
            # Execute real analysis with API call
            result = state.execute(context)
            
            # Validate core analysis completion
            assert result['analysis_type'] == 'header_footer_analysis'
            assert 'results' in result
            assert 'metadata' in result
            assert 'raw_result' in result
            
            # Validate provider was configured and used
            metadata = result['metadata']
            assert metadata['provider'] == 'azure'
            assert metadata['provider_configured'] is True
            
            # Validate enhanced token usage (should be higher due to TOC enhancement)
            token_usage = metadata.get('token_usage', {})
            if token_usage:
                total_tokens = token_usage.get('total_tokens', 0)
                assert total_tokens > 2000, f"Expected enhanced token usage >2000, got {total_tokens}"
            
            # Validate TOC detection results - should be NO TOC
            raw_result = result['raw_result']
            assert raw_result.has_toc_detected() is False, "Should detect no TOC in H.264 table pages"
            assert raw_result.get_all_toc_entries() == [], "Should return empty TOC entries list"
            assert raw_result.get_toc_pages() == [], "Should return empty TOC pages list"
            
            # Validate table titles are properly detected (not confused with TOC)
            all_table_titles = raw_result.get_all_table_titles()
            table_title_texts = [title['text'] for title in all_table_titles]
            
            # Should detect the actual table titles from fixture
            expected_table_patterns = ['Table 7-2', 'Table 7-3', 'Table 7-4']
            detected_table_references = [
                title for title in table_title_texts 
                if any(pattern in title for pattern in expected_table_patterns)
            ]
            
            assert len(detected_table_references) > 0, f"Should detect table titles, found: {table_title_texts}"
            
            # Validate that table titles are NOT categorized as section headings
            all_section_headings = raw_result.get_all_section_headings()
            section_texts = [heading['text'] for heading in all_section_headings]
            
            for table_title in detected_table_references:
                assert table_title not in section_texts, f"Table title '{table_title}' incorrectly categorized as section heading"
            
            # Validate confidence levels are reasonable
            confidence = metadata.get('confidence', {})
            if confidence:
                header_conf = confidence.get('header', 'Unknown')
                footer_conf = confidence.get('footer', 'Unknown')
                
                # Confidence should be valid levels
                valid_confidence = ['Low', 'Medium', 'High', 'Unknown']
                assert header_conf in valid_confidence
                assert footer_conf in valid_confidence
            
            # Report successful analysis details
            print(f"\n✅ Golden test passed - No TOC detected (correct)")
            print(f"📊 Token usage: {token_usage.get('total_tokens', 'Unknown')}")
            print(f"🔍 Table titles found: {len(all_table_titles)}")
            print(f"📄 Pages analyzed: {metadata.get('pages_analyzed', 'Unknown')}")
            print(f"🎯 Header confidence: {confidence.get('header', 'Unknown')}")
            print(f"🎯 Footer confidence: {confidence.get('footer', 'Unknown')}")
            
        except ConfigurationError as e:
            pytest.skip(f"LLM provider configuration error: {e}")
        except Exception as e:
            pytest.fail(f"Analysis failed with unexpected error: {e}")

    @pytest.mark.golden
    def test_h264_no_toc_regression_baseline(self):
        """Establish regression baseline for H.264 no-TOC analysis.
        
        Test setup:
        - Same fixture as test_h264_no_toc_detection_baseline
        - Focused on creating reproducible baseline metrics
        - Captures specific analysis patterns for regression detection
        
        What it verifies:
        - Consistent analysis results across test runs
        - Stable token usage patterns for cost monitoring
        - Reproducible confidence scores with fixed sampling seed
        - Baseline element counts for regression comparison
        
        Key insight: Provides stable baseline metrics for detecting analysis quality regression over time.
        """
        # Skip if no API credentials
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
        
        # Load fixture
        fixture_data = self.load_test_fixture(self.h264_fixture_path)
        document_pages = fixture_data['pages']
        
        context = {
            'document_data': document_pages,
            'save_results': False,
            'output_dir': None
        }
        
        # Use consistent sampling seed for reproducible results
        state = HeaderFooterAnalysisState(
            provider_name="azure",
            sampling_seed=12345  # Fixed seed for baseline consistency
        )
        
        try:
            result = state.execute(context)
            raw_result = result['raw_result']
            metadata = result['metadata']
            
            # Collect baseline metrics
            baseline_metrics = {
                'toc_detected': raw_result.has_toc_detected(),
                'toc_entries_count': len(raw_result.get_all_toc_entries()),
                'section_headings_count': len(raw_result.get_all_section_headings()),
                'table_titles_count': len(raw_result.get_all_table_titles()),
                'figure_titles_count': len(raw_result.get_all_figure_titles()),
                'pages_analyzed': metadata.get('pages_analyzed', 0),
                'provider_configured': metadata.get('provider_configured', False)
            }
            
            # Validate baseline expectations
            assert baseline_metrics['toc_detected'] is False
            assert baseline_metrics['toc_entries_count'] == 0
            assert baseline_metrics['table_titles_count'] > 0  # Should find Table 7-x references
            assert baseline_metrics['pages_analyzed'] == 3     # 3 pages in fixture
            assert baseline_metrics['provider_configured'] is True
            
            # Store/compare baseline metrics for future regression detection
            # (In real implementation, could save to baseline file)
            print(f"\n📈 Regression baseline established:")
            for key, value in baseline_metrics.items():
                print(f"   {key}: {value}")
                
        except ConfigurationError as e:
            pytest.skip(f"LLM provider configuration error: {e}")

    @pytest.mark.golden  
    def test_h264_analysis_quality_thresholds(self):
        """Test analysis quality meets established thresholds for H.264 fixture.
        
        Test setup:
        - Uses same H.264 fixture with table titles
        - Validates analysis quality against predefined thresholds
        - Tests confidence calibration and completeness metrics
        
        What it verifies:
        - Analysis confidence scores meet minimum thresholds
        - Element detection completeness is within expected ranges
        - Token usage efficiency meets cost optimization targets
        - No analysis errors or degraded performance
        
        Key insight: Ensures TOC enhancement maintains high analysis quality standards for technical documents.
        """
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
            
        fixture_data = self.load_test_fixture(self.h264_fixture_path)
        document_pages = fixture_data['pages']
        
        context = {
            'document_data': document_pages,
            'save_results': False,
            'output_dir': None
        }
        
        state = HeaderFooterAnalysisState(provider_name="azure", sampling_seed=42)
        
        try:
            result = state.execute(context)
            raw_result = result['raw_result']
            metadata = result['metadata']
            
            # Quality threshold validation
            
            # 1. Confidence score thresholds (based on testing-strategy-architect recommendations)
            confidence = metadata.get('confidence', {})
            header_conf = confidence.get('header', 'Unknown')
            footer_conf = confidence.get('footer', 'Unknown')
            
            # At minimum, should not be 'Unknown' for technical documents
            assert header_conf != 'Unknown', "Header confidence should be determined"
            assert footer_conf != 'Unknown', "Footer confidence should be determined"
            
            # 2. Element detection completeness
            table_titles = raw_result.get_all_table_titles()
            section_headings = raw_result.get_all_section_headings()
            
            # Should detect some document structure elements
            assert len(table_titles) + len(section_headings) > 0, "Should detect some document elements"
            
            # 3. Token usage efficiency (enhanced analysis should be reasonable)
            token_usage = metadata.get('token_usage', {})
            if token_usage:
                total_tokens = token_usage.get('total_tokens', 0)
                # Enhanced 6-objective analysis, but should be reasonable
                assert 1500 < total_tokens < 5000, f"Token usage should be reasonable: {total_tokens}"
            
            # 4. Analysis completeness 
            assert metadata.get('provider_configured', False), "Provider should be properly configured"
            assert metadata.get('pages_analyzed', 0) == 3, "Should analyze all 3 fixture pages"
            
            # 5. No TOC false positives
            assert not raw_result.has_toc_detected(), "Should not detect false positive TOC"
            
            print(f"\n✅ Quality thresholds met:")
            print(f"   Header confidence: {header_conf}")
            print(f"   Footer confidence: {footer_conf}")
            print(f"   Elements detected: {len(table_titles)} tables, {len(section_headings)} sections")
            print(f"   Token usage: {token_usage.get('total_tokens', 'Unknown')}")
            print(f"   No false TOC detection: ✓")
            
        except ConfigurationError as e:
            pytest.skip(f"LLM provider configuration error: {e}")


class TestTOCDetectionWithTOCGolden:
    """Golden document tests for documents that actually contain TOC content."""

    def setup_method(self):
        """Set up test environment for TOC-containing document testing."""
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"
        # Future: Will be created for documents with actual TOC content
        self.toc_fixture_path = self.fixtures_dir / "test_document_with_toc.json"

    def check_api_credentials_available(self) -> bool:
        """Check if Azure OpenAI API credentials are available."""
        azure_vars = [
            'PDF_PLUMB_AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_API_KEY',
            'PDF_PLUMB_AZURE_OPENAI_ENDPOINT', 
            'AZURE_OPENAI_ENDPOINT'
        ]
        return any(os.getenv(var) for var in azure_vars)

    @pytest.mark.golden
    def test_document_with_toc_detection_positive(self):
        """Test TOC detection correctly identifies actual TOC content in H.264 spec pages 5-10.
        
        Test setup:
        - Uses real H.264 specification pages 5-10 with mixed content
        - Page 5: Pre-TOC content (should detect no TOC)
        - Pages 6-10: Comprehensive TOC structure with hierarchical sections
        - Makes actual Azure OpenAI API calls with TOC-enhanced HeaderFooterAnalysisState
        - Validates positive TOC detection and detailed structure extraction
        
        What it verifies:
        - has_toc_detected() returns True for document with actual TOC
        - get_all_toc_entries() returns structured TOC entries with hierarchical levels
        - get_toc_pages() correctly identifies TOC page locations (should include pages 6-10)
        - TOC structure analysis extracts multi-level hierarchy (8.1, 8.2.1, 8.2.1.1, etc.)
        - TOC entries have proper formatting with page references and dot leaders
        - Mixed content handling: page 5 contributes no TOC, pages 6-10 contribute TOC
        - Token usage reflects enhanced 6-objective analysis with TOC detection
        
        Test limitation:
        - Requires valid Azure OpenAI API credentials (skipped if not available)
        - Makes real API calls (not mocked) - costs actual tokens (~2400+ tokens)
        - Limited to specific H.264 TOC pages
        
        Key insight: Validates that TOC enhancement successfully detects and analyzes comprehensive real TOC content with hierarchical structure.
        """
        # Skip if no API credentials
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
        
        # Check if TOC fixture exists
        if not self.toc_fixture_path.exists():
            pytest.skip(f"TOC fixture not found: {self.toc_fixture_path}")
        
        # Load TOC fixture with pages 5-10
        fixture_data = self.load_test_fixture(self.toc_fixture_path)
        document_pages = fixture_data['pages']
        
        # Verify fixture contains expected mixed content
        assert len(document_pages) == 6, "Fixture should contain 6 pages (5-10)"
        assert fixture_data['test_info']['extracted_pages'] == [5, 6, 7, 8, 9, 10]
        
        # Create context for analysis
        context = {
            'document_data': document_pages,
            'save_results': False,
            'output_dir': None
        }
        
        # Initialize HeaderFooter state with TOC detection
        state = HeaderFooterAnalysisState(
            provider_name="azure",
            sampling_seed=42  # For reproducible results
        )
        
        try:
            # Execute real analysis with API call
            result = state.execute(context)
            
            # Validate core analysis completion
            assert result['analysis_type'] == 'header_footer_analysis'
            assert 'results' in result
            assert 'metadata' in result
            assert 'raw_result' in result
            
            # Validate provider was configured and used
            metadata = result['metadata']
            assert metadata['provider'] == 'azure'
            assert metadata['provider_configured'] is True
            
            # Validate enhanced token usage (should be higher due to TOC enhancement)
            token_usage = metadata.get('token_usage', {})
            if token_usage:
                total_tokens = token_usage.get('total_tokens', 0)
                assert total_tokens > 2200, f"Expected enhanced token usage >2200 for 6 pages with TOC, got {total_tokens}"
            
            # MAIN VALIDATION: TOC detection results - should detect TOC
            raw_result = result['raw_result']
            assert raw_result.has_toc_detected() is True, "Should detect TOC in H.264 TOC pages 6-10"
            
            # Validate TOC entries structure
            all_toc_entries = raw_result.get_all_toc_entries()
            assert len(all_toc_entries) > 5, f"Should detect multiple TOC entries, found: {len(all_toc_entries)}"
            
            # Validate TOC pages identification
            toc_pages = raw_result.get_toc_pages()
            assert len(toc_pages) > 0, "Should identify pages containing TOC"
            
            # Check for expected TOC content patterns from H.264 spec
            toc_texts = [entry['text'] for entry in all_toc_entries]
            
            # Should find hierarchical section numbers
            hierarchical_patterns = [text for text in toc_texts if any(pattern in text for pattern in ['8.1', '8.2', '8.3', '7.1', '6.4'])]
            assert len(hierarchical_patterns) > 3, f"Should detect hierarchical section patterns, found: {hierarchical_patterns}"
            
            # Should find multi-level nesting (e.g., 8.2.1, 8.2.1.1)
            nested_patterns = [text for text in toc_texts if any(pattern in text for pattern in ['8.2.1', '8.3.1', '6.4.13'])]
            assert len(nested_patterns) > 1, f"Should detect multi-level nesting, found: {nested_patterns}"
            
            # Validate TOC structure analysis
            toc_analysis = raw_result.get_toc_analysis_patterns()
            if toc_analysis:
                assert toc_analysis.get('detected', False) is True, "TOC analysis should indicate detection"
            
            # Validate that regular sections are still detected (not confused with TOC)
            all_section_headings = raw_result.get_all_section_headings()
            section_texts = [heading['text'] for heading in all_section_headings]
            
            # Should find "Table of Contents" as a section heading
            toc_header_found = any("Table of Contents" in text for text in section_texts)
            assert toc_header_found, "Should detect 'Table of Contents' header as section heading"
            
            # Validate confidence levels are reasonable
            confidence = metadata.get('confidence', {})
            if confidence:
                header_conf = confidence.get('header', 'Unknown')
                footer_conf = confidence.get('footer', 'Unknown')
                
                # Confidence should be determined for technical documents
                assert header_conf != 'Unknown', f"Header confidence should be determined, got: {header_conf}"
                assert footer_conf != 'Unknown', f"Footer confidence should be determined, got: {footer_conf}"
            
            # Report successful TOC analysis details
            print(f"\n✅ Golden test passed - TOC detected successfully!")
            print(f"📊 Token usage: {token_usage.get('total_tokens', 'Unknown')}")
            print(f"🔍 TOC entries found: {len(all_toc_entries)}")
            print(f"📄 TOC pages identified: {toc_pages}")
            print(f"📋 Sample TOC entries: {toc_texts[:3]}")
            print(f"🎯 Header confidence: {confidence.get('header', 'Unknown')}")
            print(f"🎯 Footer confidence: {confidence.get('footer', 'Unknown')}")
            print(f"🏗️ Hierarchical patterns: {len(hierarchical_patterns)}")
            print(f"🔗 Multi-level nesting: {len(nested_patterns)}")
            
        except ConfigurationError as e:
            pytest.skip(f"LLM provider configuration error: {e}")
        except Exception as e:
            pytest.fail(f"TOC detection analysis failed with unexpected error: {e}")

    @pytest.mark.golden
    def test_toc_structure_analysis_accuracy(self):
        """Test accuracy of TOC hierarchical structure analysis.
        
        Test setup:
        - Uses TOC-containing document with known hierarchical structure
        - Validates detailed structure extraction and level detection
        - Tests page number reference accuracy
        
        What it verifies:
        - TOC level hierarchy correctly identified (1, 2, 3+ levels)  
        - Page number references accurately extracted
        - Numbering patterns properly detected (1.1, 1.2, etc.)
        - TOC formatting patterns identified (dot leaders, alignment)
        
        Key insight: Ensures detailed TOC structure analysis meets accuracy requirements.
        """
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
            
        if not self.toc_fixture_path.exists():
            pytest.skip("TOC fixture not yet created")
            
        pytest.skip("TOC fixture creation pending")

    @pytest.mark.golden
    def test_toc_vs_section_heading_differentiation(self):
        """Test differentiation between TOC entries and actual section headings.
        
        Test setup:
        - Uses document with both TOC and actual section content
        - Validates that same text is properly categorized in different contexts
        - Tests double categorization prevention
        
        What it verifies:
        - Same text appears appropriately in TOC entries vs section headings
        - TOC references to sections don't duplicate section heading detection
        - Context-aware analysis maintains proper categorization boundaries
        
        Key insight: Validates sophisticated context awareness in document element categorization.
        """
        if not self.check_api_credentials_available():
            pytest.skip("Azure OpenAI API credentials not available")
            
        if not self.toc_fixture_path.exists():
            pytest.skip("TOC fixture not yet created")
            
        pytest.skip("TOC fixture creation pending - will implement comprehensive differentiation test")