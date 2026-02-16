"""Tests for memory module — WorkingMemory, WorkingState, TaskInfo, BlockerInfo."""

from __future__ import annotations

import os

import pytest

from memory.working_memory import (
    BlockerInfo,
    SessionEntry,
    TaskInfo,
    WorkingMemory,
    WorkingState,
)


class TestTaskInfo:
    def test_create_defaults(self):
        task = TaskInfo(title="Test task")
        assert task.status == "pending"
        assert task.assigned_at != ""

    def test_invalid_status_defaults(self):
        task = TaskInfo(title="Test", status="invalid")
        assert task.status == "pending"

    def test_valid_statuses(self):
        for status in ["pending", "in_progress", "completed", "blocked"]:
            task = TaskInfo(title="Test", status=status)
            assert task.status == status


class TestBlockerInfo:
    def test_create_defaults(self):
        blocker = BlockerInfo(description="Waiting for API key")
        assert blocker.severity == "medium"
        assert blocker.created_at != ""

    def test_invalid_severity_defaults(self):
        blocker = BlockerInfo(description="Test", severity="unknown")
        assert blocker.severity == "medium"


class TestWorkingState:
    def test_empty_state(self):
        state = WorkingState()
        assert state.current_task is None
        assert state.context == []
        assert state.has_active_task() is False
        assert state.has_blockers() is False

    def test_has_active_task(self):
        state = WorkingState(
            current_task=TaskInfo(title="Active", status="in_progress")
        )
        assert state.has_active_task() is True

    def test_completed_task_not_active(self):
        state = WorkingState(
            current_task=TaskInfo(title="Done", status="completed")
        )
        assert state.has_active_task() is False

    def test_has_blockers(self):
        state = WorkingState(
            blockers=[BlockerInfo(description="blocked")]
        )
        assert state.has_blockers() is True

    def test_critical_blockers(self):
        state = WorkingState(
            blockers=[
                BlockerInfo(description="minor", severity="low"),
                BlockerInfo(description="critical issue", severity="critical"),
                BlockerInfo(description="another critical", severity="critical"),
            ]
        )
        critical = state.critical_blockers()
        assert len(critical) == 2


class TestWorkingMemory:
    def test_init_creates_dir(self, tmp_dir):
        subdir = os.path.join(tmp_dir, "agent-memory")
        memory = WorkingMemory("test-agent", subdir)
        assert os.path.isdir(subdir)

    def test_load_empty(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        state = memory.load()
        assert isinstance(state, WorkingState)
        assert state.current_task is None

    def test_set_and_load_task(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.set_task("Test task", "Description")
        state = memory.load()
        assert state.current_task is not None
        assert state.current_task.title == "Test task"
        assert state.current_task.status == "pending"

    def test_complete_task(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.set_task("Test task")
        memory.complete_task()
        state = memory.load()
        assert state.current_task.status == "completed"

    def test_complete_no_task(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.complete_task()  # Should not raise

    def test_add_blocker_updates_task_status(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.set_task("Test task")
        memory.add_blocker("Waiting for review", severity="high")
        state = memory.load()
        assert state.current_task.status == "blocked"
        assert len(state.blockers) == 1

    def test_clear_blockers_restores_status(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.set_task("Test task")
        memory.add_blocker("Blocker 1")
        memory.clear_blockers()
        state = memory.load()
        assert len(state.blockers) == 0
        assert state.current_task.status == "in_progress"

    def test_add_context(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.add_context("Organization type: Municipal")
        memory.add_context("Organization type: Municipal")  # duplicate, should not add
        state = memory.load()
        assert len(state.context) == 1

    def test_add_next_step(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.add_next_step("Review regulations")
        state = memory.load()
        assert "Review regulations" in state.next_steps

    def test_update_session(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.update_session("Analyzed data", "Found 4 insights")
        state = memory.load()
        assert len(state.session_history) == 1
        assert state.session_history[0].action == "Analyzed data"

    def test_add_file_modified(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.add_file_modified("src/main.py")
        state = memory.load()
        assert "src/main.py" in state.files_modified

    def test_add_decision(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        memory.load()
        memory.add_decision("Use PostgreSQL for persistence")
        state = memory.load()
        assert "Use PostgreSQL for persistence" in state.decisions_made

    def test_get_state_loads_if_needed(self, tmp_dir):
        memory = WorkingMemory("test-agent", tmp_dir)
        state = memory.get_state()
        assert isinstance(state, WorkingState)
