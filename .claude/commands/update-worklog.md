---
name: update-worklog
description: EXECUTE IMMEDIATE WORK_LOG.md UPDATE - Analyze recent work and generate timestamped entry
usage: /update-worklog [user_notes]
---

# IMMEDIATE ACTION REQUIRED

**🚨 EXECUTE IMMEDIATELY WHEN CALLED - This is not optional guidance, this is a required action trigger.**

## STEP 1: EXECUTE WORK_LOG.md UPDATE NOW

**Run this bash command immediately:**

```bash
echo "---
### $(date '+%Y-%m-%d %H:%M') - [Describe the work completed]
- **Completed**: [List major achievements based on analysis below]
- **Files Modified**: [List changed files with brief descriptions and line counts]
- **Tests**: [Test results if applicable]
- **Design Work**: [Architecture/design work if applicable]
- **User Notes**: [Include user_notes parameter if provided]
- **Next**: [Inferred next steps]" >> WORK_LOG.md
```

## STEP 2: SELF-AUDITING AND COMPLIANCE REVIEW

**Self-Reminder**: "Manual `/update-worklog` call indicates automatic WORK_LOG updates may have been missed. Per CLAUDE.md protocol, work log updates should happen IMMEDIATELY after completing any significant work."

**Compliance Review**: Analyze recent conversation to identify work that should have triggered automatic updates.

**Self-Correction**: Acknowledge any missed automatic updates and commit to better compliance.

---

# Command Documentation

## Usage Examples
```
/update-worklog [user_notes]
/update-worklog "discovered performance bottleneck during testing"
/update-worklog  # Auto-analysis only
```

## What it analyzes:

1. **Recent Work Analysis**:
   - Git diff and staged/unstaged changes
   - File modifications and additions
   - Test results and status
   - Import errors or implementation fixes

2. **Work Log Entry Generation**:
   - Current timestamp (YYYY-MM-DD HH:MM format)
   - **Completed**: What was accomplished based on file analysis
   - **Files Modified**: List of changed files with brief descriptions
   - **Tests**: Test status and any relevant results
   - **Next**: Inferred next steps or remaining work

3. **User Context Integration**:
   - Optional user_notes parameter adds literal text to the entry
   - Provides context Claude cannot infer from code changes
   - Supplemental information about decisions, collaboration, discoveries

## Example Output Format:
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
- **Primary purpose**: Backup for missed automatic updates with compliance improvement