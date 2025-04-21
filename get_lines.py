# Filename: extract_pdf_text_paged.py

import argparse
import json
import pdfplumber
import os
import sys  # Import sys to exit gracefully on error


def extract_text_from_pdf(pdf_path, start_page=None, stop_page=None):
    """
    Extracts text from a PDF file, page by page, line by line, within an
    optional page range.

    Args:
        pdf_path (str): The path to the input PDF file.
        start_page (int, optional): The first page number to process (1-based).
                                     Defaults to None (start from page 1).
        stop_page (int, optional): The last page number to process (1-based, inclusive).
                                    Defaults to None (process until the last page).

    Returns:
        list: A list of dictionaries, where each dictionary represents a page
              and contains the page number and a list of line dictionaries.
              Returns None if the file cannot be processed or if page range is invalid.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: Input file not found at {pdf_path}", file=sys.stderr)
        return None

    all_pages_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            # Validate and determine the page range to process
            actual_start_page = 1
            actual_stop_page = total_pages

            if start_page is not None:
                if 1 <= start_page <= total_pages:
                    actual_start_page = start_page
                else:
                    print(
                        f"Error: --start-page ({start_page}) is outside the valid range "
                        f"(1 to {total_pages}).",
                        file=sys.stderr,
                    )
                    return None

            if stop_page is not None:
                if actual_start_page <= stop_page <= total_pages:
                    actual_stop_page = stop_page
                elif stop_page < actual_start_page:
                    print(
                        f"Error: --stop-page ({stop_page}) cannot be less than "
                        f"--start-page ({actual_start_page}).",
                        file=sys.stderr,
                    )
                    return None
                else:  # stop_page > total_pages
                    print(
                        f"Error: --stop-page ({stop_page}) is outside the valid range "
                        f"(up to {total_pages}).",
                        file=sys.stderr,
                    )
                    return None

            print(
                f"Processing pages {actual_start_page} to {actual_stop_page} "
                f"(out of {total_pages} total) from {pdf_path}..."
            )

            # Iterate through the specified page range (0-based index for list access)
            for i in range(actual_start_page - 1, actual_stop_page):
                page = pdf.pages[i]
                page_number = i + 1  # 1-based page number for output

                # Extract text, preserving layout to some extent
                text = page.extract_text(x_tolerance=3, y_tolerance=3)

                page_lines = []
                if text:
                    # Split text into lines based on newline characters
                    lines = text.split("\n")
                    for line_num, line_text in enumerate(lines):
                        # Only add non-empty lines
                        if line_text.strip():
                            page_lines.append(
                                {"line_number": line_num + 1, "text": line_text.strip()}
                            )

                all_pages_data.append({"page_number": page_number, "lines": page_lines})

            print("Extraction complete.")
            return all_pages_data
    except Exception as e:
        print(f"Error processing PDF file {pdf_path}: {e}", file=sys.stderr)
        return None


def main():
    """
    Main function to parse arguments and orchestrate PDF text extraction.
    """
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF file (or a range of pages) and output as JSON.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # Show defaults in help
    )
    parser.add_argument("input_pdf", help="Path to the input PDF file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the output JSON file. If not specified, prints to stdout.",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--start-page",
        type=int,
        help="The first page number to process (1-based index). Processes from page 1 if not set.",
        default=None,  # Default is handled within the extraction function logic
    )
    parser.add_argument(
        "-e",
        "--stop-page",
        type=int,
        help="The last page number to process (1-based index, inclusive). Processes until the last page if not set.",
        default=None,  # Default is handled within the extraction function logic
    )

    args = parser.parse_args()

    extracted_data = extract_text_from_pdf(
        args.input_pdf, start_page=args.start_page, stop_page=args.stop_page
    )

    if extracted_data is None:
        sys.exit(1)  # Exit with an error code if extraction failed

    if extracted_data:
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(extracted_data, f, indent=4, ensure_ascii=False)
                print(f"Successfully wrote extracted text to {args.output}")
            except IOError as e:
                print(
                    f"Error writing to output file {args.output}: {e}", file=sys.stderr
                )
                sys.exit(1)  # Exit with an error code
        else:
            # Print to standard output if no output file is specified
            # Use ensure_ascii=False for broader character support
            print(json.dumps(extracted_data, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
