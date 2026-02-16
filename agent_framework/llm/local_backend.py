"""
Local LLM Backend

Provides integration with local LLM servers (Ollama, vLLM, etc.).
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from agent_framework.llm.base_backend import LLMBackend, LLMResponse
from ano_core.errors import LLMBackendError

logger = logging.getLogger(__name__)


class LocalBackend(LLMBackend):
    """
    LLM backend for local model servers.

    Supports Ollama and vLLM endpoints. No API key required.
    Default endpoint: http://localhost:11434/api/generate (Ollama default)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/api/generate",
        model: str = "llama3.1:8b",
    ):
        """
        Initialize local LLM backend.

        Args:
            base_url: Local server endpoint URL
            model: Model identifier for the local server
        """
        self.base_url = base_url
        self.model = model

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion using a local LLM server.

        Args:
            system_prompt: System-level instructions
            user_prompt: User message
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters passed to the server

        Returns:
            LLMResponse with generated text and metadata

        Raises:
            LLMBackendError: If the server call fails
        """
        start_time = time.time()

        # Override model if provided in kwargs
        model = kwargs.pop("model", self.model)

        # Combine system and user prompts for Ollama
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        payload = {
            "model": model,
            "prompt": combined_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            **kwargs,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    timeout=300.0,  # Local models can be slower
                )

                if response.status_code != 200:
                    error_body = response.text
                    logger.error(
                        f"Local LLM server error ({response.status_code}): {error_body}"
                    )
                    raise LLMBackendError(
                        f"Local LLM server returned status {response.status_code}: {error_body}",
                        provider="local",
                        status_code=response.status_code,
                    )

                data = response.json()
                text = data.get("response", "")

                # Ollama provides token counts if available
                input_tokens = data.get("prompt_eval_count", 0)
                output_tokens = data.get("eval_count", 0)

                latency_ms = (time.time() - start_time) * 1000

                return LLMResponse(
                    text=text,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    metadata={
                        "provider": "local",
                        "base_url": self.base_url,
                    },
                )

        except httpx.TimeoutException as e:
            logger.error(f"Local LLM server timeout: {e}")
            raise LLMBackendError(
                "Local LLM server request timed out after 300s",
                provider="local",
            )
        except httpx.RequestError as e:
            logger.error(f"Local LLM server request error: {e}")
            raise LLMBackendError(
                f"Local LLM server request failed: {e}. Is the server running at {self.base_url}?",
                provider="local",
            )
