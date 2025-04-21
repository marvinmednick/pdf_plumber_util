import argparse
import json
import sys
import pdfplumber
from tqdm import tqdm


def make_json_serializable(obj):
    """
    Recursively convert non-serializable objects (like PSLiteral) to strings.
    """
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(make_json_serializable(v) for v in obj)
    elif hasattr(obj, "__dict__"):
        return str(obj)
    elif not isinstance(obj, (str, int, float, bool, type(None))):
        return str(obj)
    else:
        return obj


def main():
    parser = argparse.ArgumentParser(description="Extract PDF non-text elements")
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("--output", "-o", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--edges", action="store_true", help="Include edge decomposition (rect_edges, curve_edges, lines)")
    parser.add_argument("--annotations", action="store_true", help="Include PDF annotations")
    args = parser.parse_args()

    results = []

    with pdfplumber.open(args.input) as pdf:
        total_pages = len(pdf.pages)
        with tqdm(total=total_pages, desc="Processing Pages", unit="page") as pbar:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Process images
                for img in page.images:
                    results.append(
                        {
                            "type": "image",
                            "page": page_num,
                            "bbox": {"x0": img.get("x0"), "y0": img.get("top"), "x1": img.get("x1"), "y1": img.get("bottom")},
                            "width": img.get("width", None),
                            "height": img.get("height", None),
                            "metadata": {"name": img.get("name", None), "colorspace": img.get("colorspace", None), "bits": img.get("bits", None), "imagemask": img.get("imagemask", None)},
                        }
                    )

                # Process annotations (optional)
                if args.annotations:
                    for annot in page.annots:
                        subtype = str(annot.get("subtype", "") or "")
                        content = str(annot.get("content", "") or "")
                        title = str(annot.get("title", "") or "")
                        subject = str(annot.get("subject", "") or "")

                        # Skip annotations with no meaningful data
                        if not any([subtype.strip(), content.strip(), title.strip(), subject.strip()]):
                            continue

                        results.append(
                            {
                                "type": "annotation",
                                "subtype": subtype,
                                "page": page_num,
                                "bbox": {"x0": annot.get("x0"), "y0": annot.get("top"), "x1": annot.get("x1"), "y1": annot.get("bottom")},
                                "content": content,
                                "metadata": {"title": title, "subject": subject},
                            }
                        )

                # Process hyperlinks (always included)
                for link in page.hyperlinks:
                    results.append({"type": "hyperlink", "page": page_num, "uri": link["uri"], "bbox": {"x0": link["x0"], "y0": link["top"], "x1": link["x1"], "y1": link["bottom"]}})

                # Process vector shapes (lines, curves, rects)
                for obj_type in ["lines", "curves", "rects"]:
                    for obj in getattr(page, obj_type, []):
                        results.append(
                            {
                                "type": obj_type[:-1],  # Singularize
                                "page": page_num,
                                "bbox": {"x0": obj.get("x0"), "y0": obj.get("top"), "x1": obj.get("x1"), "y1": obj.get("bottom")},
                                "metadata": {"linewidth": obj.get("linewidth", None), "stroke": obj.get("stroke", None), "fill": obj.get("fill", None)},
                            }
                        )

                # Process edges (optional)
                if args.edges:
                    for edge in page.edges:
                        results.append(
                            {
                                "type": "edge",
                                "page": page_num,
                                "bbox": {"x0": edge.get("x0"), "y0": edge.get("top"), "x1": edge.get("x1"), "y1": edge.get("bottom")},
                                "metadata": {
                                    "linewidth": edge.get("linewidth", None),
                                    "stroke": edge.get("stroke", None),
                                    "fill": edge.get("fill", None),
                                    "source": edge.get("object_type", "unknown"),
                                },
                            }
                        )

                pbar.update(1)

        sorted_results = sorted(results, key=lambda x: x["bbox"]["y0"])
        serializable_results = make_json_serializable(sorted_results)

        # Output handling
        if args.output == "-":
            json.dump(serializable_results, sys.stdout, indent=4)
        else:
            with open(args.output, "w") as f:
                json.dump(serializable_results, f, indent=4)


if __name__ == "__main__":
    main()
