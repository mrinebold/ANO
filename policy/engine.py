"""
Policy Engine

Orchestrates policy gate evaluation for pre- and post-execution checks.
Aggregates gate results into policy decisions and violation reports.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from ano_core.environment import EnvironmentTier
from ano_core.types import PolicyViolation
from policy.gates import GateResult, PolicyGate

logger = logging.getLogger(__name__)


@dataclass
class PolicyDecision:
    """
    Decision from policy evaluation.

    Aggregates results from multiple policy gates into a single
    allow/deny decision with detailed violation tracking.
    """

    allowed: bool
    gates_passed: list[str] = field(default_factory=list)
    gates_failed: list[str] = field(default_factory=list)
    violations: list[PolicyViolation] = field(default_factory=list)


class PolicyEngine:
    """
    Policy enforcement engine.

    Evaluates a set of policy gates against agent execution context
    in both pre-execution and post-execution phases. Supports tier-specific
    gate configuration with different enforcement levels.
    """

    def __init__(self, gates: list[PolicyGate], tier: EnvironmentTier):
        """
        Initialize policy engine.

        Args:
            gates: List of policy gates to evaluate
            tier: Environment tier (controls enforcement strictness)
        """
        self.gates = gates
        self.tier = tier
        logger.info(
            f"Initialized PolicyEngine with {len(gates)} gates for tier {tier.value}"
        )

    async def evaluate_pre(
        self,
        agent_name: str,
        input_data: dict[str, Any],
    ) -> PolicyDecision:
        """
        Evaluate policy gates before agent execution.

        Pre-execution checks validate that the agent has proper context,
        required approvals, and passes environmental restrictions.

        Args:
            agent_name: Name of the agent about to execute
            input_data: Input data and context for the agent

        Returns:
            PolicyDecision indicating whether execution should proceed
        """
        logger.info(f"Pre-execution policy evaluation for agent '{agent_name}'")

        # Build evaluation context
        context = {
            "agent_name": agent_name,
            "input_data": input_data,
            "tier": self.tier.value,
            "phase": "pre-execution",
        }

        # Merge input_data into context for gate evaluation
        context.update(input_data)

        return await self._evaluate_gates(context)

    async def evaluate_post(
        self,
        agent_name: str,
        output: dict[str, Any],
    ) -> PolicyDecision:
        """
        Evaluate policy gates after agent execution.

        Post-execution checks validate output quality, security, and
        ensure no violations occurred during execution.

        Args:
            agent_name: Name of the agent that executed
            output: Output data from the agent

        Returns:
            PolicyDecision indicating whether output should be accepted
        """
        logger.info(f"Post-execution policy evaluation for agent '{agent_name}'")

        # Build evaluation context
        context = {
            "agent_name": agent_name,
            "output": output,
            "tier": self.tier.value,
            "phase": "post-execution",
        }

        # Merge output into context for gate evaluation
        context.update(output)

        return await self._evaluate_gates(context)

    async def _evaluate_gates(self, context: dict[str, Any]) -> PolicyDecision:
        """
        Evaluate all gates against context.

        Args:
            context: Evaluation context containing all relevant data

        Returns:
            Aggregated PolicyDecision from all gate evaluations
        """
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        violations: list[PolicyViolation] = []

        for gate in self.gates:
            try:
                result = await gate.evaluate(context)
                logger.debug(
                    f"Gate '{gate.name}': {'PASS' if result.passed else 'FAIL'} "
                    f"({result.message})"
                )

                if result.passed:
                    gates_passed.append(gate.name)
                else:
                    gates_failed.append(gate.name)
                    violations.append(
                        self._create_violation(gate, result, context)
                    )

            except Exception as e:
                logger.error(f"Gate '{gate.name}' evaluation failed: {e}")
                gates_failed.append(gate.name)
                violations.append(
                    PolicyViolation(
                        gate=gate.name,
                        severity="error",
                        message=f"Gate evaluation error: {str(e)}",
                        remediation="Check gate configuration and context data",
                    )
                )

        # Determine overall decision based on tier
        allowed = self._compute_decision(gates_failed, context)

        decision = PolicyDecision(
            allowed=allowed,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            violations=violations,
        )

        logger.info(
            f"Policy decision: {'ALLOW' if allowed else 'DENY'} "
            f"(passed: {len(gates_passed)}, failed: {len(gates_failed)})"
        )

        return decision

    def _compute_decision(
        self,
        gates_failed: list[str],
        context: dict[str, Any],
    ) -> bool:
        """
        Compute final allow/deny decision based on failed gates and tier.

        Args:
            gates_failed: List of gate names that failed
            context: Evaluation context

        Returns:
            True if execution should be allowed, False otherwise
        """
        # No failures = always allow
        if not gates_failed:
            return True

        # Tier-based enforcement
        if self.tier == EnvironmentTier.DEVELOPMENT:
            # Development: warnings only, always allow
            logger.warning(
                f"DEVELOPMENT tier: {len(gates_failed)} gates failed (proceeding)"
            )
            return True

        elif self.tier == EnvironmentTier.TEST:
            # Test: block on failures, but could add exceptions
            logger.warning(f"TEST tier: {len(gates_failed)} gates failed (blocking)")
            return False

        else:  # PRODUCTION
            # Production: strict enforcement
            logger.error(
                f"PRODUCTION tier: {len(gates_failed)} gates failed (blocking)"
            )
            return False

    def _create_violation(
        self,
        gate: PolicyGate,
        result: GateResult,
        context: dict[str, Any],
    ) -> PolicyViolation:
        """
        Create a PolicyViolation from a failed gate result.

        Args:
            gate: The gate that failed
            result: Gate evaluation result
            context: Evaluation context

        Returns:
            PolicyViolation with remediation guidance
        """
        # Generate tier-specific remediation advice
        remediation = self._generate_remediation(gate, result, context)

        return PolicyViolation(
            gate=gate.name,
            severity=result.severity,
            message=result.message,
            remediation=remediation,
        )

    def _generate_remediation(
        self,
        gate: PolicyGate,
        result: GateResult,
        context: dict[str, Any],
    ) -> str:
        """
        Generate remediation guidance for a failed gate.

        Args:
            gate: The gate that failed
            result: Gate evaluation result
            context: Evaluation context

        Returns:
            Human-readable remediation advice
        """
        # Gate-specific remediation templates
        remediation_templates = {
            "test-success": "Run tests locally and fix failures before retrying",
            "file-verification": "Ensure all required files are present and have correct checksums",
            "branch-policy": "Switch to an allowed branch for this environment",
            "documentation": "Update documentation to reflect your changes",
            "code-quality": "Run linting and type checking tools, fix reported issues",
            "security-validation": "Review security scan results and remediate vulnerabilities",
            "approval": "Request approval from authorized personnel before proceeding",
        }

        base_remediation = remediation_templates.get(
            gate.name,
            f"Review {gate.name} requirements and retry",
        )

        # Add tier-specific context
        if self.tier == EnvironmentTier.PRODUCTION:
            return f"{base_remediation}. Production requires strict compliance."
        elif self.tier == EnvironmentTier.TEST:
            return f"{base_remediation}. Approval may be required in test environment."
        else:
            return base_remediation
