"""Tests for agents module — CEO, CTO, AgentBuilder, ChatAdvisor."""

from __future__ import annotations

import pytest

from agents.agent_builder.agent import AgentBuilderAgent
from agents.agent_builder.certification import CertificationEngine, RESERVED_NAMES
from agents.agent_builder.schemas import (
    AgentSpec,
    Capability,
    CapabilityCategory,
    CheckResult,
    OnboardingResult,
    PersonalitySpec,
    PolicyAttachment,
    RegistryEntry,
    ReportingRelationship,
    TeamType,
)
from agents.ceo.agent import CEOAdvisorAgent
from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput

from tests.conftest import MockLLMBackend


def _make_valid_spec(**overrides) -> AgentSpec:
    """Create a valid AgentSpec with sensible defaults."""
    defaults = dict(
        name="data_analyst",
        display_name="Data Analyst",
        role="Analyze data and generate insights",
        team=TeamType.DEVELOPMENT,
        capabilities=[
            Capability(
                name="data-analysis",
                category=CapabilityCategory.ANALYSIS,
                description="Analyze datasets",
            )
        ],
        reporting=ReportingRelationship(reports_to="cto_advisor"),
        personality=PersonalitySpec(description="Analytical and detail-oriented"),
        description="A data analyst agent that processes datasets and generates insights.",
    )
    defaults.update(overrides)
    return AgentSpec(**defaults)


# --- AgentSpec Validation ---


class TestAgentSpec:
    def test_valid_spec(self):
        spec = _make_valid_spec()
        assert spec.name == "data_analyst"
        assert spec.team == TeamType.DEVELOPMENT

    def test_name_too_short(self):
        with pytest.raises(ValueError):
            _make_valid_spec(name="ab")

    def test_name_not_lowercase(self):
        with pytest.raises(ValueError):
            _make_valid_spec(name="DataAnalyst")

    def test_name_invalid_chars(self):
        with pytest.raises(ValueError):
            _make_valid_spec(name="data analyst!")

    def test_no_capabilities_raises(self):
        with pytest.raises(ValueError):
            _make_valid_spec(capabilities=[])


# --- CertificationEngine ---


class TestCertificationEngine:
    def test_certify_valid_spec(self):
        engine = CertificationEngine()
        spec = _make_valid_spec()
        report = engine.certify(spec)
        assert report.overall_passed is True
        assert report.score > 0.5

    def test_certify_duplicate_name(self):
        engine = CertificationEngine(existing_agent_names=["data_analyst"])
        spec = _make_valid_spec()
        report = engine.certify(spec)
        assert report.overall_passed is False

    def test_certify_reserved_name(self):
        engine = CertificationEngine()
        spec = _make_valid_spec(name="admin")
        report = engine.certify(spec)
        assert report.overall_passed is False

    def test_reserved_names_list(self):
        assert "base" in RESERVED_NAMES
        assert "system" in RESERVED_NAMES
        assert "admin" in RESERVED_NAMES

    def test_certify_no_personality_warns(self):
        engine = CertificationEngine()
        spec = _make_valid_spec(personality=None)
        report = engine.certify(spec)
        # Should still pass (warning, not error)
        assert report.overall_passed is True
        assert len(report.warnings) > 0

    def test_certify_no_reporting_warns(self):
        engine = CertificationEngine()
        spec = _make_valid_spec(
            reporting=ReportingRelationship()
        )
        report = engine.certify(spec)
        assert report.overall_passed is True

    def test_check_count(self):
        engine = CertificationEngine()
        spec = _make_valid_spec()
        report = engine.certify(spec)
        # 6 required + 5 advisory + 1 info = 12
        assert len(report.checks) == 12


# --- AgentBuilderAgent ---


class TestAgentBuilderAgent:
    def test_init(self):
        builder = AgentBuilderAgent()
        assert builder.agent_name == "agent_builder"
        assert len(builder.existing_agents) == 0

    def test_init_with_existing(self):
        builder = AgentBuilderAgent(existing_agents=["ceo", "cto"])
        assert len(builder.existing_agents) == 2

    def test_validate_valid_spec(self):
        builder = AgentBuilderAgent()
        spec = _make_valid_spec()
        errors = builder.validate(spec)
        assert errors == []

    def test_certify(self):
        builder = AgentBuilderAgent()
        spec = _make_valid_spec()
        report = builder.certify(spec)
        assert report.overall_passed is True

    def test_generate(self):
        builder = AgentBuilderAgent()
        spec = _make_valid_spec()
        files = builder.generate(spec)
        assert len(files) == 3  # agent.py, __init__.py, skill.md
        assert any("agent.py" in path for path in files.keys())
        assert any("skill.md" in path for path in files.keys())

    def test_register(self):
        builder = AgentBuilderAgent()
        entry = RegistryEntry(
            name="test_agent",
            display_name="Test Agent",
            capabilities=["testing"],
            team="development",
            specialization="Testing",
        )
        assert builder.register(entry) is True
        assert "test_agent" in builder.existing_agents

    def test_register_duplicate(self):
        builder = AgentBuilderAgent(existing_agents=["test_agent"])
        entry = RegistryEntry(
            name="test_agent",
            display_name="Test Agent",
            capabilities=["testing"],
            team="development",
            specialization="Testing",
        )
        assert builder.register(entry) is False

    def test_wire_hierarchy(self):
        builder = AgentBuilderAgent()
        spec = _make_valid_spec(
            reporting=ReportingRelationship(reports_to="cto_advisor")
        )
        changes = builder.wire_hierarchy(spec)
        assert changes["reports_to"] == "cto_advisor"
        hierarchy = builder.get_hierarchy()
        assert "data_analyst" in hierarchy.get("cto_advisor", [])

    def test_onboard_success(self):
        builder = AgentBuilderAgent()
        spec = _make_valid_spec()
        result = builder.onboard(spec)
        assert result.success is True
        assert result.registry_entry is not None
        assert len(result.generated_files) == 3

    def test_onboard_duplicate_fails(self):
        builder = AgentBuilderAgent(existing_agents=["data_analyst"])
        spec = _make_valid_spec()
        result = builder.onboard(spec)
        assert result.success is False
        assert "already exists" in result.error or "Certification failed" in result.error


# --- CEOAdvisorAgent ---


class TestCEOAdvisorAgent:
    @pytest.mark.asyncio
    async def test_execute(self, sample_context):
        llm = MockLLMBackend(
            response_text='{"analysis": "Strategic overview", "recommendations": [], "risks": [], "next_steps": []}'
        )
        agent = CEOAdvisorAgent(context=sample_context, llm=llm)
        input_data = AgentInput(
            data={"question": "Should we expand to new markets?"},
            context=sample_context,
        )
        result = await agent.execute(input_data)
        assert "analysis" in result.result
        assert result.metadata.agent_name == "ceo_advisor"

    @pytest.mark.asyncio
    async def test_missing_question_raises(self, sample_context):
        llm = MockLLMBackend()
        agent = CEOAdvisorAgent(context=sample_context, llm=llm)
        input_data = AgentInput(
            data={},  # No question
            context=sample_context,
        )
        with pytest.raises(AgentExecutionError):
            await agent.execute(input_data)

    def test_system_prompt(self, sample_context):
        llm = MockLLMBackend()
        agent = CEOAdvisorAgent(context=sample_context, llm=llm)
        prompt = agent.get_system_prompt()
        assert "CEO" in prompt
        assert "strategic" in prompt.lower()

    def test_validate_result_fills_defaults(self, sample_context):
        llm = MockLLMBackend()
        agent = CEOAdvisorAgent(context=sample_context, llm=llm)
        result = agent._validate_result({})
        assert "analysis" in result
        assert "recommendations" in result
        assert "risks" in result
        assert "next_steps" in result
