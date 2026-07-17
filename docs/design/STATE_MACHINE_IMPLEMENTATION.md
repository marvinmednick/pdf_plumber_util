# State Machine Implementation (As-Built)

## Overview

This document analyzes the **state machine as it is actually implemented today** in
`src/pdf_plumb/workflow/`. It is the as-built companion to
[STATE_MACHINE_ARCHITECTURE.md](STATE_MACHINE_ARCHITECTURE.md), which describes the *design* of
the framework (concepts, `execute`/`determine_next_state` contract, loop-prevention rules, and a
generic illustrative pipeline). Where the design doc says "here is how a state machine like this
should work," this doc says "here is what the code does right now, what is wired, what is
stubbed, and where the two docs have drifted from the code."

Read this when you need to know the *current* runtime behavior of `llm-analyze` — the live
execution path, what each real state sends to the LLM, and what is designed-but-not-yet-built.

**Source files covered:**

| File | Role |
|------|------|
| `workflow/state.py` | `AnalysisState` ABC + `StateTransition` dataclass |
| `workflow/registry.py` | Explicit `STATE_REGISTRY` and lookup/registration helpers |
| `workflow/state_map.py` | `WorkflowStateMap` — map generation, validation, path finding, export |
| `workflow/orchestrator.py` | `AnalysisOrchestrator` — the execution engine |
| `workflow/states/header_footer.py` | `HeaderFooterAnalysisState` (live) |
| `workflow/states/additional_section_headings.py` | `AdditionalSectionHeadingState` (live) |
| `workflow/states/example.py` | `ExampleState` / `Example2State` (test scaffolding) |

---

## The Live Execution Path (Today)

For `pdf-plumb llm-analyze <blocks.json> --focus headers-footers` (the default; **without**
`--use-direct-analyzer`), the CLI runs:

```
header_footer_analysis ──► additional_section_headings ──► END
        (LLM call #1)              (LLM call #2)
```

That is the **entire** workflow that runs in production. Two states, two LLM calls, then
terminate. Everything else in the framework (the example states, and the commented-out
refinement/section/TOC/table states) is **not** on this path.

Key wiring facts (from `cli.py:561-602`):

- The CLI passes **`initial_state='header_footer_analysis'` explicitly** rather than relying on
  the orchestrator's auto-detect. This matters — see [Entry-State Ambiguity](#entry-state-ambiguity-why-the-cli-passes-initial_state-explicitly).
- `--use-direct-analyzer` **bypasses the state machine entirely** and calls the legacy
  `LLMDocumentAnalyzer` directly. So the state machine is the default but not the only path.
- Reproducible sampling (`--sampling-seed`) is implemented with a **runtime registry swap**: the
  CLI dynamically subclasses `HeaderFooterAnalysisState` to bake in the seed, replaces the
  `STATE_REGISTRY` entry, runs the workflow, then restores the original. Functional but a code
  smell worth knowing about.
- The CLI reaches into `workflow_results['header_footer_analysis']['raw_result']` to recover the
  `HeaderFooterAnalysisResult` for display.

---

## Framework Components (As-Built)

### `AnalysisState` — the state contract (`state.py`)

Every state subclasses `AnalysisState` (ABC) and provides:

| Member | Kind | Purpose |
|--------|------|---------|
| `execute(context) -> dict` | abstract | Do the work (programmatic and/or LLM), return standardized result |
| `determine_next_state(result, context) -> Optional[str]` | abstract | Return next state name, or `None` to terminate |
| `POSSIBLE_TRANSITIONS: Dict[str, StateTransition]` | class attr | Declares allowed outgoing edges |
| `REQUIRED_FIELDS: list` | class attr | Context keys checked by `validate_input` |
| `validate_input(context)` | method | Raises if a required field is missing |
| `validate_transitions()` | classmethod | Rejects self-transitions at registration time |

`StateTransition` is a small dataclass: `target_state` (string or `None` for terminal),
`condition` (a human-readable label), and `description`.

The **execute result is a standardized dict** the orchestrator understands:

```python
{
  'analysis_type': str,          # label for this analysis
  'results': {...},              # findings
  'metadata': {...},             # provider, token usage, confidence, pages, ...
  'knowledge': {...},            # extracted patterns → merged into accumulated_knowledge
  # states may add extra keys (e.g. 'raw_result', 'pattern_scan_result')
}
```

Only `knowledge` is treated specially by the engine (see context flow below); everything else
is stored verbatim under `workflow_results[state_name]`.

### `registry.py` — explicit registration

There is **no magic name conversion**. `STATE_REGISTRY` is a hand-maintained dict:

```python
STATE_REGISTRY = {
    'example_1': ExampleState,
    'example_2': Example2State,
    'header_footer_analysis': HeaderFooterAnalysisState,
    'additional_section_headings': AdditionalSectionHeadingState,
    # TODO (commented out): header_footer_refinement, section_analysis,
    #                       toc_detection, table_figure_analysis
}
```

So **four** states are registered: two real analysis states and two example/test states. The
four future states named in the design doc exist only as commented-out imports and TODO entries
— no implementation files (`states/sections.py`, `states/toc.py`, `states/tables.py`) exist.

Helpers: `get_all_states`, `get_state_class`, `register_state` (validates subclass + no
self-transitions), `unregister_state`, `list_state_names`.

### `state_map.py` — introspection & validation

`WorkflowStateMap` builds a map from the registry and offers:

- `generate_state_map()` — `{state: {transitions, possible_next_states, is_terminal}}`
- `validate_state_map()` — checks reachability, flags fully-unreachable graphs, and requires at
  least one terminal path. **Currently returns no errors.**
- `get_entry_states()` — states with no incoming transitions
- `get_terminal_states()` — states that can reach `None`
- `find_workflow_paths()` — enumerates paths (with visited-set loop guarding)
- `print_state_map()` / `export_state_map(format=json|yaml|dot)` — the DOT export can be rendered
  with Graphviz for a visual workflow diagram

### `AnalysisOrchestrator` — the engine (`orchestrator.py`)

`run_workflow(document_data, initial_state=None, timeout_seconds=None, save_context=False,
output_dir=None)` drives execution:

1. **Timeout** defaults to config `workflow_timeout_seconds` (**1800s / 30 min**).
2. **Initial state** — if not given, auto-detects via `get_entry_states()[0]`; otherwise uses the
   caller's value (the CLI always supplies one). Validated against the registry.
3. **Context** is initialized (see below) and the main loop runs while
   `current_state_name and iteration_count < MAX_TOTAL_STATES` (**`MAX_TOTAL_STATES = 50`**, a
   module constant — the old `workflow_max_iterations` config was deliberately removed).
4. Each iteration (`_execute_state_iteration`): instantiate the state, record start metadata,
   `execute()`, store results, merge `knowledge` into `accumulated_knowledge`,
   `determine_next_state()`, **validate the transition** against `POSSIBLE_TRANSITIONS`, record
   end metadata, optionally snapshot.
5. **Termination** — normal when a state returns `None`; error if the loop hits
   `MAX_TOTAL_STATES` or the timeout. Both paths stamp `termination_reason` into metadata; the
   error path can also save an `error` snapshot.
6. `_finalize_workflow_results` returns `workflow_results`, `accumulated_knowledge`,
   `workflow_metadata`, and a computed `summary` (execution path, iteration count, duration,
   analysis types, states executed, knowledge item count).

### Context Flow

The context dict threaded through every state:

| Key | Content | Grows? |
|-----|---------|--------|
| `document_data` | Original blocks data (list of pages or `{pages: [...]}`) | No |
| `config` | Pydantic config instance | No |
| `workflow_results` | `{state_name: execute() result}` | +1 per state |
| `accumulated_knowledge` | Merge of every state's `knowledge` dict | Grows each state |
| `workflow_metadata` | Orchestrator version, state map, per-iteration timing, termination info | Grows each state |
| `output_dir` | Where snapshots/results go | No |

**Context snapshots** (`--save-context` / `save_context=True`) write
`workflow_context_<timestamp>_<label>.json` per iteration and on error.
`_make_context_serializable` strips the heavy/unserializable parts first — `config` becomes a
`model_dump()`, and `document_data` is reduced to a type+length stub rather than the full page
data. Snapshot failures are swallowed with a warning and never abort the workflow. (See
[docs/output-files.md](../output-files.md) for the `workflow_context_*.json` format.)

### Loop Prevention (as coded)

Three mechanisms, all present in code:

1. **Self-transition prohibition** — `validate_transitions()` rejects a state whose transition
   targets itself, enforced at registration.
2. **Transition whitelist** — the orchestrator rejects any `determine_next_state` return value
   not in that state's declared `POSSIBLE_TRANSITIONS`.
3. **Hard iteration cap** — `MAX_TOTAL_STATES = 50` bounds total iterations regardless of graph
   shape, plus the wall-clock timeout.

---

## The Live States (As-Built)

### 1. `HeaderFooterAnalysisState` → registered as `header_footer_analysis`

**Name vs. reality:** despite the class name, this is now a **comprehensive pattern-analysis
entry state**, not a narrow header/footer detector. Its docstring describes a three-phase design:

- **Phase 1 — Programmatic pattern detection:** `DocumentScanner` (+ `PatternSetManager`) scans
  the full document for section/TOC/figure/table patterns. **Partially built:**
  `_perform_programmatic_analysis` runs the scan but still carries `TODO`s for font-consistency
  analysis "across 7 parameter combinations" and section-completeness/TOC cross-reference.
- **Phase 2 — LLM comprehensive analysis:** intended to be a single pattern-aware LLM call. **As
  built it falls back to the existing `LLMDocumentAnalyzer.analyze_headers_footers`** — the code
  comment says *"For now, fall back to existing LLM analysis — will be enhanced with pattern
  data."* So the pattern scan results are **not yet fed into the LLM prompt**.
- **Phase 3 — Knowledge integration:** `_integrate_pattern_and_llm_results` is a **stub** —
  it returns `{'pattern_validation': 'pending_llm_enhancement', 'cross_validation':
  'pending_implementation', 'unified_hypothesis': 'pending_implementation'}`.

What *does* work end-to-end: the programmatic scan runs, the legacy LLM header/footer analysis
runs, results/metadata/knowledge are assembled (including `pattern_scan_result` and a
`_calculate_pattern_confidence` heuristic), and `estimate_cost()` is available.

**Transitions:** declares `additional_sections → additional_section_headings` and `complete →
None`. **But `determine_next_state` unconditionally returns `'additional_section_headings'`**
(comment: *"For now, always proceed"*). The `complete`/terminate branch is declared but never
taken — the conditional routing the design envisions is not yet exercised.

Result `analysis_type`: `'comprehensive_pattern_analysis'`.

### 2. `AdditionalSectionHeadingState` → registered as `additional_section_headings`

The **terminal** state on the live path. It analyzes pages the earlier state did **not** sample:

- `_get_unused_pages` computes all pages minus pages recorded in prior states'
  `sampling_summary` (checking both `page_indexes_analyzed` and `selected_page_indexes` for
  compatibility).
- If there are no unused pages, it returns empty results and terminates.
- Otherwise it samples up to `max_additional_pages` (**default 10**) unused pages (random,
  seedable), streamlines them, builds a specialized prompt via
  `PromptTemplates.additional_section_heading_analysis`, calls the provider **directly**, parses
  the response with the header/footer parser (the LLM returns that format), tracks token usage,
  and optionally saves prompt/response/structured results
  (`llm_additional_sections_<timestamp>_*`).
- Looks for new section/figure/table headings, new font styles, and validates header/footer
  consistency against `previous_patterns` pulled from the earlier state.

**Transitions:** both declared transitions (`complete`, `next_analysis`) target `None`, and
`determine_next_state` **always returns `None`** → the workflow always ends here.

Result `analysis_type`: `'additional_section_heading_analysis'`.

### 3. `ExampleState` / `Example2State` → `example_1` / `example_2`

Test scaffolding: `example_1 → example_2 → END`. Registered so state-map validation, path
finding, and orchestrator tests have a trivial multi-state graph to exercise. Not part of any
real analysis.

---

## Drift Between the Design Doc and the Code

Things a reader of [STATE_MACHINE_ARCHITECTURE.md](STATE_MACHINE_ARCHITECTURE.md) should know
are out of step with the implementation:

1. **"Implementation Strategy" phases are largely done, not future.** The design doc frames core
   infrastructure and state migration as upcoming Phases 1–2. In reality the orchestrator, base
   class, registry, state map, and two production states are built and shipping as the default
   `llm-analyze` path.

2. **`HeaderFooterAnalysisState` is misnamed for what it does.** It is the comprehensive
   pattern-analysis entry point, and its Phase 2/3 pattern→LLM integration is stubbed. Neither
   the class name nor the design doc reflects that the pattern scan currently runs *alongside*
   (not *inside*) the legacy LLM call.

3. **Conditional routing is designed but not exercised.** Both live states have
   `determine_next_state` methods that return a **constant** (always proceed / always end). The
   branching-on-confidence flow the design describes has no live example yet.

4. **Four "next" states are vaporware in the registry.** `section_analysis`, `toc_detection`,
   `table_figure_analysis`, and `header_footer_refinement` appear only as commented TODOs. TOC
   and section/table analysis currently happen *inside* the two existing states, not as separate
   states.

5. <a id="entry-state-ambiguity-why-the-cli-passes-initial_state-explicitly"></a>**Entry-state
   ambiguity.** Because the example states are registered, `get_entry_states()` returns
   **`['example_1', 'header_footer_analysis']`** — two entry points. The orchestrator's
   auto-detect would pick `entry_states[0]`, which is order-dependent and could select
   `example_1`. This is precisely why the CLI passes `initial_state='header_footer_analysis'`
   explicitly. Auto-detect is effectively unused in production and would be unsafe to rely on
   while example states share the registry.

---

## What Works vs. What's Stubbed — Quick Status

| Piece | Status |
|-------|--------|
| Orchestrator loop, timeout, iteration cap | ✅ Working |
| Transition validation + self-transition guard | ✅ Working |
| State map generation / validation / export (json/yaml/dot) | ✅ Working |
| Context threading + `knowledge` accumulation | ✅ Working |
| Context snapshots (`--save-context`) | ✅ Working |
| `header_footer_analysis` programmatic scan | ⚠️ Runs, but font-consistency & section-completeness are TODO |
| `header_footer_analysis` LLM call | ✅ Works via legacy analyzer (not yet pattern-aware) |
| `header_footer_analysis` Phase 3 integration | ❌ Stub (`pending_*` placeholders) |
| `additional_section_headings` | ✅ Working (unused-page analysis, terminal) |
| Conditional/confidence-based routing | ❌ Not exercised (constant next-state) |
| `section` / `toc` / `table` / `refinement` states | ❌ Not implemented (commented TODOs) |
| Auto initial-state detection | ⚠️ Present but ambiguous; CLI bypasses it |

---

## Cross-References

- Framework design & rationale: [STATE_MACHINE_ARCHITECTURE.md](STATE_MACHINE_ARCHITECTURE.md)
- Deterministic analysis that produces the blocks these states consume:
  [STATISTICAL_ANALYSIS_PIPELINE.md](STATISTICAL_ANALYSIS_PIPELINE.md)
- LLM stage internals: [LLM_INTEGRATION.md](LLM_INTEGRATION.md), [LLM_STRATEGY.md](LLM_STRATEGY.md)
- Pattern detection the header/footer state's Phase 1 relies on:
  [PATTERN_DETECTION_ARCHITECTURE.md](PATTERN_DETECTION_ARCHITECTURE.md)
- Snapshot/output file formats: [docs/output-files.md](../output-files.md)
- System overview: [docs/architecture.md](../architecture.md)
</content>
