"""
Agent Discovery

Automatic discovery of agents decorated with @register_agent from Python
packages. Supports lazy loading and package scanning.
"""

import importlib
import logging
import pkgutil
from typing import Any

from registry.agent_registry import AgentMetadataEntry

logger = logging.getLogger(__name__)


def discover_agents(package: str = "agents") -> list[tuple[type, AgentMetadataEntry]]:
    """
    Discover agents decorated with @register_agent from a package.

    Recursively imports all modules in the specified package and searches
    for classes with the _agent_metadata attribute set by the decorator.

    Args:
        package: Package name to scan (e.g., "agents", "plugins.custom_agents")

    Returns:
        List of tuples (agent_class, metadata) for discovered agents

    Raises:
        ImportError: If the package cannot be imported
    """
    discovered: list[tuple[type, AgentMetadataEntry]] = []

    try:
        # Import the package
        pkg = importlib.import_module(package)
    except ImportError as e:
        logger.error(f"Failed to import package '{package}': {e}")
        raise

    # Get package path for recursive traversal
    if not hasattr(pkg, "__path__"):
        logger.warning(f"Package '{package}' is not a package (no __path__)")
        return discovered

    # Walk all modules in the package
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=pkg.__path__,
        prefix=f"{package}.",
        onerror=lambda x: logger.warning(f"Error importing module: {x}"),
    ):
        try:
            module = importlib.import_module(modname)
            logger.debug(f"Scanning module: {modname}")

            # Look for classes with _agent_metadata attribute
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                # Check if it's a class with agent metadata
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "_agent_metadata")
                    and isinstance(attr._agent_metadata, AgentMetadataEntry)
                ):
                    discovered.append((attr, attr._agent_metadata))
                    logger.info(
                        f"Discovered agent '{attr._agent_metadata.name}' "
                        f"in {modname}"
                    )

        except Exception as e:
            logger.warning(f"Failed to scan module '{modname}': {e}")
            continue

    logger.info(f"Discovered {len(discovered)} agents in package '{package}'")
    return discovered


def auto_register_agents(
    package: str = "agents",
    registry: Any = None,
    capability_registry: Any = None,
) -> int:
    """
    Discover and automatically register agents from a package.

    Scans the package for decorated agents and registers them in the
    provided registries. If no registries are provided, uses the global
    singletons.

    Args:
        package: Package name to scan
        registry: AgentRegistry instance (optional, uses global if None)
        capability_registry: CapabilityRegistry instance (optional, uses global if None)

    Returns:
        Number of agents registered

    Raises:
        ImportError: If the package cannot be imported
    """
    from registry.agent_registry import get_registry
    from registry.capability_registry import get_capability_registry

    if registry is None:
        registry = get_registry()
    if capability_registry is None:
        capability_registry = get_capability_registry()

    discovered = discover_agents(package)
    registered_count = 0

    for agent_class, metadata in discovered:
        try:
            # Register agent
            if not registry.has(metadata.name):
                registry.register(agent_class, metadata)
                registered_count += 1

                # Register capabilities
                for capability in metadata.capabilities:
                    capability_registry.register(
                        capability=capability,
                        agent_name=metadata.name,
                        description=f"Provided by {metadata.name}",
                        category=metadata.team,
                    )
            else:
                logger.debug(f"Agent '{metadata.name}' already registered, skipping")

        except Exception as e:
            logger.error(f"Failed to register agent '{metadata.name}': {e}")
            continue

    logger.info(f"Auto-registered {registered_count} agents from package '{package}'")
    return registered_count


def discover_from_modules(*module_names: str) -> list[tuple[type, AgentMetadataEntry]]:
    """
    Discover agents from specific module names.

    Useful for loading agents from multiple non-package modules or
    for selective loading.

    Args:
        *module_names: Module names to scan (e.g., "agents.strategy", "agents.qa")

    Returns:
        List of tuples (agent_class, metadata) for discovered agents
    """
    discovered: list[tuple[type, AgentMetadataEntry]] = []

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            logger.debug(f"Scanning module: {module_name}")

            # Look for classes with _agent_metadata attribute
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                if (
                    isinstance(attr, type)
                    and hasattr(attr, "_agent_metadata")
                    and isinstance(attr._agent_metadata, AgentMetadataEntry)
                ):
                    discovered.append((attr, attr._agent_metadata))
                    logger.info(
                        f"Discovered agent '{attr._agent_metadata.name}' "
                        f"in {module_name}"
                    )

        except Exception as e:
            logger.warning(f"Failed to scan module '{module_name}': {e}")
            continue

    logger.info(f"Discovered {len(discovered)} agents from specified modules")
    return discovered
