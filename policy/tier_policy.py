"""
Tier-Based Policy Configuration

Provides tier-specific policy gate configurations that match operational
requirements for development, test, and production environments.
"""

import logging

from ano_core.environment import EnvironmentTier
from policy.gates import (
    ApprovalGate,
    BranchPolicyGate,
    CodeQualityGate,
    DocumentationGate,
    FileVerificationGate,
    PolicyGate,
    SecurityValidationGate,
    TestSuccessGate,
)

logger = logging.getLogger(__name__)


def get_tier_policy(tier: EnvironmentTier) -> list[PolicyGate]:
    """
    Get policy gates appropriate for the given environment tier.

    Returns tier-specific gate configurations:
    - DEVELOPMENT: All gates advisory (warnings only, never block)
    - TEST: All gates enforced, approval required for destructive operations
    - PRODUCTION: All gates strictly enforced with no exceptions

    Args:
        tier: Environment tier to get policy gates for

    Returns:
        List of PolicyGate instances configured for the tier
    """
    if tier == EnvironmentTier.DEVELOPMENT:
        return _get_development_policy()
    elif tier == EnvironmentTier.TEST:
        return _get_test_policy()
    else:  # PRODUCTION
        return _get_production_policy()


def _get_development_policy() -> list[PolicyGate]:
    """
    Get policy gates for development environment.

    Development policy is permissive to enable rapid iteration:
    - All gates are advisory (warnings only)
    - No blocking on failures
    - Focus on education and awareness

    Returns:
        List of development-appropriate policy gates
    """
    gates = [
        TestSuccessGate(),
        FileVerificationGate(),
        BranchPolicyGate(),
        DocumentationGate(),
        CodeQualityGate(),
        SecurityValidationGate(),
        # No approval gate in development
    ]

    logger.info(
        f"Loaded {len(gates)} policy gates for DEVELOPMENT tier (advisory mode)"
    )
    return gates


def _get_test_policy() -> list[PolicyGate]:
    """
    Get policy gates for test environment.

    Test policy balances validation with flexibility:
    - All gates enforced
    - Approval required for destructive operations
    - Provides pre-production validation

    Returns:
        List of test-appropriate policy gates
    """
    gates = [
        TestSuccessGate(),
        FileVerificationGate(),
        BranchPolicyGate(),
        DocumentationGate(),
        CodeQualityGate(),
        SecurityValidationGate(),
        ApprovalGate(),  # Required for destructive operations
    ]

    logger.info(f"Loaded {len(gates)} policy gates for TEST tier (enforced mode)")
    return gates


def _get_production_policy() -> list[PolicyGate]:
    """
    Get policy gates for production environment.

    Production policy is strict with no exceptions:
    - All gates strictly enforced
    - Approval always required
    - Zero tolerance for violations

    Returns:
        List of production-appropriate policy gates
    """
    gates = [
        TestSuccessGate(),
        FileVerificationGate(),
        BranchPolicyGate(),
        DocumentationGate(),
        CodeQualityGate(),
        SecurityValidationGate(),
        ApprovalGate(),  # Always required in production
    ]

    logger.info(f"Loaded {len(gates)} policy gates for PRODUCTION tier (strict mode)")
    return gates


def get_custom_policy(gate_names: list[str]) -> list[PolicyGate]:
    """
    Build a custom policy from a list of gate names.

    Useful for creating specialized policies for specific operations
    or testing individual gates.

    Args:
        gate_names: List of gate names to include (e.g., ["test-success", "security-validation"])

    Returns:
        List of PolicyGate instances

    Raises:
        ValueError: If any gate name is not recognized
    """
    from policy.gates import GATE_REGISTRY

    gates = []

    for gate_name in gate_names:
        if gate_name not in GATE_REGISTRY:
            raise ValueError(
                f"Unknown gate: {gate_name}. Available: {list(GATE_REGISTRY.keys())}"
            )
        gate_class = GATE_REGISTRY[gate_name]
        gates.append(gate_class())

    logger.info(f"Built custom policy with {len(gates)} gates: {gate_names}")
    return gates


def get_minimal_policy() -> list[PolicyGate]:
    """
    Get a minimal policy for basic validation.

    Includes only essential gates:
    - Test success
    - Security validation

    Useful for lightweight validation or testing scenarios.

    Returns:
        List of minimal policy gates
    """
    gates = [
        TestSuccessGate(),
        SecurityValidationGate(),
    ]

    logger.info(f"Loaded minimal policy with {len(gates)} gates")
    return gates


def get_quality_policy() -> list[PolicyGate]:
    """
    Get a quality-focused policy.

    Focuses on code quality and documentation:
    - Test success
    - Code quality
    - Documentation

    Useful for CI/CD pipelines focused on code quality.

    Returns:
        List of quality-focused policy gates
    """
    gates = [
        TestSuccessGate(),
        CodeQualityGate(),
        DocumentationGate(),
    ]

    logger.info(f"Loaded quality policy with {len(gates)} gates")
    return gates


def get_security_policy() -> list[PolicyGate]:
    """
    Get a security-focused policy.

    Focuses on security and compliance:
    - Security validation
    - File verification
    - Approval

    Useful for security-sensitive operations.

    Returns:
        List of security-focused policy gates
    """
    gates = [
        SecurityValidationGate(),
        FileVerificationGate(),
        ApprovalGate(),
    ]

    logger.info(f"Loaded security policy with {len(gates)} gates")
    return gates
