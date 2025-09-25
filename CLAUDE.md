# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Context

PDF Plumb is a Python PDF text extraction and analysis tool for technical documents. Uses multiple extraction methods to identify document structure, fonts, spacing patterns, and generates visualizations.

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
uv run pytest -m golden                   # Golden document tests (requires API credentials)
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
├── golden/              # Golden document tests with real LLM API calls
├── fixtures/            # Test fixtures and prepared document data
└── conftest.py          # Shared test fixtures
```

**Key Files to Read First**:
- `src/pdf_plumb/cli.py` - Click CLI with Rich console integration + LLM commands
- `src/pdf_plumb/config.py` - Pydantic configuration and profiles + Azure OpenAI settings
- `src/pdf_plumb/core/extractor.py` - Three extraction methods implementation
- `src/pdf_plumb/core/llm_analyzer.py` - LLM-enhanced analysis coordinator
- `src/pdf_plumb/llm/providers.py` - Azure OpenAI integration
- `docs/cli-usage.md` - Complete user command reference

## Development Patterns

### Session Startup Guidance (For Claude Code Context)

When starting a new development session, Claude Code should review these documents in order to understand both immediate work state and codebase architecture:

**Immediate Work Context:**
1. **WORK_LOG.md** - Current work in progress and immediate next steps
2. **docs/status.md** - Overall project status and recent completed work
3. **Recent git commits** - `git log --oneline -5` to understand latest changes

**Codebase Architecture Context:**
4. **docs/architecture.md** - System overview, data flow, and component relationships
5. **docs/design-decisions.md** - Critical architectural choices and rationale for consistency

**Core Code Context:**
6. **Key implementation files** - Review as needed based on work area:
   - `src/pdf_plumb/cli.py` - Entry points and command structure
   - `src/pdf_plumb/config.py` - Configuration and profiles system
   - `src/pdf_plumb/core/extractor.py` - Core PDF processing logic
   - `src/pdf_plumb/core/analyzer.py` - Document analysis algorithms

This ensures Claude Code understands immediate work context, architectural patterns to maintain, and implementation details for informed code decisions.

### Work Log Protocol (MANDATORY - IMMEDIATE EXECUTION REQUIRED)

**CRITICAL REQUIREMENT**: After completing ANY of the following work types, you MUST IMMEDIATELY append to WORK_LOG.md using Bash. This is not optional:
- **Code implementation**: Functions, classes, configuration changes, testing infrastructure
- **Design documentation**: Architecture docs, design decisions, methodology creation/updates
- **Analysis work**: Significant research, problem-solving, architectural planning
- **File creation/modification**: Any substantial document or code file changes

**AUTOMATIC EXECUTION RULE**: Do not ask the user or wait for permission. Execute the work log update immediately after completing work. If user calls `/update-worklog` command, this indicates automatic updates may have been missed - review recent work for compliance gaps.

**During development - IMMEDIATE ACTION:**
```bash
echo "---
### $(date '+%Y-%m-%d %H:%M') - [Task description]
- **Completed**: [Achievements with file references]
- **Tests**: [Results and counts]
- **Next**: [Next steps or issues]" >> WORK_LOG.md
```

**MANDATORY DOCUMENTATION SCOPE**: Document ALL significant work including:
- **Implementation work**: File creation/modification with line counts for substantial changes
- **Code changes**: New functions, classes, or significant logic changes
- **Configuration work**: Updates and registry modifications
- **Testing work**: Test infrastructure creation or updates
- **Design work**: Architecture documentation creation/updates (including design docs)
- **Analysis work**: Significant research, problem-solving, or design decisions

**Immediate Status Updates** (don't wait for commit):
- **Phase changes**: Implementation ↔ Design, or major scope changes
- **Major design completion**: Architecture documents, design methodology completion
- **Significant capability additions**: New features, major analysis capabilities
- **Active work scope changes**: What you're working on has fundamentally changed

**Status.md Archival Management**:
- **Size Monitoring**: Check docs/status.md line count during updates
- **Archival Trigger**: When approaching 200 lines, archive older entries
- **Archive Process**: Move oldest "Last Completed Work" entries to docs/phase-history.md
- **Maintain Balance**: Keep recent work visible, preserve historical record

**Before each commit:**
1. Review WORK_LOG.md entries
2. Consolidate into docs/status.md "Last Completed Work" section
3. Archive older status entries to phase-history.md if approaching 200 lines
4. Update docs/status.md current phase/active work if not already current
5. Clear WORK_LOG.md entries and create empty file for next session:
   ```bash
   echo "# Work Log

This file tracks development progress during active work sessions. It gets cleared after each commit.

---" > WORK_LOG.md
   ```

### Custom Update Commands with Self-Auditing

#### **/update-worklog Command**
**Purpose**: Manual backup for missed automatic WORK_LOG.md updates
**Self-Auditing Behavior**:
1. Execute work log update with recent completed work
2. **Self-Reminder**: "Manual `/update-worklog` call indicates automatic WORK_LOG updates may have been missed. Per protocol, work log updates should happen IMMEDIATELY after completing any significant work."
3. **Compliance Review**: Analyze recent conversation exchanges to identify work that should have triggered automatic updates
4. **Self-Correction**: Acknowledge any missed automatic updates and commit to better compliance

#### **/update-status Command**
**Purpose**: Immediate docs/status.md updates for phase changes or major milestones
**Self-Auditing Behavior**:
1. Execute status.md updates (Active Work, Current State, or Last Completed Work as appropriate)
2. **Self-Reminder**: "Manual `/update-status` call indicates automatic status updates may have been missed. Per protocol, status.md should be updated immediately for phase changes and major design completions."
3. **Compliance Review**: Analyze recent work to identify phase changes, design completions, or capability additions that warranted status updates
4. **Self-Correction**: Acknowledge any missed automatic status updates and improve future compliance

**Command Integration**: Both commands serve as **compliance auditing tools** that help Claude identify and correct gaps in automatic update adherence while executing the needed updates.

### Architecture Documentation Standards
- **Track documentation changes in git commits**: Architecture and feature documentation history should be maintained through git commit messages
- **Review revisions for completeness**: When updating major documents like docs/architecture.md, ensure changes are properly documented in commit messages for future reference

### Adding New CLI Commands
1. Add command function to `src/pdf_plumb/cli.py` using Click decorators
2. Use common decorators: `@common_options`, `@visualization_options`
3. Implement Rich console output: `console.print(f"✅ Success message")`
4. Add integration tests in `tests/integration/test_cli_commands.py`
5. Update docs/cli-usage.md with examples

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
- **Golden tests** (`tests/golden/`): Real LLM API calls for regression testing and validation (fail if no API credentials)
- **Real PDF testing**: Validated CLI migration with actual H.264 spec document
- **Markers**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.golden`

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
- README.md, docs/status.md, docs/cli-usage.md, docs/architecture.md, CLAUDE.md, WORK_LOG.md

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

## Project Status References

**For current project status**: See [docs/status.md](docs/status.md) - current phase, active work, recent completions
**For development history**: See [docs/phase-history.md](docs/phase-history.md) - detailed phase achievements and evolution

## Documentation Navigation for Development

This project uses a hierarchical documentation structure designed to preserve design decisions while providing clear user guidance. When working on features or making architectural decisions, use this guide to find relevant context.

### Documentation Hierarchy

**Tier 1: User Entry Points**
- `README.md` - Project overview, quick start, features list
- `docs/cli-usage.md` - Complete command reference with examples and environment variables
- `INSTALLATION.md` - Setup and configuration (to be created if needed)

**Tier 2: Architecture & Design Context**
- `docs/architecture.md` - System design, component relationships, data flow
- `docs/design-decisions.md` - **KEY FOR DEVELOPMENT** - Architectural choices and rationale
- `docs/phase-history.md` - Detailed development phase history and achievements

**Tier 3: Implementation Deep-Dives**
- `docs/design/TEXT_PROCESSING_AND_BLOCK_GROUPING.md` - Text segment spacing reconstruction and block formation algorithms
- `docs/design/HEADER_FOOTER_DETECTION.md` - Iterative boundary detection development
- `docs/design/STATE_MACHINE_ARCHITECTURE.md` - State machine orchestrator for multi-objective analysis workflows
- `docs/design/LLM_INTEGRATION.md` - LLM implementation guide and current usage
- `docs/design/LLM_STRATEGY.md` - Complete LLM strategic framework and advanced features
- `docs/design/CONTEXTUAL_SPACING.md` - Core spacing analysis algorithm (to be created)
- `docs/design/PATTERN_DETECTION_ARCHITECTURE.md` - Comprehensive Phase 1 pattern detection methodology

**Tier 4: Analysis & Strategy**
- `docs/analysis/token_analysis.md` - LLM token counting analysis and batch sizing
- `docs/analysis/performance_optimization.md` - Performance analysis and decisions (to be created)
- `docs/analysis/llm_strategy_evolution.md` - How LLM approach evolved (to be created)

### When to Reference Which Documents

**Before making architectural changes:**
1. Check `docs/design-decisions.md` for existing rationale
2. Review relevant `docs/design/*.md` for implementation details
3. Check `docs/analysis/*.md` for supporting data

**When implementing new features:**
1. Start with `docs/architecture.md` for system overview
2. Review related design docs for patterns to follow
3. Update `docs/design-decisions.md` with new choices

**When adding LLM capabilities:**
1. `docs/design/STATE_MACHINE_ARCHITECTURE.md` - State machine framework for multi-objective workflows
2. `docs/design/LLM_INTEGRATION.md` - Current implementation and usage
3. `docs/design/LLM_STRATEGY.md` - Complete strategic framework and advanced features
4. `docs/analysis/token_analysis.md` - Batch sizing and cost analysis
5. `docs/analysis/llm_strategy_evolution.md` - How the approach evolved

**When optimizing performance:**
1. `docs/analysis/token_analysis.md` - Token optimization and LLM performance analysis
2. `docs/phase-history.md#phase-23` - Phase 2.3 performance optimization details
3. Relevant design docs for implementation details

**When reviewing project evolution:**
1. `docs/phase-history.md` - Complete development phase history and achievements
2. `docs/design-decisions.md` - Current architectural rationale
3. `docs/status.md` - Current phase summary with references

### Documentation Update Protocol

**When adding features:**
- Update user docs (`README.md`, `docs/cli-usage.md`) first
- Document design decisions in `docs/design-decisions.md`
- Create/update relevant design docs
- Cross-reference between levels

**When changing architecture:**
- Update `docs/architecture.md` with new design
- Document rationale in `docs/design-decisions.md` 
- Determine if need to create/update design docs
- Add entry to `docs/phase-history.md`

### Documentation Guidelines

**CLAUDE.md Guidelines:**
- **Development guidance only** - Commands, architecture patterns, coding standards, workflows
- **NO project status** - No current phases, recent work, active tasks, or project state (use docs/status.md)
- **NO historical information** - No completed work, achievements, or phase details (use docs/phase-history.md)
- **NO specific metrics** - No test counts, performance numbers, or changing statistics
- **Architecture and patterns** - Focus on current system design patterns to follow
- **Reference other docs** - Point to appropriate documentation for detailed information
- **Keep concise** - Avoid duplicating information available in specialized documents

**docs/status.md Guidelines:**
- Focus on current development phase and immediate next steps
- Keep to ~200 lines maximum with automatic archival management
- Archive older "Last Completed Work" entries to docs/phase-history.md when approaching limit
- Avoid detailed technical explanations (use design docs for that)
- Update when phases change, not for minor feature additions

**README.md Guidelines:**
- Brief project overview and key features (including LLM analysis)
- Quick start instructions
- Link to detailed documentation
- Keep under 100 lines for accessibility
- **NO test counts or metrics** - These change frequently and create maintenance burden

**docs/cli-usage.md Guidelines:**
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
See: [docs/design/TEXT_PROCESSING_AND_BLOCK_GROUPING.md](docs/design/TEXT_PROCESSING_AND_BLOCK_GROUPING.md)
Design rationale: [docs/design-decisions.md#spacing-analysis](docs/design-decisions.md)
Performance analysis: [docs/analysis/performance_optimization.md](docs/analysis/performance_optimization.md)
```

## Template-Specific Notes

This project structure supports PDF analysis development by:
- **Iterative validation approach** - Implement multiple methods, compare, choose best
- **Rich console experience** - Professional CLI with progress bars and emojis
- **Document type profiles** - Pre-configured settings for different PDF types  
- **Comprehensive testing** - Real PDF validation ensures reliability
- **Modern Python practices** - Click + Rich + Pydantic for maintainability