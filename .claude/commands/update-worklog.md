---
name: update-worklog
description: Automatically analyze recent work and generate timestamped work log entry
usage: /update-worklog [user_notes]
---

# Update Work Log Command

Analyzes recent file changes, git status, and test results to automatically generate a comprehensive work log entry with current timestamp.

## Usage
```
/update-worklog [user_notes]
/update-worklog "discovered performance bottleneck during testing"
/update-worklog  # Auto-analysis only
```

## What it does:

1. **Analyzes Recent Work**:
   - Git diff and staged/unstaged changes
   - File modifications and additions
   - Test results and status
   - Import errors or implementation fixes

2. **Auto-Generates Work Log Entry**:
   - Current timestamp (YYYY-MM-DD HH:MM format)
   - **Completed**: What was accomplished based on file analysis
   - **Files Modified**: List of changed files with brief descriptions
   - **Tests**: Test status and any relevant results
   - **Next**: Inferred next steps or remaining work

3. **Adds User Context**:
   - Optional user_notes parameter adds literal text to the entry
   - Provides context Claude cannot infer from code changes
   - Supplemental information about decisions, collaboration, discoveries

## Example Output:
```
---
### 2025-09-06 12:30 - Implementation Issues Fixed
- **Completed**: Fixed save_json import error and standardized page_indexes_analyzed field naming across codebase
- **Files Modified**: 
  - src/pdf_plumb/utils/json_utils.py: Added save_json function with orjson backend (12 lines)
  - src/pdf_plumb/workflow/states/additional_section_headings.py: Added field name compatibility
  - tests/unit/test_header_footer_toc_enhanced.py: Updated mock data field names
- **Tests**: All 11/11 TOC tests + 23/23 additional section heading tests passing
- **User Notes**: discovered performance bottleneck during testing
- **Next**: Ready for production deployment with all critical issues resolved
```

## Integration with Workflow:
- Can be called anytime during development when work hasn't been logged
- Automatically appends to existing WORK_LOG.md content
- Follows established work log format for consistency
- Prepares work log content for subsequent /commit-work command