# PDF Plumb

A Python PDF text extraction and analysis tool for technical documents. Combines intelligent document structure analysis with LLM-enhanced content understanding to identify headers, footers, sections, and document patterns.

## Features

- **Intelligent Text Extraction**: Word-based extraction with contextual spacing analysis
- **Document Structure Analysis**: Font-aware block formation and boundary detection
- **LLM Integration**: Azure OpenAI-powered content analysis for headers/footers and sections
- **Modern CLI**: Click + Rich interface with profiles, progress bars, and error handling
- **Performance Optimized**: Sub-linear scaling with orjson integration
- **Comprehensive Testing**: Robust test suite with unit, integration, and golden document tests

## Quick Start

```bash
# Install dependencies
uv sync

# Basic document processing
uv run pdf-plumb process document.pdf --show-output

# Extract and analyze separately
uv run pdf-plumb extract document.pdf
uv run pdf-plumb analyze output/document_lines.json

# LLM-enhanced analysis (requires Azure OpenAI setup)
uv run pdf-plumb llm-analyze output/document_lines.json --focus headers-footers

# Use document type profiles
uv run pdf-plumb --profile technical process document.pdf
```

## What You Get

Running `process` on a PDF produces a set of structured output files
(default: `output/`):

```
output/
├── document_full_lines.json   # Raw line data, including blank lines
├── document_lines.json        # Cleaned line data - main input for analysis
├── document_words.json        # Raw word-level data (debugging)
├── document_compare.json      # Extraction method comparison (debugging)
├── document_info.json         # Metadata and extraction statistics
├── document_blocks.json       # Lines grouped into paragraphs/headings
└── document_analysis.txt      # Human-readable structure report
```

See the [Output Files Reference](docs/output-files.md) for the full schema
of each file and how they feed into `llm-analyze`.

## LLM Analysis

PDF Plumb integrates with Azure OpenAI for intelligent document analysis:

- **Header/Footer Detection**: Content-aware boundary identification
- **Cost Estimation**: Token counting and cost prediction before analysis
- **Strategic Sampling**: Efficient analysis using representative page samples
- **Multiple Focus Areas**: Headers/footers, sections, table of contents

Requires Azure OpenAI configuration. See documentation for setup details.

## Documentation

- **[CLI Usage Guide](docs/cli-usage.md)** - Complete command reference and examples
- **[Output Files Reference](docs/output-files.md)** - What each command produces and how the JSON is structured
- **[Architecture Overview](docs/architecture.md)** - System design and components
- **[Design Decisions](docs/design-decisions.md)** - Key architectural choices and rationale
- **[Development Guide](CLAUDE.md)** - Documentation navigation for developers

## Current Status

LLM integration implemented with Azure OpenAI support, strategic sampling, and cost estimation. Core functionality stable with modern CLI interface and comprehensive testing coverage.

## Technology Stack

Python 3.12+ • Click + Rich • Pydantic • Azure OpenAI • pdfplumber • orjson

**Requirements**: Python 3.12+, uv package manager  
**Optional**: Azure OpenAI account for LLM analysis features