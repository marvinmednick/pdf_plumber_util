# Work Log

This file tracks development progress during active work sessions. It gets cleared after each commit.

------
### 2026-07-16 23:12 - Documentation & output-file review
- **Completed**: Reviewed README, docs/cli-usage.md, docs/architecture.md, docs/index.md against actual output-writing code (extractor.py, analyzer.py, visualizer.py, llm_analyzer.py, pipeline/stages.py, workflow/orchestrator.py, utils/file_handler.py). Identified undocumented output files (_full_lines, _visualization.*, _spacing.json, _headers_footers.json, _report.json, workflow_context_*.json), stale docs (_spacing.pdf/_block_spacing.pdf no longer produced), broken docs/index.md links, and wholesale content duplication in utils/file_handler.py
- **Tests**: None run (documentation review only)
- **Next**: Proposed a docs/output-files.md reference doc, cli-usage.md corrections, and code cleanup; awaiting user direction
---
### 2026-07-16 23:22 - Git archaeology on code issues from doc review
- **Completed**: Traced origins of three code issues: file_handler.py duplication (9438a22, 2025-05-08, pure 146-line append), _full_lines/_lines identical output (0d3fc9a, 2025-05-07, blank-line processing moved to _process_words leaving _full_lines a misnomer), analyzer.py analyze_document/analyze_document_data copy-paste (2f01646, 2025-05-07, deliberate in-memory variant)
- **Tests**: None run (history analysis only)
- **Next**: Cleanup decisions for the three issues pending user direction
---
### 2026-07-16 23:26 - Verified code-issue paths vs pattern-detection flow
- **Completed**: Confirmed pattern-detection work (tools/prompt_testing/) is standalone scripts on pre-extracted JSON fixtures, importing none of FileHandler/PDFExtractor/PDFAnalyzer; core/pipeline is legacy (May 2025, only imported by pdf_plumb.py old entry point, not cli.py)
- **Tests**: None run (code-path analysis only)
- **Next**: n/a
---
### 2026-07-16 23:34 - _full_lines/_lines investigation: inverted finding
- **Completed**: Discovered 0d3fc9a's comment 'already processed in _process_words' is wrong — no blank-line filtering exists anywhere in current extractor. Verified real output (h264_20pages_lines.json) contains 49 blank lines of 1064. _full_lines.json is true to its name; _lines.json is the file not honoring its contract (analyzer.py:1177 docstring claims blanks removed). _process_blank_lines recoverable from git (deleted in 0d3fc9a)
- **Tests**: Data inspection of existing output only
- **Next**: User decision — drop _full_lines and fix docstrings (zero behavioral risk) vs restore filtering to _lines (changes downstream analysis inputs)
---
### 2026-07-16 23:40 - Downstream blank-line handling analysis
- **Completed**: Traced blank-line handling through analyzer. _analyze_blocks skips blanks (analyzer.py:743) but uses stored gap_before (751) for merge decisions — real data shows true visual gaps of 16.2/39.6/50.5pt seen as 0/0/43.7pt where blanks intervene (false-merge risk). Spacing statistics (_analyze_line_spacing:331, _collect_contextual_gaps:68) include blank lines entirely, polluting contextual spacing rules (blanks carry predominant_size=10.0 matching body text). Recovered deleted _process_blank_lines from git: it recomputed gaps from prev/next non-blank bboxes, correctly preserving true visual gaps
- **Tests**: Empirical inspection of h264_20pages_lines.json
- **Next**: Recommendation now REVERSED — restore _process_blank_lines for _lines.json (fixes live correctness bug in block merge decisions); user decision pending
---
### 2026-07-16 23:46 - Verification methodology + geometric ground-truth measurement
- **Completed**: Defined verification hierarchy for blank-line handling (geometric ground truth, block-level A/B diff, spacing-rule comparison, regression suite, visual adjudication). Ran geometric test on h264_20pages_lines.json: 13/996 (1.3%) consecutive visible-line pairs have understated gaps, errors up to 194pt (stored 7.1 vs true 201.7)
- **Tests**: Geometric gap validation script against real extraction data
- **Next**: Block-level A/B diff (current vs filtered) to see which merge decisions actually change
---
### 2026-07-16 23:48 - Identified pages with largest blank-line gap errors for visual review
- **Completed**: Full site scan of both datasets: 13 sites (20-page), 104 sites (100-page extract). Hotspots: page 1 (194.6pt max error), page 48 (174.5pt, figure caption), page 5 (4 sites, 58-78pt, headings), pages 70-73 (10/8/6/5 sites — figure/table dense), pages 17/19 (List of Figures/Tables headings stored as ~8.5pt gaps)
- **Tests**: Geometric scan script on h264_20pages/h264_100pages lines.json
- **Next**: User visual review of recommended pages; then A/B block diff
---
### 2026-07-16 23:53 - Generated gap-error overlay PDF for visual review
- **Completed**: Built scratch script annotating stored-vs-true gap discrepancies onto source PDF; generated output/h264_100pages_gap_error_overlay.pdf covering pages 5,17,19,48,70,71 (23 sites). Red band = actual visual gap, blue band = gap analyzer uses. Verified rendering on pages 5 and 17. Noted built-in visualizer recomputes gaps from non-blank bboxes (visualizer.py:289-297) so it shows true gaps, not stored ones
- **Tests**: Visual verification of rendered overlay pages 1-2
- **Next**: User visual review; then decide on restoring _process_blank_lines
---
### 2026-07-16 23:57 - Consolidated review of proposed doc changes and fixes
- **Completed**: Retracted earlier 'broken links' finding for docs/index.md — verified readme.md and development.md are generated at build time by mkdocs-gen-files (mkdocs.yml:17-20, scripts/docs/generate_readme.py + generate_development.py) from README.md and CLAUDE.md; confirmed present in built site/ as readme/ and development/. Links are valid in the mkdocs site, only appear broken when browsing raw docs/ on disk or GitHub. Verified remaining doc edit points: cli-usage.md:115-120 (extract, missing _full_lines), :148-150 (analyze), :202-205 (phantom _spacing.pdf/_block_spacing.pdf), :657 (Output File Structure section)
- **Tests**: None run (verification of doc/build state only)
- **Next**: Awaiting user decision on _lines blank-line filter restore (gates the output-files doc); then A/B block diff
---
### 2026-07-17 00:20 - Ratio-cap heuristic validated against full 100-page corpus
- **Completed**: Tested gap<=k*font_size cap layered on statistical spacing_rules, k in [1.2,1.5,1.8,2.0,2.5,3.0], on filtered (blank-line-removed) lines data. Dense classes (size 9.0 n=141, size 10.0 n=3822) completely unaffected at all k -- validates cap targets sparse classes only. k=1.8-2.0 fixes page 23 (title/heading merge) without the k=1.2 regression on page 40 (splits a piecewise Min/Max math formula's brace fragments apart -- false positive). But found a NEW false positive persistent at every k up to 2.5: page 51 size 7.5 class (n=1 sample) splits '01'/'23' figure-label grid into 2 blocks -- baseline statistical range (22-33pt) already exceeds any reasonable k*size, so no k value fixes both page23 and page51 simultaneously
- **Tests**: Full-corpus programmatic diff (ratio_cap_test.py, ratio_cap_detail.py in scratchpad) across 6 k values, page-level detail inspection for k=1.2 and k=1.8
- **Next**: Recommend cap only apply when sample count is adequate (e.g. n>=5); leave extremely sparse classes (n=1-3) to a different fallback. Report findings to user
---
### 2026-07-17 00:31 - ISSUE: sparse contextual-spacing classes need font+size grouping and a small-n fallback
- **Issue**: _collect_contextual_gaps (analyzer.py:68-120) groups gap samples by predominant_size only; predominant_font is not part of the key or the pair-match condition. This pools structurally unrelated content (headings, math-formula fragments, heading-wrap continuations) into one bucket whenever they share a font size, corrupting the derived merge threshold for any sparse size class. Confirmed corpus-wide for size=12.0 (n=3, sources: page23 title->heading 25.7pt, page40 Min/Max formula brace 15.1pt, page43 heading-wrap 1.8pt)
- **Root cause #1**: no font grouping -- verified font+size bucketing correctly ejects the formula fragment (different font: TimesNewRomanPSMT vs TimesNewRomanPS-BoldMT) but does NOT separate title from section heading, since both share identical font/size/weight (TimesNewRomanPS-BoldMT 12pt) -- that distinction is positional/semantic, not typographic, and cannot be recovered from font metadata alone
- **Root cause #2** (newly found, independent): _analyze_contextual_spacing (analyzer.py:122-197) derives line_spacing_range from Counter.most_common(1) -- the statistical mode -- times +/-20% tolerance. With small-n all-distinct sample sets (e.g. n=2-3, no repeats), 'the mode' is an arbitrary tie-break on iteration order, not a meaningful typical value. Font+size grouping alone would still leave the genuine-heading bucket at n=2 (25.7, 1.8) -- still too sparse for mode-picking to be reliable
- **Proposed direction (UPDATED 2026-07-17, supersedes original framing below)**: the primary defect is not sparsity per se but the same-size-adjacency gate itself -- _collect_contextual_gaps only records a gap_before sample when the immediately PRECEDING line also matches the current line's predominant_size, which silently discards most real occurrences of a heading style (verified: 12 of 15 occurrences of TimesNewRomanPS-BoldMT/12.0pt on the H.264 doc are preceded by differently-sized body text and never contribute a sample). Fix: drop the same-size-adjacency requirement and pool gap_before across ALL lines of a font+size class regardless of predecessor size. Validated this reveals real signal invisible to the current gate -- 7 numbered top-level headings (1 Scope through 7 Syntax and semantics) cluster tightly at 25.7-26.0pt, and page 23's disputed gap (25.7pt) sits dead-center in that cluster, confirming the original 2-block (unmerged) decision was correct all along, with much stronger evidence than the n=3 bucket the current algorithm sees. Font-aware bucketing (add font to the grouping key, not just size) remains a useful complementary fix for excluding unrelated content sharing a size (e.g. correctly ejects the page-40 math-formula fragment, a different, non-bold font, from the heading bucket). The k*font_size ratio-cap explored earlier is still a plausible fallback for classes that remain genuinely sparse even after broadening (e.g. page 51, size 7.5 n=1, a 2x2 figure-label grid, where the content is diagram-label text that may not follow body-text line-spacing conventions at all) -- but is no longer the primary mechanism, since broadening the sample pool resolves the page-23 case directly without needing an arbitrary multiplier. Original narrower framing (kept for history): [see below]
- **Blocks**: this is a pre-existing issue, independent of but adjacent to the _lines/_full_lines blank-line-filter fix (see prior entries) -- the blank-line fix is still correct and worth doing on its own; this sparse-class issue should be tracked separately since fixing it well needs broader validation than one document provides
- **Tests**: none (design investigation only); scripts in scratchpad: font_size_grouping.py
---
### 2026-07-17 00:39 - Added sparse-spacing-class issue to docs/status.md Pending Issues
- **Completed**: Added Medium Priority entry to docs/status.md Pending Issues section summarizing the sparse contextual-spacing-class issue (font grouping + small-n mode instability) with pointer back to full WORK_LOG.md investigation
- **Note**: docs/status.md is now 226 lines, over the CLAUDE.md 200-line archival trigger -- flagging for the next checkpoint's archival pass to phase-history.md, not addressed in this session
- **Next**: n/a
---
### 2026-07-17 00:45 - Correction: broadening gap-sample pool beyond same-size-adjacency
- **Completed**: User correctly challenged the '3 samples' framing -- traced all 15 occurrences of TimesNewRomanPS-BoldMT/12.0pt. Confirmed root cause precisely: _collect_contextual_gaps requires the PREVIOUS line to also be size 12.0 before a gap is recorded as a sample; 12 of 15 occurrences are preceded by 10pt body text and are silently excluded regardless of their actual gap_before value. Only page23's title->'0 Introduction' pair has a same-size predecessor, which is why it was the sole real occupant of the corrupted 3-sample bucket
- **Key finding**: broadening to 'all gap_before values for a font+size class, regardless of predecessor size' reveals 7 numbered top-level headings (1 Scope through 7 Syntax and semantics) cluster at 25.7-26.0pt -- an extremely tight, document-native convention. Page 23's disputed 25.7pt gap sits dead-center in this cluster, meaning it is NOT an outlier -- strong evidence the original block-separation (2 blocks) is correct, independent of and stronger than the earlier ratio-cap/font-grouping analysis
- **Revised fix direction**: replace the same-size-adjacency gate in _collect_contextual_gaps with pooling gap_before across ALL lines of a font+size class regardless of predecessor size -- more data (13 vs 3 samples for this class) and conceptually the right question (how far does this style typically sit from whatever precedes it, not only from same-size predecessors)
- **Open question**: cannot verify whether ANNEX headings (page >100, outside current h264_100pages.pdf extraction) follow the same ~25.8pt convention -- would need a longer extraction
- **Tests**: heading_adjacency.py in scratchpad, traced against h264_100pages_lines.json
- **Next**: update the Pending Issues entry in docs/status.md to reflect this stronger finding
---
### 2026-07-17 00:59 - Implemented the three code fixes from this session's investigation
- **Completed**:
  1. extractor.py: restored _process_blank_lines (recovered from git 0d3fc9a^, adapted to NOT round gap_before/gap_after -- the A/B test earlier this session proved that rounding step was an unrelated confound causing false merges). Wired into save_results: _full_lines.json now saves the raw unfiltered data, _lines.json saves the filtered result. Resolves the byte-identical-duplicate-file issue as a side effect
  2. utils/file_handler.py: removed the whole-file self-duplication (9438a22, 2025-05-08) -- file was 287 lines with two complete FileHandler class definitions, now 143 lines with one, keeping the first copy's __init__ (which correctly updates output_dir/logger on re-init)
  3. core/analyzer.py: analyze_document (file-based entry point) now loads the file and delegates to analyze_document_data instead of duplicating ~117 lines of identical logic (confirmed via diff before refactoring)
- **Tests**: uv run pytest -m 'not golden': 163 passed, 5 failed (all pre-existing Azure OpenAI connectivity failures, unrelated -- no network/credentials in this environment). Targeted unit tests (test_analyzer.py, test_spacing_reconstruction.py, test_error_handling.py): 19/19 passed. End-to-end smoke test: ran 'pdf-plumb extract' on data/h264_100pages.pdf -- verify_full_lines.json retains all 229 blank lines (4787 total), verify_lines.json has 0 blank lines (4558 total, -229), and page 5's 'NOTE' heading gap_before now reads 66.9pt (previously ~8pt), matching the true visual gap measured/visualized earlier this session
- **Next**: doc updates -- docs/output-files.md (new), cli-usage.md corrections, README 'what you get' section, architecture.md data-flow chain, mkdocs.yml nav entry
---
### 2026-07-17 01:03 - Documentation updates completed
- **Completed**:
  1. Created docs/output-files.md -- canonical reference for every output file: naming convention, pipeline diagram, per-command file tables, JSON schema for _lines.json/_full_lines.json, and a 'debug/internal outputs' section documenting workflow_context_*.json, _visualization.txt/.json, and the legacy pipeline's _spacing.json/_headers_footers.json/_report.json as not reachable from the current CLI (verified via grep -- generate_visualization has zero callers in cli.py, core/pipeline only imported by legacy pdf_plumb.py)
  2. mkdocs.yml: added Output Files nav entry
  3. docs/cli-usage.md: added _full_lines.json to extract's Output Files list; removed phantom _spacing.pdf/_block_spacing.pdf from process command and from the Output File Structure troubleshooting section (replaced with accurate document_full_lines.json/document_lines.json/document_visualized.pdf); added pointers to output-files.md from each Output Files subsection
  4. README.md: added 'What You Get' section showing the process command's output tree; added Output Files Reference to Documentation links
  5. docs/architecture.md: added 'Concrete File Chain' subsection mapping the existing conceptual data-flow diagram to actual filenames, linking to output-files.md
  6. scripts/docs/generate_readme.py: added docs/output-files.md -> output-files.md to the link-transformation mapping (same pattern as existing cli-usage.md/architecture.md entries) -- required for the new README link to resolve correctly in the generated mkdocs readme.md page
- **Tests**: uv run mkdocs build -- clean, no new warnings (confirmed the output-files.md link warning was introduced and fixed within this session, all remaining warnings pre-exist and are out of scope). uv run pytest -m 'not golden': 163 passed, 5 failed (same pre-existing Azure OpenAI connectivity failures as before these changes)
- **Next**: This completes the full scope from this session's investigation (code fixes + doc updates). Sparse contextual-spacing-class issue remains tracked separately in docs/status.md Pending Issues for future work
