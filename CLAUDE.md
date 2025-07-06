# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Plumb is a Python PDF text extraction and analysis tool that provides comprehensive PDF document analysis capabilities. The tool uses multiple extraction strategies and advanced text processing to identify document structure, fonts, spacing patterns, headers/footers, and generates detailed visualizations.

## Development Environment

This project uses Python 3.12+ and is managed with uv (modern Python package management).

**Key dependencies:**
- `pdfplumber>=0.11.6` - Primary PDF processing library
- `pdfminer-six>=20250327` - Low-level PDF text extraction
- `pymupdf>=1.25.5` - PDF manipulation and visualization

## Common Commands

### CLI Usage
The main CLI is accessible via the `pdf-plumb` command after installation:

```bash
# Extract text from PDF
pdf-plumb extract input.pdf -o output_dir

# Analyze existing extracted data
pdf-plumb analyze output_dir/filename_lines.json

# Complete extraction and analysis pipeline
pdf-plumb process input.pdf -o output_dir --visualize-spacing
```

### Development Scripts
Several standalone scripts are available in the root directory:

```bash
# Legacy extraction script (plumb3.py)
python plumb3.py input.pdf --output-dir extract

# Font analysis
python get_fonts.py

# Line analysis
python get_lines.py

# Vector analysis
python get_vectors.py
```

### Testing
No formal test framework is currently configured. Test by running CLI commands on sample PDFs and examining output files.

## Code Architecture

### Core Components

**Main CLI Entry Point**: `src/pdf_plumb/cli.py`
- Provides three main commands: `extract`, `analyze`, `process`
- Handles argument parsing, tolerance settings, visualization options
- Coordinates between extractor, analyzer, and visualizer components

**PDF Processing Pipeline**: `src/pdf_plumb/core/`
- `extractor.py` - PDFExtractor class handles multi-method text extraction
- `analyzer.py` - DocumentAnalyzer and PDFAnalyzer classes perform document structure analysis  
- `visualizer.py` - SpacingVisualizer creates PDF visualizations with spacing overlays

**Support Utilities**: `src/pdf_plumb/utils/`
- `file_handler.py` - Centralized file I/O operations
- `helpers.py` - Utility functions for text normalization, path handling
- `constants.py` - Configuration constants (page dimensions, tolerances, etc.)

### Data Flow

1. **Extraction** (`PDFExtractor`):
   - Uses three methods: `extract_text()`, `extract_text_lines()`, `extract_words()` 
   - Groups words into lines based on y-tolerance
   - Creates text segments by font/size changes
   - Calculates gaps between lines and predominant fonts/sizes
   - Outputs: `*_lines.json`, `*_words.json`, `*_compare.json`, `*_info.json`

2. **Analysis** (`DocumentAnalyzer`):
   - Analyzes font usage, size distribution, spacing patterns
   - Identifies header/footer boundaries using traditional and contextual methods
   - Performs contextual spacing analysis based on font sizes
   - Creates block-level groupings of lines
   - Outputs: `*_analysis.txt`, `*_blocks.json`

3. **Visualization** (`SpacingVisualizer`):
   - Overlays colored lines on original PDF to show spacing patterns
   - Supports custom spacing ranges, colors, and line patterns
   - Creates legend pages explaining visualization
   - Outputs: `*_visualized.pdf`, `*_spacing.pdf`, `*_block_spacing.pdf`

### Key Algorithms

**Contextual Spacing Analysis**: Groups lines by predominant font size and analyzes spacing patterns within each context. This allows more accurate classification of line spacing vs paragraph spacing vs section spacing.

**Block Formation**: Combines consecutive lines with the same predominant size whose gaps fall within contextual line spacing ranges into logical blocks.

**Header/Footer Detection**: Uses both traditional Y-coordinate analysis and contextual gap analysis to identify document boundaries.

## Important Implementation Notes

- All spacing values are rounded to nearest 0.5pt for consistency
- Lines with no text content are filtered out during processing  
- Gap calculations handle edge cases like overlapping lines
- File operations are centralized through FileHandler for consistent output structure
- Multiple extraction methods are compared to identify potential text processing issues

## Output Files Structure

Generated files follow naming pattern: `{basename}_{type}.json`
- `_lines.json` - Processed line data with segments, gaps, fonts
- `_words.json` - Raw word-level extraction data  
- `_compare.json` - Comparison between extraction methods
- `_info.json` - Metadata and extraction statistics
- `_analysis.txt` - Human-readable analysis report
- `_blocks.json` - Block-level document structure
- `_visualized.pdf` - PDF with spacing visualization overlays