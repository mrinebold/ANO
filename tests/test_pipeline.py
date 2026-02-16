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
