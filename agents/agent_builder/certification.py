"""
Agent Certification Engine

Validates agent specifications against organizational standards and best practices.
"""

import logging
import re
from datetime import datetime
from typing import Optional

from agents.agent_builder.schemas import AgentSpec, CertificationReport, CheckResult

logger = logging.getLogger(__name__)

# Reserved agent names that cannot be used
RESERVED_NAMES = frozenset({
    "base",
    "system",
    "admin",
    "root",
    "agent",
    "builder",
    "registry",
})


class CertificationEngine:
    """
    Certification engine for agent specifications.

    Performs a series of checks to validate that an agent specification
    meets organizational standards before onboarding.
    """

    def __init__(self, existing_agent_names: Optional[list[str]] = None):
        """
        Initialize the certification engine.

        Args:
            existing_agent_names: List of already-registered agent names
        """
        self.existing_agent_names = set(existing_agent_names or [])

    def certify(self, spec: AgentSpec) -> CertificationReport:
        """
        Run full certification suite on an agent specification.

        Args:
            spec: Agent specification to certify

        Returns:
            CertificationReport with all check results
        """
        logger.info(f"Certifying agent: {spec.name}")

        checks: list[CheckResult] = []

        # Required checks (errors)
        checks.append(self._check_name_format(spec))
        checks.append(self._check_name_uniqueness(spec))
        checks.append(self._check_name_not_reserved(spec))
        checks.append(self._check_has_capabilities(spec))
        checks.append(self._check_has_role(spec))
        checks.append(self._check_has_team(spec))

        # Advisory checks (warnings)
        checks.append(self._check_has_personality(spec))
        checks.append(self._check_has_reporting(spec))
        checks.append(self._check_has_description(spec))
        checks.append(self._check_has_policy(spec))
        checks.append(self._check_capability_tools(spec))

        # Info checks
        checks.append(self._check_mcp_servers(spec))

        # Calculate score and overall pass/fail
        total_checks = len(checks)
        passed_checks = sum(1 for c in checks if c.passed)
        score = passed_checks / total_checks if total_checks > 0 else 0.0

        # Overall passed = all error-level checks passed
        error_checks = [c for c in checks if c.severity == "error"]
        overall_passed = all(c.passed for c in error_checks)

        # Collect warnings
        warnings = [c.message for c in checks if c.severity == "warning" and not c.passed]

        report = CertificationReport(
            agent_name=spec.name,
            timestamp=datetime.utcnow(),
            checks=checks,
            overall_passed=overall_passed,
            score=score,
            warnings=warnings,
            generated_files=[],
        )

        logger.info(
            f"Certification complete: {spec.name} - "
            f"Passed: {overall_passed}, Score: {score:.2f}"
        )

        return report

    def _check_name_format(self, spec: AgentSpec) -> CheckResult:
        """Check that agent name follows format requirements."""
        # This is already validated by Pydantic, but we check again for the report
        valid = (
            len(spec.name) >= 3
            and len(spec.name) <= 50
            and spec.name.islower()
            and all(c.isalnum() or c in ["-", "_"] for c in spec.name)
        )

        return CheckResult(
            check_name="name_format",
            passed=valid,
            severity="error",
            message=(
                "Agent name meets format requirements"
                if valid
                else "Agent name must be lowercase, 3-50 chars, alphanumeric + hyphens/underscores"
            ),
        )

    def _check_name_uniqueness(self, spec: AgentSpec) -> CheckResult:
        """Check that agent name is not already registered."""
        is_unique = spec.name not in self.existing_agent_names

        return CheckResult(
            check_name="name_uniqueness",
            passed=is_unique,
            severity="error",
            message=(
                f"Agent name '{spec.name}' is unique"
                if is_unique
                else f"Agent name '{spec.name}' is already registered"
            ),
        )

    def _check_name_not_reserved(self, spec: AgentSpec) -> CheckResult:
        """Check that agent name is not a reserved word."""
        not_reserved = spec.name not in RESERVED_NAMES

        return CheckResult(
            check_name="name_not_reserved",
            passed=not_reserved,
            severity="error",
            message=(
                f"Agent name '{spec.name}' is not reserved"
                if not_reserved
                else f"Agent name '{spec.name}' is reserved and cannot be used"
            ),
        )

    def _check_has_capabilities(self, spec: AgentSpec) -> CheckResult:
        """Check that agent has at least one capability."""
        has_capabilities = len(spec.capabilities) > 0

        return CheckResult(
            check_name="has_capabilities",
            passed=has_capabilities,
            severity="error",
            message=(
                f"Agent has {len(spec.capabilities)} capabilities"
                if has_capabilities
                else "Agent must have at least one capability"
            ),
        )

    def _check_has_role(self, spec: AgentSpec) -> CheckResult:
        """Check that agent has a defined role."""
        has_role = bool(spec.role and spec.role.strip())

        return CheckResult(
            check_name="has_role",
            passed=has_role,
            severity="error",
            message=(
                f"Agent has role: {spec.role}"
                if has_role
                else "Agent must have a defined role"
            ),
        )

    def _check_has_team(self, spec: AgentSpec) -> CheckResult:
        """Check that agent has a team assignment."""
        has_team = bool(spec.team)

        return CheckResult(
            check_name="has_team",
            passed=has_team,
            severity="error",
            message=(
                f"Agent assigned to team: {spec.team.value}"
                if has_team
                else "Agent must be assigned to a team"
            ),
        )

    def _check_has_personality(self, spec: AgentSpec) -> CheckResult:
        """Advisory: Check if agent has personality defined."""
        has_personality = spec.personality is not None

        return CheckResult(
            check_name="has_personality",
            passed=has_personality,
            severity="warning",
            message=(
                "Agent has personality specification"
                if has_personality
                else "Consider adding personality specification for better user experience"
            ),
        )

    def _check_has_reporting(self, spec: AgentSpec) -> CheckResult:
        """Advisory: Check if agent has reporting structure."""
        has_reporting = (
            spec.reporting.reports_to is not None
            or len(spec.reporting.dotted_line_to) > 0
            or spec.reporting.orchestrator is not None
        )

        return CheckResult(
            check_name="has_reporting",
            passed=has_reporting,
            severity="warning",
            message=(
                "Agent has reporting structure defined"
                if has_reporting
                else "Consider defining reporting structure for organizational clarity"
            ),
        )

    def _check_has_description(self, spec: AgentSpec) -> CheckResult:
        """Advisory: Check if agent has extended description."""
        has_description = bool(spec.description and len(spec.description) > 20)

        return CheckResult(
            check_name="has_description",
            passed=has_description,
            severity="warning",
            message=(
                "Agent has extended description"
                if has_description
                else "Consider adding extended description for documentation"
            ),
        )

    def _check_has_policy(self, spec: AgentSpec) -> CheckResult:
        """Advisory: Check if agent has policy attachment."""
        has_policy = spec.policy is not None

        return CheckResult(
            check_name="has_policy",
            passed=has_policy,
            severity="warning",
            message=(
                f"Agent has policy attachment: {spec.policy.policy_bundle_id}"
                if has_policy
                else "Consider attaching a policy bundle for governance"
            ),
        )

    def _check_capability_tools(self, spec: AgentSpec) -> CheckResult:
        """Advisory: Check if capabilities define required tools."""
        capabilities_with_tools = sum(
            1 for cap in spec.capabilities if len(cap.tools) > 0
        )
        total_capabilities = len(spec.capabilities)

        has_tools = capabilities_with_tools > 0

        return CheckResult(
            check_name="capability_tools",
            passed=has_tools,
            severity="warning",
            message=(
                f"{capabilities_with_tools}/{total_capabilities} capabilities define tools"
                if has_tools
                else "Consider defining required tools/MCP servers for capabilities"
            ),
        )

    def _check_mcp_servers(self, spec: AgentSpec) -> CheckResult:
        """Info: List any MCP servers referenced."""
        all_tools = []
        for cap in spec.capabilities:
            all_tools.extend(cap.tools)

        # Extract potential MCP server references (tools starting with "mcp__")
        mcp_servers = [t for t in all_tools if t.startswith("mcp__")]

        return CheckResult(
            check_name="mcp_servers",
            passed=True,
            severity="info",
            message=(
                f"MCP servers referenced: {', '.join(set(mcp_servers))}"
                if mcp_servers
                else "No MCP servers referenced"
            ),
        )
