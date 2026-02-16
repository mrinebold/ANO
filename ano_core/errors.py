"""
ANO Error Hierarchy

Defines exception classes for structured error handling throughout
the ANO framework.
"""

from typing import Any, Optional


class ANOError(Exception):
    """
    Base exception for all ANO framework errors.

    All ANO-specific exceptions inherit from this class to enable
    framework-level error handling and reporting.
    """

    def __init__(self, message: str, **kwargs: Any):
        self.message = message
        self.extra = kwargs
        super().__init__(message)

    def __str__(self) -> str:
        if self.extra:
            extras = ", ".join(f"{k}={v}" for k, v in self.extra.items())
            return f"{self.message} ({extras})"
        return self.message


class AgentExecutionError(ANOError):
    """
    Error during agent execution.

    Raised when an agent fails to execute successfully, either due to
    internal errors or invalid inputs.
    """

    def __init__(self, message: str, agent_name: str, **kwargs: Any):
        self.agent_name = agent_name
        super().__init__(message, agent_name=agent_name, **kwargs)


class LLMBackendError(ANOError):
    """
    Error communicating with an LLM backend.

    Raised when LLM API calls fail due to network issues, rate limits,
    authentication problems, or service errors.
    """

    def __init__(
        self,
        message: str,
        provider: str,
        status_code: Optional[int] = None,
        **kwargs: Any,
    ):
        self.provider = provider
        self.status_code = status_code
        super().__init__(
            message, provider=provider, status_code=status_code, **kwargs
        )


class PolicyViolationError(ANOError):
    """
    Policy gate violation error.

    Raised when policy enforcement detects violations that prevent
    agent execution from continuing.
    """

    def __init__(self, message: str, violations: list[dict[str, Any]], **kwargs: Any):
        self.violations = violations
        super().__init__(message, violations=violations, **kwargs)


class RegistryError(ANOError):
    """
    Agent or resource registry lookup failure.

    Raised when attempting to load an agent, policy, or other registered
    resource that doesn't exist or fails validation.
    """

    pass


class ConfigurationError(ANOError):
    """
    Configuration or profile error.

    Raised when settings, profiles, or configuration files are invalid,
    missing required values, or contain conflicting options.
    """

    pass


class ChannelError(ANOError):
    """
    Deployment channel error.

    Raised when a deployment channel (Telegram, Web, CLI) fails to
    initialize, send messages, or handle user interactions.
    """

    pass
