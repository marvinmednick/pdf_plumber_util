# PDF Plumb CLI Usage Guide

## Installation & Setup

### Method 1: Direct uv execution (Recommended for development)
```bash
# No installation needed - run directly from source
uv run -m pdf_plumb.cli --help
```

### Method 2: Install package (For system-wide usage)
```bash
# Install in development mode (from project root)
pip install -e .

# Then use the installed command
pdf-plumb --help
```

## Command Overview

PDF Plumb provides three main commands:
- **`extract`** - Extract text from PDF files
- **`analyze`** - Analyze existing extracted data
- **`process`** - Full pipeline (extract + analyze + visualize)

## Command Reference

### 1. Extract Command

Extract text from a PDF file using multiple methods and save structured data.

**Direct uv execution:**
```bash
uv run -m pdf_plumb.cli extract input.pdf [options]
```

**Installed package:**
```bash
pdf-plumb extract input.pdf [options]
```

#### Basic Usage
```bash
# Simple extraction
uv run -m pdf_plumb.cli extract document.pdf

# Custom output directory
uv run -m pdf_plumb.cli extract document.pdf -o my_output

# Custom base name for output files
uv run -m pdf_plumb.cli extract document.pdf -b my_document
```

#### Advanced Options
```bash
# Adjust tolerance settings for text alignment
uv run -m pdf_plumb.cli extract document.pdf -y 4.0 -x 2.5

# Enable spacing visualization
uv run -m pdf_plumb.cli extract document.pdf --visualize-spacing

# Custom visualization with specific spacing ranges
uv run -m pdf_plumb.cli extract document.pdf --visualize-spacing \
  --spacing-sizes "12.0,14.0-16.0,18.0-" \
  --spacing-colors "red,blue,green" \
  --spacing-patterns "solid,dashed,dotted"

# Debug mode
uv run -m pdf_plumb.cli extract document.pdf --debug-level DEBUG
```

#### Output Files
- `{basename}_lines.json` - Processed line data with gaps and fonts
- `{basename}_words.json` - Raw word-level data
- `{basename}_compare.json` - Comparison between extraction methods
- `{basename}_info.json` - Metadata and statistics
- `{basename}_visualized.pdf` - Visualization overlay (if requested)

### 2. Analyze Command

Analyze existing extracted text data to identify document structure.

**Direct uv execution:**
```bash
uv run -m pdf_plumb.cli analyze lines_file.json [options]
```

**Installed package:**
```bash
pdf-plumb analyze lines_file.json [options]
```

#### Basic Usage
```bash
# Analyze extracted data
uv run -m pdf_plumb.cli analyze output/document_lines.json

# Show results on screen instead of saving to file
uv run -m pdf_plumb.cli analyze output/document_lines.json --show-output

# Custom output file
uv run -m pdf_plumb.cli analyze output/document_lines.json -f my_analysis.txt
```

#### Output Files
- `{basename}_analysis.txt` - Human-readable analysis report
- `{basename}_blocks.json` - Block-level document structure

### 3. Process Command (Recommended)

Complete pipeline: extract text, analyze structure, and create visualizations.

**Direct uv execution:**
```bash
uv run -m pdf_plumb.cli process input.pdf [options]
```

**Installed package:**
```bash
pdf-plumb process input.pdf [options]
```

#### Basic Usage
```bash
# Full processing pipeline
uv run -m pdf_plumb.cli process document.pdf

# Show analysis results on screen
uv run -m pdf_plumb.cli process document.pdf --show-output

# Custom output directory and analysis file
uv run -m pdf_plumb.cli process document.pdf -o results -f detailed_analysis.txt
```

#### Advanced Processing
```bash
# Full processing with custom tolerances and visualization
uv run -m pdf_plumb.cli process document.pdf \
  -y 3.5 -x 3.0 \
  --visualize-spacing \
  --spacing-sizes "10.0-12.0,14.0-16.0,18.0-" \
  --spacing-colors "lightblue,orange,red" \
  --spacing-patterns "solid,dashed,dotted" \
  --show-output \
  --debug-level INFO

# Your example command (actual usage from history)
uv run -m pdf_plumb.cli process -x 2.5 data/h264_pg305_10pgs.pdf \
  --visualize-spacing --spacing-sizes "1.75-20" --show-output
```

#### Output Files
All files from extract + analyze commands plus:
- `{basename}_spacing.pdf` - Line spacing visualization
- `{basename}_block_spacing.pdf` - Block spacing visualization

## Parameter Reference

### Common Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pdf_file` | string | required | Path to input PDF file |
| `-o, --output-dir` | string | "output" | Directory for output files |
| `-b, --basename` | string | PDF filename | Base name for output files |
| `-y, --y-tolerance` | float | 3.0 | Y-axis tolerance for word alignment |
| `-x, --x-tolerance` | float | 3.0 | X-axis tolerance for word alignment |
| `--debug-level` | choice | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Visualization Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--visualize-spacing` | flag | Generate visualization PDF |
| `--spacing-sizes` | string | Comma-separated spacing ranges to visualize |
| `--spacing-colors` | string | Comma-separated colors for each spacing |
| `--spacing-patterns` | string | Comma-separated line patterns |

### Analysis Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `-f, --output-file` | string | Custom path for analysis output |
| `--show-output` | flag | Display analysis results on stdout |

## Spacing Visualization Options

### Spacing Size Formats
- **Single value**: `"12.0"` - Exact spacing value
- **Range**: `"12.0-14.0"` - Between two values
- **Less than or equal**: `"-14.0"` - Up to this value
- **Greater than or equal**: `"14.0-"` - This value and above
- **Large range**: `"1.75-20"` - All spacing from 1.75pt to 20pt (as in your example)

### Color Options
Standard color names: `red`, `blue`, `green`, `purple`, `orange`, `pink`, `magenta`, `yellow`, `lightblue`, `darkred`, `darkblue`, `darkgreen`, etc.

### Pattern Options
- `solid` - Continuous lines
- `dashed` - Dashed lines
- `dotted` - Dotted lines  
- `dashdot` - Alternating dash-dot pattern

## Usage Examples

### Example 1: Basic Document Analysis
```bash
# Extract and analyze a technical specification
uv run -m pdf_plumb.cli process technical_spec.pdf --show-output
```
**Output**: Complete analysis with line/block structure, headers/footers identified

### Example 2: Your Actual Usage Pattern
```bash
# Based on your command history
uv run -m pdf_plumb.cli process -x 2.5 data/h264_pg305_10pgs.pdf \
  --visualize-spacing --spacing-sizes "1.75-20" --show-output
```
**Output**: Processing with tighter X-tolerance, visualization of all spacing from 1.75-20pt, analysis displayed on screen

### Example 3: Detailed Visualization
```bash
# Create visualization showing different spacing patterns
uv run -m pdf_plumb.cli process manual.pdf \
  --visualize-spacing \
  --spacing-sizes "10.0-12.0,14.0,16.0-18.0,20.0-" \
  --spacing-colors "lightblue,green,orange,red" \
  --spacing-patterns "solid,dashed,dotted,dashdot"
```
**Output**: PDF with color-coded spacing overlays and legend

### Example 4: Fine-Tuned Extraction
```bash
# Adjust tolerances for tightly-spaced document
uv run -m pdf_plumb.cli process dense_document.pdf \
  -y 2.0 -x 1.5 \
  --debug-level DEBUG \
  --show-output
```
**Output**: More precise text grouping with detailed logging

### Example 5: Two-Stage Processing
```bash
# First extract data
uv run -m pdf_plumb.cli extract document.pdf -o temp_results

# Then analyze with custom settings
uv run -m pdf_plumb.cli analyze temp_results/document_lines.json \
  --show-output \
  -f detailed_report.txt
```
**Output**: Separated extraction and analysis for debugging

### Example 6: Using Installed Package
```bash
# If you've run: pip install -e .
pdf-plumb process document.pdf --show-output
pdf-plumb extract document.pdf --visualize-spacing
```

## Legacy Scripts

The project also includes standalone legacy scripts in the root directory:

### plumb3.py (Legacy Extraction)
```bash
python plumb3.py document.pdf --output-dir extract
```
Note: This uses "extract" as the default output directory (older pattern)

### analyzer_head.py (Standalone Header/Footer Analysis)
```bash
python analyzer_head.py output/document_lines.json
```

## Testing Commands for Migration

### Test Basic Functionality
```bash
# Test simple extraction
uv run -m pdf_plumb.cli extract test_document.pdf

# Test analysis
uv run -m pdf_plumb.cli analyze output/test_document_lines.json --show-output

# Test full pipeline
uv run -m pdf_plumb.cli process test_document.pdf --show-output
```

### Test Visualization
```bash
# Test basic visualization
uv run -m pdf_plumb.cli process test_document.pdf --visualize-spacing

# Test custom visualization (your pattern)
uv run -m pdf_plumb.cli process test_document.pdf \
  --visualize-spacing \
  --spacing-sizes "1.75-20" \
  --show-output
```

### Test Edge Cases
```bash
# Test tight tolerances
uv run -m pdf_plumb.cli process test_document.pdf -y 1.0 -x 1.0

# Test loose tolerances  
uv run -m pdf_plumb.cli process test_document.pdf -y 5.0 -x 5.0

# Test debug output
uv run -m pdf_plumb.cli process test_document.pdf --debug-level DEBUG
```

## Output File Structure

After running `uv run -m pdf_plumb.cli process document.pdf`, expect these files in the output directory:

```
output/
├── document_lines.json           # Main structured data
├── document_words.json           # Raw word data
├── document_compare.json         # Method comparison
├── document_info.json            # Metadata
├── document_analysis.txt         # Human-readable analysis
├── document_blocks.json          # Block structure
├── document_visualized.pdf       # Spacing visualization
├── document_spacing.pdf          # Line spacing overlay
└── document_block_spacing.pdf    # Block spacing overlay
```

## Troubleshooting

### Common Issues
1. **Permission errors**: Ensure output directory is writable
2. **Missing dependencies**: Run `uv sync` to install all dependencies
3. **PDF parsing errors**: Try adjusting tolerance values
4. **Visualization failures**: PyMuPDF dependency issues (development only)

### Debug Steps
```bash
# Enable debug logging
uv run -m pdf_plumb.cli process problem.pdf --debug-level DEBUG

# Test without visualization first
uv run -m pdf_plumb.cli extract problem.pdf

# Check output files manually
ls -la output/

# Check if using old extract directory
ls -la extract/
```

## Installation Methods Comparison

| Method | Command Format | Use Case |
|--------|----------------|----------|
| Direct uv | `uv run -m pdf_plumb.cli` | Development, testing |
| Installed package | `pdf-plumb` | Production, system-wide usage |
| Legacy scripts | `python plumb3.py` | Backward compatibility |