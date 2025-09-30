# Pattern Detection Architecture

## Overview

This document specifies the architecture for intelligent document structure analysis using hybrid programmatic pattern detection and LLM validation. The system combines regex-based pattern matching with LLM intelligence to systematically discover document structure, validate patterns, and guide strategic page sampling for cost-effective detailed analysis.

**Companion documents:**
- [PATTERN_DETECTION_EVOLUTION.md](PATTERN_DETECTION_EVOLUTION.md) - Historical context and decision rationale
- PATTERN_DETECTION_IMPLEMENTATION.md (future) - Detailed implementation guide
- PATTERN_DETECTION_CONFIG.md (future) - Configuration reference

## System Goals

- **Strategic Sampling**: Use full-document pattern scanning to identify key pages for detailed analysis
- **Cost Optimization**: Minimize expensive LLM calls through intelligent page selection
- **Pattern Discovery**: Use configurable regex patterns to find document structure elements
- **Intelligent Validation**: Leverage LLM analysis to distinguish valid patterns from false positives
- **Iterative Refinement**: Build knowledge incrementally through multiple analysis cycles
- **Document Adaptability**: Support diverse document types with configurable patterns

---

## Architecture Overview

### Four-Phase Analysis Process

```
Document Input (all pages)
    ↓
┌─────────────────────────────────────────────────┐
│ Phase 0: Document Structure Discovery          │
│ - Full document regex scan (lightweight)       │
│ - LLM analyzes pattern distribution            │
│ - Recommends strategic page sampling           │
└─────────────────────────────────────────────────┘
    ↓
    Selected Pages: [5, 6, 17, 19, 50, 120, ...]
    ↓
┌─────────────────────────────────────────────────┐
│ Phase 1: Pattern Discovery & Validation        │
│ - Sequential single-page processing            │
│ - Comprehensive LLM validation per page        │
│ - Knowledge accumulation across pages          │
└─────────────────────────────────────────────────┘
    ↓
    Validated Patterns + Confidence Scores
    ↓
┌─────────────────────────────────────────────────┐
│ Phase 2: Iterative Content Analysis            │
│ - LLM content analysis with pattern context    │
│ - Iterative refinement based on findings       │
└─────────────────────────────────────────────────┘
    ↓
    Enhanced Document Understanding
    ↓
┌─────────────────────────────────────────────────┐
│ Phase 3: Completion Assessment                 │
│ - Multi-dimensional completeness metrics       │
│ - Determine analysis sufficiency               │
└─────────────────────────────────────────────────┘
    ↓
    Complete Document Structure Analysis
```

### Key Architecture Principles

1. **Pattern-Driven Sampling**: Let regex results guide page selection (not rigid formulas)
2. **Sequential Single-Page Processing**: Avoid API timeouts while maintaining comprehensive analysis
3. **Format Optimization**: Lightweight format for scanning, detailed format for validation
4. **Knowledge Accumulation**: Progressive understanding across sequential pages
5. **Hybrid Efficiency**: Programmatic preprocessing + strategic LLM usage

---

## Phase 0: Document Structure Discovery

### Purpose

Analyze the entire document structure using lightweight regex pattern matching to identify document regions and recommend strategic page sampling for detailed Phase 1 analysis.

### Process Flow

1. **Document Flattening**: Convert block-based format to line-based format optimized for regex scanning
2. **Regex Scanning**: Execute pattern matching across all document pages with location tracking
3. **Match Sampling**: Apply parameterized sampling to reduce LLM input size (front + back + random middle)
4. **LLM Analysis**: Analyze pattern distribution and recommend pages for Phase 1
5. **Output**: List of page numbers for detailed analysis

### Input Format

**Line-based document** (optimized for efficient regex scanning):
- Page number + line number (page-relative) + text content
- Minimal metadata (no font information needed for scanning)
- Flat structure for fast regex processing

*See Appendix B for detailed format specification*

### Regex Pattern Categories

Phase 0 uses patterns to identify:
- **Navigation indicators**: TOC headings, list headings, TOC entries
- **Section structure**: Hierarchical sections, chapter headings, appendix markers
- **Content indicators**: Figure titles, table titles, equation numbers
- **Document regions**: Front matter, back matter, annex markers

*See Appendix A for complete pattern catalog*

### Match Sampling Strategy

To keep LLM input manageable, apply parameterized sampling:
- **Small sets (≤10 matches)**: Include all
- **Medium sets (11-30 matches)**: Front 3 + Back 3 + Random 3
- **Large sets (>30 matches)**: Front 3 + Back 3 + Random 5

Example: 132 TOC entries → 11 sampled entries (3+5+3)

*See Appendix C for detailed algorithm*

### LLM Sampling Guidance

The LLM receives sampled regex results and is guided to:
- **Prioritize pattern-rich pages**: Pages with navigation markers (TOC, lists) are high-value
- **Ensure document coverage**: Sample across full document span
- **Weight toward boundaries**: Slightly favor first and last 20% (navigation and reference content)
- **Maintain diversity**: Avoid clustering, prefer distributed sampling

**Key principle**: Sampling is **pattern-driven** (based on where interesting content was found) rather than **formula-driven** (rigid percentages).

### Output

Simple list of page numbers for Phase 1 analysis:
```json
{
  "pages_to_analyze": [5, 6, 17, 19, 50, 120, 250, 305, 420, 550, 630, 685, 720, 750],
  "total_pages": 14,
  "rationale": "4 navigation pages, 10 content pages distributed across document"
}
```

---

## Phase 1: Pattern Discovery & Validation

### Purpose

Perform comprehensive pattern validation on selected pages using sequential single-page analysis. Each page receives one comprehensive LLM call that performs section validation, TOC validation, and cross-validation together.

**Key design decision**: Single-page processing prevents API timeouts while maintaining comprehensive analysis capabilities.

### Process Flow

1. **Load Page**: Retrieve page with detailed format (blocks, font metadata, text lines)
2. **Comprehensive LLM Call**: Analyze page for sections, TOC entries, figures, tables, equations
3. **Knowledge Update**: Accumulate findings into growing document structure understanding
4. **Next Page**: Repeat for each selected page, carrying forward accumulated knowledge

### Input Format

**Detailed page structure** (provides rich context for pattern validation):
- Blocks with font metadata (font family, size, style)
- Text lines as arrays (index = line number within page)
- Positioning information (y0, x0 coordinates)

*See Appendix B for detailed format specification*

### Comprehensive Single-Page Analysis

Each LLM call performs all validation tasks together:
- **Section identification**: Find genuine section headings, distinguish from false positives
- **TOC recognition**: Identify table of contents entries and structure
- **Content detection**: Find figures, tables, equations
- **Cross-validation**: Validate patterns against each other (e.g., sections vs TOC structure)
- **Hypothesis synthesis**: Update document structure understanding with confidence scores

### Knowledge Accumulation

As pages are processed sequentially, the system accumulates:
- **Confirmed patterns**: Validated section numbering schemes, figure numbering formats
- **Expected elements**: Sections/figures implied by TOC but not yet found
- **Font signatures**: Consistent font usage for different content types
- **Confidence evolution**: Pattern confidence increases with supporting evidence

This accumulated knowledge informs analysis of subsequent pages.

### Output

Validated document structure with confidence scores:
```json
{
  "document_structure": {
    "primary_numbering_scheme": "decimal_hierarchical",
    "section_levels": [1, 2, 3, 4],
    "confidence": 0.95
  },
  "navigation_structure": {
    "toc_pages": [5, 6, 7],
    "list_of_figures": [17],
    "confidence": 0.90
  },
  "content_patterns": {
    "figures": {"format": "Figure X-Y", "confidence": 0.85},
    "tables": {"format": "Table X-Y", "confidence": 0.80}
  },
  "validation_priorities": [
    "Verify appendix numbering (limited samples)",
    "Confirm table patterns (need more diversity)"
  ]
}
```

---

## Phase 2: Iterative Content Analysis

### Purpose

Use validated patterns from Phase 1 to enhance LLM analysis of document content, with iterative refinement based on new findings.

### Enhanced Context from Phase 1

Phase 2 LLM calls receive rich context:
- Validated numbering schemes and formatting patterns
- Expected document elements (from TOC or section implications)
- Font signatures for different content types
- Specific validation requests ("look for missing section 6.4.3")

### Iterative Process

1. Execute LLM analysis with Phase 1 pattern context
2. Extract new findings and compare against Phase 1 expectations
3. Update knowledge state and adjust pattern confidence
4. Generate updated projections for next analysis batch

This iterative approach progressively refines document understanding.

---

## Phase 3: Completion Assessment

### Purpose

Evaluate analysis completeness using multi-dimensional metrics to determine when sufficient understanding has been achieved.

### Completion Metrics

- **Pattern validation completeness**: All major pattern types validated
- **Content coverage**: Percentage of expected elements found
- **Validation priorities**: High-priority tasks addressed
- **Knowledge gaps**: Identified gaps resolved
- **Overall completeness score**: Combined metric determining analysis sufficiency

### Threshold-Based Decision

When completeness metrics exceed configured thresholds (e.g., 0.75 overall), analysis is considered complete. Otherwise, additional iterations or sampling may be recommended.

---

## Key Design Decisions

### Why Phase 0 Exists

**Problem**: Analyzing all 756 pages with LLM is prohibitively expensive.

**Solution**: Phase 0 performs cheap regex scan across full document, then uses LLM once to recommend which pages are most valuable for detailed analysis.

**Benefit**: $2-3 for Phase 0 + $20-30 for Phase 1 (20 pages) vs $500+ for full document analysis.

### Why Single-Page Processing

**Problem**: Multi-page LLM requests caused API timeouts and reliability issues.

**Solution**: Process one page at a time sequentially, accumulating knowledge between pages.

**Benefit**: Consistent performance, no timeouts, still maintains comprehensive analysis through knowledge accumulation.

*See PATTERN_DETECTION_EVOLUTION.md for detailed analysis*

### Why Different Formats for Phase 0 vs Phase 1

**Phase 0 Format** (line-based):
- **Purpose**: Fast regex scanning across full document
- **Optimization**: Minimal metadata, flat structure
- **Trade-off**: No font information, but scanning speed critical

**Phase 1 Format** (detailed blocks):
- **Purpose**: Rich context for pattern validation
- **Optimization**: Font metadata, positioning, block grouping
- **Trade-off**: Larger data size, but only processing ~20 pages

### Why Pattern-Driven Sampling

**Alternative approach**: Use rigid formulas (e.g., "10% of pages from front matter")

**Chosen approach**: Let regex results guide sampling (prioritize pages with navigation markers)

**Rationale**: Documents vary widely in structure. Pattern-driven approach adapts to actual document organization rather than assuming uniform structure.

---

## Appendix A: Regex Pattern Catalog

### Navigation/TOC Indicators
```python
{
    "toc_heading": r"^(Table of Contents|Contents|List of (Tables|Figures|Equations))$",
    "toc_entry": r"^([A-Z]?[\d\.]+|Figure|Table)\s+.+\s+\.{3,}\s+(\d+)$",
    "list_heading": r"^List of (Tables|Figures)$"
}
```

### Section Structure Patterns
```python
{
    "hierarchical_section": r"^(\d+\.[\d\.]+)\s+([A-Z][A-Za-z0-9 ,\-()]+)$",
    "appendix_section": r"^([A-Z]\.\d+(?:\.\d+)*)\s+([A-Z][A-Za-z0-9 ,\-()]+)$",
    "chapter_heading": r"^(Chapter|Section|Part|Appendix)\s+(\d+|[A-Z])[\s:]"
}
```

### Content Type Indicators
```python
{
    "figure_title": r"^Figure\s+([A-Z]?[\d\-]+)\s+[–\-]\s+(.+)$",
    "table_title": r"^Table\s+([\d\-]+)\s+[–\-]\s+(.+)$",
    "equation_number": r"\((\d+\-\d+)\)$"
}
```

### Document Region Markers
```python
{
    "front_matter": r"^(Abstract|Foreword|Preface|Executive Summary|Introduction)$",
    "back_matter": r"^(References|Bibliography|Glossary|Index|Acronyms|Abbreviations)$",
    "annex_marker": r"^(Annex|Appendix)\s+([A-Z])[\s:]?"
}
```

---

## Appendix B: Data Format Specifications

### Phase 0 Line-Based Format

Optimized for regex scanning across full document:

```json
{
  "document_id": "h264_spec",
  "total_pages": 756,
  "pages": [
    {
      "page": 50,
      "lines": [
        {"line_num": 1, "text": "6.4.2.1 Inverse macroblock partition scanning process"},
        {"line_num": 2, "text": "Input to this process is the index of a macroblock partition."},
        {"line_num": 3, "text": ""}
      ]
    }
  ]
}
```

**Key characteristics**:
- **Page-relative line numbers**: Explicit line numbering (1-indexed)
- **Minimal metadata**: Only page, line_num, text
- **Flat structure**: No blocks, no font information

### Phase 1 Detailed Format

Provides rich context for pattern validation:

```json
{
  "page_index": 50,
  "blocks": [
    {
      "text_lines": [
        "6.4.2.1 Inverse macroblock partition scanning process"
      ],
      "font_name": "TimesNewRomanPS-BoldMT",
      "font_size": 10.0,
      "y0": 100.0,
      "x0": 54.48
    },
    {
      "text_lines": [
        "Input to this process is the index of a macroblock partition mbPartIdx.",
        "Output of this process is the location ( x, y ) of the upper-left luma sample."
      ],
      "font_name": "TimesNewRomanPSMT",
      "font_size": 10.0,
      "y0": 115.0,
      "x0": 54.48
    }
  ]
}
```

**Key characteristics**:
- **Implicit line numbers**: Array index = line number (0-indexed array, presented as 1-indexed to LLM)
- **Font metadata**: Family, size, style for pattern consistency analysis
- **Positioning**: Y/X coordinates for spatial context
- **Block grouping**: Related text lines grouped by formatting

### Phase 0 Regex Scan Output

Sampled matches with location tracking:

```json
{
  "pattern_results": {
    "toc_entries": {
      "total_matches": 132,
      "sampling_applied": "front_3_back_3_random_5",
      "sampled_matches": [
        {"page": 5, "line": 12, "text": "J.8.4 Initialization ........................... 485"},
        {"page": 5, "line": 13, "text": "J.8.5 Decoding process ......................... 486"},
        {"page": 6, "line": 8, "text": "0.1 Overview ................................... 1"}
      ]
    },
    "section_headings": {
      "total_matches": 1247,
      "sampling_applied": "front_3_back_3_random_5",
      "sampled_matches": [...]
    }
  }
}
```

---

## Appendix C: Sampling Strategy Algorithm

Parameterized sampling to reduce LLM input size while maintaining representative coverage:

```python
def sample_matches(matches, threshold_low=10, threshold_high=30,
                   front_count=3, back_count=3,
                   random_medium=3, random_large=5):
    """
    Apply front + back + random middle sampling

    Args:
        matches: List of regex matches
        threshold_low: Include all if N <= this
        threshold_high: Switch to large random at this point
        front_count: Items from beginning
        back_count: Items from end
        random_medium: Random items for medium sets
        random_large: Random items for large sets

    Returns:
        Sampled subset of matches
    """
    N = len(matches)

    if N <= threshold_low:
        return matches  # All items

    elif N <= threshold_high:
        front = matches[:front_count]
        back = matches[-back_count:]
        middle = matches[front_count:-back_count]
        random_middle = random.sample(middle, min(random_medium, len(middle)))
        return front + random_middle + back

    else:
        front = matches[:front_count]
        back = matches[-back_count:]
        middle = matches[front_count:-back_count]
        random_middle = random.sample(middle, min(random_large, len(middle)))
        return front + random_middle + back
```

**Default parameters**: 10, 30, 3, 3, 3, 5

**Example**: 132 matches → 3 + 5 + 3 = 11 sampled items

---

## Appendix D: Component Interfaces

### Phase 0 Components

```python
class DocumentFlattener:
    """Convert block-based document to line-based format"""
    def flatten_document(self, doc_blocks: Dict) -> Dict:
        """Returns: {"pages": [{"page": N, "lines": [...]}]}"""

class DocumentScanner:
    """Execute regex patterns across full document"""
    def scan_full_document(self, flattened_doc: Dict, patterns: Dict) -> Dict:
        """Returns: {"pattern_name": {"total_matches": N, "matches": [...]}}"""

class SamplingStrategy:
    """Apply parameterized sampling to matches"""
    def sample(self, matches: List, params: SamplingParams) -> List:
        """Returns: Sampled subset of matches"""

class LLMSamplingAdvisor:
    """Generate page sampling strategy via LLM"""
    def recommend_sampling(self, regex_summary: Dict) -> List[int]:
        """Returns: List of page numbers to analyze in Phase 1"""
```

### Phase 1 Components

```python
class ComprehensivePatternValidator:
    """Single LLM call handler for pattern validation"""
    def analyze_page(self, page_data: Dict, knowledge_state: Dict) -> PageAnalysisResult:
        """Execute comprehensive pattern validation for single page"""

class KnowledgeTracker:
    """Accumulate knowledge across sequential page analysis"""
    def update(self, page_result: PageAnalysisResult):
        """Update knowledge state with new page findings"""

    def get_context_for_next_page(self) -> Dict:
        """Get accumulated knowledge for next page analysis"""
```

---

## Summary

The Pattern Detection Architecture provides a four-phase approach balancing cost efficiency, analysis quality, and system reliability:

1. **Phase 0**: Pattern-driven strategic sampling (cheap, full document)
2. **Phase 1**: Sequential comprehensive validation (expensive, selected pages)
3. **Phase 2**: Iterative content analysis (context-enhanced)
4. **Phase 3**: Completeness assessment (confidence-based)

This architecture enables intelligent document structure analysis while minimizing LLM costs through strategic preprocessing and sampling.