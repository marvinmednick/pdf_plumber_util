"""Pattern management for comprehensive document structure analysis."""

import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import yaml
from dataclasses import dataclass, field

from .exceptions import ConfigurationError


@dataclass
class PatternDefinition:
    """Defines a single regex pattern with metadata."""
    name: str
    regex: str
    description: str
    pattern_type: str
    hierarchy_level: Optional[int] = None
    compiled_regex: Optional[re.Pattern] = field(init=False, default=None)

    def __post_init__(self):
        """Compile regex pattern after initialization."""
        try:
            self.compiled_regex = re.compile(self.regex)
        except re.error as e:
            raise ConfigurationError(f"Invalid regex pattern '{self.name}': {e}")


@dataclass
class PatternMatch:
    """Represents a single pattern match with context."""
    pattern_name: str
    page: int
    line: int
    text: str
    match: str
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_style: Optional[str] = None
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    confidence: Optional[float] = None


class PatternSetManager:
    """Manages configurable regex patterns for document structure analysis."""

    def __init__(self, config_path: Optional[Path] = None, custom_patterns: Optional[Dict[str, Any]] = None):
        """Initialize pattern set manager.

        Args:
            config_path: Path to YAML configuration file with patterns
            custom_patterns: Additional custom patterns to include
        """
        self.patterns: Dict[str, PatternDefinition] = {}
        self.pattern_sets: Dict[str, List[str]] = {}

        # Load default patterns
        self._load_default_patterns()

        # Load from config file if provided
        if config_path:
            self._load_patterns_from_file(config_path)

        # Add custom patterns if provided
        if custom_patterns:
            self._add_custom_patterns(custom_patterns)

    def _load_default_patterns(self) -> None:
        """Load default pattern definitions."""
        default_patterns = {
            # Decimal numbering patterns (most common)
            'decimal_simple': {
                'regex': r'^(\d+(?:\.\d+)*)\s+[A-Z]',
                'description': 'Simple decimal numbering (1.1 Introduction, 2.3.4 Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'decimal_with_letter_prefix': {
                'regex': r'^([A-Z]\.\d+(?:\.\d+)*)\s+[A-Z]',
                'description': 'Letter-prefixed decimal (A.1 Overview, B.2.3 Details)',
                'type': 'section',
                'hierarchy_level': None
            },
            'decimal_no_space_numeric': {
                'regex': r'^(\d+(?:\.\d+)+)[A-Z][a-z]',
                'description': 'Multi-level decimal without space (9.3.4.6Byte, 1.2.3Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'decimal_no_space_letter': {
                'regex': r'^([A-Z]\d+(?:\.\d+)*)[A-Z][a-z]',
                'description': 'Letter-prefixed decimal without space (A1Requirements, B2Overview)',
                'type': 'section',
                'hierarchy_level': None
            },

            # Mixed alphanumeric patterns
            'decimal_letter_suffix': {
                'regex': r'^(\d+(?:\.\d+)*[A-Z])\s+[A-Z]',
                'description': 'Decimal with letter suffix (1.1.A Introduction, 2.3B Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'letter_decimal_mixed': {
                'regex': r'^([A-Z]\d+(?:\.\d+)*)\s+[A-Z]',
                'description': 'Letter-number mixed (A1 Introduction, B2.3 Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },

            # Roman numeral patterns
            'roman_uppercase': {
                'regex': r'^([IVX]+)\s+[A-Z]',
                'description': 'Uppercase roman numerals (I Introduction, II Analysis, III Results)',
                'type': 'section',
                'hierarchy_level': None
            },
            'roman_lowercase': {
                'regex': r'^([ivx]+)\s+[A-Za-z]',
                'description': 'Lowercase roman numerals (i introduction, ii analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'roman_parentheses': {
                'regex': r'^\(([ivx]+)\)\s+[A-Za-z]',
                'description': 'Roman numerals in parentheses ((i) introduction, (ii) analysis)',
                'type': 'section',
                'hierarchy_level': None
            },

            # Letter-only patterns
            'letter_simple': {
                'regex': r'^([A-Z])\s+[A-Z][a-z]',
                'description': 'Single letter numbering (A Introduction, B Analysis)',
                'type': 'section',
                'hierarchy_level': 1
            },
            'letter_parentheses': {
                'regex': r'^\(([a-z])\)\s+[A-Za-z]',
                'description': 'Letters in parentheses ((a) introduction, (b) analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'letter_dot': {
                'regex': r'^([a-z])\.\s+[A-Za-z]',
                'description': 'Letters with dot (a. introduction, b. analysis)',
                'type': 'section',
                'hierarchy_level': None
            },

            # Special document sections
            'annex_heading': {
                'regex': r'^(Annex\s+[A-Z])',
                'description': 'Annex headings (Annex A, Annex B)',
                'type': 'section',
                'hierarchy_level': 1
            },
            'appendix_heading': {
                'regex': r'^(Appendix\s+[A-Z])',
                'description': 'Appendix headings (Appendix A, Appendix B)',
                'type': 'section',
                'hierarchy_level': 1
            },
            'chapter_pattern': {
                'regex': r'^(Chapter\s+\d+)',
                'description': 'Chapter headings (Chapter 1, Chapter 2)',
                'type': 'section',
                'hierarchy_level': 1
            },
            'part_pattern': {
                'regex': r'^(Part\s+[IVX\d]+)',
                'description': 'Part headings (Part I, Part II, Part 1)',
                'type': 'section',
                'hierarchy_level': 1
            },
            'section_explicit': {
                'regex': r'^(Section\s+\d+(?:\.\d+)*)',
                'description': 'Explicit section headings (Section 1, Section 2.1)',
                'type': 'section',
                'hierarchy_level': None
            },

            # Additional common patterns found in testing
            'roman_dot': {
                'regex': r'^([IVX]+)\.\s+[A-Z]',
                'description': 'Roman numerals with dot (I. Introduction, II. Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'letter_single_dot': {
                'regex': r'^([A-Z])\.\s+[A-Z]',
                'description': 'Single letter with dot (A. Introduction, B. Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'number_dot': {
                'regex': r'^(\d+)\.\s+[A-Z]',
                'description': 'Number with dot (1. Introduction, 2. Analysis)',
                'type': 'section',
                'hierarchy_level': None
            },
            'decimal_no_space_letter_prefix': {
                'regex': r'^([A-Z]\.\d+(?:\.\d+)*)[A-Z][a-z]',
                'description': 'Letter-prefixed decimal no space (A.1Requirements, B.2.3Overview)',
                'type': 'section',
                'hierarchy_level': None
            },

            # TOC patterns
            'toc_title_contents': {
                'regex': r'(Table\s+of\s+Contents|Contents)',
                'description': 'Table of Contents title',
                'type': 'toc_title'
            },
            'toc_title_list_figures': {
                'regex': r'(List\s+of\s+Figures)',
                'description': 'List of Figures title',
                'type': 'toc_title'
            },
            'toc_title_list_tables': {
                'regex': r'(List\s+of\s+Tables)',
                'description': 'List of Tables title',
                'type': 'toc_title'
            },
            'toc_entry_dotted': {
                'regex': r'(\d+(?:\.\d+)*)\s+(.+?)\s+\.{3,}\s+(\d+)',
                'description': 'TOC entries with dotted leaders',
                'type': 'toc_entry'
            },
            'toc_entry_simple': {
                'regex': r'(\d+(?:\.\d+)*)\s+(.+?)\s+(\d+)$',
                'description': 'Simple TOC entries without dots',
                'type': 'toc_entry'
            },

            # Figure and table patterns (improved)
            'figure_caption': {
                'regex': r'^(Figure\s+\d+(?:-\d+)?)\s*[–-]',
                'description': 'Figure captions (Figure 9-11 –, Figure 9-12 –)',
                'type': 'figure'
            },
            'table_caption': {
                'regex': r'^(Table\s+\d+(?:-\d+)?)\s*[–:-]',
                'description': 'Table captions (Table 7-2:, Table 9-1 –)',
                'type': 'table'
            },
            'figure_reference': {
                'regex': r'(Figure\s+\d+(?:-\d+)?)',
                'description': 'Figure references in text',
                'type': 'figure'
            },
            'table_reference': {
                'regex': r'(Table\s+\d+(?:-\d+)?)',
                'description': 'Table references in text',
                'type': 'table'
            },

            # Header/footer patterns
            'page_number_simple': {
                'regex': r'^(\d+)$',
                'description': 'Simple page numbers',
                'type': 'page_number'
            },
            'page_number_formatted': {
                'regex': r'(Page\s+\d+|\d+\s+of\s+\d+)',
                'description': 'Formatted page numbers',
                'type': 'page_number'
            }
        }

        for name, pattern_data in default_patterns.items():
            self.patterns[name] = PatternDefinition(
                name=name,
                regex=pattern_data['regex'],
                description=pattern_data['description'],
                pattern_type=pattern_data['type'],
                hierarchy_level=pattern_data.get('hierarchy_level')
            )

        # Define pattern sets for different analysis phases
        self.pattern_sets = {
            'section_patterns': [
                'decimal_simple', 'decimal_with_letter_prefix', 'decimal_no_space_numeric', 'decimal_no_space_letter', 'decimal_no_space_letter_prefix',
                'decimal_letter_suffix', 'letter_decimal_mixed',
                'roman_uppercase', 'roman_lowercase', 'roman_parentheses', 'roman_dot',
                'letter_simple', 'letter_parentheses', 'letter_dot', 'letter_single_dot',
                'number_dot',
                'annex_heading', 'appendix_heading', 'chapter_pattern', 'part_pattern', 'section_explicit'
            ],
            'toc_patterns': [
                'toc_title_contents', 'toc_title_list_figures', 'toc_title_list_tables',
                'toc_entry_dotted', 'toc_entry_simple'
            ],
            'figure_table_patterns': [
                'figure_caption', 'table_caption', 'figure_reference', 'table_reference'
            ],
            'page_number_patterns': [
                'page_number_simple', 'page_number_formatted'
            ]
        }

    def _load_patterns_from_file(self, config_path: Path) -> None:
        """Load patterns from YAML configuration file."""
        if not config_path.exists():
            raise ConfigurationError(f"Pattern configuration file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            # Load patterns from config
            if 'patterns' in config_data:
                for name, pattern_data in config_data['patterns'].items():
                    self.patterns[name] = PatternDefinition(
                        name=name,
                        regex=pattern_data['regex'],
                        description=pattern_data.get('description', ''),
                        pattern_type=pattern_data.get('type', 'custom'),
                        hierarchy_level=pattern_data.get('hierarchy_level')
                    )

            # Load pattern sets from config
            if 'pattern_sets' in config_data:
                self.pattern_sets.update(config_data['pattern_sets'])

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing pattern configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading pattern configuration: {e}")

    def _add_custom_patterns(self, custom_patterns: Dict[str, Any]) -> None:
        """Add custom patterns at runtime."""
        for name, pattern_data in custom_patterns.items():
            if isinstance(pattern_data, str):
                # Simple regex string
                self.patterns[name] = PatternDefinition(
                    name=name,
                    regex=pattern_data,
                    description=f"Custom pattern: {name}",
                    pattern_type="custom"
                )
            else:
                # Full pattern definition
                self.patterns[name] = PatternDefinition(
                    name=name,
                    regex=pattern_data['regex'],
                    description=pattern_data.get('description', f"Custom pattern: {name}"),
                    pattern_type=pattern_data.get('type', 'custom'),
                    hierarchy_level=pattern_data.get('hierarchy_level')
                )

    def get_pattern(self, name: str) -> Optional[PatternDefinition]:
        """Get a specific pattern by name."""
        return self.patterns.get(name)

    def get_patterns_by_type(self, pattern_type: str) -> List[PatternDefinition]:
        """Get all patterns of a specific type."""
        return [p for p in self.patterns.values() if p.pattern_type == pattern_type]

    def get_pattern_set(self, set_name: str) -> List[PatternDefinition]:
        """Get all patterns in a named set."""
        if set_name not in self.pattern_sets:
            raise ValueError(f"Unknown pattern set: {set_name}")

        patterns = []
        for pattern_name in self.pattern_sets[set_name]:
            if pattern_name in self.patterns:
                patterns.append(self.patterns[pattern_name])

        return patterns

    def get_all_patterns(self) -> Dict[str, PatternDefinition]:
        """Get all loaded patterns."""
        return self.patterns.copy()

    def get_patterns_for_comprehensive_analysis(self) -> Dict[str, Dict[str, Any]]:
        """Get patterns formatted for comprehensive LLM analysis.

        Returns:
            Dictionary structure expected by comprehensive pattern analysis
        """
        result = {
            'section_patterns': {},
            'toc_patterns': {},
            'figure_table_patterns': {},
            'page_number_patterns': {}
        }

        # Group patterns by analysis category
        for set_name, pattern_names in self.pattern_sets.items():
            if set_name in result:
                for pattern_name in pattern_names:
                    if pattern_name in self.patterns:
                        pattern = self.patterns[pattern_name]
                        result[set_name][pattern_name] = {
                            'regex': pattern.regex,
                            'description': pattern.description,
                            'type': pattern.pattern_type,
                            'hierarchy_level': pattern.hierarchy_level
                        }

        return result

    def add_pattern(self, name: str, regex: str, pattern_type: str, description: str = "", hierarchy_level: Optional[int] = None) -> None:
        """Add a new pattern at runtime."""
        if name in self.patterns:
            raise ValueError(f"Pattern '{name}' already exists")

        self.patterns[name] = PatternDefinition(
            name=name,
            regex=regex,
            description=description,
            pattern_type=pattern_type,
            hierarchy_level=hierarchy_level
        )

    def remove_pattern(self, name: str) -> None:
        """Remove a pattern by name."""
        if name not in self.patterns:
            raise ValueError(f"Pattern '{name}' not found")

        del self.patterns[name]

    def validate_patterns(self) -> List[str]:
        """Validate all patterns and return any errors."""
        errors = []

        for name, pattern in self.patterns.items():
            try:
                # Test regex compilation
                re.compile(pattern.regex)

                # Test with simple string
                test_match = re.search(pattern.compiled_regex, "test 1.2.3 content")

            except re.error as e:
                errors.append(f"Pattern '{name}': Invalid regex - {e}")
            except Exception as e:
                errors.append(f"Pattern '{name}': Validation error - {e}")

        return errors

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns."""
        type_counts = {}
        for pattern in self.patterns.values():
            type_counts[pattern.pattern_type] = type_counts.get(pattern.pattern_type, 0) + 1

        return {
            'total_patterns': len(self.patterns),
            'pattern_types': type_counts,
            'pattern_sets': {name: len(patterns) for name, patterns in self.pattern_sets.items()},
            'patterns_with_hierarchy': sum(1 for p in self.patterns.values() if p.hierarchy_level is not None)
        }