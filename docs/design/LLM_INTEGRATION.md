# LLM Integration Design

This document consolidates the LLM analysis strategy and implementation approach for PDF Plumb, combining strategic planning with practical implementation details.

## Implementation Status

**Current Phase**: LLM integration implemented and operational
- Azure OpenAI integration with GPT-4.1 (1M context window)
- Strategic page sampling for header/footer analysis
- Cost estimation and token usage tracking
- CLI command: `llm-analyze` with multiple analysis focuses

## Core Strategy: Hybrid Intelligence

### Architectural Principle

**Hybrid Approach**: Combine programmatic precision with LLM content understanding via strategic sampling.

**Rationale**:
- Programmatic methods excel at positioning and spacing analysis
- LLM provides content-aware classification (distinguishing headers from section titles)
- Strategic sampling (3 groups + 4 individuals) balances cost with pattern recognition
- Multi-objective continuous analysis gathers multiple insights simultaneously

### Data Volume Management

**Strategic Sampling**: Intelligently select representative content rather than processing entire documents
- **Sample Strategy**: 3 groups of 4 consecutive pages + 4 individual pages
- **Rationale**: Balance pattern recognition with cost efficiency
- **GPT-4.1 Advantage**: 1M context window enables 20-page batches vs GPT-4's 4-page limit

**Adaptive Sample Size**: System determines sample requirements based on document consistency patterns
**Context-Aware Selection**: Choose pages/sections that represent structural diversity

## Implementation Architecture

### Core Components

**LLM Analysis Engine** (`src/pdf_plumb/core/llm_analyzer.py`):
- `LLMDocumentAnalyzer`: Main coordinator for LLM-enhanced analysis
- Integration with existing contextual block analysis
- Cost estimation and token usage tracking

**LLM Module Structure** (`src/pdf_plumb/llm/`):
- `providers.py`: Azure OpenAI and multi-provider support framework
- `sampling.py`: Strategic page sampling strategies  
- `prompts.py`: Analysis prompt templates
- `responses.py`: Response parsing and result structures

### Analysis Capabilities

**Currently Implemented**:
- **Headers/Footers Detection**: Content-aware boundary detection with confidence scoring
- **Cost Estimation**: Token counting and cost prediction
- **Status Checking**: Configuration validation and provider status

**Planned Extensions**:
- **Section Hierarchy**: Identification of section patterns and numbering systems
- **Table of Contents**: TOC extraction and cross-validation
- **Multi-Objective Analysis**: Simultaneous pattern detection with priority focus

## Multi-Modal Information Collection Strategy

### Priority-Driven Focus with Comprehensive Data Collection

Rather than sequential phases, the system collects multiple types of information simultaneously while maintaining focus priorities.

**Priority 1 Focus: Headers/Footers** (with simultaneous data collection)
- **Primary Objective**: Establish reliable content area boundaries
- **Secondary Collection**: 
  - Font style usage patterns and their likely purposes
  - Potential section heading candidates (distinctive fonts/spacing)
  - TOC-like content patterns (page numbers, hierarchical text)

**Priority 2 Focus: Section Headings** (with cross-validation)
- **Primary Objective**: Identify section hierarchy and numbering patterns
- **Secondary Collection**:
  - TOC validation opportunities (cross-reference page numbers with section titles)
  - Font style classification refinement (update assumptions based on content analysis)

**Priority 3 Focus: TOC/Lists** (with structural validation)
- **Primary Objective**: Map document navigation structure
- **Secondary Collection**:
  - Section hierarchy validation (TOC entries vs discovered sections)

### Adaptive Decision Framework

**Confidence-Driven Transitions**: Shift focus based on objective confidence levels
- 80% confidence → expand sampling in current focus area
- 90% confidence → shift to next priority focus

**Dynamic Sampling**: Strategic page selection based on information gaps and validation needs
**Pattern Evolution**: Continuous refinement of structural rules based on accumulated evidence

## Technical Implementation

### Token Analysis and Optimization

**Token Requirements** (based on H.264 specification analysis):
- **Average**: ~20,000-24,000 tokens per page
- **High Variability**: ±9,000 tokens standard deviation
- **Conservative Batching**: Required for reliable processing

**GPT-4.1 Batch Recommendations**:
- **Initial batches**: 20 pages (vs GPT-4's 4-page limit)
- **Incremental batches**: 8 pages
- **Context preservation**: 1M token window enables pattern tracking

**Data Optimization**:
- Lines file format provides optimal balance of detail and token efficiency
- Strategic consecutive page sampling for pattern recognition
- Token counting infrastructure for accurate cost prediction

### Configuration and Environment

**Azure OpenAI Configuration**:
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**LLM Analysis Settings**:
```bash
PDF_PLUMB_LLM_BATCH_SIZE=16
PDF_PLUMB_LLM_SAMPLING_GROUPS=3
PDF_PLUMB_LLM_SAMPLING_INDIVIDUALS=4
```

## CLI Integration

### llm-analyze Command

**Basic Usage**:
```bash
# Header/footer analysis
uv run pdf-plumb llm-analyze document_lines.json --focus headers-footers

# Cost estimation
uv run pdf-plumb llm-analyze document_lines.json --estimate-cost

# Configuration status
uv run pdf-plumb llm-analyze document_lines.json --show-status
```

**Parameters**:
- `--focus`: Analysis type (headers-footers, sections, toc, multi-objective)
- `--provider`: LLM provider (azure)
- `--estimate-cost`: Cost estimation without running analysis
- `--no-save`: Skip saving results to files
- `--show-status`: Display configuration status

### Integration with Main Pipeline

**Current Status**: Standalone command for focused analysis
**Future Integration**: LLM analysis as optional enhancement in main `process` command

## Design Philosophy Integration

### Iterative Validation Approach

Following PDF Plumb's established pattern:
1. **Implement programmatic baseline** (contextual spacing analysis)
2. **Add LLM enhancement** for content understanding
3. **Compare and validate** approaches
4. **Standardize on best combination**

### Contextual Foundation

**Building on Existing Strengths**:
- LLM analysis uses contextual blocks as input (not raw lines)
- Leverages proven contextual spacing analysis
- Enhances rather than replaces programmatic methods

## Performance and Scalability

### Cost Management

**Token Efficiency**:
- Strategic sampling reduces analysis cost by ~80%
- Batch optimization for GPT-4.1's large context window
- Cost estimation prevents unexpected charges

**Scalability Considerations**:
- Page-by-page processing for memory efficiency
- Configurable batch sizes for different document types
- Provider abstraction for future model integration

## Future Development

### Multi-Provider Support Framework

**Architecture Ready For**:
- Google Gemini integration
- Anthropic Claude integration
- Local model support (via appropriate APIs)

### Advanced Features (Planned)

**Enhanced Sampling**:
- Document-adaptive sampling strategies
- Confidence-based sample size adjustment
- Cross-validation between multiple samples

**Integration Expansion**:
- Real-time pattern validation
- Incremental analysis for large documents
- Export to structured formats (JSON, XML)

## Cross-References

- **Strategic Framework**: [design/LLM_STRATEGY.md](LLM_STRATEGY.md) - Complete multi-objective analysis framework and advanced features
- **Token Analysis**: [analysis/token_analysis.md](../analysis/token_analysis.md)
- **Strategy Evolution**: [analysis/llm_strategy_evolution.md](../analysis/llm_strategy_evolution.md)
- **Design Decisions**: [design-decisions.md](../design-decisions.md#llm-integration-architecture)
- **Implementation**: `src/pdf_plumb/core/llm_analyzer.py`
- **CLI Documentation**: [cli-usage.md](../cli-usage.md) (llm-analyze section to be added)

This document focuses on the current implementation. For comprehensive strategic framework including font learning systems, anomaly detection, and advanced optimization strategies, see [design/LLM_STRATEGY.md](LLM_STRATEGY.md).