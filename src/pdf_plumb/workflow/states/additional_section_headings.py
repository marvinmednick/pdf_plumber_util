"""Additional section heading analysis state implementation."""

from typing import Dict, Any, Optional, List, Set
from pathlib import Path
from datetime import datetime
import random

from ..state import AnalysisState, StateTransition
from ...core.llm_analyzer import LLMDocumentAnalyzer
from ...llm.responses import HeaderFooterAnalysisResult
from ...llm.sampling import SamplingResult
from ...llm.prompts import PromptTemplates
from ...core.exceptions import AnalysisError, ConfigurationError


class AdditionalSectionHeadingState(AnalysisState):
    """State for comprehensive document analysis including section headings and TOC detection.
    
    This state performs supplementary document analysis to identify:
    - New section heading levels, formats, and numbering patterns
    - Additional table headings, figure headings, or equation headings
    - Previously undetected font styles and formatting patterns
    - Table of Contents (TOC) sections and their formatting patterns
    - TOC start locations and organizational structure  
    - Validation of header/footer formats and page margins consistency
    
    Requirements:
    - Uses pages that have NOT been used in previous states (up to 10 additional pages)
    - Randomly selects from unused pages
    - Skips to next state if no unused pages remain
    - Performs multi-faceted analysis including TOC detection and validation
    - Stores comprehensive information: fonts, styles, numbering, TOC patterns
    """
    
    POSSIBLE_TRANSITIONS = {
        'complete': StateTransition(
            target_state=None,
            condition='additional_analysis_complete',
            description='Additional section heading analysis complete - workflow terminated'
        ),
        'next_analysis': StateTransition(
            target_state=None,  # No next state - workflow complete after additional analysis
            condition='additional_patterns_found',
            description='Additional patterns found but no further states available - workflow complete'
        )
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def __init__(
        self, 
        provider_name: str = "azure", 
        config_overrides: Optional[Dict[str, Any]] = None, 
        sampling_seed: Optional[int] = None,
        max_additional_pages: int = 10
    ):
        """Initialize comprehensive document analysis state.
        
        Args:
            provider_name: LLM provider to use (default: "azure")
            config_overrides: Optional configuration overrides for LLM provider
            sampling_seed: Optional seed for reproducible page sampling
            max_additional_pages: Maximum number of additional pages to analyze (default: 10)
        """
        super().__init__()
        self.provider_name = provider_name
        self.config_overrides = config_overrides or {}
        self.sampling_seed = sampling_seed
        self.max_additional_pages = max_additional_pages
        self.llm_analyzer = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive document analysis including section headings and TOC detection.
        
        Args:
            context: Workflow context containing document data and previous results
            
        Returns:
            Analysis results including new section heading patterns, TOC detection,
            font styles, and validation of header/footer consistency
        """
        self.validate_input(context)
        
        # Get unused pages from previous analysis
        unused_pages = self._get_unused_pages(context)
        
        # If no unused pages, skip analysis
        if not unused_pages:
            return self._create_empty_results("No unused pages available for additional analysis")
        
        # Limit to max additional pages and randomly sample
        if len(unused_pages) > self.max_additional_pages:
            if self.sampling_seed is not None:
                random.seed(self.sampling_seed)
            unused_pages = sorted(random.sample(unused_pages, self.max_additional_pages))
        
        # Initialize LLM analyzer
        self.llm_analyzer = LLMDocumentAnalyzer(
            provider_name=self.provider_name,
            config_overrides=self.config_overrides,
            sampling_seed=self.sampling_seed
        )
        
        # Extract document data
        document_data = context['document_data']
        
        # Get analysis options from context
        save_results = context.get('save_results', True)
        output_dir = context.get('output_dir')
        if output_dir:
            output_dir = Path(output_dir)
        
        # Create subset of document data for unused pages
        additional_pages_data = self._extract_pages_data(document_data, unused_pages)
        
        try:
            # Perform analysis on additional pages
            analysis_result = self._analyze_additional_pages(
                additional_pages_data, 
                context, 
                save_results, 
                output_dir
            )
            
            # Extract structured results for state machine
            results = self._extract_state_results(analysis_result, unused_pages)
            
            # Get analysis status and token usage
            analysis_status = self.llm_analyzer.get_analysis_status()
            
            return {
                'analysis_type': 'additional_section_heading_analysis',
                'results': results,
                'metadata': {
                    'provider': self.provider_name,
                    'provider_configured': analysis_status['provider_configured'],
                    'token_usage': analysis_status.get('token_usage_summary', {}),
                    'pages_analyzed': len(unused_pages),
                    'unused_pages_analyzed': unused_pages,
                    'additional_patterns_found': results.get('new_patterns_count', 0) > 0
                },
                'knowledge': {
                    'additional_section_patterns': results.get('section_headings', []),
                    'additional_figure_patterns': results.get('figure_titles', []),
                    'additional_table_patterns': results.get('table_titles', []),
                    'header_footer_consistency': results.get('header_footer_validation', {}),
                    'new_font_styles_found': len(results.get('new_font_styles', [])),
                    'pages_with_new_content': unused_pages
                },
                'raw_result': analysis_result  # Store full result for external access
            }
            
        except ConfigurationError as e:
            raise AnalysisError(f"LLM configuration error in additional section heading analysis: {e}")
        except Exception as e:
            raise AnalysisError(f"Additional section heading analysis failed: {e}")
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state based on whether additional patterns were found.
        
        Args:
            execution_result: Results from execute() method
            context: Current workflow context
            
        Returns:
            None to terminate workflow, or next state name if patterns found
        """
        # Check if additional patterns were found
        additional_patterns_found = execution_result.get('metadata', {}).get('additional_patterns_found', False)
        
        if additional_patterns_found:
            # Could proceed to next analysis phase if there are more states to process
            # For now, always complete since this is a supplementary analysis
            return None
        else:
            # No additional patterns found, complete workflow
            return None
    
    def estimate_cost(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the cost of running additional section heading analysis.
        
        Args:
            context: Workflow context with document data
            
        Returns:
            Cost estimation details
        """
        self.validate_input(context)
        
        # Get unused pages
        unused_pages = self._get_unused_pages(context)
        
        if not unused_pages:
            return {"estimated_cost_usd": 0.0, "reason": "No unused pages available"}
        
        # Limit to max additional pages for cost estimation
        pages_to_analyze = min(len(unused_pages), self.max_additional_pages)
        
        # Initialize analyzer for cost estimation
        temp_analyzer = LLMDocumentAnalyzer(
            provider_name=self.provider_name,
            config_overrides=self.config_overrides,
            sampling_seed=self.sampling_seed
        )
        
        document_data = context['document_data']
        additional_pages_data = self._extract_pages_data(document_data, unused_pages[:pages_to_analyze])
        
        try:
            return temp_analyzer.estimate_analysis_cost(
                document_data=additional_pages_data,
                analysis_type="headers-footers"  # Using similar analysis type for estimation
            )
        except Exception as e:
            return {"error": f"Cost estimation failed: {e}"}
    
    def _get_unused_pages(self, context: Dict[str, Any]) -> List[int]:
        """Get list of pages not used in previous analysis states.
        
        Args:
            context: Workflow context containing previous results
            
        Returns:
            List of unused page numbers (1-indexed)
        """
        # Extract total pages from document data
        document_data = context['document_data']
        if isinstance(document_data, dict) and 'pages' in document_data:
            total_pages = len(document_data['pages'])
        elif isinstance(document_data, list):
            total_pages = len(document_data)
        else:
            return []
        
        all_pages = set(range(1, total_pages + 1))
        used_pages = set()
        
        # Collect used pages from previous workflow results
        workflow_results = context.get('workflow_results', {})
        
        for state_name, state_result in workflow_results.items():
            # Look for sampling information in previous results
            if 'raw_result' in state_result and hasattr(state_result['raw_result'], 'sampling_summary'):
                sampling_summary = state_result['raw_result'].sampling_summary
                # Check for page indexes under different field names (compatibility)
                page_indexes = sampling_summary.get('page_indexes_analyzed') or sampling_summary.get('selected_page_indexes', [])
                if page_indexes:
                    used_pages.update(page_indexes)
            
            # Also check results structure for page information
            results = state_result.get('results', {})
            if 'sampling_summary' in results:
                sampling_info = results['sampling_summary']
                # Check for page indexes under different field names (compatibility)
                page_indexes = sampling_info.get('page_indexes_analyzed') or sampling_info.get('selected_page_indexes', [])
                if page_indexes:
                    used_pages.update(page_indexes)
        
        # Return unused pages as sorted list
        unused_pages = sorted(all_pages - used_pages)
        return unused_pages
    
    def _extract_pages_data(self, document_data: Any, page_numbers: List[int]) -> List[Dict[str, Any]]:
        """Extract specific pages from document data.
        
        Args:
            document_data: Full document data
            page_numbers: List of page numbers to extract (1-indexed)
            
        Returns:
            List of page data for specified pages
        """
        # Convert document data to pages list
        if isinstance(document_data, dict) and 'pages' in document_data:
            all_pages = document_data['pages']
        elif isinstance(document_data, list):
            all_pages = document_data
        else:
            raise AnalysisError("Invalid document data format")
        
        # Extract requested pages (convert to 0-indexed)
        extracted_pages = []
        for page_num in page_numbers:
            if 1 <= page_num <= len(all_pages):
                extracted_pages.append(all_pages[page_num - 1])
        
        return extracted_pages
    
    def _analyze_additional_pages(
        self, 
        pages_data: List[Dict[str, Any]], 
        context: Dict[str, Any],
        save_results: bool, 
        output_dir: Optional[Path]
    ) -> HeaderFooterAnalysisResult:
        """Analyze additional pages for new section heading patterns.
        
        Args:
            pages_data: Pages data to analyze
            context: Full workflow context for reference
            save_results: Whether to save results
            output_dir: Output directory for results
            
        Returns:
            Analysis result for additional pages
        """
        # Extract previous patterns from context for specialized analysis
        previous_patterns = self._extract_previous_patterns(context)
        
        # Get page metadata
        document_data = context['document_data']
        if isinstance(document_data, dict) and 'pages' in document_data:
            total_pages = len(document_data['pages'])
            page_width = document_data['pages'][0].get('page_width', document_data['pages'][0].get('width', 612))
            page_height = document_data['pages'][0].get('page_height', document_data['pages'][0].get('height', 792))
        elif isinstance(document_data, list):
            total_pages = len(document_data)
            page_width = document_data[0].get('page_width', document_data[0].get('width', 612))
            page_height = document_data[0].get('page_height', document_data[0].get('height', 792))
        else:
            total_pages = len(pages_data)
            page_width = 612
            page_height = 792
        
        # Get analyzed page numbers
        analyzed_pages = self._get_analyzed_page_numbers(pages_data, document_data)
        
        # Extract streamlined page data for LLM
        page_data_for_llm = self._extract_streamlined_page_data(pages_data)
        
        # Generate specialized prompt for additional section heading analysis
        prompt = PromptTemplates.additional_section_heading_analysis(
            total_pages=total_pages,
            analyzed_pages=analyzed_pages,
            page_data=page_data_for_llm,
            previous_patterns=previous_patterns,
            page_width=page_width,
            page_height=page_height
        )
        
        # Estimate cost
        cost_estimate = self.llm_analyzer.provider.estimate_cost(prompt)
        
        # Save prompt if saving is enabled
        base_name = None
        output_dir_path = None
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"llm_additional_sections_{timestamp}"
            output_dir_path = Path(output_dir or self.llm_analyzer.config.output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            prompt_file = output_dir_path / f"{base_name}_prompt.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
        
        # Send request to LLM
        try:
            llm_response = self.llm_analyzer.provider.analyze_document_structure(prompt)
            
            # Save response if saving is enabled
            if save_results:
                response_file = output_dir_path / f"{base_name}_response.txt"
                with open(response_file, 'w') as f:
                    f.write(llm_response.content)
            
            # Track token usage
            self.llm_analyzer.token_usage['additional_sections'] = {
                'estimated': cost_estimate,
                'actual': llm_response.usage,
                'model': llm_response.model,
                'timestamp': datetime.now().isoformat()
            }
            
            # Parse response using header/footer parser (matches actual LLM response format)
            analysis_result = self.llm_analyzer.parser.parse_header_footer_response(llm_response.content)
            
            # Save structured results if requested
            if save_results:
                self.llm_analyzer._save_structured_results_only(
                    analysis_type='additional_sections',
                    results=analysis_result,
                    base_name=base_name,
                    output_dir_path=output_dir_path,
                    sampling_info=None,  # No specific sampling for this analysis
                    llm_response=llm_response
                )
            
            return analysis_result
            
        except Exception as e:
            raise AnalysisError(f"Additional section heading analysis failed: {e}")
    
    def _extract_state_results(self, analysis_result: HeaderFooterAnalysisResult, analyzed_pages: List[int]) -> Dict[str, Any]:
        """Extract key results for state machine context.
        
        Args:
            analysis_result: Full HeaderFooterAnalysisResult
            analyzed_pages: List of page numbers that were analyzed
            
        Returns:
            Structured results for workflow context
        """
        # Get new section headings
        section_headings = analysis_result.get_all_section_headings()
        figure_titles = analysis_result.get_all_figure_titles()
        table_titles = analysis_result.get_all_table_titles()
        
        # Count new patterns found
        new_patterns_count = len(section_headings) + len(figure_titles) + len(table_titles)
        
        return {
            'section_headings': section_headings,
            'figure_titles': figure_titles,
            'table_titles': table_titles,
            'new_patterns_count': new_patterns_count,
            'header_footer_validation': {
                'header_pattern': analysis_result.header_pattern,
                'footer_pattern': analysis_result.footer_pattern,
                'content_boundaries': analysis_result.get_content_boundaries()
            },
            'new_font_styles': analysis_result.get_font_style_patterns(),
            'page_analysis': {
                'pages_analyzed': analyzed_pages,
                'pages_with_headers': analysis_result.get_pages_with_headers(),
                'pages_with_footers': analysis_result.get_pages_with_footers()
            },
            'insights': analysis_result.insights,
            'sampling_summary': analysis_result.sampling_summary
        }
    
    def _create_empty_results(self, reason: str) -> Dict[str, Any]:
        """Create empty results when no analysis can be performed.
        
        Args:
            reason: Reason why no analysis was performed
            
        Returns:
            Empty results structure
        """
        return {
            'analysis_type': 'additional_section_heading_analysis',
            'results': {
                'section_headings': [],
                'figure_titles': [],
                'table_titles': [],
                'new_patterns_count': 0,
                'header_footer_validation': {},
                'new_font_styles': [],
                'page_analysis': {'pages_analyzed': []},
                'insights': [],
                'sampling_summary': {}
            },
            'metadata': {
                'provider': self.provider_name,
                'provider_configured': False,
                'token_usage': {},
                'pages_analyzed': 0,
                'unused_pages_analyzed': [],
                'additional_patterns_found': False,
                'skip_reason': reason
            },
            'knowledge': {
                'additional_section_patterns': [],
                'additional_figure_patterns': [],
                'additional_table_patterns': [],
                'header_footer_consistency': {},
                'new_font_styles_found': 0,
                'pages_with_new_content': []
            },
            'raw_result': None
        }
    
    def validate_input(self, context: Dict[str, Any]) -> None:
        """Validate required input context for additional section heading analysis.
        
        Args:
            context: Workflow context to validate
            
        Raises:
            AnalysisError: If required fields are missing or invalid
        """
        super().validate_input(context)
        
        document_data = context.get('document_data')
        if document_data is None:
            raise AnalysisError("Missing required 'document_data' in context")
        
        # Validate document data format
        if isinstance(document_data, dict):
            if 'pages' not in document_data:
                raise AnalysisError("Document data dict must contain 'pages' key")
            pages_data = document_data['pages']
        elif isinstance(document_data, list):
            pages_data = document_data
        else:
            raise AnalysisError("Document data must be list of pages or dict with 'pages' key")
        
        if not pages_data:
            raise AnalysisError("Document data cannot be empty")
        
        # No minimum page requirement for additional analysis since we work with unused pages
    
    def _extract_previous_patterns(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract previous analysis patterns from workflow context.
        
        Args:
            context: Workflow context containing previous results
            
        Returns:
            Dictionary of previous patterns for reference, or None
        """
        workflow_results = context.get('workflow_results', {})
        
        # Look for header/footer analysis results
        for state_name, state_result in workflow_results.items():
            if state_result.get('analysis_type') == 'header_footer_analysis':
                raw_result = state_result.get('raw_result')
                if raw_result:
                    return {
                        'header_pattern': raw_result.header_pattern,
                        'footer_pattern': raw_result.footer_pattern,
                        'section_headings': raw_result.get_all_section_headings(),
                        'figure_titles': raw_result.get_all_figure_titles(),
                        'table_titles': raw_result.get_all_table_titles(),
                        'font_style_patterns': raw_result.get_font_style_patterns()
                    }
        
        return None
    
    def _get_analyzed_page_numbers(self, pages_data: List[Dict[str, Any]], document_data: Any) -> List[int]:
        """Get the page numbers for the pages being analyzed.
        
        Args:
            pages_data: Subset of pages being analyzed
            document_data: Full document data for reference
            
        Returns:
            List of page numbers (1-indexed) corresponding to pages_data
        """
        # Convert document data to full pages list
        if isinstance(document_data, dict) and 'pages' in document_data:
            all_pages = document_data['pages']
        elif isinstance(document_data, list):
            all_pages = document_data
        else:
            # Fallback: assume sequential pages
            return list(range(1, len(pages_data) + 1))
        
        # Find the page numbers by matching page data
        analyzed_page_numbers = []
        for page_data in pages_data:
            # Try to find this page in the full document
            for i, full_page in enumerate(all_pages):
                if full_page == page_data:  # Exact match
                    analyzed_page_numbers.append(i + 1)  # Convert to 1-indexed
                    break
            else:
                # If exact match fails, try to match by unique identifiers
                page_index = page_data.get('page_index', page_data.get('page_number'))
                if page_index is not None:
                    analyzed_page_numbers.append(page_index)
        
        # If we couldn't determine page numbers, return sequential numbers
        if not analyzed_page_numbers or len(analyzed_page_numbers) != len(pages_data):
            return list(range(1, len(pages_data) + 1))
        
        return analyzed_page_numbers
    
    def _extract_streamlined_page_data(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract streamlined page data suitable for LLM analysis.
        
        Args:
            pages_data: Full page data
            
        Returns:
            Streamlined page data with essential fields only
        """
        streamlined_data = []
        
        for page_data in pages_data:
            # Extract essential information for LLM analysis
            page_info = {
                'page_index': page_data.get('page_index', page_data.get('page_number', 1)),
                'page_width': page_data.get('page_width', page_data.get('width', 612)),
                'page_height': page_data.get('page_height', page_data.get('height', 792))
            }
            
            # Include text blocks if available
            if 'blocks' in page_data:
                page_info['blocks'] = page_data['blocks']
            elif 'text_blocks' in page_data:
                page_info['blocks'] = page_data['text_blocks']
            
            # Include analysis information if available
            if 'analysis' in page_data:
                page_info['analysis'] = page_data['analysis']
            
            streamlined_data.append(page_info)
        
        return streamlined_data