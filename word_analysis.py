import argparse
import json
import sys
import re


def process_page(page_name, words):
    # Extract page number from name
    page_number = int(re.search(r"\d+", page_name).group())

    # Add initial order and height
    for idx, word in enumerate(words, 1):
        word["initial_order"] = idx
        word["height"] = word["bounding_box"]["y1"] - word["bounding_box"]["y0"]

    # Sort by y0
    sorted_words = sorted(words, key=lambda x: x["bounding_box"]["y0"])

    # Initialize previous values with top of page (y=0)
    prev_y0 = 0.0
    prev_y1 = 0.0

    for word in sorted_words:
        # Calculate distances relative to previous element or top of page
        word["y0_dist"] = word["bounding_box"]["y0"] - prev_y0
        word["y_gap"] = word["bounding_box"]["y0"] - prev_y1

        # Update previous values for next iteration
        prev_y0 = word["bounding_box"]["y0"]
        prev_y1 = word["bounding_box"]["y1"]

    return {
        "original_name": page_name,
        "page_number": page_number,
        "words": sorted_words,
    }


def main():
    parser = argparse.ArgumentParser(description="Process document words metadata")
    parser.add_argument("input", help="Input JSON file")
    parser.add_argument("-o", "--output", help="Output JSON file")

    args = parser.parse_args()

    with open(args.input, "r") as f:
        input_data = json.load(f)

    output_data = {
        "pages": [
            process_page(page_name, page_data)
            for page_name, page_data in input_data.items()
        ]
    }

    # Sort pages by extracted page number
    output_data["pages"].sort(key=lambda x: x["page_number"])

    result = json.dumps(output_data, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
    else:
        print(result)


if __name__ == "__main__":
    main()
