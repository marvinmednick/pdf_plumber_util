"""Page sampling strategies for LLM document analysis."""

import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SamplingResult:
    """Result of page sampling operation."""
    groups: List[List[int]]  # Groups of consecutive pages
    individuals: List[int]   # Individual pages
    selected_pages: List[int]  # All selected pages sorted
    total_pages_selected: int
    
    def get_group_ranges(self) -> List[str]:
        """Get human-readable group ranges."""
        return [f"{group[0]}-{group[-1]}" for group in self.groups]


class PageSampler:
    """Strategic page sampling for LLM document analysis."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize page sampler.
        
        Args:
            seed: Optional random seed for reproducible sampling
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def sample_for_header_footer_analysis(
        self,
        total_pages: int,
        num_groups: int = 3,
        group_size: int = 4,
        num_individuals: int = 4,
        min_pages_required: int = 20
    ) -> Optional[SamplingResult]:
        """Sample pages for header/footer pattern analysis.
        
        Strategy: 3 groups of 4 consecutive pages + 4 individual pages
        This provides good coverage while maintaining pattern recognition
        through consecutive page analysis.
        
        Args:
            total_pages: Total number of pages in document
            num_groups: Number of consecutive page groups (default: 3)
            group_size: Size of each group (default: 4) 
            num_individuals: Number of individual pages (default: 4)
            min_pages_required: Minimum pages needed for this strategy
            
        Returns:
            SamplingResult or None if document too short
        """
        if total_pages < min_pages_required:
            return None
        
        selected_pages = set()
        groups = []
        individuals = []
        
        # Select consecutive page groups
        max_attempts = 100
        for group_num in range(num_groups):
            for attempt in range(max_attempts):
                # Ensure we can fit group_size consecutive pages
                max_start = total_pages - group_size + 1
                if max_start <= 0:
                    break
                    
                start_page = random.randint(1, max_start)
                group_pages = list(range(start_page, start_page + group_size))
                
                # Check for overlap with existing selections
                if not any(p in selected_pages for p in group_pages):
                    groups.append(group_pages)
                    selected_pages.update(group_pages)
                    break
            else:
                # If we couldn't find non-overlapping groups after max attempts
                raise RuntimeError(
                    f"Could not find non-overlapping page groups after {max_attempts} attempts. "
                    f"Document may be too short ({total_pages} pages) for {num_groups} groups "
                    f"of {group_size} pages each."
                )
        
        # Select individual pages from remaining pages
        available_pages = [p for p in range(1, total_pages + 1) if p not in selected_pages]
        if len(available_pages) < num_individuals:
            raise RuntimeError(
                f"Not enough pages available for individual selection. "
                f"Need {num_individuals} individual pages, but only {len(available_pages)} "
                f"pages remain after group selection."
            )
        
        individuals = sorted(random.sample(available_pages, num_individuals))
        selected_pages.update(individuals)
        
        return SamplingResult(
            groups=groups,
            individuals=individuals,
            selected_pages=sorted(selected_pages),
            total_pages_selected=len(selected_pages)
        )
    
    def sample_for_section_analysis(
        self,
        total_pages: int,
        focus_early_pages: bool = True,
        coverage_percentage: float = 0.15
    ) -> SamplingResult:
        """Sample pages optimized for section hierarchy analysis.
        
        Strategy: Focus on early pages where section patterns are established,
        with some mid/late document sampling for validation.
        
        Args:
            total_pages: Total number of pages in document
            focus_early_pages: Weight sampling toward document beginning
            coverage_percentage: Target percentage of document to sample
            
        Returns:
            SamplingResult with section-optimized sampling
        """
        target_pages = max(10, int(total_pages * coverage_percentage))
        
        if focus_early_pages:
            # 60% from first third, 30% from middle third, 10% from last third
            first_third = total_pages // 3
            middle_third = total_pages * 2 // 3
            
            early_pages = int(target_pages * 0.6)
            middle_pages = int(target_pages * 0.3)
            late_pages = target_pages - early_pages - middle_pages
            
            # Sample from each section
            early_range = list(range(1, first_third + 1))
            middle_range = list(range(first_third + 1, middle_third + 1))
            late_range = list(range(middle_third + 1, total_pages + 1))
            
            selected_pages = []
            if early_pages > 0 and early_range:
                selected_pages.extend(random.sample(early_range, min(early_pages, len(early_range))))
            if middle_pages > 0 and middle_range:
                selected_pages.extend(random.sample(middle_range, min(middle_pages, len(middle_range))))
            if late_pages > 0 and late_range:
                selected_pages.extend(random.sample(late_range, min(late_pages, len(late_range))))
            
        else:
            # Uniform random sampling
            selected_pages = random.sample(range(1, total_pages + 1), target_pages)
        
        return SamplingResult(
            groups=[],  # Section analysis uses individual pages
            individuals=sorted(selected_pages),
            selected_pages=sorted(selected_pages),
            total_pages_selected=len(selected_pages)
        )
    
    def sample_for_toc_analysis(
        self,
        total_pages: int,
        max_early_pages: int = 20
    ) -> SamplingResult:
        """Sample pages optimized for Table of Contents detection.
        
        Strategy: Focus heavily on early pages where TOC typically appears,
        with some later pages for validation.
        
        Args:
            total_pages: Total number of pages in document
            max_early_pages: Maximum number of early pages to check
            
        Returns:
            SamplingResult optimized for TOC detection
        """
        # TOC usually appears in first 10-20 pages
        early_pages_to_check = min(max_early_pages, total_pages)
        early_pages = list(range(1, early_pages_to_check + 1))
        
        # Add some later pages for cross-validation (10% of remaining pages)
        if total_pages > max_early_pages:
            remaining_pages = list(range(max_early_pages + 1, total_pages + 1))
            validation_count = max(1, len(remaining_pages) // 10)
            validation_pages = random.sample(remaining_pages, min(validation_count, len(remaining_pages)))
        else:
            validation_pages = []
        
        selected_pages = early_pages + validation_pages
        
        return SamplingResult(
            groups=[],  # TOC analysis uses individual pages
            individuals=sorted(selected_pages),
            selected_pages=sorted(selected_pages),
            total_pages_selected=len(selected_pages)
        )
    
    def adaptive_sampling(
        self,
        total_pages: int,
        analysis_focus: str,
        **kwargs
    ) -> SamplingResult:
        """Adaptive sampling based on analysis focus.
        
        Args:
            total_pages: Total number of pages in document
            analysis_focus: Type of analysis ("headers-footers", "sections", "toc")
            **kwargs: Additional parameters passed to specific sampling methods
            
        Returns:
            SamplingResult optimized for the analysis focus
        """
        sampling_strategies = {
            "headers-footers": self.sample_for_header_footer_analysis,
            "sections": self.sample_for_section_analysis,
            "toc": self.sample_for_toc_analysis
        }
        
        if analysis_focus not in sampling_strategies:
            available = ", ".join(sampling_strategies.keys())
            raise ValueError(f"Unknown analysis focus '{analysis_focus}'. Available: {available}")
        
        strategy = sampling_strategies[analysis_focus]
        return strategy(total_pages, **kwargs)
    
    def extract_page_data(
        self,
        pages_data: List[Dict[str, Any]],
        sampling_result: SamplingResult
    ) -> List[Dict[str, Any]]:
        """Extract streamlined data for selected pages.
        
        Args:
            pages_data: Full document pages data
            sampling_result: Result from sampling operation
            
        Returns:
            List of streamlined page data for LLM analysis
        """
        page_data_for_llm = []
        
        for page_idx in sampling_result.selected_pages:
            # Convert to 0-based index for array access
            array_idx = page_idx - 1
            
            if array_idx >= len(pages_data):
                raise IndexError(f"Page index {page_idx} out of range (document has {len(pages_data)} pages)")
            
            page = pages_data[array_idx]
            
            # Extract streamlined block data
            streamlined_blocks = self._extract_streamlined_blocks(page)
            
            page_data_for_llm.append({
                'page_index': page_idx,
                'blocks': streamlined_blocks,
                'block_count': len(streamlined_blocks)
            })
        
        return page_data_for_llm
    
    def _extract_streamlined_blocks(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract streamlined block data for LLM analysis."""
        streamlined_blocks = []
        
        # Handle different block data structures
        blocks = page_data.get('blocks', [])
        if not blocks:
            # Try to get from lines if blocks not available
            blocks = page_data.get('lines', [])
        
        for block in blocks:
            # Extract bounding box with consistent format
            bbox = block.get('bbox', {})
            if isinstance(bbox, dict):
                bbox_formatted = {
                    'x0': bbox.get('x0', 0),
                    'top': bbox.get('top', 0),
                    'x1': bbox.get('x1', 0),
                    'bottom': bbox.get('bottom', 0)
                }
            else:
                # Handle list format [x0, top, x1, bottom]
                bbox_formatted = {
                    'x0': bbox[0] if len(bbox) > 0 else 0,
                    'top': bbox[1] if len(bbox) > 1 else 0,
                    'x1': bbox[2] if len(bbox) > 2 else 0,
                    'bottom': bbox[3] if len(bbox) > 3 else 0
                }
            
            streamlined_block = {
                'text': block.get('text', '').strip(),
                'bbox': bbox_formatted,
                'font': block.get('predominant_font', block.get('font', '')),
                'size': block.get('predominant_size', block.get('size', 0)),
                'gap_before': block.get('gap_before', 0),
                'gap_after': block.get('gap_after', 0)
            }
            
            # Only include blocks with actual text content
            if streamlined_block['text']:
                streamlined_blocks.append(streamlined_block)
        
        return streamlined_blocks