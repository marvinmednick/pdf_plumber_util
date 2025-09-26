"""Document scanning for comprehensive pattern detection."""

import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from collections import defaultdict

from .pattern_manager import PatternSetManager, PatternDefinition, PatternMatch
from .exceptions import AnalysisError


@dataclass
class FontInfo:
    """Font information for text elements."""
    family: Optional[str] = None
    size: Optional[str] = None
    style: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'family': self.family,
            'size': self.size,
            'style': self.style
        }


@dataclass
class ScanResult:
    """Results from document pattern scanning."""
    pattern_matches: Dict[str, List[PatternMatch]]
    document_context: Dict[str, Any]
    font_analysis: Dict[str, Any]
    scan_statistics: Dict[str, Any]


class DocumentScanner:
    """Scans entire documents for pattern matches with font and position context."""

    def __init__(self, pattern_manager: PatternSetManager):
        """Initialize document scanner.

        Args:
            pattern_manager: Pattern manager with loaded patterns
        """
        self.pattern_manager = pattern_manager
        self.scan_cache: Dict[str, ScanResult] = {}

    def scan_full_document(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        pattern_sets: Optional[List[str]] = None
    ) -> ScanResult:
        """Scan entire document for all configured patterns.

        Args:
            document_data: Document pages data or full document structure
            pattern_sets: Specific pattern sets to scan (defaults to all)

        Returns:
            Comprehensive scan results with matches, context, and analysis
        """
        # Extract pages data
        if isinstance(document_data, dict) and 'pages' in document_data:
            pages_data = document_data['pages']
            document_metadata = {k: v for k, v in document_data.items() if k != 'pages'}
        elif isinstance(document_data, list):
            pages_data = document_data
            document_metadata = {}
        else:
            raise AnalysisError("Invalid document data format")

        if not pages_data:
            raise AnalysisError("Document data cannot be empty")

        # Determine which patterns to use
        if pattern_sets is None:
            patterns_to_scan = list(self.pattern_manager.get_all_patterns().values())
        else:
            patterns_to_scan = []
            for set_name in pattern_sets:
                patterns_to_scan.extend(self.pattern_manager.get_pattern_set(set_name))

        # Scan all pages
        all_matches = defaultdict(list)
        font_statistics = defaultdict(lambda: {'total': 0, 'pages': set()})
        position_data = []

        for page_idx, page_data in enumerate(pages_data):
            page_matches, page_fonts, page_positions = self._scan_page(
                page_data, patterns_to_scan, page_idx + 1
            )

            # Accumulate matches
            for pattern_name, matches in page_matches.items():
                all_matches[pattern_name].extend(matches)

            # Accumulate font statistics
            for font_key, count in page_fonts.items():
                font_statistics[font_key]['total'] += count
                font_statistics[font_key]['pages'].add(page_idx + 1)

            position_data.extend(page_positions)

        # Analyze fonts and create document context
        font_analysis = self._analyze_fonts(font_statistics, pages_data)
        document_context = self._build_document_context(
            pages_data, document_metadata, font_analysis
        )

        # Generate scan statistics
        scan_statistics = self._generate_scan_statistics(
            all_matches, patterns_to_scan, len(pages_data)
        )

        return ScanResult(
            pattern_matches=dict(all_matches),
            document_context=document_context,
            font_analysis=font_analysis,
            scan_statistics=scan_statistics
        )

    def rescan_with_new_patterns(
        self,
        document_data: Union[List[Dict[str, Any]], Dict[str, Any]],
        additional_patterns: List[PatternDefinition]
    ) -> ScanResult:
        """Re-scan document when new patterns are discovered.

        Args:
            document_data: Document data to re-scan
            additional_patterns: New patterns to add to scan

        Returns:
            Updated scan results including new pattern matches
        """
        # Temporarily add new patterns to manager
        original_patterns = self.pattern_manager.get_all_patterns()

        try:
            for pattern in additional_patterns:
                if pattern.name not in original_patterns:
                    self.pattern_manager.add_pattern(
                        pattern.name,
                        pattern.regex,
                        pattern.pattern_type,
                        pattern.description,
                        pattern.hierarchy_level
                    )

            # Perform full scan with updated patterns
            return self.scan_full_document(document_data)

        finally:
            # Restore original patterns (remove temporarily added ones)
            for pattern in additional_patterns:
                if pattern.name not in original_patterns:
                    try:
                        self.pattern_manager.remove_pattern(pattern.name)
                    except ValueError:
                        pass  # Pattern might not have been added due to conflict

    def _scan_page(
        self,
        page_data: Dict[str, Any],
        patterns: List[PatternDefinition],
        page_number: int
    ) -> tuple[Dict[str, List[PatternMatch]], Dict[str, int], List[Dict[str, Any]]]:
        """Scan a single page for pattern matches.

        Returns:
            Tuple of (pattern_matches, font_counts, position_data)
        """
        page_matches = defaultdict(list)
        font_counts = defaultdict(int)
        position_data = []

        # Extract text blocks/lines from page
        text_blocks = self._extract_text_blocks(page_data)

        for line_idx, block in enumerate(text_blocks):
            text = block.get('text', '')
            if not text.strip():
                continue

            # Extract font information
            font_info = self._extract_font_info(block)
            font_key = self._create_font_key(font_info)
            font_counts[font_key] += 1

            # Position information
            position_info = {
                'page': page_number,
                'line': line_idx,
                'x': block.get('x', 0),
                'y': block.get('y', 0),
                'font_info': font_info.to_dict()
            }
            position_data.append(position_info)

            # Test all patterns against this text
            for pattern in patterns:
                matches = pattern.compiled_regex.finditer(text)

                for match in matches:
                    pattern_match = PatternMatch(
                        pattern_name=pattern.name,
                        page=page_number,
                        line=line_idx,
                        text=text,
                        match=match.group(0),
                        font_family=font_info.family,
                        font_size=font_info.size,
                        font_style=font_info.style,
                        x_position=block.get('x'),
                        y_position=block.get('y')
                    )

                    page_matches[pattern.name].append(pattern_match)

        return dict(page_matches), dict(font_counts), position_data

    def _extract_text_blocks(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract text blocks/lines from page data."""
        # Try different possible locations for text data
        if 'blocks' in page_data:
            return page_data['blocks']
        elif 'lines' in page_data:
            return page_data['lines']
        elif 'words' in page_data:
            # Group words into lines if only word data available
            return self._group_words_into_lines(page_data['words'])
        elif 'text_blocks' in page_data:
            return page_data['text_blocks']
        else:
            # Fall back to raw text if structured data not available
            raw_text = page_data.get('text', '')
            if raw_text:
                return [{'text': line, 'x': 0, 'y': i} for i, line in enumerate(raw_text.split('\n'))]
            return []

    def _group_words_into_lines(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into logical lines based on y-coordinates."""
        if not words:
            return []

        # Sort words by y-coordinate, then x-coordinate
        sorted_words = sorted(words, key=lambda w: (w.get('y', 0), w.get('x', 0)))

        lines = []
        current_line = []
        current_y = None
        y_tolerance = 2.0  # Allow small y variations within same line

        for word in sorted_words:
            word_y = word.get('y', 0)

            if current_y is None or abs(word_y - current_y) <= y_tolerance:
                # Same line
                current_line.append(word)
                if current_y is None:
                    current_y = word_y
            else:
                # New line
                if current_line:
                    line_text = ' '.join(w.get('text', '') for w in current_line)
                    line_x = min(w.get('x', 0) for w in current_line)

                    # Use font info from first word in line
                    first_word = current_line[0]
                    line_block = {
                        'text': line_text,
                        'x': line_x,
                        'y': current_y,
                        'font': first_word.get('font', ''),
                        'font_size': first_word.get('font_size', ''),
                        'font_family': first_word.get('font_family', ''),
                        'font_style': first_word.get('font_style', '')
                    }
                    lines.append(line_block)

                # Start new line
                current_line = [word]
                current_y = word_y

        # Add final line
        if current_line:
            line_text = ' '.join(w.get('text', '') for w in current_line)
            line_x = min(w.get('x', 0) for w in current_line)
            first_word = current_line[0]
            line_block = {
                'text': line_text,
                'x': line_x,
                'y': current_y,
                'font': first_word.get('font', ''),
                'font_size': first_word.get('font_size', ''),
                'font_family': first_word.get('font_family', ''),
                'font_style': first_word.get('font_style', '')
            }
            lines.append(line_block)

        return lines

    def _extract_font_info(self, block: Dict[str, Any]) -> FontInfo:
        """Extract font information from text block."""
        # Try different possible font field names
        font_family = (
            block.get('font_family') or
            block.get('fontname') or
            block.get('font', '').split('-')[0] if block.get('font') else None
        )

        font_size = (
            block.get('font_size') or
            block.get('size') or
            str(block.get('fontsize', '')) if block.get('fontsize') else None
        )

        # Determine font style from font name or explicit field
        font_style = block.get('font_style', 'Regular')
        font_name = block.get('font', '')

        if not font_style or font_style == 'Regular':
            if 'Bold' in font_name and 'Italic' in font_name:
                font_style = 'Bold+Italic'
            elif 'Bold' in font_name:
                font_style = 'Bold'
            elif 'Italic' in font_name:
                font_style = 'Italic'
            else:
                font_style = 'Regular'

        return FontInfo(
            family=font_family,
            size=font_size,
            style=font_style
        )

    def _create_font_key(self, font_info: FontInfo) -> str:
        """Create a unique key for font combination."""
        return f"{font_info.family or 'Unknown'}|{font_info.size or 'Unknown'}|{font_info.style or 'Regular'}"

    def _analyze_fonts(
        self,
        font_statistics: Dict[str, Dict[str, Any]],
        pages_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze font usage patterns across the document."""
        if not font_statistics:
            return {'body_text_font': 'Unknown', 'body_text_size': 'Unknown'}

        # Find most common font (likely body text)
        font_usage = [(font_key, data['total']) for font_key, data in font_statistics.items()]
        font_usage.sort(key=lambda x: x[1], reverse=True)

        most_common_font_key = font_usage[0][0] if font_usage else "Unknown|Unknown|Regular"
        family, size, style = most_common_font_key.split('|', 2)

        # Build font analysis
        analysis = {
            'body_text_font': family,
            'body_text_size': size,
            'body_text_style': style,
            'total_unique_fonts': len(font_statistics),
            'font_distribution': {
                font_key: data['total'] for font_key, data in font_statistics.items()
            }
        }

        # Add common fonts list
        analysis['common_fonts'] = [
            {'font': font_key, 'count': count}
            for font_key, count in font_usage[:10]  # Top 10 fonts
        ]

        return analysis

    def _build_document_context(
        self,
        pages_data: List[Dict[str, Any]],
        document_metadata: Dict[str, Any],
        font_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive document context."""
        total_pages = len(pages_data)

        # Get page dimensions from first page
        first_page = pages_data[0] if pages_data else {}
        page_width = first_page.get('page_width', first_page.get('width', 612))
        page_height = first_page.get('page_height', first_page.get('height', 792))

        context = {
            'total_pages': total_pages,
            'page_width': page_width,
            'page_height': page_height,
            'body_text_font': font_analysis.get('body_text_font', 'Unknown'),
            'body_text_size': font_analysis.get('body_text_size', 'Unknown'),
            'document_metadata': document_metadata
        }

        return context

    def _generate_scan_statistics(
        self,
        all_matches: Dict[str, List[PatternMatch]],
        patterns_scanned: List[PatternDefinition],
        total_pages: int
    ) -> Dict[str, Any]:
        """Generate comprehensive scan statistics."""
        total_matches = sum(len(matches) for matches in all_matches.values())

        pattern_stats = {}
        for pattern in patterns_scanned:
            matches = all_matches.get(pattern.name, [])
            pattern_stats[pattern.name] = {
                'match_count': len(matches),
                'pages_with_matches': len(set(m.page for m in matches)),
                'pattern_type': pattern.pattern_type
            }

        return {
            'total_matches': total_matches,
            'patterns_with_matches': len([p for p in pattern_stats if pattern_stats[p]['match_count'] > 0]),
            'total_patterns_scanned': len(patterns_scanned),
            'pages_scanned': total_pages,
            'pattern_statistics': pattern_stats
        }

    def get_matches_by_pattern(self, scan_result: ScanResult, pattern_name: str) -> List[PatternMatch]:
        """Get all matches for a specific pattern."""
        return scan_result.pattern_matches.get(pattern_name, [])

    def get_matches_by_type(self, scan_result: ScanResult, pattern_type: str) -> Dict[str, List[PatternMatch]]:
        """Get all matches for patterns of a specific type."""
        result = {}

        for pattern_name, matches in scan_result.pattern_matches.items():
            pattern = self.pattern_manager.get_pattern(pattern_name)
            if pattern and pattern.pattern_type == pattern_type:
                result[pattern_name] = matches

        return result

    def format_for_llm_analysis(self, scan_result: ScanResult) -> Dict[str, Any]:
        """Format scan results for LLM analysis input.

        Returns structure matching the design document format.
        """
        return {
            'section_pattern_matches': self._format_pattern_group(
                scan_result, 'section'
            ),
            'toc_pattern_matches': self._format_pattern_group(
                scan_result, 'toc'
            ),
            'figure_table_pattern_matches': self._format_pattern_group(
                scan_result, ['figure', 'table']
            ),
            'document_context': scan_result.document_context
        }

    def _format_pattern_group(
        self,
        scan_result: ScanResult,
        pattern_types: Union[str, List[str]]
    ) -> Dict[str, Any]:
        """Format a group of patterns for LLM input."""
        if isinstance(pattern_types, str):
            pattern_types = [pattern_types]

        result = {}

        for pattern_name, matches in scan_result.pattern_matches.items():
            pattern = self.pattern_manager.get_pattern(pattern_name)
            if pattern and pattern.pattern_type in pattern_types:
                result[pattern_name] = {
                    'regex': pattern.regex,
                    'description': pattern.description,
                    'matches': [
                        {
                            'page': m.page,
                            'line': m.line,
                            'text': m.text,
                            'match': m.match,
                            'font_family': m.font_family,
                            'font_size': m.font_size,
                            'font_style': m.font_style,
                            'x': m.x_position,
                            'y': m.y_position
                        }
                        for m in matches
                    ]
                }

        return result