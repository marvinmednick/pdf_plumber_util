# Statistical Analysis Pipeline (Pre-LLM)

## Overview

This document describes the **deterministic, statistics-driven analysis** that PDF Plumb
performs *before* any LLM is involved. It covers the flow inside
`src/pdf_plumb/core/analyzer.py` — how enriched lines are turned into font/size/spacing
statistics, how gaps are grouped and classified, how lines are grouped into blocks, and how
header/footer boundaries are estimated.

The goal of this stage is to convert raw geometry (word boxes, font metadata) into a compact
set of **document-level characteristics and structured blocks** that either:

1. Answer structural questions directly (body font, body size, line spacing, header/footer
   boundaries), or
2. Serve as the pre-digested input the LLM stage reasons over (`*_blocks.json`), so the LLM
   never has to re-derive geometry.

**Pipeline position:**

```
extract  ──►  {basename}_lines.json      (enriched, blank-filtered lines)
                     │
                     ▼
analyze  ──►  DocumentAnalyzer.analyze_document_data()
                     │
                     ├──► analysis results  ──►  {basename}_analysis.txt / .json
                     └──► block analysis     ──►  {basename}_blocks.json
                                                        │
                                                        ▼
                                          llm-analyze (Azure OpenAI)
```

For the file formats themselves see
[docs/output-files.md](../output-files.md). For the segment-reconstruction and block-formation
internals see
[TEXT_PROCESSING_AND_BLOCK_GROUPING.md](TEXT_PROCESSING_AND_BLOCK_GROUPING.md). This document
focuses on the **statistics and decision criteria** that tie them together.

---

## Input Contract: The Enriched Line

All analysis operates on the enriched line objects produced by the extractor
(`_process_words` in `extractor.py`). Each line already carries the geometry and typographic
metadata the analyzer needs; the analyzer computes **no** new per-line geometry, only
aggregates and classifications.

| Field | Meaning | Produced by |
|-------|---------|-------------|
| `bbox` = {`x0`,`top`,`x1`,`bottom`} | Line bounding box, points, origin top-left | `_calculate_line_bbox` |
| `text_segments[]` | Runs of constant font+size+orientation, each with `font`, `rounded_size`, `bbox` | `_create_text_segments` |
| `predominant_size` | Font size covering the most horizontal width on the line | `_process_words` (width-weighted) |
| `predominant_font` | Font covering the most horizontal width on the line | `_process_words` (width-weighted) |
| `predominant_size_coverage` / `predominant_font_coverage` | % of line width using the predominant size/font | `_process_words` |
| `gap_before` | Vertical gap to the previous non-blank line (`this.top − prev.bottom`) | `_process_words`, corrected by `_process_blank_lines` |
| `gap_after` | Vertical gap to the next non-blank line (or to page bottom for the last line) | `_process_words`, corrected by `_process_blank_lines` |

Two subtleties that the statistics depend on:

- **Predominant size/font is width-weighted, not count-weighted.** A line with one large word
  and three tiny footnote markers is classified by whichever *font size occupies the most
  horizontal space*, matching how a reader perceives the line. See `_process_words`
  (`size_widths` / `font_widths` accumulation).
- **Gaps are geometric ground truth.** `gap_before`/`gap_after` are true visual whitespace
  between ink, because blank (whitespace-only) lines have been folded into the surrounding
  gaps by `_process_blank_lines` before the analyzer ever sees the data. This is why the
  analyzer can trust gaps without re-deriving them. (This blank-line folding was a correctness
  fix — see [docs/output-files.md](../output-files.md) and the extractor's `_process_blank_lines`.)

---

## Top-Level Flow: `analyze_document_data`

`DocumentAnalyzer.analyze_document_data(data, base_name)` (analyzer.py:1342) orchestrates the
whole pre-LLM stage in a fixed sequence:

```
Pass 1  Basic stats            → font_counts, size_counts, page_details, page height
Detailed analysis:
  A  Line spacing              _analyze_line_spacing
  B  Paragraph spacing         _analyze_paragraph_spacing
  C  Contextual distribution   _analyze_spacing_distribution
        ├ _collect_contextual_gaps
        └ _analyze_contextual_spacing
  D  Block formation           _analyze_blocks           → {basename}_blocks.json
  E  Header/footer (traditional)   _identify_header_footer_candidates
  F  Header/footer (contextual)    _identify_header_footer_contextual
Final   Boundary selection     _determine_final_boundaries
```

The result is a single flat `analysis_results` dict (keys documented per-section below) plus a
side-effect write of `{basename}_blocks.json`.

---

## Pass 1 — Basic Font & Size Statistics

Source: `analyze_document_data` first loop (analyzer.py:1369) + `_create_analysis_results`.

For every **valid** line (non-empty text, valid bbox where `bottom > top`), each text segment
contributes its `rounded_size` (rounded again to `round_to_nearest_pt`, default **0.5pt**) and
its `font` to two flat lists. These become `Counter`s:

- `font_counts` → `most_common_font` → reported as **"Likely body text font"**
- `size_counts` → `most_common_size` → reported as **"Likely body text size"**

**Decision criterion:** the single most frequent value wins. The assumption is that in a
technical document body text vastly outnumbers headings, captions, and footnotes, so the mode
*is* the body style. Counting is **per-segment**, so a line contributes multiple votes when it
mixes fonts/sizes.

The pass also tracks `max_page_bottom` (the largest observed line bottom across all pages),
used as the fallback page height for footer math.

---

## A — Line Spacing Statistics (`_analyze_line_spacing`)

Source: analyzer.py:331.

Collects every positive `gap_before` across all pages, rounds each to `round_to_nearest_pt`
(0.5pt), and builds a `Counter`.

- **`most_common_spacing`** = the most frequent *non-zero* gap → reported as **"Likely
  standard line spacing (within paragraphs)"**. The mode is used rather than the mean because
  line spacing in a fixed-layout PDF is discrete and highly repetitive; the mean would be
  dragged upward by paragraph and section gaps.
- **`potential_para_gaps`** = gaps in the window
  `(mode × 1.3, mode × large_gap_multiplier × 1.5)` — i.e. clearly larger than a line gap but
  not yet a full section break. The largest-count entry is reported as **"Likely paragraph
  spacing"**.

  - `para_gap_multiplier` = **1.3** (hard-coded floor: a paragraph gap must exceed 1.3× the
    line gap to be distinguishable from line-spacing jitter).
  - `large_gap_multiplier` = **1.8** (profile default) sets the upper cutoff so page-break-scale
    gaps don't masquerade as paragraph spacing.

---

## B — Paragraph & Section Spacing (`_analyze_paragraph_spacing`)

Source: analyzer.py:384.

Walks consecutive line pairs and classifies each `gap_before` using the **contextual**
classifier (Section C). Gaps classified `Paragraph` and `Section` are collected separately,
yielding counts and averages:

- `paragraph_spacings` / `section_spacings` (frequency dicts)
- `avg_paragraph_spacing`, `avg_section_spacing`

> **Implementation note:** this method recomputes the contextual spacing rules *per line*
> (`_analyze_contextual_spacing(_collect_contextual_gaps(lines))` inside the loop). It is
> correct but redundant with Section C, and is a known efficiency target. It does not change
> results, only cost.

---

## C — Contextual Spacing Rules (the core of the pipeline)

This is where "how decisions are made and by what criteria" is most important. The insight:
**a gap only means something relative to the font size around it.** 6pt of whitespace is a
tight line gap for a 24pt heading but a paragraph break for 8pt footnotes. So spacing rules are
derived **per predominant font size** ("context size").

### C.1 Collect gaps by context — `_collect_contextual_gaps` (analyzer.py:68)

1. Count total lines per `predominant_size` (`total_lines_by_context`).
2. Walk consecutive line pairs. **Record `gap_before` only when the current and previous line
   share the same `predominant_size`** and it is non-null.
3. Keep gaps `> 0.01pt`, rounded to `gap_rounding` (**0.5pt**).

Output: `{ context_size: {gaps: [...], total_lines: N} }`.

> **The same-size-adjacency gate is significant.** A gap is sampled only when a line of size S
> is immediately preceded by another line of size S. This makes body-text spacing rules very
> robust (body lines follow body lines constantly) but **starves sparse styles** — headings are
> almost always preceded by body text, so most heading occurrences contribute *zero* samples to
> their own size's rules. This is the root cause of the deferred "sparse contextual-spacing
> class" issue tracked in [docs/status.md](../status.md).

### C.2 Derive rules — `_analyze_contextual_spacing` (analyzer.py:122)

For each context size with at least one sampled gap:

| Rule | Formula | Default constant | Meaning |
|------|---------|------------------|---------|
| `most_common_gap` | `Counter(gaps).most_common(1)` | — | The modal gap = this size's baseline line spacing |
| `line_spacing_range` | `(mode × (1−t), mode × (1+t))` | `t = line_spacing_tolerance = 0.20` | Gaps within ±20% of the mode count as *line* spacing |
| `para_spacing_max` | `context_size × m` | `m = para_spacing_multiplier = 1.1` | Upper bound for *paragraph* spacing, tied to the font size itself |

Every observed gap is then bucketed:

- `line_gaps`: `gap ≤ line_spacing_range[1]`
- `para_gaps`: `line_spacing_range[1] < gap ≤ para_spacing_max`
- `section_gaps`: `gap > para_spacing_max`

Plus bookkeeping: `gap_distribution` (full histogram), `total_gaps`, `total_lines`.

**Why two different bases?** Line spacing is anchored to the *observed modal gap* (empirical),
while the paragraph ceiling is anchored to the *font size* (typographic). This lets the line
range adapt to a document's actual leading while keeping the paragraph boundary predictable
even for sizes with few samples.

### C.3 Classify a single gap — `_classify_gap_contextual` (analyzer.py:212)

Given a gap and a context size:

1. If the size has no rules, **fall back to the size with the most `total_gaps`** (effectively
   body text). If nothing is available, default to `Line`.
2. Round the gap to `gap_rounding` and apply thresholds:
   - `gap ≤ line_spacing_range[1]` → **Line**
   - `gap ≤ para_spacing_max` → **Paragraph**
   - otherwise → **Section**

The five classification labels live in `SPACING_TYPES` (`Tight`/`Line`/`Paragraph`/
`Section`/`Wide`); the classifier emits `Line`/`Paragraph`/`Section`, and the header/footer
logic additionally treats `Section`/`Wide` as boundary signals.

`_analyze_spacing_distribution` (analyzer.py:435) simply runs C.1 → C.2 over **all** lines and
packages `contextual_gaps`, `spacing_rules`, and `distribution_by_size` into the results.

---

## D — Block Formation (`_analyze_blocks`)

Source: analyzer.py:693. Full treatment in
[TEXT_PROCESSING_AND_BLOCK_GROUPING.md](TEXT_PROCESSING_AND_BLOCK_GROUPING.md); summarized here
for pipeline context.

Consecutive lines are merged into one block when **both**:

1. Same `predominant_size` as the current block, and
2. `gap_before ≤ line_spacing_range[1]` for that size (i.e. the gap classifies as *line*
   spacing, not paragraph/section).

Any other condition starts a new block. Blank/invalid lines are skipped. After a page's blocks
are formed, **inter-block gaps are recomputed from block bounding boxes**
(`next.bbox.top − this.bbox.bottom`, analyzer.py:804) so `gap_before`/`gap_after` on a block
reflect true block-to-block whitespace rather than the first line's gap.

`_calculate_block_metadata` (analyzer.py:821) computes each block's `size_coverage`,
`predominant_font`, and `font_coverage` by counting text segments (not widths) — the
predominant size/font is whichever appears in the most segments across the block's lines. The result is written
to `{basename}_blocks.json` — the primary structured hand-off to the LLM stage.

**Criterion summary — do two lines merge?**

| Predominant sizes | Gap vs line-spacing range | Merge? |
|-------------------|---------------------------|--------|
| equal | `gap ≤ range_max` | **Yes** |
| equal | `gap > range_max` | No (new block) |
| different | any | No (new block) |

---

## E & F — Header/Footer Boundary Detection

Two independent methods run, and both are reported so they can be compared.

### E — Traditional (`_identify_header_footer_candidates`, analyzer.py:474)

- **Zones:** a line is a header candidate only if `bbox.top < header_zone_inches × 72`
  (default top **1.25"**); a footer candidate only if `bbox.bottom > page_height −
  footer_zone_inches × 72` (default bottom **1.0"**).
- **Signal:** within the zone, the gap separating the candidate from the body must be *large*:
  `gap ≥ large_gap_multiplier × base_spacing`, where `base_spacing` is the page's most common
  non-zero gap (`_get_base_spacing`) and `large_gap_multiplier` defaults to **1.8**.
- Each qualifying line contributes its boundary `y` coordinate; `Counter(y_coords)` finds the
  `y` that recurs on the most pages.

### F — Contextual (`_identify_header_footer_contextual`, analyzer.py:583)

Same zones, but the "is this a boundary" test uses the **contextual classifier** (Section C)
instead of a fixed multiple: a candidate qualifies when its gap classifies as `Section` or
`Wide` for its font size. This adapts the threshold to heading-sized text automatically.

### Final selection (`_determine_final_boundaries`, analyzer.py:1303)

For each of the four candidate sets (traditional/contextual × header/footer), the boundary is
the **most common candidate `y` across pages** (`Counter.most_common(1)`), because a genuine
running header/footer sits at the *same* coordinate on every page. Defaults when no candidates
exist: header bottom `= 0.0`, footer top `= page_height`.

The console/report (`print_analysis`, analyzer.py:883) shows both methods side by side with
supporting per-coordinate page counts, so a human (or reviewer) can see the evidence, not just
the conclusion.

---

## Decision Criteria & Thresholds — Quick Reference

All defaults come from `config.py` (profile overrides in parentheses where they differ).

| Constant | Default | Where used | Effect |
|----------|---------|------------|--------|
| `y_tolerance` | 3.0pt (technical 2.5 / academic 4.0 / dense 2.0) | word→line grouping (`_process_words`) | Max vertical delta for words to share a line — sets which words become one analyzed line |
| `x_tolerance` | 3.0pt (varies by profile) | word combining (`_combine_words`, extractor.py:148) | Max horizontal gap to merge adjacent words; feeds the `content` line representation only, not the segment/`predominant_size` path |
| `round_to_nearest_pt` | 0.5pt | font size & line-spacing histograms | Quantizes sizes/spacings so near-identical values coalesce |
| `gap_rounding` | 0.5pt | contextual gap collection & classification | Quantizes gaps before bucketing |
| `line_spacing_tolerance` | 0.20 (dense 0.15) | `line_spacing_range` | ±20% band around modal gap counts as *line* spacing |
| `para_spacing_multiplier` | 1.1 (dense 1.05) | `para_spacing_max` | Paragraph ceiling = 1.1 × font size |
| `large_gap_multiplier` | 1.8 (technical 1.6 / academic 2.0 / dense 1.5) | traditional header/footer, para-gap window | Gap must exceed 1.8 × body spacing to be "large" |
| `para_gap_multiplier` | 1.3 (hard-coded) | `_analyze_line_spacing` | Floor for distinguishing paragraph from line gaps |
| `header_zone_inches` | 1.25 (varies by profile) | header candidate zone | Search band from top of page |
| `footer_zone_inches` | 1.0 (varies by profile) | footer candidate zone | Search band from bottom of page |
| `points_per_inch` | 72.0 | zone math | pt ↔ inch conversion |
| `default_page_height` | 792 (11") | footer math fallback | Used when a page has no height |

Profiles (`--profile technical|academic|manual|dense`) shift several of these together; see
`config.py` `PROFILES` and [docs/cli-usage.md](../cli-usage.md).

---

## What the LLM Stage Receives

The LLM stage (`llm_analyzer.py`) does **not** re-run any of the above. It consumes the
pre-digested products:

- **`{basename}_blocks.json`** — the primary structured input: page-ordered blocks with text,
  predominant font/size + coverage, and true inter-block gaps.
- The document-level conclusions (body font/size, line/paragraph spacing, header/footer
  boundaries) provide the statistical context the LLM reasons against (e.g. "a heading is text
  larger than the 10pt body with a Section-scale gap before it").

Because all geometry is resolved deterministically first, the LLM's job is **semantic**
(what is this block — heading, TOC entry, caption?) rather than **geometric**, which keeps
token usage down and results reproducible.

---

## Known Limitations & Deferred Work

1. **Sparse contextual-spacing classes (deferred, tracked in
   [docs/status.md](../status.md)).** The same-size-adjacency gate in `_collect_contextual_gaps`
   discards most heading/caption occurrences (they are preceded by body text), so rare styles
   get few or zero gap samples and fall back to body-text rules. Revised fix direction: pool
   `gap_before` across *all* lines of a font+size class regardless of the predecessor's size,
   and add `font` to the grouping key so, e.g., "12pt Bold Times" headings are analyzed as one
   population across the document rather than page-by-page.

2. **Redundant recomputation in `_analyze_paragraph_spacing`** rebuilds contextual rules per
   line. Correct but wasteful; candidate for hoisting the rules out of the loop.

3. **Mode-based body detection** assumes body text is the plurality style. Robust for technical
   specs; could mislead on cover pages or heavily tabular documents where no single style
   dominates.

---

## Cross-References

- File formats & schemas: [docs/output-files.md](../output-files.md)
- Segment reconstruction & block formation internals:
  [TEXT_PROCESSING_AND_BLOCK_GROUPING.md](TEXT_PROCESSING_AND_BLOCK_GROUPING.md)
- Header/footer iterative development history:
  [HEADER_FOOTER_DETECTION.md](HEADER_FOOTER_DETECTION.md)
- LLM stage that consumes these outputs: [LLM_INTEGRATION.md](LLM_INTEGRATION.md)
- System overview & data flow: [docs/architecture.md](../architecture.md)
</content>
</invoke>
