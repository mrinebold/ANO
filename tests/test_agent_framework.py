"""Tests for agent_framework module — BaseAgent, LLM backends, context, IO."""

from __future__ import annotations

from datetime import datetime

import pytest

from agent_framework.base_agent import BaseAgent
from agent_framework.llm.base_backend import LLMBackend, LLMResponse
from ano_core.errors import AgentExecutionError
from ano_core.types import AgentContext, AgentInput, AgentMetadata, AgentOutput, OrgProfile

from tests.conftest import MockLLMBackend


class ConcreteAgent(BaseAgent):
    """Concrete agent for testing BaseAgent functionality."""

    agent_name = "test-agent"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are a test agent."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        response = await self.call_llm(input_data.data.get("query", ""))
        return AgentOutput(
            result=self.parse_json_response(response),
            metadata=self.get_metadata(),
        )


class TestBaseAgent:
    def test_init(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        assert agent.agent_name == "test-agent"
        assert agent.version == "1.0.0"
        assert agent._llm_call_count == 0

    @pytest.mark.asyncio
    async def test_execute(self, sample_context, sample_input, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        result = await agent.execute(sample_input)
        assert result.result == {"result": "test"}
        assert result.metadata.agent_name == "test-agent"

    @pytest.mark.asyncio
    async def test_call_llm_tracks_usage(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        await agent.call_llm("test prompt")
        assert agent._llm_call_count == 1
        assert agent._total_input_tokens == 100
        assert agent._total_output_tokens == 50

    @pytest.mark.asyncio
    async def test_call_llm_multiple(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        await agent.call_llm("prompt 1")
        await agent.call_llm("prompt 2")
        assert agent._llm_call_count == 2
        assert agent._total_input_tokens == 200

    @pytest.mark.asyncio
    async def test_call_llm_passes_params(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        await agent.call_llm("test", max_tokens=1000, temperature=0.7)
        assert mock_llm.calls[0]["max_tokens"] == 1000
        assert mock_llm.calls[0]["temperature"] == 0.7

    def test_parse_json_response_valid(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        result = agent.parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_response_markdown_block(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        result = agent.parse_json_response('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_response_plain_block(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        result = agent.parse_json_response('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_parse_json_response_invalid(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        result = agent.parse_json_response("not json at all")
        assert "raw_text" in result

    def test_attach_policy(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        hook = lambda: None
        agent.attach_policy(hook)
        assert len(agent._policy_hooks) == 1

    def test_get_metadata(self, sample_context, mock_llm):
        agent = ConcreteAgent(context=sample_context, llm=mock_llm)
        meta = agent.get_metadata()
        assert meta.agent_name == "test-agent"
        assert meta.version == "1.0.0"
        assert meta.completed_at is not None
        assert meta.llm_calls == 0

    @pytest.mark.asyncio
    async def test_llm_failure_raises(self, sample_context):
        class FailingBackend(LLMBackend):
            async def complete(self, **kwargs) -> LLMResponse:
                raise Exception("API down")

        agent = ConcreteAgent(context=sample_context, llm=FailingBackend())
        with pytest.raises(AgentExecutionError):
            await agent.call_llm("test")


class TestLLMResponse:
    def test_create(self):
        resp = LLMResponse(
            text="Hello",
            model="claude-sonnet-4-5-20250929",
            input_tokens=50,
            output_tokens=25,
            latency_ms=150.5,
        )
        assert resp.text == "Hello"
        assert resp.model == "claude-sonnet-4-5-20250929"
        assert resp.metadata is None

    def test_create_with_metadata(self):
        resp = LLMResponse(
            text="Hello",
            model="gpt-4",
            input_tokens=50,
            output_tokens=25,
            latency_ms=150.5,
            metadata={"stop_reason": "end_turn"},
        )
        assert resp.metadata["stop_reason"] == "end_turn"
