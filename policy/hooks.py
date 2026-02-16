"""
Policy Hooks

Extension points for custom policy enforcement logic. Hooks can intercept
and modify agent execution flow at key lifecycle points.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class HookResult:
    """
    Result from executing a policy hook.

    Indicates whether execution should proceed and optionally provides
    modified data or context messages.
    """

    proceed: bool
    message: str = ""
    modified_data: Optional[dict[str, Any]] = None


class PolicyHook(ABC):
    """
    Base class for policy hooks.

    Hooks provide extension points in the agent execution lifecycle,
    allowing custom logic to run before and after agent execution.
    """

    def __init__(self, name: str):
        """
        Initialize a policy hook.

        Args:
            name: Hook identifier (e.g., "audit-logging", "data-sanitization")
        """
        self.name = name

    @abstractmethod
    async def before_execute(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> HookResult:
        """
        Hook called before agent execution.

        Can inspect, validate, or modify input data before the agent runs.
        Can block execution by returning HookResult(proceed=False).

        Args:
            agent_name: Name of the agent about to execute
            input_data: Input data for the agent

        Returns:
            HookResult indicating whether to proceed and optional modifications
        """
        pass

    @abstractmethod
    async def after_execute(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> HookResult:
        """
        Hook called after agent execution.

        Can inspect, validate, or modify agent output. Can reject output
        by returning HookResult(proceed=False).

        Args:
            agent_name: Name of the agent that executed
            output: Output data from the agent

        Returns:
            HookResult indicating whether to accept output and optional modifications
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class AuditLoggingHook(PolicyHook):
    """
    Audit logging hook.

    Logs all agent executions for compliance, debugging, and security
    monitoring purposes.
    """

    def __init__(self):
        super().__init__(name="audit-logging")

    async def before_execute(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> HookResult:
        """Log agent execution start."""
        logger.info(
            f"AUDIT: Agent '{agent_name}' starting execution",
            extra={
                "agent_name": agent_name,
                "input_keys": list(input_data.keys()),
                "phase": "pre-execution",
            },
        )

        return HookResult(proceed=True, message="Audit logged")

    async def after_execute(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> HookResult:
        """Log agent execution completion."""
        logger.info(
            f"AUDIT: Agent '{agent_name}' completed execution",
            extra={
                "agent_name": agent_name,
                "output_keys": list(output.keys()),
                "phase": "post-execution",
            },
        )

        return HookResult(proceed=True, message="Audit logged")


class DataSanitizationHook(PolicyHook):
    """
    Data sanitization hook.

    Removes sensitive data (PII, credentials) from input before execution
    and from output before storage.
    """

    def __init__(self, sensitive_keys: Optional[list[str]] = None):
        super().__init__(name="data-sanitization")
        self.sensitive_keys = sensitive_keys or [
            "password",
            "api_key",
            "secret",
            "token",
            "ssn",
            "credit_card",
        ]

    async def before_execute(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> HookResult:
        """Sanitize input data."""
        modified = self._sanitize_dict(input_data.copy())
        return HookResult(
            proceed=True,
            message=f"Sanitized {len(self.sensitive_keys)} sensitive keys",
            modified_data=modified,
        )

    async def after_execute(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> HookResult:
        """Sanitize output data."""
        modified = self._sanitize_dict(output.copy())
        return HookResult(
            proceed=True,
            message=f"Sanitized {len(self.sensitive_keys)} sensitive keys",
            modified_data=modified,
        )

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize dictionary by redacting sensitive keys."""
        for key in list(data.keys()):
            if any(sensitive in key.lower() for sensitive in self.sensitive_keys):
                data[key] = "***REDACTED***"
            elif isinstance(data[key], dict):
                data[key] = self._sanitize_dict(data[key])
            elif isinstance(data[key], list):
                data[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in data[key]
                ]
        return data


class RateLimitHook(PolicyHook):
    """
    Rate limiting hook.

    Enforces rate limits on agent execution to prevent resource exhaustion
    and control costs.
    """

    def __init__(self, max_executions_per_minute: int = 60):
        super().__init__(name="rate-limiting")
        self.max_executions_per_minute = max_executions_per_minute
        self._execution_count: dict[str, list[float]] = {}

    async def before_execute(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> HookResult:
        """Check if agent is within rate limit."""
        import time

        now = time.time()

        # Initialize tracking for this agent if needed
        if agent_name not in self._execution_count:
            self._execution_count[agent_name] = []

        # Remove executions older than 1 minute
        self._execution_count[agent_name] = [
            ts for ts in self._execution_count[agent_name] if now - ts < 60
        ]

        # Check rate limit
        if len(self._execution_count[agent_name]) >= self.max_executions_per_minute:
            return HookResult(
                proceed=False,
                message=f"Rate limit exceeded: {self.max_executions_per_minute}/min",
            )

        # Record this execution
        self._execution_count[agent_name].append(now)

        return HookResult(
            proceed=True,
            message=f"Rate limit OK: {len(self._execution_count[agent_name])}/{self.max_executions_per_minute}",
        )

    async def after_execute(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> HookResult:
        """No post-execution rate limiting needed."""
        return HookResult(proceed=True)


class CostTrackingHook(PolicyHook):
    """
    Cost tracking hook.

    Monitors and logs LLM token usage and estimated costs for agent
    executions.
    """

    def __init__(self, cost_per_1k_tokens: float = 0.01):
        super().__init__(name="cost-tracking")
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self._total_cost = 0.0

    async def before_execute(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> HookResult:
        """No pre-execution cost tracking needed."""
        return HookResult(proceed=True)

    async def after_execute(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> HookResult:
        """Track costs from agent execution."""
        tokens_used = output.get("metadata", {}).get("tokens_used", 0)
        cost = (tokens_used / 1000) * self.cost_per_1k_tokens
        self._total_cost += cost

        logger.info(
            f"COST: Agent '{agent_name}' used {tokens_used} tokens "
            f"(${cost:.4f}). Total: ${self._total_cost:.4f}"
        )

        return HookResult(
            proceed=True,
            message=f"Cost tracked: ${cost:.4f}",
        )

    def get_total_cost(self) -> float:
        """Get total accumulated cost across all executions."""
        return self._total_cost

    def reset(self) -> None:
        """Reset cost tracking."""
        self._total_cost = 0.0
        logger.info("Cost tracking reset")
