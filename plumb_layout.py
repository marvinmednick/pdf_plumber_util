import argparse
import json
import os
import re
from collections import defaultdict, Counter


def parse_page_range(page_range, max_page, exclude_pages=None):
    if not page_range:
        pages = set(range(1, max_page + 1))
    else:
        pages = set()
        for part in page_range.split(","):
            if "-" in part:
                start, end = map(int, part.split("-"))
                pages.update(range(start, end + 1))
            else:
                pages.add(int(part))
    if exclude_pages:
        pages -= set(exclude_pages)
    return sorted(pages)


def is_line_empty(line):
    return not line.get("text", "").strip()


def find_margins(lines, page_width, page_height):
    if not lines:
        return {"left": None, "right": None, "top": None, "bottom": None}
    left = min(line["bbox"]["x0"] for line in lines)
    right = max(line["bbox"]["x1"] for line in lines)
    top = min(line["bbox"]["top"] for line in lines)
    bottom = max(line["bbox"]["bottom"] for line in lines)
    return {
        "left": left,
        "right": page_width - right,
        "top": top,
        "bottom": page_height - bottom,
    }


def round_font_size(size):
    try:
        return round(float(size) * 2) / 2
    except Exception:
        return size


def analyze_vertical_layout(lines, page_height, page_width):
    regions = []
    if not lines:
        return regions
    sorted_lines = sorted(lines, key=lambda l: l["bbox"]["top"])
    prev_bottom = 0
    for line in sorted_lines:
        top = line["bbox"]["top"]
        bottom = line["bbox"]["bottom"]
        x0 = line["bbox"]["x0"]
        x1 = line["bbox"]["x1"]
        left_indent = round(x0, 2)
        right_indent = round(page_width - x1, 2)
        unused = round(top - prev_bottom, 2)
        used = round(bottom - top, 2)
        fonts = set()
        for seg in line.get("text_segments", []):
            font = seg.get("font", "")
            rounded_size = seg.get("rounded_size", "")
            fonts.add(f"{font} {rounded_size}")
        preview = line.get("text", "")[:60].replace("\n", " ")
        regions.append(
            {
                "unused": unused,
                "used": used,
                "left_indent": left_indent,
                "right_indent": right_indent,
                "fonts": sorted(fonts),
                "preview": preview,
            }
        )
        prev_bottom = bottom
    # Add unused space after last line
    unused = round(page_height - prev_bottom, 2)
    regions.append(
        {
            "unused": unused,
            "used": None,
            "left_indent": None,
            "right_indent": None,
            "fonts": [],
            "preview": "",
        }
    )
    return regions


def display_vertical_layout_table(regions):
    FONT_NAME_WIDTH = 24
    FONT_SIZE_WIDTH = 6
    FONT_COL_WIDTH = FONT_NAME_WIDTH + FONT_SIZE_WIDTH + 1  # +1 for space

    print(f"{'Line':>5} {'Unused':>8} {'Used':>8} {'Left':>8} {'Right':>8} {'Font':<{FONT_NAME_WIDTH}} {'Size':>{FONT_SIZE_WIDTH}} {'Preview'}")
    line_num = 1
    for idx, reg in enumerate(regions):
        unused = f"{reg['unused']:.2f}" if reg["unused"] is not None else "-"
        used = f"{reg['used']:.2f}" if reg["used"] is not None else "-"
        left_indent = f"{reg['left_indent']:.2f}" if reg["left_indent"] is not None else "-"
        right_indent = f"{reg['right_indent']:.2f}" if reg["right_indent"] is not None else "-"
        fonts = reg["fonts"]
        preview = reg["preview"]
        is_last = idx == len(regions) - 1

        if not fonts and not is_last:
            print(f"{'':>5} {unused:>8} {used:>8} {left_indent:>8} {right_indent:>8} {'':<{FONT_NAME_WIDTH}} {'':>{FONT_SIZE_WIDTH}}")
            continue

        if is_last:
            # Last row: show line number, unused, and dashes for other fields
            print(f"{line_num:>5} {unused:>8} {'-':>8} {'-':>8} {'-':>8} {'-':<{FONT_NAME_WIDTH}} {'-':>{FONT_SIZE_WIDTH}}")
        else:
            for i, font in enumerate(fonts):
                if " " in font:
                    font_name, font_size = font.rsplit(" ", 1)
                else:
                    font_name, font_size = font, ""
                if i == 0:
                    print(f"{line_num:>5} {unused:>8} {used:>8} {left_indent:>8} {right_indent:>8} {font_name:<{FONT_NAME_WIDTH}.{FONT_NAME_WIDTH}} {font_size:>{FONT_SIZE_WIDTH}} {preview}")
                else:
                    print(f"{'':>5} {'':>8} {'':>8} {'':>8} {'':>8} {font_name:<{FONT_NAME_WIDTH}.{FONT_NAME_WIDTH}} {font_size:>{FONT_SIZE_WIDTH}}")
            line_num += 1


def collect_fonts(lines):
    font_counter = defaultdict(set)
    for line in lines:
        for seg in line.get("text_segments", []):
            font = seg.get("font", "")
            rounded_size = seg.get("rounded_size", "")
            rounded_size_str = f"{float(rounded_size):.1f}"
            font_counter[font].add(rounded_size_str)
    return font_counter


def round_to_quarter(val):
    try:
        return round(float(val) * 4) / 4
    except Exception:
        return val


def print_spacing_table(title, counter, by_indent=None):
    print(title)
    if by_indent is None:
        # Unused spacing table
        gt1 = []
        eq1 = []
        for val, count in sorted(counter.items(), key=lambda x: float(x[0])):
            if count > 1:
                gt1.append((val, count))
            else:
                eq1.append(val)
        for val, count in gt1:
            print(f"  {val:>6} {count}")
        if eq1:
            eq1_sorted = ", ".join(str(v) for v in sorted(eq1, key=float))
            print(f"  Occurred 1x: {eq1_sorted}")
        print()
    else:
        # Used spacing table with indent breakdown
        print(f"{'Line Spacing':>12} {'Indent':>10} {'Count':>8}")
        for used_size in sorted(counter.keys(), key=float):
            total_count = counter[used_size]
            indents = by_indent[used_size]
            indent_items = sorted(indents.items(), key=lambda x: float(x[0]))
            if len(indent_items) == 1:
                indent_val, indent_count = indent_items[0]
                print(f"{used_size:>12} {indent_val:>10} {indent_count:>8}")
                print()
            else:
                print(f"{used_size:>12} {'':>10} {total_count:>8}")
                gt1 = []
                eq1 = []
                for indent_val, indent_count in indent_items:
                    if indent_count > 1:
                        gt1.append((indent_val, indent_count))
                    else:
                        eq1.append(indent_val)
                for indent_val, indent_count in gt1:
                    print(f"{'':>12} {indent_val:>10} {indent_count:>8}")
                if eq1:
                    eq1_sorted = ", ".join(str(v) for v in sorted(eq1, key=float))
                    print(f"{'':>22} {'1x:':>10} {eq1_sorted}")
                print()


def main():
    parser = argparse.ArgumentParser(description="Analyze PDF layout from plumb3.py lines JSON")
    parser.add_argument("input_json", help="Input lines JSON file")
    parser.add_argument("--pages", type=str, default=None, help="Pages to process (e.g. 1-3,5)")
    parser.add_argument("--exclude-pages", type=str, default=None, help="Pages to exclude (e.g. 2,4)")
    parser.add_argument("--output", type=str, default="extract", help="Output directory")
    parser.add_argument("--text-view", action="store_true", help="Show vertical layout as plain text instead of table")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    max_page = max(page["page"] for page in data)
    exclude_pages = [int(x) for x in args.exclude_pages.split(",")] if args.exclude_pages else []
    pages_to_process = parse_page_range(args.pages, max_page, exclude_pages)

    os.makedirs(args.output, exist_ok=True)

    all_fonts = defaultdict(set)
    total_lines = 0
    total_unused = 0.0

    sorted_data = []
    filtered_data = []

    doc_used_counter = Counter()
    doc_unused_counter = Counter()
    doc_used_by_indent = defaultdict(Counter)  # used_size -> left_indent -> count

    for page in data:
        page_num = page["page"]
        if page_num not in pages_to_process:
            continue
        lines = [line for line in page["lines"] if not is_line_empty(line)]
        if not lines:
            continue

        # Get page dimensions from the JSON
        try:
            page_width = page["page_width"]
            page_height = page["page_height"]
        except KeyError:
            raise ValueError(f"Page {page_num} is missing 'page_width' or 'page_height' in the JSON.")
        
        print(f"\nPage {page_num} (width={page_width:.2f}, height={page_height:.2f})")
        margins = find_margins(lines, page_width, page_height)
        print(f"Margins: left={margins['left']:.2f}, right={margins['right']:.2f}, top={margins['top']:.2f}, bottom={margins['bottom']:.2f}")
        regions = analyze_vertical_layout(lines, page_height, page_width)
        if args.text_view:
            for reg in regions:
                if reg["used"] is not None:
                    print(f"{reg['unused']:.2f}-{reg['used']:.2f}: {reg['preview']}")
        else:
            display_vertical_layout_table(regions)
        # Font collection
        fonts = collect_fonts(lines)
        for font, sizes in fonts.items():
            all_fonts[font].update(sizes)
        total_lines += len(lines)
        total_unused += sum(reg["used"] for reg in regions if reg["used"] is not None)
        # Save sorted and filtered data
        sorted_lines = sorted(lines, key=lambda l: l["bbox"]["top"])
        sorted_data.append({"page": page_num, "lines": sorted_lines})
        filtered_data.append({"page": page_num, "lines": sorted_lines})

        # --- Collect per-page used/unused stats ---
        page_used_counter = Counter()
        page_unused_counter = Counter()
        page_used_by_indent = defaultdict(Counter)
        for reg in regions:
            if reg["used"] is not None:
                used_rounded = round_to_quarter(reg["used"])
                page_used_counter[used_rounded] += 1
                doc_used_counter[used_rounded] += 1
            if reg["unused"] is not None:
                unused_rounded = round_to_quarter(reg["unused"])
                page_unused_counter[unused_rounded] += 1
                doc_unused_counter[unused_rounded] += 1
            if reg["used"] is not None and reg["left_indent"] is not None:
                used_rounded = round_to_quarter(reg["used"])
                left_indent_rounded = round(reg["left_indent"])
                doc_used_by_indent[used_rounded][left_indent_rounded] += 1
                page_used_by_indent[used_rounded][left_indent_rounded] += 1

        # --- Print per-page stats ---
        print()
        print_spacing_table("  Used spacing (rounded to 0.25):", page_used_counter, by_indent=page_used_by_indent)
        print_spacing_table("  Unused spacing (rounded to 0.25):", page_unused_counter)

    # Save sorted and filtered JSON
    with open(os.path.join(args.output, "sorted_lines.json"), "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(args.output, "filtered_lines.json"), "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)

    # Font summary
    print("\nFont summary:")
    for font, sizes in all_fonts.items():
        # Only use the rounded sizes, sort and display
        try:
            rounded_sizes = sorted(float(s) for s in sizes)
            rounded_sizes_str = ", ".join(f"{s:.1f}" for s in rounded_sizes)
        except Exception:
            rounded_sizes_str = ", ".join(str(s) for s in sorted(sizes))
        print(f"  {font:<30}: {rounded_sizes_str}")

    # Summary
    print(f"\nSummary: {len(pages_to_process)} pages, {total_lines} lines, {len(all_fonts)} unique fonts, {total_unused:.2f} units unused vertical space.")

    print_spacing_table("\nDocument-wide used spacing (rounded to 0.25):", doc_used_counter, by_indent=doc_used_by_indent)
    print_spacing_table("Document-wide unused spacing (rounded to 0.25):", doc_unused_counter)


if __name__ == "__main__":
    main()

