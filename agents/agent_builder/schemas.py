"""
Agent Builder Schemas

Pydantic models for agent specification, certification, and onboarding.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TeamType(str, Enum):
    """Standard team types for agent organization."""

    EXECUTIVE = "executive"
    DEVELOPMENT = "development"
    OPERATIONS = "operations"
    RESEARCH = "research"
    COMMUNICATIONS = "communications"
    COORDINATION = "coordination"
    CUSTOM = "custom"


class CapabilityCategory(str, Enum):
    """Categories of agent capabilities."""

    RESEARCH = "research"
    WRITING = "writing"
    ANALYSIS = "analysis"
    COMPLIANCE = "compliance"
    COMMUNICATION = "communication"
    DEVELOPMENT = "development"
    TESTING = "testing"
    SECURITY = "security"
    CUSTOM = "custom"


class Capability(BaseModel):
    """A specific capability of an agent."""

    name: str = Field(description="Capability name")
    category: CapabilityCategory = Field(description="Capability category")
    description: str = Field(default="", description="Capability description")
    tools: list[str] = Field(
        default_factory=list,
        description="MCP tools or external services used for this capability",
    )


class ReportingRelationship(BaseModel):
    """Agent reporting structure within the organization."""

    reports_to: Optional[str] = Field(
        default=None,
        description="Name of supervisor agent (e.g., 'ceo_advisor')",
    )
    dotted_line_to: list[str] = Field(
        default_factory=list,
        description="Additional reporting relationships (matrix management)",
    )
    orchestrator: Optional[str] = Field(
        default=None,
        description="Name of orchestrator agent for coordination (e.g., 'helio_orchestrator')",
    )


class PersonalitySpec(BaseModel):
    """Agent personality and communication style."""

    description: str = Field(
        description="Personality description (e.g., 'Analytical and detail-oriented')"
    )
    response_style: str = Field(
        default="",
        description="How the agent responds (e.g., 'Structured with bullet points')",
    )
    collaboration_style: str = Field(
        default="",
        description="How the agent collaborates with other agents",
    )


class PolicyAttachment(BaseModel):
    """Reference to a policy bundle that governs this agent."""

    policy_bundle_id: str = Field(
        description="ID of the policy bundle to enforce"
    )
    version: str = Field(
        default="1.0",
        description="Policy bundle version",
    )


class AgentSpec(BaseModel):
    """
    Complete specification for a new agent.

    Defines all aspects of an agent including identity, capabilities,
    reporting structure, personality, and policy governance.
    """

    name: str = Field(
        description="Unique agent name (lowercase, 3-50 chars, alphanumeric + hyphens)"
    )
    display_name: str = Field(
        description="Human-readable display name"
    )
    role: str = Field(
        description="Agent's primary role or job title"
    )
    team: TeamType = Field(
        description="Team assignment"
    )
    capabilities: list[Capability] = Field(
        description="List of agent capabilities (at least 1 required)"
    )
    reporting: ReportingRelationship = Field(
        default_factory=ReportingRelationship,
        description="Reporting structure",
    )
    personality: Optional[PersonalitySpec] = Field(
        default=None,
        description="Optional personality specification",
    )
    policy: Optional[PolicyAttachment] = Field(
        default=None,
        description="Optional policy bundle attachment",
    )
    description: str = Field(
        default="",
        description="Extended description of agent purpose and behavior",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional tags for categorization",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name format."""
        if not v:
            raise ValueError("Agent name cannot be empty")
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Agent name must be 3-50 characters")
        if not v.islower():
            raise ValueError("Agent name must be lowercase")
        if not all(c.isalnum() or c in ["-", "_"] for c in v):
            raise ValueError("Agent name must be alphanumeric with hyphens or underscores")
        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: list[Capability]) -> list[Capability]:
        """Validate at least one capability is provided."""
        if not v:
            raise ValueError("At least one capability is required")
        return v


class CheckResult(BaseModel):
    """Result of a single certification check."""

    check_name: str = Field(description="Name of the check performed")
    passed: bool = Field(description="Whether the check passed")
    severity: str = Field(
        default="error",
        description="Severity level: error, warning, info",
    )
    message: str = Field(
        default="",
        description="Detailed message about the check result",
    )


class CertificationReport(BaseModel):
    """
    Certification report for an agent.

    Contains results of all certification checks, overall pass/fail status,
    and any generated files during the certification process.
    """

    agent_name: str = Field(description="Name of the certified agent")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Certification timestamp",
    )
    checks: list[CheckResult] = Field(
        description="List of all certification checks performed"
    )
    overall_passed: bool = Field(
        default=False,
        description="True if all required checks passed",
    )
    score: float = Field(
        default=0.0,
        description="Certification score (0.0-1.0)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-blocking warnings",
    )
    generated_files: list[str] = Field(
        default_factory=list,
        description="List of files generated during certification",
    )


class RegistryEntry(BaseModel):
    """
    Entry for the agent registry.

    Simplified metadata format for agent discovery and lookup.
    """

    name: str = Field(description="Agent name")
    display_name: str = Field(description="Display name")
    capabilities: list[str] = Field(description="List of capability names")
    team: str = Field(description="Team name")
    specialization: str = Field(description="Primary specialization or role")
    reporting_to: Optional[str] = Field(
        default=None,
        description="Name of supervisor agent",
    )
    module_path: str = Field(
        default="",
        description="Python module path for importing the agent",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this agent is active",
    )


class OnboardingResult(BaseModel):
    """
    Complete result of agent onboarding process.

    Includes the original spec, certification report, registry entry,
    generated files, and overall success/failure status.
    """

    spec: AgentSpec = Field(description="Original agent specification")
    certification: CertificationReport = Field(description="Certification report")
    registry_entry: Optional[RegistryEntry] = Field(
        default=None,
        description="Registry entry if registration succeeded",
    )
    generated_files: dict[str, str] = Field(
        default_factory=dict,
        description="Map of file paths to content",
    )
    success: bool = Field(
        default=False,
        description="True if onboarding completed successfully",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if onboarding failed",
    )
