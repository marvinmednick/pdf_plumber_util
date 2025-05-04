"""PDF visualization module for showing vertical spacing patterns."""

from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import re
import fitz  # PyMuPDF
from ..utils.constants import ROUND_TO_NEAREST_PT
from ..utils.helpers import round_to_nearest
import collections


class SpacingVisualizer:
    """Visualizes vertical spacing patterns in PDF documents."""
    
    # Default colors and patterns
    DEFAULT_COLORS = [
        'red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray',
        'darkred', 'darkblue', 'darkgreen', 'darkviolet', 'darkorange', 'saddlebrown', 'deeppink', 'dimgray',
        'crimson', 'navy', 'forestgreen', 'indigo', 'orangered', 'chocolate', 'hotpink', 'slategray'
    ]
    
    DEFAULT_PATTERNS = [
        'solid', 'dashed', 'dotted', 'dashdot',
        'solid', 'dashed', 'dotted', 'dashdot',
        'solid', 'dashed', 'dotted', 'dashdot',
        'solid', 'dashed', 'dotted', 'dashdot',
        'solid', 'dashed', 'dotted', 'dashdot',
        'solid', 'dashed', 'dotted', 'dashdot'
    ]
    
    def __init__(self):
        """Initialize the visualizer."""
        pass
    
    def _parse_range(self, range_str: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse a single range specification into min and max values."""
        range_str = range_str.strip()
        
        # Single value
        if re.match(r'^\d+(\.\d+)?$', range_str):
            val = float(range_str)
            return val, val
            
        # Less than or equal
        if re.match(r'^-(\d+(\.\d+)?)$', range_str):
            return None, float(range_str[1:])
            
        # Greater than or equal
        if re.match(r'^(\d+(\.\d+)?)-$', range_str):
            return float(range_str[:-1]), None
            
        # Range between two values
        range_match = re.match(r'^(\d+(\.\d+)?)-(\d+(\.\d+)?)$', range_str)
        if range_match:
            return float(range_match.group(1)), float(range_match.group(3))
            
        raise ValueError(f"Invalid range format: {range_str}")
    
    def parse_spacing_sizes(self, sizes_str: str) -> List[Tuple[Optional[float], Optional[float]]]:
        """Parse spacing sizes from command line argument.
        
        Returns a list of (min, max) tuples where:
        - None for min means no lower bound
        - None for max means no upper bound
        - min == max means exact value
        """
        if not sizes_str:
            return []
            
        ranges = []
        for range_str in sizes_str.split(','):
            try:
                min_val, max_val = self._parse_range(range_str.strip())
                ranges.append((min_val, max_val))
            except ValueError as e:
                raise ValueError(f"Invalid spacing sizes format: {e}")
                
        return ranges
    
    def matches_range(self, value: float, range_spec: Tuple[Optional[float], Optional[float]]) -> bool:
        """Check if a value matches a range specification."""
        min_val, max_val = range_spec
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True
    
    def parse_colors(self, colors_str: str) -> List[str]:
        """Parse colors from command line argument."""
        if not colors_str:
            return self.DEFAULT_COLORS
        return [c.strip() for c in colors_str.split(',')]
    
    def parse_patterns(self, patterns_str: str) -> List[str]:
        """Parse line patterns from command line argument."""
        if not patterns_str:
            return self.DEFAULT_PATTERNS
        return [p.strip() for p in patterns_str.split(',')]
    
    def create_visualization(
        self,
        input_pdf: str,
        output_pdf: str,
        spacing_ranges: List[Tuple[Optional[float], Optional[float]]],
        spacing_colors: List[str],
        spacing_patterns: List[str],
        lines_data: List[Dict]
    ) -> None:
        """Create a visualization PDF with spacing lines using PyMuPDF, and add a legend page."""
        print(f"[DEBUG] ROUND_TO_NEAREST_PT: {ROUND_TO_NEAREST_PT}")
        doc = fitz.open(input_pdf)
        color_map = self._get_color_map()

        # Collect all spacings
        spacing_occurrences = collections.Counter()
        spacing_lines = collections.defaultdict(list)  # spacing_value: list of (page_num, y)

        for page_data in lines_data:
            print(f"[DEBUG] Page {page_data['page']} has {len(page_data['lines'])} lines")
            page_num = page_data['page'] - 1
            lines = page_data['lines']
            if lines:
                print(f"[DEBUG] First line keys: {list(lines[0].keys())}")
                if page_num == 0:
                    for i, line in enumerate(lines):
                        print(f"[DEBUG] Line {i} keys: {list(line.keys())}")
            
            # Find the last non-blank line's bottom position
            prev_bottom = None
            for line in lines:
                bbox = line.get('bbox', {})
                top = bbox.get('top')
                bottom = bbox.get('bottom')
                text = line.get('text', '').strip()
                
                # Skip lines with no text content
                if not text:
                    continue
                    
                if top is None or bottom is None:
                    prev_bottom = bottom
                    continue
                    
                if prev_bottom is not None:
                    raw_spacing = top - prev_bottom
                    if raw_spacing > 0:
                        spacing = round_to_nearest(raw_spacing, ROUND_TO_NEAREST_PT)
                        print(f"[DEBUG] raw spacing: {raw_spacing}, rounded spacing: {spacing}, top: {top}")
                        for i, range_spec in enumerate(spacing_ranges):
                            print(f"[DEBUG] comparing {spacing} to {range_spec}")
                            if self.matches_range(spacing, range_spec):
                                print(f"[DEBUG] MATCHED: {spacing} in {range_spec}")
                                spacing_occurrences[spacing] += 1
                                spacing_lines[spacing].append((page_num, top))
                                break
                prev_bottom = bottom

        # Assign color/pattern to each unique spacing (cycling if needed)
        unique_spacings = sorted(spacing_occurrences.keys())
        spacing_to_color = {}
        spacing_to_pattern = {}
        for idx, spacing in enumerate(unique_spacings):
            spacing_to_color[spacing] = spacing_colors[idx % len(spacing_colors)]
            spacing_to_pattern[spacing] = spacing_patterns[idx % len(spacing_patterns)]

        # Draw lines for each spacing occurrence
        for spacing, occurrences in spacing_lines.items():
            color = color_map.get(spacing_to_color[spacing], (1, 0, 0))
            print(f"[TRACE] Drawing {len(occurrences)} lines for spacing {spacing} on pages {[p for p, _ in occurrences]}")
            for page_num, top in occurrences:
                page = doc[page_num]
                y_draw = top
                print(
                    f"[TRACE] Drawing line: page={page_num+1}, "
                    f"pdfplumber_top={top:.2f}, y_draw={y_draw:.2f}, "
                    f"spacing={spacing:.2f}, color={spacing_to_color[spacing]}, "
                    f"page_height={page.rect.height:.2f}"
                )
                if not (0 <= y_draw <= page.rect.height):
                    print(f"[WARNING] y_draw {y_draw} is out of bounds for page height {page.rect.height}")
                page.draw_line(
                    p1=(0, y_draw),
                    p2=(page.rect.width, y_draw),
                    color=color,
                    width=1.5
                )

        # Add a legend page for each unique spacing
        self._add_legend_page(doc, unique_spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences)

        doc.save(output_pdf)
    
    def _format_range(self, range_spec: Tuple[Optional[float], Optional[float]]) -> str:
        """Format a range specification for display."""
        min_val, max_val = range_spec
        if min_val is None and max_val is not None:
            return f"≤ {max_val:.2f}"
        elif min_val is not None and max_val is None:
            return f"≥ {min_val:.2f}"
        elif min_val == max_val:
            return f"{min_val:.2f}"
        else:
            return f"{min_val:.2f} - {max_val:.2f}"
    
    def _add_legend_page(self, doc, spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences):
        width = doc[0].rect.width
        height = doc[0].rect.height
        legend_page = doc.new_page(width=width, height=height)

        # Add title
        legend_page.insert_text(
            (72, 72),
            "Vertical Spacing Legend",
            fontsize=18,
            fontname="helv",
            color=(0, 0, 0)
        )

        # Add column headers
        y = 110
        legend_page.insert_text((72, y), "Spacing (pt)", fontsize=12, fontname="helv", color=(0, 0, 0))
        legend_page.insert_text((180, y), "Count", fontsize=12, fontname="helv", color=(0, 0, 0))
        legend_page.insert_text((250, y), "Color", fontsize=12, fontname="helv", color=(0, 0, 0))
        legend_page.insert_text((350, y), "Pattern", fontsize=12, fontname="helv", color=(0, 0, 0))
        y += 20

        # Add entries for each spacing
        color_map = self._get_color_map()
        for spacing in spacings:
            color_name = spacing_to_color[spacing]
            pattern = spacing_to_pattern[spacing]
            color_rgb = color_map.get(color_name, (1, 0, 0))
            count = spacing_occurrences[spacing]
            
            # Add spacing value
            legend_page.insert_text((72, y), f"{spacing:.2f}", fontsize=12, fontname="helv", color=(0, 0, 0))
            
            # Add count
            legend_page.insert_text((180, y), str(count), fontsize=12, fontname="helv", color=(0, 0, 0))
            
            # Add color name
            legend_page.insert_text((250, y), color_name, fontsize=12, fontname="helv", color=color_rgb)
            
            # Add pattern name
            legend_page.insert_text((350, y), pattern, fontsize=12, fontname="helv", color=(0, 0, 0))
            
            # Draw sample line
            legend_page.draw_line(
                p1=(420, y + 8),
                p2=(520, y + 8),
                color=color_rgb,
                width=2
            )
            
            y += 24

    def _get_color_map(self):
        """Return the color map for legend use."""
        return {
            'red': (1, 0, 0),
            'blue': (0, 0, 1),
            'green': (0, 1, 0),
            'purple': (0.5, 0, 0.5),
            'orange': (1, 0.65, 0),
            'brown': (0.6, 0.3, 0),
            'pink': (1, 0.75, 0.8),
            'gray': (0.5, 0.5, 0.5),
            'darkred': (0.55, 0, 0),
            'darkblue': (0, 0, 0.55),
            'darkgreen': (0, 0.39, 0),
            'darkviolet': (0.58, 0, 0.83),
            'darkorange': (1, 0.55, 0),
            'saddlebrown': (0.55, 0.27, 0.07),
            'deeppink': (1, 0.08, 0.58),
            'dimgray': (0.41, 0.41, 0.41),
            'crimson': (0.86, 0.08, 0.24),
            'navy': (0, 0, 0.5),
            'forestgreen': (0.13, 0.55, 0.13),
            'indigo': (0.29, 0, 0.51),
            'orangered': (1, 0.27, 0),
            'chocolate': (0.82, 0.41, 0.12),
            'hotpink': (1, 0.41, 0.71),
            'slategray': (0.44, 0.5, 0.56),
        } 