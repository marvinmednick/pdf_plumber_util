# PDF Plumb Architecture

## Project Overview

PDF Plumb is a sophisticated PDF text extraction and analysis tool designed specifically for technical specifications and structured documents. The project addresses the limitations of basic PDF text extraction by implementing intelligent text grouping, spacing analysis, and document structure identification.

## Problem Statement

### Technical Challenges
1. **PDF Text Extraction Limitations**: Basic PDF text extraction often produces poor results for technical documents with complex layouts, tables, headers/footers, and varied font sizes.

2. **Block Identification**: Technical specifications require grouping text into logical blocks (paragraphs, sections, headers) based on visual spacing and typography rather than just line breaks.

3. **Header/Footer Detection**: Consistent identification of headers and footers across pages for accurate content extraction.

4. **Content vs. Structure Distinction**: Programmatic analysis struggles to distinguish document structure elements (headers/footers) from content elements (section headings) based on position alone.

5. **Pattern Recognition Complexity**: Cross-document patterns (TOC validation, section hierarchy, content relationships) require content understanding beyond spacing analysis.

6. **Licensing Constraints**: Moving away from PyMuPDF for core extraction due to licensing costs, while retaining it for development visualization tasks.

## Architecture Principles

### Core Design Decisions
- **Multi-Method Extraction**: Use multiple PDF extraction strategies and compare results
- **Contextual Analysis**: Analyze spacing and fonts in context rather than absolute values
- **Hybrid Intelligence**: Combine programmatic precision with LLM content understanding
- **Multi-Stream Validation**: Cross-validate findings between position, content, and pattern analysis
- **Modular Pipeline**: Separate extraction, analysis, and visualization into distinct phases
- **Data Preservation**: Maintain rich metadata throughout the pipeline for debugging and analysis
- **LLM Context Optimization**: Design processing to consider token sizes and context windows, optimizing as needed for efficient LLM integration

### Technology Stack
- **Python 3.12+** with modern package management via `uv`
- **pdfplumber** as primary extraction engine (license-friendly)
- **PyMuPDF** for visualization only (development use)
- **pdfminer-six** for low-level PDF operations
- **Click + Rich** for modern CLI interface with progress bars and styling
- **Pydantic** for configuration management and data validation
- **LLM Integration**: Azure OpenAI (GPT-4.1), multi-model support framework  
- **tiktoken** for accurate token counting and batch optimization
- **orjson** for high-performance JSON serialization
- **openai** for Azure OpenAI API integration
- **python-dotenv** for environment variable management

## System Architecture

### High-Level Data Flow

```
PDF Input
    ↓
[Extraction Process]
    ↓ produces
Line Data + Word Data + Page Metadata
    ↓
[Programmatic Analysis Process]
    ↓ produces
Block Data + Contextual Spacing Rules + Boundary Candidates
    ↓
[LLM Analysis Process - Continuous Multi-Objective]
    ↓ produces
Priority-Focused Results + Font Style Database + Structural Element Catalog + Cross-Reference Mapping + Confidence Metrics + Anomaly Detection + Pattern Validation
    ↓
[Adaptive Decision Framework Process]
    ↓ produces
Confidence-Driven Focus Shifts + Dynamic Sampling Decisions + Pattern Evolution + Cross-Validation Results
    ↓
[Final Structure Assembly]
    ↓ produces
Document Structure + Analysis Reports
```

**Hybrid Intelligence**: The pipeline combines programmatic precision (spacing, positioning, fonts) with content understanding (LLM-powered classification) to achieve accurate document structure identification.

**Diagnostic Visualization**: At any processing stage, visualization can be applied for debugging and troubleshooting - examining extraction results, spacing patterns, block formation, classification decisions, or boundary validation.

### Core Components

#### 1. PDF Extraction Engine (`src/pdf_plumb/core/extractor.py`)
**Purpose**: Extract text using multiple strategies and create structured line data

**Key Classes**:
- `PDFExtractor`: Main extraction coordinator

**Extraction Methods**:
1. **Raw Text**: `page.extract_text()` - baseline comparison
2. **Text Lines**: `page.extract_text_lines()` - layout-aware extraction  
3. **Word-based**: `page.extract_words()` - manual alignment with tolerance-based grouping

**Output Data Structures**:
- **Lines JSON**: Enriched line objects with:
  - Text segments (font, size, direction changes)
  - Bounding boxes (precise positioning)
  - Predominant font/size analysis
  - Gap calculations (before/after each line)
- **Words JSON**: Raw word-level data for debugging
- **Comparison JSON**: Side-by-side method comparison

#### 2. Document Analysis Engine (`src/pdf_plumb/core/analyzer.py`)

**Purpose**: Hybrid intelligence system combining programmatic precision with adaptive content understanding

**Key Classes**:
- `DocumentAnalyzer`: High-level document analysis coordinator
- `PDFAnalyzer`: Detailed spacing and structure analysis

**Programmatic Analysis Foundation**

##### Contextual Spacing Analysis
- Groups lines by predominant font size (context)
- Analyzes spacing patterns within each font size context
- Classifies gaps as: Tight, Line, Paragraph, Section, Wide
- Accounts for font size differences in spacing expectations

##### Block Formation Algorithm
```python
# Combines lines into logical blocks based on:
# 1. Same predominant font size
# 2. Gap ≤ contextual line spacing threshold
# 3. Consecutive positioning
```

##### Header/Footer Detection
- **Traditional Method**: Y-coordinate analysis within defined zones (1.25" header, 1.0" footer)
- **Contextual Method**: Gap analysis using contextual spacing rules
- **Cross-page Aggregation**: Identifies consistent boundaries across document

**LLM Analysis Integration (State Machine Orchestrator)**

The system uses a state machine architecture to orchestrate complex, multi-objective analysis workflows. States execute discrete analysis tasks and determine workflow progression based on results and context.

*State machine architecture: [design/STATE_MACHINE_ARCHITECTURE.md](design/STATE_MACHINE_ARCHITECTURE.md)*
*Current LLM implementation: [design/LLM_INTEGRATION.md](design/LLM_INTEGRATION.md)*

##### State-Based Analysis Framework
- **Execute Functions**: Each state performs discrete analysis tasks (programmatic logic, LLM calls, or hybrid)
- **Transition Logic**: States determine next steps based on execution results and accumulated context
- **Context Accumulation**: Growing knowledge base passed between states
- **Workflow Orchestration**: Manages progression through different analysis objectives
- **Validation & Quality**: Built-in state transition validation and error handling

##### Current Analysis Capabilities
- **Headers/Footers Detection**: Content-aware boundary detection with confidence scoring
- **Section Hierarchy**: Identification of section patterns and numbering systems  
- **Document Element Classification**: Separation of Figure/Table titles from section headings
- **Multi-Objective Processing**: Simultaneous pattern detection with priority focus

**Analysis Outputs**:
- Font usage statistics and predominant fonts/sizes
- Spacing distribution by context
- Content-classified boundaries with confidence scores
- Block-level document structure with content types
- Cross-validated structural patterns
- Anomaly reports and pattern refinements
- Growing knowledge base for document-specific patterns

#### 3. Visualization Engine (`src/pdf_plumb/core/visualizer.py`)

**Purpose**: Create visual overlays showing spacing patterns and analysis results

**Key Classes**:
- `SpacingVisualizer`: PDF visualization with spacing overlays

**Visualization Features**:
- **Line Spacing Visualization**: Color-coded lines showing gaps between text lines
- **Block Spacing Visualization**: Shows gaps between logical blocks
- **Legend Generation**: Automatic legend pages explaining colors and patterns
- **Customizable Styling**: User-defined colors, patterns, and spacing ranges

**Technical Implementation**:
- Uses PyMuPDF for PDF manipulation (development only)
- Supports complex line patterns (solid, dashed, dotted, dash-dot)
- Handles multiple spacing ranges with frequency-based color assignment

#### 4. Support Infrastructure

##### File Handler (`src/pdf_plumb/utils/file_handler.py`)
- Centralized file I/O operations
- Consistent naming conventions
- JSON serialization with proper encoding

##### Constants & Configuration (`src/pdf_plumb/utils/constants.py`)
- Page dimensions and zone definitions
- Spacing thresholds and multipliers
- Rounding precision settings

##### Utilities (`src/pdf_plumb/utils/helpers.py`)
- Text normalization functions
- Path handling utilities
- Mathematical rounding operations

#### 5. LLM Analysis Engine (`src/pdf_plumb/core/llm_analyzer.py`)

**Purpose**: LLM-enhanced document analysis with Azure OpenAI integration

**Key Classes**:
- `LLMDocumentAnalyzer`: Main coordinator for LLM-enhanced analysis
- `AzureOpenAIProvider`: Azure OpenAI API integration
- `PageSampler`: Strategic page sampling for analysis
- `ResponseParser`: LLM response parsing and validation

**Analysis Capabilities**:
- **Headers/Footers Detection**: Content-aware boundary detection with confidence scoring
- **Section Hierarchy**: Identification of section patterns and numbering systems
- **Table of Contents**: TOC extraction and cross-validation
- **Multi-Objective Analysis**: Simultaneous pattern detection with priority focus

**LLM Module Structure** (`src/pdf_plumb/llm/`):
- `providers.py`: Azure OpenAI and multi-provider support
- `sampling.py`: Strategic page sampling strategies  
- `prompts.py`: Analysis prompt templates
- `responses.py`: Response parsing and result structures

### CLI Interface (`src/pdf_plumb/cli.py`)

**Command Structure**:
1. **extract**: PDF → structured data files
2. **analyze**: structured data → analysis reports  
3. **llm-analyze**: LLM-enhanced document structure analysis
4. **process**: end-to-end pipeline with visualization

**Key Parameters**:
- Tolerance settings (x/y alignment)
- Output directory management
- Visualization options (colors, patterns, spacing ranges)
- Debug levels and logging

## Data Models

### Line Object Structure
```json
{
  "line_number": 1,
  "text": "Combined line text",
  "bbox": {"x0": 72, "top": 100, "x1": 400, "bottom": 112},
  "text_segments": [
    {
      "font": "Arial-Bold",
      "reported_size": 12.0,
      "rounded_size": 12.0,
      "direction": "upright",
      "text": "Bold text",
      "bbox": {"x0": 72, "top": 100, "x1": 150, "bottom": 112}
    }
  ],
  "predominant_size": 12.0,
  "predominant_font": "Arial-Bold",
  "predominant_size_coverage": 85.5,
  "predominant_font_coverage": 85.5,
  "gap_before": 14.5,
  "gap_after": 14.5
}
```

### Block Object Structure  
```json
{
  "lines": [/* array of line objects */],
  "text": "Combined block text",
  "predominant_size": 12.0,
  "gap_before": 18.0,
  "gap_after": 18.0,
  "size_coverage": 92.3,
  "predominant_font": "Arial",
  "font_coverage": 89.7,
  "bbox": {"x0": 72, "x1": 400, "top": 100, "bottom": 140}
}
```

## Algorithmic Details

### Contextual Spacing Classification

The core innovation is analyzing spacing relative to font size context:

```python
def _classify_gap_contextual(gap, context_size, spacing_rules):
    rules = spacing_rules[context_size]
    if gap <= rules['line_spacing_range'][1]:
        return 'Line'  # Within paragraph
    elif gap <= rules['para_spacing_max']:
        return 'Paragraph'  # Between paragraphs
    else:
        return 'Section'  # Between sections
```

This accounts for the fact that 14pt text naturally has larger line spacing than 10pt text.

### Header/Footer Boundary Detection

Two-phase approach:
1. **Zone Analysis**: Look for text within predefined header/footer zones
2. **Gap Analysis**: Identify large spacing breaks that suggest boundaries
3. **Cross-Page Validation**: Aggregate candidates across pages for consistency

### Tolerance-Based Word Grouping

Words are grouped into lines based on configurable tolerances:
- **Y-tolerance**: Vertical alignment threshold (default 3.0pt)
- **X-tolerance**: Horizontal spacing threshold (default 3.0pt)

This handles slight positioning variations in PDF text extraction.

## Performance & Scalability

### Design for Large Documents
- Streaming JSON processing for large files
- Page-by-page analysis to manage memory
- Configurable precision settings to balance accuracy vs performance

### Optimization Strategies
- Text segment caching during analysis
- Efficient gap calculation algorithms
- Minimal data copying between pipeline stages

## Quality & Reliability

### Multi-Method Validation
- Compare three extraction methods to identify potential issues
- Generate comparison reports highlighting discrepancies
- Maintain raw data for debugging extraction problems

### Robust Error Handling
- Graceful degradation for malformed PDF data
- Comprehensive logging at multiple levels
- Input validation and sanitization

### Consistent Output
- Standardized file naming conventions
- Configurable rounding precision (0.5pt default)
- Rich metadata in all output files

## Future Architecture Considerations

### Licensing Strategy
- Core extraction uses only license-friendly libraries (pdfplumber, pdfminer-six)
- PyMuPDF isolated to visualization module for easy removal/replacement
- Modular design allows visualization backend swapping

### Extensibility Points
- Plugin architecture for new analysis algorithms
- Configurable spacing classification rules
- Customizable output formats and visualizations

### Integration Capabilities
- JSON-based data exchange for external tool integration
- CLI interface suitable for automation and scripting
- Rich metadata preservation for downstream processing