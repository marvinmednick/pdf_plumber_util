# Output Files Reference

PDF Plumb writes every output file as `{basename}_{stage}.{ext}` into the
output directory (`-o`/`--output-dir`, default `output/`). `{basename}`
defaults to the input PDF's filename without extension, or the value passed
via `-b`/`--basename`.

This page is the canonical reference for what each command produces and what
each file contains. Command-specific quick lists (in the sections below) link
back here rather than duplicating the schema details.

## Pipeline overview

```
document.pdf
    │
    ▼  extract
{basename}_full_lines.json   (raw, unfiltered)
{basename}_lines.json        (blank lines removed, gaps re-derived) ──┐
{basename}_words.json                                                 │
{basename}_compare.json                                               │
{basename}_info.json                                                  │
{basename}_visualized.pdf    (if --visualize-spacing)                 │
                                                                       ▼  analyze
                                                        {basename}_blocks.json
                                                        {basename}_analysis.txt
                                                                       │
                                                                       ▼  llm-analyze
                                                        llm_{focus}_{timestamp}_results.json
                                                        llm_{focus}_{timestamp}_prompt.txt
                                                        llm_{focus}_{timestamp}_response.txt
```

`process` runs `extract` followed by `analyze` in one step, producing every
file in the first two stages.

## `extract` command

| File | Contents |
|---|---|
| `{basename}_full_lines.json` | **Raw, unfiltered** line data — every line pdfplumber found, including whitespace-only ("blank") lines. This is the ground-truth record of the page; nothing is removed or adjusted. |
| `{basename}_lines.json` | The same line data with blank lines removed and `gap_before`/`gap_after` re-derived from the nearest non-blank neighbours, so vertical spacing reflects real visual gaps rather than being split across a removed blank line. **This is the primary input to `analyze` and `llm-analyze`.** Lines carry an `original_line_number` pointing back to their position in `_full_lines.json`. |
| `{basename}_words.json` | Raw word-level data per page, before grouping into lines. Used for debugging extraction/alignment issues, not by downstream analysis. |
| `{basename}_compare.json` | Side-by-side comparison of PDF Plumb's three extraction methods (raw text, layout-aware text lines, word-based manual alignment) on the same page, for validating extraction accuracy. |
| `{basename}_info.json` | Metadata and extraction statistics: `{"metadata": {"total_pages", "total_lines", "total_words"}, "statistics": {"extraction_methods": {...}}}`. |
| `{basename}_visualized.pdf` | Only produced with `--visualize-spacing`. A copy of the source PDF with color-coded lines overlaid at each measured vertical gap, plus a legend page. Gaps are recomputed geometrically from non-blank line positions (not read from the JSON files), so this always reflects true visual spacing. |

### Line object schema (`_lines.json` / `_full_lines.json`)

Each file is a list of per-page objects:

```
{
  "page": 5,
  "page_width": 612.0,
  "page_height": 792.0,
  "lines": [
    {
      "line_number": 12,
      "text": "NOTE",                     # normalized (single spaces)
      "text_proportional": "NOTE",         # proportional spacing preserved
      "proportional_spacing_info": {...},
      "bbox": {"x0":..., "x1":..., "top":..., "bottom":...},
      "text_segments": [...],              # per-font/size runs within the line
      "predominant_size": 11.0,
      "predominant_font": "TimesNewRomanPS-BoldMT",
      "predominant_size_coverage": 100.0,  # % of line width at this size
      "predominant_font_coverage": 100.0,
      "gap_before": 66.9,
      "gap_after": 10.6,
      "original_line_number": 15           # _lines.json only, points into _full_lines.json
    }
  ]
}
```

## `analyze` command

Takes a `_lines.json` file (or in-memory data, when run as part of `process`)
and produces:

| File | Contents |
|---|---|
| `{basename}_blocks.json` | Lines grouped into blocks (paragraphs/headings) using contextual spacing rules derived per font size. Shape: `{"pages": [{"page": N, "blocks": [{"lines": [...], "text_lines": [...], "predominant_size", "gap_before", "gap_after", "bbox", ...}]}]}`. |
| `{basename}_analysis.txt` | Human-readable report: font/size distribution, spacing statistics, contextual spacing rules per size, header/footer boundary candidates. |

## `process` command

Runs `extract` then `analyze` against the in-memory result (no intermediate
file round-trip), so it produces every file listed above for both commands,
plus `{basename}_visualized.pdf` if `--visualize-spacing` is passed.

There is no separate `_spacing.pdf` or `_block_spacing.pdf` output — only
`_visualized.pdf` is produced by the current CLI.

## `llm-analyze` command

Requires Azure OpenAI configuration (see [CLI Usage Guide](cli-usage.md)).
Takes a `_lines.json` or `_blocks.json` file as input. Each run writes a
timestamped set of files named `llm_{focus}_{timestamp}_*`:

| File | Contents |
|---|---|
| `llm_{focus}_{timestamp}_results.json` | Structured analysis results: analysis type, sampling info, parsed results, token usage, model. |
| `llm_{focus}_{timestamp}_prompt.txt` | The exact prompt sent to the LLM, saved before the call (useful even if the call fails). |
| `llm_{focus}_{timestamp}_response.txt` | The raw LLM response text, saved before parsing. |

Pass `--no-save` to skip writing these files and only print results.

## Debug / internal outputs

These are produced by code paths not reachable from the standard
`extract` / `analyze` / `process` / `llm-analyze` commands, but may appear in
an output directory if you use the workflow orchestrator or legacy tooling
directly:

| File | Producer | Notes |
|---|---|---|
| `workflow_context_{timestamp}_{label}.json` | State machine orchestrator (`workflow/orchestrator.py`) | Debug snapshot of workflow context at a given state transition. Best-effort; a failure to save never fails the workflow. |
| `{basename}_visualization.txt`, `{basename}_visualization.json` | `SpacingVisualizer.generate_visualization` (`core/visualizer.py`) | Not called by the current Click CLI (`cli.py`); present in the code but currently unused by any command. |
| `{basename}_spacing.json`, `{basename}_headers_footers.json`, `{basename}_report.json` | `core/pipeline/stages.py` | Part of an older pipeline abstraction, only reachable via the legacy `pdf_plumb.py` entry point (`python plumb3.py` / `python -m pdf_plumb.pdf_plumb`), not the modern `pdf-plumb` CLI. |

## Debugging artifacts from `llm-analyze`

Multi-page or multi-objective LLM runs may also write `llm_input_debug_*.json`
and `llm_optimized_format_*.txt` files for inspecting exactly what data was
sent to the LLM — useful when troubleshooting unexpected analysis results.
