"""Header and footer analysis state implementation."""

from typing import Dict, Any, Optional
from pathlib import Path

from ..state import AnalysisState, StateTransition
from ...core.llm_analyzer import LLMDocumentAnalyzer
from ...llm.responses import HeaderFooterAnalysisResult
from ...core.exceptions import AnalysisError, ConfigurationError


class HeaderFooterAnalysisState(AnalysisState):
    """State for LLM-enhanced header and footer analysis.
    
    This state performs comprehensive document analysis including:
    - Header and footer pattern detection
    - Section heading identification 
    - Figure and table title detection
    - Content boundary analysis
    - Page numbering analysis
    
    Terminates workflow after completion (single-state workflow).
    """
    
    POSSIBLE_TRANSITIONS = {
        'complete': StateTransition(
            target_state=None,
            condition='analysis_complete',
            description='Header/footer analysis workflow complete'
        )
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def __init__(self, provider_name: str = "azure", config_overrides: Optional[Dict[str, Any]] = None, sampling_seed: Optional[int] = None):
        """Initialize header/footer analysis state.
        
        Args:
            provider_name: LLM provider to use (default: "azure")
            config_overrides: Optional configuration overrides for LLM provider
            sampling_seed: Optional seed for reproducible page sampling
        """
        super().__init__()
        self.provider_name = provider_name
        self.config_overrides = config_overrides or {}
        self.sampling_seed = sampling_seed
        self.llm_analyzer = None
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM-enhanced header/footer analysis.
        
        Args:
            context: Workflow context containing document data and configuration
            
        Returns:
            Analysis results including header/footer patterns, section headings,
            figure/table titles, and content boundaries
        """
        self.validate_input(context)
        
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
        
        try:
            # Use basic header/footer analysis (no incremental processing)
            analysis_result = self.llm_analyzer.analyze_headers_footers(
                document_data=document_data,
                save_results=save_results,
                output_dir=output_dir
            )
            
            # Extract structured results for state machine
            results = self._extract_state_results(analysis_result)
            
            # Get analysis status and token usage
            analysis_status = self.llm_analyzer.get_analysis_status()
            
            return {
                'analysis_type': 'header_footer_analysis',
                'results': results,
                'metadata': {
                    'provider': self.provider_name,
                    'provider_configured': analysis_status['provider_configured'],
                    'token_usage': analysis_status.get('token_usage_summary', {}),
                    'confidence': {
                        'header': analysis_result.header_confidence.value,
                        'footer': analysis_result.footer_confidence.value
                    },
                    'pages_analyzed': len(analysis_result.per_page_analysis)
                },
                'knowledge': {
                    'header_pattern': analysis_result.header_pattern,
                    'footer_pattern': analysis_result.footer_pattern,
                    'content_boundaries': analysis_result.get_content_boundaries(),
                    'section_headings_found': len(analysis_result.get_all_section_headings()),
                    'figure_titles_found': len(analysis_result.get_all_figure_titles()),
                    'table_titles_found': len(analysis_result.get_all_table_titles())
                },
                'raw_result': analysis_result  # Store full result for external access
            }
            
        except ConfigurationError as e:
            raise AnalysisError(f"LLM configuration error in header/footer analysis: {e}")
        except Exception as e:
            raise AnalysisError(f"Header/footer analysis failed: {e}")
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state - analysis is complete so terminate workflow.
        
        Args:
            execution_result: Results from execute() method
            context: Current workflow context
            
        Returns:
            None to terminate workflow
        """
        # Single-state workflow: always terminate after completion
        return None
    
    def estimate_cost(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate the cost of running this analysis.
        
        Args:
            context: Workflow context with document data
            
        Returns:
            Cost estimation details
        """
        self.validate_input(context)
        
        # Initialize analyzer for cost estimation
        temp_analyzer = LLMDocumentAnalyzer(
            provider_name=self.provider_name,
            config_overrides=self.config_overrides,
            sampling_seed=self.sampling_seed
        )
        
        document_data = context['document_data']
        
        try:
            return temp_analyzer.estimate_analysis_cost(
                document_data=document_data,
                analysis_type="headers-footers"
            )
        except Exception as e:
            return {"error": f"Cost estimation failed: {e}"}
    
    def _extract_state_results(self, analysis_result: HeaderFooterAnalysisResult) -> Dict[str, Any]:
        """Extract key results for state machine context.
        
        Args:
            analysis_result: Full HeaderFooterAnalysisResult
            
        Returns:
            Structured results for workflow context
        """
        return {
            'header_footer_patterns': {
                'header_pattern': analysis_result.header_pattern,
                'footer_pattern': analysis_result.footer_pattern,
                'content_boundaries': analysis_result.get_content_boundaries()
            },
            'document_elements': {
                'section_headings': analysis_result.get_all_section_headings(),
                'figure_titles': analysis_result.get_all_figure_titles(),
                'table_titles': analysis_result.get_all_table_titles()
            },
            'page_analysis': {
                'pages_with_headers': analysis_result.get_pages_with_headers(),
                'pages_with_footers': analysis_result.get_pages_with_footers(),
                'page_numbering': analysis_result.page_numbering_analysis
            },
            'insights': analysis_result.insights,
            'sampling_summary': analysis_result.sampling_summary
        }
    
    def validate_input(self, context: Dict[str, Any]) -> None:
        """Validate required input context for header/footer analysis.
        
        Args:
            context: Workflow context to validate
            
        Raises:
            AnalysisError: If required fields are missing or invalid
        """
        super().validate_input(context)
        
        document_data = context.get('document_data')
        if not document_data:
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
        
        if len(pages_data) < 20:
            raise AnalysisError(
                f"Document too short ({len(pages_data)} pages) for header/footer analysis. "
                "Minimum 20 pages required."
            )