"""
OpenAI LLM Backend

Provides integration with OpenAI-compatible APIs (OpenAI, Azure OpenAI, etc.).
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


class OpenAIBackend(LLMBackend):
    """
    LLM backend for OpenAI-compatible APIs.

    Supports OpenAI, Azure OpenAI, and other providers implementing the
    OpenAI Chat Completions API.
    Default model: gpt-4o
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1/chat/completions",
    ):
        """
        Initialize OpenAI backend.

        Args:
            api_key: OpenAI API key. If None, reads from settings.OPENAI_API_KEY
            model: Model identifier (default: gpt-4o)
            base_url: API endpoint URL (default: official OpenAI endpoint)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.base_url = base_url

        if not self.api_key:
            raise LLMBackendError(
                "OPENAI_API_KEY is required",
                provider="openai",
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
        Generate a completion using OpenAI API.

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
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            **kwargs,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
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
                        f"OpenAI API error ({response.status_code}): {error_body}"
                    )
                    raise LLMBackendError(
                        f"OpenAI API returned status {response.status_code}: {error_body}",
                        provider="openai",
                        status_code=response.status_code,
                    )

                data = response.json()
                text = data["choices"][0]["message"]["content"]
                input_tokens = data["usage"]["prompt_tokens"]
                output_tokens = data["usage"]["completion_tokens"]

                latency_ms = (time.time() - start_time) * 1000

                return LLMResponse(
                    text=text,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    metadata={"provider": "openai"},
                )

        except httpx.TimeoutException as e:
            logger.error(f"OpenAI API timeout: {e}")
            raise LLMBackendError(
                "OpenAI API request timed out after 120s",
                provider="openai",
            )
        except httpx.RequestError as e:
            logger.error(f"OpenAI API request error: {e}")
            raise LLMBackendError(
                f"OpenAI API request failed: {e}",
                provider="openai",
            )
