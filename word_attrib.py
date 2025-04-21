import sys
import pdfplumber


def analyze_pdf_attributes(pdf_file):
    try:
        with pdfplumber.open(pdf_file) as pdf:
            attribute_counts = {}
            total_words = 0

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

            for page in pdf.pages:
                words = page.extract_words(extra_attrs=extra_attrs)
                total_words += len(words)

                for word in words:
                    for key in word.keys():
                        attribute_counts[key] = attribute_counts.get(key, 0) + 1

            # Print results
            print("Attribute Occurrence Counts:")
            for attr, count in sorted(attribute_counts.items()):
                print(f"- {attr}: {count} ({count / total_words:.1%} of words)")

            print(f"\nTotal words processed: {total_words}")

            # Show warning for attributes with less than 100% occurrence
            missing_attrs = [
                attr for attr in extra_attrs if attr not in attribute_counts
            ]
            if missing_attrs:
                print("\nWarning: These attributes were never found:")
                for attr in missing_attrs:
                    print(f"- {attr}")

    except FileNotFoundError:
        print(f"Error: File '{pdf_file}' not found")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_pdf.py <pdf-file>")
        sys.exit(1)

    analyze_pdf_attributes(sys.argv[1])
