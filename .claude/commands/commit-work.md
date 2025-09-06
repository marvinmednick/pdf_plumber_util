---
name: commit-work
description: Complete development checkpoint with auto-generated commits and status updates
usage: /commit-work [--code-only] [user_guidance]
---

# Commit Work Command

Main workflow command that commits implementation work and updates project status using auto-generated content based on file analysis and work log entries.

## Usage
```
/commit-work [user_guidance]                    # Default: two-commit checkpoint
/commit-work --code-only [user_guidance]       # Implementation commit only
/commit-work "emphasize testing improvements"   # With guidance for framing
```

## Default Behavior (Two-Commit Checkpoint):

1. **Implementation Commit**:
   - Stages implementation files + WORK_LOG.md
   - Auto-generates descriptive commit message from file analysis
   - Creates commit with work log as evidence of development process

2. **Status Update Commit**:
   - Consolidates WORK_LOG.md entries → docs/status.md "Last Completed Work"
   - Updates system capabilities and current state
   - Clears WORK_LOG.md for next development session
   - Creates administrative commit with status checkpoint

## Parameters:

### `user_guidance` (Optional)
**Type**: Instructions to Claude on how to frame the work
**Purpose**: Influences how Claude writes commit messages and status updates
**Examples**:
- `"emphasize the performance benefits over implementation details"`
- `"focus on bug fix impact, this was critical for users"`
- `"highlight the testing improvements and quality assurance"`
- `"this enables the TOC feature to work properly"`

### `--code-only` Flag
**Purpose**: Edge case for when status update should be deferred
**Behavior**: Only creates implementation commit, skips status consolidation
**Use cases**:
- Experimental features not ready for status documentation
- Incremental work that's part of larger feature
- When additional testing needed before declaring completion

## Auto-Generation Process:

1. **Analyzes All Changes**:
   - Git diff of staged and unstaged files
   - Work log entries and development history
   - Test results and implementation patterns
   - File types and scope of modifications

2. **Generates Commit Messages**:
   - Descriptive summary of what was accomplished
   - Technical details about key changes
   - Impact on system capabilities
   - Follows established commit message format

3. **Updates Project Status**:
   - Adds new section to "Last Completed Work" in docs/status.md
   - Updates "System Status" and "Current State" if applicable
   - Moves resolved issues from "Pending Issues" if relevant
   - Maintains project status document structure

## Example Workflow:

**Standard Development Cycle**:
```bash
# During development (optional)
/update-worklog "focusing on error handling edge cases"

# Complete development checkpoint
/commit-work "this completes the TOC detection feature"
```

**Result**: Two commits created:
1. `"Complete TOC detection implementation with comprehensive testing"`
2. `"Update project status and clear work log"`

**Edge Case Workflow**:
```bash
# Implementation only
/commit-work --code-only "experimental optimization, needs more testing"

# Later, when ready
/complete-checkpoint
```

## Integration:
- Works with existing git workflow and repository structure
- Maintains established documentation standards
- Preserves work log format and project status organization
- Compatible with both individual and collaborative development