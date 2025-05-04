"""Core PDF extraction functionality."""

import json
from typing import Dict, List, Optional
import pdfplumber
from ..utils.helpers import normalize_line, save_json


class PDFExtractor:
    """Handles PDF text extraction and processing."""

    def __init__(self, y_tolerance: int = 5, x_tolerance: int = 5):
        """Initialize the extractor with tolerance values."""
        self.y_tolerance = y_tolerance
        self.x_tolerance = x_tolerance
        self.extra_attrs = ["x0", "y0", "x1", "y1", "text", "fontname", "size", "top", "adv"]

    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF using multiple methods."""
        results = {
            "extract_text": [],
            "extract_text_lines": [],
            "extract_words_manual": [],
            "comparison": [],
            "lines_json_by_page": [],
            "raw_words_by_page": [],
        }

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Method 1: extract_text()
                text_raw = page.extract_text()
                results["extract_text"].append({
                    "page": page_num + 1,
                    "content": text_raw.split("\n") if text_raw else [],
                })

                # Method 2: extract_text_lines()
                text_lines = page.extract_text_lines(layout=True)
                results["extract_text_lines"].append({
                    "page": page_num + 1,
                    "content": [line["text"] for line in text_lines] if text_lines else [],
                })

                # Method 3: extract_words() with manual alignment
                words = page.extract_words(
                    x_tolerance_ratio=0.3,
                    use_text_flow=True,
                    keep_blank_chars=True,
                    extra_attrs=self.extra_attrs
                )

                if words:
                    lines_json, raw_words = self._process_words(words, page_num + 1, page.width, page.height)
                    results["lines_json_by_page"].append(lines_json)
                    results["raw_words_by_page"].append(raw_words)
                    results["extract_words_manual"].append({
                        "page": page_num + 1,
                        "content": [" ".join(w["text"] for w in line) for line in self._combine_words(words)],
                    })
                else:
                    results["lines_json_by_page"].append({
                        "page": page_num + 1,
                        "lines": [],
                        "page_width": page.width,
                        "page_height": page.height
                    })
                    results["raw_words_by_page"].append({
                        "page": page_num + 1,
                        "words": []
                    })

            # Generate comparison
            results["comparison"] = self._generate_comparison(results)

        return results

    def _process_words(self, words: List[Dict], page_num: int, page_width: float, page_height: float) -> tuple:
        """Process words into lines and segments."""
        # Sort words by vertical position
        sorted_words = sorted(words, key=lambda w: w["top"])

        # Group words into lines
        lines = []
        current_line = []
        prev_top = sorted_words[0]["top"]

        for word in sorted_words:
            if abs(word["top"] - prev_top) > self.y_tolerance:
                lines.append(current_line)
                current_line = [word]
                prev_top = word["top"]
            else:
                current_line.append(word)
        if current_line:
            lines.append(current_line)

        # Process each line
        lines_json = []
        prev_line_bottom = None  # Track previous line's bottom for gap calculation

        for line_number, line in enumerate(lines, 1):
            line_sorted = sorted(line, key=lambda w: w["x0"])
            text_segments = self._create_text_segments(line_sorted)
            line_bbox = self._calculate_line_bbox(line_sorted)

            # Get the text from segments instead of joining words
            line_text = "".join(segment["text"] for segment in text_segments)

            # Calculate predominant size and font
            size_widths = {}  # Map of size -> total width
            font_widths = {}  # Map of font -> total width
            total_line_width = 0

            for segment in text_segments:
                # Get segment width
                width = segment["bbox"]["x1"] - segment["bbox"]["x0"]
                total_line_width += width

                # Track size widths
                size = segment.get("rounded_size", 0)
                size_widths[size] = size_widths.get(size, 0) + width

                # Track font widths
                font = segment.get("font", "UnknownFont")
                font_widths[font] = font_widths.get(font, 0) + width

            # Find predominant size and font
            predominant_size = max(size_widths.items(), key=lambda x: x[1])[0] if size_widths else None
            predominant_font = max(font_widths.items(), key=lambda x: x[1])[0] if font_widths else None

            # Calculate coverage percentages
            predominant_size_coverage = (size_widths[predominant_size] / total_line_width * 100) if predominant_size and total_line_width > 0 else 0
            predominant_font_coverage = (font_widths[predominant_font] / total_line_width * 100) if predominant_font and total_line_width > 0 else 0

            # Calculate gap_before
            gap_before = None
            if prev_line_bottom is not None and line_bbox.get("top") is not None:
                gap_before = line_bbox["top"] - prev_line_bottom
                if gap_before < 0:  # Handle overlapping lines
                    gap_before = 0

            # Create line object
            line_obj = {
                "line_number": line_number,
                "text": line_text,
                "bbox": line_bbox,
                "text_segments": text_segments,
                "predominant_size": predominant_size,
                "predominant_font": predominant_font,
                "predominant_size_coverage": round(predominant_size_coverage, 1),  # Round to 1 decimal place
                "predominant_font_coverage": round(predominant_font_coverage, 1),  # Round to 1 decimal place
                "gap_before": gap_before,
            }
            lines_json.append(line_obj)

            # Update prev_line_bottom for next iteration
            if line_bbox.get("bottom") is not None:
                prev_line_bottom = line_bbox["bottom"]

        # Calculate gap_after in a second pass
        for i in range(len(lines_json) - 1):
            current_line = lines_json[i]
            next_line = lines_json[i + 1]
            
            if (current_line["bbox"].get("bottom") is not None and 
                next_line["bbox"].get("top") is not None):
                gap_after = next_line["bbox"]["top"] - current_line["bbox"]["bottom"]
                if gap_after < 0:  # Handle overlapping lines
                    gap_after = 0
                current_line["gap_after"] = gap_after
            else:
                current_line["gap_after"] = None

        # Set gap_after for last line
        if lines_json:
            lines_json[-1]["gap_after"] = None

        return {
            "page": page_num,
            "lines": lines_json,
            "page_width": page_width,
            "page_height": page_height
        }, {
            "page": page_num,
            "words": [dict(word, page=page_num) for word in sorted_words]
        }

    def _create_text_segments(self, line: List[Dict]) -> List[Dict]:
        """Create text segments from a line of words."""
        text_segments = []
        seg_start = 0

        for i in range(1, len(line)):
            prev = line[i - 1]
            curr = line[i]
            if (
                prev.get("fontname") != curr.get("fontname")
                or prev.get("size") != curr.get("size")
                or prev.get("upright", True) != curr.get("upright", True)
            ):
                segment_words = line[seg_start:i]
                text_segments.append(self._create_segment(segment_words))
                seg_start = i

        # Add last segment
        if seg_start < len(line):
            text_segments.append(self._create_segment(line[seg_start:]))

        return text_segments

    def _create_segment(self, words: List[Dict]) -> Dict:
        """Create a text segment from a group of words."""
        segment_text = "".join(w["text"] for w in words)
        segment_bbox = {
            "x0": min(w["x0"] for w in words),
            "top": min(w["top"] for w in words),
            "x1": max(w["x1"] for w in words),
            "bottom": max(w["bottom"] for w in words),
        }
        return {
            "font": words[0].get("fontname"),
            "reported_size": words[0].get("size"),
            "rounded_size": round(float(words[0].get("size", "0")) * 2) / 2,
            "direction": "upright" if words[0].get("upright", True) else "rotated",
            "text": segment_text,
            "bbox": segment_bbox,
        }

    def _calculate_line_bbox(self, line: List[Dict]) -> Dict:
        """Calculate bounding box for a line of words."""
        return {
            "x0": min(w["x0"] for w in line),
            "top": min(w["top"] for w in line),
            "x1": max(w["x1"] for w in line),
            "bottom": max(w["bottom"] for w in line),
        }

    def _combine_words(self, words: List[Dict]) -> List[List[Dict]]:
        """Combine consecutive words within x_tolerance."""
        lines = []
        current_line = []
        prev_top = words[0]["top"]

        for word in words:
            if abs(word["top"] - prev_top) > self.y_tolerance:
                lines.append(current_line)
                current_line = [word]
                prev_top = word["top"]
            else:
                current_line.append(word)
        if current_line:
            lines.append(current_line)

        combined_lines = []
        for line in lines:
            line_sorted = sorted(line, key=lambda w: w["x0"])
            combined_line = []
            current_word = line_sorted[0].copy()
            for next_word in line_sorted[1:]:
                if abs(next_word["x0"] - current_word["x1"]) <= self.x_tolerance:
                    current_word["text"] += next_word["text"]
                    current_word["x1"] = next_word["x1"]
                else:
                    combined_line.append(current_word)
                    current_word = next_word.copy()
            combined_line.append(current_word)
            combined_lines.append(combined_line)

        return combined_lines

    def _generate_comparison(self, results: Dict) -> List[Dict]:
        """Generate comparison of extraction methods."""
        comparison = []
        for page_idx in range(len(results["extract_text"])):
            page_num = page_idx + 1
            methods = {
                "text": [normalize_line(line) for line in results["extract_text"][page_idx]["content"] if line.strip()],
                "lines": [normalize_line(line) for line in results["extract_text_lines"][page_idx]["content"] if line.strip()],
                "words": [normalize_line(line) for line in results["extract_words_manual"][page_idx]["content"] if line.strip()],
            }
            max_lines = max(len(methods["text"]), len(methods["lines"]), len(methods["words"]))

            for line_idx in range(max_lines):
                comparison_entry = {
                    "page": page_num,
                    "line": line_idx + 1,
                    "methods": {},
                }
                for method in methods:
                    try:
                        content = methods[method][line_idx]
                        comparison_entry["methods"][method] = content
                    except IndexError:
                        comparison_entry["methods"][method] = None
                comparison.append(comparison_entry)

        return comparison

    def save_results(self, results: Dict, output_dir: str, base_name: str) -> None:
        """Save extraction results to files."""
        from pathlib import Path

        # Save lines data
        lines_path = Path(output_dir) / f"{base_name}_lines.json"
        save_json(results["lines_json_by_page"], lines_path)

        # Save raw words data
        words_path = Path(output_dir) / f"{base_name}_words.json"
        save_json(results["raw_words_by_page"], words_path)

        # Save comparison data
        compare_path = Path(output_dir) / f"{base_name}_compare.json"
        save_json(results["comparison"], compare_path)

        # Save metadata and statistics
        metadata = {
            "y_tolerance": self.y_tolerance,
            "x_tolerance": self.x_tolerance,
        }
        statistics = {
            "page_count": len(results["extract_text"]),
            "avg_lines_per_page": {
                "extract_text": sum(len(p["content"]) for p in results["extract_text"]) / len(results["extract_text"]),
                "extract_text_lines": sum(len(p["content"]) for p in results["extract_text_lines"]) / len(results["extract_text_lines"]),
                "extract_words_manual": sum(len(p["content"]) for p in results["extract_words_manual"]) / len(results["extract_words_manual"]),
            },
            "total_differences": sum(
                1 for entry in results["comparison"]
                if len(set(v for v in entry["methods"].values() if v is not None)) > 1
            ) if results["comparison"] else None,
        }
        info_path = Path(output_dir) / f"{base_name}_info.json"
        save_json({"metadata": metadata, "statistics": statistics}, info_path) 