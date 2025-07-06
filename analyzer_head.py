import json
import argparse
from collections import Counter
import math

# --- Constants ---
POINTS_PER_INCH = 72
DEFAULT_PAGE_HEIGHT = 11 * POINTS_PER_INCH  # US Letter default
HEADER_ZONE_INCHES = 1.25
FOOTER_ZONE_INCHES = 1.0
# Spacing multipliers (relative to typical body spacing)
# Gap must be > this * body_spacing to be considered 'large' (header/footer break)
LARGE_GAP_MULTIPLIER = 1.8
# Gap must be < this * body_spacing to be considered 'small' (within same block)
SMALL_GAP_MULTIPLIER = 1.3
# Gaps between SMALL and LARGE are 'ambiguous' (paragraph-like)
# Rounding precision for font sizes and spacings
ROUND_TO_NEAREST_PT = 0.5  # Change to 0.25 for quarter-point rounding


def round_to_nearest(value, nearest):
    """Round value to the nearest specified increment (e.g., 0.5 or 0.25)."""
    return round(value / nearest) * nearest


def identify_header_footer_candidates(page_lines, page_height, analysis_results):
    """
    Identifies candidate header and footer boundaries for a single page
    using iterative spacing analysis.

    Args:
        page_lines (list): List of line objects for the page, sorted by top y-coord.
        page_height (float): The height of the page in points.
        analysis_results (dict): Dictionary containing overall document analysis
                                 (e.g., 'most_common_spacing').

    Returns:
        tuple: (candidate_header_bottom_y, candidate_footer_top_y)
               Returns (None, None) if analysis is not possible.
    """
    if not page_lines or not analysis_results or not analysis_results.get("most_common_spacing"):
        # Check if most_common_spacing exists and has a value
        if not analysis_results or not analysis_results.get("most_common_spacing"):
            print("  Warning: Cannot perform header/footer analysis without most_common_spacing.")
            return None, None
        # If page_lines is empty but we have spacing, treat as empty page
        elif not page_lines:
            return 0, page_height  # Empty page means header ends at 0, footer starts at height

    # --- Define Zones ---
    header_max_y = HEADER_ZONE_INCHES * POINTS_PER_INCH
    footer_min_y = page_height - (FOOTER_ZONE_INCHES * POINTS_PER_INCH)

    # --- Get Spacing Thresholds ---
    # Use most common spacing as the base for thresholds
    # most_common_spacing is a tuple (value, count)
    base_spacing = analysis_results["most_common_spacing"][0]
    large_gap_threshold = base_spacing * LARGE_GAP_MULTIPLIER
    small_gap_threshold = base_spacing * SMALL_GAP_MULTIPLIER
    # Note: Ambiguous gaps are between small_gap_threshold and large_gap_threshold

    # --- Header Identification ---
    candidate_header_bottom_y = 0  # Default: header is empty space at top
    header_block_lines = []
    last_line_in_header_zone_bottom = 0  # Track bottom of the last line physically in zone

    for i, current_line in enumerate(page_lines):
        line_top = current_line.get("bbox", {}).get("top")
        line_bottom = current_line.get("bbox", {}).get("bottom")

        if line_top is None or line_bottom is None:
            continue  # Skip lines with bad bbox

        # --- Initial Check: Is the first line already below the header zone? ---
        if i == 0 and line_top >= header_max_y:
            # No text in header zone, header is empty space above this line
            candidate_header_bottom_y = 0  # Explicitly set
            break  # Stop header search

        # Track the bottom-most point of any line starting within the header zone
        if line_top < header_max_y:
            last_line_in_header_zone_bottom = max(last_line_in_header_zone_bottom, line_bottom)

        # --- If line starts within header zone, evaluate spacing to next line ---
        if line_top < header_max_y:
            header_block_lines.append(current_line)  # Tentatively add to header block
            current_block_bottom = line_bottom

            # Look at the next line
            if i + 1 < len(page_lines):
                next_line = page_lines[i + 1]
                next_line_top = next_line.get("bbox", {}).get("top")
                next_line_bottom = next_line.get("bbox", {}).get("bottom")

                if next_line_top is None or next_line_bottom is None:
                    # Cannot evaluate gap, assume current line ends header for safety
                    candidate_header_bottom_y = current_block_bottom
                    break

                gap = next_line_top - current_block_bottom

                if gap < 0:
                    gap = 0  # Handle minor overlaps gracefully

                # --- Evaluate Gap ---
                if gap >= large_gap_threshold:
                    # Large gap found: current block is the header
                    candidate_header_bottom_y = current_block_bottom
                    break  # Header found

                elif gap < small_gap_threshold:
                    # Small gap: next line is part of the same block.
                    # Continue loop - next_line will be processed.
                    # If this combined block eventually crosses header_max_y,
                    # it will be classified as body text starting high.
                    pass  # Continue iteration

                else:  # Ambiguous (paragraph-like) gap
                    # Treat as potential header end for now. Cross-page
                    # analysis will be needed to confirm.
                    candidate_header_bottom_y = current_block_bottom
                    # Don't break yet, let next line be evaluated in case it's
                    # also in the header zone with ambiguous spacing.
                    # However, if the *next* line is clearly body text (below zone),
                    # this boundary holds.

            else:
                # This is the last line on the page and it's in the header zone.
                candidate_header_bottom_y = current_block_bottom
                break  # End of page

        # --- Line starts below header zone ---
        else:
            # We've hit the first line that starts *outside* the header zone.
            # The header ended before this line. The candidate_header_bottom_y
            # should be the bottom of the last line processed *within* the zone.
            # Use the tracked 'last_line_in_header_zone_bottom' if no large gap was found earlier.
            if not header_block_lines:  # No lines were ever added to the block
                candidate_header_bottom_y = 0
            elif candidate_header_bottom_y == 0:  # Default wasn't overridden by a gap break
                candidate_header_bottom_y = last_line_in_header_zone_bottom

            break  # Stop header search

    # --- Footer Identification (Iterate from bottom up) ---
    candidate_footer_top_y = page_height  # Default: footer is empty space at bottom
    footer_block_lines = []
    first_line_in_footer_zone_top = page_height  # Track top of the first line physically in zone

    for i in range(len(page_lines) - 1, -1, -1):  # Iterate backwards
        current_line = page_lines[i]
        line_top = current_line.get("bbox", {}).get("top")
        line_bottom = current_line.get("bbox", {}).get("bottom")

        if line_top is None or line_bottom is None:
            continue  # Skip lines with bad bbox

        # --- Initial Check: Is the last line already above the footer zone? ---
        if i == len(page_lines) - 1 and line_bottom <= footer_min_y:
            # No text in footer zone, footer is empty space below this line
            candidate_footer_top_y = page_height  # Explicitly set
            break  # Stop footer search

        # Track the top-most point of any line ending within the footer zone
        if line_bottom > footer_min_y:
            first_line_in_footer_zone_top = min(first_line_in_footer_zone_top, line_top)

        # --- If line ends within footer zone, evaluate spacing to previous line ---
        if line_bottom > footer_min_y:
            footer_block_lines.append(current_line)  # Tentatively add to footer block
            current_block_top = line_top

            # Look at the previous line (higher up the page)
            if i - 1 >= 0:
                prev_line = page_lines[i - 1]
                prev_line_top = prev_line.get("bbox", {}).get("top")
                prev_line_bottom = prev_line.get("bbox", {}).get("bottom")

                if prev_line_top is None or prev_line_bottom is None:
                    # Cannot evaluate gap, assume current line starts footer
                    candidate_footer_top_y = current_block_top
                    break

                gap = current_block_top - prev_line_bottom

                if gap < 0:
                    gap = 0  # Handle minor overlaps

                # --- Evaluate Gap ---
                if gap >= large_gap_threshold:
                    # Large gap found: current block is the footer
                    candidate_footer_top_y = current_block_top
                    break  # Footer found

                elif gap < small_gap_threshold:
                    # Small gap: previous line is part of the same block.
                    # Continue loop - prev_line will be processed.
                    pass  # Continue iteration

                else:  # Ambiguous (paragraph-like) gap
                    # Treat as potential footer start for now.
                    candidate_footer_top_y = current_block_top
                    # Continue loop to potentially group more lines.

            else:
                # This is the first line on the page and it's in the footer zone.
                candidate_footer_top_y = current_block_top
                break  # End of page (top reached)

        # --- Line ends above footer zone ---
        else:
            # We've hit the first line (from bottom) that ends *outside* footer zone.
            # The footer started after this line. candidate_footer_top_y
            # should be the top of the first line processed *within* the zone.
            if not footer_block_lines:  # No lines were ever added
                candidate_footer_top_y = page_height
            elif candidate_footer_top_y == page_height:  # Default wasn't overridden
                candidate_footer_top_y = first_line_in_footer_zone_top

            break  # Stop footer search

    # Round results for consistency in aggregation
    if candidate_header_bottom_y is not None:
        candidate_header_bottom_y = round(candidate_header_bottom_y, 1)
    if candidate_footer_top_y is not None:
        candidate_footer_top_y = round(candidate_footer_top_y, 1)

    return candidate_header_bottom_y, candidate_footer_top_y


def analyze_document_lines(file_path):
    """
    Analyzes text line data from a JSON file to find common font styles,
    sizes, line spacings, and identify candidate header/footer boundaries.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        dict: A dictionary containing analysis results including aggregated
              header/footer candidates. Returns None if an error occurs.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred loading the file: {e}")
        return None

    all_fonts = []
    all_sizes = []
    all_spacings = []
    page_details = []  # Store per-page info including lines and height

    print(f"Analyzing {len(data)} page(s)...")

    max_page_bottom = 0

    # --- First Pass: Collect basic stats and page info ---
    for page_data in data:
        page_num = page_data.get("page", "Unknown")
        lines = page_data.get("lines", [])

        # Sort lines by vertical position (top coordinate)
        lines.sort(key=lambda line: line.get("bbox", {}).get("top", float("inf")))

        print(f"  Processing Page {page_num} with {len(lines)} lines (Pass 1).")

        page_max_bottom = 0
        previous_line_bottom = None
        valid_lines_for_page = []  # Store lines with valid bbox for pass 2

        for i, line in enumerate(lines):
            bbox = line.get("bbox")
            text_segments = line.get("text_segments", [])

            # --- Basic Validity Check ---
            # Skip lines that are just whitespace or have no segments/bbox
            if not text_segments or not bbox or not line.get("text", "").strip():
                # print(f"    Skipping line {i+1} on page {page_num} due to missing data or empty text.")
                continue

            line_top = bbox.get("top")
            line_bottom = bbox.get("bottom")

            if line_top is None or line_bottom is None or line_bottom <= line_top:
                # print(f"    Skipping line {i+1} on page {page_num} due to invalid bbox: {bbox}")
                continue

            valid_lines_for_page.append(line)  # Add line for Pass 2 processing

            # Update page height estimate
            if line_bottom > page_max_bottom:
                page_max_bottom = line_bottom

            # --- Font and Size Analysis ---
            first_segment = text_segments[0]
            font_name = first_segment.get("font", "UnknownFont")
            font_size = first_segment.get("rounded_size")
            if font_size is None:
                font_size = first_segment.get("reported_size")

            if font_size is not None:
                rounded_font_size = round_to_nearest(font_size, ROUND_TO_NEAREST_PT)
                all_fonts.append(font_name)
                all_sizes.append(rounded_font_size)

            # --- Spacing Analysis ---
            if previous_line_bottom is not None:
                spacing = line_top - previous_line_bottom
                # Only consider positive spacing for typical analysis
                if spacing > 0:
                    rounded_spacing = round_to_nearest(spacing, ROUND_TO_NEAREST_PT)
                    all_spacings.append(rounded_spacing)
                # elif spacing < 0:
                # print(f"    Warning: Negative spacing ({spacing:.2f}) detected before line {i+1} on page {page_num}.")

            previous_line_bottom = line_bottom  # Update for next valid line

        page_details.append(
            {
                "page_num": page_num,
                "lines": valid_lines_for_page,
                "estimated_height": page_max_bottom,  # Use max bottom found on page
            }
        )
        if page_max_bottom > max_page_bottom:
            max_page_bottom = page_max_bottom

    # --- Aggregate Initial Results ---
    if not all_fonts or not all_sizes or not all_spacings:
        print("Warning: Insufficient data found to perform basic analysis.")
        # Still try header/footer if possible, but provide empty initial results
        analysis_results = {
            "font_counts": {},
            "size_counts": {},
            "spacing_counts": {},
            "most_common_font": None,
            "most_common_size": None,
            "most_common_spacing": None,
            "page_details": page_details,
            "overall_estimated_height": max_page_bottom or DEFAULT_PAGE_HEIGHT,
            "header_candidates": {},  # Initialize for later aggregation
            "footer_candidates": {},
        }
    else:
        font_counts = Counter(all_fonts)
        size_counts = Counter(all_sizes)
        spacing_counts = Counter(all_spacings)
        most_common_font = font_counts.most_common(1)[0] if font_counts else None
        most_common_size = size_counts.most_common(1)[0] if size_counts else None
        # Filter out zero spacing if it's most common but others exist
        common_spacings = spacing_counts.most_common()
        most_common_spacing = None
        for sp, count in common_spacings:
            if sp > 0.01:  # Use a small threshold to avoid floating point issues
                most_common_spacing = (sp, count)
                break
        if most_common_spacing is None and common_spacings:  # Fallback if only 0 exists
            most_common_spacing = common_spacings[0]

        analysis_results = {
            "font_counts": dict(font_counts),
            "size_counts": dict(size_counts),
            "spacing_counts": dict(spacing_counts),
            "most_common_font": most_common_font,
            "most_common_size": most_common_size,
            "most_common_spacing": most_common_spacing,
            "page_details": page_details,
            # Use max bottom found across all pages, or default
            "overall_estimated_height": max_page_bottom or DEFAULT_PAGE_HEIGHT,
            "header_candidates": {},  # Initialize for later aggregation
            "footer_candidates": {},
        }

    # --- Second Pass: Identify Header/Footer Candidates Per Page ---
    all_header_candidates = []
    all_footer_candidates = []
    page_height_to_use = analysis_results["overall_estimated_height"]
    print(f"\nUsing estimated page height: {page_height_to_use:.2f} points ({page_height_to_use / POINTS_PER_INCH:.2f} inches)")

    for page_info in analysis_results["page_details"]:
        page_num = page_info["page_num"]
        print(f"  Processing Page {page_num} (Pass 2 - Header/Footer).")
        header_cand, footer_cand = identify_header_footer_candidates(
            page_info["lines"],
            page_height_to_use,  # Use consistent height estimate
            analysis_results,  # Pass common stats
        )
        if header_cand is not None:
            all_header_candidates.append(header_cand)
        if footer_cand is not None:
            all_footer_candidates.append(footer_cand)

    # --- Aggregate Header/Footer Candidates ---
    if all_header_candidates:
        analysis_results["header_candidates"] = Counter(all_header_candidates)
    if all_footer_candidates:
        analysis_results["footer_candidates"] = Counter(all_footer_candidates)

    # --- Add Final Determined Boundaries ---
    analysis_results["final_header_bottom"] = analysis_results["header_candidates"].most_common(1)[0][0] if analysis_results.get("header_candidates") else 0.0
    analysis_results["final_footer_top"] = analysis_results["footer_candidates"].most_common(1)[0][0] if analysis_results.get("footer_candidates") else page_height_to_use

    return analysis_results


def print_analysis(results):
    """Prints the analysis results and conclusions in a readable format."""
    if not results:
        return

    print("\n--- Analysis Results ---")

    # --- Font Analysis ---
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

    # --- Size Analysis ---
    print(f"\nFont Size Analysis (Rounded to nearest {ROUND_TO_NEAREST_PT}pt):")
    likely_body_size = "N/A"
    if results["size_counts"]:
        sorted_sizes = sorted(results["size_counts"].items(), key=lambda item: item[0])  # Sort by size
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

    # --- Spacing Analysis ---
    print(f"\nVertical Line Spacing Analysis (Gap between lines, rounded to {ROUND_TO_NEAREST_PT}pt):")
    likely_line_spacing = "N/A"
    likely_para_spacing = "N/A"
    potential_para_gaps_found = []
    if results["spacing_counts"]:
        spacing_counts = Counter(results["spacing_counts"])  # Ensure it's a Counter
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

            # Suggest paragraph spacing (look for gaps larger than most common)
            para_gap_multiplier = 1.3
            potential_para_gaps = {k: v for k, v in spacing_counts.items() if k > common_spacing_val * para_gap_multiplier and k < common_spacing_val * LARGE_GAP_MULTIPLIER * 1.5}
            if potential_para_gaps:
                sorted_para_gaps = sorted(potential_para_gaps.items(), key=lambda item: item[1], reverse=True)
                likely_para_spacing_val = round_to_nearest(sorted_para_gaps[0][0], ROUND_TO_NEAREST_PT)
                likely_para_spacing = f"{likely_para_spacing_val:.2f} pt"
                potential_para_gaps_found = [f"{round_to_nearest(g, ROUND_TO_NEAREST_PT):.2f} pt ({n} times)" for g, n in sorted_para_gaps[:3]]
                print(f"  Conclusion: Likely paragraph spacing is around {likely_para_spacing} (found {sorted_para_gaps[0][1]} times).")
                print(f"              Other potential paragraph/section gaps: {', '.join(potential_para_gaps_found[1:])}")

            else:
                print("  Conclusion: Could not clearly distinguish paragraph spacing from line spacing or larger section breaks.")
        else:
            print("\n  Conclusion: Could not determine a dominant line spacing.")

    else:
        print("  No spacing data found.")

    # --- Header/Footer Analysis ---
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze font styles, sizes, line spacing, and header/footer candidates from a JSON line data file.")
    parser.add_argument("input_file", help="Path to the input JSON file containing line data.")

    args = parser.parse_args()

    analysis_data = analyze_document_lines(args.input_file)

    if analysis_data:
        print_analysis(analysis_data)
