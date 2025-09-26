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
        config_overrides: Optional[Dict[str, Any]] = None,
        sampling_seed: Optional[int] = None
    ):
        """Initialize LLM document analyzer.
        
        Args:
            provider_name: LLM provider to use ("azure")
            config_overrides: Optional provider configuration overrides
            sampling_seed: Optional seed for reproducible page sampling
        """
        self.provider_name = provider_name
        self.config_overrides = config_overrides or {}
        self.sampling_seed = sampling_seed
        
        # Initialize components
        self.provider: LLMProvider = get_llm_provider(provider_name, **self.config_overrides)
        self.sampler = PageSampler(seed=sampling_seed)
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
        
        # Sample pages for analysis using config parameters
        sampling_result = self.sampler.sample_for_header_footer_analysis(
            total_pages,
            num_groups=self.config.llm_sampling_groups,
            sequence_length=self.config.llm_sequence_length,
            num_individuals=self.config.llm_sampling_individuals
        )
        if not sampling_result:
            raise AnalysisError(
                f"Document too short ({total_pages} pages) for header/footer analysis. "
                "Minimum 20 pages required."
            )
        
        # Extract streamlined page data
        output_dir_path = Path(output_dir or self.config.output_dir) if save_results else None
        page_data_for_llm = self.sampler.extract_page_data(
            pages_data,
            sampling_result,
            save_debug_data=save_results,
            output_dir=output_dir_path
        )
        
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
        
        # Save prompt immediately (before LLM call) if saving is enabled
        base_name = None
        output_dir_path = None
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"llm_headers_footers_{timestamp}"
            output_dir_path = Path(output_dir or self.config.output_dir)
            output_dir_path.mkdir(parents=True, exist_ok=True)
            
            prompt_file = output_dir_path / f"{base_name}_prompt.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
        
        # Send request to LLM
        try:
            llm_response = self.provider.analyze_document_structure(prompt)
            
            # Save response immediately (after LLM call, before parsing)
            if save_results:
                response_file = output_dir_path / f"{base_name}_response.txt"
                with open(response_file, 'w') as f:
                    f.write(llm_response.content)
            
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
            
            # Save structured results if requested
            if save_results:
                self._save_structured_results_only(
                    analysis_type='headers_footers',
                    results=analysis_result,
                    base_name=base_name,
                    output_dir_path=output_dir_path,
                    sampling_info=sampling_result,
                    llm_response=llm_response
                )
            
            return analysis_result
            
        except Exception as e:
            raise AnalysisError(f"Header/footer analysis failed: {e}")
    
    def analyze_headers_footers_incremental(
        self,
        document_data: List[Dict[str, Any]],
        save_results: bool = True,
        output_dir: Optional[Path] = None
    ) -> HeaderFooterAnalysisResult:
        """Analyze headers/footers using incremental batch processing.
        
        This method processes large documents in smaller batches to avoid timeouts
        and build context progressively.
        """
        if not self.config.llm_incremental_processing:
            # Fall back to single-batch processing
            return self.analyze_headers_footers(document_data, save_results, output_dir)
        
        total_pages = len(document_data)
        
        # Check if document is large enough for incremental processing
        if total_pages < self.config.llm_min_document_size_for_incremental:
            return self.analyze_headers_footers(document_data, save_results, output_dir)
        
        print(f"🔄 Starting incremental analysis for {total_pages}-page document")
        
        # Phase 1: Initial context-building batch
        initial_result = self._analyze_initial_batch(document_data, save_results, output_dir)
        
        # Phase 2: Incremental processing with context
        all_results = [initial_result]
        context_summary = self._summarize_analysis_context(initial_result)
        
        # Process remaining pages in increments
        processed_pages = self.config.llm_initial_batch_size
        batch_number = 2
        
        while processed_pages < total_pages:
            batch_size = min(self.config.llm_increment_batch_size, total_pages - processed_pages)
            
            print(f"🔄 Processing batch {batch_number}: pages {processed_pages+1}-{processed_pages+batch_size}")
            
            batch_result = self._analyze_incremental_batch(
                document_data, processed_pages, batch_size, 
                context_summary, batch_number, save_results, output_dir
            )
            
            all_results.append(batch_result)
            context_summary = self._update_context_summary(context_summary, batch_result)
            
            processed_pages += batch_size
            batch_number += 1
        
        # Phase 3: Merge all results
        merged_result = self._merge_incremental_results(all_results, save_results, output_dir)
        
        print(f"✅ Incremental analysis complete: {len(all_results)} batches processed")
        return merged_result
    
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
            sampling_result = self.sampler.sample_for_header_footer_analysis(
                total_pages,
                num_groups=self.config.llm_sampling_groups,
                sequence_length=self.config.llm_sequence_length,
                num_individuals=self.config.llm_sampling_individuals
            )
            if not sampling_result:
                return {"error": f"Document too short ({total_pages} pages)"}
            
            page_data_for_llm = self.sampler.extract_page_data(pages_data, sampling_result, save_debug_data=False)
            
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
                'sampling_individuals': self.config.llm_sampling_individuals,
                'sequence_length': self.config.llm_sequence_length
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
    
    def _save_structured_results_only(
        self,
        analysis_type: str,
        results: Any,
        base_name: str,
        output_dir_path: Path,
        sampling_info: SamplingResult,
        llm_response: LLMResponse
    ) -> None:
        """Save only the structured results JSON (prompt/response already saved)."""
        results_file = output_dir_path / f"{base_name}_results.json"
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
    
    def _analyze_initial_batch(
        self,
        document_data: List[Dict[str, Any]],
        save_results: bool,
        output_dir: Optional[Path]
    ) -> HeaderFooterAnalysisResult:
        """Analyze initial batch to build context."""
        # Use first N pages for initial context
        initial_pages = document_data[:self.config.llm_initial_batch_size]
        print(f"🔍 Initial context batch: analyzing first {len(initial_pages)} pages")
        
        return self.analyze_headers_footers(initial_pages, save_results, output_dir)
    
    def _analyze_incremental_batch(
        self,
        document_data: List[Dict[str, Any]],
        start_page: int,
        batch_size: int,
        context_summary: Dict[str, Any],
        batch_number: int,
        save_results: bool,
        output_dir: Optional[Path]
    ) -> HeaderFooterAnalysisResult:
        """Analyze incremental batch with existing context."""
        # Extract batch data
        end_page = min(start_page + batch_size, len(document_data))
        batch_data = document_data[start_page:end_page]
        
        print(f"🔍 Batch {batch_number}: analyzing pages {start_page+1}-{end_page} with context")
        
        # Use contextual analysis (to be implemented)
        return self._analyze_with_context(batch_data, context_summary, batch_number, save_results, output_dir)
    
    def _analyze_with_context(
        self,
        batch_data: List[Dict[str, Any]],
        context_summary: Dict[str, Any],
        batch_number: int,
        save_results: bool,
        output_dir: Optional[Path]
    ) -> HeaderFooterAnalysisResult:
        """Analyze batch with existing context knowledge."""
        # For now, use regular analysis - will enhance with contextual prompts later
        return self.analyze_headers_footers(batch_data, save_results, output_dir)
    
    def _summarize_analysis_context(self, result: HeaderFooterAnalysisResult) -> Dict[str, Any]:
        """Create context summary from analysis result."""
        return {
            'header_pattern': {
                'detected': len(result.get_pages_with_headers()) > 0,
                'typical_y': result.header_pattern.get('y_boundary_typical'),
                'confidence': result.header_pattern.get('confidence')
            },
            'footer_pattern': {
                'detected': len(result.get_pages_with_footers()) > 0,
                'typical_y': result.footer_pattern.get('y_boundary_typical'),
                'confidence': result.footer_pattern.get('confidence')
            },
            'content_boundaries': result.get_content_boundaries(),
            'document_elements': {
                'section_patterns': result.get_font_style_patterns(),
                'figure_patterns': [],  # Will be populated
                'table_patterns': []    # Will be populated
            },
            'page_numbering': result.page_numbering_analysis,
            'pages_analyzed': len(result.per_page_analysis)
        }
    
    def _update_context_summary(
        self, 
        context: Dict[str, Any], 
        new_result: HeaderFooterAnalysisResult
    ) -> Dict[str, Any]:
        """Update context with new batch results."""
        # Merge patterns and update confidence levels
        updated_context = context.copy()
        
        # Update page count
        updated_context['pages_analyzed'] += len(new_result.per_page_analysis)
        
        # Could add pattern refinement logic here
        return updated_context
    
    def _merge_incremental_results(
        self,
        all_results: List[HeaderFooterAnalysisResult],
        save_results: bool,
        output_dir: Optional[Path]
    ) -> HeaderFooterAnalysisResult:
        """Merge multiple batch results into single comprehensive result."""
        if len(all_results) == 1:
            return all_results[0]
        
        # For now, return the first result as the master
        # TODO: Implement sophisticated merging logic
        master_result = all_results[0]
        
        # Combine per_page_analysis from all batches
        all_page_analysis = []
        for result in all_results:
            all_page_analysis.extend(result.per_page_analysis)
        
        # Create merged result (simplified for now)
        merged_result = HeaderFooterAnalysisResult(
            sampling_summary=master_result.sampling_summary,
            per_page_analysis=all_page_analysis,
            header_pattern=master_result.header_pattern,
            footer_pattern=master_result.footer_pattern,
            page_numbering_analysis=master_result.page_numbering_analysis,
            content_area_boundaries=master_result.content_area_boundaries,
            insights=master_result.insights,
            content_positioning_analysis=master_result.content_positioning_analysis,
            document_element_analysis=master_result.document_element_analysis,
            raw_response=f"MERGED_FROM_{len(all_results)}_BATCHES"
        )
        
        if save_results:
            # Save merged results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"llm_headers_footers_incremental_{timestamp}"
            output_dir_path = Path(output_dir or self.config.output_dir)
            
            self._save_structured_results_only(
                analysis_type='headers_footers_incremental',
                results=merged_result,
                base_name=base_name,
                output_dir_path=output_dir_path,
                sampling_info=None,  # TODO: Create combined sampling info
                llm_response=None    # TODO: Handle merged response
            )
        
        return merged_result
    
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