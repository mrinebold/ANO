"""
Context Builder

Fluent builder for constructing AgentContext instances.
"""

from __future__ import annotations

from typing import Any

from ano_core.types import AgentContext, AgentOutput, OrgProfile


class ContextBuilder:
    """
    Fluent builder for creating AgentContext instances.

    Provides a convenient API for constructing context objects with
    organization profile, pipeline state, and upstream agent outputs.

    Example:
        context = (
            ContextBuilder()
            .with_org_profile(profile)
            .with_pipeline_state({"step": 1})
            .with_upstream_output("researcher", researcher_output)
            .build()
        )
    """

    def __init__(self):
        """Initialize an empty context builder."""
        self._org_profile: OrgProfile | None = None
        self._pipeline_state: dict[str, Any] = {}
        self._upstream_outputs: dict[str, AgentOutput] = {}

    def with_org_profile(self, profile: OrgProfile) -> "ContextBuilder":
        """
        Set the organization profile.

        Args:
            profile: Organization profile to include in context

        Returns:
            Self for method chaining
        """
        self._org_profile = profile
        return self

    def with_pipeline_state(self, state: dict[str, Any]) -> "ContextBuilder":
        """
        Set the pipeline state.

        Args:
            state: Pipeline state dictionary

        Returns:
            Self for method chaining
        """
        self._pipeline_state = state
        return self

    def with_upstream_output(
        self,
        agent_name: str,
        output: AgentOutput,
    ) -> "ContextBuilder":
        """
        Add an upstream agent's output to the context.

        Args:
            agent_name: Name of the upstream agent
            output: Output from the upstream agent

        Returns:
            Self for method chaining
        """
        self._upstream_outputs[agent_name] = output
        return self

    def build(self) -> AgentContext:
        """
        Build the AgentContext instance.

        Returns:
            Constructed AgentContext

        Raises:
            ValueError: If org_profile is not set (required field)
        """
        if self._org_profile is None:
            raise ValueError("org_profile is required to build AgentContext")

        return AgentContext(
            org_profile=self._org_profile,
            pipeline_state=self._pipeline_state,
            upstream_outputs=self._upstream_outputs,
        )
