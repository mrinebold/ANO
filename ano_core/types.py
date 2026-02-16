"""
ANO Core Types

Defines the foundational data structures used throughout the ANO framework
for agent execution, context passing, and policy reporting.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class OrgProfile(BaseModel):
    """
    Organization profile for contextual agent execution.

    Provides organizational context that agents can use to tailor their
    behavior and outputs. Supports multiple org types (municipal, enterprise,
    nonprofit, education, healthcare).
    """

    org_name: str = Field(
        description="Organization name",
    )
    org_type: str = Field(
        description="Organization type (e.g., 'municipal', 'enterprise', 'nonprofit', 'education', 'healthcare')",
    )
    state: Optional[str] = Field(
        default=None,
        description="State/province location",
    )
    industry: Optional[str] = Field(
        default=None,
        description="Industry or mission area",
    )
    size: Optional[str] = Field(
        default=None,
        description="Organization size (employees, student population, etc.)",
    )
    population: Optional[str] = Field(
        default=None,
        description="Population served (for municipal) or company size",
    )
    budget: Optional[str] = Field(
        default=None,
        description="Annual budget or revenue",
    )
    website: Optional[str] = Field(
        default=None,
        description="Organization website URL",
    )
    departments: list[str] = Field(
        default_factory=list,
        description="List of departments or organizational units",
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Key concerns or focus areas",
    )
    contact_email: Optional[str] = Field(
        default=None,
        description="Primary contact email",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional organization-specific metadata",
    )


class AgentContext(BaseModel):
    """
    Runtime context passed to agents during pipeline execution.

    Contains organizational profile, pipeline state, and outputs from
    upstream agents.
    """

    org_profile: OrgProfile = Field(
        description="Organization profile for this execution",
    )
    pipeline_state: dict[str, Any] = Field(
        default_factory=dict,
        description="Shared state across pipeline execution",
    )
    upstream_outputs: dict[str, Any] = Field(
        default_factory=dict,
        description="Outputs from upstream agents in the pipeline",
    )


class AgentInput(BaseModel):
    """
    Input data structure for agent execution.

    Combines the agent's specific input data with runtime context and
    any policy attachments.
    """

    data: dict[str, Any] = Field(
        description="Agent-specific input data",
    )
    context: AgentContext = Field(
        description="Runtime execution context",
    )
    policy_attachments: list[str] = Field(
        default_factory=list,
        description="List of policy document identifiers to enforce",
    )


class AgentMetadata(BaseModel):
    """
    Metadata about agent execution.

    Tracks execution timing, LLM usage, and version information for
    observability and cost tracking.
    """

    agent_name: str = Field(
        description="Name of the agent that executed",
    )
    version: str = Field(
        description="Agent version identifier",
    )
    started_at: datetime = Field(
        description="Execution start timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Execution completion timestamp",
    )
    llm_calls: int = Field(
        default=0,
        description="Number of LLM API calls made",
    )
    tokens_used: int = Field(
        default=0,
        description="Total tokens consumed (prompt + completion)",
    )


class PolicyViolation(BaseModel):
    """
    A single policy gate violation.

    Records the gate that failed, severity, descriptive message, and
    recommended remediation steps.
    """

    gate: str = Field(
        description="Name of the policy gate that was violated",
    )
    severity: str = Field(
        description="Violation severity (e.g., 'error', 'warning', 'info')",
    )
    message: str = Field(
        description="Human-readable description of the violation",
    )
    remediation: str = Field(
        description="Suggested steps to resolve the violation",
    )


class PolicyReport(BaseModel):
    """
    Policy enforcement report.

    Summarizes which policy gates passed, failed, and any violations
    that occurred during execution.
    """

    gates_passed: list[str] = Field(
        default_factory=list,
        description="List of policy gates that passed",
    )
    gates_failed: list[str] = Field(
        default_factory=list,
        description="List of policy gates that failed",
    )
    violations: list[PolicyViolation] = Field(
        default_factory=list,
        description="Detailed violations for failed gates",
    )


class AgentOutput(BaseModel):
    """
    Output data structure from agent execution.

    Contains the agent's result data, execution metadata, and optional
    policy enforcement report.
    """

    result: dict[str, Any] = Field(
        description="Agent-specific output data",
    )
    metadata: AgentMetadata = Field(
        description="Execution metadata",
    )
    policy_report: Optional[PolicyReport] = Field(
        default=None,
        description="Policy enforcement report if policies were attached",
    )
