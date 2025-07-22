"""Core LLM-enhanced document analysis."""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from ..config import get_config
from ..llm.providers import get_llm_provider, LLMProvider, LLMResponse
from ..llm.sampling import PageSampler, SamplingResult
from ..llm.prompts import PromptTemplates
from ..llm.responses import ResponseParser, HeaderFooterAnalysisResult
from ..utils.token_counter import DocumentTokenAnalyzer
from ..core.exceptions import AnalysisError, ConfigurationError


class LLMDocumentAnalyzer:
    """LLM-enhanced document analysis coordinator."""
    
    def __init__(
        self,
        provider_name: str = "azure",
        config_overrides: Optional[Dict[str, Any]] = None
    ):
        """Initialize LLM document analyzer.
        
        Args:
            provider_name: LLM provider to use ("azure")
            config_overrides: Optional provider configuration overrides
        """
        self.provider_name = provider_name
        self.config_overrides = config_overrides or {}
        
        # Initialize components
        self.provider: LLMProvider = get_llm_provider(provider_name, **self.config_overrides)
        self.sampler = PageSampler()
        self.parser = ResponseParser()
        self.config = get_config()
        
        # Analysis state
        self.analysis_results: Dict[str, Any] = {}
        self.token_usage: Dict[str, Any] = {}
    
    def analyze_headers_footers(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> HeaderFooterAnalysisResult:
        """Analyze document headers and footers using LLM.
        
        Args:
            document_data: Document pages data or full document structure
            save_results: Whether to save results to file
            output_dir: Directory to save results (uses config default if None)
            
        Returns:
            Structured header/footer analysis results
        """
        # Validate provider configuration
        if not self.provider.is_configured():
            raise ConfigurationError(
                f"LLM provider '{self.provider_name}' not properly configured. "
                "Check environment variables for API credentials."
            )
        
        # Extract pages data
        if isinstance(document_data, dict) and 'pages' in document_data:
            pages_data = document_data['pages']
        elif isinstance(document_data, list):
            pages_data = document_data
        else:
            raise AnalysisError("Invalid document data format. Expected list of pages or dict with 'pages' key.")
        
        total_pages = len(pages_data)
        
        # Sample pages for analysis
        sampling_result = self.sampler.sample_for_header_footer_analysis(total_pages)
        if not sampling_result:
            raise AnalysisError(
                f"Document too short ({total_pages} pages) for header/footer analysis. "
                "Minimum 20 pages required."
            )
        
        # Extract streamlined page data
        page_data_for_llm = self.sampler.extract_page_data(pages_data, sampling_result)
        
        # Get document metadata
        page_width = pages_data[0].get('page_width', pages_data[0].get('width', 612))
        page_height = pages_data[0].get('page_height', pages_data[0].get('height', 792))
        footer_boundary = self._extract_footer_boundary(pages_data[0])
        
        # Generate prompt
        prompt = PromptTemplates.header_footer_analysis(
            total_pages=total_pages,
            group_ranges=sampling_result.get_group_ranges(),
            individual_pages=sampling_result.individuals,
            selected_page_indexes=sampling_result.selected_pages,
            page_data=page_data_for_llm,
            page_width=page_width,
            page_height=page_height,
            footer_boundary=footer_boundary
        )
        
        # Estimate cost
        cost_estimate = self.provider.estimate_cost(prompt)
        
        # Send request to LLM
        try:
            llm_response = self.provider.analyze_document_structure(prompt)
            
            # Track token usage
            self.token_usage['headers_footers'] = {
                'estimated': cost_estimate,
                'actual': llm_response.usage,
                'model': llm_response.model,
                'timestamp': datetime.now().isoformat()
            }
            
            # Parse response
            analysis_result = self.parser.parse_header_footer_response(llm_response.content)
            
            # Store results
            self.analysis_results['headers_footers'] = analysis_result
            
            # Save results if requested
            if save_results:
                self._save_analysis_results(
                    analysis_type='headers_footers',
                    results=analysis_result,
                    output_dir=output_dir,
                    sampling_info=sampling_result,
                    prompt=prompt,
                    llm_response=llm_response
                )
            
            return analysis_result
            
        except Exception as e:
            raise AnalysisError(f"Header/footer analysis failed: {e}")
    
    def analyze_sections(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        known_header_footer_patterns: Optional[Dict[str, Any]] = None,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Analyze document section hierarchy using LLM."""
        # Implementation similar to headers/footers but focused on sections
        raise NotImplementedError("Section analysis not yet implemented")
    
    def analyze_toc(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        known_section_patterns: Optional[Dict[str, Any]] = None,
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Analyze document Table of Contents using LLM."""
        # Implementation for TOC detection
        raise NotImplementedError("TOC analysis not yet implemented")
    
    def multi_objective_analysis(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        primary_focus: str = "headers-footers",
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Perform multi-objective analysis with priority focus."""
        # Implementation for continuous multi-objective analysis
        raise NotImplementedError("Multi-objective analysis not yet implemented")
    
    def estimate_analysis_cost(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        analysis_type: str = "headers-footers"
    ) -> Dict[str, Any]:
        """Estimate the cost of LLM analysis.
        
        Args:
            document_data: Document data to analyze
            analysis_type: Type of analysis to estimate
            
        Returns:
            Cost estimation details
        """
        # Extract pages data
        if isinstance(document_data, dict) and 'pages' in document_data:
            pages_data = document_data['pages']
        elif isinstance(document_data, list):
            pages_data = document_data
        else:
            raise AnalysisError("Invalid document data format")
        
        total_pages = len(pages_data)
        
        # Create mock sampling for cost estimation
        if analysis_type == "headers-footers":
            sampling_result = self.sampler.sample_for_header_footer_analysis(total_pages)
            if not sampling_result:
                return {"error": f"Document too short ({total_pages} pages)"}
            
            page_data_for_llm = self.sampler.extract_page_data(pages_data, sampling_result)
            
            # Generate prompt for estimation
            prompt = PromptTemplates.header_footer_analysis(
                total_pages=total_pages,
                group_ranges=sampling_result.get_group_ranges(),
                individual_pages=sampling_result.individuals,
                selected_page_indexes=sampling_result.selected_pages,
                page_data=page_data_for_llm
            )
            
            return self.provider.estimate_cost(prompt)
        
        else:
            raise ValueError(f"Cost estimation not implemented for analysis type: {analysis_type}")
    
    def get_analysis_status(self) -> Dict[str, Any]:
        """Get current analysis status and results summary."""
        return {
            'provider': self.provider_name,
            'provider_configured': self.provider.is_configured(),
            'completed_analyses': list(self.analysis_results.keys()),
            'token_usage_summary': self._summarize_token_usage(),
            'config': {
                'batch_size': self.config.llm_batch_size,
                'sampling_groups': self.config.llm_sampling_groups,
                'sampling_individuals': self.config.llm_sampling_individuals
            }
        }
    
    def _extract_footer_boundary(self, page_data: Dict[str, Any]) -> Optional[float]:
        """Extract programmatic footer boundary from page data."""
        # Try various locations where footer boundary might be stored
        analysis = page_data.get('analysis', {})
        if 'footer_boundary' in analysis:
            return analysis['footer_boundary']
        
        # Could also check other locations based on document format
        return None
    
    def _save_analysis_results(
        self,
        analysis_type: str,
        results: Any,
        output_dir: Optional[Path],
        sampling_info: SamplingResult,
        prompt: str,
        llm_response: LLMResponse
    ) -> None:
        """Save analysis results to files."""
        if not output_dir:
            output_dir = self.config.output_dir
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"llm_{analysis_type}_{timestamp}"
        
        # Save structured results
        results_file = output_dir / f"{base_name}_results.json"
        results_data = {
            'analysis_type': analysis_type,
            'timestamp': datetime.now().isoformat(),
            'provider': self.provider_name,
            'sampling_info': {
                'groups': sampling_info.groups,
                'individuals': sampling_info.individuals,
                'total_selected': sampling_info.total_pages_selected
            },
            'results': results.__dict__ if hasattr(results, '__dict__') else results,
            'token_usage': llm_response.usage,
            'model': llm_response.model
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        # Save raw prompt and response for debugging
        prompt_file = output_dir / f"{base_name}_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)
        
        response_file = output_dir / f"{base_name}_response.txt"
        with open(response_file, 'w') as f:
            f.write(llm_response.content)
    
    def _summarize_token_usage(self) -> Dict[str, Any]:
        """Summarize token usage across all analyses."""
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost_estimate = 0.0
        
        for analysis_type, usage_data in self.token_usage.items():
            if 'actual' in usage_data and usage_data['actual']:
                actual = usage_data['actual']
                total_input_tokens += actual.get('prompt_tokens', 0)
                total_output_tokens += actual.get('completion_tokens', 0)
            
            if 'estimated' in usage_data:
                estimated = usage_data['estimated']
                total_cost_estimate += estimated.get('estimated_cost_usd', 0)
        
        return {
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_input_tokens + total_output_tokens,
            'estimated_total_cost_usd': round(total_cost_estimate, 4),
            'analyses_completed': len(self.token_usage)
        }