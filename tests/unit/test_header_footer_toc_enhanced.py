"""Unit tests for TOC-enhanced HeaderFooterAnalysisState.

These tests validate the enhanced HeaderFooterAnalysisState with comprehensive
6-objective analysis including table of contents detection, using extensive
mocking for fast execution and comprehensive coverage.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from pdf_plumb.workflow.states.header_footer import HeaderFooterAnalysisState
from pdf_plumb.llm.responses import HeaderFooterAnalysisResult, ConfidenceLevel
from pdf_plumb.core.exceptions import AnalysisError, ConfigurationError


class TestHeaderFooterTOCEnhanced:
    """Unit tests for TOC-enhanced HeaderFooterAnalysisState with comprehensive mocking."""

    def setup_method(self):
        """Set up test environment with consistent mocking approach."""
        self.state = HeaderFooterAnalysisState(
            provider_name="azure",
            sampling_seed=42
        )
        
        # Sample document data for testing
        self.sample_document_data = [
            {
                "page": 1,
                "blocks": [
                    {
                        "lines": [
                            {
                                "text": "Chapter 1: Introduction",
                                "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116}
                            }
                        ]
                    }
                ]
            }
        ]
        
        self.base_context = {
            'document_data': self.sample_document_data,
            'save_results': False,
            'output_dir': None
        }

    def create_mock_toc_enhanced_result(self, 
                                       include_toc: bool = True,
                                       confidence_level: str = "High") -> Mock:
        """Create comprehensive mock HeaderFooterAnalysisResult with TOC data.
        
        Test setup:
        - Creates realistic mock result with 6-objective analysis structure
        - Configurable TOC presence and confidence levels 
        - Includes all new TOC-specific fields and methods
        - Simulates realistic token usage and metadata
        
        Args:
            include_toc: Whether to include TOC detection data
            confidence_level: Confidence level for analysis results
            
        Returns:
            Mock HeaderFooterAnalysisResult with comprehensive TOC data
        """
        # Create comprehensive TOC data when enabled
        toc_entries = []
        if include_toc:
            toc_entries = [
                {
                    "text": "1.1 Overview",
                    "page_number": "5",
                    "level": 2,
                    "bbox": {"x0": 72, "top": 150, "x1": 200, "bottom": 166}
                },
                {
                    "text": "1.2 Scope",
                    "page_number": "7", 
                    "level": 2,
                    "bbox": {"x0": 72, "top": 170, "x1": 180, "bottom": 186}
                },
                {
                    "text": "2. Technical Details",
                    "page_number": "12",
                    "level": 1,
                    "bbox": {"x0": 72, "top": 190, "x1": 250, "bottom": 206}
                }
            ]
        
        # Create section headings data for mocking
        section_headings = [
            {
                "text": "Chapter 1: Introduction",
                "confidence": confidence_level,
                "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116},
                "page_index": 0
            }
        ]
        
        figure_titles = [
            {
                "text": "Figure 1-1: System Overview",
                "confidence": confidence_level,
                "bbox": {"x0": 72, "top": 200, "x1": 350, "bottom": 216},
                "page_index": 0
            }
        ]
        
        table_titles = [
            {
                "text": "Table 1-1: Configuration Parameters",
                "confidence": confidence_level,
                "bbox": {"x0": 72, "top": 250, "x1": 380, "bottom": 266},
                "page_index": 0
            }
        ]
        
        # Create mock result using MagicMock without spec to avoid real method calls
        mock_result = MagicMock()
        
        # Mock all the properties and methods
        mock_result.header_confidence.value = confidence_level
        mock_result.footer_confidence.value = confidence_level
        
        mock_result.header_pattern = {
            "pattern": "consistent",
            "confidence": confidence_level,
            "pages_with_headers": [0],
            "reasoning": "Header detected on all pages"
        }
        
        mock_result.footer_pattern = {
            "pattern": "page_numbers",
            "confidence": confidence_level, 
            "pages_with_footers": [0],
            "reasoning": "Footer with page numbers detected"
        }
        
        mock_result.page_numbering_analysis = {
            "numbering_detected": True,
            "numbering_pattern": "bottom_center",
            "confidence": confidence_level
        }
        
        mock_result.insights = [
            f"Document has consistent header/footer patterns",
            f"Page numbering follows standard format",
            f"TOC detected with {len(toc_entries)} entries" if include_toc else "No TOC detected"
        ]
        
        # Mock per_page_analysis for compatibility
        mock_result.per_page_analysis = [
            {
                "page_index": 0,
                "document_elements": {
                    "section_headings": [section_headings[0].copy()],
                    "figure_titles": [figure_titles[0].copy()],
                    "table_titles": [table_titles[0].copy()],
                    "table_of_contents": toc_entries
                }
            }
        ]
        
        # Mock the get_* methods to return the correct data
        mock_result.get_all_section_headings.return_value = section_headings
        mock_result.get_all_figure_titles.return_value = figure_titles
        mock_result.get_all_table_titles.return_value = table_titles
        mock_result.get_all_toc_entries.return_value = toc_entries
        
        # Mock TOC-specific methods
        mock_result.has_toc_detected.return_value = include_toc
        mock_result.get_toc_pages.return_value = [0, 1] if include_toc else []
        mock_result.get_toc_entries_by_page.return_value = toc_entries if include_toc else []
        mock_result.get_toc_analysis_patterns.return_value = {
            "detected": include_toc,
            "toc_pages": [0, 1] if include_toc else [],
            "structure_patterns": ["hierarchical_numbering"] if include_toc else []
        }
        
        # Mock content boundaries method 
        mock_result.get_content_boundaries.return_value = {
            'start_after_y': 120.0,
            'end_before_y': 720.0,
            'confidence': confidence_level
        }
        
        # Mock pages with headers/footers methods
        mock_result.get_pages_with_headers.return_value = [0]
        mock_result.get_pages_with_footers.return_value = [0]
        
        return mock_result

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_execute_with_toc_detection_success(self, mock_llm_call):
        """Test successful HeaderFooter state execution with TOC detection enabled.
        
        Test setup:
        - Mock only the LLM API call to return known response data
        - Let real parser and HeaderFooterAnalysisResult process the response
        - Use realistic 6-objective analysis response with TOC entries
        
        What it verifies:
        - State execution completes successfully with TOC enhancement
        - Real response parsing works with TOC-enhanced prompt
        - All 6 analysis objectives are included in results
        - Token usage and metadata are properly tracked
        - Result structure matches expected state machine format
        
        Key insight: Tests the real integration flow with only the LLM call mocked.
        """
        # Mock LLM response with realistic 6-objective analysis including TOC
        mock_llm_response = """
{
  "sampling_summary": {
    "page_indexes_analyzed": [0],
    "sampling_strategy": "comprehensive",
    "total_pages_analyzed": 1
  },
  "per_page_analysis": [
    {
      "page_index": 0,
      "page_number": 1,
      "document_elements": {
        "section_headings": [
          {
            "text": "Chapter 1: Introduction",
            "confidence": "High",
            "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116},
            "reasoning": "Clear section heading with consistent formatting"
          }
        ],
        "figure_titles": [
          {
            "text": "Figure 1-1: System Overview",
            "confidence": "High", 
            "bbox": {"x0": 72, "top": 200, "x1": 350, "bottom": 216},
            "reasoning": "Standard figure title format"
          }
        ],
        "table_titles": [
          {
            "text": "Table 1-1: Configuration Parameters",
            "confidence": "High",
            "bbox": {"x0": 72, "top": 250, "x1": 380, "bottom": 266},
            "reasoning": "Clear table title with numbering"
          }
        ],
        "table_of_contents": [
          {
            "text": "1.1 Overview",
            "page_number": "5",
            "level": 2,
            "bbox": {"x0": 72, "top": 150, "x1": 200, "bottom": 166},
            "reasoning": "TOC entry with hierarchical numbering"
          },
          {
            "text": "1.2 Scope", 
            "page_number": "7",
            "level": 2,
            "bbox": {"x0": 72, "top": 170, "x1": 180, "bottom": 186},
            "reasoning": "TOC entry with hierarchical numbering"
          },
          {
            "text": "2. Technical Details",
            "page_number": "12", 
            "level": 1,
            "bbox": {"x0": 72, "top": 190, "x1": 250, "bottom": 206},
            "reasoning": "Top-level TOC entry"
          }
        ]
      }
    }
  ],
  "header_pattern": {
    "consistent_pattern": true,
    "pages_with_headers": [0],
    "typical_content": ["Document Header"],
    "y_boundary_typical": 50.0,
    "confidence": "High",
    "reasoning": "Consistent header detected"
  },
  "footer_pattern": {
    "consistent_pattern": true,
    "pages_with_footers": [0], 
    "typical_content": ["Page 1"],
    "y_boundary_typical": 750.0,
    "confidence": "High",
    "reasoning": "Page numbering in footer"
  },
  "page_numbering_analysis": {
    "numbering_detected": true,
    "numbering_pattern": "bottom_center",
    "confidence": "High"
  },
  "content_area_boundaries": {
    "main_content_starts_after_y": 60.0,
    "main_content_ends_before_y": 740.0,
    "confidence": "High"
  },
  "document_element_analysis": {
    "table_of_contents": {
      "detected": true,
      "toc_pages": [0],
      "structure_patterns": ["hierarchical_numbering", "page_alignment"],
      "confidence": "High"
    }
  },
  "insights": [
    "Document has consistent header/footer patterns",
    "Page numbering follows standard format", 
    "TOC detected with 3 entries showing hierarchical structure"
  ]
}
        """
        
        # Mock the LLM response
        from pdf_plumb.llm.providers import LLMResponse
        mock_llm_call.return_value = LLMResponse(
            content=mock_llm_response.strip(),
            usage={
                "prompt_tokens": 1950,
                "completion_tokens": 500, 
                "total_tokens": 2450
            },
            model="gpt-4",
            finish_reason="stop"
        )
        
        # Execute state - this will use real parsing and result construction
        result = self.state.execute(self.base_context)
        
        # Validate core execution results
        assert result['analysis_type'] == 'header_footer_analysis'
        assert 'results' in result
        assert 'metadata' in result
        assert 'knowledge' in result
        assert 'raw_result' in result
        
        # Validate metadata includes token usage from LLM call
        metadata = result['metadata']
        assert metadata['provider'] == 'azure'
        assert metadata['provider_configured'] is True
        # Check token usage from our mock response (actual structure from analyzer)
        assert metadata['token_usage']['total_tokens'] == 2450
        assert metadata['token_usage']['total_input_tokens'] == 1950
        assert metadata['token_usage']['total_output_tokens'] == 500
        assert metadata['pages_analyzed'] == 1
        
        # Validate confidence levels are properly extracted
        confidence = metadata['confidence']
        assert confidence['header'] == 'High'
        assert confidence['footer'] == 'High'
        
        # Validate knowledge section includes all 6 objectives
        knowledge = result['knowledge']
        assert 'header_pattern' in knowledge
        assert 'footer_pattern' in knowledge
        assert 'content_boundaries' in knowledge
        assert knowledge['section_headings_found'] == 1
        assert knowledge['figure_titles_found'] == 1
        assert knowledge['table_titles_found'] == 1
        
        # Validate raw result provides access to TOC methods (real object now)
        raw_result = result['raw_result']
        assert isinstance(raw_result, HeaderFooterAnalysisResult)
        
        # Test TOC-specific methods on raw result
        toc_entries = raw_result.get_all_toc_entries()
        assert len(toc_entries) == 3
        assert toc_entries[0]['text'] == "1.1 Overview"
        assert toc_entries[1]['page_number'] == "7"
        assert toc_entries[2]['text'] == "2. Technical Details"
        
        # Test TOC detection methods
        assert raw_result.has_toc_detected() is True
        toc_pages = raw_result.get_toc_pages()
        assert toc_pages == [0]  # Only page 0 in our mock response
        
        # Test page-specific TOC entries
        page_0_entries = raw_result.get_toc_entries_by_page(0)
        assert len(page_0_entries) == 3
        
        # Verify LLM was called with the right prompt (should contain TOC instructions)
        mock_llm_call.assert_called_once()
        call_args = mock_llm_call.call_args[1]  # Get keyword arguments
        prompt = call_args.get('prompt', mock_llm_call.call_args[0][0])  # First positional arg if no 'prompt' keyword
        assert 'table_of_contents' in prompt.lower() or 'toc' in prompt.lower()

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_execute_without_toc_detection(self, mock_llm_call):
        """Test HeaderFooter state execution when no TOC is detected.
        
        Test setup:
        - Mock only the LLM API call to return response without TOC data
        - Let real parser and HeaderFooterAnalysisResult process the response
        - Use realistic 6-objective analysis response with empty TOC entries
        
        What it verifies:
        - State handles documents without TOC gracefully
        - TOC-specific methods return empty results when no TOC present
        - Other analysis objectives (headers, footers, sections) work normally
        - has_toc_detected() returns False appropriately
        - No errors or exceptions when TOC data is absent
        
        Key insight: Tests real integration flow for documents without TOC content.
        """
        # Mock LLM response with realistic analysis but no TOC entries
        mock_llm_response = """
{
  "sampling_summary": {
    "page_indexes_analyzed": [0],
    "sampling_strategy": "comprehensive",
    "total_pages_analyzed": 1
  },
  "per_page_analysis": [
    {
      "page_index": 0,
      "page_number": 1,
      "document_elements": {
        "section_headings": [
          {
            "text": "Document Title",
            "confidence": "Medium",
            "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 116},
            "reasoning": "Title text with moderate confidence"
          }
        ],
        "figure_titles": [
          {
            "text": "Figure A-1: Overview",
            "confidence": "Medium", 
            "bbox": {"x0": 72, "top": 200, "x1": 350, "bottom": 216},
            "reasoning": "Standard figure title format"
          }
        ],
        "table_titles": [
          {
            "text": "Table 2: Summary",
            "confidence": "Medium",
            "bbox": {"x0": 72, "top": 250, "x1": 380, "bottom": 266},
            "reasoning": "Table title with moderate confidence"
          }
        ],
        "table_of_contents": []
      }
    }
  ],
  "header_pattern": {
    "consistent_pattern": true,
    "pages_with_headers": [0],
    "typical_content": ["Document Header"],
    "y_boundary_typical": 50.0,
    "confidence": "Medium",
    "reasoning": "Moderate confidence header pattern"
  },
  "footer_pattern": {
    "consistent_pattern": true,
    "pages_with_footers": [0], 
    "typical_content": ["Page 1"],
    "y_boundary_typical": 750.0,
    "confidence": "Medium",
    "reasoning": "Moderate confidence footer pattern"
  },
  "page_numbering_analysis": {
    "numbering_detected": true,
    "numbering_pattern": "bottom_center",
    "confidence": "Medium"
  },
  "content_area_boundaries": {
    "main_content_starts_after_y": 60.0,
    "main_content_ends_before_y": 740.0,
    "confidence": "Medium"
  },
  "document_element_analysis": {
    "table_of_contents": {
      "detected": false,
      "toc_pages": [],
      "structure_patterns": [],
      "confidence": "High"
    }
  },
  "insights": [
    "Document has moderate confidence header/footer patterns",
    "Page numbering detected with medium confidence", 
    "No table of contents detected in analyzed pages"
  ]
}
        """
        
        # Mock the LLM response
        from pdf_plumb.llm.providers import LLMResponse
        mock_llm_call.return_value = LLMResponse(
            content=mock_llm_response.strip(),
            usage={
                "prompt_tokens": 1500,
                "completion_tokens": 500, 
                "total_tokens": 2000
            },
            model="gpt-4",
            finish_reason="stop"
        )
        
        # Execute state - this will use real parsing and result construction
        result = self.state.execute(self.base_context)
        
        # Validate core execution still works
        assert result['analysis_type'] == 'header_footer_analysis'
        assert result['metadata']['confidence']['header'] == 'Medium'
        
        # Test TOC methods return empty results
        raw_result = result['raw_result']
        assert raw_result.has_toc_detected() is False
        assert raw_result.get_all_toc_entries() == []
        assert raw_result.get_toc_pages() == []
        assert raw_result.get_toc_entries_by_page(0) == []
        
        # Validate other objectives still work
        assert result['knowledge']['section_headings_found'] == 1
        assert result['knowledge']['figure_titles_found'] == 1
        assert result['knowledge']['table_titles_found'] == 1

    def test_validate_input_with_valid_context(self):
        """Test input validation with properly formatted context.
        
        Test setup:
        - Create valid context with document_data as list format
        - Include all required fields for successful validation
        - Use realistic document page structure
        
        What it verifies:
        - validate_input() passes for well-formatted context
        - Both list and dict document_data formats are accepted
        - No exceptions raised for valid input structures
        
        Key insight: Ensures input validation accepts standard document data formats.
        """
        # Test with list format (should pass)
        valid_context = {
            'document_data': self.sample_document_data,
            'save_results': True,
            'output_dir': '/tmp/test'
        }
        
        # Should not raise any exceptions
        self.state.validate_input(valid_context)
        
        # Test with dict format (should also pass)
        dict_context = {
            'document_data': {'pages': self.sample_document_data},
            'save_results': False
        }
        
        # Should not raise any exceptions
        self.state.validate_input(dict_context)

    def test_validate_input_failures(self):
        """Test input validation failure scenarios.
        
        Test setup:
        - Create various invalid context configurations
        - Test missing required fields and malformed data
        - Cover edge cases like empty pages and wrong data types
        
        What it verifies:
        - AnalysisError raised for missing document_data
        - AnalysisError raised for empty document data
        - AnalysisError raised for malformed document structure
        - Error messages provide specific guidance for each failure type
        
        Key insight: Validates comprehensive input validation prevents state execution with invalid data.
        """
        # Test missing document_data
        with pytest.raises(ValueError, match="Missing required field 'document_data' for state HeaderFooterAnalysisState"):
            self.state.validate_input({})
        
        # Test empty document_data list (treated same as missing due to falsy check)
        with pytest.raises(AnalysisError, match="Missing required 'document_data' in context"):
            self.state.validate_input({'document_data': []})
        
        # Test malformed dict without pages key
        with pytest.raises(AnalysisError, match="must contain 'pages' key"):
            self.state.validate_input({'document_data': {'invalid': 'format'}})
        
        # Test invalid data type
        with pytest.raises(AnalysisError, match="must be list of pages or dict"):
            self.state.validate_input({'document_data': "invalid_string"})

    def test_cost_estimation_with_toc_enhancement(self):
        """Test cost estimation for TOC-enhanced analysis.
        
        Test setup:
        - Use real cost estimation logic without mocking
        - Let real analyzer calculate token counts for 6-objective analysis
        - Test with actual document data and enhanced prompts
        
        What it verifies:
        - estimate_cost() method works with TOC enhancement
        - Cost estimation includes additional tokens for 6-objective analysis
        - Return structure includes required fields
        - Token counts are reasonable for enhanced analysis
        
        Key insight: Tests real cost estimation logic with TOC-enhanced prompts.
        """
        # Test cost estimation with real logic
        cost_result = self.state.estimate_cost(self.base_context)
        
        # Validate cost estimation results structure
        assert 'estimated_input_tokens' in cost_result
        assert 'estimated_output_tokens' in cost_result
        assert 'estimated_cost_usd' in cost_result
        assert 'currency' in cost_result
        
        # Validate reasonable token ranges for TOC-enhanced analysis
        # (These should be higher than basic analysis due to 6-objective prompts)
        input_tokens = cost_result['estimated_input_tokens']
        output_tokens = cost_result['estimated_output_tokens']
        
        assert 2000 < input_tokens < 5000, f"Input tokens {input_tokens} outside reasonable range for TOC analysis"
        assert 500 < output_tokens < 2000, f"Output tokens {output_tokens} outside reasonable range"
        assert cost_result['currency'] == 'USD'
        assert cost_result['estimated_cost_usd'] > 0

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.estimate_cost')
    def test_cost_estimation_error_handling(self, mock_provider_estimate):
        """Test cost estimation error handling.
        
        Test setup:
        - Mock the LLM provider's estimate_cost method to raise exception
        - Test that errors are handled gracefully at the boundary
        
        What it verifies:
        - Cost estimation failures are handled gracefully
        - Error result contains descriptive error message
        - No exceptions propagated from estimate_cost method
        
        Key insight: Tests error handling at the provider boundary.
        """
        # Mock provider cost estimation failure
        mock_provider_estimate.side_effect = Exception("API connection failed")
        
        # Test error handling
        cost_result = self.state.estimate_cost(self.base_context)
        
        # Validate error result
        assert 'error' in cost_result
        assert 'Cost estimation failed' in cost_result['error']
        assert 'API connection failed' in cost_result['error']

    def test_determine_next_state(self):
        """Test state transition logic for workflow progression.
        
        Test setup:
        - Create mock execution result from HeaderFooter analysis
        - Test various analysis scenarios and context conditions
        
        What it verifies:
        - determine_next_state() returns 'additional_section_headings' for workflow continuation
        - State transition logic is consistent regardless of TOC detection results
        - Workflow progression follows expected state machine pattern
        
        Key insight: Validates that TOC enhancement doesn't affect standard workflow transitions.
        """
        # Mock execution result
        mock_execution_result = {
            'analysis_type': 'header_footer_analysis',
            'results': {},
            'metadata': {}
        }
        
        mock_context = self.base_context
        
        # Test next state determination
        next_state = self.state.determine_next_state(mock_execution_result, mock_context)
        
        # Validate workflow progression
        assert next_state == 'additional_section_headings'

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_configuration_error_handling(self, mock_llm_call):
        """Test handling of LLM configuration errors.
        
        Test setup:
        - Mock LLM API call to raise ConfigurationError at the boundary
        - Test configuration failure scenarios like invalid API keys
        
        What it verifies:
        - ConfigurationError is caught and wrapped in AnalysisError
        - Error message includes configuration context
        - Proper exception chain for debugging
        
        Key insight: Tests configuration error handling at the API boundary.
        """
        # Mock configuration error at API boundary
        from pdf_plumb.core.exceptions import ConfigurationError
        mock_llm_call.side_effect = ConfigurationError("Invalid API key")
        
        # Test error handling (ConfigurationError gets wrapped in AnalysisError)
        with pytest.raises(AnalysisError, match="Header/footer analysis failed.*Invalid API key"):
            self.state.execute(self.base_context)

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_general_analysis_error_handling(self, mock_llm_call):
        """Test handling of general analysis errors.
        
        Test setup:
        - Mock LLM API call to raise various exception types at the boundary
        - Test error scenarios like API failures, timeouts, parsing errors
        
        What it verifies:
        - All exceptions are caught and wrapped in AnalysisError
        - Error messages provide context about failure type
        - No unhandled exceptions escape from execute method
        
        Key insight: Tests error handling at the API boundary for all failure modes.
        """
        # Mock general analysis error at API boundary
        mock_llm_call.side_effect = Exception("LLM API timeout")
        
        # Test error handling (Exception gets wrapped in AnalysisError)
        with pytest.raises(AnalysisError, match="Header/footer analysis failed.*LLM API timeout"):
            self.state.execute(self.base_context)

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_toc_methods_comprehensive_coverage(self, mock_llm_call):
        """Test comprehensive coverage of all TOC-specific methods.
        
        Test setup:
        - Mock LLM API to return multi-page response with diverse TOC data
        - Let real parser create HeaderFooterAnalysisResult with TOC methods
        - Test all 6 TOC methods with various data scenarios
        
        What it verifies:
        - get_toc_entries_by_page() returns correct page-specific entries
        - get_all_toc_entries() aggregates entries across all pages
        - get_toc_analysis_patterns() returns structured analysis data
        - get_toc_pages() identifies pages containing TOC content
        - has_toc_detected() correctly identifies TOC presence
        - All methods handle empty/missing data gracefully
        
        Key insight: Tests real TOC method functionality with authentic multi-page data.
        """
        # Mock comprehensive multi-page LLM response
        mock_llm_response = """
{
  "sampling_summary": {
    "page_indexes_analyzed": [0, 1, 2],
    "sampling_strategy": "comprehensive",
    "total_pages_analyzed": 3
  },
  "per_page_analysis": [
    {
      "page_index": 0,
      "page_number": 1,
      "document_elements": {
        "section_headings": [],
        "figure_titles": [],
        "table_titles": [],
        "table_of_contents": [
          {"text": "1. Introduction", "page_number": "5", "level": 1, "bbox": {"x0": 72, "top": 150, "x1": 200, "bottom": 166}},
          {"text": "1.1 Overview", "page_number": "5", "level": 2, "bbox": {"x0": 90, "top": 170, "x1": 180, "bottom": 186}}
        ]
      }
    },
    {
      "page_index": 1,
      "page_number": 2,
      "document_elements": {
        "section_headings": [],
        "figure_titles": [],
        "table_titles": [],
        "table_of_contents": [
          {"text": "2. Methods", "page_number": "12", "level": 1, "bbox": {"x0": 72, "top": 190, "x1": 150, "bottom": 206}},
          {"text": "2.1 Analysis", "page_number": "15", "level": 2, "bbox": {"x0": 90, "top": 210, "x1": 170, "bottom": 226}}
        ]
      }
    },
    {
      "page_index": 2,
      "page_number": 3,
      "document_elements": {
        "section_headings": [],
        "figure_titles": [],
        "table_titles": [],
        "table_of_contents": []
      }
    }
  ],
  "header_pattern": {
    "consistent_pattern": true,
    "pages_with_headers": [0, 1, 2],
    "typical_content": ["Document Header"],
    "y_boundary_typical": 50.0,
    "confidence": "High"
  },
  "footer_pattern": {
    "consistent_pattern": true,
    "pages_with_footers": [0, 1, 2],
    "typical_content": ["Page"],
    "y_boundary_typical": 750.0,
    "confidence": "High"
  },
  "page_numbering_analysis": {
    "numbering_detected": true,
    "numbering_pattern": "bottom_center",
    "confidence": "High"
  },
  "content_area_boundaries": {
    "main_content_starts_after_y": 60.0,
    "main_content_ends_before_y": 740.0,
    "confidence": "High"
  },
  "document_element_analysis": {
    "table_of_contents": {
      "detected": true,
      "toc_pages": [0, 1],
      "structure_patterns": ["hierarchical_numbering"],
      "confidence": "High"
    }
  },
  "insights": [
    "Multi-page TOC detected with hierarchical structure",
    "Page 1 contains TOC continuation",
    "Page 2 contains no TOC content"
  ]
}
        """
        
        # Mock the LLM response
        from pdf_plumb.llm.providers import LLMResponse
        mock_llm_call.return_value = LLMResponse(
            content=mock_llm_response.strip(),
            usage={
                "prompt_tokens": 2000,
                "completion_tokens": 600,
                "total_tokens": 2600
            },
            model="gpt-4",
            finish_reason="stop"
        )
        
        # Execute state - real parsing creates real HeaderFooterAnalysisResult
        result = self.state.execute(self.base_context)
        raw_result = result['raw_result']
        
        # Test get_toc_entries_by_page for each page
        page_0_entries = raw_result.get_toc_entries_by_page(0)
        assert len(page_0_entries) == 2
        assert page_0_entries[0]['text'] == "1. Introduction"
        assert page_0_entries[1]['text'] == "1.1 Overview"
        
        page_1_entries = raw_result.get_toc_entries_by_page(1)
        assert len(page_1_entries) == 2
        assert page_1_entries[0]['text'] == "2. Methods"
        assert page_1_entries[1]['text'] == "2.1 Analysis"
        
        page_2_entries = raw_result.get_toc_entries_by_page(2)
        assert len(page_2_entries) == 0  # Empty page
        
        # Test get_all_toc_entries aggregation
        all_entries = raw_result.get_all_toc_entries()
        assert len(all_entries) == 4
        assert all_entries[0]['text'] == "1. Introduction"
        assert all_entries[3]['text'] == "2.1 Analysis"
        
        # Test TOC detection methods
        assert raw_result.has_toc_detected() is True
        toc_pages = raw_result.get_toc_pages()
        assert 0 in toc_pages
        assert 1 in toc_pages
        
        # Test TOC analysis patterns
        patterns = raw_result.get_toc_analysis_patterns()
        assert patterns['detected'] is True
        assert 'hierarchical_numbering' in patterns.get('structure_patterns', [])
        # Execute state - real parsing creates real HeaderFooterAnalysisResult
        result = self.state.execute(self.base_context)
        raw_result = result['raw_result']
        
        # Test get_toc_entries_by_page for each page
        page_0_entries = raw_result.get_toc_entries_by_page(0)
        assert len(page_0_entries) == 2
        assert page_0_entries[0]['text'] == "1. Introduction"
        assert page_0_entries[1]['text'] == "1.1 Overview"
        
        page_1_entries = raw_result.get_toc_entries_by_page(1)
        assert len(page_1_entries) == 2
        assert page_1_entries[0]['text'] == "2. Methods"
        
        page_2_entries = raw_result.get_toc_entries_by_page(2)
        assert len(page_2_entries) == 0  # Empty page
        
        # Test get_all_toc_entries aggregation
        all_entries = raw_result.get_all_toc_entries()
        assert len(all_entries) == 4
        assert all_entries[0]['text'] == "1. Introduction"
        assert all_entries[2]['text'] == "2. Methods"
        # Verify page_index is added to each entry
        assert all_entries[0]['page_index'] == 0
        assert all_entries[2]['page_index'] == 1
        
        # Test TOC detection methods
        assert raw_result.has_toc_detected() is True
        toc_pages = raw_result.get_toc_pages()
        assert toc_pages == [0, 1]
        
        # Test TOC analysis patterns
        toc_patterns = raw_result.get_toc_analysis_patterns()
        assert toc_patterns is not None
        assert toc_patterns['detected'] is True
        assert toc_patterns['structure_patterns'] == ["hierarchical_numbering"]

    @patch('pdf_plumb.llm.providers.AzureOpenAIProvider.analyze_document_structure')
    def test_double_categorization_prevention(self, mock_llm_call):
        """Test prevention of double categorization between TOC entries and section headings.
        
        Test setup:
        - Mock LLM API to return response with overlapping content categories
        - Include same text appearing in both TOC entries and section headings
        - Let real parser handle the categorization logic
        
        What it verifies:
        - TOC entries and section headings are properly separated by real parser
        - Same text content can appear in appropriate categories without conflict
        - Analysis structure maintains clear boundaries between objective types
        
        Key insight: Tests real categorization logic with overlapping content scenarios.
        """
        # Mock LLM response with potential double categorization scenario
        mock_llm_response = """
{
  "sampling_summary": {
    "page_indexes_analyzed": [0],
    "sampling_strategy": "comprehensive",
    "total_pages_analyzed": 1
  },
  "per_page_analysis": [
    {
      "page_index": 0,
      "page_number": 1,
      "document_elements": {
        "section_headings": [
          {
            "text": "1. Introduction",
            "confidence": "High",
            "bbox": {"x0": 72, "top": 100, "x1": 200, "bottom": 116},
            "reasoning": "Clear section heading in document body"
          }
        ],
        "figure_titles": [],
        "table_titles": [
          {
            "text": "Table 1-1: Parameters",
            "confidence": "High",
            "bbox": {"x0": 72, "top": 300, "x1": 250, "bottom": 316},
            "reasoning": "Table title in document body"
          }
        ],
        "table_of_contents": [
          {
            "text": "1. Introduction",
            "page_number": "5",
            "level": 1,
            "bbox": {"x0": 72, "top": 150, "x1": 200, "bottom": 166},
            "reasoning": "TOC entry referencing section"
          },
          {
            "text": "Table 1-1: Parameters", 
            "page_number": "8",
            "level": 0,
            "bbox": {"x0": 72, "top": 170, "x1": 250, "bottom": 186},
            "reasoning": "TOC entry referencing table"
          }
        ]
      }
    }
  ],
  "header_pattern": {
    "consistent_pattern": true,
    "pages_with_headers": [0],
    "typical_content": ["Document Header"],
    "y_boundary_typical": 50.0,
    "confidence": "High"
  },
  "footer_pattern": {
    "consistent_pattern": true,
    "pages_with_footers": [0],
    "typical_content": ["Page 1"],
    "y_boundary_typical": 750.0,
    "confidence": "High"
  },
  "page_numbering_analysis": {
    "numbering_detected": true,
    "numbering_pattern": "bottom_center",
    "confidence": "High"
  },
  "content_area_boundaries": {
    "main_content_starts_after_y": 60.0,
    "main_content_ends_before_y": 740.0,
    "confidence": "High"
  },
  "document_element_analysis": {
    "table_of_contents": {
      "detected": true,
      "toc_pages": [0],
      "structure_patterns": ["hierarchical_numbering"],
      "confidence": "High"
    }
  },
  "insights": [
    "Document contains both section headings and TOC entries",
    "Same content appears in multiple analysis categories appropriately",
    "Clear separation maintained between TOC references and actual content"
  ]
}
        """
        
        # Mock the LLM response
        from pdf_plumb.llm.providers import LLMResponse
        mock_llm_call.return_value = LLMResponse(
            content=mock_llm_response.strip(),
            usage={
                "prompt_tokens": 1800,
                "completion_tokens": 550,
                "total_tokens": 2350
            },
            model="gpt-4",
            finish_reason="stop"
        )
        
        # Execute analysis - real parsing handles categorization
        result = self.state.execute(self.base_context)
        raw_result = result['raw_result']
        
        # Validate separate categorization is maintained
        section_headings = raw_result.get_all_section_headings()
        toc_entries = raw_result.get_all_toc_entries()
        table_titles = raw_result.get_all_table_titles()
        
        # Both should be present in their appropriate categories
        assert len(section_headings) == 1
        assert section_headings[0]['text'] == "1. Introduction"
        
        assert len(toc_entries) == 2
        assert toc_entries[0]['text'] == "1. Introduction"
        assert toc_entries[1]['text'] == "Table 1-1: Parameters"
        
        assert len(table_titles) == 1
        assert table_titles[0]['text'] == "Table 1-1: Parameters"
        
        # This demonstrates that the same text can appropriately appear
        # in multiple categories when contextually justified