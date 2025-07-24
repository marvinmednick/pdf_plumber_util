# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Context

PDF Plumb is a Python PDF text extraction and analysis tool for technical documents. Uses multiple extraction methods to identify document structure, fonts, spacing patterns, and generates visualizations.

**Current Phase**: Phase 2.3 Performance Optimization (JSON optimization complete - further optimization deferred)

## Common Commands

```bash
# Development
uv run pdf-plumb --help                    # Modern Click CLI
uv run pdf-plumb process test.pdf --show-output
uv run pdf-plumb --profile technical extract test.pdf

# LLM Analysis (requires Azure OpenAI configuration)
uv run pdf-plumb llm-analyze output/doc_blocks.json --show-status
uv run pdf-plumb llm-analyze output/doc_blocks.json --focus headers-footers
uv run pdf-plumb llm-analyze output/doc_blocks.json --estimate-cost

# Testing
uv run pytest                             # All tests
uv run pytest -m unit                     # Unit tests only
uv run pytest -m integration              # Integration tests only
uv run pytest -v                          # Verbose output

# Code quality (when available)
uv run ruff check                          # Linting
uv run black .                             # Code formatting
```

## Architecture Overview

**Technology Stack**: Click + Rich + Pydantic + UV + orjson + Azure OpenAI (Python 3.12+)
- **Click**: Modern CLI framework (Phase 2.1 migration complete)
- **Rich**: Console formatting, progress bars, panels, emojis
- **Pydantic**: Configuration management with document type profiles
- **orjson**: High-performance JSON serialization (3-5x faster than standard json)
- **Azure OpenAI**: LLM-enhanced document structure analysis (Phase 3.0)
- **Three extraction methods**: Raw text, lines, word-based manual alignment

**Directory Structure**:
```
src/pdf_plumb/
├── cli.py               # Modern Click CLI entry point (includes llm-analyze)
├── config.py            # Pydantic configuration with profiles + Azure OpenAI
├── core/
│   ├── extractor.py     # Three PDF extraction methods
│   ├── analyzer.py      # Document structure analysis
│   ├── llm_analyzer.py  # LLM-enhanced analysis coordinator
│   └── visualizer.py    # PDF spacing visualization
├── llm/                 # LLM integration module
│   ├── providers.py     # Azure OpenAI provider
│   ├── sampling.py      # Strategic page sampling
│   ├── prompts.py       # Analysis prompt templates
│   └── responses.py     # Response parsing
├── utils/               # Shared utilities and helpers
│   └── token_counter.py # Token counting for LLM batch optimization
tests/
├── unit/                # Unit tests for individual functions
├── integration/         # CLI command integration tests
└── conftest.py          # Shared test fixtures
```

**Key Files to Read First**:
- `src/pdf_plumb/cli.py` - Click CLI with Rich console integration + LLM commands
- `src/pdf_plumb/config.py` - Pydantic configuration and profiles + Azure OpenAI settings
- `src/pdf_plumb/core/extractor.py` - Three extraction methods implementation
- `src/pdf_plumb/core/llm_analyzer.py` - LLM-enhanced analysis coordinator
- `src/pdf_plumb/llm/providers.py` - Azure OpenAI integration
- `CLI_USAGE.md` - Complete user command reference

## Development Patterns

### Architecture Documentation Standards
- **Track documentation changes in git commits**: Architecture and feature documentation history should be maintained through git commit messages
- **Review revisions for completeness**: When updating major documents like ARCHITECTURE.md, ensure changes are properly documented in commit messages for future reference

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

### Test Docstring Standards
Test docstrings should explain **what is tested and how** for code review purposes.

**Structure:**
- **Purpose**: What method/capability is being tested
- **Test setup**: Key data and conditions created
- **What it verifies**: Specific assertions and validations
- **Test limitations**: What isn't covered or weak assertions
- **Key insight**: One-sentence summary of what the test proves

**Be specific**: Use exact values (14pt font, 6.0pt gap) not generic terms ("various sizes", "edge cases").

**Full guidelines**: See [docs/test_docstring_guidelines.md](docs/test_docstring_guidelines.md) for detailed standards and examples

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

**Current Development Priority**: Performance Optimization (JSON optimization complete)
1. ✅ **JSON optimization complete**: orjson implementation providing 10% pipeline improvement
2. ✅ **Performance testing framework**: Comprehensive profiling and scaling validation  
3. ✅ **Sub-linear scaling confirmed**: 35% better than linear for medium files
4. **Further optimization deferred**: pdfplumber retained for functionality reasons

**Phase 2.3 Achievements** ✅:
- ✅ orjson integration with 56% function call reduction  
- ✅ Performance testing framework with detailed profiling
- ✅ JSON bottleneck elimination from performance profile
- ✅ Comprehensive performance baseline and scaling analysis

**Phase 2.2 Achievements** ✅:
- ✅ Structured exception hierarchy with 15+ specialized classes
- ✅ Rich console error formatting with colors and emojis
- ✅ Error context and recovery suggestions system
- ✅ Retry mechanisms for transient failures
- ✅ Comprehensive error handling test coverage (21 tests)

**Performance Optimization Status**:
- **PDF Processing**: Intentionally retained pdfplumber for functionality over performance
- **Further optimization**: Not currently planned or considered urgent
- **Current performance**: Adequate for project requirements (12.46s for 20 pages)
- **Future work**: Can be revisited if requirements change

## Documentation Navigation for Development

This project uses a hierarchical documentation structure designed to preserve design decisions while providing clear user guidance. When working on features or making architectural decisions, use this guide to find relevant context.

### Documentation Hierarchy

**Tier 1: User Entry Points**
- `README.md` - Project overview, quick start, features list
- `CLI_USAGE.md` - Complete command reference with examples and environment variables
- `INSTALLATION.md` - Setup and configuration (to be created if needed)

**Tier 2: Architecture & Design Context**
- `ARCHITECTURE.md` - System design, component relationships, data flow
- `DESIGN_DECISIONS.md` - **KEY FOR DEVELOPMENT** - Architectural choices and rationale
- `PHASE_HISTORY.md` - Detailed development phase history and achievements

**Tier 3: Implementation Deep-Dives**
- `design/BLOCK_GROUPING.md` - Contextual spacing and block formation algorithm
- `design/HEADER_FOOTER_DETECTION.md` - Iterative boundary detection development
- `design/STATE_MACHINE_ARCHITECTURE.md` - State machine orchestrator for multi-objective analysis workflows
- `design/LLM_INTEGRATION.md` - LLM implementation guide and current usage
- `design/LLM_STRATEGY.md` - Complete LLM strategic framework and advanced features
- `design/CONTEXTUAL_SPACING.md` - Core spacing analysis algorithm (to be created)

**Tier 4: Analysis & Strategy**
- `analysis/token_analysis.md` - LLM token counting analysis and batch sizing
- `analysis/performance_optimization.md` - Performance analysis and decisions (to be created)
- `analysis/llm_strategy_evolution.md` - How LLM approach evolved (to be created)

### When to Reference Which Documents

**Before making architectural changes:**
1. Check `DESIGN_DECISIONS.md` for existing rationale
2. Review relevant `design/*.md` for implementation details
3. Check `analysis/*.md` for supporting data

**When implementing new features:**
1. Start with `ARCHITECTURE.md` for system overview
2. Review related design docs for patterns to follow
3. Update `DESIGN_DECISIONS.md` with new choices

**When adding LLM capabilities:**
1. `design/STATE_MACHINE_ARCHITECTURE.md` - State machine framework for multi-objective workflows
2. `design/LLM_INTEGRATION.md` - Current implementation and usage
3. `design/LLM_STRATEGY.md` - Complete strategic framework and advanced features
4. `analysis/token_analysis.md` - Batch sizing and cost analysis
5. `analysis/llm_strategy_evolution.md` - How the approach evolved

**When optimizing performance:**
1. `analysis/token_analysis.md` - Token optimization and LLM performance analysis
2. `PHASE_HISTORY.md#phase-23` - Phase 2.3 performance optimization details
3. Relevant design docs for implementation details

**When reviewing project evolution:**
1. `PHASE_HISTORY.md` - Complete development phase history and achievements
2. `DESIGN_DECISIONS.md` - Current architectural rationale
3. `STATUS.md` - Current phase summary with references

### Documentation Update Protocol

**When adding features:**
- Update user docs (`README.md`, `CLI_USAGE.md`) first
- Document design decisions in `DESIGN_DECISIONS.md`
- Create/update relevant design docs
- Cross-reference between levels

**When changing architecture:**
- Update `ARCHITECTURE.md` with new design
- Document rationale in `DESIGN_DECISIONS.md` 
- Determine if need to create/update design docs
- Add entry to `PHASE_HISTORY.md`

### Documentation Guidelines

**STATUS.md Guidelines:**
- Focus on current development phase and immediate next steps
- Keep to ~100 lines maximum
- Avoid detailed technical explanations (use design docs for that)
- Update when phases change, not for minor feature additions

**README.md Guidelines:**
- Brief project overview and key features (including LLM analysis)
- Quick start instructions
- Link to detailed documentation
- Keep under 100 lines for accessibility

**CLI_USAGE.md Guidelines:**
- Complete command reference with examples
- Environment variable documentation and priority rules:
  1. CLI arguments (highest priority)
  2. Profile settings (via `--profile` flag)
  3. Environment variables (with `PDF_PLUMB_` prefix)
  4. Default values (lowest priority)
- Configuration examples and troubleshooting

### Cross-Reference Patterns

Use this format for linking between documentation levels:
```markdown
See: [design/BLOCK_GROUPING.md](design/BLOCK_GROUPING.md)
Design rationale: [DESIGN_DECISIONS.md#spacing-analysis](DESIGN_DECISIONS.md)
Performance analysis: [analysis/performance_optimization.md](analysis/performance_optimization.md)
```

## Template-Specific Notes

This project structure supports PDF analysis development by:
- **Iterative validation approach** - Implement multiple methods, compare, choose best
- **Rich console experience** - Professional CLI with progress bars and emojis
- **Document type profiles** - Pre-configured settings for different PDF types  
- **Comprehensive testing** - Real PDF validation ensures reliability
- **Modern Python practices** - Click + Rich + Pydantic for maintainability