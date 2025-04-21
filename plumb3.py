import argparse
import json
import pdfplumber
from typing import Dict, List


def extract_three_methods(
    pdf_path: str, y_tolerance: int = 5, x_tolerance: int = 5, words_file: str = None
) -> Dict:
    """Extract text using three different methods and return comparison."""
    results = {
        "extract_text": [],
        "extract_text_lines": [],
        "extract_words_manual": [],
        "comparison": [],
    }

    # List of required attributes for word sorting
    extra_attrs = ["x0", "y0", "x1", "y1", "text", "fontname", "size", "top"]

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
                    "content": [line["text"] for line in text_lines]
                    if text_lines
                    else [],
                }
            )

            # Method 3: extract_words() with manual alignment and combining consecutive words
            words = page.extract_words(extra_attrs=extra_attrs)
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
                for line in lines:
                    line_sorted = sorted(line, key=lambda w: w["x0"])
                    # Combine consecutive words within x_tolerance
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

                # 4. Write words and lines to file in one operation
                if words_file:
                    with open(words_file, "w", encoding="utf-8") as wf:
                        # Write all sorted words
                        for word in sorted_words:
                            word_out = word.copy()
                            word_out["page"] = page_num + 1
                            wf.write(json.dumps(word_out) + "\n")
                        # Write all lines with bounding boxes
                        for line_sorted, line_bbox in line_bboxes:
                            line_texts = [w["text"] for w in line_sorted]
                            wf.write(
                                json.dumps(
                                    {
                                        "page": page_num + 1,
                                        "line_texts": line_texts,
                                        "bounding_box": line_bbox,
                                    }
                                )
                                + "\n"
                            )

                # 5. Prepare extract_words_manual output as before
                results["extract_words_manual"].append(
                    {
                        "page": page_num + 1,
                        "content": [
                            " ".join(w["text"] for w in line) for line in combined_lines
                        ],
                    }
                )

        # Generate comparison
        for page_idx in range(len(results["extract_text"])):
            page_num = page_idx + 1
            methods = {
                "text": results["extract_text"][page_idx]["content"],
                "lines": results["extract_text_lines"][page_idx]["content"],
                "words": results["extract_words_manual"][page_idx]["content"],
            }

            max_lines = max(
                len(methods["text"]), len(methods["lines"]), len(methods["words"])
            )

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


def main():
    parser = argparse.ArgumentParser(description="PDF Text Extraction Comparison Tool")
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument(
        "-o",
        "--output",
        type=argparse.FileType("w"),
        default="-",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=int,
        default=5,
        help="Y-axis tolerance for word grouping (default: 5)",
    )
    parser.add_argument(
        "-x",
        "--x_tolerance",
        type=int,
        default=2,
        help="X-axis tolerance for combining consecutive words (default: 3)",
    )
    parser.add_argument(
        "--words-file",
        type=str,
        default=None,
        help="Optional: Output file to write all words (one JSON object per line)",
    )

    args = parser.parse_args()

    results = extract_three_methods(
        args.input_pdf, args.tolerance, args.x_tolerance, args.words_file
    )

    # Generate summary statistics
    stats = {
        "page_count": len(results["extract_text"]),
        "avg_lines_per_page": {
            "extract_text": sum(len(p["content"]) for p in results["extract_text"])
            / len(results["extract_text"]),
            "extract_text_lines": sum(
                len(p["content"]) for p in results["extract_text_lines"]
            )
            / len(results["extract_text_lines"]),
            "extract_words_manual": sum(
                len(p["content"]) for p in results["extract_words_manual"]
            )
            / len(results["extract_words_manual"]),
        },
        "total_differences": sum(
            1
            for entry in results["comparison"]
            if len(set(entry["methods"].values())) > 1
        ),
    }

    output = {
        "metadata": {
            "input_file": args.input_pdf,
            "y_tolerance": args.tolerance,
            "x_tolerance": args.x_tolerance,
        },
        "statistics": stats,
        "detailed_results": results,
    }

    json.dump(output, args.output, indent=2)
    args.output.write("\n")


if __name__ == "__main__":
    main()
