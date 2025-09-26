# Pattern Detection Architecture

## Key Architecture Summary

### **Single LLM Call Design**
- **All three phases (1A, 1B, 1C) in one comprehensive request**
- **Token efficiency**: ~20K savings vs separate calls
- **Context preservation**: Full cross-referential analysis
- **Technical benefits**: Reduced latency, lower failure rate, simplified parsing

### **Complete System Architecture**
1. **Phase 1**: Comprehensive pattern validation (single LLM call) - **DETAILED DESIGN COMPLETE**
2. **Phase 2**: Iterative content analysis with pattern context
3. **Phase 3**: Completion assessment with multi-dimensional metrics

### **Core Components**
- **ComprehensivePatternValidator**: Handles single LLM call for all pattern phases
- **PatternSetManager**: Configurable regex patterns
- **DocumentScanner**: Full-document pattern matching
- **KnowledgeTracker**: Progressive knowledge building

### **Data Flow Architecture**
- **Programmatic preprocessing**: Extract all pattern matches first
- **Single LLM validation**: Comprehensive analysis of all patterns
- **Iterative refinement**: Use validated patterns to enhance content analysis
- **Completion assessment**: Multi-dimensional confidence scoring

### **Implementation Status**
- **Phase 1 (Pattern Discovery & Validation)**: Detailed design complete with comprehensive LLM call structure
- **Phase 2 (Iterative Content Analysis)**: High-level design outlined, detailed implementation needed
- **Phase 3 (Completion Assessment)**: Conceptual framework defined, detailed metrics and thresholds needed

### **Next Steps**
1. Review and refine Phase 2 iterative content analysis workflow
2. Define detailed completion assessment metrics and scoring algorithms for Phase 3
3. Specify component interfaces and integration points between phases
4. Design configuration management and pattern customization system

## Overview

This document outlines the architecture for intelligent document structure analysis using hybrid programmatic pattern detection and LLM validation. The system combines regex-based pattern matching with LLM intelligence to systematically discover and validate document numbering schemes, navigation structures, and content organization.

## System Goals

- **Systematic Pattern Discovery**: Use configurable regex patterns to find potential document structure elements
- **Intelligent Validation**: Leverage LLM analysis to distinguish valid patterns from false positives
- **Iterative Refinement**: Build knowledge incrementally through multiple analysis cycles
- **Cost Optimization**: Minimize expensive LLM calls through strategic programmatic preprocessing
- **Configurable Patterns**: Support document-specific numbering schemes and formats

## Overall System Architecture

### **High-Level Data Flow**

```
Document Input
    ↓
[Phase 1: Pattern Discovery & Validation - SINGLE LLM CALL]
    ↓
Programmatic Analysis → Comprehensive LLM Analysis → Unified Knowledge State
    ↓
[Phase 2: Iterative Content Analysis] 
    ↓
LLM Content Analysis ← Updated Context ← Pattern Re-scanning
    ↓
[Phase 3: Completion Assessment]
    ↓
Knowledge Validation → Confidence Scoring → Analysis Complete
```

### **Core Components**

#### **1. Programmatic Analysis Engine**
- **PatternSetManager**: Configurable regex patterns for all content types
- **DocumentScanner**: Full-document pattern matching and extraction
- **KnowledgeTracker**: Tracks discovered patterns, confidence, gaps
- **ProjectionEngine**: Generates expectations based on current knowledge

#### **2. LLM Integration Layer** 
- **ComprehensivePatternValidator**: Single LLM call for all pattern validation phases
- **ContentAnalyzer**: LLM analysis of document content with pattern context
- **CompletionAssessor**: LLM-driven analysis completeness evaluation

#### **3. Knowledge Management**
- **DocumentKnowledgeBase**: Persistent storage of discovered patterns
- **CompletionAssessment**: Multi-dimensional analysis completeness scoring
- **ValidationPriorities**: Dynamic prioritization of uncertain areas

## Phase 1: Pattern Discovery & Validation (SINGLE LLM CALL)

### **Comprehensive Pattern Analysis Architecture**

**Key Design Decision**: All pattern validation phases (1A, 1B, 1C) are executed in a **single comprehensive LLM request** for optimal token efficiency, context preservation, and cross-referential analysis.

### **Phase 1 Process Flow**

Phase 1 consists of three distinct stages that work together to produce validated pattern intelligence:

#### **Stage 1: Programmatic Preprocessing**
- **PatternSetManager**: Load and configure regex patterns for different document types
- **DocumentScanner**: Execute full-document regex scanning for all pattern types
- **DataPreparation**: Format regex matches with font/context metadata for LLM analysis

#### **Stage 2: LLM Analysis (Single Comprehensive Call)**
- **ComprehensivePatternValidator**: Send all preprocessed regex matches to LLM
- **Sub-phase 1A**: Section pattern validation and false positive filtering
- **Sub-phase 1B**: TOC/navigation pattern validation and structure extraction
- **Sub-phase 1C**: Cross-validation, conflict resolution, and unified synthesis

#### **Stage 3: Post-LLM Processing**
- **KnowledgeTracker**: Store validated patterns and analysis priorities
- **ContextPreparation**: Format results for Phase 2 iterative content analysis

### **⚠️ Design Gap: Confidence Calculation**

**IMPORTANT**: While confidence scores appear throughout Phase 1 outputs (e.g., `"confidence": "high"`, numerical scores like `0.95`), **the confidence calculation methodology is not yet defined**.

**Missing Specifications**:
- How confidence scores are calculated (programmatic metrics vs LLM assessment)
- Integration with existing `ConfidenceLevel` enum (HIGH/MEDIUM/LOW)
- Confidence adjustment algorithms for cross-validation
- Threshold definitions for confidence levels

This must be specified before Phase 1 implementation begins.

### **Programmatic Pattern Consistency Framework**

#### **Font Consistency Analysis**

Font consistency will be measured across multiple parameter combinations for each text type (section headers level 1/2/3, document headers, footers). Each text element has three independent font dimensions:

- **Font Family**: TimesNewRoman, Arial, Helvetica, etc.
- **Font Size**: 10pt, 12pt, 14pt, etc. (assuming rounding completed in preprocessing)
- **Font Style**: Regular, Bold, Italic, Bold+Italic

**Parameter Combination Analysis**: Seven consistency calculations will be performed for each text type:

**Single Parameters (3)**:
- Font Family only
- Font Size only
- Font Style only

**Two-Parameter Combinations (3)**:
- Font Family + Font Size
- Font Family + Font Style
- Font Size + Font Style

**Three-Parameter Combination (1)**:
- Font Family + Font Size + Font Style (complete font signature)

**Consistency Calculation Method**: Distribution-based consistency measuring the proportion of instances that match the most common value within each parameter combination. For example, if 99 instances use "TimesNewRoman" and 1 uses "Arial", the font family consistency is 99/100 = 0.99.

**Text Type Considerations**: Different text types have different consistency expectations:
- **Section Headers**: Expected to be highly consistent within each hierarchical level
- **Document Headers/Footers**: May have legitimate variations (page numbers, chapter titles, dates)

**⚠️ Decision Integration TBD**: How these consistency scores will be weighted, combined, and used to influence overall confidence calculations remains to be determined.

#### **Section Completeness Analysis**

**Missing Section Detection**: Programmatically identify missing sections through hierarchical and sequence implications. Child sections imply parent existence (e.g., `1.2.3` implies `1.2` and `1` must exist). Found sections imply complete sequences up to the highest number at each level (e.g., finding `2.5` implies `2.1, 2.2, 2.3, 2.4` should exist).

**TOC Cross-Reference Completeness**: Compare found sections against all discovered Table of Contents entries across all TOC pages. Calculate what percentage of TOC-promised sections are actually found in the document.

**Combined Implication Analysis**: Merge expectations from both section sequence analysis and TOC discovery to create comprehensive expected section set. All TOC entries generate their own hierarchical implications (e.g., TOC entry `4.1.1` implies complete sequence `1, 2, 3, 4, 4.1` should exist).

**Completeness Metrics**:
- **Section Sequence Completeness**: `found_sections / (found_sections + section_implied_missing)`
- **TOC Completeness**: `found_toc_sections / total_toc_sections_across_all_pages`
- **Comprehensive Completeness**: `found_sections / total_expected_from_all_implications`

**⚠️ Decision Integration TBD**: How completeness scores will be weighted and used in confidence calculations remains to be determined.

#### **Combined Input Data Structure**

```python
comprehensive_pattern_input = {
    "section_pattern_matches": {
        "decimal_pattern": {
            "regex": r"(\d+(?:\.\d+)*)",
            "matches": [
                {"page": 1, "line": 5, "text": "1.1 Introduction", "match": "1.1", 
                 "font": "TimesNewRomanPS-BoldMT", "size": "12.0pt"},
                {"page": 2, "line": 8, "text": "version 2.1 of the", "match": "2.1", 
                 "font": "TimesNewRomanPSMT", "size": "10.0pt"}
            ]
        },
        "chapter_pattern": {
            "regex": r"(Chapter\s+\d+)",
            "matches": [...]
        }
    },
    "toc_pattern_matches": {
        "toc_title_patterns": {
            "table_of_contents": {"matches": [...]},
            "contents": {"matches": [...]}
        },
        "toc_entry_patterns": {
            "dotted_leader": {"matches": [...]},
            "simple_spacing": {"matches": [...]}
        },
        "list_of_figures_patterns": {...},
        "list_of_tables_patterns": {...}
    },
    "document_context": {
        "total_pages": 10,
        "body_text_font": "TimesNewRomanPSMT",
        "body_text_size": "10.0pt"
    }
}
```

#### **Single LLM Request Structure**

```python
comprehensive_analysis_prompt = {
    "task": "Comprehensive document pattern analysis in three sequential phases within single response",
    "phases": {
        "phase_1a": {
            "name": "Section Numbering Pattern Analysis",
            "input": "section_pattern_matches",
            "tasks": [
                "Identify valid section heading patterns vs false positives",
                "Determine hierarchical heading levels from numbering depth", 
                "Filter non-heading matches based on font/context",
                "Generate section numbering hypothesis with confidence"
            ]
        },
        "phase_1b": {
            "name": "TOC/Navigation Pattern Analysis", 
            "input": "toc_pattern_matches",
            "tasks": [
                "Identify actual TOC/LOF/LOT sections vs false matches",
                "Extract document structure expectations from navigation",
                "Determine entry formats and numbering schemes",
                "Generate navigation structure hypothesis"
            ]
        },
        "phase_1c": {
            "name": "Unified Hypothesis Synthesis",
            "input": "phase_1a_results + phase_1b_results + all_raw_data",
            "tasks": [
                "Cross-validate section patterns against TOC structure",
                "Resolve conflicts between section and navigation analyses",
                "Adjust confidence scores based on cross-validation",
                "Create unified document structure hypothesis",
                "Prioritize validation tasks for content analysis"
            ]
        }
    }
}
```

#### **Single Response Output Structure**

```python
comprehensive_pattern_result = {
    "phase_1a_section_analysis": {
        "primary_pattern": {
            "name": "decimal_pattern",
            "confidence": "high",
            "heading_levels": [1, 2, 3],
            "false_positives": [...],
            "missing_sections": [...]
        },
        "rejected_patterns": [...],
        "evidence_summary": "..."
    },
    "phase_1b_toc_analysis": {
        "navigation_sections": [
            {"type": "table_of_contents", "location": "page_2", "confidence": "high"},
            {"type": "list_of_figures", "location": "page_4", "confidence": "high"}
        ],
        "implied_structure": {
            "sections": {"expected_sections": [...], "numbering_scheme": "decimal"},
            "figures": {"expected_figures": [...], "gaps": [...]},
            "tables": {"expected_tables": [...]}
        }
    },
    "phase_1c_unified_synthesis": {
        "document_structure": {
            "primary_numbering": {...},
            "secondary_numbering": [...]
        },
        "cross_validation_results": {
            "alignments": [...],
            "conflicts": [...],
            "confidence_adjustments": [...]
        },
        "expected_document_elements": {
            "sections": [...],
            "figures": [...], 
            "tables": [...]
        },
        "validation_priorities": [
            {"priority": "high", "task": "verify_missing_section_2.2", "reason": "implied by 2.2.1 but not in TOC"},
            {"priority": "medium", "task": "confirm_level_3_headings", "reason": "section analysis found evidence, TOC doesn't show them"}
        ]
    },
    "overall_confidence": {
        "section_numbering": 0.95,
        "navigation_structure": 0.85,
        "cross_validation": 0.90
    }
}
```

### **Sequential Single-Call Analysis Approach**

**Core Design**: Each page group receives **one comprehensive LLM call** performing all analysis tasks (pattern validation, section identification, TOC analysis, cross-validation) to maintain token efficiency and context preservation benefits.

**Sequential Processing**: Due to context window limitations, analysis proceeds through sequential page groups with knowledge accumulation:

#### **Single Call Per Group Benefits**
- **Token Efficiency**: One comprehensive call vs multiple separate calls on same pages
- **Context Preservation**: Full cross-referential analysis within each page group
- **Unified Analysis**: All pattern validation tasks performed together with shared context

#### **Sequential Group Process**
- **Group 1** (4 consecutive pages): Comprehensive analysis → initial patterns and knowledge
- **Group 2** (4 consecutive pages): Comprehensive analysis + Group 1 knowledge → refined understanding
- **Group 3** (4 consecutive pages): Comprehensive analysis + accumulated knowledge → final patterns
- **Individual Pages**: Comprehensive validation call using established pattern knowledge

#### **Knowledge Accumulation Between Groups**
- **Confirmed Sections**: High-confidence section identifications carry forward
- **Pattern Performance**: Regex pattern effectiveness tracked across groups
- **Working Hypotheses**: Document structure possibilities with evolving confidence
- **LLM Decision Authority**: LLM acts as final arbiter of section identification and confidence scoring

#### **Comprehensive Analysis Per Call**
Each single LLM call performs:
- **Direct Section Identification**: Analyze page content for genuine section headings
- **Regex Pattern Cross-Reference**: Evaluate all regex matches against identified sections
- **TOC Structure Recognition**: Identify and validate table of contents patterns
- **Knowledge Integration**: Synthesize findings with previous group knowledge
- **Hypothesis Management**: Update confidence in competing document structure theories

## Phase 2: Iterative Content Analysis

### **Enhanced LLM Context from Phase 1**

Phase 1's comprehensive analysis provides rich context for content analysis:

```python
llm_content_context = {
    "validated_patterns": {
        "primary_section_pattern": "decimal (1.1, 1.2, 2.1)",
        "confirmed_heading_levels": [1, 2, 3],
        "navigation_structure": "TOC on page 2, LOF on page 4"
    },
    "expected_elements": [
        {"type": "section", "number": "2.2", "status": "missing_implied_by_2.2.1"},
        {"type": "figure", "number": "Figure 1.2", "status": "gap_in_sequence"}
    ],
    "validation_requests": [
        "Flag any section numbering not matching decimal pattern",
        "Report figure numbers higher than Figure 2.5",
        "Look specifically for missing section 2.2"
    ],
    "confidence_levels": {
        "section_detection": 0.95,
        "figure_detection": 0.75,
        "table_detection": 0.80
    }
}
```

### **Iterative Knowledge Updates**

```
For Each LLM Content Batch:
    ↓
Execute LLM Analysis with Phase 1 Context
    ↓
Extract New Findings → Compare Against Phase 1 Expectations
    ↓
Update Knowledge State → Run Full Document Regex Re-scan
    ↓
Generate Updated Projections → Prepare Next Batch Context
```

## Phase 3: Completion Assessment

### **Multi-Dimensional Completion Metrics**

Building on Phase 1's comprehensive foundation:

```python
completion_assessment = {
    "pattern_validation_complete": {
        "section_numbering": True,   # Phase 1 validated decimal pattern
        "navigation_structure": True, # Phase 1 confirmed TOC/LOF structure
        "cross_validation": True     # Phase 1 resolved conflicts
    },
    "content_analysis_progress": {
        "expected_sections_found": 0.85,  # 85% of Phase 1 expectations confirmed
        "validation_priorities_addressed": 0.70,  # 70% of high-priority validations complete
        "knowledge_gaps_resolved": 0.60   # 60% of identified gaps filled
    },
    "overall_completeness": 0.78
}
```

## Component Interfaces

### **ComprehensivePatternValidator** (Core Component)

```python
class ComprehensivePatternValidator:
    """Single LLM call handler for all pattern validation phases"""
    
    def analyze_all_patterns(
        self, 
        section_patterns: Dict, 
        toc_patterns: Dict, 
        context: Dict
    ) -> ComprehensivePatternResult:
        """
        Execute Phases 1A, 1B, and 1C in single LLM request
        
        Returns:
            ComprehensivePatternResult with all three phases
        """
        
    def _build_comprehensive_prompt(self, section_patterns: Dict, toc_patterns: Dict) -> str:
        """Build single structured prompt for all phases"""
        
    def _parse_comprehensive_response(self, response: str) -> ComprehensivePatternResult:
        """Parse single response containing all three phases"""
```

### **PatternSetManager**

```python
class PatternSetManager:
    def __init__(self, config_path: Optional[str] = None):
        """Load configurable pattern definitions"""
        
    def get_all_patterns(self) -> Dict[str, Dict]:
        """Get all patterns for comprehensive analysis"""
        
    def add_custom_pattern(self, pattern_type: str, name: str, regex: str):
        """Add document-specific pattern"""
```

### **DocumentScanner**

```python
class DocumentScanner:
    def scan_full_document(self, document_data: Dict, patterns: Dict) -> Dict:
        """Run all patterns on entire document for Phase 1 input"""
        
    def rescan_with_new_patterns(self, additional_patterns: List) -> Dict:
        """Re-scan document when Phase 1 suggests new patterns"""
```

## Configuration Management

### **Pattern Configuration**

```yaml
# config/patterns.yaml
comprehensive_analysis:
  single_llm_call: true
  phases_included: ["1a_section", "1b_toc", "1c_synthesis"]
  
section_patterns:
  decimal:
    regex: '(\d+(?:\.\d+)*)'
    description: 'Standard decimal numbering (1.1, 1.1.1)'
  chapter:
    regex: '(Chapter\s+\d+)'
    description: 'Chapter-style headings'
    
toc_patterns:
  dotted_leader:
    regex: '(\d+(?:\.\d+)*)\s+(.+?)\s+\.{3,}\s+(\d+)'
    description: 'TOC entries with dotted leaders'
    
completion_thresholds:
  headers_footers: 0.95
  section_headings: 0.90
  table_figures: 0.85
```

## Benefits of Single LLM Call Architecture

### **Technical Advantages**
- **Token Efficiency**: ~20K token savings vs three separate calls
- **Context Preservation**: Complete cross-referential analysis capability
- **Reduced Latency**: Single network round-trip vs three sequential calls
- **Lower Failure Rate**: Single point of failure vs multiple API calls

### **Analysis Quality Benefits**
- **Comprehensive Cross-Validation**: Section patterns immediately validated against TOC
- **Holistic Confidence Assessment**: Unified confidence scoring across all pattern types  
- **Real-Time Conflict Resolution**: Immediate reconciliation of discrepancies
- **Unified Knowledge Base**: Single authoritative source of pattern validation results

### **Implementation Benefits**
- **Simplified Architecture**: One response parser vs coordinating three
- **Atomic Operations**: All-or-nothing pattern validation
- **Easier Testing**: Single comprehensive response to validate
- **Cleaner Error Handling**: Simplified failure scenarios and recovery logic

This architecture provides a robust foundation for intelligent document structure analysis while optimizing for cost, performance, and analysis quality through the strategic use of a single comprehensive LLM call for all pattern validation phases.