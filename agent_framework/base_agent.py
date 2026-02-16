"""
Base Agent

Abstract base class for all agents in the ANO framework.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from agent_framework.llm.base_backend import LLMBackend, get_default_backend
from ano_core.errors import AgentExecutionError
from ano_core.types import AgentContext, AgentInput, AgentMetadata, AgentOutput

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all ANO agents.

    Provides common infrastructure for agent execution, LLM interaction,
    and policy enforcement. Concrete agents implement get_system_prompt()
    and execute() to define their specific behavior.

    Attributes:
        agent_name: Unique identifier for this agent type
        version: Agent version string (e.g., "1.0.0")
        input_schema: Optional JSON schema for input validation
        output_schema: Optional JSON schema for output validation
    """

    # Class-level metadata (override in subclasses)
    agent_name: str = "base"
    version: str = "1.0.0"
    input_schema: dict[str, Any] | None = None
    output_schema: dict[str, Any] | None = None

    def __init__(
        self,
        context: AgentContext,
        llm: LLMBackend | None = None,
    ):
        """
        Initialize the agent with execution context and LLM backend.

        Args:
            context: Execution context containing org profile and pipeline state
            llm: LLM backend to use. If None, will attempt to get default backend
                 on first LLM call.
        """
        self.context = context
        self._llm = llm  # Store as private, initialize lazily
        self.started_at = datetime.now()
        self._policy_hooks: list[Any] = []
        self._llm_call_count = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    @property
    def llm(self) -> LLMBackend:
        """Get the LLM backend, initializing default if needed."""
        if self._llm is None:
            self._llm = get_default_backend()
        return self._llm

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt for this agent.

        The system prompt defines the agent's role, capabilities, and behavior.
        Must be implemented by subclasses.

        Returns:
            System prompt string for LLM calls
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_system_prompt()"
        )

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent's primary task.

        Performs the agent's specialized function using the provided input
        and execution context. Must be implemented by subclasses.

        Args:
            input_data: Agent-specific input parameters

        Returns:
            AgentOutput with result data and metadata

        Raises:
            AgentExecutionError: If execution fails
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute()"
        )

    async def call_llm(
        self,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> str:
        """
        Call the LLM with the agent's system prompt and user prompt.

        Delegates to the configured LLM backend and tracks usage metrics.

        Args:
            user_prompt: The user/task prompt to send
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            **kwargs: Additional LLM-specific parameters

        Returns:
            Generated text from the LLM

        Raises:
            LLMBackendError: If the LLM call fails
        """
        system_prompt = self.get_system_prompt()

        try:
            response = await self.llm.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            # Track usage
            self._llm_call_count += 1
            self._total_input_tokens += response.input_tokens
            self._total_output_tokens += response.output_tokens

            logger.debug(
                f"{self.agent_name}: LLM call completed "
                f"({response.input_tokens} in, {response.output_tokens} out, "
                f"{response.latency_ms:.0f}ms)"
            )

            return response.text

        except Exception as e:
            logger.error(f"{self.agent_name}: LLM call failed: {e}")
            raise AgentExecutionError(
                f"LLM call failed: {e}",
                agent_name=self.agent_name,
            )

    def parse_json_response(self, text: str) -> dict[str, Any]:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Attempts to extract and parse JSON from the response text, with
        fallback to raw text if parsing fails.

        Args:
            text: Raw response text from LLM

        Returns:
            Parsed dict, or {"raw_text": text} if parsing fails
        """
        # Strip markdown code blocks if present
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(
                f"{self.agent_name}: Could not parse JSON response, returning raw text"
            )
            return {"raw_text": text}

    def attach_policy(self, hook: Any) -> None:
        """
        Attach a policy enforcement hook to this agent.

        Policy hooks are called during agent execution to enforce
        organizational policies and compliance requirements.

        Args:
            hook: Policy hook callable or object
        """
        self._policy_hooks.append(hook)
        logger.debug(f"{self.agent_name}: Attached policy hook {hook}")

    def get_metadata(self) -> AgentMetadata:
        """
        Get execution metadata for this agent.

        Returns:
            AgentMetadata with execution statistics
        """
        completed_at = datetime.now()
        duration_ms = (completed_at - self.started_at).total_seconds() * 1000

        return AgentMetadata(
            agent_name=self.agent_name,
            version=self.version,
            started_at=self.started_at,
            completed_at=completed_at,
            llm_calls=self._llm_call_count,
            tokens_used=self._total_input_tokens + self._total_output_tokens,
        )
