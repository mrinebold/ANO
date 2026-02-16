"""
Anthropic LLM Backend

Provides integration with Anthropic's Claude models via the Messages API.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from agent_framework.llm.base_backend import LLMBackend, LLMResponse
from ano_core.errors import LLMBackendError
from ano_core.settings import settings

logger = logging.getLogger(__name__)


class AnthropicBackend(LLMBackend):
    """
    LLM backend for Anthropic Claude models.

    Uses the Anthropic Messages API for completion generation.
    Default model: claude-sonnet-4-5-20250929
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str = "https://api.anthropic.com/v1/messages",
    ):
        """
        Initialize Anthropic backend.

        Args:
            api_key: Anthropic API key. If None, reads from settings.ANTHROPIC_API_KEY
            model: Model identifier. If None, uses settings.DEFAULT_LLM_MODEL
            base_url: API endpoint URL (default: official Anthropic endpoint)
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.DEFAULT_LLM_MODEL
        self.base_url = base_url

        if not self.api_key:
            raise LLMBackendError(
                "ANTHROPIC_API_KEY is required",
                provider="anthropic",
            )

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion using Claude.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters passed to the API

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            LLMBackendError: If the API call fails
        """
        start_time = time.time()

        # Override model if provided in kwargs
        model = kwargs.pop("model", self.model)

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            **kwargs,
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )

                if response.status_code != 200:
                    error_body = response.text
                    logger.error(
                        f"Anthropic API error ({response.status_code}): {error_body}"
                    )
                    raise LLMBackendError(
                        f"Anthropic API returned status {response.status_code}: {error_body}",
                        provider="anthropic",
                        status_code=response.status_code,
                    )

                data = response.json()
                text = data["content"][0]["text"]
                input_tokens = data["usage"]["input_tokens"]
                output_tokens = data["usage"]["output_tokens"]

                latency_ms = (time.time() - start_time) * 1000

                return LLMResponse(
                    text=text,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    metadata={"provider": "anthropic"},
                )

        except httpx.TimeoutException as e:
            logger.error(f"Anthropic API timeout: {e}")
            raise LLMBackendError(
                "Anthropic API request timed out after 120s",
                provider="anthropic",
            )
        except httpx.RequestError as e:
            logger.error(f"Anthropic API request error: {e}")
            raise LLMBackendError(
                f"Anthropic API request failed: {e}",
                provider="anthropic",
            )
