"""
Registry Module

Central registration system for agents and capabilities in the ANO framework.

Provides:
- AgentRegistry: Central agent registration and lookup
- CapabilityRegistry: Capability tracking and discovery
- Discovery: Automatic agent loading from packages
- Decorators: @register_agent for declarative registration
"""

from registry.agent_registry import (
    AgentMetadataEntry,
    AgentRegistry,
    get_registry,
    register_agent,
)
from registry.capability_registry import (
    CapabilityEntry,
    CapabilityRegistry,
    get_capability_registry,
)
from registry.discovery import (
    auto_register_agents,
    discover_agents,
    discover_from_modules,
)

__all__ = [
    # Agent registry
    "AgentRegistry",
    "AgentMetadataEntry",
    "get_registry",
    "register_agent",
    # Capability registry
    "CapabilityRegistry",
    "CapabilityEntry",
    "get_capability_registry",
    # Discovery
    "discover_agents",
    "discover_from_modules",
    "auto_register_agents",
]
