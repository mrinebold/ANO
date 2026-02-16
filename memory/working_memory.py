"""
Working Memory

Persistent memory for agents across sessions, tracking tasks, context,
blockers, and session history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ano_core.logging import get_agent_logger

from memory.template import parse_working_state, render_working_state

logger = get_agent_logger(__name__)


@dataclass
class TaskInfo:
    """Information about a task assigned to an agent."""

    title: str
    description: str = ""
    status: str = "pending"
    assigned_at: str = ""

    def __post_init__(self) -> None:
        """Set default timestamp if not provided."""
        if not self.assigned_at:
            self.assigned_at = datetime.now().isoformat()

        # Validate status
        valid_statuses = {"pending", "in_progress", "completed", "blocked"}
        if self.status not in valid_statuses:
            logger.warning(
                f"Invalid task status '{self.status}', defaulting to 'pending'"
            )
            self.status = "pending"


@dataclass
class BlockerInfo:
    """Information about a blocker preventing task progress."""

    description: str
    severity: str = "medium"
    created_at: str = ""

    def __post_init__(self) -> None:
        """Set default timestamp and validate severity."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

        # Validate severity
        valid_severities = {"low", "medium", "high", "critical"}
        if self.severity not in valid_severities:
            logger.warning(
                f"Invalid blocker severity '{self.severity}', defaulting to 'medium'"
            )
            self.severity = "medium"


@dataclass
class SessionEntry:
    """A single entry in the session history."""

    timestamp: str
    action: str
    outcome: str

    def __post_init__(self) -> None:
        """Set default timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class WorkingState:
    """
    Complete working state for an agent.

    This structure is persisted to WORKING.md and loaded on session start
    to provide continuity across sessions.
    """

    current_task: TaskInfo | None = None
    context: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    blockers: list[BlockerInfo] = field(default_factory=list)
    handoff_notes: str = ""
    session_history: list[SessionEntry] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    decisions_made: list[str] = field(default_factory=list)

    def has_active_task(self) -> bool:
        """Check if there is an active task."""
        return self.current_task is not None and self.current_task.status in {
            "pending",
            "in_progress",
            "blocked",
        }

    def has_blockers(self) -> bool:
        """Check if there are any blockers."""
        return len(self.blockers) > 0

    def critical_blockers(self) -> list[BlockerInfo]:
        """Get list of critical blockers."""
        return [b for b in self.blockers if b.severity == "critical"]


class WorkingMemory:
    """
    Persistent working memory for an agent across sessions.

    Manages reading and writing the WORKING.md file that tracks an agent's
    current task state, context, blockers, and session history.
    """

    def __init__(self, agent_name: str, memory_dir: str) -> None:
        """
        Initialize working memory.

        Args:
            agent_name: Name of the agent
            memory_dir: Directory to store WORKING.md file
        """
        self.agent_name = agent_name
        self.memory_dir = Path(memory_dir)
        self.working_file = self.memory_dir / "WORKING.md"
        self._state: WorkingState | None = None

        # Ensure memory directory exists
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"WorkingMemory initialized for agent '{agent_name}' at {self.working_file}"
        )

    def load(self) -> WorkingState:
        """
        Load working state from WORKING.md file.

        Returns:
            WorkingState loaded from file, or empty state if file doesn't exist
        """
        if not self.working_file.exists():
            logger.info(
                f"No existing WORKING.md for '{self.agent_name}', "
                f"starting with empty state"
            )
            self._state = WorkingState()
            return self._state

        try:
            content = self.working_file.read_text(encoding="utf-8")
            self._state = parse_working_state(content)
            logger.info(
                f"Loaded working state for '{self.agent_name}' - "
                f"Task: {self._state.current_task.title if self._state.current_task else 'None'}, "
                f"Blockers: {len(self._state.blockers)}"
            )
            return self._state
        except Exception as e:
            logger.error(
                f"Failed to load WORKING.md for '{self.agent_name}': {e}",
                exc_info=True,
            )
            # Return empty state on error
            self._state = WorkingState()
            return self._state

    def save(self, state: WorkingState) -> None:
        """
        Save working state to WORKING.md file.

        Args:
            state: WorkingState to persist
        """
        self._state = state

        try:
            content = render_working_state(state)
            self.working_file.write_text(content, encoding="utf-8")
            logger.info(f"Saved working state for '{self.agent_name}'")
        except Exception as e:
            logger.error(
                f"Failed to save WORKING.md for '{self.agent_name}': {e}",
                exc_info=True,
            )
            raise

    def get_state(self) -> WorkingState:
        """Get current working state, loading if necessary."""
        if self._state is None:
            self._state = self.load()
        return self._state

    def update_session(self, action: str, outcome: str) -> None:
        """
        Append a session entry and save.

        Args:
            action: Description of the action taken
            outcome: Description of the outcome
        """
        state = self.get_state()
        entry = SessionEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            outcome=outcome,
        )
        state.session_history.append(entry)
        self.save(state)
        logger.debug(f"Added session entry for '{self.agent_name}': {action}")

    def set_task(self, title: str, description: str = "") -> None:
        """
        Set the current task.

        Args:
            title: Task title
            description: Optional task description
        """
        state = self.get_state()
        state.current_task = TaskInfo(
            title=title,
            description=description,
            status="pending",
        )
        self.save(state)
        logger.info(f"Set task for '{self.agent_name}': {title}")

    def complete_task(self) -> None:
        """Mark the current task as completed."""
        state = self.get_state()
        if state.current_task:
            state.current_task.status = "completed"
            self.save(state)
            logger.info(
                f"Completed task for '{self.agent_name}': "
                f"{state.current_task.title}"
            )
        else:
            logger.warning(
                f"Attempted to complete task for '{self.agent_name}' "
                f"but no task is set"
            )

    def add_blocker(self, description: str, severity: str = "medium") -> None:
        """
        Add a blocker.

        Args:
            description: Description of the blocker
            severity: Severity level (low, medium, high, critical)
        """
        state = self.get_state()
        blocker = BlockerInfo(description=description, severity=severity)
        state.blockers.append(blocker)

        # Update task status to blocked if there's an active task
        if state.current_task and state.current_task.status != "completed":
            state.current_task.status = "blocked"

        self.save(state)
        logger.warning(f"Added blocker for '{self.agent_name}': {description}")

    def clear_blockers(self) -> None:
        """Clear all blockers."""
        state = self.get_state()
        blocker_count = len(state.blockers)
        state.blockers.clear()

        # Update task status if it was blocked
        if state.current_task and state.current_task.status == "blocked":
            state.current_task.status = "in_progress"

        self.save(state)
        logger.info(f"Cleared {blocker_count} blockers for '{self.agent_name}'")

    def add_context(self, context_item: str) -> None:
        """Add a context item."""
        state = self.get_state()
        if context_item not in state.context:
            state.context.append(context_item)
            self.save(state)

    def add_next_step(self, step: str) -> None:
        """Add a next step."""
        state = self.get_state()
        if step not in state.next_steps:
            state.next_steps.append(step)
            self.save(state)

    def add_file_modified(self, file_path: str) -> None:
        """Record a file modification."""
        state = self.get_state()
        if file_path not in state.files_modified:
            state.files_modified.append(file_path)
            self.save(state)

    def add_decision(self, decision: str) -> None:
        """Record a decision."""
        state = self.get_state()
        if decision not in state.decisions_made:
            state.decisions_made.append(decision)
            self.save(state)
