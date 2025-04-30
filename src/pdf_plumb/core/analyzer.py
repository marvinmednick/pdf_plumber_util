"""Core document analysis functionality."""

import json
from collections import Counter
from typing import Dict, List, Optional, Tuple
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


class DocumentAnalyzer:
    """Analyzes document structure, fonts, and spacing."""

    def __init__(self):
        """Initialize the analyzer."""
        pass

    def analyze_document(self, lines_file: str) -> Dict:
        """Analyze document structure from lines JSON file."""
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

        all_fonts = []
        all_sizes = []
        all_spacings = []
        page_details = []
        max_page_bottom = 0

        print(f"Analyzing {len(data)} page(s)...")

        # First pass: Collect basic stats
        for page_data in data:
            page_num = page_data.get("page", "Unknown")
            lines = page_data.get("lines", [])
            page_height = page_data.get("page_height", DEFAULT_PAGE_HEIGHT)

            print(f"  Processing Page {page_num} with {len(lines)} lines (Pass 1).")

            page_max_bottom = 0
            previous_line_bottom = None
            valid_lines_for_page = []

            for line in lines:
                bbox = line.get("bbox")
                text_segments = line.get("text_segments", [])

                if not text_segments or not bbox or not line.get("text", "").strip():
                    continue

                line_top = bbox.get("top")
                line_bottom = bbox.get("bottom")

                if line_top is None or line_bottom is None or line_bottom <= line_top:
                    continue

                valid_lines_for_page.append(line)

                if line_bottom > page_max_bottom:
                    page_max_bottom = line_bottom

                # Font and size analysis
                for segment in text_segments:
                    font_name = segment.get("font", "UnknownFont")
                    font_size = segment.get("rounded_size")
                    if font_size is not None:
                        rounded_font_size = round_to_nearest(font_size, ROUND_TO_NEAREST_PT)
                        all_fonts.append(font_name)
                        all_sizes.append(rounded_font_size)

                # Spacing analysis
                if previous_line_bottom is not None:
                    spacing = line_top - previous_line_bottom
                    if spacing > 0:
                        rounded_spacing = round_to_nearest(spacing, ROUND_TO_NEAREST_PT)
                        all_spacings.append(rounded_spacing)

                previous_line_bottom = line_bottom

            page_details.append({
                "page_num": page_num,
                "lines": valid_lines_for_page,
                "estimated_height": page_max_bottom,
            })
            if page_max_bottom > max_page_bottom:
                max_page_bottom = page_max_bottom

        # Aggregate initial results
        if not all_fonts or not all_sizes or not all_spacings:
            print("Warning: Insufficient data found to perform basic analysis.")
            analysis_results = {
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
            }
        else:
            font_counts = Counter(all_fonts)
            size_counts = Counter(all_sizes)
            spacing_counts = Counter(all_spacings)
            most_common_font = font_counts.most_common(1)[0] if font_counts else None
            most_common_size = size_counts.most_common(1)[0] if size_counts else None
            common_spacings = spacing_counts.most_common()
            most_common_spacing = None
            for sp, count in common_spacings:
                if sp > 0.01:
                    most_common_spacing = (sp, count)
                    break
            if most_common_spacing is None and common_spacings:
                most_common_spacing = common_spacings[0]

            analysis_results = {
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
            }

        # Second pass: Identify header/footer candidates
        all_header_candidates = []
        all_footer_candidates = []
        page_height_to_use = analysis_results["overall_estimated_height"]

        print(f"\nUsing estimated page height: {page_height_to_use:.2f} points ({page_height_to_use / POINTS_PER_INCH:.2f} inches)")

        for page_info in analysis_results["page_details"]:
            page_num = page_info["page_num"]
            print(f"  Processing Page {page_num} (Pass 2 - Header/Footer).")
            header_cand, footer_cand = self._identify_header_footer_candidates(
                page_info["lines"],
                page_height_to_use,
                analysis_results,
            )
            if header_cand is not None:
                all_header_candidates.append(header_cand)
            if footer_cand is not None:
                all_footer_candidates.append(footer_cand)

        # Aggregate header/footer candidates
        if all_header_candidates:
            analysis_results["header_candidates"] = Counter(all_header_candidates)
        if all_footer_candidates:
            analysis_results["footer_candidates"] = Counter(all_footer_candidates)

        # Add final determined boundaries
        analysis_results["final_header_bottom"] = (
            analysis_results["header_candidates"].most_common(1)[0][0]
            if analysis_results.get("header_candidates")
            else 0.0
        )
        analysis_results["final_footer_top"] = (
            analysis_results["footer_candidates"].most_common(1)[0][0]
            if analysis_results.get("footer_candidates")
            else page_height_to_use
        )

        return analysis_results

    def _identify_header_footer_candidates(
        self, page_lines: List[Dict], page_height: float, analysis_results: Dict
    ) -> Tuple[Optional[float], Optional[float]]:
        """Identify candidate header and footer boundaries for a single page."""
        if not page_lines or not analysis_results or not analysis_results.get("most_common_spacing"):
            if not analysis_results or not analysis_results.get("most_common_spacing"):
                print("  Warning: Cannot perform header/footer analysis without most_common_spacing.")
                return None, None
            elif not page_lines:
                return 0, page_height

        # Define zones
        header_max_y = HEADER_ZONE_INCHES * POINTS_PER_INCH
        footer_min_y = page_height - (FOOTER_ZONE_INCHES * POINTS_PER_INCH)

        # Get spacing thresholds
        base_spacing = analysis_results["most_common_spacing"][0]
        large_gap_threshold = base_spacing * LARGE_GAP_MULTIPLIER
        small_gap_threshold = base_spacing * SMALL_GAP_MULTIPLIER

        # Header identification
        candidate_header_bottom_y = 0
        header_block_lines = []
        last_line_in_header_zone_bottom = 0

        for i, current_line in enumerate(page_lines):
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            if i == 0 and line_top >= header_max_y:
                candidate_header_bottom_y = 0
                break

            if line_top < header_max_y:
                last_line_in_header_zone_bottom = max(last_line_in_header_zone_bottom, line_bottom)

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
                if not header_block_lines:
                    candidate_header_bottom_y = 0
                elif candidate_header_bottom_y == 0:
                    candidate_header_bottom_y = last_line_in_header_zone_bottom
                break

        # Footer identification
        candidate_footer_top_y = page_height
        footer_block_lines = []
        first_line_in_footer_zone_top = page_height

        for i in range(len(page_lines) - 1, -1, -1):
            current_line = page_lines[i]
            line_top = current_line.get("bbox", {}).get("top")
            line_bottom = current_line.get("bbox", {}).get("bottom")

            if line_top is None or line_bottom is None:
                continue

            if i == len(page_lines) - 1 and line_bottom <= footer_min_y:
                candidate_footer_top_y = page_height
                break

            if line_bottom > footer_min_y:
                first_line_in_footer_zone_top = min(first_line_in_footer_zone_top, line_top)

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
                if not footer_block_lines:
                    candidate_footer_top_y = page_height
                elif candidate_footer_top_y == page_height:
                    candidate_footer_top_y = first_line_in_footer_zone_top
                break

        # Round results
        if candidate_header_bottom_y is not None:
            candidate_header_bottom_y = round_to_nearest(candidate_header_bottom_y, ROUND_TO_NEAREST_PT)
        if candidate_footer_top_y is not None:
            candidate_footer_top_y = round_to_nearest(candidate_footer_top_y, ROUND_TO_NEAREST_PT)

        return candidate_header_bottom_y, candidate_footer_top_y

    def print_analysis(self, results: Dict) -> None:
        """Print analysis results in a readable format."""
        if not results:
            return

        print("\n--- Analysis Results ---")

        # Font analysis
        print("\nFont Usage Analysis:")
        likely_body_font = "N/A"
        if results["font_counts"]:
            sorted_fonts = sorted(results["font_counts"].items(), key=lambda item: item[1], reverse=True)
            print("  Distribution:")
            for font, count in sorted_fonts:
                print(f"    - {font}: {count} lines")
            if results["most_common_font"]:
                likely_body_font = results["most_common_font"][0]
                print(f"\n  Conclusion: Likely body text font is '{likely_body_font}' ({results['most_common_font'][1]} lines).")
            else:
                print("\n  Conclusion: Could not determine a dominant font.")
        else:
            print("  No font data found.")

        # Size analysis
        print(f"\nFont Size Analysis (Rounded to nearest {ROUND_TO_NEAREST_PT}pt):")
        likely_body_size = "N/A"
        if results["size_counts"]:
            sorted_sizes = sorted(results["size_counts"].items(), key=lambda item: item[0])
            print("  Distribution:")
            for size, count in sorted_sizes:
                rounded_size = round_to_nearest(size, ROUND_TO_NEAREST_PT)
                print(f"    - {rounded_size:.2f} pt: {count} lines")
            if results["most_common_size"]:
                likely_body_size_val = round_to_nearest(results['most_common_size'][0], ROUND_TO_NEAREST_PT)
                likely_body_size = f"{likely_body_size_val:.2f} pt"
                print(f"\n  Conclusion: Likely body text size is {likely_body_size} ({results['most_common_size'][1]} lines).")
            else:
                print("\n  Conclusion: Could not determine a dominant font size.")
        else:
            print("  No font size data found.")

        # Spacing analysis
        print(f"\nVertical Line Spacing Analysis (Gap between lines, rounded to {ROUND_TO_NEAREST_PT}pt):")
        likely_line_spacing = "N/A"
        likely_para_spacing = "N/A"
        potential_para_gaps_found = []
        if results["spacing_counts"]:
            spacing_counts = Counter(results["spacing_counts"])
            print("  Spacing Distribution (Top 10 most frequent):")
            limit = 10
            count = 0
            for spacing, num in spacing_counts.most_common():
                rounded_spacing = round_to_nearest(spacing, ROUND_TO_NEAREST_PT)
                if count < limit or len(spacing_counts) <= limit:
                    print(f"    - {rounded_spacing:.2f} pt gap: {num} occurrences")
                elif count == limit:
                    print("    ...")
                count += 1

            if results["most_common_spacing"]:
                common_spacing_val = round_to_nearest(results["most_common_spacing"][0], ROUND_TO_NEAREST_PT)
                likely_line_spacing = f"{common_spacing_val:.2f} pt"
                print(f"\n  Conclusion: Likely standard line spacing (within paragraphs) is {likely_line_spacing} ({results['most_common_spacing'][1]} occurrences).")

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
                    print(f"  Conclusion: Likely paragraph spacing is around {likely_para_spacing} (found {sorted_para_gaps[0][1]} times).")
                    print(f"              Other potential paragraph/section gaps: {', '.join(potential_para_gaps_found[1:])}")
                else:
                    print("  Conclusion: Could not clearly distinguish paragraph spacing from line spacing or larger section breaks.")
            else:
                print("\n  Conclusion: Could not determine a dominant line spacing.")
        else:
            print("  No spacing data found.")

        # Header/Footer analysis
        print("\nHeader Analysis:")
        header_bottom_y = round_to_nearest(results.get("final_header_bottom", 0.0), ROUND_TO_NEAREST_PT)
        header_bottom_in = header_bottom_y / POINTS_PER_INCH
        print(f"  Conclusion: Determined Header Bottom Boundary at Y = {header_bottom_y:.2f} pt ({header_bottom_in:.2f} inches from top).")
        if results.get("header_candidates"):
            header_counter = Counter(results["header_candidates"])
            if header_counter:
                print("  Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in header_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(header_counter) <= limit:
                        print(f"    - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        print("    ...")
                    count += 1
            else:
                print("  No consistent header candidates found across pages.")
        else:
            print("  No header candidates identified during processing.")

        print("\nFooter Analysis:")
        page_height = results.get("overall_estimated_height", DEFAULT_PAGE_HEIGHT)
        footer_top_y = round_to_nearest(results.get("final_footer_top", page_height), ROUND_TO_NEAREST_PT)
        footer_top_in = footer_top_y / POINTS_PER_INCH
        footer_size_in = (page_height - footer_top_y) / POINTS_PER_INCH
        print(f"  Conclusion: Determined Footer Top Boundary at Y = {footer_top_y:.2f} pt ({footer_top_in:.2f} inches from top).")
        print(f"              (Implies footer region starts {footer_size_in:.2f} inches from bottom edge)")

        if results.get("footer_candidates"):
            footer_counter = Counter(results["footer_candidates"])
            if footer_counter:
                print("  Supporting Evidence (Candidate Y coords and page counts, Top 5):")
                limit = 5
                count = 0
                for y_coord, num in footer_counter.most_common():
                    rounded_y = round_to_nearest(y_coord, ROUND_TO_NEAREST_PT)
                    if count < limit or len(footer_counter) <= limit:
                        print(f"    - {rounded_y:.2f} pt : {num} pages")
                    elif count == limit:
                        print("    ...")
                    count += 1
            else:
                print("  No consistent footer candidates found across pages.")
        else:
            print("  No footer candidates identified during processing.")

        print("\n--- Summary of Key Document Characteristics ---")
        print(f"  Likely Body Font:   {likely_body_font}")
        print(f"  Likely Body Size:   {likely_body_size}")
        print(f"  Likely Line Spacing: {likely_line_spacing}")
        print(f"  Likely Para Spacing: {likely_para_spacing}")
        print(f"  Est. Header Bottom: {header_bottom_y:.2f} pt ({header_bottom_in:.2f} in)")
        print(f"  Est. Footer Top:    {footer_top_y:.2f} pt ({footer_top_in:.2f} in)")
        print("---------------------------------------------")

        for line in results["page_details"]:
            if 'spacing' in line:
                raw_spacing = line['spacing']
                spacing = round_to_nearest(raw_spacing, ROUND_TO_NEAREST_PT)
                print(f"[DEBUG] raw spacing: {raw_spacing}, rounded spacing: {spacing}, top: {line['bbox']['top']}")
                for i, range_spec in enumerate(spacing_ranges):
                    print(f"[DEBUG] comparing {spacing} to {range_spec}")
                    if self.matches_range(spacing, range_spec):
                        print(f"[DEBUG] MATCHED: {spacing} in {range_spec}")
                        spacing_occurrences[spacing] += 1
                        spacing_lines[spacing].append((line['page_num'], line['bbox']['top']))
                        break 