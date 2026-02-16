"""
LLM Backend Abstraction Layer

Provides pluggable LLM backends for the ANO agent framework.
"""

from agent_framework.llm.anthropic_backend import AnthropicBackend
from agent_framework.llm.base_backend import LLMBackend, LLMResponse, get_default_backend
from agent_framework.llm.local_backend import LocalBackend
from agent_framework.llm.openai_backend import OpenAIBackend

__all__ = [
    "LLMBackend",
    "LLMResponse",
    "AnthropicBackend",
    "OpenAIBackend",
    "LocalBackend",
    "get_default_backend",
]
