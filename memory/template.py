"""
WORKING.md Template Rendering and Parsing

Handles conversion between WorkingState dataclass and markdown format.
"""

from typing import TYPE_CHECKING

from ano_core.logging import get_agent_logger

if TYPE_CHECKING:
    from memory.working_memory import WorkingState, TaskInfo, BlockerInfo, SessionEntry

logger = get_agent_logger(__name__)


def render_working_state(state: "WorkingState") -> str:
    """
    Render WorkingState to markdown matching the WORKING.md template format.

    Args:
        state: WorkingState to render

    Returns:
        Markdown-formatted string
    """
    lines = [
        "# Agent Working Memory",
        "",
        "## Current Task",
        "",
    ]

    # Current Task section
    if state.current_task:
        lines.extend([
            f"**Title**: {state.current_task.title}",
            "",
            f"**Status**: {state.current_task.status}",
            "",
            f"**Assigned**: {state.current_task.assigned_at}",
            "",
        ])
        if state.current_task.description:
            lines.extend([
                f"**Description**: {state.current_task.description}",
                "",
            ])
    else:
        lines.extend([
            "No active task.",
            "",
        ])

    # Context section
    lines.extend([
        "## Context",
        "",
    ])
    if state.context:
        for item in state.context:
            lines.append(f"- {item}")
        lines.append("")
    else:
        lines.extend([
            "No context items.",
            "",
        ])

    # Next Steps section
    lines.extend([
        "## Next Steps",
        "",
    ])
    if state.next_steps:
        for i, step in enumerate(state.next_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
    else:
        lines.extend([
            "No next steps defined.",
            "",
        ])

    # Blockers section
    lines.extend([
        "## Blockers",
        "",
    ])
    if state.blockers:
        for blocker in state.blockers:
            lines.extend([
                f"### {blocker.severity.upper()}: {blocker.description}",
                "",
                f"*Created: {blocker.created_at}*",
                "",
            ])
    else:
        lines.extend([
            "No blockers.",
            "",
        ])

    # Handoff Notes section
    lines.extend([
        "## Handoff Notes",
        "",
    ])
    if state.handoff_notes:
        lines.extend([
            state.handoff_notes,
            "",
        ])
    else:
        lines.extend([
            "No handoff notes.",
            "",
        ])

    # Files Modified section
    lines.extend([
        "## Files Modified",
        "",
    ])
    if state.files_modified:
        for file_path in state.files_modified:
            lines.append(f"- `{file_path}`")
        lines.append("")
    else:
        lines.extend([
            "No files modified.",
            "",
        ])

    # Decisions Made section
    lines.extend([
        "## Decisions Made",
        "",
    ])
    if state.decisions_made:
        for decision in state.decisions_made:
            lines.append(f"- {decision}")
        lines.append("")
    else:
        lines.extend([
            "No decisions recorded.",
            "",
        ])

    # Session History section
    lines.extend([
        "## Session History",
        "",
    ])
    if state.session_history:
        for entry in state.session_history:
            lines.extend([
                f"### {entry.timestamp}",
                "",
                f"**Action**: {entry.action}",
                "",
                f"**Outcome**: {entry.outcome}",
                "",
            ])
    else:
        lines.extend([
            "No session history.",
            "",
        ])

    return "\n".join(lines)


def parse_working_state(markdown: str) -> "WorkingState":
    """
    Parse a WORKING.md file back into WorkingState.

    Args:
        markdown: Markdown content to parse

    Returns:
        WorkingState parsed from markdown
    """
    # Import here to avoid circular dependency
    from memory.working_memory import (
        WorkingState,
        TaskInfo,
        BlockerInfo,
        SessionEntry,
    )

    state = WorkingState()
    lines = markdown.split("\n")
    current_section = None
    current_blocker_desc = None
    current_blocker_severity = None
    current_session_timestamp = None
    current_session_action = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Section headers
        if line.startswith("## "):
            current_section = line[3:].strip()
            i += 1
            continue

        # Parse based on current section
        if current_section == "Current Task":
            if line.startswith("**Title**:"):
                title = line.split(":", 1)[1].strip()
                state.current_task = TaskInfo(title=title)
            elif line.startswith("**Status**:") and state.current_task:
                state.current_task.status = line.split(":", 1)[1].strip()
            elif line.startswith("**Assigned**:") and state.current_task:
                state.current_task.assigned_at = line.split(":", 1)[1].strip()
            elif line.startswith("**Description**:") and state.current_task:
                state.current_task.description = line.split(":", 1)[1].strip()

        elif current_section == "Context":
            if line.startswith("- ") and line != "- No context items.":
                state.context.append(line[2:])

        elif current_section == "Next Steps":
            if line and line[0].isdigit() and ". " in line:
                step = line.split(". ", 1)[1]
                state.next_steps.append(step)

        elif current_section == "Blockers":
            if line.startswith("### "):
                # Parse blocker header: "### SEVERITY: description"
                parts = line[4:].split(":", 1)
                if len(parts) == 2:
                    current_blocker_severity = parts[0].strip().lower()
                    current_blocker_desc = parts[1].strip()
            elif line.startswith("*Created:") and current_blocker_desc:
                created_at = line.replace("*Created:", "").replace("*", "").strip()
                state.blockers.append(
                    BlockerInfo(
                        description=current_blocker_desc,
                        severity=current_blocker_severity or "medium",
                        created_at=created_at,
                    )
                )
                current_blocker_desc = None
                current_blocker_severity = None

        elif current_section == "Handoff Notes":
            if line and not line.startswith("#") and line != "No handoff notes.":
                if state.handoff_notes:
                    state.handoff_notes += "\n" + line
                else:
                    state.handoff_notes = line

        elif current_section == "Files Modified":
            if line.startswith("- `") and line.endswith("`"):
                file_path = line[3:-1]
                state.files_modified.append(file_path)

        elif current_section == "Decisions Made":
            if line.startswith("- ") and line != "- No decisions recorded.":
                state.decisions_made.append(line[2:])

        elif current_section == "Session History":
            if line.startswith("### "):
                # New session entry
                if current_session_timestamp and current_session_action:
                    # Save previous entry
                    state.session_history.append(
                        SessionEntry(
                            timestamp=current_session_timestamp,
                            action=current_session_action,
                            outcome="",
                        )
                    )
                current_session_timestamp = line[4:]
                current_session_action = None
            elif line.startswith("**Action**:"):
                current_session_action = line.split(":", 1)[1].strip()
            elif line.startswith("**Outcome**:"):
                outcome = line.split(":", 1)[1].strip()
                if current_session_timestamp and current_session_action:
                    state.session_history.append(
                        SessionEntry(
                            timestamp=current_session_timestamp,
                            action=current_session_action,
                            outcome=outcome,
                        )
                    )
                    current_session_timestamp = None
                    current_session_action = None

        i += 1

    # Save any remaining session entry
    if current_session_timestamp and current_session_action:
        state.session_history.append(
            SessionEntry(
                timestamp=current_session_timestamp,
                action=current_session_action,
                outcome="",
            )
        )

    logger.debug("Parsed working state from markdown")
    return state
