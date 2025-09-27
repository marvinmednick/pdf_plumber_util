"""Page sampling strategies for LLM document analysis."""

import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


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
        sequence_length: int = 4,
        num_individuals: int = 4
    ) -> SamplingResult:
        """Sample pages for header/footer pattern analysis using improved overlap-free algorithm.
        
        Strategy: Select groups first using pre-computed sets to avoid overlap,
        then select individuals from remaining pages.
        
        For small documents (<= requested sample size), returns all pages in order.
        
        Args:
            total_pages: Total number of pages in document
            num_groups: Number of consecutive page groups (default: 3)
            sequence_length: Number of pages in each consecutive sequence (default: 4) 
            num_individuals: Number of individual pages (default: 4)
            
        Returns:
            SamplingResult with selected pages
        """
        requested_sample_size = num_groups * sequence_length + num_individuals
        
        # For small documents, return all pages in order
        if total_pages <= requested_sample_size:
            all_pages = list(range(1, total_pages + 1))
            return SamplingResult(
                groups=[],
                individuals=all_pages,
                selected_pages=all_pages,
                total_pages_selected=total_pages
            )
        
        # Initialize sets for overlap-free selection
        individual_pages = set(range(1, total_pages + 1))
        group_starts = set(range(1, total_pages - sequence_length + 2))  # Valid starting positions
        
        groups = []
        individuals = []
        
        # Phase 1: Select consecutive page groups
        for _ in range(num_groups):
            if not group_starts:
                break  # No more valid group positions
                
            # Pick random group start
            start_page = random.choice(list(group_starts))
            group_pages = list(range(start_page, start_page + sequence_length))
            groups.append(group_pages)
            
            # Remove overlapping group starts
            # Any group that would share pages with this group
            overlap_starts = set()
            for page in group_pages:
                # Remove starts that would include this page
                for potential_start in range(max(1, page - sequence_length + 1), 
                                           min(total_pages - sequence_length + 2, page + 1)):
                    overlap_starts.add(potential_start)
            
            group_starts -= overlap_starts
            
            # Remove used pages from individual set
            individual_pages -= set(group_pages)
        
        # Phase 2: Select individual pages from remaining pages
        available_individuals = list(individual_pages)
        num_individuals_to_select = min(num_individuals, len(available_individuals))
        
        if num_individuals_to_select > 0:
            individuals = sorted(random.sample(available_individuals, num_individuals_to_select))
        
        # Combine all selected pages
        all_selected = set()
        for group in groups:
            all_selected.update(group)
        all_selected.update(individuals)
        
        return SamplingResult(
            groups=groups,
            individuals=individuals,
            selected_pages=sorted(all_selected),
            total_pages_selected=len(all_selected)
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
        sampling_result: SamplingResult,
        save_debug_data: bool = True,
        output_dir: Optional[Path] = None
    ) -> List[Dict[str, Any]]:
        """Extract streamlined data for selected pages.

        Args:
            pages_data: Full document pages data
            sampling_result: Result from sampling operation
            save_debug_data: Whether to save LLM input data for troubleshooting
            output_dir: Directory to save debug data (uses 'output' if None)

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

        # Save debug data for troubleshooting
        if save_debug_data:
            self._save_llm_input_debug_data(page_data_for_llm, sampling_result, output_dir)

        return page_data_for_llm
    
    def _extract_streamlined_blocks(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract streamlined block data for LLM analysis.

        Creates an optimized format that reduces context usage while preserving
        essential information for document structure analysis. Uses text_lines
        array instead of concatenated text to improve LLM parsing accuracy.
        """
        streamlined_blocks = []

        # Handle different block data structures
        blocks = page_data.get('blocks', [])
        if not blocks:
            # Try to get from lines if blocks not available
            blocks = page_data.get('lines', [])

        for block in blocks:
            # Prefer text_lines array over concatenated text
            text_lines = block.get('text_lines', [])
            if not text_lines:
                # Fallback to old format for backward compatibility
                text = block.get('text', '').strip()
                if not text:
                    continue
                text_lines = [line.strip() for line in text.split('\n') if line.strip()]

            # Skip empty blocks
            if not text_lines:
                continue

            # Extract essential positioning (simplified)
            y_position = None
            x_position = None

            # Handle different bbox formats
            bbox = block.get('bbox', {})
            if isinstance(bbox, dict):
                y_position = bbox.get('top', bbox.get('y0', 0))
                x_position = bbox.get('x0', 0)
            elif isinstance(bbox, list) and len(bbox) >= 2:
                x_position = bbox[0]
                y_position = bbox[1]
            else:
                # Fallback to direct position attributes
                y_position = block.get('y0', block.get('top', 0))
                x_position = block.get('x0', 0)

            # Extract font information (critical for hierarchy)
            font_name = block.get('predominant_font', block.get('font_name', block.get('font', '')))
            font_size = block.get('predominant_size', block.get('font_size', block.get('size', 0)))

            # Create optimized block structure with line array
            streamlined_block = {
                'text_lines': text_lines,
                'y0': y_position,
                'x0': x_position,
                'font_name': font_name,
                'font_size': font_size
            }

            streamlined_blocks.append(streamlined_block)

        return streamlined_blocks

    def _save_llm_input_debug_data(
        self,
        page_data_for_llm: List[Dict[str, Any]],
        sampling_result: SamplingResult,
        output_dir: Optional[Path] = None
    ) -> None:
        """Save LLM input data for troubleshooting and analysis.

        Creates a JSON file containing the exact data structure sent to the LLM,
        which is useful for debugging extraction issues and optimizing prompts.

        Args:
            page_data_for_llm: Streamlined page data prepared for LLM
            sampling_result: Sampling information
            output_dir: Directory to save debug data
        """
        if output_dir is None:
            output_dir = Path("output")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create debug data structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_data = {
            'debug_info': {
                'timestamp': datetime.now().isoformat(),
                'purpose': 'LLM input data for troubleshooting',
                'format_version': 'optimized_v1',
                'optimization': 'reduced_context_with_font_preservation',
                'total_pages': len(page_data_for_llm),
                'total_blocks': sum(page['block_count'] for page in page_data_for_llm)
            },
            'sampling_info': {
                'selected_pages': sampling_result.selected_pages,
                'groups': sampling_result.groups,
                'individuals': sampling_result.individuals,
                'total_selected': sampling_result.total_pages_selected
            },
            'llm_input_data': page_data_for_llm
        }

        # Save debug file
        debug_file = output_dir / f"llm_input_debug_{timestamp}.json"
        with open(debug_file, 'w') as f:
            json.dump(debug_data, f, indent=2)

        print(f"🔧 Debug: LLM input data saved to {debug_file}")
        print(f"📊 Debug: {debug_data['debug_info']['total_pages']} pages, {debug_data['debug_info']['total_blocks']} blocks")

        # Also save a clean format for manual review
        self._save_optimized_format_for_review(page_data_for_llm, timestamp, output_dir)

    def _save_optimized_format_for_review(
        self,
        page_data_for_llm: List[Dict[str, Any]],
        timestamp: str,
        output_dir: Path
    ) -> None:
        """Save clean LLM optimized format for manual review and verification.

        Creates a human-readable file showing exactly what text the LLM sees,
        organized for easy manual TOC counting and accuracy verification.
        """
        review_file = output_dir / f"llm_optimized_format_{timestamp}.txt"

        with open(review_file, 'w') as f:
            f.write("LLM OPTIMIZED FORMAT - MANUAL REVIEW\n")
            f.write("="*50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Pages: {len(page_data_for_llm)}\n")
            f.write("="*50 + "\n\n")

            for page_data in page_data_for_llm:
                page_index = page_data['page_index']
                blocks = page_data['blocks']

                f.write(f"PAGE {page_index}\n")
                f.write("-" * 20 + "\n")

                toc_entries_on_page = 0

                for i, block in enumerate(blocks):
                    text_lines = block.get('text_lines', [])
                    y0 = block.get('y0', 0)
                    x0 = block.get('x0', 0)
                    font_size = block.get('font_size', 0)

                    f.write(f"\nBlock {i+1}: y={y0:.1f}, x={x0:.1f}, size={font_size}\n")

                    block_toc_count = 0
                    for line_num, line in enumerate(text_lines):
                        # Mark potential TOC entries
                        is_toc = '...' in line and line.strip().split()[-1].isdigit()
                        marker = " [TOC]" if is_toc else ""

                        f.write(f"  {line_num+1}. {line}{marker}\n")

                        if is_toc:
                            block_toc_count += 1
                            toc_entries_on_page += 1

                    if block_toc_count > 0:
                        f.write(f"     → {block_toc_count} TOC entries in this block\n")

                f.write(f"\nPAGE {page_index} SUMMARY: {toc_entries_on_page} TOC entries\n")
                f.write("="*50 + "\n\n")

            # Overall summary
            total_toc = sum(
                sum(1 for block in page['blocks']
                    for line in block.get('text_lines', [])
                    if '...' in line and line.strip().split()[-1].isdigit())
                for page in page_data_for_llm
            )

            f.write(f"OVERALL SUMMARY\n")
            f.write("-"*20 + "\n")
            f.write(f"Total TOC entries found: {total_toc}\n")
            f.write(f"Expected for manual verification\n")

        print(f"📋 Review: LLM optimized format saved to {review_file}")
        print(f"👀 Use this file to manually verify TOC entry accuracy")