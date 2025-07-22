# PDF Plumb CLI Usage Guide

## 🎉 Modern Click CLI - Phase 2.1 Migration Complete

**Major Update**: PDF Plumb now uses a modern Click-based CLI with Rich console output, replacing the legacy argparse implementation. The new CLI provides enhanced user experience with better help text, progress bars, and document type profiles.

## Installation & Setup

### Method 1: Direct uv execution (Recommended for development)
```bash
# No installation needed - run directly from source
uv run pdf-plumb --help
```

### Method 2: Install package (For system-wide usage)
```bash
# Install in development mode (from project root)
pip install -e .

# Then use the installed command
pdf-plumb --help
```

## Command Overview

PDF Plumb provides three main commands with modern Click interface:
- **`extract`** - Extract text from PDF files using multiple methods
- **`analyze`** - Analyze existing extracted data to determine document structure
- **`process`** - Full pipeline (extract + analyze + visualize)

## New Features in Click CLI

### Document Type Profiles
```bash
# Apply pre-configured settings for different document types
pdf-plumb --profile technical extract document.pdf
pdf-plumb --profile academic process paper.pdf
pdf-plumb --profile manual extract manual.pdf
pdf-plumb --profile dense process dense_doc.pdf
```

### Rich Console Output
- **Progress bars** during PDF processing
- **Emojis and panels** for better visual feedback
- **Color-coded status messages** (✅ success, ❌ error, ℹ️ info)
- **Formatted help text** with better organization

### Enhanced Help System
```bash
# Main help with rich formatting
pdf-plumb --help

# Command-specific help
pdf-plumb extract --help
pdf-plumb analyze --help
pdf-plumb process --help
```

## Command Reference

### 1. Extract Command

Extract text from a PDF file and save structured data for analysis.

**PDF Text Extraction:**
PDF Plumb extracts text using word-based analysis with manual alignment to preserve document structure, fonts, and positioning information needed for intelligent block formation.

**Direct uv execution:**
```bash
uv run pdf-plumb extract input.pdf [options]
```

**Installed package:**
```bash
pdf-plumb extract input.pdf [options]
```

#### Basic Usage
```bash
# Simple extraction
uv run pdf-plumb extract document.pdf

# Custom output directory
uv run pdf-plumb extract document.pdf -o my_output

# Custom base name for output files
uv run pdf-plumb extract document.pdf -b my_document

# With document profile
uv run pdf-plumb --profile technical extract document.pdf
```

#### Advanced Options
```bash
# Adjust tolerance settings for text alignment
uv run pdf-plumb extract document.pdf -y 4.0 -x 2.5

# Enable spacing visualization
uv run pdf-plumb extract document.pdf --visualize-spacing

# Custom visualization with specific spacing ranges
uv run pdf-plumb extract document.pdf --visualize-spacing \
  --spacing-sizes "12.0,14.0-16.0,18.0-" \
  --spacing-colors "red,blue,green" \
  --spacing-patterns "solid,dashed,dotted"

# Debug mode with rich console output
uv run pdf-plumb extract document.pdf --debug-level DEBUG

# Combine profile with custom settings
uv run pdf-plumb --profile technical extract document.pdf \
  --visualize-spacing -y 2.5 --debug-level INFO
```

#### Output Files
- `{basename}_lines.json` - Structured line data with gaps and fonts (main input for analysis)
- `{basename}_words.json` - Raw word-level data (for debugging)
- `{basename}_compare.json` - Extraction method comparison (for debugging)
- `{basename}_info.json` - Metadata and extraction statistics
- `{basename}_visualized.pdf` - Visualization overlay (if requested)

### 2. Analyze Command

Analyze existing extracted text data to identify document structure.

**Direct uv execution:**
```bash
uv run pdf-plumb analyze lines_file.json [options]
```

**Installed package:**
```bash
pdf-plumb analyze lines_file.json [options]
```

#### Basic Usage
```bash
# Analyze extracted data with rich console output
uv run pdf-plumb analyze output/document_lines.json

# Show results on screen instead of saving to file
uv run pdf-plumb analyze output/document_lines.json --show-output

# Custom output file
uv run pdf-plumb analyze output/document_lines.json -f my_analysis.txt
```

#### Output Files
- `{basename}_analysis.txt` - Human-readable analysis report
- `{basename}_blocks.json` - Block-level document structure

### 3. Process Command (Recommended)

Complete pipeline: extract text, analyze structure, and create visualizations.

**Direct uv execution:**
```bash
uv run pdf-plumb process input.pdf [options]
```

**Installed package:**
```bash
pdf-plumb process input.pdf [options]
```

#### Basic Usage
```bash
# Full processing pipeline with rich console output
uv run pdf-plumb process document.pdf

# Show analysis results on screen with progress bars
uv run pdf-plumb process document.pdf --show-output

# Custom output directory and analysis file
uv run pdf-plumb process document.pdf -o results -f detailed_analysis.txt

# With document profile for optimal settings
uv run pdf-plumb --profile technical process document.pdf --show-output
```

#### Advanced Processing
```bash
# Full processing with custom tolerances and visualization
uv run pdf-plumb process document.pdf \
  -y 3.5 -x 3.0 \
  --visualize-spacing \
  --spacing-sizes "10.0-12.0,14.0-16.0,18.0-" \
  --spacing-colors "lightblue,orange,red" \
  --spacing-patterns "solid,dashed,dotted" \
  --show-output \
  --debug-level INFO

# Your example command (actual usage from history)
uv run pdf-plumb process -x 2.5 data/h264_pg305_10pgs.pdf \
  --visualize-spacing --spacing-sizes "1.75-20" --show-output

# Combine profile with custom settings
uv run pdf-plumb --profile technical process document.pdf \
  -x 2.5 --visualize-spacing --show-output
```

#### Output Files
All files from extract + analyze commands plus:
- `{basename}_spacing.pdf` - Line spacing visualization
- `{basename}_block_spacing.pdf` - Block spacing visualization

### 4. LLM Analyze Command

Perform LLM-enhanced analysis of document structure using Azure OpenAI.

**Direct uv execution:**
```bash
uv run pdf-plumb llm-analyze document_lines.json [options]
```

**Installed package:**
```bash
pdf-plumb llm-analyze document_lines.json [options]
```

#### Prerequisites

LLM analysis requires Azure OpenAI configuration via environment variables:
```bash
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=your-api-key-here
export AZURE_OPENAI_DEPLOYMENT=gpt-4
export AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### Basic Usage

```bash
# Header/footer analysis (default)
uv run pdf-plumb llm-analyze output/document_lines.json

# Specific analysis focus
uv run pdf-plumb llm-analyze output/document_lines.json --focus headers-footers

# Cost estimation before running
uv run pdf-plumb llm-analyze output/document_lines.json --estimate-cost

# Check configuration status
uv run pdf-plumb llm-analyze output/document_lines.json --show-status
```

#### Advanced Usage

```bash
# Save results to custom directory
uv run pdf-plumb llm-analyze output/document_lines.json -o llm_results/

# Run analysis without saving files
uv run pdf-plumb llm-analyze output/document_lines.json --no-save

# Multiple analysis types (future)
uv run pdf-plumb llm-analyze output/document_lines.json --focus multi-objective
```

#### LLM Analysis Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_file` | string | required | Path to JSON file from extract/process commands |
| `--focus` | choice | headers-footers | Analysis focus (headers-footers, sections, toc, multi-objective) |
| `--provider` | choice | azure | LLM provider to use |
| `-o, --output-dir` | string | config default | Directory to save analysis results |
| `--estimate-cost` | flag | false | Only estimate cost without running analysis |
| `--no-save` | flag | false | Do not save results to files |
| `--show-status` | flag | false | Show LLM provider configuration status |

#### Expected Input

The `document_file` should be a JSON file produced by the `extract` or `process` commands, typically:
- `{basename}_lines.json` - Structured line data (recommended)
- `{basename}_blocks.json` - Block-level data (also supported)

#### Output Files

When analysis completes successfully:
```
llm_results/
├── llm_headers_footers_20240115_143022_results.json    # Structured analysis results
├── llm_headers_footers_20240115_143022_prompt.txt      # Prompt sent to LLM
└── llm_headers_footers_20240115_143022_response.txt    # Raw LLM response
```

#### Usage Examples

**Example 1: Basic Header/Footer Analysis**
```bash
# First extract document structure
uv run pdf-plumb extract technical_spec.pdf

# Then run LLM analysis
uv run pdf-plumb llm-analyze output/technical_spec_lines.json
```

**Example 2: Cost Estimation Workflow**
```bash
# Check cost before running
uv run pdf-plumb llm-analyze output/large_document_lines.json --estimate-cost

# Output example:
# 💰 Cost Estimation
# Input tokens: ~245,680
# Output tokens: ~1,200  
# Total tokens: ~246,880
# Estimated cost: $0.7406 USD

# Run if cost is acceptable
uv run pdf-plumb llm-analyze output/large_document_lines.json
```

**Example 3: Configuration Troubleshooting**
```bash
# Check if Azure OpenAI is properly configured
uv run pdf-plumb llm-analyze output/document_lines.json --show-status

# Output example:
# 📊 LLM Configuration Status
# Provider: AZURE
# Configured: ✅
# LLM Enabled: ✅
# Batch Size: 16 pages
```

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

## Configuration and Environment Variables

### Configuration Priority (Highest to Lowest)

PDF Plumb uses a hierarchical configuration system where settings can be specified in multiple ways:

1. **CLI Arguments** (highest priority) - Override everything
2. **Profile Settings** (via `--profile` flag) - Override environment variables and defaults  
3. **Environment Variables** (with `PDF_PLUMB_` prefix) - Override defaults only
4. **Default Values** (lowest priority) - Built-in fallback values

### Environment Variables

All configuration settings can be controlled via environment variables with the `PDF_PLUMB_` prefix:

#### Core Settings
```bash
# Extraction tolerances (in points)
PDF_PLUMB_Y_TOLERANCE=3.0
PDF_PLUMB_X_TOLERANCE=3.0

# Analysis settings
PDF_PLUMB_LARGE_GAP_MULTIPLIER=1.8
PDF_PLUMB_SMALL_GAP_MULTIPLIER=1.3
PDF_PLUMB_ROUND_TO_NEAREST_PT=0.5

# Page layout settings
PDF_PLUMB_HEADER_ZONE_INCHES=1.25
PDF_PLUMB_FOOTER_ZONE_INCHES=1.0

# Directories (relative or absolute paths)
PDF_PLUMB_OUTPUT_DIR=output
PDF_PLUMB_DATA_DIR=data

# Logging level
PDF_PLUMB_LOG_LEVEL=INFO
```

#### Contextual Analysis Settings
```bash
# Contextual spacing analysis
PDF_PLUMB_LINE_SPACING_TOLERANCE=0.2
PDF_PLUMB_PARA_SPACING_MULTIPLIER=1.1
PDF_PLUMB_GAP_ROUNDING=0.5
```

#### LLM Analysis Settings
```bash
# LLM integration
PDF_PLUMB_LLM_BATCH_SIZE=16
PDF_PLUMB_LLM_SAMPLING_GROUPS=3
PDF_PLUMB_LLM_SAMPLING_INDIVIDUALS=4
```

#### Azure OpenAI Configuration (for LLM analysis)
```bash
# Azure OpenAI settings (use direct names, not PDF_PLUMB_ prefix)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Document Type Profiles

Instead of manually setting environment variables, you can use predefined profiles optimized for different document types:

```bash
# Apply profile for technical specifications
pdf-plumb --profile technical process document.pdf

# Apply profile for academic papers  
pdf-plumb --profile academic process document.pdf

# Apply profile for user manuals
pdf-plumb --profile manual process document.pdf

# Apply profile for densely-packed documents
pdf-plumb --profile dense process document.pdf
```

**Available Profiles:**
- **technical**: Optimized for technical specifications (default tolerances)
- **academic**: Optimized for academic papers (tighter tolerances)
- **manual**: Optimized for user manuals (looser tolerances for varied layouts)
- **dense**: Optimized for densely-packed documents (very tight tolerances)

### Configuration Examples

#### Example 1: Environment Variables Only
```bash
# Set via environment
export PDF_PLUMB_Y_TOLERANCE=2.5
export PDF_PLUMB_OUTPUT_DIR=/tmp/results

# Run with environment settings
pdf-plumb process document.pdf
```

#### Example 2: Profile + CLI Override
```bash
# Profile sets base configuration, CLI overrides specific settings
pdf-plumb --profile technical process document.pdf -x 2.5 -o custom_output
```

#### Example 3: Full Environment Setup
```bash
# Complete environment configuration
export PDF_PLUMB_LOG_LEVEL=DEBUG
export PDF_PLUMB_Y_TOLERANCE=2.0
export PDF_PLUMB_X_TOLERANCE=1.5
export PDF_PLUMB_OUTPUT_DIR=/project/output

# Azure OpenAI for LLM analysis
export AZURE_OPENAI_ENDPOINT=https://my-resource.openai.azure.com/
export AZURE_OPENAI_API_KEY=sk-...
export AZURE_OPENAI_DEPLOYMENT=gpt-4
export AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Run with all environment settings
pdf-plumb process document.pdf --show-output
```

### Priority Examples

```bash
# Environment variable sets default
export PDF_PLUMB_Y_TOLERANCE=4.0

# Profile overrides environment variable  
pdf-plumb --profile dense process doc.pdf  # Uses dense profile Y_TOLERANCE=2.0

# CLI argument overrides everything
pdf-plumb --profile dense process doc.pdf -y 5.0  # Uses Y_TOLERANCE=5.0
```

## Token Analysis Utilities

The following scripts are available for LLM analysis planning and optimization:

### analyze_tokens.py
```bash
python scripts/analyze_tokens.py document_lines.json
```
Analyzes token requirements for LLM analysis and provides batch size recommendations.

**Output**: Token statistics, batch size recommendations, cost estimates for different page counts.

### precision_analysis.py  
```bash
python scripts/precision_analysis.py document_lines.json
```
Tests coordinate precision reduction for token optimization (research tool).

**Output**: Token savings analysis with different precision levels (1-4 decimal places).

### field_analysis.py
```bash  
python scripts/field_analysis.py document_lines.json
```
Analyzes field name compression opportunities for token savings (research tool).

**Output**: Field usage statistics and potential token reduction through field name shortening.

### llm_header_footer_analysis.py
```bash
python scripts/llm_header_footer_analysis.py document_lines.json
```
Standalone LLM header/footer analysis script for testing and development.

**Note**: These scripts are primarily for analysis planning and research. For production LLM analysis, use the `llm-analyze` command.

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
├── document_compare.json         # Method comparison (debugging)
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