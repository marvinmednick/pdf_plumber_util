# Documentation Framework

**Purpose**: Define the documentation structure used in this project, optimized for Claude Code efficiency.

**Audience**: **HUMANS ONLY** - This is a reference guide for understanding or updating the documentation structure. Claude Code should NOT read this file during normal development.

**For Claude Code**: Read `CLAUDE.md` instead - it contains the actual project-specific guidance.

**Originally Created**: October 27, 2025

---

## Overview

This document defines the tiered documentation structure for the pdf_plumb project. It was derived from a unified framework that was previously shared across multiple projects.

---

## File Structure

```
/
├── CLAUDE.md                          # AI development guidance
├── WORK_LOG.md                        # Session tracking (cleared after commits)
├── README.md                          # User-facing overview
├── DOCUMENTATION_FRAMEWORK.md        # This file - framework reference (humans only)
└── docs/
    ├── status.md                      # Current state (90-150 lines, archive at 150)
    ├── architecture.md                # System design
    ├── design-decisions.md            # Architectural rationale
    ├── phase-history.md               # Complete chronology
    ├── design/                        # Feature deep-dives
    │   └── FEATURE_NAME.md
    └── analysis/                      # Research findings
        └── ANALYSIS_TOPIC.md
```

---

## Tier System

**Tier 1: Session Context (Read First)**
1. `WORK_LOG.md` - What happened in recent sessions
2. `docs/status.md` - Current phase and active work
3. Recent git commits - Latest changes

**Tier 2: Architecture & Context**
- `docs/architecture.md` - System design
- `docs/design-decisions.md` - WHY choices were made
- `docs/phase-history.md` - Historical record

**Tier 3: Feature Deep-Dives**
- `docs/design/FEATURE.md` - Detailed implementation plans

**Tier 4: Analysis & Research**
- `docs/analysis/TOPIC.md` - Performance, research findings

---

## File Size Guidelines

| File | Target Size | Archival Trigger | Archive Destination |
|------|-------------|------------------|---------------------|
| `WORK_LOG.md` | Varies (session-based) | Every commit | `docs/status.md` then cleared |
| `docs/status.md` | 90-150 lines | 150 lines | `docs/phase-history.md` |
| `docs/architecture.md` | 200-300 lines | As needed | Create new design docs |
| `docs/design-decisions.md` | Grows indefinitely | N/A | Historical record |
| `docs/phase-history.md` | Grows indefinitely | N/A | Complete archive |
| `docs/design/*.md` | 100-400 lines | N/A | Focused per feature |

**Principle**: Keep frequently-read files small for token efficiency, archive older content to phase-history.md

---

## Documentation Maintenance Workflows

### Session Startup
1. Read `WORK_LOG.md` first - Recent session context
2. Read `docs/status.md` - Current priorities
3. Continue from where previous session left off

### During Development
After ANY significant work (MANDATORY):
```bash
echo "---
### $(date '+%Y-%m-%d %H:%M') - [Task description]
- **Completed**: [Achievements with file references]
- **Tests**: [Results if applicable]
- **Next**: [Next steps]" >> WORK_LOG.md
```

### Preparing for Commit
1. Review WORK_LOG.md entries since last commit
2. Consolidate key achievements to docs/status.md "Recent Completions"
3. Add detailed entry to docs/phase-history.md (current phase)
4. Archive docs/status.md if approaching 150 lines
5. Clear WORK_LOG.md to template

### Starting New Phase
1. Add new phase section to docs/phase-history.md
2. Mark previous phase as complete (✅)
3. Update "Current Phase" in docs/status.md
4. Move completed items from status to phase-history
5. Archive old "Recent Completions" (>30 days)

---

## docs/status.md Structure Template

```markdown
# pdf_plumb Status

**Date**: [Current date]
**Current Phase**: [Phase name]
**Status**: [Active Development | Stable | Maintenance]

---

## Current State

**System Status**: [1-2 sentence capability summary]
**Active Work**: [1 sentence - what's being worked on RIGHT NOW]

---

## Current Work

### 1. [Work Item Name]
- **Status**: [Not started | In progress | Blocked]
- **Priority**: [High | Medium | Low]
- **What**: [1-2 sentence description]
- **Details**: See `docs/design/ITEM.md` [if complex]

---

## Next Up

### 2. [Next Work Item]
- **Priority**: [High | Medium | Low]
- **What**: [Brief description]

---

## Blockers

[List or "None currently"]

---

## Last Completed Work

[Brief entries for last 30 days only]
- ✅ **Date/Name** - Brief description

**For complete history**: See `docs/phase-history.md`

---

## Known Test Issues

**Deferred Issues** (require further investigation):
- `test_name`: Description and reason deferred

---

*For historical context and completed phases, see `docs/phase-history.md`.*
```

**Size Management**:
- Target: 90-150 lines
- Archive trigger: 150 lines
- Archive process: Move oldest "Last Completed Work" entries to phase-history.md

---

## Anti-Patterns (Avoid These)

❌ **Duplicating content** across files — each piece of info lives in ONE place

❌ **Implementation details in docs/status.md** — keep status lean, move details to design docs

❌ **Historical completions in docs/status.md** — only keep last 30 days, full history in phase-history.md

❌ **Code snippets in docs/status.md** — reference actual code files with line numbers

❌ **Inferring architectural decisions** — only document explicitly documented decisions

❌ **Status or metrics in CLAUDE.md** — CLAUDE.md is for patterns, not state

❌ **Large README files** — keep under 100 lines, link to detailed docs

---

## Custom Commands

Project commands are in `.claude/commands/`:
- `/update-worklog` - Auto-generate WORK_LOG.md entries with self-auditing
- `/update-status` - Update docs/status.md with archival management
- `/commit-work` - Two-commit checkpoint (implementation + status consolidation)
- `/complete-checkpoint` - Complete deferred status consolidation

---

## Validation Checklist

When verifying framework compliance:

- [ ] WORK_LOG.md exists with template
- [ ] CLAUDE.md has Work Log Protocol section
- [ ] CLAUDE.md references (not duplicates) other docs
- [ ] docs/status.md is 90-150 lines
- [ ] docs/status.md has "Last Completed Work" section
- [ ] docs/status.md links to design docs for details
- [ ] docs/architecture.md exists
- [ ] docs/design-decisions.md exists
- [ ] docs/phase-history.md exists
- [ ] docs/design/ directory exists
- [ ] docs/analysis/ directory exists
- [ ] Cross-references use relative paths
- [ ] No duplicate content across files
- [ ] CLAUDE.md has no status/metrics/history
