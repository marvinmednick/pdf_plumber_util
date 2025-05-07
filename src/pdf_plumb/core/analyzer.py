"""Core document analysis functionality.

This module provides functionality for analyzing PDF document structure, including:
- Font usage and distribution analysis
- Text size analysis
- Line spacing and paragraph spacing analysis
- Header and footer boundary detection
- Contextual spacing analysis

The analysis is performed in multiple passes:
1. Basic stats collection (fonts, sizes, spacing)
2. Header/footer candidate identification
3. Contextual spacing analysis
4. Final boundary determination

The module uses both traditional and contextual methods for header/footer detection,
with the contextual method taking into account font sizes and spacing patterns.
"""

import json
from collections import Counter
from typing import Dict, List, Optional, Tuple, Any
from ..utils.constants import (
    POINTS_PER_INCH,
    DEFAULT_PAGE_HEIGHT,
    HEADER_ZONE_INCHES,
    FOOTER_ZONE_INCHES,
    LARGE_GAP_MULTIPLIER,
    SMALL_GAP_MULTIPLIER,
    ROUND_TO_NEAREST_PT,
)
from ..utils.helpers import round_to_nearest


# --- Constants for Contextual Analysis ---
LINE_SPACING_TOLERANCE = 0.2  # 20% tolerance for line spacing
PARA_SPACING_MULTIPLIER = 1.1  # Paragraph spacing is ~1.1x font size
SECTION_SPACING_MULTIPLIER = 2.0  # Section spacing is > paragraph spacing
GAP_ROUNDING = 0.5  # Round gaps to nearest 0.5pt for analysis

# --- Spacing Classification Types ---
SPACING_TYPES = {
    'TIGHT': 'Tight',      # Very small gaps between lines
    'LINE': 'Line',        # Standard line spacing within paragraphs
    'PARA': 'Paragraph',   # Spacing between paragraphs
    'SECTION': 'Section',  # Spacing between major sections
    'WIDE': 'Wide'         # Very large gaps (potential page breaks)
}

# --- Colors for Visualization ---
SPACING_COLORS = {
    'TIGHT': '#FFB6C1',  # Light pink
    'LINE': '#98FB98',   # Light green
    'PARA': '#87CEEB',   # Sky blue
    'SECTION': '#DDA0DD', # Plum
    'WIDE': '#F0E68C'    # Khaki
}


class DocumentAnalyzer:
    """Analyzes document structure, fonts, and spacing.
    
    This class provides comprehensive analysis of PDF document structure through
    multiple analysis passes. It can identify:
    - Most common fonts and font sizes
    - Line spacing patterns
    - Header and footer boundaries
    - Contextual spacing rules based on font sizes
    
    The analysis is performed using both traditional methods (based on spacing
    thresholds) and contextual methods (based on font sizes and patterns).
    
    Attributes:
        None (stateless class)
    """

    def __init__(self):
        """Initialize the analyzer.
        
        This is a stateless class, so initialization is minimal.
        """
        pass

    def analyze_document(self, lines_file: str) -> Dict:
        """Analyze document structure from lines JSON file.
        
        This is the main entry point for document analysis. It performs multiple
        passes over the document to collect various statistics and identify
        document structure.
        
        Args:
            lines_file: Path to the JSON file containing line data
            
        Returns:
            Dict containing analysis results including:
            - Font usage statistics
            - Size distribution
            - Spacing patterns
            - Header/footer boundaries
            - Contextual spacing rules
            
        Raises:
            FileNotFoundError: If the input file doesn't exist
            JSONDecodeError: If the input file isn't valid JSON
        """
        # --- Load and Validate Input ---
        try:
            with open(lines_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: File not found at {lines_file}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {lines_file}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred loading the file: {e}")
            return None

        # --- Initialize Analysis Variables ---
        all_fonts = []
        all_sizes = []
        all_spacings = []
        page_details = []
        max_page_bottom = 0

        print(f"Analyzing {len(data)} page(s)...")

        # --- First Pass: Collect Basic Stats ---
        for page_data in data:
            page_num = page_data.get("page", "Unknown")
            lines = page_data.get("lines", [])
            page_height = page_data.get("page_height", DEFAULT_PAGE_HEIGHT)

            print(f"  Processing Page {page_num} with {len(lines)} lines (Pass 1).")

            page_max_bottom = 0
            previous_line_bottom = None
            valid_lines_for_page = []

            # Process each line on the page
            for line in lines:
                bbox = line.get("bbox")
                text_segments = line.get("text_segments", [])

                # Skip invalid lines
                if not text_segments or not bbox or not line.get("text", "").strip():
                    continue

                line_top = bbox.get("top")
                line_bottom = bbox.get("bottom")

                if line_top is None or line_bottom is None or line_bottom <= line_top:
                    continue

                valid_lines_for_page.append(line)

                # Update page height estimate
                if line_bottom > page_max_bottom:
                    page_max_bottom = line_bottom

                # --- Font and Size Analysis ---
                for segment in text_segments:
                    font_name = segment.get("font", "UnknownFont")
                    font_size = segment.get("rounded_size")
                    if font_size is not None:
                        rounded_font_size = round_to_nearest(font_size, ROUND_TO_NEAREST_PT)
                        all_fonts.append(font_name)
                        all_sizes.append(rounded_font_size)

                # --- Spacing Analysis ---
                if previous_line_bottom is not None:
                    spacing = line_top - previous_line_bottom
                    if spacing > 0:
                        rounded_spacing = round_to_nearest(spacing, ROUND_TO_NEAREST_PT)
                        all_spacings.append(rounded_spacing)

                previous_line_bottom = line_bottom

            # Store page details
            page_details.append({
                "page_num": page_num,
                "lines": valid_lines_for_page,
                "estimated_height": page_max_bottom,
            })
            if page_max_bottom > max_page_bottom:
                max_page_bottom = page_max_bottom

        # --- Aggregate Initial Results ---
        if not all_fonts or not all_sizes or not all_spacings:
            print("Warning: Insufficient data found to perform basic analysis.")
            analysis_results = self._create_empty_analysis_results(page_details, max_page_bottom)
        else:
            analysis_results = self._create_analysis_results(
                all_fonts, all_sizes, all_spacings, page_details, max_page_bottom
            )

        # --- Second Pass: Header/Footer Analysis ---
        all_header_candidates = []
        all_footer_candidates = []
        all_contextual_header_candidates = []
        all_contextual_footer_candidates = []
        page_height_to_use = analysis_results["overall_estimated_height"]

        print(f"\nUsing estimated page height: {page_height_to_use:.2f} points ({page_height_to_use / POINTS_PER_INCH:.2f} inches)")

        # --- Collect Contextual Gaps ---
        all_lines = []
        for page_info in analysis_results["page_details"]:
            all_lines.extend(page_info["lines"])
        
        # Perform contextual analysis
        contextual_gaps = self._collect_contextual_gaps(all_lines)
        spacing_rules_by_context = self._analyze_contextual_spacing(contextual_gaps)
        
        # Store contextual analysis results
        analysis_results["contextual_gaps"] = contextual_gaps
        analysis_results["contextual_spacing_rules"] = spacing_rules_by_context

        # --- Process Each Page for Header/Footer ---
        for page_info in analysis_results["page_details"]:
            page_num = page_info["page_num"]
            print(f"  Processing Page {page_num} (Pass 2 - Header/Footer).")
            
            # Traditional method
            header_cand, footer_cand = self._identify_header_footer_candidates(
                page_info["lines"],
                page_height_to_use,
                analysis_results,
            )
            if header_cand is not None:
                all_header_candidates.append(header_cand)
            if footer_cand is not None:
                all_footer_candidates.append(footer_cand)
            
            # Contextual method
            contextual_header_cand, contextual_footer_cand = self._identify_header_footer_contextual(
                page_info["lines"],
                page_height_to_use,
                spacing_rules_by_context
            )
            if contextual_header_cand is not None:
                all_contextual_header_candidates.append(contextual_header_cand)
            if contextual_footer_cand is not None:
                all_contextual_footer_candidates.append(contextual_footer_cand)

        # --- Aggregate Header/Footer Results ---
        if all_header_candidates:
            analysis_results["header_candidates"] = Counter(all_header_candidates)
        if all_footer_candidates:
            analysis_results["footer_candidates"] = Counter(all_footer_candidates)
        if all_contextual_header_candidates:
            analysis_results["contextual_header_candidates"] = Counter(all_contextual_header_candidates)
        if all_contextual_footer_candidates:
            analysis_results["contextual_footer_candidates"] = Counter(all_contextual_footer_candidates)

        # --- Determine Final Boundaries ---
        analysis_results.update(self._determine_final_boundaries(
            analysis_results,
            page_height_to_use
        ))

        return analysis_results

    def _create_empty_analysis_results(self, page_details: List[Dict], max_page_bottom: float) -> Dict:
        """Create empty analysis results structure.
        
        Args:
            page_details: List of page details
            max_page_bottom: Maximum page bottom coordinate
            
        Returns:
            Dictionary with empty analysis results
        """
        return {
            "font_counts": {},
            "size_counts": {},
            "spacing_counts": {},
            "most_common_font": None,
            "most_common_size": None,
            "most_common_spacing": None,
            "page_details": page_details,
            "overall_estimated_height": max_page_bottom or DEFAULT_PAGE_HEIGHT,
            "header_candidates": {},
            "footer_candidates": {},
            "contextual_gaps": {},
            "contextual_spacing_rules": {},
            "contextual_header_candidates": {},
            "contextual_footer_candidates": {},
        }

    def _create_analysis_results(
        self,
        all_fonts: List[str],
        all_sizes: List[float],
        all_spacings: List[float],
        page_details: List[Dict],
        max_page_bottom: float
    ) -> Dict:
        """Create analysis results from collected data.
        
        Args:
            all_fonts: List of all font names
            all_sizes: List of all font sizes
            all_spacings: List of all spacings
            page_details: List of page details
            max_page_bottom: Maximum page bottom coordinate
            
        Returns:
            Dictionary with analysis results
        """
        font_counts = Counter(all_fonts)
        size_counts = Counter(all_sizes)
        spacing_counts = Counter(all_spacings)
        
        # Find most common values
        most_common_font = font_counts.most_common(1)[0] if font_counts else None
        most_common_size = size_counts.most_common(1)[0] if size_counts else None
        
        # Find most common non-zero spacing
        common_spacings = spacing_counts.most_common()
        most_common_spacing = None
        for sp, count in common_spacings:
            if sp > 0.01:
                most_common_spacing = (sp, count)
                break
        if most_common_spacing is None and common_spacings:
            most_common_spacing = common_spacings[0]

        return {
            "font_counts": dict(font_counts),
            "size_counts": dict(size_counts),
            "spacing_counts": dict(spacing_counts),
            "most_common_font": most_common_font,
            "most_common_size": most_common_size,
            "most_common_spacing": most_common_spacing,
            "page_details": page_details,
            "overall_estimated_height": max_page_bottom or DEFAULT_PAGE_HEIGHT,
            "header_candidates": {},
            "footer_candidates": {},
            "contextual_gaps": {},
            "contextual_spacing_rules": {},
            "contextual_header_candidates": {},
            "contextual_footer_candidates": {},
        }

    def _determine_final_boundaries(self, analysis_results: Dict, page_height: float) -> Dict:
        """Determine final header and footer boundaries.
        
        Args:
            analysis_results: Dictionary containing analysis results
            page_height: Height of the page in points
            
        Returns:
            Dictionary with final boundary coordinates
        """
        return {
            "final_header_bottom": (
                analysis_results["header_candidates"].most_common(1)[0][0]
                if analysis_results.get("header_candidates")
                else 0.0
            ),
            "final_footer_top": (
                analysis_results["footer_candidates"].most_common(1)[0][0]
                if analysis_results.get("footer_candidates")
                else page_height
            ),
            "contextual_final_header_bottom": (
                analysis_results["contextual_header_candidates"].most_common(1)[0][0]
                if analysis_results.get("contextual_header_candidates")
                else 0.0
            ),
            "contextual_final_footer_top": (
                analysis_results["contextual_footer_candidates"].most_common(1)[0][0]
                if analysis_results.get("contextual_footer_candidates")
                else page_height
            )
        }

    def _identify_header_footer_candidates(
        self, page_lines: List[Dict], page_height: float, analysis_results: Dict
    ) -> Tuple[Optional[float], Optional[float]]:
        """Identify candidate header and footer boundaries for a single page.
        
        Uses traditional spacing-based method to identify header and footer
        boundaries. This method looks for large gaps in the header and footer
        zones of the page.
        
        Args:
            page_lines: List of line objects for the page
            page_height: Height of the page in points
            analysis_results: Dictionary containing analysis results from first pass
            
        Returns:
            Tuple of (header_bottom_y, footer_top_y) coordinates, or (None, None)
            if analysis cannot be performed
        """
        # --- Validate Input ---
        if not page_lines or not analysis_results or not analysis_results.get("most_common_spacing"):
            if not analysis_results or not analysis_results.get("most_common_spacing"):
                print("  Warning: Cannot perform header/footer analysis without most_common_spacing.")
                return None, None
            elif not page_lines:
                return 0, page_height

        # --- Define Analysis Zones ---
        header_max_y = HEADER_ZONE_INCHES * POINTS_PER_INCH
        footer_min_y = page_height - (FOOTER_ZONE_INCHES * POINTS_PER_INCH)

        # --- Calculate Spacing Thresholds ---
        base_spacing = analysis_results["most_common_spacing"][0]
        large_gap_threshold = base_spacing * LARGE_GAP_MULTIPLIER
        small_gap_threshold = base_spacing * SMALL_GAP_MULTIPLIER

        # --- Identify Header Boundary ---
        header_boundary = self._identify_header_boundary(
            page_lines,
            header_max_y,
            large_gap_threshold,
            small_gap_threshold
        )

        # --- Identify Footer Boundary ---
        footer_boundary = self._identify_footer_boundary(
            page_lines,
            footer_min_y,
            page_height,
            large_gap_threshold,
            small_gap_threshold
        )

        return header_boundary, footer_boundary

    def _identify_header_boundary(
        self,
        page_lines: List[Dict],
        header_max_y: float,
        large_gap_threshold: float,
        small_gap_threshold: float
    ) -> float:
        """Identify the header boundary using traditional spacing analysis.
        
        Args:
            page_lines: List of line objects for the page
            header_max_y: Maximum y-coordinate for header zone
            large_gap_threshold: Threshold for identifying section breaks
            small_gap_threshold: Threshold for identifying paragraph breaks
            
        Returns:
            Y-coordinate of the header bottom boundary
        """
        candidate_header_bottom_y = 0
        header_block_lines = []
        last_line_in_header_zone_bottom = 0

        for i, current_line in enumerate(page_lines):
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            # Handle case where first line is below header zone
            if i == 0 and line_top >= header_max_y:
                candidate_header_bottom_y = 0
                break

            # Track the bottom of the last line in header zone
            if line_top < header_max_y:
                last_line_in_header_zone_bottom = max(last_line_in_header_zone_bottom, line_bottom)

            # Process lines in header zone
            if line_top < header_max_y:
                header_block_lines.append(current_line)
                current_block_bottom = line_bottom

                if i + 1 < len(page_lines):
                    next_line = page_lines[i + 1]
                    next_line_top = next_line.get("bbox", {}).get("top")
                    next_line_bottom = next_line.get("bbox", {}).get("bottom")

                    if next_line_top is None or next_line_bottom is None:
                        candidate_header_bottom_y = current_block_bottom
                        break

                    # Analyze gap to next line
                    gap = next_line_top - current_block_bottom
                    if gap < 0:
                        gap = 0

                    if gap >= large_gap_threshold:
                        candidate_header_bottom_y = current_block_bottom
                        break
                    elif gap < small_gap_threshold:
                        pass
                    else:
                        candidate_header_bottom_y = current_block_bottom
                else:
                    candidate_header_bottom_y = current_block_bottom
                    break
            else:
                # Handle transition out of header zone
                if not header_block_lines:
                    candidate_header_bottom_y = 0
                elif candidate_header_bottom_y == 0:
                    candidate_header_bottom_y = last_line_in_header_zone_bottom
                break

        return round_to_nearest(candidate_header_bottom_y, ROUND_TO_NEAREST_PT)

    def _identify_footer_boundary(
        self,
        page_lines: List[Dict],
        footer_min_y: float,
        page_height: float,
        large_gap_threshold: float,
        small_gap_threshold: float
    ) -> float:
        """Identify the footer boundary using traditional spacing analysis.
        
        Args:
            page_lines: List of line objects for the page
            footer_min_y: Minimum y-coordinate for footer zone
            page_height: Height of the page in points
            large_gap_threshold: Threshold for identifying section breaks
            small_gap_threshold: Threshold for identifying paragraph breaks
            
        Returns:
            Y-coordinate of the footer top boundary
        """
        candidate_footer_top_y = page_height
        footer_block_lines = []
        first_line_in_footer_zone_top = page_height

        for i in range(len(page_lines) - 1, -1, -1):
            current_line = page_lines[i]
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            # Handle case where last line is above footer zone
            if i == len(page_lines) - 1 and line_bottom <= footer_min_y:
                candidate_footer_top_y = page_height
                break

            # Track the top of the first line in footer zone
            if line_bottom > footer_min_y:
                first_line_in_footer_zone_top = min(first_line_in_footer_zone_top, line_top)

            # Process lines in footer zone
            if line_bottom > footer_min_y:
                footer_block_lines.append(current_line)
                current_block_top = line_top

                if i - 1 >= 0:
                    prev_line = page_lines[i - 1]
                    prev_line_top = prev_line.get("bbox", {}).get("top")
                    prev_line_bottom = prev_line.get("bbox", {}).get("bottom")

                    if prev_line_top is None or prev_line_bottom is None:
                        candidate_footer_top_y = current_block_top
                        break

                    # Analyze gap from previous line
                    gap = current_block_top - prev_line_bottom
                    if gap < 0:
                        gap = 0

                    if gap >= large_gap_threshold:
                        candidate_footer_top_y = current_block_top
                        break
                    elif gap < small_gap_threshold:
                        pass
                    else:
                        candidate_footer_top_y = current_block_top
                else:
                    candidate_footer_top_y = current_block_top
                    break
            else:
                # Handle transition out of footer zone
                if not footer_block_lines:
                    candidate_footer_top_y = page_height
                elif candidate_footer_top_y == page_height:
                    candidate_footer_top_y = first_line_in_footer_zone_top
                break

        return round_to_nearest(candidate_footer_top_y, ROUND_TO_NEAREST_PT)

    def _identify_header_footer_contextual(
        self,
        page_lines: List[Dict],
        page_height: float,
        spacing_rules_by_context: Dict[float, Dict[str, Any]]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Identify header and footer boundaries using contextual analysis.
        
        Uses the contextual spacing rules to identify header and footer
        boundaries. This method takes into account the font size and spacing
        patterns of the text to make more accurate determinations.
        
        Args:
            page_lines: List of line objects for the page
            page_height: Height of the page in points
            spacing_rules_by_context: Dictionary of spacing rules by context
            
        Returns:
            Tuple of (header_bottom_y, footer_top_y) coordinates
        """
        if not page_lines:
            return 0, page_height

        # --- Define Analysis Zones ---
        header_max_y = HEADER_ZONE_INCHES * POINTS_PER_INCH
        footer_min_y = page_height - (FOOTER_ZONE_INCHES * POINTS_PER_INCH)

        # --- Identify Header Boundary ---
        header_boundary = self._identify_header_boundary_contextual(
            page_lines,
            header_max_y,
            spacing_rules_by_context
        )

        # --- Identify Footer Boundary ---
        footer_boundary = self._identify_footer_boundary_contextual(
            page_lines,
            footer_min_y,
            page_height,
            spacing_rules_by_context
        )

        return header_boundary, footer_boundary

    def _identify_header_boundary_contextual(
        self,
        page_lines: List[Dict],
        header_max_y: float,
        spacing_rules_by_context: Dict[float, Dict[str, Any]]
    ) -> float:
        """Identify the header boundary using contextual spacing analysis.
        
        Args:
            page_lines: List of line objects for the page
            header_max_y: Maximum y-coordinate for header zone
            spacing_rules_by_context: Dictionary of spacing rules by context
            
        Returns:
            Y-coordinate of the header bottom boundary
        """
        candidate_header_bottom_y = 0
        header_block_lines = []
        last_line_in_header_zone_bottom = 0

        for i, current_line in enumerate(page_lines):
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            # Handle case where first line is below header zone
            if i == 0 and line_top >= header_max_y:
                candidate_header_bottom_y = 0
                break

            # Track the bottom of the last line in header zone
            if line_top < header_max_y:
                last_line_in_header_zone_bottom = max(last_line_in_header_zone_bottom, line_bottom)

            # Process lines in header zone
            if line_top < header_max_y:
                header_block_lines.append(current_line)
                current_block_bottom = line_bottom

                if i + 1 < len(page_lines):
                    next_line = page_lines[i + 1]
                    gap = current_line.get('gap_after')
                    
                    if gap is not None:
                        # Use contextual classification
                        gap_type = self._classify_gap_contextual(
                            gap,
                            current_line.get('predominant_size', 0),
                            spacing_rules_by_context
                        )
                        
                        if gap_type in [SPACING_TYPES['SECTION'], SPACING_TYPES['WIDE']]:
                            candidate_header_bottom_y = current_block_bottom
                            break
                else:
                    candidate_header_bottom_y = current_block_bottom
                    break
            else:
                # Handle transition out of header zone
                if not header_block_lines:
                    candidate_header_bottom_y = 0
                elif candidate_header_bottom_y == 0:
                    candidate_header_bottom_y = last_line_in_header_zone_bottom
                break

        return round_to_nearest(candidate_header_bottom_y, ROUND_TO_NEAREST_PT)

    def _identify_footer_boundary_contextual(
        self,
        page_lines: List[Dict],
        footer_min_y: float,
        page_height: float,
        spacing_rules_by_context: Dict[float, Dict[str, Any]]
    ) -> float:
        """Identify the footer boundary using contextual spacing analysis.
        
        Args:
            page_lines: List of line objects for the page
            footer_min_y: Minimum y-coordinate for footer zone
            page_height: Height of the page in points
            spacing_rules_by_context: Dictionary of spacing rules by context
            
        Returns:
            Y-coordinate of the footer top boundary
        """
        candidate_footer_top_y = page_height
        footer_block_lines = []
        first_line_in_footer_zone_top = page_height

        for i in range(len(page_lines) - 1, -1, -1):
            current_line = page_lines[i]
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            # Handle case where last line is above footer zone
            if i == len(page_lines) - 1 and line_bottom <= footer_min_y:
                candidate_footer_top_y = page_height
                break

            # Track the top of the first line in footer zone
            if line_bottom > footer_min_y:
                first_line_in_footer_zone_top = min(first_line_in_footer_zone_top, line_top)

            # Process lines in footer zone
            if line_bottom > footer_min_y:
                footer_block_lines.append(current_line)
                current_block_top = line_top

                if i - 1 >= 0:
                    prev_line = page_lines[i - 1]
                    gap = current_line.get('gap_before')
                    
                    if gap is not None:
                        # Use contextual classification
                        gap_type = self._classify_gap_contextual(
                            gap,
                            current_line.get('predominant_size', 0),
                            spacing_rules_by_context
                        )
                        
                        if gap_type in [SPACING_TYPES['SECTION'], SPACING_TYPES['WIDE']]:
                            candidate_footer_top_y = current_block_top
                            break
                else:
                    candidate_footer_top_y = current_block_top
                    break
            else:
                # Handle transition out of footer zone
                if not footer_block_lines:
                    candidate_footer_top_y = page_height
                elif candidate_footer_top_y == page_height:
                    candidate_footer_top_y = first_line_in_footer_zone_top
                break

        return round_to_nearest(candidate_footer_top_y, ROUND_TO_NEAREST_PT)

    def print_analysis(self, results: Dict, output_file: Optional[str] = None, show_output: bool = False) -> None:
        """Print analysis results in a readable format.
        
        Formats and prints the analysis results, including:
        - Font usage statistics
        - Size distribution
        - Spacing patterns
        - Header/footer boundaries
        - Contextual spacing rules
        
        Args:
            results: Dictionary containing analysis results
            output_file: Optional path to save the analysis output
            show_output: Whether to print the analysis to stdout
            
        Raises:
            IOError: If there's an error writing to the output file
        """
        output = []
        
        output.append("\n--- Analysis Results ---")

        # Font analysis
        output.append("\nFont Usage Analysis:")
        likely_body_font = "N/A"
        if results["font_counts"]:
            sorted_fonts = sorted(results["font_counts"].items(), key=lambda item: item[1], reverse=True)
            output.append("  Distribution:")
            for font, count in sorted_fonts:
                output.append(f"    - {font}: {count} lines")
            if results["most_common_font"]:
                likely_body_font = results["most_common_font"][0]
                output.append(f"\n  Conclusion: Likely body text font is '{likely_body_font}' ({results['most_common_font'][1]} lines).")
            else:
                output.append("\n  Conclusion: Could not determine a dominant font.")
        else:
            output.append("  No font data found.")

        # Size analysis
        output.append(f"\nFont Size Analysis (Rounded to nearest {ROUND_TO_NEAREST_PT}pt):")
        likely_body_size = "N/A"
        if results["size_counts"]:
            sorted_sizes = sorted(results["size_counts"].items(), key=lambda item: item[0])
            output.append("  Distribution:")
            for size, count in sorted_sizes:
                rounded_size = round_to_nearest(size, ROUND_TO_NEAREST_PT)
                output.append(f"    - {rounded_size:.2f} pt: {count} lines")
            if results["most_common_size"]:
                likely_body_size_val = round_to_nearest(results['most_common_size'][0], ROUND_TO_NEAREST_PT)
                likely_body_size = f"{likely_body_size_val:.2f} pt"
                output.append(f"\n  Conclusion: Likely body text size is {likely_body_size} ({results['most_common_size'][1]} lines).")
            else:
                output.append("\n  Conclusion: Could not determine a dominant font size.")
        else:
            output.append("  No font size data found.")

        # Spacing analysis
        output.append(f"\nVertical Line Spacing Analysis (Gap between lines, rounded to {ROUND_TO_NEAREST_PT}pt):")
        likely_line_spacing = "N/A"
        likely_para_spacing = "N/A"
        potential_para_gaps_found = []
        if results["spacing_counts"]:
            spacing_counts = Counter(results["spacing_counts"])
            output.append("  Spacing Distribution (Top 10 most frequent):")
            limit = 10
            count = 0
            for spacing, num in spacing_counts.most_common():
                rounded_spacing = round_to_nearest(spacing, ROUND_TO_NEAREST_PT)
                if count < limit or len(spacing_counts) <= limit:
                    output.append(f"    - {rounded_spacing:.2f} pt gap: {num} occurrences")
                elif count == limit:
                    output.append("    ...")
                count += 1

            if results["most_common_spacing"]:
                common_spacing_val = round_to_nearest(results["most_common_spacing"][0], ROUND_TO_NEAREST_PT)
                likely_line_spacing = f"{common_spacing_val:.2f} pt"
                output.append(f"\n  Conclusion: Likely standard line spacing (within paragraphs) is {likely_line_spacing} ({results['most_common_spacing'][1]} occurrences).")

                para_gap_multiplier = 1.3
                potential_para_gaps = {
                    k: v for k, v in spacing_counts.items()
                    if k > common_spacing_val * para_gap_multiplier
                    and k < common_spacing_val * LARGE_GAP_MULTIPLIER * 1.5
                }
                if potential_para_gaps:
                    sorted_para_gaps = sorted(potential_para_gaps.items(), key=lambda item: item[1], reverse=True)
                    likely_para_spacing_val = round_to_nearest(sorted_para_gaps[0][0], ROUND_TO_NEAREST_PT)
                    likely_para_spacing = f"{likely_para_spacing_val:.2f} pt"
                    potential_para_gaps_found = [
                        f"{round_to_nearest(g, ROUND_TO_NEAREST_PT):.2f} pt ({n} times)"
                        for g, n in sorted_para_gaps[:3]
                    ]
                    output.append(f"  Conclusion: Likely paragraph spacing is around {likely_para_spacing} (found {sorted_para_gaps[0][1]} times).")
                    output.append(f"              Other potential paragraph/section gaps: {', '.join(potential_para_gaps_found[1:])}")
                else:
                    output.append("  Conclusion: Could not clearly distinguish paragraph spacing from line spacing or larger section breaks.")
            else:
                output.append("\n  Conclusion: Could not determine a dominant line spacing.")
        else:
            output.append("  No spacing data found.")

        # Contextual spacing rules
        output.append("\nContextual Spacing Rules:")
        if results["contextual_spacing_rules"]:
            # Sort contexts by total gaps (most common first)
            sorted_contexts = sorted(
                results["contextual_spacing_rules"].items(),
                key=lambda x: x[1]['total_gaps'],
                reverse=True
            )
            
            for context_size, rules in sorted_contexts:
                output.append(f"\n  For text size {context_size}pt (found in {rules['total_lines']} lines, {rules['total_gaps']} gaps):")
                
                # Base spacing
                if "most_common_gap" in rules:
                    output.append(f"    Base spacing: {rules['most_common_gap']:.1f}pt")
                
                # Line spacing
                if "line_spacing_range" in rules:
                    output.append(f"    Line spacing range: {rules['line_spacing_range'][0]:.1f}pt - {rules['line_spacing_range'][1]:.1f}pt")
                    if rules['line_gaps']:
                        output.append("      Common line gaps:")
                        for gap, count in rules['line_gaps'].items():
                            output.append(f"        {gap:.1f}pt ({count} occurrences)")
                
                # Paragraph spacing
                if "para_spacing_max" in rules:
                    output.append(f"    Paragraph spacing max: {rules['para_spacing_max']:.1f}pt")
                    if rules['para_gaps']:
                        output.append("      Common paragraph gaps:")
                        for gap, count in rules['para_gaps'].items():
                            output.append(f"        {gap:.1f}pt ({count} occurrences)")
                
                # Section spacing
                if rules['section_gaps']:
                    output.append("    Section gaps:")
                    for gap, count in rules['section_gaps'].items():
                        output.append(f"        {gap:.1f}pt ({count} occurrences)")
                
                # Overall gap distribution
                if rules['gap_distribution']:
                    output.append("    Overall gap distribution (top 5):")
                    for gap, count in sorted(rules['gap_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]:
                        output.append(f"        {gap:.1f}pt ({count} occurrences)")
        else:
            output.append("  No contextual spacing rules found.")

        # Header analysis
        output.append("\nHeader Analysis:")
        header_bottom_y = round_to_nearest(results.get("final_header_bottom", 0.0), ROUND_TO_NEAREST_PT)
        header_bottom_in = header_bottom_y / POINTS_PER_INCH
        output.append(f"  Traditional method:")
        output.append(f"    Conclusion: Determined Header Bottom Boundary at Y = {header_bottom_y:.2f} pt ({header_bottom_in:.2f} inches from top).")
        if results.get("header_candidates"):
            header_counter = Counter(results["header_candidates"])
            if header_counter:
                output.append("    Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in header_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(header_counter) <= limit:
                        output.append(f"      - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        output.append("      ...")
                    count += 1
            else:
                output.append("    No consistent header candidates found across pages.")
        else:
            output.append("    No header candidates identified during processing.")

        # Contextual header analysis
        contextual_header_bottom_y = round_to_nearest(results.get("contextual_final_header_bottom", 0.0), ROUND_TO_NEAREST_PT)
        contextual_header_bottom_in = contextual_header_bottom_y / POINTS_PER_INCH
        output.append(f"  Contextual method:")
        output.append(f"    Conclusion: Determined Header Bottom Boundary at Y = {contextual_header_bottom_y:.2f} pt ({contextual_header_bottom_in:.2f} inches from top).")
        if results.get("contextual_header_candidates"):
            contextual_header_counter = Counter(results["contextual_header_candidates"])
            if contextual_header_counter:
                output.append("    Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in contextual_header_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(contextual_header_counter) <= limit:
                        output.append(f"      - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        output.append("      ...")
                    count += 1
            else:
                output.append("    No consistent header candidates found across pages.")
        else:
            output.append("    No header candidates identified during processing.")

        # Footer analysis
        output.append("\nFooter Analysis:")
        page_height = results.get("overall_estimated_height", DEFAULT_PAGE_HEIGHT)
        footer_top_y = round_to_nearest(results.get("final_footer_top", page_height), ROUND_TO_NEAREST_PT)
        footer_top_in = footer_top_y / POINTS_PER_INCH
        footer_size_in = (page_height - footer_top_y) / POINTS_PER_INCH
        output.append(f"  Traditional method:")
        output.append(f"    Conclusion: Determined Footer Top Boundary at Y = {footer_top_y:.2f} pt ({footer_top_in:.2f} inches from top).")
        output.append(f"                (Implies footer region starts {footer_size_in:.2f} inches from bottom edge)")
        if results.get("footer_candidates"):
            footer_counter = Counter(results["footer_candidates"])
            if footer_counter:
                output.append("    Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in footer_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(footer_counter) <= limit:
                        output.append(f"      - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        output.append("      ...")
                    count += 1
            else:
                output.append("    No consistent footer candidates found across pages.")
        else:
            output.append("    No footer candidates identified during processing.")

        # Contextual footer analysis
        contextual_footer_top_y = round_to_nearest(results.get("contextual_final_footer_top", page_height), ROUND_TO_NEAREST_PT)
        contextual_footer_top_in = contextual_footer_top_y / POINTS_PER_INCH
        contextual_footer_size_in = (page_height - contextual_footer_top_y) / POINTS_PER_INCH
        output.append(f"  Contextual method:")
        output.append(f"    Conclusion: Determined Footer Top Boundary at Y = {contextual_footer_top_y:.2f} pt ({contextual_footer_top_in:.2f} inches from top).")
        output.append(f"                (Implies footer region starts {contextual_footer_size_in:.2f} inches from bottom edge)")
        if results.get("contextual_footer_candidates"):
            contextual_footer_counter = Counter(results["contextual_footer_candidates"])
            if contextual_footer_counter:
                output.append("    Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in contextual_footer_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(contextual_footer_counter) <= limit:
                        output.append(f"      - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        output.append("      ...")
                    count += 1
            else:
                output.append("    No consistent footer candidates found across pages.")
        else:
            output.append("    No footer candidates identified during processing.")

        output.append("\n--- Summary of Key Document Characteristics ---")
        output.append(f"  Likely Body Font:   {likely_body_font}")
        output.append(f"  Likely Body Size:   {likely_body_size}")
        output.append(f"  Likely Line Spacing: {likely_line_spacing}")
        output.append(f"  Likely Para Spacing: {likely_para_spacing}")
        output.append(f"  Est. Header Bottom: {header_bottom_y:.2f} pt ({header_bottom_in:.2f} in)")
        output.append(f"  Est. Footer Top:    {footer_top_y:.2f} pt ({footer_top_in:.2f} in)")
        output.append("---------------------------------------------")

        # Join all output lines
        output_text = "\n".join(output)

        # Always save to file
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output_text)
            print(f"Analysis results saved to {output_file}")
        except Exception as e:
            print(f"Error saving analysis results to file: {e}")
            return

        # Optionally show on stdout
        if show_output:
            print("\nAnalysis Results:")
            print(output_text)

    def _collect_contextual_gaps(self, lines: List[Dict]) -> Dict[float, Dict[str, Any]]:
        """Collect gaps between lines with the same predominant size.
        
        This method analyzes the vertical spacing between lines, grouping them
        by their predominant font size. This allows for more accurate spacing
        analysis that takes into account the context of the text.
        
        Args:
            lines: List of enriched line objects containing font and spacing info
            
        Returns:
            Dictionary mapping context sizes to gap data:
            {
                font_size: {
                    'gaps': [list of gaps],
                    'total_lines': count
                }
            }
        """
        gaps_by_context = {}
        total_lines_by_context = {}
        
        # First count total lines per context size
        for line in lines:
            context_size = line.get('predominant_size')
            if context_size is not None:
                total_lines_by_context[context_size] = total_lines_by_context.get(context_size, 0) + 1
        
        # Then collect gaps
        for i in range(1, len(lines)):
            current_line = lines[i]
            previous_line = lines[i-1]
            
            # Only consider gaps between lines with the same predominant size
            if (current_line.get('predominant_size') == previous_line.get('predominant_size') and
                current_line.get('predominant_size') is not None):
                
                context_size = current_line['predominant_size']
                gap = current_line.get('gap_before')
                
                if gap is not None and gap > 0.01:
                    # Round gap to nearest 0.5pt for analysis
                    rounded_gap = round(gap / GAP_ROUNDING) * GAP_ROUNDING
                    gaps_by_context.setdefault(context_size, []).append(rounded_gap)
        
        # Add total line counts to the results
        for context_size in gaps_by_context:
            gaps_by_context[context_size] = {
                'gaps': gaps_by_context[context_size],
                'total_lines': total_lines_by_context.get(context_size, 0)
            }
        
        return gaps_by_context

    def _analyze_contextual_spacing(self, gaps_by_context: Dict[float, Dict[str, Any]]) -> Dict[float, Dict[str, Any]]:
        """Analyze spacing patterns for each context size.
        
        Takes the collected gaps and analyzes them to determine spacing rules
        for each font size context. This includes identifying:
        - Line spacing ranges
        - Paragraph spacing thresholds
        - Section spacing patterns
        
        Args:
            gaps_by_context: Dictionary mapping context sizes to gap data
            
        Returns:
            Dictionary mapping context sizes to their spacing rules:
            {
                font_size: {
                    'line_spacing_range': (min, max),
                    'para_spacing_max': value,
                    'most_common_gap': value,
                    'gap_distribution': {gap: count},
                    'line_gaps': {gap: count},
                    'para_gaps': {gap: count},
                    'section_gaps': {gap: count},
                    'total_gaps': count,
                    'total_lines': count
                }
            }
        """
        spacing_rules_by_context = {}
        
        for context_size, gap_data in gaps_by_context.items():
            gap_list = gap_data['gaps']
            total_lines = gap_data['total_lines']
            
            if not gap_list:
                continue
                
            # Get frequency distribution of gaps
            gap_counts = Counter(gap_list)
            most_common_gap = gap_counts.most_common(1)[0][0]
            
            # Define line spacing range based on most common gap
            line_spacing_range = (
                most_common_gap * (1 - LINE_SPACING_TOLERANCE),
                most_common_gap * (1 + LINE_SPACING_TOLERANCE)
            )
            
            # Define paragraph spacing range based on font size
            para_spacing_max = context_size * PARA_SPACING_MULTIPLIER
            
            # Collect gaps within each category
            line_gaps = {g: c for g, c in gap_counts.items() if g <= line_spacing_range[1]}
            para_gaps = {g: c for g, c in gap_counts.items() 
                        if g > line_spacing_range[1] and g <= para_spacing_max}
            section_gaps = {g: c for g, c in gap_counts.items() 
                          if g > para_spacing_max}
            
            # Store rules and statistics for this context
            spacing_rules_by_context[context_size] = {
                'line_spacing_range': line_spacing_range,
                'para_spacing_max': para_spacing_max,
                'most_common_gap': most_common_gap,
                'gap_distribution': dict(gap_counts),
                'line_gaps': dict(sorted(line_gaps.items())),
                'para_gaps': dict(sorted(para_gaps.items())),
                'section_gaps': dict(sorted(section_gaps.items())),
                'total_gaps': len(gap_list),
                'total_lines': total_lines
            }
        
        return spacing_rules_by_context

    def _classify_gap_contextual(
        self, 
        gap: float, 
        context_size: float, 
        spacing_rules_by_context: Dict[float, Dict[str, Any]]
    ) -> str:
        """Classify a gap based on contextual rules.
        
        Uses the spacing rules determined for a particular font size context
        to classify a gap as line spacing, paragraph spacing, or section spacing.
        
        Args:
            gap: The gap to classify in points
            context_size: The predominant size of the line
            spacing_rules_by_context: Dictionary of spacing rules by context
            
        Returns:
            String classification of the gap ('Tight', 'Line', 'Paragraph',
            'Section', or 'Wide')
        """
        if context_size not in spacing_rules_by_context:
            # Fall back to most common font size if available
            common_sizes = sorted(spacing_rules_by_context.keys(), 
                                key=lambda x: spacing_rules_by_context[x]['total_gaps'],
                                reverse=True)
            if common_sizes:
                context_size = common_sizes[0]
            else:
                return SPACING_TYPES['OTHER']
            
        rules = spacing_rules_by_context[context_size]
        rounded_gap = round(gap / GAP_ROUNDING) * GAP_ROUNDING
        
        # Check if gap falls within any defined range
        if rounded_gap <= rules['line_spacing_range'][1]:
            return SPACING_TYPES['LINE']
        elif rounded_gap <= rules['para_spacing_max']:
            return SPACING_TYPES['PARA']
        else:
            return SPACING_TYPES['SECTION'] 