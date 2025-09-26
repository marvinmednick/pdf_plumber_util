"""Response parsing and validation for LLM document analysis."""

import json
import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from ..core.exceptions import AnalysisError


class ConfidenceLevel(Enum):
    """Confidence levels for analysis results."""
    HIGH = "High"
    MEDIUM = "Medium" 
    LOW = "Low"


@dataclass
class HeaderFooterAnalysisResult:
    """Structured result from header/footer analysis."""
    sampling_summary: Dict[str, Any]
    per_page_analysis: List[Dict[str, Any]]
    header_pattern: Dict[str, Any]
    footer_pattern: Dict[str, Any]
    page_numbering_analysis: Dict[str, Any]
    content_area_boundaries: Dict[str, Any]
    insights: List[str]
    content_positioning_analysis: Optional[Dict[str, Any]] = None
    document_element_analysis: Optional[Dict[str, Any]] = None
    # Maintain backward compatibility 
    section_heading_analysis: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    
    @property
    def header_confidence(self) -> ConfidenceLevel:
        """Get header pattern confidence level."""
        conf_str = self.header_pattern.get('confidence', 'Low')
        return ConfidenceLevel(conf_str)
    
    @property
    def footer_confidence(self) -> ConfidenceLevel:
        """Get footer pattern confidence level."""
        conf_str = self.footer_pattern.get('confidence', 'Low')
        return ConfidenceLevel(conf_str)
    
    def get_content_boundaries(self) -> Dict[str, Any]:
        """Get validated content area boundaries."""
        boundaries = self.content_area_boundaries
        
        # Handle None boundaries gracefully
        if boundaries is None:
            return {
                'start_after_y': 0.0,
                'end_before_y': 792.0,
                'confidence': 'Low'
            }
        
        # Get values with proper defaults and None handling
        start_y_val = boundaries.get('main_content_starts_after_y')
        end_y_val = boundaries.get('main_content_ends_before_y')
        
        # Convert to float with None handling
        try:
            start_y = float(start_y_val) if start_y_val is not None else 0.0
        except (ValueError, TypeError):
            start_y = 0.0
            
        try:
            end_y = float(end_y_val) if end_y_val is not None else 792.0
        except (ValueError, TypeError):
            end_y = 792.0
        
        return {
            'start_after_y': start_y,
            'end_before_y': end_y,
            'confidence': boundaries.get('confidence', 'Low')
        }
    
    def get_pages_with_headers(self) -> List[int]:
        """Get list of page indexes that have headers."""
        return self.header_pattern.get('pages_with_headers', [])
    
    def get_pages_with_footers(self) -> List[int]:
        """Get list of page indexes that have footers.""" 
        return self.footer_pattern.get('pages_with_footers', [])
    
    def get_content_positioning_patterns(self) -> Optional[Dict[str, Any]]:
        """Get content positioning analysis if available."""
        return self.content_positioning_analysis
    
    def get_section_headings_by_page(self, page_index: int) -> List[Dict[str, Any]]:
        """Get section headings found on a specific page."""
        for page_analysis in self.per_page_analysis:
            if page_analysis.get('page_index') == page_index:
                # Check new structure first, fall back to old
                elements = page_analysis.get('document_elements', {})
                return elements.get('section_headings', page_analysis.get('section_headings', []))
        return []
    
    def get_all_section_headings(self) -> List[Dict[str, Any]]:
        """Get all section headings across all analyzed pages."""
        all_headings = []
        for page_analysis in self.per_page_analysis:
            # Use the new document_elements structure first, fall back to old structure
            elements = page_analysis.get('document_elements', {})
            headings = elements.get('section_headings', page_analysis.get('section_headings', []))
            
            for heading in headings:
                # Add page context to heading data
                heading_with_page = heading.copy()
                heading_with_page['page_index'] = page_analysis.get('page_index')
                all_headings.append(heading_with_page)
        return all_headings
    
    def get_font_style_patterns(self) -> List[Dict[str, Any]]:
        """Get font style patterns for section headings."""
        if self.section_heading_analysis:
            return self.section_heading_analysis.get('font_style_patterns', [])
        return []
    
    def get_figure_titles_by_page(self, page_index: int) -> List[Dict[str, Any]]:
        """Get figure titles found on a specific page."""
        for page_analysis in self.per_page_analysis:
            if page_analysis.get('page_index') == page_index:
                elements = page_analysis.get('document_elements', {})
                return elements.get('figure_titles', [])
        return []
    
    def get_table_titles_by_page(self, page_index: int) -> List[Dict[str, Any]]:
        """Get table titles found on a specific page."""
        for page_analysis in self.per_page_analysis:
            if page_analysis.get('page_index') == page_index:
                elements = page_analysis.get('document_elements', {})
                return elements.get('table_titles', [])
        return []
    
    def get_all_figure_titles(self) -> List[Dict[str, Any]]:
        """Get all figure titles across all analyzed pages."""
        all_figures = []
        for page_analysis in self.per_page_analysis:
            elements = page_analysis.get('document_elements', {})
            figures = elements.get('figure_titles', [])
            for figure in figures:
                figure_with_page = figure.copy()
                figure_with_page['page_index'] = page_analysis.get('page_index')
                all_figures.append(figure_with_page)
        return all_figures
    
    def get_all_table_titles(self) -> List[Dict[str, Any]]:
        """Get all table titles across all analyzed pages."""
        all_tables = []
        for page_analysis in self.per_page_analysis:
            elements = page_analysis.get('document_elements', {})
            tables = elements.get('table_titles', [])
            for table in tables:
                table_with_page = table.copy()
                table_with_page['page_index'] = page_analysis.get('page_index')
                all_tables.append(table_with_page)
        return all_tables
    
    def get_document_element_patterns(self) -> Optional[Dict[str, Any]]:
        """Get document element analysis patterns."""
        return self.document_element_analysis
    
    def get_toc_entries_by_page(self, page_index: int) -> List[Dict[str, Any]]:
        """Get table of contents entries found on a specific page."""
        for page_analysis in self.per_page_analysis:
            if page_analysis.get('page_index') == page_index:
                elements = page_analysis.get('document_elements', {})
                return elements.get('table_of_contents', [])
        return []
    
    def get_all_toc_entries(self) -> List[Dict[str, Any]]:
        """Get all table of contents entries across all analyzed pages."""
        all_toc_entries = []
        for page_analysis in self.per_page_analysis:
            elements = page_analysis.get('document_elements', {})
            toc_entries = elements.get('table_of_contents', [])
            for entry in toc_entries:
                entry_with_page = entry.copy()
                entry_with_page['page_index'] = page_analysis.get('page_index')
                all_toc_entries.append(entry_with_page)
        return all_toc_entries
    
    def get_toc_analysis_patterns(self) -> Optional[Dict[str, Any]]:
        """Get table of contents analysis patterns."""
        if self.document_element_analysis:
            return self.document_element_analysis.get('table_of_contents')
        return None
    
    def get_toc_pages(self) -> List[int]:
        """Get list of pages that contain table of contents."""
        toc_patterns = self.get_toc_analysis_patterns()
        if toc_patterns:
            return toc_patterns.get('toc_pages', [])
        return []
    
    def has_toc_detected(self) -> bool:
        """Check if table of contents was detected in the document."""
        toc_patterns = self.get_toc_analysis_patterns()
        if toc_patterns:
            return toc_patterns.get('detected', False)
        return False


@dataclass
class SectionAnalysisResult:
    """Structured result from section hierarchy analysis."""
    section_hierarchy: Dict[str, Any]
    per_page_sections: List[Dict[str, Any]]
    confidence: str
    insights: List[str]
    raw_response: Optional[str] = None
    
    def get_hierarchy_levels(self) -> int:
        """Get number of hierarchy levels detected."""
        return self.section_hierarchy.get('levels_detected', 0)
    
    def get_font_patterns(self) -> List[Dict[str, Any]]:
        """Get font patterns for different section levels."""
        return self.section_hierarchy.get('font_patterns', [])


@dataclass
class TOCAnalysisResult:
    """Structured result from TOC analysis."""
    toc_detected: bool
    toc_pages: List[int]
    toc_structure: List[Dict[str, Any]]
    validation: Dict[str, Any]
    confidence: str
    insights: List[str]
    raw_response: Optional[str] = None
    
    def get_toc_entries(self) -> List[Dict[str, Any]]:
        """Get structured TOC entries."""
        return self.toc_structure
    
    def validate_against_sections(self, section_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-validate TOC entries against known section patterns."""
        # Implementation would compare TOC structure with section patterns
        return self.validation


class ResponseParser:
    """Parser for LLM analysis responses."""
    
    def __init__(self):
        """Initialize response parser."""
        self.json_pattern = re.compile(r'```json\s*(.*?)\s*```', re.DOTALL)
    
    def parse_header_footer_response(self, response_content: str) -> HeaderFooterAnalysisResult:
        """Parse header/footer analysis response.
        
        Args:
            response_content: Raw LLM response content
            
        Returns:
            Structured HeaderFooterAnalysisResult
            
        Raises:
            AnalysisError: If response cannot be parsed
        """
        try:
            # Extract JSON from response
            json_data = self._extract_json_from_response(response_content)
            
            # Validate required fields
            required_fields = [
                'sampling_summary', 'per_page_analysis', 'header_pattern',
                'footer_pattern', 'page_numbering_analysis', 'content_area_boundaries'
            ]
            
            for field in required_fields:
                if field not in json_data:
                    raise AnalysisError(f"Missing required field '{field}' in LLM response")
            
            return HeaderFooterAnalysisResult(
                sampling_summary=json_data['sampling_summary'],
                per_page_analysis=json_data['per_page_analysis'],
                header_pattern=json_data['header_pattern'],
                footer_pattern=json_data['footer_pattern'],
                page_numbering_analysis=json_data['page_numbering_analysis'],
                content_area_boundaries=json_data['content_area_boundaries'],
                insights=json_data.get('insights', []),
                content_positioning_analysis=json_data.get('content_positioning_analysis'),
                document_element_analysis=json_data.get('document_element_analysis'),
                section_heading_analysis=json_data.get('section_heading_analysis') or json_data.get('document_element_analysis', {}).get('section_headings'),
                raw_response=response_content
            )
            
        except Exception as e:
            raise AnalysisError(f"Failed to parse header/footer analysis response: {e}")
    
    def parse_section_response(self, response_content: str) -> SectionAnalysisResult:
        """Parse section hierarchy analysis response."""
        try:
            json_data = self._extract_json_from_response(response_content)
            
            required_fields = ['section_hierarchy', 'per_page_sections', 'confidence']
            for field in required_fields:
                if field not in json_data:
                    raise AnalysisError(f"Missing required field '{field}' in section analysis response")
            
            return SectionAnalysisResult(
                section_hierarchy=json_data['section_hierarchy'],
                per_page_sections=json_data['per_page_sections'],
                confidence=json_data['confidence'],
                insights=json_data.get('insights', []),
                raw_response=response_content
            )
            
        except Exception as e:
            raise AnalysisError(f"Failed to parse section analysis response: {e}")
    
    def parse_toc_response(self, response_content: str) -> TOCAnalysisResult:
        """Parse TOC analysis response."""
        try:
            json_data = self._extract_json_from_response(response_content)
            
            required_fields = ['toc_detected', 'confidence']
            for field in required_fields:
                if field not in json_data:
                    raise AnalysisError(f"Missing required field '{field}' in TOC analysis response")
            
            return TOCAnalysisResult(
                toc_detected=json_data['toc_detected'],
                toc_pages=json_data.get('toc_pages', []),
                toc_structure=json_data.get('toc_structure', []),
                validation=json_data.get('validation', {}),
                confidence=json_data['confidence'],
                insights=json_data.get('insights', []),
                raw_response=response_content
            )
            
        except Exception as e:
            raise AnalysisError(f"Failed to parse TOC analysis response: {e}")
    
    def parse_multi_objective_response(self, response_content: str) -> Dict[str, Any]:
        """Parse multi-objective analysis response."""
        try:
            json_data = self._extract_json_from_response(response_content)
            
            required_fields = ['primary_focus', 'primary_analysis']
            for field in required_fields:
                if field not in json_data:
                    raise AnalysisError(f"Missing required field '{field}' in multi-objective response")
            
            # Return raw structured data for multi-objective analysis
            # Can be processed further based on primary focus type
            json_data['raw_response'] = response_content
            return json_data
            
        except Exception as e:
            raise AnalysisError(f"Failed to parse multi-objective analysis response: {e}")
    
    def _extract_json_from_response(self, response_content: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response.
        
        Args:
            response_content: Raw response content
            
        Returns:
            Parsed JSON data
            
        Raises:
            AnalysisError: If JSON cannot be extracted or parsed
        """
        # First try to find JSON in code blocks
        json_match = self.json_pattern.search(response_content)
        
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Fallback: try to find JSON-like content in the response
            # Look for content between { and } that spans multiple lines
            start_idx = response_content.find('{')
            if start_idx == -1:
                raise AnalysisError("No JSON content found in LLM response")
            
            # Find the matching closing brace
            brace_count = 0
            end_idx = start_idx
            for i, char in enumerate(response_content[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            json_str = response_content[start_idx:end_idx]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try cleaning up common LLM JSON issues before failing
            cleaned_json = self._clean_llm_json(json_str)
            if cleaned_json != json_str:
                try:
                    return json.loads(cleaned_json)
                except json.JSONDecodeError:
                    pass  # Fall through to original error handling

            raise AnalysisError(f"Invalid JSON in LLM response: {e}")

    def _clean_llm_json(self, json_str: str) -> str:
        """Clean common LLM JSON issues like comments and trailing commas."""
        import re

        # Check for truncation indicators first
        truncation_indicators = [
            r'//.*?(?:omitted|truncated|brevity|abbreviated)',
            r'/\*.*?(?:omitted|truncated|brevity|abbreviated).*?\*/',
            r'\.\.\..*?(?:omitted|truncated|brevity|abbreviated)',
        ]

        for pattern in truncation_indicators:
            if re.search(pattern, json_str, re.IGNORECASE | re.DOTALL):
                raise AnalysisError(
                    "LLM response appears truncated with abbreviation comments. "
                    "This indicates incomplete analysis. The response contains "
                    "markers suggesting content was omitted for brevity."
                )

        # Remove JavaScript-style single line comments (// ...)
        # This handles cases where LLM adds comments to abbreviate long responses
        original_json = json_str
        json_str = re.sub(r'//.*?(?=\n|$)', '', json_str)

        # Remove multi-line comments (/* ... */)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

        # Remove trailing commas before } and ]
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # Clean up any extra whitespace that might have been left
        json_str = re.sub(r'\n\s*\n', '\n', json_str)

        # If we had to remove comments, this indicates a configuration or prompting issue
        if json_str != original_json:
            raise AnalysisError(
                "LLM response contained JavaScript-style comments that had to be cleaned. "
                "This indicates either: (1) prompting issues where LLM ignored instructions, "
                "or (2) token limits causing abbreviation. The response was processed but "
                "should be investigated to ensure completeness."
            )

        return json_str

    def validate_confidence_levels(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize confidence levels in response data."""
        confidence_fields = ['confidence']  # Add more fields as needed
        
        for field in confidence_fields:
            if field in data:
                conf_value = data[field]
                if isinstance(conf_value, str):
                    # Normalize confidence strings
                    conf_lower = conf_value.lower()
                    if conf_lower in ['high', 'h']:
                        data[field] = 'High'
                    elif conf_lower in ['medium', 'med', 'm']:
                        data[field] = 'Medium'
                    elif conf_lower in ['low', 'l']:
                        data[field] = 'Low'
                    else:
                        # Default to Low for unknown values
                        data[field] = 'Low'
        
        return data
    
    def extract_insights(self, response_data: Dict[str, Any]) -> List[str]:
        """Extract insights and observations from response data."""
        insights = []
        
        # Common insight fields
        if 'insights' in response_data:
            insights.extend(response_data['insights'])
        
        # Extract reasoning from patterns
        if 'header_pattern' in response_data:
            reasoning = response_data['header_pattern'].get('reasoning')
            if reasoning:
                insights.append(f"Header pattern: {reasoning}")
        
        if 'footer_pattern' in response_data:
            reasoning = response_data['footer_pattern'].get('reasoning')
            if reasoning:
                insights.append(f"Footer pattern: {reasoning}")
        
        return insights
    
    def get_parser_for_analysis_type(self, analysis_type: str):
        """Get appropriate parser method for analysis type.
        
        Args:
            analysis_type: Type of analysis
            
        Returns:
            Parser method
        """
        parsers = {
            'headers-footers': self.parse_header_footer_response,
            'sections': self.parse_section_response,
            'toc': self.parse_toc_response,
            'multi-objective': self.parse_multi_objective_response
        }
        
        if analysis_type not in parsers:
            available = ", ".join(parsers.keys())
            raise ValueError(f"Unknown analysis type '{analysis_type}'. Available: {available}")
        
        return parsers[analysis_type]