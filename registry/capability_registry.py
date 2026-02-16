"""
Capability Registry

Tracks capabilities provided by agents and enables capability-based
agent discovery. Supports many-to-many relationships between capabilities
and agents.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CapabilityEntry:
    """
    Metadata for a registered capability.

    Describes a capability, its purpose, and which agents provide it.
    """

    name: str
    description: str
    provided_by: list[str] = field(default_factory=list)  # Agent names
    category: str = ""


class CapabilityRegistry:
    """
    Registry for capabilities provided by agents.

    Maintains bidirectional mapping:
    - Capability -> Agents that provide it
    - Agent -> Capabilities it provides

    Supports categorization and discovery of capabilities.
    """

    def __init__(self) -> None:
        """Initialize empty capability registry."""
        self._capabilities: dict[str, CapabilityEntry] = {}
        self._agent_capabilities: dict[str, set[str]] = defaultdict(set)
        logger.debug("Initialized CapabilityRegistry")

    def register(
        self,
        capability: str,
        agent_name: str,
        description: str = "",
        category: str = "",
    ) -> None:
        """
        Register a capability provided by an agent.

        If the capability doesn't exist, it will be created. If it exists,
        the agent will be added to its provider list.

        Args:
            capability: Name of the capability (e.g., "qa", "security-scan")
            agent_name: Name of the agent providing this capability
            description: Human-readable description of the capability
            category: Optional category for grouping (e.g., "testing", "security")
        """
        if capability not in self._capabilities:
            self._capabilities[capability] = CapabilityEntry(
                name=capability,
                description=description,
                provided_by=[],
                category=category,
            )

        entry = self._capabilities[capability]

        # Add agent to providers if not already present
        if agent_name not in entry.provided_by:
            entry.provided_by.append(agent_name)

        # Track reverse mapping
        self._agent_capabilities[agent_name].add(capability)

        logger.debug(
            f"Registered capability '{capability}' for agent '{agent_name}' "
            f"(category={category})"
        )

    def get_providers(self, capability: str) -> list[str]:
        """
        Get list of agents that provide a capability.

        Args:
            capability: Capability name to look up

        Returns:
            List of agent names providing this capability (empty if not found)
        """
        if capability not in self._capabilities:
            logger.debug(f"Capability '{capability}' not found")
            return []

        return self._capabilities[capability].provided_by.copy()

    def get_capabilities(self, agent_name: str) -> list[str]:
        """
        Get list of capabilities provided by an agent.

        Args:
            agent_name: Agent name to look up

        Returns:
            List of capability names (empty if agent has none)
        """
        if agent_name not in self._agent_capabilities:
            logger.debug(f"Agent '{agent_name}' has no registered capabilities")
            return []

        return sorted(self._agent_capabilities[agent_name])

    def list_all(self) -> list[CapabilityEntry]:
        """
        List all registered capabilities.

        Returns:
            List of all CapabilityEntry instances
        """
        return list(self._capabilities.values())

    def get_entry(self, capability: str) -> CapabilityEntry | None:
        """
        Get the full capability entry.

        Args:
            capability: Capability name to look up

        Returns:
            CapabilityEntry if found, None otherwise
        """
        return self._capabilities.get(capability)

    def list_by_category(self, category: str) -> list[CapabilityEntry]:
        """
        List capabilities in a specific category.

        Args:
            category: Category name to filter by

        Returns:
            List of CapabilityEntry instances in the category
        """
        return [
            entry
            for entry in self._capabilities.values()
            if entry.category == category
        ]

    def unregister_capability(self, capability: str) -> None:
        """
        Unregister a capability completely.

        Args:
            capability: Capability name to unregister
        """
        if capability in self._capabilities:
            # Remove from agent mappings
            for agent_name in self._capabilities[capability].provided_by:
                if agent_name in self._agent_capabilities:
                    self._agent_capabilities[agent_name].discard(capability)

            # Remove capability entry
            del self._capabilities[capability]
            logger.info(f"Unregistered capability '{capability}'")

    def unregister_agent(self, agent_name: str) -> None:
        """
        Remove an agent from all capabilities it provides.

        Args:
            agent_name: Agent name to unregister
        """
        if agent_name not in self._agent_capabilities:
            return

        # Remove agent from all capability provider lists
        for capability in self._agent_capabilities[agent_name]:
            if capability in self._capabilities:
                entry = self._capabilities[capability]
                if agent_name in entry.provided_by:
                    entry.provided_by.remove(agent_name)

        # Remove agent's capability tracking
        del self._agent_capabilities[agent_name]
        logger.info(f"Unregistered agent '{agent_name}' from all capabilities")


# Module-level singleton
_global_capability_registry: CapabilityRegistry | None = None


def get_capability_registry() -> CapabilityRegistry:
    """
    Get the global capability registry instance.

    Returns:
        The singleton CapabilityRegistry instance
    """
    global _global_capability_registry
    if _global_capability_registry is None:
        _global_capability_registry = CapabilityRegistry()
    return _global_capability_registry
