"""Shared fixtures for ANO Foundation tests."""

from __future__ import annotations

import os
import tempfile
from unittest.mock import AsyncMock

import pytest

from agent_framework.llm.base_backend import LLMBackend, LLMResponse
from ano_core.types import AgentContext, AgentInput, OrgProfile


# Ensure test environment
os.environ.setdefault("ANO_ENV", "development")
os.environ.setdefault("ANO_PROFILE", "minimal")


class MockLLMBackend(LLMBackend):
    """Mock LLM backend for testing without real API calls."""

    def __init__(self, response_text: str = '{"result": "test"}'):
        self.response_text = response_text
        self.calls: list[dict] = []

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs,
    ) -> LLMResponse:
        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        })
        return LLMResponse(
            text=self.response_text,
            model="mock-model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=10.0,
        )


@pytest.fixture
def mock_llm():
    """Provide a mock LLM backend."""
    return MockLLMBackend()


@pytest.fixture
def sample_org_profile():
    """Provide a sample organization profile."""
    return OrgProfile(
        org_name="Test Organization",
        org_type="enterprise",
        state="California",
        industry="Technology",
        size="100-500",
    )


@pytest.fixture
def sample_context(sample_org_profile):
    """Provide a sample agent context."""
    return AgentContext(org_profile=sample_org_profile)


@pytest.fixture
def sample_input(sample_context):
    """Provide a sample agent input."""
    return AgentInput(
        data={"query": "Test query"},
        context=sample_context,
    )


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as d:
        yield d
