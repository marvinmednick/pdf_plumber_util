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
    
    def get_content_boundaries(self) -> Dict[str, float]:
        """Get validated content area boundaries."""
        boundaries = self.content_area_boundaries
        return {
            'start_after_y': float(boundaries.get('main_content_starts_after_y', 0)),
            'end_before_y': float(boundaries.get('main_content_ends_before_y', 792)),
            'confidence': boundaries.get('confidence', 'Low')
        }
    
    def get_pages_with_headers(self) -> List[int]:
        """Get list of page indexes that have headers."""
        return self.header_pattern.get('pages_with_headers', [])
    
    def get_pages_with_footers(self) -> List[int]:
        """Get list of page indexes that have footers.""" 
        return self.footer_pattern.get('pages_with_footers', [])


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
            raise AnalysisError(f"Invalid JSON in LLM response: {e}")
    
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