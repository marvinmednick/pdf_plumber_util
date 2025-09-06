"""Unit tests for AdditionalSectionHeadingState."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from pdf_plumb.workflow.states.additional_section_headings import AdditionalSectionHeadingState
from pdf_plumb.workflow.state import StateTransition
from pdf_plumb.core.exceptions import AnalysisError, ConfigurationError
from pdf_plumb.llm.responses import HeaderFooterAnalysisResult


class TestAdditionalSectionHeadingState:
    """Test suite for AdditionalSectionHeadingState.
    
    Tests the functionality of the additional section heading analysis state,
    including page selection logic, LLM integration, and result processing.
    """
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.state = AdditionalSectionHeadingState(
            provider_name="azure",
            config_overrides={},
            sampling_seed=42,
            max_additional_pages=10
        )
        
        # Mock document data
        self.mock_document_data = [
            {
                'page_index': 1,
                'page_width': 612,
                'page_height': 792,
                'blocks': [
                    {'text': 'Header Text', 'y': 750, 'font': 'Arial', 'size': 10},
                    {'text': '1.1 Introduction', 'y': 700, 'font': 'Arial-Bold', 'size': 14},
                    {'text': 'Body text here', 'y': 650, 'font': 'Arial', 'size': 12}
                ]
            },
            {
                'page_index': 2,
                'page_width': 612,
                'page_height': 792,
                'blocks': [
                    {'text': 'Header Text', 'y': 750, 'font': 'Arial', 'size': 10},
                    {'text': 'A.1 Appendix Section', 'y': 700, 'font': 'Arial-Bold', 'size': 12},
                    {'text': 'Appendix content', 'y': 650, 'font': 'Arial', 'size': 12}
                ]
            }
        ]
        
        # Mock context with previous analysis results
        self.mock_context = {
            'document_data': self.mock_document_data,
            'save_results': False,
            'output_dir': None,
            'workflow_results': {
                'header_footer_analysis': {
                    'analysis_type': 'header_footer_analysis',
                    'raw_result': Mock(spec=HeaderFooterAnalysisResult)
                }
            }
        }
        
        # Setup mock raw result
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].sampling_summary = {
            'selected_page_indexes': [3, 4, 5, 6]  # Previously used pages
        }
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].header_pattern = {
            'consistent_pattern': True,
            'typical_content': ['Document Title']
        }
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].footer_pattern = {
            'consistent_pattern': True,
            'typical_content': ['Page X']
        }
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].get_all_section_headings.return_value = [
            {'text': '1. Introduction', 'font': 'Arial-Bold', 'size': 16}
        ]
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].get_all_figure_titles.return_value = []
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].get_all_table_titles.return_value = []
        self.mock_context['workflow_results']['header_footer_analysis']['raw_result'].get_font_style_patterns.return_value = [
            {'font': 'Arial-Bold', 'size': 16, 'usage': 'section_heading'}
        ]
    
    def test_state_initialization(self):
        """Test that AdditionalSectionHeadingState initializes correctly with proper configuration."""
        assert self.state.provider_name == "azure"
        assert self.state.max_additional_pages == 10
        assert self.state.sampling_seed == 42
        assert self.state.llm_analyzer is None
        
        # Check that required fields are defined
        assert 'document_data' in self.state.REQUIRED_FIELDS
        
        # Check that transitions are properly defined
        assert 'complete' in self.state.POSSIBLE_TRANSITIONS
        assert 'next_analysis' in self.state.POSSIBLE_TRANSITIONS
        assert isinstance(self.state.POSSIBLE_TRANSITIONS['complete'], StateTransition)
    
    def test_get_unused_pages_with_previous_results(self):
        """Test unused page detection when previous analysis results exist with used pages."""
        unused_pages = self.state._get_unused_pages(self.mock_context)
        
        # With 2 total pages and pages 3,4,5,6 marked as used (even though they don't exist),
        # pages 1,2 should be available as unused
        assert unused_pages == [1, 2]
    
    def test_get_unused_pages_no_previous_results(self):
        """Test unused page detection when no previous analysis results exist."""
        context = {
            'document_data': self.mock_document_data,
            'workflow_results': {}
        }
        
        unused_pages = self.state._get_unused_pages(context)
        
        # All pages should be available when no previous results
        assert unused_pages == [1, 2]
    
    def test_get_unused_pages_empty_document(self):
        """Test unused page detection with empty document returns empty list."""
        context = {
            'document_data': [],
            'workflow_results': {}
        }
        
        unused_pages = self.state._get_unused_pages(context)
        assert unused_pages == []
    
    def test_extract_pages_data_valid_pages(self):
        """Test page data extraction for valid page numbers returns correct subset."""
        pages_data = self.state._extract_pages_data(self.mock_document_data, [1, 2])
        
        assert len(pages_data) == 2
        assert pages_data[0]['page_index'] == 1
        assert pages_data[1]['page_index'] == 2
    
    def test_extract_pages_data_invalid_pages(self):
        """Test page data extraction handles invalid page numbers gracefully."""
        pages_data = self.state._extract_pages_data(self.mock_document_data, [5, 10])
        
        # Should return empty list for non-existent pages
        assert len(pages_data) == 0
    
    def test_extract_previous_patterns_with_results(self):
        """Test extraction of previous analysis patterns when results exist."""
        patterns = self.state._extract_previous_patterns(self.mock_context)
        
        assert patterns is not None
        assert 'header_pattern' in patterns
        assert 'footer_pattern' in patterns
        assert 'section_headings' in patterns
        assert patterns['header_pattern']['consistent_pattern'] is True
    
    def test_extract_previous_patterns_no_results(self):
        """Test extraction of previous patterns when no analysis results exist."""
        context = {'workflow_results': {}}
        patterns = self.state._extract_previous_patterns(context)
        
        assert patterns is None
    
    def test_extract_streamlined_page_data(self):
        """Test extraction of streamlined page data includes essential fields."""
        streamlined = self.state._extract_streamlined_page_data(self.mock_document_data)
        
        assert len(streamlined) == 2
        assert 'page_index' in streamlined[0]
        assert 'page_width' in streamlined[0]
        assert 'page_height' in streamlined[0]
        assert 'blocks' in streamlined[0]
        assert streamlined[0]['page_width'] == 612
        assert streamlined[0]['page_height'] == 792
    
    def test_create_empty_results(self):
        """Test creation of empty results structure when no analysis can be performed."""
        reason = "No unused pages available"
        results = self.state._create_empty_results(reason)
        
        assert results['analysis_type'] == 'additional_section_heading_analysis'
        assert results['metadata']['skip_reason'] == reason
        assert results['metadata']['additional_patterns_found'] is False
        assert results['results']['new_patterns_count'] == 0
        assert len(results['results']['section_headings']) == 0
    
    @patch('pdf_plumb.workflow.states.additional_section_headings.LLMDocumentAnalyzer')
    def test_execute_no_unused_pages(self, mock_analyzer_class):
        """Test execute method when no unused pages are available returns empty results."""
        # Mock context with all pages already used
        context = {
            'document_data': self.mock_document_data,
            'workflow_results': {
                'header_footer_analysis': {
                    'raw_result': Mock(sampling_summary={'selected_page_indexes': [1, 2]})
                }
            }
        }
        
        result = self.state.execute(context)
        
        assert result['analysis_type'] == 'additional_section_heading_analysis'
        assert result['metadata']['additional_patterns_found'] is False
        assert 'No unused pages available' in result['metadata']['skip_reason']
        
        # Should not initialize LLM analyzer when no pages to analyze
        mock_analyzer_class.assert_not_called()
    
    @patch('pdf_plumb.workflow.states.additional_section_headings.random.sample')
    @patch('pdf_plumb.workflow.states.additional_section_headings.LLMDocumentAnalyzer')
    def test_execute_limits_pages_to_max(self, mock_analyzer_class, mock_sample):
        """Test execute method limits analysis to maximum additional pages when many unused pages exist."""
        # Create more unused pages than max_additional_pages
        large_document = [{'page_index': i} for i in range(1, 16)]  # 15 pages
        context = {
            'document_data': large_document,
            'workflow_results': {},  # No previous results, so all pages unused
            'save_results': False,
            'output_dir': None
        }
        
        # Mock sampling to return limited set
        mock_sample.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        # Mock LLM analyzer and its components
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.config = Mock()
        mock_analyzer.config.output_dir = "/tmp/test"
        mock_analyzer.provider = Mock()
        mock_analyzer.provider.estimate_cost.return_value = {'estimated_cost_usd': 0.05}
        mock_analyzer.provider.analyze_document_structure.return_value = Mock()
        mock_analyzer.parser = Mock()
        
        # Mock the analysis result with proper method returns
        mock_result = Mock(spec=HeaderFooterAnalysisResult)
        mock_result.get_all_section_headings.return_value = [{'text': 'A.1 New Section'}]
        mock_result.get_all_figure_titles.return_value = []
        mock_result.get_all_table_titles.return_value = []
        mock_result.get_font_style_patterns.return_value = []
        mock_result.insights = ['Some insights']
        mock_result.sampling_summary = {}
        mock_result.get_pages_with_headers.return_value = []
        mock_result.get_pages_with_footers.return_value = []
        mock_result.header_pattern = {'consistent_pattern': True}
        mock_result.footer_pattern = {'consistent_pattern': True}
        mock_result.get_content_boundaries.return_value = {'top': 60, 'bottom': 740}
        
        mock_analyzer.parser.parse_header_footer_response.return_value = mock_result
        mock_analyzer.get_analysis_status.return_value = {'provider_configured': True}
        mock_analyzer.token_usage = {}
        mock_analyzer._save_structured_results_only = Mock()
        
        self.state.execute(context)
        
        # Should call random.sample with max_additional_pages limit
        mock_sample.assert_called_once()
        call_args = mock_sample.call_args
        # call_args is (args, kwargs) tuple, we want the second positional argument (k parameter)
        assert call_args[0][1] == 10  # max_additional_pages
    
    def test_determine_next_state_always_complete(self):
        """Test determine_next_state always returns None (workflow complete)."""
        execution_result = {'metadata': {'additional_patterns_found': True}}
        context = {}
        
        next_state = self.state.determine_next_state(execution_result, context)
        assert next_state is None
        
        # Test with no additional patterns found
        execution_result = {'metadata': {'additional_patterns_found': False}}
        next_state = self.state.determine_next_state(execution_result, context)
        assert next_state is None
    
    def test_validate_input_valid_context(self):
        """Test input validation passes with valid context containing required fields."""
        # Should not raise any exception
        self.state.validate_input(self.mock_context)
    
    def test_validate_input_missing_document_data(self):
        """Test input validation raises ValueError when document_data is missing."""
        invalid_context = {'workflow_results': {}}
        
        with pytest.raises(ValueError, match="Missing required field 'document_data'"):
            self.state.validate_input(invalid_context)
    
    def test_validate_input_empty_document_data(self):
        """Test input validation raises AnalysisError when document_data is empty."""
        invalid_context = {'document_data': []}
        
        with pytest.raises(AnalysisError, match="Document data cannot be empty"):
            self.state.validate_input(invalid_context)
    
    def test_validate_input_invalid_document_format(self):
        """Test input validation raises AnalysisError for invalid document data format."""
        invalid_context = {'document_data': "invalid_format"}
        
        with pytest.raises(AnalysisError, match="Document data must be list of pages"):
            self.state.validate_input(invalid_context)
    
    @patch('pdf_plumb.workflow.states.additional_section_headings.LLMDocumentAnalyzer')
    def test_estimate_cost_no_unused_pages(self, mock_analyzer_class):
        """Test cost estimation returns zero cost when no unused pages available."""
        # Mock context with all pages used
        context = {
            'document_data': self.mock_document_data,
            'workflow_results': {
                'header_footer_analysis': {
                    'raw_result': Mock(sampling_summary={'selected_page_indexes': [1, 2]})
                }
            }
        }
        
        cost_result = self.state.estimate_cost(context)
        
        assert cost_result['estimated_cost_usd'] == 0.0
        assert cost_result['reason'] == "No unused pages available"
        mock_analyzer_class.assert_not_called()
    
    @patch('pdf_plumb.workflow.states.additional_section_headings.LLMDocumentAnalyzer')
    def test_estimate_cost_with_unused_pages(self, mock_analyzer_class):
        """Test cost estimation calls LLM analyzer when unused pages exist."""
        # Mock analyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.estimate_analysis_cost.return_value = {'estimated_cost_usd': 0.05}
        
        cost_result = self.state.estimate_cost(self.mock_context)
        
        mock_analyzer_class.assert_called_once()
        mock_analyzer.estimate_analysis_cost.assert_called_once()
        assert cost_result['estimated_cost_usd'] == 0.05


class TestAdditionalSectionHeadingStateTOCEnhancement:
    """Test suite for new TOC detection capabilities in AdditionalSectionHeadingState."""
    
    def test_enhanced_prompt_includes_toc_detection(self):
        """Test that the enhanced prompt includes TOC detection instructions.
        
        Verifies that the LLM prompt has been updated to include:
        - TOC detection capabilities in system prompt
        - TOC analysis objectives in user prompt
        - TOC-related response format in JSON schema
        
        This test ensures the state properly requests TOC analysis from the LLM.
        """
        from pdf_plumb.llm.prompts import PromptTemplates
        
        # Create test data for prompt generation
        test_data = [
            {
                'page_index': 5,
                'page_width': 612,
                'page_height': 792,
                'blocks': [
                    {'text': 'Table of Contents', 'y': 700, 'font': 'Arial-Bold', 'size': 16},
                    {'text': '1. Introduction ..................... 1', 'y': 650, 'font': 'Arial', 'size': 12},
                    {'text': '2. Methods ......................... 5', 'y': 620, 'font': 'Arial', 'size': 12}
                ]
            }
        ]
        
        # Generate the enhanced prompt
        prompt = PromptTemplates.additional_section_heading_analysis(
            total_pages=50,
            analyzed_pages=[5],
            page_data=test_data,
            previous_patterns=None
        )
        
        # Verify TOC-related content is present in the prompt
        assert "Table of Contents (TOC) detection and analysis" in prompt
        assert "TOC start locations and content organization" in prompt
        assert "Table of Contents Detection" in prompt
        assert "TOC Start Detection" in prompt
        assert "toc_detection" in prompt
        assert "toc_patterns" in prompt
        assert "main_contents|list_of_figures|list_of_tables|list_of_equations" in prompt
        
    def test_toc_response_format_in_prompt(self):
        """Test that the prompt includes proper TOC response format structure.
        
        Verifies that the JSON response format includes:
        - toc_detection section in per_page_analysis
        - toc_patterns section in new_patterns_identified
        - TOC-related insights in insights array
        
        This ensures the LLM knows how to structure TOC detection results.
        """
        from pdf_plumb.llm.prompts import PromptTemplates
        
        prompt = PromptTemplates.additional_section_heading_analysis(
            total_pages=20,
            analyzed_pages=[3],
            page_data=[{'page_index': 3, 'blocks': []}]
        )
        
        # Verify TOC response format elements
        assert '"toc_detection"' in prompt
        assert '"toc_sections_found"' in prompt
        assert '"toc_type"' in prompt
        assert '"starts_on_page"' in prompt
        assert '"start_y_position"' in prompt
        assert '"toc_patterns"' in prompt
        assert '"toc_sections_detected"' in prompt
        assert '"toc_types_found"' in prompt
        assert '"toc_start_pages"' in prompt
        assert "TOC sections detected and their formatting patterns" in prompt


@pytest.mark.integration
class TestAdditionalSectionHeadingStateIntegration:
    """Integration tests for AdditionalSectionHeadingState with real components.
    
    These tests verify the state works correctly with actual LLM analyzer components
    and state machine orchestrator integration.
    """
    
    def test_state_registration(self):
        """Test that AdditionalSectionHeadingState is properly registered in the state registry."""
        from pdf_plumb.workflow.registry import get_state_class, list_state_names
        
        # Check state is in registry
        state_names = list_state_names()
        assert 'additional_section_headings' in state_names
        
        # Check we can retrieve the state class
        state_class = get_state_class('additional_section_headings')
        assert state_class == AdditionalSectionHeadingState
    
    def test_state_transitions_validation(self):
        """Test that state transitions are properly validated on registration."""
        # This should not raise any exceptions
        AdditionalSectionHeadingState.validate_transitions()
        
        # Check that transitions don't reference self
        for transition in AdditionalSectionHeadingState.POSSIBLE_TRANSITIONS.values():
            assert transition.target_state != 'additional_section_headings'