"""Unit tests for text segment spacing reconstruction.

Tests the _build_line_with_proportional_spacing method that fixes the issue
where PDF text segments are concatenated without proper spacing, causing
patterns like "9.3.4.6Byte" instead of "9.3.4.6 Byte".
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any

# Import the class we're testing
from pdf_plumb.core.extractor import PDFExtractor


class TestSpacingReconstruction:
    """Test spacing reconstruction algorithm with comprehensive edge cases."""

    @pytest.fixture
    def test_data(self) -> Dict[str, Any]:
        """Load test fixture data for spacing reconstruction tests."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "test_spacing_reconstruction.json"
        with open(fixture_path, 'r') as f:
            return json.load(f)

    @pytest.fixture
    def extractor(self) -> PDFExtractor:
        """Create PDFExtractor instance for testing."""
        return PDFExtractor()

    def test_h264_known_spacing_issue(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test the known H.264 spacing issue that started this investigation.

        This test validates that the real-world case from H.264 documentation
        where "9.3.4.6Byte stuffing process" should become "9.3.4.6 Byte stuffing process".
        The issue was caused by an empty segment between the section number and text.

        Test setup: Uses actual segment data from H.264 document extraction
        What it verifies: Proper spacing insertion and proportional text generation
        Test limitations: Uses specific coordinate values from real document
        Key insight: Empty segments should be ignored for text but used for gap calculation
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "h264_known_spacing_issue")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Verify normalized text has single space
        assert result["text"] == test_case["expected"]["text"]
        assert "9.3.4.6 Byte" in result["text"], "Should have space between section number and text"

        # Verify proportional text has multiple spaces
        assert result["text_proportional"] == test_case["expected"]["text_proportional"]
        assert "9.3.4.6    Byte" in result["text_proportional"], "Should have multiple spaces in proportional version"

        # Verify spacing metadata
        spacing_info = result["proportional_spacing_info"]
        assert len(spacing_info) == 1
        assert spacing_info[0]["normalized_text_index"] == 7  # Position after "9.3.4.6"
        assert spacing_info[0]["proportional_spaces"] == 4   # Should be ~4 spaces for 12.25pt gap

    def test_space_only_segment_single(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test segment containing single space character is treated as empty.

        This test validates our design decision to treat space-only segments
        the same as empty segments, using positional data for gap calculation.

        Test setup: Segment with single space character between two text segments
        What it verifies: Space-only segment ignored, gap calculated from positions
        Test limitations: Synthetic data may not reflect all real PDF extraction scenarios
        Key insight: Avoids double-counting of spaces (segment content + positional gap)
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "space_only_segment_single")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Verify space-only segment is treated as empty
        assert result["text"] == "Section Title"
        assert result["text_proportional"] == test_case["expected"]["text_proportional"]

        # Verify gap calculation uses positional data, not segment content
        spacing_info = result["proportional_spacing_info"]
        assert len(spacing_info) == 1
        assert spacing_info[0]["raw_gap_pt"] == 20.0  # 70 - 50 = 20pt gap

    def test_space_only_segment_multiple(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test segment with multiple space characters treated as empty.

        This test ensures consistency in space-only segment handling regardless
        of how many space characters the segment contains.

        Test setup: Segment with three space characters creating large visual gap
        What it verifies: Multiple spaces treated same as single space or empty
        Test limitations: May not capture all space character variations (tabs, non-breaking spaces)
        Key insight: Content of space-only segments is ignored, position determines spacing
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "space_only_segment_multiple")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Verify multiple space segment treated as empty
        assert result["text"] == "Table 7-2:"

        # Verify large gap results in many proportional spaces
        spacing_info = result["proportional_spacing_info"]
        assert spacing_info[0]["raw_gap_pt"] == 35.0
        assert spacing_info[0]["proportional_spaces"] >= 10  # Large gap should give many spaces

    def test_multiple_consecutive_empty_segments(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test multiple consecutive empty segments handled seamlessly.

        This test validates that multiple empty segments in sequence don't
        create multiple spacing entries or break the gap calculation logic.

        Test setup: Two consecutive empty segments between text segments
        What it verifies: Gap spans all empty segments, single spacing entry created
        Test limitations: Only tests two consecutive empties, not longer sequences
        Key insight: Algorithm should handle any number of consecutive empty segments
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "multiple_consecutive_empty_segments")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Should have single space in normalized text
        assert result["text"] == "A.2.1 Profile"

        # Gap should span both empty segments
        spacing_info = result["proportional_spacing_info"]
        assert len(spacing_info) == 1  # Only one spacing entry despite multiple empties
        assert spacing_info[0]["raw_gap_pt"] == 30.0  # Total gap across both empties

    def test_single_segment_line(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test line with only one text segment works without spacing calculations.

        This test ensures the algorithm handles the simple case of a single
        segment without attempting spacing calculations that would fail.

        Test setup: Single text segment with no other segments to space against
        What it verifies: No spacing info generated, both text versions identical
        Test limitations: Single test case may not cover all single-segment scenarios
        Key insight: Algorithm must handle edge cases gracefully without errors
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "single_segment_line")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Both text versions should be identical
        assert result["text"] == "Introduction"
        assert result["text_proportional"] == "Introduction"

        # No spacing calculations needed
        assert len(result["proportional_spacing_info"]) == 0

    def test_all_empty_segments(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test line with only empty/space-only segments results in empty line.

        This test validates graceful handling of the edge case where all
        segments are filtered out as empty or space-only.

        Test setup: Line containing only empty segment and space-only segment
        What it verifies: Empty result without errors or invalid spacing calculations
        Test limitations: May not test all combinations of empty segment types
        Key insight: Edge case handling prevents crashes on unusual PDF extraction results
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "all_empty_segments")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Should result in completely empty line
        assert result["text"] == ""
        assert result["text_proportional"] == ""
        assert len(result["proportional_spacing_info"]) == 0

    def test_overlapping_segments_negative_gap(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test segments with overlapping bounding boxes (negative gap) handled gracefully.

        This test validates that when PDF extraction produces overlapping text
        segments (which can happen with complex layouts), the spacing algorithm
        doesn't break and still produces reasonable output.

        Test setup: Two segments where second starts before first ends (negative gap)
        What it verifies: At least one space inserted despite negative gap
        Test limitations: May not cover all types of segment overlap scenarios
        Key insight: Real PDF data can have overlapping segments, algorithm must be robust
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "overlapping_segments_negative_gap")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Should still have space in normalized text
        assert result["text"] == "over lapping"

        # Should handle negative gap gracefully
        spacing_info = result["proportional_spacing_info"]
        assert len(spacing_info) == 1
        assert spacing_info[0]["raw_gap_pt"] == -3.0  # Negative gap preserved in metadata
        assert spacing_info[0]["proportional_spaces"] >= 1  # At least one space despite negative gap

    def test_mixed_font_sizes(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test segments with different font sizes use appropriate space width estimation.

        This test validates that when a line contains multiple font sizes,
        the space width estimation adapts to each segment's font context.

        Test setup: Three segments with different font sizes (12pt, 14pt, 10pt)
        What it verifies: Each gap uses appropriate font size for space width calculation
        Test limitations: Uses rounded font sizes, may not test fractional sizes
        Key insight: Font-aware spacing produces more accurate proportional text
        """
        test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == "mixed_font_sizes")

        result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

        # Should have proper spacing in both versions
        assert result["text"] == "Normal BOLD italic"
        assert result["text_proportional"] == test_case["expected"]["text_proportional"]

        # Should have two spacing entries (two gaps between three segments)
        spacing_info = result["proportional_spacing_info"]
        assert len(spacing_info) == 2

        # Each gap should use font size from previous segment
        assert spacing_info[0]["estimated_space_width_pt"] == 3.6  # 12pt * 0.3
        assert spacing_info[1]["estimated_space_width_pt"] == 4.2  # 14pt * 0.3

    def test_comprehensive_pattern_validation(self, extractor: PDFExtractor, test_data: Dict[str, Any]):
        """Test that spacing fixes improve pattern detection accuracy.

        This integration test validates that the spacing reconstruction
        fixes actually improve the pattern detection that motivated this work.

        Test setup: Multiple test cases representing common pattern issues
        What it verifies: Pattern-style text has proper word boundaries
        Test limitations: Limited to test fixture patterns, not full pattern detection
        Key insight: Spacing fix should make section numbers and titles more detectable
        """
        # Test cases that should benefit pattern detection
        pattern_cases = [
            "h264_known_spacing_issue",
            "multiple_consecutive_empty_segments"
        ]

        for case_id in pattern_cases:
            test_case = next(tc for tc in test_data["test_cases"] if tc["case_id"] == case_id)
            result = extractor._build_line_with_proportional_spacing(test_case["input"]["text_segments"])

            # Verify pattern-friendly spacing exists
            normalized_text = result["text"]

            # Should not have patterns like "9.3.4.6Byte" or "A.2.1Profile"
            assert "6Byte" not in normalized_text, f"Case {case_id}: Should have space before 'Byte'"
            assert "1Profile" not in normalized_text, f"Case {case_id}: Should have space before 'Profile'"

            # Should have proper word boundaries for pattern detection
            words = normalized_text.split()
            assert len(words) >= 2, f"Case {case_id}: Should have multiple words separated by spaces"