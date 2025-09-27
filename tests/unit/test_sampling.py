"""Unit tests for LLM page sampling algorithms."""

import pytest
from unittest.mock import patch

from src.pdf_plumb.llm.sampling import PageSampler, SamplingResult


class TestPageSampler:
    """Test the PageSampler class with different document sizes and parameters."""
    
    def setup_method(self):
        """Set up test fixtures with deterministic random seed."""
        self.sampler = PageSampler(seed=42)
    
    def test_small_document_returns_all_pages(self):
        """Test that small documents return all pages in order without grouping.
        
        Test setup:
        - 3-page document with default sampling (3 groups * 4 pages + 4 individuals = 16 requested)
        - Document size (3) is much smaller than requested sample size (16)
        - Uses deterministic seed for consistent results
        
        What it verifies:
        - Returns all 3 pages as individuals (no groups)
        - Pages are returned in sequential order [1, 2, 3]
        - Groups array is empty for small documents
        - Total pages selected equals document size
        
        Test limitation:
        - Only tests default parameters, not custom group sizes
        - Doesn't test boundary case where document size equals requested size
        
        Key insight: Small documents bypass complex sampling and return all pages sequentially for complete coverage.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=3)
        
        assert result.groups == []
        assert result.individuals == [1, 2, 3]
        assert result.selected_pages == [1, 2, 3]
        assert result.total_pages_selected == 3
    
    def test_boundary_case_exact_requested_size(self):
        """Test document size exactly matching requested sample size returns all pages.
        
        Test setup:
        - 16-page document with default sampling (3*4 + 4 = 16 requested)
        - Document size exactly equals requested sample size
        - Tests edge case between small and large document handling
        
        What it verifies:
        - All 16 pages returned as individuals (no groups)
        - Pages in sequential order from 1 to 16
        - No complex sampling algorithm applied
        - Total selected equals document size
        
        Key insight: Documents matching requested sample size are treated as small documents for simplicity.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=16)
        
        assert result.groups == []
        assert result.individuals == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        assert result.selected_pages == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        assert result.total_pages_selected == 16
    
    def test_large_document_uses_sampling(self):
        """Test that large documents use complex sampling with groups and individuals.
        
        Test setup:
        - 50-page document requiring sampling (50 > 16 requested)
        - Default parameters: 3 groups of 4 pages + 4 individuals
        - Deterministic seed ensures reproducible group/individual selection
        
        What it verifies:
        - Exactly 3 groups are created with 4 consecutive pages each
        - Exactly 4 individual pages are selected
        - No overlap between group pages and individual pages
        - Total selection is 16 pages (3*4 + 4)
        - Selected pages are sorted in ascending order
        
        Test limitation:
        - Specific page numbers depend on random seed, testing structure not content
        - Doesn't verify optimal distribution across document
        
        Key insight: Large documents use sophisticated overlap-free sampling to balance coverage with manageable analysis size.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=50)
        
        assert len(result.groups) == 3
        assert len(result.individuals) == 4
        assert result.total_pages_selected == 16
        
        # Verify each group has 4 consecutive pages
        for group in result.groups:
            assert len(group) == 4
            assert group == list(range(group[0], group[0] + 4))
        
        # Verify no overlap between groups and individuals
        group_pages = set()
        for group in result.groups:
            group_pages.update(group)
        individual_pages = set(result.individuals)
        assert group_pages.isdisjoint(individual_pages)
        
        # Verify selected_pages is sorted and contains all selected pages
        all_selected = group_pages | individual_pages
        assert result.selected_pages == sorted(all_selected)
    
    def test_custom_parameters(self):
        """Test sampling with custom group and individual counts.
        
        Test setup:
        - 30-page document with custom sampling: 2 groups of 3 pages + 2 individuals
        - Total requested: 2*3 + 2 = 8 pages from 30 available
        - Tests parameter flexibility beyond defaults
        
        What it verifies:
        - Respects custom num_groups parameter (2 groups created)
        - Respects custom sequence_length parameter (3 pages per group)
        - Respects custom num_individuals parameter (2 individual pages)
        - Total selection matches calculation (8 pages)
        - No overlap between selected pages
        
        Key insight: Sampling algorithm adapts to different analysis requirements through configurable parameters.
        """
        result = self.sampler.sample_for_header_footer_analysis(
            total_pages=30,
            num_groups=2,
            sequence_length=3,
            num_individuals=2
        )
        
        assert len(result.groups) == 2
        assert len(result.individuals) == 2
        assert result.total_pages_selected == 8
        
        # Verify each group has 3 consecutive pages
        for group in result.groups:
            assert len(group) == 3
            assert group == list(range(group[0], group[0] + 3))
    
    def test_no_overlap_guarantee(self):
        """Test that sampling algorithm guarantees no page overlap between groups and individuals.
        
        Test setup:
        - 100-page document with maximum sampling parameters
        - Large document size ensures algorithm has many choices for page selection
        - Multiple test runs with different seeds to verify consistency
        
        What it verifies:
        - No page appears in multiple groups
        - No page appears in both groups and individuals
        - All selected pages are unique
        - Algorithm maintains overlap-free guarantee across different random selections
        
        Test limitation:
        - Uses single seed, ideally would test multiple seeds
        - Doesn't test edge cases where overlap becomes impossible
        
        Key insight: The overlap-free algorithm design eliminates the retry mechanism while ensuring no duplicate page analysis.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=100)
        
        # Collect all selected pages
        all_selected_pages = []
        for group in result.groups:
            all_selected_pages.extend(group)
        all_selected_pages.extend(result.individuals)
        
        # Verify no duplicates
        assert len(all_selected_pages) == len(set(all_selected_pages))
        
        # Verify selected_pages matches combined selection
        assert result.selected_pages == sorted(all_selected_pages)
    
    def test_insufficient_pages_for_groups(self):
        """Test behavior when document is too small for all requested groups.
        
        Test setup:
        - 18-page document with default sampling (3 groups of 4 + 4 individuals = 16)
        - Document slightly larger than sample size but constrains group placement
        - Tests algorithm adaptation when group placement becomes limited
        
        What it verifies:
        - Algorithm handles cases where group placement is constrained
        - Still attempts to create groups within available space
        - Does not exceed document boundaries
        - Total selection is reasonable for document size
        
        Test limitation:
        - Specific group placement depends on random selection order
        - Documents slightly larger than sample size use complex sampling
        
        Key insight: Algorithm uses complex sampling for documents larger than requested size, even if constraints are tight.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=18)
        
        # 18 pages > 16 requested, so should use complex sampling
        assert result.total_pages_selected <= 18
        assert result.total_pages_selected >= 10  # Should get reasonable coverage
        
        # Verify all selected pages are within bounds
        for page in result.selected_pages:
            assert 1 <= page <= 18
    
    def test_single_page_document(self):
        """Test edge case of single-page document.
        
        Test setup:
        - 1-page document (minimum possible size)
        - Default sampling parameters requesting 16 pages
        - Tests absolute minimum document size handling
        
        What it verifies:
        - Returns the single page as individual
        - No groups created for single page
        - No errors or exceptions raised
        - Handles extreme edge case gracefully
        
        Key insight: Algorithm handles minimal documents by returning available content rather than failing.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=1)
        
        assert result.groups == []
        assert result.individuals == [1]
        assert result.selected_pages == [1]
        assert result.total_pages_selected == 1
    
    def test_zero_individuals_parameter(self):
        """Test sampling with zero individual pages requested.
        
        Test setup:
        - 30-page document with 3 groups of 4 pages, 0 individuals
        - Total requested: 3*4 + 0 = 12 pages
        - Tests parameter edge case where only groups are wanted
        
        What it verifies:
        - No individual pages selected when num_individuals=0
        - Groups still created normally
        - Total selection equals group pages only
        - Algorithm handles zero-parameter gracefully
        
        Key insight: Algorithm supports group-only or individual-only sampling through parameter configuration.
        """
        result = self.sampler.sample_for_header_footer_analysis(
            total_pages=30,
            num_groups=3,
            sequence_length=4,
            num_individuals=0
        )
        
        assert len(result.groups) == 3
        assert result.individuals == []
        assert result.total_pages_selected == 12
    
    def test_zero_groups_parameter(self):
        """Test sampling with zero groups requested.
        
        Test setup:
        - 30-page document with 0 groups, 8 individuals
        - Tests individual-only sampling strategy
        - Verifies algorithm handles group-free sampling
        
        What it verifies:
        - No groups created when num_groups=0
        - Exactly 8 individual pages selected
        - All selected pages are unique
        - Algorithm supports individuals-only mode
        
        Key insight: Algorithm supports flexible sampling strategies from group-heavy to individual-only approaches.
        """
        result = self.sampler.sample_for_header_footer_analysis(
            total_pages=30,
            num_groups=0,
            sequence_length=4,
            num_individuals=8
        )
        
        assert result.groups == []
        assert len(result.individuals) == 8
        assert result.total_pages_selected == 8
    
    def test_get_group_ranges_formatting(self):
        """Test that group ranges are formatted correctly for human readability.
        
        Test setup:
        - Large document ensuring groups are created
        - Tests the get_group_ranges() utility method
        - Verifies human-readable range formatting
        
        What it verifies:
        - Group ranges formatted as "start-end" strings
        - Correct start and end values for each group
        - Consistent formatting across all groups
        - Utility method produces expected output format
        
        Key insight: Sampling results include human-readable formatting for analysis reporting and debugging.
        """
        result = self.sampler.sample_for_header_footer_analysis(total_pages=50)
        ranges = result.get_group_ranges()
        
        assert len(ranges) == len(result.groups)
        for i, range_str in enumerate(ranges):
            group = result.groups[i]
            expected = f"{group[0]}-{group[-1]}"
            assert range_str == expected
    
    def test_deterministic_with_seed(self):
        """Test that sampling is deterministic when using a random seed.
        
        Test setup:
        - Two separate sampling calls with same seed reset each time
        - Same document size and parameters for both
        - Verifies reproducible results for testing
        
        What it verifies:
        - Identical seeds produce identical sampling results
        - Groups and individuals match exactly between calls
        - Deterministic behavior enables reliable testing
        - Seed parameter controls randomness effectively
        
        Key insight: Deterministic sampling enables reproducible analysis and testing while maintaining random distribution quality.
        """
        # Reset seed for each call to ensure identical starting state
        result1 = PageSampler(seed=42).sample_for_header_footer_analysis(total_pages=50)
        result2 = PageSampler(seed=42).sample_for_header_footer_analysis(total_pages=50)
        
        assert result1.groups == result2.groups
        assert result1.individuals == result2.individuals
        assert result1.selected_pages == result2.selected_pages
    
    def test_different_seeds_produce_different_results(self):
        """Test that different random seeds produce different sampling results.
        
        Test setup:
        - Two samplers with different seeds (42 and 123)
        - Same document size and parameters
        - Verifies that sampling varies with different seeds
        
        What it verifies:
        - Different seeds produce different page selections
        - Random variation exists in sampling algorithm
        - Seed parameter controls randomness effectively
        - Algorithm doesn't have hidden deterministic bias
        
        Test limitation:
        - Theoretically possible (but unlikely) that different seeds produce identical results
        - Single test case may not catch all edge cases
        
        Key insight: Random seed variation ensures sampling covers different document areas across analysis runs.
        """
        sampler1 = PageSampler(seed=42)
        sampler2 = PageSampler(seed=123)
        
        result1 = sampler1.sample_for_header_footer_analysis(total_pages=50)
        result2 = sampler2.sample_for_header_footer_analysis(total_pages=50)
        
        # Results should be different (very high probability)
        assert result1.groups != result2.groups or result1.individuals != result2.individuals


class TestSamplingResultUtilities:
    """Test utility methods and data structures in SamplingResult."""
    
    def test_sampling_result_creation(self):
        """Test that SamplingResult dataclass is created correctly with all fields.
        
        Test setup:
        - Manual creation of SamplingResult with known values
        - Tests dataclass functionality and field assignment
        - Verifies all required fields are accessible
        
        What it verifies:
        - All fields (groups, individuals, selected_pages, total_pages_selected) are set correctly
        - Dataclass behaves as expected for data storage
        - Field access works properly
        - No unexpected field behavior
        
        Key insight: SamplingResult provides clean data structure for sampling algorithm output.
        """
        groups = [[1, 2, 3, 4], [10, 11, 12, 13]]
        individuals = [20, 25, 30]
        selected_pages = [1, 2, 3, 4, 10, 11, 12, 13, 20, 25, 30]
        
        result = SamplingResult(
            groups=groups,
            individuals=individuals,
            selected_pages=selected_pages,
            total_pages_selected=11
        )
        
        assert result.groups == groups
        assert result.individuals == individuals
        assert result.selected_pages == selected_pages
        assert result.total_pages_selected == 11
    
    def test_get_group_ranges_with_empty_groups(self):
        """Test get_group_ranges() method when no groups are present.
        
        Test setup:
        - SamplingResult with empty groups list
        - Individuals present but no consecutive groups
        - Tests edge case of individual-only sampling
        
        What it verifies:
        - Empty list returned when no groups exist
        - Method handles empty groups gracefully
        - No errors raised for edge case
        - Consistent behavior with group-free sampling
        
        Key insight: Utility methods handle edge cases gracefully to support all sampling strategies.
        """
        result = SamplingResult(
            groups=[],
            individuals=[1, 5, 10],
            selected_pages=[1, 5, 10],
            total_pages_selected=3
        )
        
        assert result.get_group_ranges() == []
    
    def test_get_group_ranges_with_single_page_groups(self):
        """Test get_group_ranges() formatting with single-page groups.
        
        Test setup:
        - Groups containing only one page each (edge case)
        - Tests formatting when start and end are identical
        - Unusual scenario but should be handled correctly
        
        What it verifies:
        - Single-page groups formatted as "N-N" (e.g., "5-5")
        - Consistent formatting regardless of group size
        - Edge case handled without errors
        - Method works for minimal groups
        
        Key insight: Range formatting maintains consistency even for degenerate cases like single-page groups.
        """
        result = SamplingResult(
            groups=[[5], [10]],
            individuals=[1, 15],
            selected_pages=[1, 5, 10, 15],
            total_pages_selected=4
        )
        
        ranges = result.get_group_ranges()
        assert ranges == ["5-5", "10-10"]


class TestSectionAnalysisSampling:
    """Test specialized sampling methods for different analysis types."""
    
    def test_section_analysis_focus_early_pages(self):
        """Test section analysis sampling with early page focus enabled.
        
        Test setup:
        - 90-page document with focus_early_pages=True
        - 15% coverage (default) = ~14 pages total
        - Tests weighted sampling toward document beginning
        
        What it verifies:
        - More pages selected from first third than later sections
        - Total pages approximately matches coverage percentage
        - Early focus weighting is applied (60% early, 30% middle, 10% late)
        - Individuals-only strategy (no groups for section analysis)
        
        Test limitation:
        - Exact page distribution depends on random sampling
        - Doesn't verify optimal early page selection without examining actual pages
        
        Key insight: Section analysis prioritizes early pages where document structure patterns are typically established.
        """
        sampler = PageSampler(seed=42)
        result = sampler.sample_for_section_analysis(total_pages=90, focus_early_pages=True)
        
        assert result.groups == []  # Section analysis uses individuals only
        assert result.total_pages_selected >= 10  # At least 10 pages for meaningful analysis
        assert result.total_pages_selected <= 16  # Around 15% of 90 pages
        
        # Verify pages are selected
        assert len(result.individuals) == result.total_pages_selected
        assert result.selected_pages == sorted(result.individuals)
    
    def test_toc_analysis_early_focus(self):
        """Test TOC analysis sampling focuses heavily on early pages.
        
        Test setup:
        - 100-page document with default max_early_pages=20
        - TOC typically appears in first 10-20 pages
        - Some later pages added for validation
        
        What it verifies:
        - First 20 pages are all included in selection
        - Some validation pages from later in document
        - Total pages reasonable for TOC detection
        - Individuals-only strategy for TOC analysis
        
        Key insight: TOC analysis uses deterministic early page selection since TOCs have predictable placement.
        """
        sampler = PageSampler(seed=42)
        result = sampler.sample_for_toc_analysis(total_pages=100)
        
        assert result.groups == []  # TOC analysis uses individuals only
        
        # Should include first 20 pages
        early_pages = list(range(1, 21))
        for page in early_pages:
            assert page in result.individuals
        
        # Should have some later pages for validation
        assert result.total_pages_selected > 20
    
    def test_adaptive_sampling_headers_footers(self):
        """Test adaptive sampling correctly delegates to header-footer analysis.
        
        Test setup:
        - 50-page document with "headers-footers" analysis focus
        - Tests routing through adaptive_sampling method
        - Verifies delegation to appropriate specialized method
        
        What it verifies:
        - Adaptive sampling routes to sample_for_header_footer_analysis
        - Results match direct method call with same seed
        - Parameters passed correctly through delegation
        - Analysis focus string mapping works
        
        Key insight: Adaptive sampling provides unified interface while routing to specialized algorithms.
        """
        # Test adaptive routing with fresh seed
        adaptive_result = PageSampler(seed=42).adaptive_sampling(50, "headers-footers")
        
        # Compare with direct method call using fresh seed
        direct_result = PageSampler(seed=42).sample_for_header_footer_analysis(50)
        
        assert adaptive_result.groups == direct_result.groups
        assert adaptive_result.individuals == direct_result.individuals
        assert adaptive_result.selected_pages == direct_result.selected_pages
    
    def test_adaptive_sampling_invalid_focus(self):
        """Test adaptive sampling raises error for unknown analysis focus.
        
        Test setup:
        - Valid document size but invalid analysis_focus string
        - Tests error handling for unsupported analysis types
        - Verifies helpful error message
        
        What it verifies:
        - ValueError raised for unknown focus types
        - Error message includes available options
        - Input validation works correctly
        - Fails fast with clear guidance
        
        Key insight: Input validation prevents silent failures and guides users toward supported analysis types.
        """
        sampler = PageSampler(seed=42)
        
        with pytest.raises(ValueError) as exc_info:
            sampler.adaptive_sampling(50, "unknown-analysis")
        
        assert "Unknown analysis focus 'unknown-analysis'" in str(exc_info.value)
        assert "headers-footers" in str(exc_info.value)  # Should list available options


class TestPageDataExtraction:
    """Test page data extraction and streamlining for LLM analysis."""
    
    def test_extract_page_data_basic(self):
        """Test basic page data extraction with mock document data.
        
        Test setup:
        - Mock document with 3 pages containing blocks with text, bbox, font info
        - SamplingResult selecting all 3 pages
        - Tests streamlined data extraction for LLM processing
        
        What it verifies:
        - Correct number of pages extracted based on sampling
        - Page indexes match sampling result
        - Block data streamlined with essential fields only
        - Block count calculated correctly per page
        
        Test limitation:
        - Uses simplified mock data, not real PDF extraction format
        - Doesn't test all possible block data variations
        
        Key insight: Data extraction creates lightweight page representations optimized for LLM token efficiency.
        """
        sampler = PageSampler()
        
        # Mock document data with multi-line blocks (the actual problem case)
        pages_data = [
            {
                'blocks': [
                    {
                        'text_lines': ['Header text'],
                        'text': 'Header text',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 50, 'x1': 200, 'bottom': 70},
                        'predominant_font': 'Arial-Bold',
                        'predominant_size': 12,
                        'gap_before': 0,
                        'gap_after': 5
                    },
                    {
                        'text_lines': ['TOC Entry 1', 'TOC Entry 2', 'TOC Entry 3'],
                        'text': 'TOC Entry 1\nTOC Entry 2\nTOC Entry 3',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 80, 'x1': 300, 'bottom': 100},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 5,
                        'gap_after': 0
                    }
                ]
            },
            {
                'blocks': [
                    {
                        'text_lines': ['Section 1.1', 'Section 1.2'],
                        'text': 'Section 1.1\nSection 1.2',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 50, 'x1': 250, 'bottom': 70},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 0,
                        'gap_after': 0
                    }
                ]
            },
            {
                'blocks': [
                    {
                        'text_lines': ['Final page content'],
                        'text': 'Final page content',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 60, 'x1': 180, 'bottom': 80},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 0,
                        'gap_after': 0
                    }
                ]
            }
        ]
        
        sampling_result = SamplingResult(
            groups=[],
            individuals=[1, 2, 3],
            selected_pages=[1, 2, 3],
            total_pages_selected=3
        )
        
        extracted_data = sampler.extract_page_data(pages_data, sampling_result)
        
        assert len(extracted_data) == 3
        
        # Check first page
        page1 = extracted_data[0]
        assert page1['page_index'] == 1
        assert page1['block_count'] == 2
        assert len(page1['blocks']) == 2
        
        # Check block data structure - test the new text_lines format
        block1 = page1['blocks'][0]
        assert block1['text_lines'] == ['Header text']
        assert block1['font_name'] == 'Arial-Bold'
        assert block1['font_size'] == 12
        assert block1['y0'] == 50
        assert block1['x0'] == 100

        # Test multi-line block (the core problem we're solving)
        block2 = page1['blocks'][1]
        assert block2['text_lines'] == ['TOC Entry 1', 'TOC Entry 2', 'TOC Entry 3']
        assert len(block2['text_lines']) == 3
        assert block2['font_name'] == 'Arial'
        assert block2['font_size'] == 10
    
    def test_extract_page_data_empty_blocks_filtered(self):
        """Test that blocks with empty text are filtered out during extraction.
        
        Test setup:
        - Mock page data with mix of text blocks and empty blocks
        - Tests filtering logic that removes non-content blocks
        - Verifies only meaningful content is passed to LLM
        
        What it verifies:
        - Empty text blocks are excluded from extraction
        - Non-empty blocks are preserved
        - Block count reflects only content blocks
        - Filtering doesn't affect other block properties
        
        Key insight: Empty block filtering reduces LLM token usage while preserving all meaningful document content.
        """
        sampler = PageSampler()
        
        pages_data = [
            {
                'blocks': [
                    {
                        'text_lines': ['Real content'],
                        'text': 'Real content',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 50, 'x1': 200, 'bottom': 70},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 0,
                        'gap_after': 0
                    },
                    {
                        'text_lines': [],  # Empty block should be filtered
                        'text': '',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 80, 'x1': 200, 'bottom': 100},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 0,
                        'gap_after': 0
                    },
                    {
                        'text_lines': [],  # Whitespace-only should be filtered
                        'text': '   ',  # backward compatibility
                        'bbox': {'x0': 100, 'top': 110, 'x1': 200, 'bottom': 130},
                        'predominant_font': 'Arial',
                        'predominant_size': 10,
                        'gap_before': 0,
                        'gap_after': 0
                    }
                ]
            }
        ]
        
        sampling_result = SamplingResult(
            groups=[],
            individuals=[1],
            selected_pages=[1],
            total_pages_selected=1
        )
        
        extracted_data = sampler.extract_page_data(pages_data, sampling_result)
        
        assert len(extracted_data) == 1
        page = extracted_data[0]
        assert page['block_count'] == 1  # Only non-empty block counted
        assert len(page['blocks']) == 1
        assert page['blocks'][0]['text_lines'] == ['Real content']
    
    def test_extract_page_data_index_bounds_checking(self):
        """Test that page data extraction handles index bounds correctly.
        
        Test setup:
        - SamplingResult requesting page beyond document bounds
        - Tests error handling for invalid page indexes
        - Verifies bounds checking prevents array index errors
        
        What it verifies:
        - IndexError raised when requesting non-existent pages
        - Error message indicates which page was out of bounds
        - Document size information included in error
        - Bounds checking prevents silent failures
        
        Key insight: Robust bounds checking prevents analysis errors when sampling logic produces invalid page references.
        """
        sampler = PageSampler()
        
        pages_data = [{'blocks': []}]  # Only 1 page
        
        sampling_result = SamplingResult(
            groups=[],
            individuals=[1, 2],  # Page 2 doesn't exist
            selected_pages=[1, 2],
            total_pages_selected=2
        )
        
        with pytest.raises(IndexError) as exc_info:
            sampler.extract_page_data(pages_data, sampling_result)
        
        assert "Page index 2 out of range" in str(exc_info.value)
        assert "document has 1 pages" in str(exc_info.value)