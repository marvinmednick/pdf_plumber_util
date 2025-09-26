---
name: update-status
description: EXECUTE IMMEDIATE STATUS.MD UPDATE - Update for phase changes and major milestones
usage: /update-status [focus_area]
---

# IMMEDIATE ACTION REQUIRED

**🚨 EXECUTE IMMEDIATELY WHEN CALLED - This is not optional guidance, this is a required action trigger.**

## STEP 1: EXECUTE STATUS.MD UPDATE NOW

**Based on focus_area parameter and recent work, immediately update docs/status.md by:**

1. **Analyzing what needs updating**:
   - If "active work" or general: Update "Active Work" section
   - If "phase change": Update both "Active Work" and add to "Last Completed Work"
   - If "design completion": Add new entry to "Last Completed Work" section

2. **Execute the appropriate updates**:
   - Use Read tool to check current docs/status.md content
   - Use Edit tool to make necessary updates
   - Check line count - if approaching 200 lines, archive older entries to phase-history.md

3. **Follow archival management**:
   - If near 200-line limit, move oldest "Last Completed Work" entries to docs/phase-history.md
   - Maintain balance between current visibility and historical preservation

## STEP 2: SELF-AUDITING AND COMPLIANCE REVIEW

**Self-Reminder**: "Manual `/update-status` call indicates automatic status updates may have been missed. Per CLAUDE.md protocol, status.md should be updated immediately for phase changes and major design completions."

**Compliance Review**: Analyze recent work to identify phase changes, design completions, or capability additions that warranted automatic status updates.

**Self-Correction**: Acknowledge any missed automatic updates and commit to better compliance.

---

# Command Documentation

## Usage Examples
```
/update-status                           # General status update
/update-status "active work"             # Focus on Active Work section
/update-status "phase change"            # Focus on phase transitions
/update-status "design completion"       # Focus on completed design work
```

## What it analyzes and updates:

1. **Current State Analysis**:
   - Recent work and file changes
   - Phase transitions or major milestones
   - Active work scope changes
   - Design document completions

2. **Status.md Update Areas**:
   - **Active Work**: Current phase and focus area
   - **Last Completed Work**: Major achievements (add new entry at top)
   - **Current State**: System status and capabilities
   - **Archival Management**: Move older entries to phase-history.md if approaching 200 lines

3. **Automatic Archival Process**:
   - Check docs/status.md line count during update
   - If approaching 200 lines, move oldest "Last Completed Work" entries to phase-history.md
   - Maintain focus on recent work while preserving historical record
   - Keep status.md as current snapshot, phase-history.md as comprehensive record

## Automatic Update Triggers (Per CLAUDE.md Protocol):
Manual use of this command suggests these automatic triggers may have been missed:
- **Phase changes**: Implementation ↔ Design, or major scope changes
- **Major design completion**: Architecture documents, design methodology completion
- **Significant capability additions**: New features, major analysis capabilities
- **Active work scope changes**: What you're working on has fundamentally changed

## Self-Auditing Process:
1. Execute status.md update based on recent work analysis
2. **Self-Reminder**: "Manual `/update-status` call indicates automatic status updates may have been missed. Per protocol, status.md should be updated immediately for phase changes and major design completions."
3. **Compliance Review**: Analyze conversation history to identify work that warranted automatic status updates
4. **Self-Correction**: Acknowledge any missed triggers and commit to better automatic compliance

## Archival Management:
- **Target Size**: Keep docs/status.md under 200 lines for readability
- **Archival Trigger**: When approaching limit, archive oldest completed work entries
- **Archive Destination**: Move to appropriate section in docs/phase-history.md
- **Preservation**: Maintain detailed historical record while keeping current status concise

## Integration with Workflow:
- Complements /update-worklog for immediate status visibility
- Maintains current project state for external viewers
- Automatically manages document size through archival process
- Serves as compliance auditing tool for missed automatic updates