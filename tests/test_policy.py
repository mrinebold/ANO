"""Tests for policy module — PolicyEngine, gates, hooks, tier enforcement."""

from __future__ import annotations

from datetime import datetime

import pytest

from ano_core.environment import EnvironmentTier
from ano_core.types import AgentInput, AgentMetadata, AgentOutput, PolicyViolation
from policy.engine import PolicyDecision, PolicyEngine
from policy.gates import (
    ApprovalGate,
    BranchPolicyGate,
    CodeQualityGate,
    DocumentationGate,
    FileVerificationGate,
    GateResult,
    SecurityValidationGate,
    TestSuccessGate,
    get_gate,
    GATE_REGISTRY,
)


# --- Individual Gates ---


class TestTestSuccessGate:
    @pytest.mark.asyncio
    async def test_passes_when_true(self):
        gate = TestSuccessGate()
        result = await gate.evaluate({"tests_passed": True})
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails_when_false(self):
        gate = TestSuccessGate()
        result = await gate.evaluate({"tests_passed": False})
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_fails_when_missing(self):
        gate = TestSuccessGate()
        result = await gate.evaluate({})
        assert result.passed is False


class TestFileVerificationGate:
    @pytest.mark.asyncio
    async def test_passes(self):
        gate = FileVerificationGate()
        result = await gate.evaluate({"files_verified": True})
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails_with_missing_files(self):
        gate = FileVerificationGate()
        result = await gate.evaluate({
            "files_verified": False,
            "missing_files": ["README.md", "LICENSE"],
        })
        assert result.passed is False
        assert "README.md" in result.message


class TestBranchPolicyGate:
    @pytest.mark.asyncio
    async def test_passes_allowed_branch(self):
        gate = BranchPolicyGate()
        result = await gate.evaluate({
            "current_branch": "main",
            "allowed_branches": ["main", "develop"],
        })
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails_disallowed_branch(self):
        gate = BranchPolicyGate()
        result = await gate.evaluate({
            "current_branch": "feature/hack",
            "allowed_branches": ["main"],
        })
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_fails_no_branch(self):
        gate = BranchPolicyGate()
        result = await gate.evaluate({"allowed_branches": ["main"]})
        assert result.passed is False


class TestDocumentationGate:
    @pytest.mark.asyncio
    async def test_passes(self):
        gate = DocumentationGate()
        result = await gate.evaluate({"documentation_updated": True})
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails_with_missing(self):
        gate = DocumentationGate()
        result = await gate.evaluate({
            "documentation_updated": False,
            "missing_docs": ["API.md"],
        })
        assert result.passed is False
        assert "API.md" in result.message


class TestCodeQualityGate:
    @pytest.mark.asyncio
    async def test_passes(self):
        gate = CodeQualityGate()
        result = await gate.evaluate({
            "lint_passed": True,
            "type_check_passed": True,
        })
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails_lint(self):
        gate = CodeQualityGate()
        result = await gate.evaluate({
            "lint_passed": False,
            "type_check_passed": True,
        })
        assert result.passed is False
        assert "linting" in result.message

    @pytest.mark.asyncio
    async def test_fails_both(self):
        gate = CodeQualityGate()
        result = await gate.evaluate({
            "lint_passed": False,
            "type_check_passed": False,
        })
        assert result.passed is False
        assert "linting" in result.message
        assert "type checking" in result.message


class TestSecurityValidationGate:
    @pytest.mark.asyncio
    async def test_passes(self):
        gate = SecurityValidationGate()
        result = await gate.evaluate({"security_scan_passed": True})
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_fails(self):
        gate = SecurityValidationGate()
        result = await gate.evaluate({
            "security_scan_passed": False,
            "vulnerabilities_found": 3,
        })
        assert result.passed is False


class TestApprovalGate:
    @pytest.mark.asyncio
    async def test_passes(self):
        gate = ApprovalGate()
        result = await gate.evaluate({
            "approval_granted": True,
            "approver": "admin",
        })
        assert result.passed is True
        assert "admin" in result.message

    @pytest.mark.asyncio
    async def test_fails(self):
        gate = ApprovalGate()
        result = await gate.evaluate({"approval_granted": False})
        assert result.passed is False


# --- Gate Registry ---


class TestGateRegistry:
    def test_all_gates_registered(self):
        assert len(GATE_REGISTRY) == 7
        expected = [
            "test-success", "file-verification", "branch-policy",
            "documentation", "code-quality", "security-validation", "approval",
        ]
        for name in expected:
            assert name in GATE_REGISTRY

    def test_get_gate(self):
        gate = get_gate("test-success")
        assert isinstance(gate, TestSuccessGate)

    def test_get_gate_unknown_raises(self):
        with pytest.raises(ValueError):
            get_gate("nonexistent-gate")


# --- PolicyEngine ---


class TestPolicyEngine:
    @pytest.mark.asyncio
    async def test_all_pass_dev(self):
        gates = [TestSuccessGate(), SecurityValidationGate()]
        engine = PolicyEngine(gates, EnvironmentTier.DEVELOPMENT)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": True,
            "security_scan_passed": True,
        })
        assert decision.allowed is True
        assert len(decision.gates_passed) == 2
        assert len(decision.gates_failed) == 0

    @pytest.mark.asyncio
    async def test_failure_dev_still_allows(self):
        """Development tier: failures produce warnings but still allow."""
        gates = [TestSuccessGate()]
        engine = PolicyEngine(gates, EnvironmentTier.DEVELOPMENT)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": False,
        })
        assert decision.allowed is True  # Dev always allows
        assert len(decision.gates_failed) == 1

    @pytest.mark.asyncio
    async def test_failure_test_blocks(self):
        """Test tier: failures block execution."""
        gates = [TestSuccessGate()]
        engine = PolicyEngine(gates, EnvironmentTier.TEST)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": False,
        })
        assert decision.allowed is False
        assert len(decision.violations) == 1

    @pytest.mark.asyncio
    async def test_failure_production_blocks(self):
        """Production tier: failures strictly block execution."""
        gates = [TestSuccessGate()]
        engine = PolicyEngine(gates, EnvironmentTier.PRODUCTION)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": False,
        })
        assert decision.allowed is False

    @pytest.mark.asyncio
    async def test_post_evaluation(self):
        gates = [SecurityValidationGate()]
        engine = PolicyEngine(gates, EnvironmentTier.TEST)
        decision = await engine.evaluate_post("test-agent", {
            "security_scan_passed": True,
        })
        assert decision.allowed is True

    @pytest.mark.asyncio
    async def test_multiple_gates_mixed(self):
        gates = [TestSuccessGate(), SecurityValidationGate(), ApprovalGate()]
        engine = PolicyEngine(gates, EnvironmentTier.TEST)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": True,
            "security_scan_passed": False,
            "approval_granted": True,
        })
        assert decision.allowed is False
        assert "test-success" in decision.gates_passed
        assert "security-validation" in decision.gates_failed
        assert "approval" in decision.gates_passed

    @pytest.mark.asyncio
    async def test_violation_has_remediation(self):
        gates = [TestSuccessGate()]
        engine = PolicyEngine(gates, EnvironmentTier.PRODUCTION)
        decision = await engine.evaluate_pre("test-agent", {
            "tests_passed": False,
        })
        assert len(decision.violations) == 1
        violation = decision.violations[0]
        assert violation.gate == "test-success"
        assert violation.remediation != ""
        assert "Production" in violation.remediation

    @pytest.mark.asyncio
    async def test_empty_gates_allows(self):
        engine = PolicyEngine([], EnvironmentTier.PRODUCTION)
        decision = await engine.evaluate_pre("test-agent", {})
        assert decision.allowed is True


# --- Policy Hooks ---


from policy.hooks import (
    AuditLoggingHook,
    CostTrackingHook,
    DataSanitizationHook,
    RateLimitHook,
)


class TestAuditLoggingHook:
    @pytest.mark.asyncio
    async def test_before_execute(self, sample_input):
        hook = AuditLoggingHook()
        result = await hook.before_execute("test-agent", sample_input)
        assert result.proceed is True
        assert result.message == "Audit logged"

    @pytest.mark.asyncio
    async def test_after_execute(self, sample_output):
        hook = AuditLoggingHook()
        result = await hook.after_execute("test-agent", sample_output)
        assert result.proceed is True
        assert result.message == "Audit logged"


class TestCostTrackingHook:
    @pytest.mark.asyncio
    async def test_tracks_tokens(self, sample_input, sample_output):
        hook = CostTrackingHook(cost_per_1k_tokens=0.01)
        # before is a no-op
        result = await hook.before_execute("test-agent", sample_input)
        assert result.proceed is True

        # after should track tokens from metadata
        result = await hook.after_execute("test-agent", sample_output)
        assert result.proceed is True
        assert hook.get_total_cost() > 0
        expected_cost = (500 / 1000) * 0.01
        assert abs(hook.get_total_cost() - expected_cost) < 1e-6

    @pytest.mark.asyncio
    async def test_reset(self, sample_input, sample_output):
        hook = CostTrackingHook()
        await hook.after_execute("test-agent", sample_output)
        assert hook.get_total_cost() > 0
        hook.reset()
        assert hook.get_total_cost() == 0.0


class TestRateLimitHook:
    @pytest.mark.asyncio
    async def test_allows_within_limit(self, sample_input, sample_output):
        hook = RateLimitHook(max_executions_per_minute=5)
        for _ in range(5):
            result = await hook.before_execute("test-agent", sample_input)
            assert result.proceed is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, sample_input, sample_output):
        hook = RateLimitHook(max_executions_per_minute=2)
        await hook.before_execute("test-agent", sample_input)
        await hook.before_execute("test-agent", sample_input)
        result = await hook.before_execute("test-agent", sample_input)
        assert result.proceed is False
        assert "Rate limit exceeded" in result.message

    @pytest.mark.asyncio
    async def test_after_execute_noop(self, sample_output):
        hook = RateLimitHook()
        result = await hook.after_execute("test-agent", sample_output)
        assert result.proceed is True


class TestDataSanitizationHook:
    @pytest.mark.asyncio
    async def test_sanitizes_input(self, sample_context):
        hook = DataSanitizationHook()
        agent_input = AgentInput(
            data={"query": "test", "api_key": "sk-secret-123"},
            context=sample_context,
        )
        result = await hook.before_execute("test-agent", agent_input)
        assert result.proceed is True
        assert result.modified_data["api_key"] == "***REDACTED***"
        assert result.modified_data["query"] == "test"

    @pytest.mark.asyncio
    async def test_sanitizes_output(self):
        hook = DataSanitizationHook()
        output = AgentOutput(
            result={"data": "ok", "password": "hunter2"},
            metadata=AgentMetadata(
                agent_name="test-agent",
                version="1.0.0",
                started_at=datetime(2026, 1, 1),
                tokens_used=100,
            ),
        )
        result = await hook.after_execute("test-agent", output)
        assert result.proceed is True
        assert result.modified_data["password"] == "***REDACTED***"
        assert result.modified_data["data"] == "ok"
