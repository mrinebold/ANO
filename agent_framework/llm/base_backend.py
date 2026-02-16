"""
LLM Backend Base Classes

Defines the abstract interface for LLM backends and shared response types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ano_core.errors import LLMBackendError


@dataclass
class LLMResponse:
    """
    Response from an LLM backend.

    Contains the generated text, model information, token usage, and
    timing metrics for observability and cost tracking.
    """

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    metadata: dict[str, Any] | None = None


class LLMBackend(ABC):
    """
    Abstract base class for LLM backends.

    Implementations provide concrete integrations with LLM providers
    (Anthropic, OpenAI, local models, etc.).
    """

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            system_prompt: System-level instructions for the LLM
            user_prompt: User message / task description
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            **kwargs: Backend-specific parameters

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            LLMBackendError: If the LLM call fails
        """
        pass


def get_default_backend() -> LLMBackend:
    """
    Get the default LLM backend based on settings.

    Reads DEFAULT_LLM_PROVIDER from settings and returns the appropriate
    backend instance (Anthropic, OpenAI, or Local).

    Returns:
        Configured LLM backend instance

    Raises:
        ConfigurationError: If provider is invalid or API keys are missing
    """
    from ano_core.errors import ConfigurationError
    from ano_core.settings import settings

    provider = settings.DEFAULT_LLM_PROVIDER.lower()

    if provider == "anthropic":
        from agent_framework.llm.anthropic_backend import AnthropicBackend

        if not settings.ANTHROPIC_API_KEY:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY is required when DEFAULT_LLM_PROVIDER=anthropic"
            )
        return AnthropicBackend()

    elif provider == "openai":
        from agent_framework.llm.openai_backend import OpenAIBackend

        if not settings.OPENAI_API_KEY:
            raise ConfigurationError(
                "OPENAI_API_KEY is required when DEFAULT_LLM_PROVIDER=openai"
            )
        return OpenAIBackend()

    elif provider == "local":
        from agent_framework.llm.local_backend import LocalBackend

        return LocalBackend()

    else:
        raise ConfigurationError(
            f"Unknown LLM provider '{provider}'. "
            "Valid options: anthropic, openai, local"
        )
