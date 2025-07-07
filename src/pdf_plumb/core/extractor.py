"""Core PDF extraction functionality.

This module provides functionality for extracting and processing text from PDF documents.
It includes methods for:
- Text extraction using multiple strategies (raw text, text lines, word-based)
- Word and line processing with font and size analysis
- Text segment creation and bounding box calculation
- Comparison of different extraction methods
- Results saving and statistics generation

The extraction process involves:
1. Opening and reading the PDF file
2. Processing each page using multiple extraction methods
3. Analyzing and normalizing the extracted text
4. Generating comparison data between methods
5. Saving results in various formats

The module uses pdfplumber for PDF processing and includes custom logic for
text alignment, font analysis, and spacing calculations.
"""

import json
from typing import Dict, List, Optional
import pdfplumber
from rich.progress import Progress, TaskID
from ..utils.helpers import normalize_line
from ..utils.file_handler import FileHandler
from ..core.utils.logging import LogManager
from ..config import get_config


class PDFExtractor:
    """Handles PDF text extraction and processing.
    
    This class provides comprehensive PDF text extraction capabilities using
    multiple methods to ensure accurate text capture. It processes the extracted
    text to identify:
    - Text lines and their properties
    - Font usage and size distribution
    - Text segment boundaries
    - Line spacing and gaps
    
    The class maintains tolerance values for text alignment and provides
    methods for saving and comparing extraction results.
    
    Attributes:
        y_tolerance (int): Vertical tolerance for line alignment
        x_tolerance (int): Horizontal tolerance for word alignment
        gap_rounding (float): Amount to round gap values to (in points)
        extra_attrs (List[str]): Additional attributes to extract from PDF
    """

    def __init__(self):
        """Initialize the extractor using configuration."""
        self.config = get_config()
        self.y_tolerance = self.config.y_tolerance
        self.x_tolerance = self.config.x_tolerance
        self.gap_rounding = self.config.gap_rounding
        self.extra_attrs = ["x0", "y0", "x1", "y1", "text", "fontname", "size", "top", "adv"]
        self.logger = LogManager(self.config.log_level)
        self.file_handler = FileHandler(debug_level=self.config.log_level)

    def extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract text from PDF using multiple methods.
        
        This is the main entry point for PDF text extraction. It processes the
        PDF file using three different extraction methods:
        1. Raw text extraction (extract_text)
        2. Text line extraction (extract_text_lines)
        3. Word-based extraction with manual alignment
        
        Args:
            pdf_path: Path to the PDF file to process
            
        Returns:
            Dictionary containing extraction results from all methods:
            - extract_text: Raw text extraction results
            - extract_text_lines: Line-based extraction results
            - extract_words_manual: Word-based extraction results
            - comparison: Comparison between methods
            - lines_json_by_page: Detailed line data
            - raw_words_by_page: Raw word data
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            Exception: For other PDF processing errors
        """
        # --- Initialize Results Structure ---
        results = {
            "extract_text": [],
            "extract_text_lines": [],
            "extract_words_manual": [],
            "comparison": [],
            "lines_json_by_page": [],
            "raw_words_by_page": [],
        }

        # --- Process PDF File ---
        with pdfplumber.open(pdf_path) as pdf:
            with Progress() as progress:
                task = progress.add_task("Extracting PDF pages...", total=len(pdf.pages))
                
                for page_num, page in enumerate(pdf.pages):
                    # --- Method 1: Raw Text Extraction ---
                    text_raw = page.extract_text()
                    results["extract_text"].append({
                        "page": page_num + 1,
                        "content": text_raw.split("\n") if text_raw else [],
                    })

                    # --- Method 2: Text Line Extraction ---
                    text_lines = page.extract_text_lines(layout=True)
                    results["extract_text_lines"].append({
                        "page": page_num + 1,
                        "content": [line["text"] for line in text_lines] if text_lines else [],
                    })

                    # --- Method 3: Word-based Extraction ---
                    words = page.extract_words(
                        x_tolerance_ratio=0.3,
                        use_text_flow=True,
                        keep_blank_chars=True,
                        extra_attrs=self.extra_attrs
                    )

                    if words:
                        # Process words into lines and segments
                        lines_json, raw_words = self._process_words(words, page_num + 1, page.width, page.height)
                        results["lines_json_by_page"].append(lines_json)
                        results["raw_words_by_page"].append(raw_words)
                        results["extract_words_manual"].append({
                            "page": page_num + 1,
                            "content": [" ".join(w["text"] for w in line) for line in self._combine_words(words)],
                        })
                    else:
                        # Handle empty page case
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
                    
                    progress.advance(task)

            # --- Generate Comparison Data ---
            results["comparison"] = self._generate_comparison(results)

        return results

    def _process_words(self, words: List[Dict], page_num: int, page_width: float, page_height: float) -> tuple:
        """Process words into lines and segments.
        
        This method takes raw word data and processes it into structured line
        data, including:
        - Text segments with font and size information
        - Line bounding boxes
        - Predominant font and size analysis
        - Gap calculations between lines
        
        Args:
            words: List of word objects from PDF
            page_num: Page number being processed
            page_width: Width of the page in points
            page_height: Height of the page in points
            
        Returns:
            Tuple containing:
            - Dictionary with processed line data
            - Dictionary with raw word data
        """
        # --- Sort and Group Words into Lines ---
        sorted_words = sorted(words, key=lambda w: w["top"])
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

        # --- Process Each Line ---
        lines_json = []
        prev_line_bottom = None  # Track previous line's bottom for gap calculation

        for line_number, line in enumerate(lines, 1):
            # --- Sort Line Words and Create Segments ---
            line_sorted = sorted(line, key=lambda w: w["x0"])
            text_segments = self._create_text_segments(line_sorted)
            line_bbox = self._calculate_line_bbox(line_sorted)

            # --- Get Line Text ---
            line_text = "".join(segment["text"] for segment in text_segments)

            # --- Analyze Font and Size Distribution ---
            size_widths = {}  # Map of size -> total width
            font_widths = {}  # Map of font -> total width
            total_line_width = 0

            for segment in text_segments:
                # Calculate segment width
                width = segment["bbox"]["x1"] - segment["bbox"]["x0"]
                total_line_width += width

                # Track size widths
                size = segment.get("rounded_size", 0)
                size_widths[size] = size_widths.get(size, 0) + width

                # Track font widths
                font = segment.get("font", "UnknownFont")
                font_widths[font] = font_widths.get(font, 0) + width

            # --- Calculate Predominant Values ---
            predominant_size = max(size_widths.items(), key=lambda x: x[1])[0] if size_widths else None
            predominant_font = max(font_widths.items(), key=lambda x: x[1])[0] if font_widths else None

            # --- Calculate Coverage Percentages ---
            predominant_size_coverage = (size_widths[predominant_size] / total_line_width * 100) if predominant_size and total_line_width > 0 else 0
            predominant_font_coverage = (font_widths[predominant_font] / total_line_width * 100) if predominant_font and total_line_width > 0 else 0

            # --- Calculate Gap Before ---
            if line_number == 1:
                gap_before = line_bbox.get("top", 0)  # Distance from top of page
            elif prev_line_bottom is not None and line_bbox.get("top") is not None:
                gap_before = line_bbox["top"] - prev_line_bottom
                if gap_before < 0:  # Handle overlapping lines
                    gap_before = 0
            else:
                gap_before = None

            # --- Create Line Object ---
            line_obj = {
                "line_number": line_number,
                "text": line_text,
                "bbox": line_bbox,
                "text_segments": text_segments,
                "predominant_size": predominant_size,
                "predominant_font": predominant_font,
                "predominant_size_coverage": round(predominant_size_coverage, 1),
                "predominant_font_coverage": round(predominant_font_coverage, 1),
                "gap_before": gap_before,
            }
            lines_json.append(line_obj)

            # Update previous line bottom for next iteration
            if line_bbox.get("bottom") is not None:
                prev_line_bottom = line_bbox["bottom"]

        # --- Calculate Gap After in Second Pass ---
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

        # --- Set Gap After for Last Line ---
        if lines_json:
            last_line = lines_json[-1]
            if last_line["bbox"].get("bottom") is not None and page_height is not None:
                gap_after = page_height - last_line["bbox"]["bottom"]
                if gap_after < 0:
                    gap_after = 0
                last_line["gap_after"] = gap_after
            else:
                last_line["gap_after"] = None

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
        """Create text segments from a line of words.
        
        Groups words into segments based on font, size, and orientation changes.
        Each segment represents a continuous text span with consistent properties.
        
        Args:
            line: List of word objects in a line
            
        Returns:
            List of text segment objects with properties and bounding boxes
        """
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
        """Create a text segment from a group of words.
        
        Args:
            words: List of word objects to combine into a segment
            
        Returns:
            Dictionary containing segment properties and bounding box
        """
        # Join words and trim whitespace while preserving original word texts
        segment_text = "".join(w["text"] for w in words).strip()
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
        """Calculate bounding box for a line of words.
        
        Args:
            line: List of word objects in a line
            
        Returns:
            Dictionary containing line bounding box coordinates
        """
        return {
            "x0": min(w["x0"] for w in line),
            "top": min(w["top"] for w in line),
            "x1": max(w["x1"] for w in line),
            "bottom": max(w["bottom"] for w in line),
        }

    def _combine_words(self, words: List[Dict]) -> List[List[Dict]]:
        """Combine consecutive words within x_tolerance.
        
        Groups words into lines based on vertical position and combines
        horizontally adjacent words within tolerance.
        
        Args:
            words: List of word objects to process
            
        Returns:
            List of lines, where each line is a list of combined word objects
        """
        # --- Group Words into Lines ---
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

        # --- Combine Words Within Lines ---
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
        """Generate comparison of extraction methods.
        
        Creates a line-by-line comparison of text extracted using different
        methods to help identify differences and potential issues.
        
        Args:
            results: Dictionary containing extraction results
            
        Returns:
            List of comparison entries, each containing text from all methods
        """
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
        """Save extraction results to files.
        
        Args:
            results: Dictionary containing extraction results
            output_dir: Directory to save results in
            base_name: Base name for output files
        """
        # Update FileHandler's output directory
        self.file_handler.output_dir = output_dir
        
        # Save full lines data
        self.file_handler.save_json(results["lines_json_by_page"], base_name, "full_lines")
        
        # Save lines data (already processed in _process_words)
        self.file_handler.save_json(results["lines_json_by_page"], base_name, "lines")
        
        # Save raw words data
        self.file_handler.save_json(results["raw_words_by_page"], base_name, "words")
        
        # Save comparison data
        self.file_handler.save_json(results["comparison"], base_name, "compare")
        
        # Generate and save metadata and statistics
        metadata = {
            "total_pages": len(results["lines_json_by_page"]),
            "total_lines": sum(len(page["lines"]) for page in results["lines_json_by_page"]),
            "total_words": sum(len(page["words"]) for page in results["raw_words_by_page"])
        }
        
        statistics = {
            "extraction_methods": {
                "raw_text": len(results["extract_text"]),
                "text_lines": len(results["extract_text_lines"]),
                "words_manual": len(results["extract_words_manual"])
            }
        }
        
        self.file_handler.save_json({"metadata": metadata, "statistics": statistics}, base_name, "info") 