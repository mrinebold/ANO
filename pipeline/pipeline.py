"""
Pipeline Definition

Defines the structure of a multi-stage agent pipeline with validation support.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ano_core.logging import get_agent_logger

logger = get_agent_logger(__name__)


@dataclass
class Stage:
    """
    A single stage in a pipeline.

    Each stage can contain one or more agents that execute sequentially
    or in parallel. Stages execute in order, with outputs from earlier
    stages available to later ones.
    """

    name: str
    agents: list[str]
    parallel: bool = False
    required: bool = True
    description: str = ""

    def __post_init__(self) -> None:
        """Validate stage configuration."""
        if not self.agents:
            raise ValueError(f"Stage '{self.name}' must have at least one agent")
        if self.parallel and len(self.agents) == 1:
            logger.warning(
                f"Stage '{self.name}' marked as parallel but only has one agent"
            )


@dataclass
class PipelineResult:
    """
    Result of a pipeline execution.

    Tracks success/failure, which stages completed, outputs from all agents,
    execution time, and any error messages.
    """

    success: bool
    stages_completed: list[str] = field(default_factory=list)
    stages_failed: list[str] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None

    @property
    def total_stages(self) -> int:
        """Total number of stages attempted."""
        return len(self.stages_completed) + len(self.stages_failed)

    def get_agent_output(self, agent_name: str) -> Any:
        """Get output from a specific agent, or None if not found."""
        return self.outputs.get(agent_name)


class Pipeline:
    """
    A multi-stage agent execution pipeline.

    Defines the structure of agent execution with validation support
    to ensure all referenced agents exist in the registry.
    """

    def __init__(self, name: str, stages: list[Stage]) -> None:
        """
        Initialize a pipeline.

        Args:
            name: Unique identifier for this pipeline
            stages: List of stages to execute in order
        """
        self.name = name
        self.stages = stages
        self._validate_structure()

    def _validate_structure(self) -> None:
        """Validate pipeline structure."""
        if not self.stages:
            raise ValueError(f"Pipeline '{self.name}' must have at least one stage")

        # Check for duplicate stage names
        stage_names = [stage.name for stage in self.stages]
        if len(stage_names) != len(set(stage_names)):
            raise ValueError(f"Pipeline '{self.name}' has duplicate stage names")

        logger.info(
            f"Pipeline '{self.name}' initialized with {len(self.stages)} stages"
        )

    @property
    def stage_names(self) -> list[str]:
        """Get list of all stage names in order."""
        return [stage.name for stage in self.stages]

    @property
    def total_agents(self) -> int:
        """Total number of agent references across all stages."""
        return sum(len(stage.agents) for stage in self.stages)

    def validate(self, registry: Any) -> list[str]:
        """
        Check that all referenced agents exist in the registry.

        Args:
            registry: AgentRegistry instance to check against

        Returns:
            List of agent names that are missing from the registry
        """
        missing_agents = []
        all_agent_names = set()

        for stage in self.stages:
            for agent_name in stage.agents:
                all_agent_names.add(agent_name)

        # Check each unique agent name against the registry
        for agent_name in all_agent_names:
            if not registry.has_agent(agent_name):
                missing_agents.append(agent_name)
                logger.warning(
                    f"Pipeline '{self.name}' references unknown agent: {agent_name}"
                )

        if missing_agents:
            logger.error(
                f"Pipeline '{self.name}' validation failed: {len(missing_agents)} "
                f"missing agents"
            )
        else:
            logger.info(f"Pipeline '{self.name}' validation passed")

        return missing_agents

    def get_stage(self, stage_name: str) -> Stage | None:
        """Get a stage by name, or None if not found."""
        for stage in self.stages:
            if stage.name == stage_name:
                return stage
        return None

    def __repr__(self) -> str:
        return (
            f"Pipeline(name='{self.name}', stages={len(self.stages)}, "
            f"agents={self.total_agents})"
        )
