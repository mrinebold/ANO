"""
Policy Gates

Concrete implementations of policy gates for enforcing quality, security,
and operational standards in agent execution.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """
    Result from evaluating a policy gate.

    Indicates whether the gate passed, which gate was evaluated, and
    provides context for failures.
    """

    passed: bool
    gate_name: str
    message: str = ""
    severity: str = "error"  # error, warning, info


class PolicyGate(ABC):
    """
    Base class for policy gates.

    A policy gate evaluates a specific aspect of agent execution context
    (e.g., test results, code quality, security) and returns a pass/fail
    decision with context.
    """

    def __init__(self, name: str, description: str):
        """
        Initialize a policy gate.

        Args:
            name: Gate identifier (e.g., "test-success")
            description: Human-readable description of what this gate checks
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Evaluate this gate against execution context.

        Args:
            context: Execution context containing data for evaluation

        Returns:
            GateResult indicating pass/fail and context
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class TestSuccessGate(PolicyGate):
    """
    Gate 1: Tests must pass.

    Ensures that all automated tests have passed before allowing
    deployment or production operations.
    """

    def __init__(self):
        super().__init__(
            name="test-success",
            description="All automated tests must pass",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check if tests passed.

        Expected context keys:
        - tests_passed: bool
        - test_results: dict with details (optional)
        """
        tests_passed = context.get("tests_passed", False)

        if tests_passed:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message="All tests passed",
                severity="info",
            )

        test_results = context.get("test_results", {})
        failed_count = test_results.get("failed", "unknown")

        return GateResult(
            passed=False,
            gate_name=self.name,
            message=f"Tests failed (failed count: {failed_count})",
            severity="error",
        )


class FileVerificationGate(PolicyGate):
    """
    Gate 2: File integrity verification.

    Ensures that required files exist and have not been corrupted or
    modified unexpectedly.
    """

    def __init__(self):
        super().__init__(
            name="file-verification",
            description="Required files must exist and have correct integrity",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check file integrity.

        Expected context keys:
        - required_files: list[str] - Files that must exist
        - files_verified: bool - Whether integrity checks passed
        - missing_files: list[str] (optional)
        """
        files_verified = context.get("files_verified", False)

        if files_verified:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message="All required files verified",
                severity="info",
            )

        missing_files = context.get("missing_files", [])
        if missing_files:
            return GateResult(
                passed=False,
                gate_name=self.name,
                message=f"Missing or corrupted files: {', '.join(missing_files)}",
                severity="error",
            )

        return GateResult(
            passed=False,
            gate_name=self.name,
            message="File verification failed",
            severity="error",
        )


class BranchPolicyGate(PolicyGate):
    """
    Gate 3: Correct branch policy.

    Ensures operations are performed on the correct Git branch for the
    current environment (e.g., development on feature branches, production
    on main).
    """

    def __init__(self):
        super().__init__(
            name="branch-policy",
            description="Operations must target correct branch for environment",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check branch policy compliance.

        Expected context keys:
        - current_branch: str
        - allowed_branches: list[str]
        - environment: str (optional)
        """
        current_branch = context.get("current_branch", "")
        allowed_branches = context.get("allowed_branches", [])

        if not current_branch:
            return GateResult(
                passed=False,
                gate_name=self.name,
                message="No branch information available",
                severity="error",
            )

        if current_branch in allowed_branches:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message=f"Branch '{current_branch}' is allowed",
                severity="info",
            )

        return GateResult(
            passed=False,
            gate_name=self.name,
            message=f"Branch '{current_branch}' not in allowed list: {allowed_branches}",
            severity="error",
        )


class DocumentationGate(PolicyGate):
    """
    Gate 4: Documentation must be present.

    Ensures that code changes are accompanied by appropriate documentation
    updates (README, API docs, inline comments).
    """

    def __init__(self):
        super().__init__(
            name="documentation",
            description="Changes must include appropriate documentation",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check documentation presence.

        Expected context keys:
        - documentation_updated: bool
        - documentation_score: float (0-1, optional)
        - missing_docs: list[str] (optional)
        """
        docs_updated = context.get("documentation_updated", False)

        if docs_updated:
            score = context.get("documentation_score", 1.0)
            return GateResult(
                passed=True,
                gate_name=self.name,
                message=f"Documentation updated (score: {score:.2f})",
                severity="info",
            )

        missing_docs = context.get("missing_docs", [])
        if missing_docs:
            return GateResult(
                passed=False,
                gate_name=self.name,
                message=f"Missing documentation: {', '.join(missing_docs)}",
                severity="error",
            )

        return GateResult(
            passed=False,
            gate_name=self.name,
            message="Documentation not updated",
            severity="error",
        )


class CodeQualityGate(PolicyGate):
    """
    Gate 5: Code quality checks (linting, type checking).

    Ensures code meets quality standards through automated linting and
    static type checking.
    """

    def __init__(self):
        super().__init__(
            name="code-quality",
            description="Code must pass linting and type checks",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check code quality.

        Expected context keys:
        - lint_passed: bool
        - type_check_passed: bool
        - quality_issues: list[str] (optional)
        """
        lint_passed = context.get("lint_passed", False)
        type_check_passed = context.get("type_check_passed", False)

        if lint_passed and type_check_passed:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message="Code quality checks passed",
                severity="info",
            )

        issues = context.get("quality_issues", [])
        failed_checks = []
        if not lint_passed:
            failed_checks.append("linting")
        if not type_check_passed:
            failed_checks.append("type checking")

        return GateResult(
            passed=False,
            gate_name=self.name,
            message=f"Failed checks: {', '.join(failed_checks)}. Issues: {len(issues)}",
            severity="error",
        )


class SecurityValidationGate(PolicyGate):
    """
    Gate 6: Security validation.

    Ensures no security vulnerabilities are introduced, including
    dependency checks, secret scanning, and vulnerability scanning.
    """

    def __init__(self):
        super().__init__(
            name="security-validation",
            description="No security vulnerabilities or exposed secrets",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check security validation.

        Expected context keys:
        - security_scan_passed: bool
        - vulnerabilities_found: int
        - severity_levels: dict[str, int] (optional)
        """
        scan_passed = context.get("security_scan_passed", False)

        if scan_passed:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message="Security validation passed",
                severity="info",
            )

        vuln_count = context.get("vulnerabilities_found", 0)
        severity_levels = context.get("severity_levels", {})

        return GateResult(
            passed=False,
            gate_name=self.name,
            message=f"Found {vuln_count} vulnerabilities: {severity_levels}",
            severity="error",
        )


class ApprovalGate(PolicyGate):
    """
    Gate 7: Human approval required.

    Ensures that sensitive or destructive operations have explicit human
    approval before proceeding.
    """

    def __init__(self):
        super().__init__(
            name="approval",
            description="Human approval required for sensitive operations",
        )

    async def evaluate(self, context: dict[str, Any]) -> GateResult:
        """
        Check approval status.

        Expected context keys:
        - approval_granted: bool
        - approver: str (optional)
        - approval_timestamp: str (optional)
        """
        approval_granted = context.get("approval_granted", False)

        if approval_granted:
            approver = context.get("approver", "unknown")
            timestamp = context.get("approval_timestamp", "unknown")
            return GateResult(
                passed=True,
                gate_name=self.name,
                message=f"Approved by {approver} at {timestamp}",
                severity="info",
            )

        return GateResult(
            passed=False,
            gate_name=self.name,
            message="Approval required but not granted",
            severity="error",
        )


# Gate registry for easy instantiation
GATE_REGISTRY: dict[str, type[PolicyGate]] = {
    "test-success": TestSuccessGate,
    "file-verification": FileVerificationGate,
    "branch-policy": BranchPolicyGate,
    "documentation": DocumentationGate,
    "code-quality": CodeQualityGate,
    "security-validation": SecurityValidationGate,
    "approval": ApprovalGate,
}


def get_gate(gate_name: str) -> PolicyGate:
    """
    Get a gate instance by name.

    Args:
        gate_name: Name of the gate to instantiate

    Returns:
        PolicyGate instance

    Raises:
        ValueError: If gate name is not recognized
    """
    if gate_name not in GATE_REGISTRY:
        raise ValueError(
            f"Unknown gate: {gate_name}. Available: {list(GATE_REGISTRY.keys())}"
        )

    gate_class = GATE_REGISTRY[gate_name]
    return gate_class()
