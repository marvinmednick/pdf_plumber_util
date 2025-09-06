"""Prompt templates for LLM document analysis."""

import json
from typing import Dict, List, Any, Optional


class PromptTemplates:
    """Collection of prompt templates for different analysis tasks."""
    
    @staticmethod
    def header_footer_analysis(
        total_pages: int,
        group_ranges: List[str],
        individual_pages: List[int],
        selected_page_indexes: List[int],
        page_data: List[Dict[str, Any]],
        page_width: float = 612,
        page_height: float = 792,
        footer_boundary: Optional[float] = None
    ) -> str:
        """Generate header/footer analysis prompt."""
        
        system_prompt = """You are a document structure analyst specializing in technical specifications. Your task is to analyze PDF document pages and identify header/footer boundaries to distinguish main content areas from page margins.

You will receive contextual block data from randomly sampled pages with spacing, font, and position metadata. Focus on identifying patterns that consistently appear at page tops/bottoms across the sample.

Important: Headers/footers may be absent on some pages or vary by document section. Provide specific text identification for each page."""

        footer_boundary_text = f"- Current programmatic footer boundary: {footer_boundary}pt" if footer_boundary else ""
        
        user_prompt = f"""Analyze these {len(selected_page_indexes)} randomly sampled pages from a {total_pages}-page technical document to identify header/footer patterns:

**IMPORTANT**: Page numbers refer to document position (page index), NOT printed page numbers on the page.
- Document has pages indexed 1-{total_pages}
- Printed page numbers may be different: roman numerals (i, ii, iii), missing, or offset
- When you identify page numbers in footers, note both the page index AND the printed page number

**Sampling Strategy**: 
- 3 groups of 4 consecutive pages: {', '.join(group_ranges)}
- 4 individual pages: {', '.join(map(str, individual_pages))}
- Selected page indexes: {', '.join(map(str, selected_page_indexes))}

**Analysis Objective**: Distinguish main content area from header/footer margins
**Document Info**:
- Total pages: {total_pages}
- Page dimensions: {page_width} x {page_height} pts
{footer_boundary_text}

**Key Guidelines**:
- Headers/footers may be ABSENT on some pages (title pages, chapter starts, etc.)
- Patterns may be INCONSISTENT across document sections
- Some pages may have headers but no footers, or vice versa
- Identify the actual TEXT content of headers/footers for each page

**Document Element Identification**:

**CRITICAL: Avoid Double Categorization**
- Each text element should appear in ONLY ONE category
- Table titles (starting with "Table X-Y") belong ONLY in table_titles, NOT section_headings
- Figure titles (starting with "Figure X-Y") belong ONLY in figure_titles, NOT section_headings
- TOC entries belong ONLY in table_of_contents, NOT section_headings
- True section headings are structural document hierarchy, not content captions

**Section Headers** (document structure ONLY):
- Look for lines with numbering patterns (1, 1.1, 1.1.1, A, A.1, etc.) that represent document hierarchy
- Bold or larger fonts often indicate section headings
- Usually represent chapters, sections, subsections in document hierarchy
- May be positioned differently (left-aligned, indented, or centered)
- Often have extra spacing above/below compared to body text
- **EXCLUDE**: Do NOT categorize "Table X-Y" or "Figure X-Y" titles as section headings

**Figure Titles** (captions and references):
- Usually start with "Figure" followed by number (Figure 6-2, Figure A.1, etc.)
- Often followed by dash or colon and descriptive text
- May appear above or below figures/diagrams
- Typically have consistent font styling (often italic or smaller)
- These are content captions, NOT document structure

**Table Titles** (captions and references):
- Usually start with "Table" followed by number (Table 1, Table A-1, etc.)
- Often followed by dash or colon and descriptive text
- May appear above or below tables
- Typically have consistent font styling (often italic or smaller)
- These are content captions, NOT document structure

**Table of Contents (TOC)** (document organization listings):
- Look for pages containing structured lists of document sections with page numbers
- TOC entries typically show document hierarchy through numbering (1, 1.1, 1.1.1, A, A.1, etc.)
- Often includes leader patterns (dots, dashes) connecting titles to page numbers
- May include specialized TOC sections (List of Figures, List of Tables, List of Equations)
- TOC section headers like "Contents", "Table of Contents", "List of Figures"
- Hierarchical indentation patterns showing document structure
- Page number references (right-aligned or after leader patterns)
- Format patterns like "1.1 Introduction ..................... 5"

**JSON Format Requirements**:
- All y-positions must be single numeric values (e.g., 735.5, not "735-740" or ranges)
- Use decimal notation for precision (e.g., 66.0, 14.0)
- Font sizes should be numeric (e.g., 14.0, not "14pt")
- No mathematical expressions in JSON values
- All confidence levels must be exactly "High", "Medium", or "Low"

**Pages Data**:
{json.dumps(page_data, indent=2)}

For each page index, analyze the blocks and identify:
1. Specific header text (or "NONE" if absent)
2. Specific footer text (or "NONE" if absent)
3. **If footer contains page numbering**: Note both the page index and printed page number
4. **Content positioning**: First and last content y-positions (excluding headers/footers)
5. **Document elements**: Distinguish between and identify:
   - Section headings (document structure: 1.1, 2.3.4, A.1, etc.)
   - Figure titles (Figure 6-2, Figure A.1, etc.)
   - Table titles (Table 1, Table A-1, etc.)
   - Table of Contents (TOC) entries and structure
6. **TOC detection**: Identify table of contents patterns:
   - TOC page locations and boundaries
   - TOC entry hierarchical structure
   - Page number references and formatting patterns
7. Main content boundaries
8. Cross-page pattern consistency

**Response Format**:
```json
{{
  "sampling_summary": {{
    "page_indexes_analyzed": {selected_page_indexes},
    "group_ranges": {group_ranges},
    "individual_pages": {individual_pages}
  }},
  "per_page_analysis": [
    {{
      "page_index": 1,
      "header": {{"detected": true, "text": "Document Title", "y_position": 52}},
      "footer": {{"detected": true, "text": "Page 1", "y_position": 748, "printed_page_number": "1"}},
      "content_positioning": {{
        "first_content_y": 66.0,
        "last_content_y": 735.0
      }},
      "document_elements": {{
        "section_headings": [
          {{
            "text": "1.1 Overview",
            "section_number": "1.1", 
            "section_name": "Overview",
            "y_position": 120.0,
            "font_name": "Arial-Bold",
            "font_size": 14.0,
            "hierarchy_level": 2
          }}
        ],
        "figure_titles": [
          {{
            "text": "Figure 6-2 – Nominal vertical and horizontal sampling locations",
            "figure_number": "6-2",
            "figure_title": "Nominal vertical and horizontal sampling locations",
            "y_position": 255.0,
            "font_name": "Times-Italic",
            "font_size": 10.0
          }}
        ],
        "table_titles": [
          {{
            "text": "Table 1 – Overview of profile and level limits",
            "table_number": "1",
            "table_title": "Overview of profile and level limits",
            "y_position": 180.0,
            "font_name": "Times-Italic", 
            "font_size": 10.0
          }}
        ],
        "table_of_contents": [
          {{
            "text": "1.1 Introduction ..................... 5",
            "toc_entry_title": "Introduction",
            "section_number": "1.1",
            "page_reference": "5",
            "y_position": 150.0,
            "font_name": "Times-Roman",
            "font_size": 10.0,
            "hierarchy_level": 2,
            "leader_pattern": "dots",
            "toc_type": "main_contents"
          }}
        ]
      }}
    }}
  ],
  "header_pattern": {{
    "consistent_pattern": true,
    "pages_with_headers": [1, 2, 3],
    "pages_without_headers": [4, 5],
    "typical_content": ["Document Title", "Chapter Name"],
    "y_boundary_typical": 55,
    "confidence": "High|Medium|Low",
    "reasoning": "explanation"
  }},
  "footer_pattern": {{
    "consistent_pattern": true,
    "pages_with_footers": [1, 2, 3, 4, 5],
    "pages_without_footers": [],
    "typical_content": ["Page X", "© Copyright"],
    "y_boundary_typical": 748,
    "confidence": "High|Medium|Low", 
    "reasoning": "explanation"
  }},
  "page_numbering_analysis": {{
    "numbering_system_detected": "arabic|roman|mixed|none",
    "patterns": [
      {{"page_indexes": [1, 2], "format": "arabic", "examples": ["1", "2"]}},
      {{"page_indexes": [3, 4], "format": "roman", "examples": ["iii", "iv"]}}
    ],
    "missing_page_numbers": [],
    "offset_detected": {{"offset": 0, "explanation": "page numbers match indexes"}}
  }},
  "content_area_boundaries": {{
    "main_content_starts_after_y": 65,
    "main_content_ends_before_y": 735,
    "confidence": "High|Medium|Low"
  }},
  "content_positioning_analysis": {{
    "positioning_consistency": "High|Medium|Low",
    "typical_first_content_y": 66.0,
    "typical_last_content_y": 735.0,
    "content_height_variation": {{"min": 650.0, "max": 700.0, "avg": 675.0}},
    "confidence": "High|Medium|Low",
    "reasoning": "explanation of positioning patterns"
  }},
  "document_element_analysis": {{
    "section_headings": {{
      "detected": true,
      "hierarchy_levels_found": [1, 2, 3],
      "numbering_patterns": ["decimal", "nested"],
      "format_pattern": "Number + Title (e.g., '1.1 Overview')",
      "font_style_patterns": [
        {{"level": 1, "typical_font": "Arial-Bold", "typical_size": 16.0, "count": 3}},
        {{"level": 2, "typical_font": "Arial-Bold", "typical_size": 14.0, "count": 8}}
      ],
      "positioning_patterns": {{"typical_y_spacing": 24.0, "indentation_used": false}},
      "confidence": "High|Medium|Low",
      "reasoning": "explanation of section heading detection patterns"
    }},
    "figure_titles": {{
      "detected": true,
      "numbering_patterns": ["sequential", "hierarchical"],
      "format_pattern": "Figure + Number + Separator + Title (e.g., 'Figure 6-2 – Description')",
      "font_style_patterns": [
        {{"typical_font": "Times-Italic", "typical_size": 10.0, "count": 5}}
      ],
      "positioning_patterns": {{"relative_to_figures": "above|below", "typical_y_spacing": 12.0}},
      "confidence": "High|Medium|Low",
      "reasoning": "explanation of figure title detection patterns"
    }},
    "table_titles": {{
      "detected": true,
      "numbering_patterns": ["sequential", "hierarchical"],
      "format_pattern": "Table + Number + Separator + Title (e.g., 'Table 1 – Description')",
      "font_style_patterns": [
        {{"typical_font": "Times-Italic", "typical_size": 10.0, "count": 3}}
      ],
      "positioning_patterns": {{"relative_to_tables": "above|below", "typical_y_spacing": 12.0}},
      "confidence": "High|Medium|Low",
      "reasoning": "explanation of table title detection patterns"
    }},
    "table_of_contents": {{
      "detected": true,
      "toc_pages": [3, 4],
      "toc_types": ["main_contents", "list_of_figures"],
      "entry_format_patterns": [
        {{"type": "main_contents", "pattern": "Number + Title + Leaders + Page (e.g., '1.1 Introduction ......... 5')", "count": 15}},
        {{"type": "list_of_figures", "pattern": "Figure + Number + Title + Page (e.g., 'Figure 2-1 System Overview 23')", "count": 8}}
      ],
      "hierarchical_structure": {{
        "levels_detected": 3,
        "level_patterns": [
          {{"level": 1, "typical_font": "Times-Roman", "typical_size": 12.0, "indentation": 0}},
          {{"level": 2, "typical_font": "Times-Roman", "typical_size": 10.0, "indentation": 20}},
          {{"level": 3, "typical_font": "Times-Roman", "typical_size": 10.0, "indentation": 40}}
        ],
        "numbering_scheme": "decimal"
      }},
      "leader_patterns": [
        {{"type": "dots", "pattern": "..................", "pages": [3, 4]}},
        {{"type": "none", "pattern": "justified_spacing", "pages": [5]}}
      ],
      "page_reference_patterns": {{
        "alignment": "right_aligned",
        "format": "arabic_numbers",
        "consistency": "High"
      }},
      "content_validation": {{
        "cross_reference_check": "High|Medium|Low",
        "section_mapping_accuracy": "High|Medium|Low",
        "page_number_validation": "High|Medium|Low"
      }},
      "confidence": "High|Medium|Low",
      "reasoning": "explanation of TOC detection patterns and validation results"
    }}
  }},
  "insights": [
    "Key observations about header/footer patterns",
    "Content positioning patterns and consistency",
    "Section heading patterns and hierarchy structure",
    "Figure title formatting and positioning patterns",
    "Table title formatting and positioning patterns",
    "Table of Contents structure and organization patterns",
    "TOC hierarchical mapping and cross-reference validation",
    "Notable exceptions or variations"
  ]
}}
```

Provide structured analysis with confidence scores and specific reasoning for your determinations."""

        return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    
    @staticmethod
    def section_hierarchy_analysis(
        page_data: List[Dict[str, Any]],
        known_header_footer_patterns: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate section hierarchy analysis prompt."""
        
        system_prompt = """You are a document structure analyst specializing in identifying section hierarchies in technical documents. Your task is to identify section headings, numbering patterns, and hierarchical structures.

Focus on distinguishing section headings from body text based on font styles, positioning, numbering patterns, and content characteristics."""

        header_footer_context = ""
        if known_header_footer_patterns:
            header_footer_context = f"""

**Known Header/Footer Patterns** (use to distinguish from section headings):
{json.dumps(known_header_footer_patterns, indent=2)}"""

        user_prompt = f"""Analyze these pages to identify section hierarchy patterns:

{header_footer_context}

**Pages Data**:
{json.dumps(page_data, indent=2)}

Identify:
1. Section headings and their hierarchy levels
2. Numbering patterns (1.0, 1.1, 1.1.1, etc.)
3. Font style patterns for different heading levels
4. Positioning and spacing patterns

**Response Format**:
```json
{{
  "section_hierarchy": {{
    "levels_detected": 3,
    "numbering_pattern": "decimal",
    "font_patterns": [
      {{"level": 1, "typical_font": "Arial-Bold", "typical_size": 16, "examples": ["1. Introduction"]}},
      {{"level": 2, "typical_font": "Arial-Bold", "typical_size": 14, "examples": ["1.1 Overview"]}}
    ]
  }},
  "per_page_sections": [
    {{
      "page_index": 1,
      "sections_found": [
        {{"text": "1. Introduction", "level": 1, "y_position": 120}}
      ]
    }}
  ],
  "confidence": "High|Medium|Low",
  "insights": ["Key observations about section patterns"]
}}
```"""

        return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    
    @staticmethod
    def toc_analysis(
        page_data: List[Dict[str, Any]],
        known_section_patterns: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate Table of Contents analysis prompt."""
        
        system_prompt = """You are a document structure analyst specializing in identifying Table of Contents (TOC) in technical documents. Your task is to locate TOC pages and extract the document structure they represent.

Look for pages with section titles followed by page numbers, typically with leader dots or spacing patterns."""

        section_context = ""
        if known_section_patterns:
            section_context = f"""

**Known Section Patterns** (for cross-validation):
{json.dumps(known_section_patterns, indent=2)}"""

        user_prompt = f"""Analyze these pages to identify Table of Contents:

{section_context}

**Pages Data**:
{json.dumps(page_data, indent=2)}

Identify:
1. Pages that contain TOC entries
2. TOC structure and hierarchy
3. Page number references
4. Cross-validation with known section patterns

**Response Format**:
```json
{{
  "toc_detected": true,
  "toc_pages": [2, 3],
  "toc_structure": [
    {{"title": "1. Introduction", "page_number": "5", "level": 1}},
    {{"title": "1.1 Overview", "page_number": "6", "level": 2}}
  ],
  "validation": {{
    "cross_references_valid": true,
    "section_pattern_match": "High|Medium|Low"
  }},
  "confidence": "High|Medium|Low",
  "insights": ["Key observations about TOC structure"]
}}
```"""

        return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    
    @staticmethod
    def multi_objective_analysis(
        page_data: List[Dict[str, Any]],
        primary_focus: str,
        total_pages: int,
        sampling_info: Dict[str, Any]
    ) -> str:
        """Generate multi-objective analysis prompt with priority focus."""
        
        system_prompt = f"""You are a document structure analyst performing multi-objective analysis of technical documents. Your primary focus is {primary_focus}, but you should simultaneously collect information about other structural elements.

This is part of a continuous learning approach where each analysis contributes to growing knowledge about the document's structure."""

        user_prompt = f"""Perform multi-objective analysis of this {total_pages}-page document with primary focus on {primary_focus}:

**Sampling Info**:
{json.dumps(sampling_info, indent=2)}

**Pages Data**:
{json.dumps(page_data, indent=2)}

**Analysis Instructions**:
PRIMARY FOCUS: {primary_focus}
- Provide detailed analysis for your primary objective
- Assign confidence scores based on evidence strength

SECONDARY COLLECTION (simultaneous information gathering):
- Font style usage patterns and their likely purposes
- Structural element identification (headings, references, special content)
- Cross-reference mapping opportunities
- Pattern consistency across pages
- Anomaly detection for unusual formatting

**Response Format**:
```json
{{
  "primary_focus": "{primary_focus}",
  "primary_analysis": {{
    // Detailed analysis specific to primary focus
  }},
  "secondary_observations": {{
    "font_style_patterns": [
      {{"font": "Arial-Bold", "size": 14, "likely_purpose": "section_heading", "confidence": "High"}}
    ],
    "structural_elements": [
      {{"type": "heading", "page": 1, "text": "Introduction", "confidence": "High"}}
    ],
    "cross_references": [
      {{"type": "page_reference", "text": "see page 10", "confidence": "Medium"}}
    ],
    "anomalies": [
      {{"page": 5, "description": "Missing header", "impact": "pattern_deviation"}}
    ]
  }},
  "growing_knowledge": {{
    "pattern_confidence_updates": [
      {{"pattern": "header_format", "new_confidence": "High", "evidence": "consistent across 80% of pages"}}
    ],
    "recommendations": [
      "Focus on pages 10-15 for section pattern validation",
      "Investigate pages 20-25 for TOC validation"
    ]
  }},
  "overall_confidence": "High|Medium|Low"
}}
```"""

        return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    
    @staticmethod
    def additional_section_heading_analysis(
        total_pages: int,
        analyzed_pages: List[int],
        page_data: List[Dict[str, Any]],
        previous_patterns: Optional[Dict[str, Any]] = None,
        page_width: float = 612,
        page_height: float = 792
    ) -> str:
        """Generate additional section heading analysis prompt for unused pages."""
        
        system_prompt = """You are a document structure analyst specializing in identifying additional section heading levels and patterns not found in previous analysis. Your task is to analyze previously unused pages to discover new heading formats, numbering patterns, and document structure elements.

Focus on identifying NEW patterns that complement existing analysis, including:
- Additional section heading levels, fonts, and numbering formats
- New table headings, figure headings, or equation headings  
- Previously undetected font styles and formatting patterns
- Table of Contents (TOC) detection and analysis
- TOC start locations and content organization
- Validation of header/footer consistency with previous findings

Important: These pages were specifically selected because they were NOT analyzed in previous document analysis passes."""

        previous_context = ""
        if previous_patterns:
            previous_context = f"""
**Previous Analysis Context** (for reference and validation):
{json.dumps(previous_patterns, indent=2)}

Use this context to:
1. Identify NEW patterns not previously found
2. Validate consistency of header/footer patterns
3. Discover additional hierarchy levels or formatting variations
4. Find supplementary content types (equations, appendices, etc.)
"""

        user_prompt = f"""Analyze these {len(analyzed_pages)} previously unused pages from a {total_pages}-page technical document to identify ADDITIONAL section heading patterns and document structure elements:

{previous_context}

**Unused Pages Being Analyzed**: {', '.join(map(str, analyzed_pages))}
**Document Info**:
- Total pages: {total_pages}
- Page dimensions: {page_width} x {page_height} pts

**Analysis Objectives**:
1. **NEW Section Heading Levels**: Identify section heading formats not found in previous analysis
2. **Additional Content Types**: Find equation headings, appendix sections, or other structured content
3. **Font Style Variations**: Discover new font combinations or formatting patterns
4. **Table of Contents Detection**: Identify TOC sections, list of figures, tables, equations
5. **TOC Start Detection**: Determine if and where TOC sections begin on each page
6. **Header/Footer Consistency**: Validate that header/footer patterns match previous findings
7. **Numbering Pattern Extensions**: Find continuation or variation of numbering schemes

**Critical Instructions**:
- Focus on ADDITIONAL patterns that complement existing analysis
- Identify section headings by structure (numbered hierarchy) NOT content captions
- Distinguish section headings from figure/table titles based on document hierarchy role
- Each text element should appear in only ONE category

**Document Element Categories**:

**Section Headers** (NEW hierarchical patterns only):
- Look for numbered hierarchy patterns not previously identified
- Focus on levels, fonts, or numbering schemes not found before  
- May include appendix sections (Appendix A, A.1, etc.)
- Could include specialized sections (Abstract, Bibliography, Index)

**Additional Content Types**:
- Equation headings/labels (Equation 1, Eq. 2.1, etc.)
- Appendix headings and sub-sections
- Bibliography/Reference section formatting
- Index or glossary patterns

**Table of Contents Detection**:
- Main table of contents (document structure listing)
- List of figures (figure captions and page numbers)
- List of tables (table captions and page numbers)  
- List of equations (equation references and page numbers)
- TOC section headers ("Contents", "Table of Contents", "List of Figures", etc.)
- TOC entry formatting patterns (dots, page numbers, indentation)

**TOC Start Detection**:
- Identify if any TOC section begins on the analyzed page
- Note the exact y-position where the TOC section starts
- Determine TOC type (main contents, figures, tables, equations)
- Identify TOC formatting patterns and structure

**Pages Data**:
{json.dumps(page_data, indent=2)}

**Response Format**:
```json
{{
  "sampling_summary": {{
    "pages_analyzed": {analyzed_pages},
    "analysis_type": "additional_section_heading_analysis",
    "total_pages_in_document": {total_pages},
    "additional_patterns_found": true,
    "new_section_levels_found": 2,
    "new_content_types_found": ["equations", "appendix"],
    "header_footer_consistency": "consistent|inconsistent|partial"
  }},
  "per_page_analysis": [
    {{
      "page_index": 25,
      "header": {{"detected": true, "text": "Document Title", "y_position": 52, "consistency_check": "matches_previous_pattern"}},
      "footer": {{"detected": true, "text": "Page 25", "y_position": 748, "consistency_check": "matches_previous_pattern"}},
      "new_document_elements": {{
        "section_headings": [
          {{
            "text": "A.2.1 Detailed Specifications",
            "section_number": "A.2.1", 
            "section_name": "Detailed Specifications",
            "y_position": 120.0,
            "font_name": "Arial-Bold",
            "font_size": 12.0,
            "hierarchy_level": 3,
            "pattern_type": "appendix_subsection",
            "new_pattern": true
          }}
        ],
        "equation_headings": [
          {{
            "text": "Equation 3.2",
            "equation_number": "3.2",
            "y_position": 200.0,
            "font_name": "Times-Italic",
            "font_size": 10.0,
            "new_pattern": true
          }}
        ],
        "figure_titles": [],
        "table_titles": [],
        "toc_detection": {{
          "toc_sections_found": [
            {{
              "toc_type": "main_contents|list_of_figures|list_of_tables|list_of_equations",
              "section_header": "Table of Contents",
              "starts_on_page": true,
              "start_y_position": 150.0,
              "entry_count": 15,
              "formatting_pattern": "numbered_sections_with_page_numbers",
              "typical_entry_format": "1.1 Introduction ..................... 5"
            }}
          ]
        }}
      }}
    }}
  ],
  "new_patterns_identified": {{
    "section_heading_patterns": {{
      "appendix_sections": {{
        "detected": true,
        "numbering_pattern": "A.1, A.2, A.2.1",
        "font_patterns": [
          {{"level": "appendix_main", "typical_font": "Arial-Bold", "typical_size": 14.0}},
          {{"level": "appendix_sub", "typical_font": "Arial-Bold", "typical_size": 12.0}}
        ],
        "confidence": "High|Medium|Low"
      }},
      "specialized_sections": {{
        "detected": true,
        "types_found": ["bibliography", "index"],
        "font_patterns": [
          {{"type": "bibliography", "typical_font": "Arial-Bold", "typical_size": 14.0}}
        ],
        "confidence": "High|Medium|Low"
      }}
    }},
    "equation_patterns": {{
      "detected": true,
      "numbering_patterns": ["sequential", "hierarchical"],
      "format_pattern": "Equation + Number (e.g., 'Equation 3.2')",
      "font_style_patterns": [
        {{"typical_font": "Times-Italic", "typical_size": 10.0}}
      ],
      "confidence": "High|Medium|Low"
    }},
    "toc_patterns": {{
      "toc_sections_detected": true,
      "toc_types_found": ["main_contents", "list_of_figures"],
      "toc_formatting_patterns": [
        {{"type": "main_contents", "entry_format": "numbered_with_dots_and_pages", "typical_font": "Times-Roman", "typical_size": 10.0}},
        {{"type": "list_of_figures", "entry_format": "figure_titles_with_pages", "typical_font": "Times-Roman", "typical_size": 10.0}}
      ],
      "toc_start_pages": [
        {{"page": 5, "toc_type": "main_contents", "start_y_position": 120.0}},
        {{"page": 8, "toc_type": "list_of_figures", "start_y_position": 100.0}}
      ],
      "confidence": "High|Medium|Low"
    }},
    "content_type_extensions": {{
      "appendix_content": {{"pages": [25, 26], "sections_found": 3}},
      "reference_content": {{"pages": [28], "sections_found": 1}},
      "equation_content": {{"pages": [10, 15], "equations_found": 4}},
      "toc_content": {{"pages": [5, 8], "toc_sections_found": 2}}
    }}
  }},
  "consistency_validation": {{
    "header_pattern_validation": {{
      "consistent_with_previous": true,
      "variations_found": [],
      "confidence": "High|Medium|Low"
    }},
    "footer_pattern_validation": {{
      "consistent_with_previous": true,
      "variations_found": [],
      "confidence": "High|Medium|Low"
    }},
    "page_margin_validation": {{
      "content_boundaries_consistent": true,
      "margin_variations": [],
      "confidence": "High|Medium|Low"
    }}
  }},
  "insights": [
    "Key observations about additional patterns found",
    "Validation results for header/footer consistency", 
    "New content types and their formatting patterns",
    "TOC sections detected and their formatting patterns",
    "TOC start locations and organizational structure",
    "Extensions to existing numbering or hierarchy schemes",
    "Notable exceptions or specialized formatting"
  ],
  "header_pattern": {{
    "detected": false,
    "pattern_type": "N/A - focus on additional content analysis",
    "confidence": "N/A"
  }},
  "footer_pattern": {{
    "detected": false,
    "pattern_type": "N/A - focus on additional content analysis", 
    "confidence": "N/A"
  }},
  "page_numbering_analysis": {{
    "pattern": "consistent_with_previous|variations_found|not_applicable",
    "confidence": "High|Medium|Low"
  }},
  "content_area_boundaries": {{
    "main_content_starts_after_y": 50.0,
    "main_content_ends_before_y": 750.0,
    "confidence": "High|Medium|Low"
  }}
}}
```

Focus on discovering NEW patterns while validating consistency with previous analysis."""

        return f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
    
    @staticmethod
    def get_prompt_for_analysis_type(
        analysis_type: str,
        **kwargs
    ) -> str:
        """Get prompt template for specific analysis type.
        
        Args:
            analysis_type: Type of analysis ("headers-footers", "sections", "toc", "multi-objective", "additional-sections")
            **kwargs: Arguments specific to the analysis type
            
        Returns:
            Formatted prompt string
        """
        prompt_generators = {
            "headers-footers": PromptTemplates.header_footer_analysis,
            "sections": PromptTemplates.section_hierarchy_analysis,
            "toc": PromptTemplates.toc_analysis,
            "multi-objective": PromptTemplates.multi_objective_analysis,
            "additional-sections": PromptTemplates.additional_section_heading_analysis
        }
        
        if analysis_type not in prompt_generators:
            available = ", ".join(prompt_generators.keys())
            raise ValueError(f"Unknown analysis type '{analysis_type}'. Available: {available}")
        
        generator = prompt_generators[analysis_type]
        return generator(**kwargs)