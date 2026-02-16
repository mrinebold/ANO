"""
ANO Agent Framework

Core agent abstraction layer providing base agent functionality, LLM backends,
context management, and input/output validation.
"""

from agent_framework.base_agent import BaseAgent
from agent_framework.context import (
    ContextBuilder,
    render_org_context,
    render_regulatory_context,
)
from agent_framework.io import validate_input, validate_output
from agent_framework.llm import (
    AnthropicBackend,
    LLMBackend,
    LLMResponse,
    LocalBackend,
    OpenAIBackend,
    get_default_backend,
)

__all__ = [
    # Base Agent
    "BaseAgent",
    # LLM Backends
    "LLMBackend",
    "LLMResponse",
    "AnthropicBackend",
    "OpenAIBackend",
    "LocalBackend",
    "get_default_backend",
    # Context Management
    "ContextBuilder",
    "render_org_context",
    "render_regulatory_context",
    # I/O Validation
    "validate_input",
    "validate_output",
]
