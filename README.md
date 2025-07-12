# PDF Plumb

A high-performance Python PDF text extraction and analysis tool for technical documents. Uses multiple extraction methods to identify document structure, fonts, spacing patterns, and generates visualizations.

## Features

- **Multi-Method Extraction**: Raw text, lines, and word-based extraction with manual alignment
- **Document Analysis**: Font usage, spacing patterns, header/footer detection, block formation
- **Performance Optimized**: orjson integration for 10% faster processing
- **Modern CLI**: Click + Rich interface with progress bars and error handling
- **Comprehensive Testing**: 28+ tests with detailed error handling coverage
- **Scalable Architecture**: Sub-linear performance scaling validated

## Quick Start

```bash
# Install dependencies
uv sync

# Extract text from PDF
uv run pdf-plumb extract document.pdf

# Analyze extracted data  
uv run pdf-plumb analyze output/document_lines.json

# View all options
uv run pdf-plumb --help
```

## Performance

- **20-page documents**: ~12.5 seconds
- **100-page documents**: ~45 seconds (sub-linear scaling)
- **Memory efficient**: Page-by-page processing
- **JSON optimized**: 56% function call reduction with orjson

## Technology Stack

- **Python 3.12+** with UV package management
- **Click + Rich** for modern CLI experience
- **Pydantic** for configuration management  
- **orjson** for high-performance JSON serialization
- **pdfplumber** for reliable PDF processing

## Status

**Phase 2.3**: Performance optimization complete - JSON bottleneck eliminated. Further optimization deferred as current performance meets requirements.

See [STATUS.md](STATUS.md) for detailed project status and [CLAUDE.md](CLAUDE.md) for development context.