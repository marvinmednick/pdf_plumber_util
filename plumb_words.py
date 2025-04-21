import sys
import pdfplumber
import json


def extract_words_metadata(pdf_file):
    # List of all possible attributes to request
    extra_attrs = [
        "fontname",
        "size",
        "adv",
        "upright",
        "height",
        "width",
        "x0",
        "x1",
        "y0",
        "y1",
        "top",
        "bottom",
        "doctop",
        "matrix",
    ]
    try:
        with pdfplumber.open(pdf_file) as pdf:
            pages_data = {
                f"Page {i + 1}": [
                    {
                        "text": word["text"],
                        "bounding_box": {
                            "x0": word["x0"],
                            "y0": word["top"],
                            "x1": word["x1"],
                            "y1": word["bottom"],
                        },
                        "font": word.get("fontname"),
                        "size": word["size"],
                        "orientation": word["upright"],
                        "position": {
                            "doctop": word["doctop"],
                            "direction": word["direction"],
                        },
                    }
                    for word in page.extract_words(extra_attrs=extra_attrs)
                ]
                for i, page in enumerate(pdf.pages)
            }

        print(json.dumps(pages_data, indent=4))
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <pdf_file>")
    else:
        extract_words_metadata(sys.argv[1])
