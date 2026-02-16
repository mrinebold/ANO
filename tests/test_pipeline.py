"""Tests for pipeline module — Pipeline, Stage, PipelineResult."""

from __future__ import annotations

import pytest

from pipeline.pipeline import Pipeline, PipelineResult, Stage


class TestStage:
    def test_create(self):
        stage = Stage(name="research", agents=["researcher"])
        assert stage.name == "research"
        assert stage.agents == ["researcher"]
        assert stage.parallel is False
        assert stage.required is True

    def test_empty_agents_raises(self):
        with pytest.raises(ValueError, match="at least one agent"):
            Stage(name="empty", agents=[])

    def test_parallel_with_multiple_agents(self):
        stage = Stage(
            name="drafting",
            agents=["drafter", "compliance"],
            parallel=True,
        )
        assert stage.parallel is True
        assert len(stage.agents) == 2


class TestPipelineResult:
    def test_successful(self):
        result = PipelineResult(
            success=True,
            stages_completed=["research", "drafting"],
            outputs={"researcher": {"data": "found"}},
            duration_ms=1500.0,
        )
        assert result.success is True
        assert result.total_stages == 2
        assert result.get_agent_output("researcher") == {"data": "found"}
        assert result.get_agent_output("nonexistent") is None

    def test_failed(self):
        result = PipelineResult(
            success=False,
            stages_completed=["research"],
            stages_failed=["drafting"],
            error="Drafter agent failed",
        )
        assert result.success is False
        assert result.total_stages == 2
        assert result.error is not None


class TestPipeline:
    def test_create(self):
        stages = [
            Stage(name="research", agents=["researcher"]),
            Stage(name="review", agents=["ceo"]),
        ]
        pipeline = Pipeline("test-pipeline", stages)
        assert pipeline.name == "test-pipeline"
        assert len(pipeline.stages) == 2

    def test_empty_stages_raises(self):
        with pytest.raises(ValueError, match="at least one stage"):
            Pipeline("empty", [])

    def test_duplicate_stage_names_raises(self):
        stages = [
            Stage(name="research", agents=["a1"]),
            Stage(name="research", agents=["a2"]),
        ]
        with pytest.raises(ValueError, match="duplicate stage names"):
            Pipeline("dupe", stages)

    def test_stage_names(self):
        stages = [
            Stage(name="step1", agents=["a1"]),
            Stage(name="step2", agents=["a2"]),
            Stage(name="step3", agents=["a3"]),
        ]
        pipeline = Pipeline("ordered", stages)
        assert pipeline.stage_names == ["step1", "step2", "step3"]

    def test_total_agents(self):
        stages = [
            Stage(name="step1", agents=["a1", "a2"]),
            Stage(name="step2", agents=["a3"]),
        ]
        pipeline = Pipeline("multi", stages)
        assert pipeline.total_agents == 3

    def test_get_stage(self):
        stages = [
            Stage(name="research", agents=["a1"]),
            Stage(name="review", agents=["a2"]),
        ]
        pipeline = Pipeline("lookup", stages)
        stage = pipeline.get_stage("research")
        assert stage is not None
        assert stage.agents == ["a1"]

    def test_get_stage_not_found(self):
        stages = [Stage(name="research", agents=["a1"])]
        pipeline = Pipeline("lookup", stages)
        assert pipeline.get_stage("nonexistent") is None

    def test_repr(self):
        stages = [Stage(name="s1", agents=["a1", "a2"])]
        pipeline = Pipeline("test", stages)
        rep = repr(pipeline)
        assert "test" in rep
        assert "stages=1" in rep
        assert "agents=2" in rep


# --- PipelineCoordinator Integration Tests ---

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from ano_core.environment import EnvironmentTier
from ano_core.errors import PolicyViolationError
from ano_core.types import (
    AgentContext,
    AgentInput,
    AgentMetadata,
    AgentOutput,
    OrgProfile,
    PolicyViolation,
)
from pipeline.coordinator import PipelineCoordinator
from policy.engine import PolicyDecision, PolicyEngine
from policy.hooks import HookResult, PolicyHook


def _make_context():
    return AgentContext(
        org_profile=OrgProfile(
            org_name="Test Org",
            org_type="enterprise",
        )
    )


def _make_output():
    return AgentOutput(
        result={"answer": "42"},
        metadata=AgentMetadata(
            agent_name="test-agent",
            version="1.0.0",
            started_at=datetime(2026, 1, 1),
            tokens_used=100,
        ),
    )


def _make_registry(agent_names: list[str]):
    """Create a mock registry that returns mock agents."""
    registry = MagicMock()
    agents = {}
    for name in agent_names:
        agent = AsyncMock()
        agent.execute = AsyncMock(return_value=_make_output())
        agents[name] = agent

    def get_agent(name):
        return agents.get(name)

    registry.get_agent = get_agent

    # validate returns empty list (no missing agents)
    registry.has = lambda name: name in agents
    return registry


class TestPipelineCoordinator:
    @pytest.mark.asyncio
    async def test_basic_execution_no_policy(self):
        """Coordinator executes agents without policy engine."""
        pipeline = Pipeline("simple", [Stage(name="step1", agents=["agent-a"])])
        registry = _make_registry(["agent-a"])
        coordinator = PipelineCoordinator(pipeline, registry)

        result = await coordinator.run({"query": "test"}, _make_context())
        assert result.success is True
        assert "agent-a" in result.outputs

    @pytest.mark.asyncio
    async def test_policy_pre_check_allows(self):
        """Coordinator calls evaluate_pre and proceeds when allowed."""
        pipeline = Pipeline("checked", [Stage(name="step1", agents=["agent-a"])])
        registry = _make_registry(["agent-a"])

        engine = AsyncMock(spec=PolicyEngine)
        engine.evaluate_pre = AsyncMock(return_value=PolicyDecision(allowed=True))
        engine.evaluate_post = AsyncMock(return_value=PolicyDecision(allowed=True))

        coordinator = PipelineCoordinator(pipeline, registry, policy_engine=engine)
        result = await coordinator.run({"query": "test"}, _make_context())

        assert result.success is True
        engine.evaluate_pre.assert_called_once()
        engine.evaluate_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_policy_pre_check_blocks(self):
        """PolicyDecision(allowed=False) raises PolicyViolationError."""
        pipeline = Pipeline("blocked", [Stage(name="step1", agents=["agent-a"])])
        registry = _make_registry(["agent-a"])

        violation = PolicyViolation(
            gate="test-success",
            severity="error",
            message="Tests failed",
            remediation="Fix tests",
        )
        engine = AsyncMock(spec=PolicyEngine)
        engine.evaluate_pre = AsyncMock(
            return_value=PolicyDecision(allowed=False, violations=[violation])
        )

        coordinator = PipelineCoordinator(pipeline, registry, policy_engine=engine)
        result = await coordinator.run({"query": "test"}, _make_context())

        # Pipeline should fail because the required stage raised PolicyViolationError
        assert result.success is False
        assert "step1" in result.stages_failed

    @pytest.mark.asyncio
    async def test_hooks_invoked_in_order(self):
        """Hooks fire before_execute then after_execute in order."""
        pipeline = Pipeline("hooked", [Stage(name="step1", agents=["agent-a"])])
        registry = _make_registry(["agent-a"])

        call_log = []

        class TrackingHook(PolicyHook):
            def __init__(self, tag: str):
                super().__init__(name=f"tracking-{tag}")
                self.tag = tag

            async def before_execute(self, agent_name, input_data):
                call_log.append(f"before-{self.tag}")
                return HookResult(proceed=True)

            async def after_execute(self, agent_name, output):
                call_log.append(f"after-{self.tag}")
                return HookResult(proceed=True)

        hooks = [TrackingHook("A"), TrackingHook("B")]
        coordinator = PipelineCoordinator(pipeline, registry, hooks=hooks)
        result = await coordinator.run({"query": "test"}, _make_context())

        assert result.success is True
        assert call_log == ["before-A", "before-B", "after-A", "after-B"]

    @pytest.mark.asyncio
    async def test_hook_blocks_execution(self):
        """A hook returning proceed=False blocks agent execution."""
        pipeline = Pipeline("hook-block", [Stage(name="step1", agents=["agent-a"])])
        registry = _make_registry(["agent-a"])

        class BlockingHook(PolicyHook):
            def __init__(self):
                super().__init__(name="blocker")

            async def before_execute(self, agent_name, input_data):
                return HookResult(proceed=False, message="Blocked by policy")

            async def after_execute(self, agent_name, output):
                return HookResult(proceed=True)

        coordinator = PipelineCoordinator(
            pipeline, registry, hooks=[BlockingHook()]
        )
        result = await coordinator.run({"query": "test"}, _make_context())

        assert result.success is False
        assert "step1" in result.stages_failed
