import argparse
import json
import pdfplumber
from typing import Dict, List
import re
import os


def extract_three_methods(pdf_path: str, y_tolerance: int = 5, x_tolerance: int = 5, words_file: str = None) -> Dict:
    """Extract text using three different methods and return comparison."""
    results = {
        "extract_text": [],
        "extract_text_lines": [],
        "extract_words_manual": [],
        "comparison": [],
        "lines_json_by_page": [],
        "raw_words_by_page": [],
    }

    # List of required attributes for word sorting
    extra_attrs = ["x0", "y0", "x1", "y1", "text", "fontname", "size", "top", "adv"]

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Method 1: extract_text()
            text_raw = page.extract_text()
            results["extract_text"].append(
                {
                    "page": page_num + 1,
                    "content": text_raw.split("\n") if text_raw else [],
                }
            )

            # Method 2: extract_text_lines()
            text_lines = page.extract_text_lines(layout=True)
            results["extract_text_lines"].append(
                {
                    "page": page_num + 1,
                    "content": [line["text"] for line in text_lines] if text_lines else [],
                }
            )

            # Method 3: extract_words() with manual alignment and combining consecutive words
            words = page.extract_words(
                x_tolerance_ratio=0.3,
                use_text_flow=True,
                keep_blank_chars=True,
                extra_attrs=extra_attrs
            )
            if words:
                # 1. Sort words by 'top' (vertical position)
                sorted_words = sorted(words, key=lambda w: w["top"])

                # 2. Group words into lines by 'top' and y_tolerance
                lines = []
                current_line = []
                prev_top = sorted_words[0]["top"]

                for word in sorted_words:
                    if abs(word["top"] - prev_top) > y_tolerance:
                        lines.append(current_line)
                        current_line = [word]
                        prev_top = word["top"]
                    else:
                        current_line.append(word)
                if current_line:
                    lines.append(current_line)

                # 3. For each line, sort by x0 and combine words
                combined_lines = []
                line_bboxes = []
                lines_json = []

                for line_number, line in enumerate(lines, 1):
                    line_sorted = sorted(line, key=lambda w: w["x0"])
                    # Combine consecutive words within x_tolerance for full line text
                    combined_line = []
                    current_word = line_sorted[0].copy()
                    for next_word in line_sorted[1:]:
                        if abs(next_word["x0"] - current_word["x1"]) <= x_tolerance:
                            current_word["text"] += f"{next_word['text']}"
                            current_word["x1"] = next_word["x1"]
                        else:
                            combined_line.append(current_word)
                            current_word = next_word.copy()
                    combined_line.append(current_word)
                    combined_lines.append(combined_line)

                    # Calculate bounding box for the line
                    line_bbox = {
                        "x0": min(w["x0"] for w in line_sorted),
                        "top": min(w["top"] for w in line_sorted),
                        "x1": max(w["x1"] for w in line_sorted),
                        "bottom": max(w["bottom"] for w in line_sorted),
                    }
                    line_bboxes.append((line_sorted, line_bbox))

                    # Split line into text segments by font, size, direction
                    text_segments = []
                    seg_start = 0
                    for i in range(1, len(line_sorted)):
                        prev = line_sorted[i - 1]
                        curr = line_sorted[i]
                        if (
                            prev.get("fontname") != curr.get("fontname")
                            or prev.get("size") != curr.get("size")
                            or prev.get("upright", True) != curr.get("upright", True)
                        ):
                            segment_words = line_sorted[seg_start:i]
                            segment_text = "".join(w["text"] for w in segment_words)
                            segment_bbox = {
                                "x0": min(w["x0"] for w in segment_words),
                                "top": min(w["top"] for w in segment_words),
                                "x1": max(w["x1"] for w in segment_words),
                                "bottom": max(w["bottom"] for w in segment_words),
                            }
                            text_segments.append(
                                {
                                    "font": prev.get("fontname"),
                                    "reported_size": prev.get("size"),
                                    "rounded_size": round(float(prev.get("size", "0")) * 2) / 2,
                                    "direction": "upright" if prev.get("upright", True) else "rotated",
                                    "text": segment_text,
                                    "bbox": segment_bbox,
                                }
                            )
                            seg_start = i
                    # Add last segment
                    segment_words = line_sorted[seg_start:]
                    if segment_words:
                        last = segment_words[0]
                        segment_text = "".join(w["text"] for w in segment_words)
                        segment_bbox = {
                            "x0": min(w["x0"] for w in segment_words),
                            "top": min(w["top"] for w in segment_words),
                            "x1": max(w["x1"] for w in segment_words),
                            "bottom": max(w["bottom"] for w in segment_words),
                        }
                        text_segments.append(
                            {
                                "font": last.get("fontname"),
                                "reported_size": last.get("size"),
                                "rounded_size": round(float(last.get("size", "0")) * 2) / 2,
                                "direction": "upright" if last.get("upright", True) else "rotated",
                                "text": segment_text,
                                "bbox": segment_bbox,
                            }
                        )

                    # Full line text (all combined words, space separated)
                    full_line_text = " ".join(w["text"] for w in combined_line)

                    # Store in new structure
                    lines_json.append(
                        {
                            "line_number": line_number,
                            "text": full_line_text,
                            "bbox": line_bbox,
                            "text_segments": text_segments,
                        }
                    )

                # 4. Write words and lines to file in one operation
                if words_file:
                    with open(words_file, "w", encoding="utf-8") as wf:
                        wf.write("=== Words (raw, sorted by top) ===\n")
                        for word in sorted_words:
                            word_out = word.copy()
                            word_out["page"] = page_num + 1
                            wf.write(json.dumps(word_out, indent=2) + "\n")
                        wf.write("\n=== Lines (grouped, with text segments) ===\n")
                        json.dump(
                            {
                                "page": page_num + 1,
                                "lines": lines_json,
                            },
                            wf,
                            indent=2,
                            ensure_ascii=False,
                        )
                        wf.write("\n\n")

                results["extract_words_manual"].append(
                    {
                        "page": page_num + 1,
                        "content": [" ".join(w["text"] for w in line) for line in combined_lines],
                    }
                )
                # Save raw words for this page
                results["raw_words_by_page"].append({
                    "page": page_num + 1,
                    "words": [dict(word, page=page_num + 1) for word in sorted_words]
                })
                # Save lines_json for this page
                results["lines_json_by_page"].append({
                    "page": page_num + 1,
                    "lines": lines_json,
                })
            else:
                results["raw_words_by_page"].append({
                    "page": page_num + 1,
                    "words": []
                })
                results["lines_json_by_page"].append({
                    "page": page_num + 1,
                    "lines": [],
                })

        # Generate comparison
        for page_idx in range(len(results["extract_text"])):
            page_num = page_idx + 1

            # Remove blank lines and normalize spaces for each method's content
            text_content = [normalize_line(line) for line in results["extract_text"][page_idx]["content"] if line.strip()]
            lines_content = [normalize_line(line) for line in results["extract_text_lines"][page_idx]["content"] if line.strip()]
            words_content = [normalize_line(line) for line in results["extract_words_manual"][page_idx]["content"] if line.strip()]

            methods = {
                "text": text_content,
                "lines": lines_content,
                "words": words_content,
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

                results["comparison"].append(comparison_entry)

    return results


def normalize_line(line):
    return re.sub(r'\s+', ' ', line).strip()


def main():
    parser = argparse.ArgumentParser(description="PDF Text Extraction Comparison Tool")
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="extract",
        help="Directory to save output files (default: extract)",
    )
    parser.add_argument(
        "--basename",
        type=str,
        default=None,
        help="Base name for output files (default: input file base name)",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=float,
        default=5,
        help="Y-axis tolerance for word grouping (default: 5)",
    )
    parser.add_argument(
        "-x",
        "--x_tolerance",
        type=float,
        default=2,
        help="X-axis tolerance for combining consecutive words (default: 3)",
    )
    parser.add_argument(
        "--save-words",
        action="store_true",
        help="If set, save raw words to <basename>_words.json",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="If set, save comparison of three methods to <basename>_compare.json",
    )

    args = parser.parse_args()

    # Determine base name
    if args.basename:
        base = args.basename
    else:
        base = os.path.splitext(os.path.basename(args.input_pdf))[0]

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Run extraction
    results = extract_three_methods(args.input_pdf, args.tolerance, args.x_tolerance)

    # Save lines_json_by_page to <output_dir>/<basename>_lines.json
    lines_path = os.path.join(args.output_dir, f"{base}_lines.json")
    with open(lines_path, "w", encoding="utf-8") as f:
        json.dump(results["lines_json_by_page"], f, indent=2, ensure_ascii=False)

    # Save raw_words_by_page to <output_dir>/<basename>_words.json if requested
    if args.save_words:
        words_path = os.path.join(args.output_dir, f"{base}_words.json")
        with open(words_path, "w", encoding="utf-8") as f:
            json.dump(results["raw_words_by_page"], f, indent=2, ensure_ascii=False)

    # Save comparison to <output_dir>/<basename>_compare.json if requested
    if args.compare:
        # Remove blank lines and normalize for comparison
        for page_idx in range(len(results["extract_text"])):
            text_content = [normalize_line(line) for line in results["extract_text"][page_idx]["content"] if line.strip()]
            lines_content = [normalize_line(line) for line in results["extract_text_lines"][page_idx]["content"] if line.strip()]
            words_content = [normalize_line(line) for line in results["extract_words_manual"][page_idx]["content"] if line.strip()]
            methods = {
                "text": text_content,
                "lines": lines_content,
                "words": words_content,
            }
            max_lines = max(len(methods["text"]), len(methods["lines"]), len(methods["words"]))
            for line_idx in range(max_lines):
                comparison_entry = {
                    "page": page_idx + 1,
                    "line": line_idx + 1,
                    "methods": {},
                }
                for method in methods:
                    try:
                        content = methods[method][line_idx]
                        comparison_entry["methods"][method] = content
                    except IndexError:
                        comparison_entry["methods"][method] = None
                results["comparison"].append(comparison_entry)
        compare_path = os.path.join(args.output_dir, f"{base}_compare.json")
        with open(compare_path, "w", encoding="utf-8") as f:
            json.dump(results["comparison"], f, indent=2, ensure_ascii=False)

    # Restore metadata and statistics
    metadata = {
        "input_file": args.input_pdf,
        "y_tolerance": args.tolerance,
        "x_tolerance": args.x_tolerance,
    }
    statistics = {
        "page_count": len(results["extract_text"]),
        "avg_lines_per_page": {
            "extract_text": sum(len(p["content"]) for p in results["extract_text"]) / len(results["extract_text"]),
            "extract_text_lines": sum(len(p["content"]) for p in results["extract_text_lines"]) / len(results["extract_text_lines"]),
            "extract_words_manual": sum(len(p["content"]) for p in results["extract_words_manual"]) / len(results["extract_words_manual"]),
        },
        "total_differences": (
            sum(
                1
                for entry in results["comparison"]
                if len(set(v for v in entry["methods"].values() if v is not None)) > 1
            ) if "comparison" in results and results["comparison"] else None
        ),
    }
    info_path = os.path.join(args.output_dir, f"{base}_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "statistics": statistics}, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
