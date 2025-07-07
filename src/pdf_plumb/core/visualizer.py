"""PDF visualization module for showing vertical spacing patterns."""

from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import re
import fitz  # PyMuPDF
from ..config import get_config
from ..utils.helpers import round_to_nearest
from ..utils.file_handler import FileHandler
import collections
from ..core.utils.logging import LogManager


class SpacingVisualizer:
    """Visualizes vertical spacing patterns in PDF documents."""
    
    def __init__(self):
        """Initialize the visualizer with configuration."""
        self.config = get_config()
        
        # Use colors from config
        self.DEFAULT_COLORS = self.config.default_spacing_colors
        self.DEFAULT_PATTERNS = self.config.default_spacing_patterns
    
    # Pattern definitions with varying line widths and dash patterns
    # Format: (pattern_name, line_width, dash_pattern)
    PATTERN_DEFINITIONS = [
        # Solid lines with increasing thickness
        ('solid', 1.0, [(1000.0, 0.0)]),
        ('solid', 1.5, [(1000.0, 0.0)]),
        ('solid', 2.0, [(1000.0, 0.0)]),
        ('solid', 2.5, [(1000.0, 0.0)]),
        ('solid', 3.0, [(1000.0, 0.0)]),
        ('solid', 3.5, [(1000.0, 0.0)]),
        ('solid', 4.0, [(1000.0, 0.0)]),
        ('solid', 4.5, [(1000.0, 0.0)]),
        ('solid', 5.0, [(1000.0, 0.0)]),
        ('solid', 5.5, [(1000.0, 0.0)]),
        ('solid', 6.0, [(1000.0, 0.0)]),
        
        # Dashed lines with varying thickness and dash lengths
        ('dashed', 1.0, [(50.0, 20.0)]),
        ('dashed', 1.5, [(50.0, 20.0)]),
        ('dashed', 2.0, [(50.0, 20.0)]),
        ('dashed', 2.5, [(50.0, 20.0)]),
        ('dashed', 3.0, [(50.0, 20.0)]),
        ('dashed', 3.5, [(50.0, 20.0)]),
        ('dashed', 4.0, [(50.0, 20.0)]),
        ('dashed', 4.5, [(50.0, 20.0)]),
        ('dashed', 5.0, [(50.0, 20.0)]),
        ('dashed', 5.5, [(50.0, 20.0)]),
        ('dashed', 6.0, [(50.0, 20.0)]),
        
        # Dotted lines with varying thickness and dot spacing
        ('dotted', 1.0, [(10.0, 30.0)]),
        ('dotted', 1.5, [(10.0, 30.0)]),
        ('dotted', 2.0, [(10.0, 30.0)]),
        ('dotted', 2.5, [(10.0, 30.0)]),
        ('dotted', 3.0, [(10.0, 30.0)]),
        ('dotted', 3.5, [(10.0, 30.0)]),
        ('dotted', 4.0, [(10.0, 30.0)]),
        ('dotted', 4.5, [(10.0, 30.0)]),
        ('dotted', 5.0, [(10.0, 30.0)]),
        ('dotted', 5.5, [(10.0, 30.0)]),
        ('dotted', 6.0, [(10.0, 30.0)]),
        
        # Dash-dot lines with varying thickness
        ('dashdot', 1.0, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 1.5, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 2.0, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 2.5, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 3.0, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 3.5, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 4.0, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 4.5, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 5.0, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 5.5, [(50.0, 20.0), (10.0, 20.0)]),
        ('dashdot', 6.0, [(50.0, 20.0), (10.0, 20.0)]),
        
        # Additional pattern variations
        ('dashed', 1.0, [(30.0, 15.0)]),  # Shorter dashes
        ('dashed', 1.5, [(30.0, 15.0)]),
        ('dashed', 2.0, [(30.0, 15.0)]),
        ('dashed', 2.5, [(30.0, 15.0)]),
        ('dashed', 3.0, [(30.0, 15.0)]),
        ('dashed', 3.5, [(30.0, 15.0)]),
        ('dashed', 4.0, [(30.0, 15.0)]),
        ('dashed', 4.5, [(30.0, 15.0)]),
        ('dashed', 5.0, [(30.0, 15.0)]),
        ('dashed', 5.5, [(30.0, 15.0)]),
        ('dashed', 6.0, [(30.0, 15.0)]),
        
        # More dotted variations
        ('dotted', 1.0, [(5.0, 20.0)]),  # Smaller dots
        ('dotted', 1.5, [(5.0, 20.0)]),
        ('dotted', 2.0, [(5.0, 20.0)]),
        ('dotted', 2.5, [(5.0, 20.0)]),
        ('dotted', 3.0, [(5.0, 20.0)]),
        ('dotted', 3.5, [(5.0, 20.0)]),
        ('dotted', 4.0, [(5.0, 20.0)]),
        ('dotted', 4.5, [(5.0, 20.0)]),
        ('dotted', 5.0, [(5.0, 20.0)]),
        ('dotted', 5.5, [(5.0, 20.0)]),
        ('dotted', 6.0, [(5.0, 20.0)]),
        
        # More dash-dot variations
        ('dashdot', 1.0, [(40.0, 15.0), (5.0, 15.0)]),  # Shorter segments
        ('dashdot', 1.5, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 2.0, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 2.5, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 3.0, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 3.5, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 4.0, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 4.5, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 5.0, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 5.5, [(40.0, 15.0), (5.0, 15.0)]),
        ('dashdot', 6.0, [(40.0, 15.0), (5.0, 15.0)])
    ]
    
    def __init__(self, output_dir: str = "output", debug_level: str = 'INFO'):
        """Initialize the visualizer.
        
        Args:
            output_dir: Directory to save output files
            debug_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.file_handler = FileHandler(output_dir=output_dir, debug_level=debug_level)
        self.logger = LogManager(debug_level)
    
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
            return self.PATTERN_DEFINITIONS
        return [p.strip() for p in patterns_str.split(',')]
    
    def _draw_patterned_line(self, page, y: float, pattern_def: Tuple[str, float, List[Tuple[float, float]]], color: Tuple[float, float, float]) -> None:
        """Draw a horizontal line with the specified pattern.
        
        Args:
            page: PyMuPDF page object
            y: Y-coordinate for the line
            pattern_def: Tuple of (pattern_name, line_width, dash_pattern)
            color: RGB color tuple
        """
        try:
            pattern_name, width, segments = pattern_def
            self.logger.debug(f"Drawing {pattern_name} line at y={y} with width={width}")
            
            # Draw each segment
            x = 0
            page_width = page.rect.width
            
            while x < page_width:
                for seg_len, gap_len in segments:
                    try:
                        # Calculate actual segment length (don't exceed page width)
                        actual_len = min(seg_len, page_width - x)
                        if actual_len > 0:
                            # Draw the segment
                            page.draw_line(
                                p1=(x, y),
                                p2=(x + actual_len, y),
                                color=color,
                                width=width
                            )
                        x += actual_len + gap_len
                        if x >= page_width:
                            break
                    except Exception as e:
                        self.logger.error(f"Error drawing segment at x={x}: {str(e)}")
                        raise
        except Exception as e:
            self.logger.error(f"Error in _draw_patterned_line: {str(e)}")
            raise

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
        try:
            doc = fitz.open(input_pdf)
            color_map = self._get_color_map()

            # Collect all spacings
            spacing_occurrences = collections.Counter()
            spacing_lines = collections.defaultdict(list)  # spacing_value: list of (page_num, y)

            for page_data in lines_data:
                page_num = page_data['page'] - 1
                lines = page_data['lines']
                page = doc[page_num]
                page_height = page.rect.height
                
                # Find the first and last non-blank lines
                first_line = None
                last_line = None
                for line in lines:
                    if line.get('text', '').strip():
                        if first_line is None:
                            first_line = line
                        last_line = line
                
                # Add top page gap if first line exists
                if first_line:
                    top_gap = first_line['bbox']['top']
                    if top_gap > 0:
                        spacing = round_to_nearest(top_gap, self.config.round_to_nearest_pt)
                        for i, range_spec in enumerate(spacing_ranges):
                            if self.matches_range(spacing, range_spec):
                                spacing_occurrences[spacing] += 1
                                spacing_lines[spacing].append((page_num, top_gap))
                                break
                
                # Process gaps between lines
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
                            spacing = round_to_nearest(raw_spacing, self.config.round_to_nearest_pt)
                            for i, range_spec in enumerate(spacing_ranges):
                                if self.matches_range(spacing, range_spec):
                                    spacing_occurrences[spacing] += 1
                                    spacing_lines[spacing].append((page_num, top))
                                    break
                    prev_bottom = bottom
                
                # Add bottom page gap if last line exists
                if last_line:
                    bottom_gap = page_height - last_line['bbox']['bottom']
                    if bottom_gap > 0:
                        spacing = round_to_nearest(bottom_gap, self.config.round_to_nearest_pt)
                        for i, range_spec in enumerate(spacing_ranges):
                            if self.matches_range(spacing, range_spec):
                                spacing_occurrences[spacing] += 1
                                spacing_lines[spacing].append((page_num, last_line['bbox']['bottom']))
                                break

            # Sort spacings by frequency (most frequent first)
            sorted_spacings = sorted(spacing_occurrences.items(), key=lambda x: x[1], reverse=True)
            
            # Log the spacings we found
            self.logger.info(f"Found {len(sorted_spacings)} unique spacing values")
            for spacing, count in sorted_spacings:
                self.logger.info(f"Spacing {spacing:.2f} occurs {count} times")
            
            # Assign colors and patterns based on frequency
            spacing_to_color = {}
            spacing_to_pattern = {}
            
            for idx, (spacing, _) in enumerate(sorted_spacings):
                try:
                    if idx < len(self.DEFAULT_COLORS):
                        spacing_to_color[spacing] = self.DEFAULT_COLORS[idx]
                        self.logger.debug(f"Assigned color {self.DEFAULT_COLORS[idx]} to spacing {spacing:.2f}")
                    else:
                        self.logger.info(f"No color available for spacing {spacing:.2f} (index {idx})")
                        spacing_to_color[spacing] = self.DEFAULT_COLORS[0]  # Fallback to first color
                        
                    if idx < len(self.PATTERN_DEFINITIONS):
                        spacing_to_pattern[spacing] = self.PATTERN_DEFINITIONS[idx]
                        self.logger.debug(f"Assigned pattern {self.PATTERN_DEFINITIONS[idx]} to spacing {spacing:.2f}")
                    else:
                        self.logger.info(f"No pattern available for spacing {spacing:.2f} (index {idx})")
                        spacing_to_pattern[spacing] = self.PATTERN_DEFINITIONS[0]  # Fallback to first pattern
                except Exception as e:
                    self.logger.error(f"Error assigning color/pattern to spacing {spacing:.2f}: {str(e)}")
                    raise

            # Draw lines for each spacing occurrence
            for spacing, occurrences in spacing_lines.items():
                try:
                    color = color_map.get(spacing_to_color[spacing], (1, 0, 0))
                    pattern_def = spacing_to_pattern[spacing]
                    self.logger.debug(f"Drawing {len(occurrences)} lines for spacing {spacing:.2f}")
                    
                    for page_num, y in occurrences:
                        try:
                            page = doc[page_num]
                            y_draw = y
                            if not (0 <= y_draw <= page.rect.height):
                                self.logger.info(f"y_draw {y_draw} is out of bounds for page height {page.rect.height}")
                                continue
                            self._draw_patterned_line(page, y_draw, pattern_def, color)
                        except Exception as e:
                            self.logger.error(f"Error drawing line on page {page_num} at y={y}: {str(e)}")
                            continue
                except Exception as e:
                    self.logger.error(f"Error processing spacing {spacing:.2f}: {str(e)}")
                    continue

            # Add a legend page
            try:
                self._add_legend_page(doc, sorted_spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences)
            except Exception as e:
                self.logger.error(f"Error creating legend page: {str(e)}")
                raise

            doc.save(output_pdf)
            self.logger.info(f"Successfully saved visualization to {output_pdf}")
            
        except Exception as e:
            self.logger.error(f"Error creating visualization: {str(e)}")
            raise
        finally:
            if 'doc' in locals():
                doc.close()
    
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
    
    def _add_legend_page(self, doc, sorted_spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences, title="Vertical Spacing Legend"):
        width = doc[0].rect.width
        height = doc[0].rect.height
        color_map = self._get_color_map()
        
        # Calculate how many entries we can fit per page
        # Each entry takes 16pt (reduced from 20pt)
        # Leave 72pt margin at top and bottom
        usable_height = height - 144  # 72pt top + 72pt bottom margin
        entries_per_page = int(usable_height / 16)
        
        # Split spacings into chunks for multiple pages
        for page_num, page_spacings in enumerate([sorted_spacings[i:i + entries_per_page] 
                                                for i in range(0, len(sorted_spacings), entries_per_page)]):
            legend_page = doc.new_page(width=width, height=height)
            
            # Add title with page number if multiple pages
            page_title = f"{title} (Page {page_num + 1})" if len(sorted_spacings) > entries_per_page else title
            legend_page.insert_text(
                (72, 72),
                page_title,
                fontsize=16,  # Reduced from 18
                fontname="helv",
                color=(0, 0, 0)
            )

            # Add column headers
            y = 100  # Reduced from 110
            legend_page.insert_text((72, y), "Spacing (pt)", fontsize=10, fontname="helv", color=(0, 0, 0))  # Reduced from 12
            legend_page.insert_text((180, y), "Count", fontsize=10, fontname="helv", color=(0, 0, 0))
            legend_page.insert_text((250, y), "Color", fontsize=10, fontname="helv", color=(0, 0, 0))
            legend_page.insert_text((350, y), "Pattern", fontsize=10, fontname="helv", color=(0, 0, 0))
            y += 12  # Reduced from 15

            # Add entries for each spacing
            for spacing, count in page_spacings:
                try:
                    color_name = spacing_to_color[spacing]
                    pattern_def = spacing_to_pattern[spacing]
                    pattern_name, width, _ = pattern_def
                    color_rgb = color_map.get(color_name, (1, 0, 0))
                    
                    # Add spacing value
                    legend_page.insert_text((72, y), f"{spacing:.2f}", fontsize=10, fontname="helv", color=(0, 0, 0))  # Reduced from 12
                    
                    # Add count
                    legend_page.insert_text((180, y), str(count), fontsize=10, fontname="helv", color=(0, 0, 0))
                    
                    # Add color name
                    legend_page.insert_text((250, y), color_name, fontsize=10, fontname="helv", color=color_rgb)
                    
                    # Add pattern name and width
                    legend_page.insert_text((350, y), f"{pattern_name} ({width}pt)", fontsize=10, fontname="helv", color=(0, 0, 0))
                    
                    # Draw sample line with pattern
                    x = 420
                    page_width = 520
                    
                    # Draw each segment
                    while x < page_width:
                        for seg_len, gap_len in pattern_def[2]:
                            actual_len = min(seg_len, page_width - x)
                            if actual_len > 0:
                                legend_page.draw_line(
                                    p1=(x, y + 4),  # Reduced from 6
                                    p2=(x + actual_len, y + 4),
                                    color=color_rgb,
                                    width=width
                                )
                            x += actual_len + gap_len
                            if x >= page_width:
                                break
                    
                    y += 16  # Reduced from 20
                except Exception as e:
                    self.logger.error(f"Error adding legend entry for spacing {spacing}: {str(e)}")
                    continue

    def _get_color_map(self):
        """Return the color map for legend use."""
        return {
            'red': (1, 0, 0),
            'blue': (0, 0, 1),
            'green': (0, 1, 0),
            'purple': (0.5, 0, 0.5),
            'orange': (1, 0.65, 0),
            'pink': (1, 0.75, 0.8),
            'magenta': (1, 0, 1),
            'yellow': (1, 1, 0),
            'lightblue': (0.68, 0.85, 0.9),
            'darkred': (0.55, 0, 0),
            'darkblue': (0, 0, 0.55),
            'darkgreen': (0, 0.39, 0),
            'crimson': (0.86, 0.08, 0.24),
            'navy': (0, 0, 0.5),
            'forestgreen': (0.13, 0.55, 0.13),
            'indigo': (0.29, 0, 0.51),
            'orangered': (1, 0.27, 0),
            'hotpink': (1, 0.41, 0.71),
            'slategray': (0.44, 0.5, 0.56),
            'deeppink': (1, 0.08, 0.58),
            'darkviolet': (0.58, 0, 0.83),
            'darkorange': (1, 0.55, 0),
            'chocolate': (0.82, 0.41, 0.12),
            'dimgray': (0.41, 0.41, 0.41),
            'saddlebrown': (0.55, 0.27, 0.07),
            'mediumblue': (0, 0, 0.8),
            'mediumpurple': (0.58, 0.44, 0.86),
            'mediumseagreen': (0.24, 0.7, 0.44),
            'mediumvioletred': (0.78, 0.08, 0.52),
            'olive': (0.5, 0.5, 0),
            'olivedrab': (0.42, 0.56, 0.14),
            'peru': (0.8, 0.52, 0.25),
            'plum': (0.87, 0.63, 0.87),
            'powderblue': (0.69, 0.88, 0.9),
            'rosybrown': (0.74, 0.56, 0.56),
            'royalblue': (0.25, 0.41, 0.88),
            'sienna': (0.63, 0.32, 0.18),
            'skyblue': (0.53, 0.81, 0.92),
            'steelblue': (0.27, 0.51, 0.71),
            'tan': (0.82, 0.71, 0.55),
            'thistle': (0.85, 0.75, 0.85),
            'tomato': (1, 0.39, 0.28),
            'turquoise': (0.25, 0.88, 0.82),
            'violet': (0.93, 0.51, 0.93),
            'wheat': (0.96, 0.87, 0.7),
            'yellowgreen': (0.6, 0.8, 0.2)
        }

    def generate_visualization(self, data: Dict, base_name: str) -> None:
        """Generate visualization output.
        
        Args:
            data: Dictionary containing analysis data
            base_name: Base name for output files
        """
        # Generate text output
        text_output = self._generate_text_output(data)
        self.file_handler.save_text(text_output, base_name, "visualization")
        
        # Generate JSON output
        json_output = self._generate_json_output(data)
        self.file_handler.save_json(json_output, base_name, "visualization")
        
    def _generate_text_output(self, data: Dict) -> str:
        """Generate text-based visualization.
        
        Args:
            data: Dictionary containing analysis data
            
        Returns:
            Formatted text output
        """
        output = []
        
        # Add header
        output.append("PDF Analysis Visualization")
        output.append("=" * 30)
        output.append("")
        
        # Add page information
        for page in data.get("pages", []):
            output.append(f"Page {page['page_number']}")
            output.append("-" * 20)
            
            # Add line information
            for line in page.get("lines", []):
                output.append(f"Line {line['line_number']}: {line['text']}")
                if line.get("gap_before"):
                    output.append(f"  Gap before: {line['gap_before']}")
                if line.get("gap_after"):
                    output.append(f"  Gap after: {line['gap_after']}")
                output.append("")
            
            output.append("")
        
        return "\n".join(output)
        
    def _generate_json_output(self, data: Dict) -> Dict:
        """Generate JSON-based visualization.
        
        Args:
            data: Dictionary containing analysis data
            
        Returns:
            Formatted JSON output
        """
        return {
            "visualization": {
                "pages": data.get("pages", []),
                "metadata": data.get("metadata", {}),
                "statistics": data.get("statistics", {})
            }
        }

    def create_block_visualization(
        self,
        input_pdf: str,
        output_pdf: str,
        spacing_ranges: List[Tuple[Optional[float], Optional[float]]],
        spacing_colors: List[str],
        spacing_patterns: List[str],
        blocks_data: List[Dict]
    ) -> None:
        """Create a visualization PDF with block spacing lines using PyMuPDF, and add a legend page."""
        doc = fitz.open(input_pdf)
        color_map = self._get_color_map()

        # Collect all spacings
        spacing_occurrences = collections.Counter()
        spacing_lines = collections.defaultdict(list)  # spacing_value: list of (page_num, y)

        for page_data in blocks_data:
            page_num = page_data['page'] - 1
            blocks = page_data['blocks']
            page = doc[page_num]
            page_height = page.rect.height
            
            # Find the first and last blocks
            if not blocks:
                continue
                
            first_block = blocks[0]
            last_block = blocks[-1]
            
            # Add top page gap if first block exists
            if first_block:
                top_gap = first_block['bbox']['top']
                if top_gap > 0:
                    spacing = round_to_nearest(top_gap, self.config.round_to_nearest_pt)
                    for i, range_spec in enumerate(spacing_ranges):
                        if self.matches_range(spacing, range_spec):
                            spacing_occurrences[spacing] += 1
                            spacing_lines[spacing].append((page_num, top_gap))
                            break
            
            # Process gaps between blocks
            for i in range(1, len(blocks)):
                prev_block = blocks[i-1]
                curr_block = blocks[i]
                
                # Calculate gap between blocks
                gap = curr_block['bbox']['top'] - prev_block['bbox']['bottom']
                if gap > 0:
                    spacing = round_to_nearest(gap, self.config.round_to_nearest_pt)
                    for i, range_spec in enumerate(spacing_ranges):
                        if self.matches_range(spacing, range_spec):
                            spacing_occurrences[spacing] += 1
                            spacing_lines[spacing].append((page_num, curr_block['bbox']['top']))
                            break
            
            # Add bottom page gap if last block exists
            if last_block:
                bottom_gap = page_height - last_block['bbox']['bottom']
                if bottom_gap > 0:
                    spacing = round_to_nearest(bottom_gap, self.config.round_to_nearest_pt)
                    for i, range_spec in enumerate(spacing_ranges):
                        if self.matches_range(spacing, range_spec):
                            spacing_occurrences[spacing] += 1
                            spacing_lines[spacing].append((page_num, last_block['bbox']['bottom']))
                            break

        # Sort spacings by frequency (most frequent first)
        sorted_spacings = sorted(spacing_occurrences.items(), key=lambda x: x[1], reverse=True)
        
        # Assign colors and patterns based on frequency
        spacing_to_color = {}
        spacing_to_pattern = {}
        
        for idx, (spacing, _) in enumerate(sorted_spacings):
            try:
                if idx < len(self.DEFAULT_COLORS):
                    spacing_to_color[spacing] = self.DEFAULT_COLORS[idx]
                else:
                    self.logger.info(f"No color available for spacing {spacing:.2f} (index {idx})")
                    spacing_to_color[spacing] = self.DEFAULT_COLORS[0]  # Fallback to first color
                    
                if idx < len(self.PATTERN_DEFINITIONS):
                    spacing_to_pattern[spacing] = self.PATTERN_DEFINITIONS[idx]
                else:
                    self.logger.info(f"No pattern available for spacing {spacing:.2f} (index {idx})")
                    spacing_to_pattern[spacing] = self.PATTERN_DEFINITIONS[0]  # Fallback to first pattern
            except Exception as e:
                self.logger.error(f"Error assigning color/pattern to spacing {spacing:.2f}: {str(e)}")
                raise

        # Draw lines for each spacing occurrence
        for spacing, occurrences in spacing_lines.items():
            try:
                color = color_map.get(spacing_to_color[spacing], (1, 0, 0))
                pattern_def = spacing_to_pattern[spacing]
                self.logger.debug(f"Drawing {len(occurrences)} lines for spacing {spacing:.2f}")
                
                for page_num, y in occurrences:
                    try:
                        page = doc[page_num]
                        y_draw = y
                        if not (0 <= y_draw <= page.rect.height):
                            self.logger.info(f"y_draw {y_draw} is out of bounds for page height {page.rect.height}")
                            continue
                        self._draw_patterned_line(page, y_draw, pattern_def, color)
                    except Exception as e:
                        self.logger.error(f"Error drawing line on page {page_num} at y={y}: {str(e)}")
                        continue
            except Exception as e:
                self.logger.error(f"Error processing spacing {spacing:.2f}: {str(e)}")
                continue

        # Add a legend page
        try:
            self._add_legend_page(doc, sorted_spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences, "Block Spacing Legend")
        except Exception as e:
            self.logger.error(f"Error creating legend page: {str(e)}")
            raise

        doc.save(output_pdf)
        self.logger.info(f"Successfully saved visualization to {output_pdf}")

    def _add_legend_page(self, doc, spacings, spacing_to_color, spacing_to_pattern, spacing_occurrences, title="Vertical Spacing Legend"):
        width = doc[0].rect.width
        height = doc[0].rect.height
        color_map = self._get_color_map()
        
        # Calculate how many entries we can fit per page
        # Each entry takes 16pt (reduced from 20pt)
        # Leave 72pt margin at top and bottom
        usable_height = height - 144  # 72pt top + 72pt bottom margin
        entries_per_page = int(usable_height / 16)
        
        # Split spacings into chunks for multiple pages
        for page_num, page_spacings in enumerate([spacings[i:i + entries_per_page] 
                                                for i in range(0, len(spacings), entries_per_page)]):
            legend_page = doc.new_page(width=width, height=height)
            
            # Add title with page number if multiple pages
            page_title = f"{title} (Page {page_num + 1})" if len(spacings) > entries_per_page else title
            legend_page.insert_text(
                (72, 72),
                page_title,
                fontsize=16,  # Reduced from 18
                fontname="helv",
                color=(0, 0, 0)
            )

            # Add column headers
            y = 100  # Reduced from 110
            legend_page.insert_text((72, y), "Spacing (pt)", fontsize=10, fontname="helv", color=(0, 0, 0))  # Reduced from 12
            legend_page.insert_text((180, y), "Count", fontsize=10, fontname="helv", color=(0, 0, 0))
            legend_page.insert_text((250, y), "Color", fontsize=10, fontname="helv", color=(0, 0, 0))
            legend_page.insert_text((350, y), "Pattern", fontsize=10, fontname="helv", color=(0, 0, 0))
            y += 12  # Reduced from 15

            # Add entries for each spacing
            for spacing, count in page_spacings:
                try:
                    color_name = spacing_to_color[spacing]
                    pattern_def = spacing_to_pattern[spacing]
                    pattern_name, width, _ = pattern_def
                    color_rgb = color_map.get(color_name, (1, 0, 0))
                    
                    # Add spacing value
                    legend_page.insert_text((72, y), f"{spacing:.2f}", fontsize=10, fontname="helv", color=(0, 0, 0))  # Reduced from 12
                    
                    # Add count
                    legend_page.insert_text((180, y), str(count), fontsize=10, fontname="helv", color=(0, 0, 0))
                    
                    # Add color name
                    legend_page.insert_text((250, y), color_name, fontsize=10, fontname="helv", color=color_rgb)
                    
                    # Add pattern name and width
                    legend_page.insert_text((350, y), f"{pattern_name} ({width}pt)", fontsize=10, fontname="helv", color=(0, 0, 0))
                    
                    # Draw sample line with pattern
                    x = 420
                    page_width = 520
                    
                    # Draw each segment
                    while x < page_width:
                        for seg_len, gap_len in pattern_def[2]:
                            actual_len = min(seg_len, page_width - x)
                            if actual_len > 0:
                                legend_page.draw_line(
                                    p1=(x, y + 4),  # Reduced from 6
                                    p2=(x + actual_len, y + 4),
                                    color=color_rgb,
                                    width=width
                                )
                            x += actual_len + gap_len
                            if x >= page_width:
                                break
                    
                    y += 16  # Reduced from 20
                except Exception as e:
                    self.logger.error(f"Error adding legend entry for spacing {spacing}: {str(e)}")
                    continue