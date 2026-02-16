"""
Agent Registry

Central registration system for agents in the ANO framework. Provides
metadata-driven agent discovery, capability tracking, and team organization.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ano_core.errors import RegistryError

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadataEntry:
    """
    Metadata entry for a registered agent.

    Captures agent identity, capabilities, team membership, and optional
    input/output schemas for validation.
    """

    name: str
    team: str  # "executive", "development", "operations", etc.
    version: str
    capabilities: list[str]
    description: str = ""
    input_schema: Optional[dict[str, Any]] = None
    output_schema: Optional[dict[str, Any]] = None
    reporting_to: Optional[str] = None  # Name of supervisor agent


class AgentRegistry:
    """
    Central registry for all agents in the ANO.

    Provides registration, lookup, and discovery operations for agents.
    Maintains bidirectional mapping between agent names and classes,
    along with their metadata.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._agents: dict[str, type] = {}
        self._metadata: dict[str, AgentMetadataEntry] = {}
        logger.debug("Initialized AgentRegistry")

    def register(self, agent_class: type, metadata: AgentMetadataEntry) -> None:
        """
        Register an agent class with its metadata.

        Args:
            agent_class: The agent class to register
            metadata: Metadata describing the agent's capabilities and structure

        Raises:
            RegistryError: If agent name is already registered
        """
        if metadata.name in self._agents:
            raise RegistryError(
                f"Agent '{metadata.name}' is already registered",
                agent_name=metadata.name,
            )

        self._agents[metadata.name] = agent_class
        self._metadata[metadata.name] = metadata
        logger.info(
            f"Registered agent '{metadata.name}' (team={metadata.team}, "
            f"version={metadata.version}, capabilities={len(metadata.capabilities)})"
        )

    def get(self, name: str) -> type:
        """
        Retrieve an agent class by name.

        Args:
            name: Agent name to look up

        Returns:
            The agent class

        Raises:
            RegistryError: If agent is not registered
        """
        if name not in self._agents:
            raise RegistryError(
                f"Agent '{name}' not found in registry",
                agent_name=name,
                available_agents=list(self._agents.keys()),
            )
        return self._agents[name]

    def get_metadata(self, name: str) -> AgentMetadataEntry:
        """
        Retrieve metadata for a registered agent.

        Args:
            name: Agent name to look up

        Returns:
            The agent's metadata entry

        Raises:
            RegistryError: If agent is not registered
        """
        if name not in self._metadata:
            raise RegistryError(
                f"Agent '{name}' not found in registry",
                agent_name=name,
                available_agents=list(self._metadata.keys()),
            )
        return self._metadata[name]

    def list_agents(
        self,
        team: Optional[str] = None,
        capability: Optional[str] = None,
    ) -> list[AgentMetadataEntry]:
        """
        List registered agents, optionally filtered by team or capability.

        Args:
            team: Filter by team name (e.g., "executive", "development")
            capability: Filter by capability name (e.g., "strategy", "qa")

        Returns:
            List of metadata entries matching the filters
        """
        results = list(self._metadata.values())

        if team:
            results = [m for m in results if m.team == team]

        if capability:
            results = [m for m in results if capability in m.capabilities]

        logger.debug(
            f"Listed {len(results)} agents (team={team}, capability={capability})"
        )
        return results

    def has(self, name: str) -> bool:
        """
        Check if an agent is registered.

        Args:
            name: Agent name to check

        Returns:
            True if agent is registered, False otherwise
        """
        return name in self._agents

    def unregister(self, name: str) -> None:
        """
        Unregister an agent.

        Args:
            name: Agent name to unregister

        Raises:
            RegistryError: If agent is not registered
        """
        if name not in self._agents:
            raise RegistryError(
                f"Agent '{name}' not found in registry",
                agent_name=name,
            )

        del self._agents[name]
        del self._metadata[name]
        logger.info(f"Unregistered agent '{name}'")


# Module-level singleton registry
_global_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.

    Returns:
        The singleton AgentRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


def register_agent(**metadata_kwargs: Any) -> Callable[[type], type]:
    """
    Decorator to register an agent with metadata.

    Usage:
        @register_agent(
            name="strategy-advisor",
            team="executive",
            version="1.0.0",
            capabilities=["strategy", "planning"],
            description="Strategic planning and analysis agent"
        )
        class StrategyAdvisorAgent:
            ...

    Args:
        **metadata_kwargs: Keyword arguments to construct AgentMetadataEntry

    Returns:
        Decorator function that registers the agent class
    """

    def decorator(agent_class: type) -> type:
        # Store metadata on the class for later discovery
        metadata = AgentMetadataEntry(**metadata_kwargs)
        agent_class._agent_metadata = metadata  # type: ignore

        # Optionally auto-register if registry is available
        try:
            registry = get_registry()
            registry.register(agent_class, metadata)
        except Exception as e:
            logger.debug(f"Deferred registration for {metadata.name}: {e}")

        return agent_class

    return decorator
