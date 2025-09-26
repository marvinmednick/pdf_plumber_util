"""Header and footer analysis state implementation."""

from typing import Dict, Any, Optional
from pathlib import Path

from ..state import AnalysisState, StateTransition
from ...core.llm_analyzer import LLMDocumentAnalyzer
from ...core.pattern_manager import PatternSetManager
from ...core.document_scanner import DocumentScanner
from ...llm.responses import HeaderFooterAnalysisResult
from ...core.exceptions import AnalysisError, ConfigurationError


class HeaderFooterAnalysisState(AnalysisState):
    """State for comprehensive pattern-based document analysis.

    This state performs comprehensive document analysis using the Pattern Detection
    Architecture with programmatic preprocessing followed by LLM validation:

    Phase 1: Programmatic Pattern Detection
    - Full-document regex scanning for all pattern types
    - Font consistency analysis across 7 parameter combinations
    - Section completeness algorithms with TOC cross-reference

    Phase 2: LLM Comprehensive Analysis (Single Call)
    - Pattern validation and false positive filtering
    - Cross-validation between sections and TOC patterns
    - Unified hypothesis synthesis with confidence scoring

    Phase 3: Knowledge Accumulation
    - Multi-hypothesis management for competing theories
    - Progressive knowledge building for iterative refinement

    Transitions to additional section heading analysis for unused pages.
    """
    
    POSSIBLE_TRANSITIONS = {
        'additional_sections': StateTransition(
            target_state='additional_section_headings',
            condition='proceed_to_additional_analysis',
            description='Proceed to additional section heading analysis'
        ),
        'complete': StateTransition(
            target_state=None,
            condition='analysis_complete',
            description='Header/footer analysis workflow complete'
        )
    }
    
    REQUIRED_FIELDS = ['document_data']
    
    def __init__(self, provider_name: str = "azure", config_overrides: Optional[Dict[str, Any]] = None, sampling_seed: Optional[int] = None):
        """Initialize comprehensive pattern analysis state.

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

        # Initialize pattern detection components
        self.pattern_manager = PatternSetManager()
        self.document_scanner = DocumentScanner(self.pattern_manager)
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive pattern-based document analysis.

        Args:
            context: Workflow context containing document data and configuration

        Returns:
            Analysis results from three-phase pattern detection architecture:
            - Programmatic pattern scanning results
            - LLM comprehensive validation results
            - Knowledge accumulation for iterative refinement
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
            # PHASE 1: Programmatic Pattern Detection
            scan_result = self._perform_programmatic_analysis(document_data)

            # PHASE 2: LLM Comprehensive Analysis (Single Call)
            # For now, fall back to existing LLM analysis - will be enhanced with pattern data
            analysis_result = self.llm_analyzer.analyze_headers_footers(
                document_data=document_data,
                save_results=save_results,
                output_dir=output_dir
            )

            # PHASE 3: Knowledge Integration
            integrated_results = self._integrate_pattern_and_llm_results(
                scan_result, analysis_result
            )

            # Extract structured results for state machine
            results = self._extract_comprehensive_state_results(
                integrated_results, scan_result, analysis_result
            )

            # Get analysis status and token usage
            analysis_status = self.llm_analyzer.get_analysis_status()

            return {
                'analysis_type': 'comprehensive_pattern_analysis',
                'results': results,
                'metadata': {
                    'provider': self.provider_name,
                    'provider_configured': analysis_status['provider_configured'],
                    'token_usage': analysis_status.get('token_usage_summary', {}),
                    'confidence': {
                        'header': analysis_result.header_confidence.value,
                        'footer': analysis_result.footer_confidence.value,
                        'pattern_detection': self._calculate_pattern_confidence(scan_result)
                    },
                    'pages_analyzed': len(analysis_result.per_page_analysis),
                    'patterns_detected': scan_result.scan_statistics['total_matches'],
                    'programmatic_analysis': scan_result.scan_statistics
                },
                'knowledge': {
                    'header_pattern': analysis_result.header_pattern,
                    'footer_pattern': analysis_result.footer_pattern,
                    'content_boundaries': analysis_result.get_content_boundaries(),
                    'section_headings_found': len(analysis_result.get_all_section_headings()),
                    'figure_titles_found': len(analysis_result.get_all_figure_titles()),
                    'table_titles_found': len(analysis_result.get_all_table_titles()),
                    'pattern_matches': scan_result.pattern_matches,
                    'font_analysis': scan_result.font_analysis,
                    'document_context': scan_result.document_context
                },
                'raw_result': analysis_result,  # Store LLM result for external access
                'pattern_scan_result': scan_result  # Store pattern detection results
            }

        except ConfigurationError as e:
            raise AnalysisError(f"LLM configuration error in pattern analysis: {e}")
        except Exception as e:
            raise AnalysisError(f"Comprehensive pattern analysis failed: {e}")
    
    def determine_next_state(self, execution_result: Dict[str, Any], context: Dict[str, Any]) -> Optional[str]:
        """Determine next state - proceed to additional section heading analysis.
        
        Args:
            execution_result: Results from execute() method
            context: Current workflow context
            
        Returns:
            'additional_section_headings' to continue analysis, or None to terminate
        """
        # Check if additional analysis should be performed
        # For now, always proceed to additional section heading analysis
        return 'additional_section_headings'
    
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
    
    def _perform_programmatic_analysis(self, document_data) -> Any:
        """Perform Phase 1: Programmatic Pattern Detection.

        Returns:
            Comprehensive scan results from document scanner
        """
        # Scan document for all patterns
        scan_result = self.document_scanner.scan_full_document(document_data)

        # TODO: Add font consistency analysis across 7 parameter combinations
        # TODO: Add section completeness algorithms with TOC cross-reference

        return scan_result

    def _integrate_pattern_and_llm_results(self, scan_result, analysis_result) -> Dict[str, Any]:
        """Perform Phase 3: Knowledge Integration.

        Combines programmatic pattern detection with LLM analysis results.
        """
        # TODO: Implement sophisticated integration logic
        # For now, return basic integration
        return {
            'pattern_validation': 'pending_llm_enhancement',
            'cross_validation': 'pending_implementation',
            'unified_hypothesis': 'pending_implementation'
        }

    def _calculate_pattern_confidence(self, scan_result) -> float:
        """Calculate confidence score for pattern detection results."""
        if scan_result.scan_statistics['total_matches'] == 0:
            return 0.0

        # Simple confidence calculation based on match distribution
        total_matches = scan_result.scan_statistics['total_matches']
        patterns_with_matches = scan_result.scan_statistics['patterns_with_matches']

        if patterns_with_matches == 0:
            return 0.0

        # Basic confidence: ratio of successful pattern types
        base_confidence = patterns_with_matches / scan_result.scan_statistics['total_patterns_scanned']

        # Boost confidence if we have many matches
        match_boost = min(total_matches / 50.0, 0.3)  # Max 30% boost for 50+ matches

        return min(base_confidence + match_boost, 1.0)

    def _extract_comprehensive_state_results(self, integrated_results, scan_result, analysis_result) -> Dict[str, Any]:
        """Extract comprehensive results combining pattern detection and LLM analysis.

        Args:
            integrated_results: Results from knowledge integration phase
            scan_result: Pattern detection scan results
            analysis_result: LLM analysis results

        Returns:
            Structured results for workflow context
        """
        # Start with traditional LLM results
        base_results = self._extract_state_results(analysis_result)

        # Enhance with pattern detection results
        base_results['pattern_detection'] = {
            'total_patterns_detected': scan_result.scan_statistics['total_matches'],
            'section_patterns': len(self.document_scanner.get_matches_by_type(scan_result, 'section')),
            'toc_patterns': len(self.document_scanner.get_matches_by_type(scan_result, 'toc')),
            'figure_patterns': len(self.document_scanner.get_matches_by_type(scan_result, 'figure')),
            'table_patterns': len(self.document_scanner.get_matches_by_type(scan_result, 'table')),
            'font_analysis': scan_result.font_analysis,
            'document_context': scan_result.document_context
        }

        # Add integration results
        base_results['knowledge_integration'] = integrated_results

        return base_results

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