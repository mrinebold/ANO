#!/usr/bin/env python3
"""
Registry & Policy Module Demo

Complete working example showing how to use the registry and policy
modules together for agent registration and governance.

Run: python3 examples/registry_policy_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from registry import (
    AgentMetadataEntry,
    get_capability_registry,
    get_registry,
    register_agent,
)
from policy import (
    PolicyEngine,
    get_tier_policy,
)
from ano_core.environment import EnvironmentTier


# =============================================================================
# STEP 1: Define agents using @register_agent decorator
# =============================================================================


@register_agent(
    name="test-runner",
    team="development",
    version="1.0.0",
    capabilities=["testing", "qa", "validation"],
    description="Runs automated test suites and reports results",
)
class TestRunnerAgent:
    """Agent that executes test suites."""

    async def execute(self, input_data: dict) -> dict:
        print(f"  TestRunnerAgent executing...")
        return {
            "tests_passed": True,
            "test_count": 42,
            "failures": 0,
        }


@register_agent(
    name="security-scanner",
    team="development",
    version="1.0.0",
    capabilities=["security", "vulnerability-scanning"],
    description="Scans code for security vulnerabilities",
)
class SecurityScannerAgent:
    """Agent that performs security scanning."""

    async def execute(self, input_data: dict) -> dict:
        print(f"  SecurityScannerAgent executing...")
        return {
            "security_scan_passed": True,
            "vulnerabilities_found": 0,
            "severity_levels": {},
        }


@register_agent(
    name="code-reviewer",
    team="development",
    version="1.0.0",
    capabilities=["code-review", "quality"],
    description="Reviews code quality and style",
)
class CodeReviewerAgent:
    """Agent that reviews code quality."""

    async def execute(self, input_data: dict) -> dict:
        print(f"  CodeReviewerAgent executing...")
        return {
            "lint_passed": True,
            "type_check_passed": True,
            "quality_issues": [],
        }


# =============================================================================
# STEP 2: Demo functions
# =============================================================================


def demo_registry():
    """Demonstrate registry functionality."""
    print("\n" + "=" * 70)
    print("REGISTRY DEMO")
    print("=" * 70)

    registry = get_registry()
    capability_registry = get_capability_registry()

    # List all registered agents
    print("\n1. All registered agents:")
    all_agents = registry.list_agents()
    for metadata in all_agents:
        print(f"  • {metadata.name} (team={metadata.team}, v{metadata.version})")
        print(f"    Capabilities: {', '.join(metadata.capabilities)}")

    # Filter by team
    print("\n2. Development team agents:")
    dev_agents = registry.list_agents(team="development")
    for metadata in dev_agents:
        print(f"  • {metadata.name}")

    # Filter by capability
    print("\n3. Agents with 'testing' capability:")
    test_agents = registry.list_agents(capability="testing")
    for metadata in test_agents:
        print(f"  • {metadata.name}")

    # Look up specific agent
    print("\n4. Get agent metadata:")
    metadata = registry.get_metadata("test-runner")
    print(f"  Name: {metadata.name}")
    print(f"  Team: {metadata.team}")
    print(f"  Description: {metadata.description}")
    print(f"  Capabilities: {metadata.capabilities}")

    # Capability registry
    print("\n5. Capability providers:")
    for capability in ["testing", "security", "quality"]:
        providers = capability_registry.get_providers(capability)
        print(f"  {capability}: {providers}")


async def demo_policy_development():
    """Demonstrate policy enforcement in development tier."""
    print("\n" + "=" * 70)
    print("POLICY DEMO - DEVELOPMENT TIER (Advisory Mode)")
    print("=" * 70)

    tier = EnvironmentTier.DEVELOPMENT
    gates = get_tier_policy(tier)
    engine = PolicyEngine(gates=gates, tier=tier)

    print(f"\nLoaded {len(gates)} policy gates for {tier.value} tier")
    for gate in gates:
        print(f"  • {gate.name}: {gate.description}")

    # Context with some failures
    print("\n1. Evaluating with some gate failures:")
    context = {
        "tests_passed": True,
        "files_verified": True,
        "current_branch": "main",
        "allowed_branches": ["feature/*", "bugfix/*"],  # main not allowed!
        "documentation_updated": False,  # Docs not updated!
        "lint_passed": True,
        "type_check_passed": True,
        "security_scan_passed": True,
    }

    decision = await engine.evaluate_pre("test-runner", context)

    print(f"\n  Decision: {'ALLOW' if decision.allowed else 'DENY'}")
    print(f"  Gates passed: {len(decision.gates_passed)}")
    print(f"  Gates failed: {len(decision.gates_failed)}")

    if decision.gates_failed:
        print("\n  Failed gates:")
        for gate_name in decision.gates_failed:
            print(f"    • {gate_name}")

    if decision.violations:
        print("\n  Violations:")
        for violation in decision.violations:
            print(f"    • {violation.gate}: {violation.message}")
            print(f"      Remediation: {violation.remediation}")

    print(f"\n  → In DEVELOPMENT, failures are advisory only (allowed={decision.allowed})")


async def demo_policy_test():
    """Demonstrate policy enforcement in test tier."""
    print("\n" + "=" * 70)
    print("POLICY DEMO - TEST TIER (Enforced Mode)")
    print("=" * 70)

    tier = EnvironmentTier.TEST
    gates = get_tier_policy(tier)
    engine = PolicyEngine(gates=gates, tier=tier)

    print(f"\nLoaded {len(gates)} policy gates for {tier.value} tier")

    # Context with all passes
    print("\n1. All gates passing:")
    context = {
        "tests_passed": True,
        "files_verified": True,
        "current_branch": "feature/demo",
        "allowed_branches": ["feature/*", "bugfix/*"],
        "documentation_updated": True,
        "lint_passed": True,
        "type_check_passed": True,
        "security_scan_passed": True,
        "approval_granted": True,
        "approver": "tech-lead",
        "approval_timestamp": "2026-02-16T10:00:00Z",
    }

    decision = await engine.evaluate_pre("test-runner", context)
    print(f"  Decision: {'ALLOW' if decision.allowed else 'DENY'}")
    print(f"  Gates passed: {decision.gates_passed}")

    # Context with approval missing
    print("\n2. Missing approval:")
    context["approval_granted"] = False

    decision = await engine.evaluate_pre("test-runner", context)
    print(f"  Decision: {'ALLOW' if decision.allowed else 'DENY'}")
    print(f"  Gates failed: {decision.gates_failed}")

    if decision.violations:
        print(f"\n  Violations:")
        for violation in decision.violations:
            print(f"    • {violation.gate}: {violation.message}")

    print(f"\n  → In TEST, failures block execution (allowed={decision.allowed})")


async def demo_policy_production():
    """Demonstrate policy enforcement in production tier."""
    print("\n" + "=" * 70)
    print("POLICY DEMO - PRODUCTION TIER (Strict Mode)")
    print("=" * 70)

    tier = EnvironmentTier.PRODUCTION
    gates = get_tier_policy(tier)
    engine = PolicyEngine(gates=gates, tier=tier)

    print(f"\nLoaded {len(gates)} policy gates for {tier.value} tier")

    # Perfect context
    context = {
        "tests_passed": True,
        "files_verified": True,
        "current_branch": "main",
        "allowed_branches": ["main"],
        "documentation_updated": True,
        "lint_passed": True,
        "type_check_passed": True,
        "security_scan_passed": True,
        "approval_granted": True,
        "approver": "deployment-manager",
        "approval_timestamp": "2026-02-16T10:00:00Z",
    }

    decision = await engine.evaluate_pre("test-runner", context)
    print(f"  Decision: {'ALLOW' if decision.allowed else 'DENY'}")
    print(f"  Gates passed: {decision.gates_passed}")
    print(f"\n  → In PRODUCTION, all gates must pass (allowed={decision.allowed})")


async def demo_complete_workflow():
    """Demonstrate complete workflow with agents and policies."""
    print("\n" + "=" * 70)
    print("COMPLETE WORKFLOW DEMO")
    print("=" * 70)

    registry = get_registry()
    tier = EnvironmentTier.TEST
    gates = get_tier_policy(tier)
    engine = PolicyEngine(gates=gates, tier=tier)

    print("\nRunning multi-agent workflow with policy enforcement...")

    # 1. Run test agent
    print("\n1. Running test-runner agent:")
    test_agent_class = registry.get("test-runner")
    test_agent = test_agent_class()
    test_output = await test_agent.execute({})

    # 2. Run security agent
    print("\n2. Running security-scanner agent:")
    security_agent_class = registry.get("security-scanner")
    security_agent = security_agent_class()
    security_output = await security_agent.execute({})

    # 3. Run code review agent
    print("\n3. Running code-reviewer agent:")
    review_agent_class = registry.get("code-reviewer")
    review_agent = review_agent_class()
    review_output = await review_agent.execute({})

    # 4. Build policy context from agent outputs
    print("\n4. Building policy context from agent outputs:")
    context = {
        **test_output,
        **security_output,
        **review_output,
        "files_verified": True,
        "current_branch": "feature/complete-workflow",
        "allowed_branches": ["feature/*"],
        "documentation_updated": True,
        "approval_granted": True,
        "approver": "workflow-manager",
    }

    # 5. Evaluate policy
    print("\n5. Evaluating policy gates:")
    decision = await engine.evaluate_pre("workflow", context)

    print(f"\n  Final Decision: {'✓ ALLOW' if decision.allowed else '✗ DENY'}")
    print(f"  Gates passed: {len(decision.gates_passed)}/{len(gates)}")

    if decision.allowed:
        print("\n  → Workflow approved! All agents passed policy checks.")
    else:
        print("\n  → Workflow blocked. Policy violations detected:")
        for violation in decision.violations:
            print(f"    • {violation.gate}: {violation.message}")


# =============================================================================
# MAIN
# =============================================================================


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("ANO FOUNDATION - REGISTRY & POLICY MODULE DEMO")
    print("=" * 70)

    # Registry demos
    demo_registry()

    # Policy demos
    await demo_policy_development()
    await demo_policy_test()
    await demo_policy_production()

    # Complete workflow
    await demo_complete_workflow()

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Registry provides centralized agent management")
    print("  2. Capabilities enable discovery by functionality")
    print("  3. Policy gates enforce quality/security standards")
    print("  4. Tier-based enforcement (dev → test → prod)")
    print("  5. Clean integration with ano_core types")
    print()


if __name__ == "__main__":
    asyncio.run(main())
