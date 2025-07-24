# Design Decisions

This document captures key architectural choices made during PDF Plumb development, including the rationale behind each decision and alternatives that were considered. This serves as context for future development and helps maintain consistency across the system.

## Core Architecture Decisions

### 1. Word-Based Extraction as Primary Method

**Decision**: Use word-based extraction with manual alignment as the primary method for document structure analysis.

**Rationale**:
- Provides detailed positioning, font metadata, and text segments needed for contextual spacing analysis
- Enables precise gap calculations between lines for block formation algorithms
- Preserves document structure through bounding boxes and font change detection
- Word-level granularity supports intelligent line grouping with tolerance-based alignment

**Development Process**:
- Multiple extraction methods were implemented for comparison during development
- Raw text and line-based extraction served as validation/comparison methods
- Testing confirmed word-based method provides the necessary detail for intelligent analysis

**Current Status**: 
- Word-based method is the only method that feeds into block creation pipeline
- Other extraction methods run for internal validation/debugging but don't affect user output
- Users interact only with structured output: `_lines.json` → `_blocks.json`

**Implementation**: `PDFExtractor._process_words()` in `core/extractor.py`

### 2. Contextual vs Absolute Spacing Analysis

**Decision**: Use font size-aware contextual spacing analysis instead of absolute pixel/point thresholds.

**Rationale**:
- 14pt text naturally has larger line spacing than 10pt text
- Absolute thresholds fail when documents mix font sizes
- Statistical analysis of document patterns provides better boundaries
- Adapts to different document formatting styles

**Alternatives Considered**:
- Fixed pixel thresholds → Rejected: Poor accuracy across document types
- Machine learning classification → Deferred: Requires training data, adds complexity
- User-defined thresholds → Rejected: Too much manual configuration required

**Implementation**: `_analyze_contextual_spacing()` in `core/analyzer.py`

### 3. Contextual Header/Footer Detection (Iterative Development)

**Decision**: Replace traditional zone-based header/footer detection with contextual spacing-based detection.

**Development Process**:
1. **Phase 1**: Implemented traditional zone-based method (Y-coordinate thresholds)
   - Achieved baseline accuracy on standard documents
   - Identified limitations with non-standard layouts and fixed zone assumptions
2. **Phase 2**: Developed contextual spacing-based method
   - Uses same contextual spacing analysis as block formation
   - Adapts to document-specific patterns rather than fixed zones
3. **Phase 3**: Comparison validation
   - Both methods implemented for side-by-side comparison
   - Testing confirmed contextual method achieves equal or better accuracy
   - Traditional method retained temporarily for validation

**Current Status**: 
- Contextual method validated as preferred approach
- Traditional method will be disabled once comparison phase complete
- Both methods currently implemented but contextual is the production choice

**Rationale for Contextual Approach**:
- Handles variable layouts and non-standard positioning
- Consistent with overall contextual spacing philosophy
- Better accuracy on complex document structures

**Implementation**: `_identify_header_footer_contextual()` in `core/analyzer.py`

### 4. LLM Integration Architecture

**Decision**: Hybrid approach combining programmatic precision with LLM content understanding via strategic sampling.

**Rationale**:
- Programmatic methods excel at positioning and spacing analysis
- LLM provides content-aware classification (distinguishing headers from section titles)
- Strategic sampling (3 groups + 4 individuals) balances cost with pattern recognition
- Multi-objective continuous analysis gathers multiple insights simultaneously

**Alternatives Considered**:
- Full document LLM analysis → Rejected: Cost prohibitive, token limits
- Replace programmatic analysis → Rejected: Loses precision advantages
- Sequential analysis phases → Rejected: Less efficient than multi-objective approach

**Implementation**: `LLMDocumentAnalyzer` in `core/llm_analyzer.py`, supporting modules in `llm/`

### 5. Configuration Management Strategy

**Decision**: Pydantic BaseSettings with environment variable support and document type profiles.

**Priority Hierarchy**:
1. **CLI arguments** (highest priority)
2. **Profile settings** (via `--profile` flag)
3. **Environment variables** (with `PDF_PLUMB_` prefix)
4. **Default values** (lowest priority)

**Rationale**:
- Pydantic provides type safety and validation
- Environment variables enable deployment flexibility
- Profiles provide quick document-specific optimization
- CLI arguments allow per-command overrides

**Implementation**: `PDFPlumbConfig` class in `config.py`

### 6. CLI Framework Migration

**Decision**: Migrate from argparse to Click + Rich for modern CLI experience.

**Rationale**:
- Click provides better help system and command organization
- Rich enables progress bars, colored output, and professional appearance
- Better error handling and user experience
- Easier to extend with new commands

**Migration Process**: Phase 2.1 - Complete rewrite with verified compatibility using real PDF testing

**Implementation**: `cli.py` with Click decorators and Rich console integration

### 7. Structured Error Handling

**Decision**: Implement structured exception hierarchy with Rich console formatting and recovery suggestions.

**Features**:
- 15+ specialized exception classes
- Color-coded error display with emojis
- Automatic retry mechanisms for transient failures
- Contextual debugging information

**Implementation**: Exception classes in `core/exceptions.py`, CLI integration in `cli.py`

### 8. Performance Optimization Strategy

**Decision**: Selective optimization focusing on JSON serialization, with pdfplumber retained for functionality.

**Rationale**:
- JSON serialization was identified bottleneck (eliminated via orjson)
- pdfplumber provides reliable PDF processing despite performance cost
- Current performance (12.46s for 20 pages) meets requirements
- Further optimization deferred until requirements change

**Results**:
- 10% total pipeline improvement
- 56% function call reduction
- Sub-linear scaling validated

### 9. Dependency Management Strategy

**Decision**: Use license-friendly libraries for core functionality, isolate PyMuPDF to visualization only.

**Core Dependencies**:
- **pdfplumber**: Primary extraction engine
- **pdfminer-six**: Low-level PDF operations
- **PyMuPDF**: Visualization only (development use)

## Data Structure Decisions

### 1. Line-Centric Data Model

**Decision**: Structure extracted data around enriched line objects with text segments.

**Data Structure**:
```json
{
  "line_number": 1,
  "text": "Combined line text",
  "text_segments": [/* font/size metadata */],
  "predominant_size": 12.0,
  "gap_before": 14.5,
  "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 112}
}
```

### 2. Block-Based Analysis Output

**Decision**: Transform line data into contextual blocks for higher-level analysis.

**Rationale**:
- Blocks represent logical document units (paragraphs, sections)
- Enables semantic analysis beyond individual lines
- Provides foundation for LLM analysis
- Maintains traceability to original lines

## Technology Stack Decisions

### 1. Python 3.12+ with Modern Tooling

**Key Libraries**:
- **uv**: Package management
- **Pydantic**: Configuration and data validation
- **Click + Rich**: Modern CLI framework
- **orjson**: High-performance JSON serialization

### 2. orjson for Performance

**Decision**: Replace standard json library with orjson for serialization.

**Results**: 3-5x performance improvement in JSON operations

**Implementation**: `utils/json_utils.py` compatibility layer

## Development Philosophy

### Iterative Validation Approach

**Pattern**: Implement multiple approaches for comparison, then standardize on the best solution.

**Examples**:
1. **Extraction Methods**: Multiple methods for comparison → Word-based as primary
2. **Header/Footer Detection**: Traditional → Contextual → Contextual as preferred
3. **Error Handling**: Basic → Structured exceptions with Rich formatting

**Benefits**:
- Validates design choices with real data
- Provides fallback options during development
- Enables objective comparison of approaches
- Reduces risk of premature optimization

## Current Decision Points

### 1. State Machine Architecture for LLM Workflows

**Decision**: Implement state machine orchestrator for multi-objective analysis workflows.

**Rationale**:
- Current iterative processing limited to single analysis focus (headers/footers)
- Need flexible workflow management for different analysis objectives (H/F → Sections → TOC → Tables)
- State-based approach enables conditional branching and adaptive decision-making
- Hybrid execution model supports both programmatic logic and LLM integration

**Design**: [design/STATE_MACHINE_ARCHITECTURE.md](design/STATE_MACHINE_ARCHITECTURE.md)

**Status**: Architecture design complete, implementation pending

## Future Decision Points

### 1. Traditional Method Removal

**Status**: Pending completion of validation phase

**Action**: Remove traditional header/footer detection once contextual method fully validated

### 2. Extraction Method Cleanup

**Status**: Consider removing comparison methods from production pipeline

**Consideration**: Keep for debugging vs simplify codebase

### 3. Advanced State Machine Features

**Status**: Deferred pending core implementation

**Considerations**: Parallel state execution, state persistence, dynamic state creation

## Decision Review Process

When making new architectural decisions:

1. **Document the decision** in this file with rationale
2. **Consider alternatives** and document why they were rejected  
3. **Update cross-references** to relevant design documents
4. **Create/update design docs** for implementation details
5. **Add entry to PHASE_HISTORY.md** for major changes

This ensures design knowledge is preserved and can inform future decisions.