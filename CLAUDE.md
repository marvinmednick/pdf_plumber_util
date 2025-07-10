# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Context

PDF Plumb is a Python PDF text extraction and analysis tool for technical documents. Uses multiple extraction methods to identify document structure, fonts, spacing patterns, and generates visualizations.

**Current Phase**: Phase 2.3 Performance Optimization (after completed Enhanced Error Handling)

## Common Commands

```bash
# Development
uv run pdf-plumb --help                    # Modern Click CLI
uv run pdf-plumb process test.pdf --show-output
uv run pdf-plumb --profile technical extract test.pdf

# Testing
uv run pytest                             # All tests (28 passing)
uv run pytest -m unit                     # Unit tests only
uv run pytest -m integration              # Integration tests only
uv run pytest -v                          # Verbose output

# Code quality (when available)
uv run ruff check                          # Linting
uv run black .                             # Code formatting
```

## Architecture Overview

**Technology Stack**: Click + Rich + Pydantic + UV (Python 3.12+)
- **Click**: Modern CLI framework (Phase 2.1 migration complete)
- **Rich**: Console formatting, progress bars, panels, emojis
- **Pydantic**: Configuration management with document type profiles
- **Three extraction methods**: Raw text, lines, word-based manual alignment

**Directory Structure**:
```
src/pdf_plumb/
├── cli.py               # Modern Click CLI entry point
├── config.py            # Pydantic configuration with profiles
├── core/
│   ├── extractor.py     # Three PDF extraction methods
│   ├── analyzer.py      # Document structure analysis
│   └── visualizer.py    # PDF spacing visualization
├── utils/               # Shared utilities and helpers
tests/
├── unit/                # Unit tests for individual functions
├── integration/         # CLI command integration tests
└── conftest.py          # Shared test fixtures
```

**Key Files to Read First**:
- `src/pdf_plumb/cli.py` - Click CLI with Rich console integration
- `src/pdf_plumb/config.py` - Pydantic configuration and profiles
- `src/pdf_plumb/core/extractor.py` - Three extraction methods implementation
- `CLI_USAGE.md` - Complete user command reference

## Development Patterns

### Adding New CLI Commands
1. Add command function to `src/pdf_plumb/cli.py` using Click decorators
2. Use common decorators: `@common_options`, `@visualization_options`
3. Implement Rich console output: `console.print(f"✅ Success message")`
4. Add integration tests in `tests/integration/test_cli_commands.py`
5. Update CLI_USAGE.md with examples

### Error Handling (Phase 2.2 Complete)
**Implemented Pattern**:
```python
from .core.exceptions import PDFExtractionError, AnalysisError

try:
    # operation
except PDFExtractionError as e:
    console.print(f"❌ [red]Extraction Failed:[/red] {e.message}")
    if e.suggestion:
        console.print(f"💡 [yellow]Suggestion:[/yellow] {e.suggestion}")
    if e.context:
        console.print(f"🔍 [blue]Context:[/blue] {e.context}")
    raise click.Abort()
```

**Features**:
- **Structured Exception Hierarchy**: 15+ specialized exception classes
- **Rich Console Integration**: Color-coded errors with emojis
- **Context & Suggestions**: Automatic helpful guidance for error resolution
- **Retry Mechanisms**: Automatic retry logic for transient failures

### Configuration Management
- All settings in `src/pdf_plumb/config.py` using Pydantic BaseSettings
- Document type profiles: `--profile technical|academic|manual|dense`
- Environment variables with `PDF_PLUMB_` prefix
- Test configuration: `apply_profile()` function

### Testing Strategy
- **Unit tests** (`tests/unit/`): Fast tests for core functions with mocks
- **Integration tests** (`tests/integration/`): Full CLI command testing with CliRunner
- **Real PDF testing**: Validated CLI migration with actual H.264 spec document
- **Markers**: Use `@pytest.mark.unit` and `@pytest.mark.integration`

## Documentation Strategy

### Core Documentation (Always Present)
- README.md, STATUS.md, CLI_USAGE.md, ARCHITECTURE.md, CLAUDE.md

### Optional Documentation (Create When Needed)
- `docs/performance.md` - Create when performance profiling conducted
- `docs/troubleshooting.md` - Create when common issues identified
- `docs/api.md` - Create if API endpoints added

**Principle**: Only create documentation when specific need arises. File existence indicates actual work/analysis conducted.

## Performance Considerations

Consider adding `docs/performance.md` when:
- PDF processing time >30 seconds for typical documents
- Memory usage >1GB during operation  
- Processing large PDFs (>100MB files, >100 pages)
- Performance requirements explicitly defined

**Standard profiling tools**: cProfile, memory_profiler, line_profiler, py-spy

## Phase 2.3 Implementation Notes

**Current Development Priority**: Performance Optimization
1. Profile PDF processing performance with large documents (>100MB, >100 pages)
2. Implement memory optimization for page-by-page processing
3. Add caching mechanisms for commonly accessed data
4. Optimize data structure usage and text processing algorithms

**Phase 2.2 Achievements** ✅:
- ✅ Structured exception hierarchy with 15+ specialized classes
- ✅ Rich console error formatting with colors and emojis
- ✅ Error context and recovery suggestions system
- ✅ Retry mechanisms for transient failures
- ✅ Comprehensive error handling test coverage (21 tests)

## Template-Specific Notes

This project structure supports PDF analysis development by:
- **Multi-method extraction validation** - Three extraction methods for accuracy
- **Rich console experience** - Professional CLI with progress bars and emojis
- **Document type profiles** - Pre-configured settings for different PDF types  
- **Comprehensive testing** - Real PDF validation ensures reliability
- **Modern Python practices** - Click + Rich + Pydantic for maintainability