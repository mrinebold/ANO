"""
Agent Onboarding Example

Demonstrates the full Agent Builder onboarding pipeline:
validate → certify → generate → register → wire_hierarchy
"""

import asyncio

from agents.agent_builder.agent import AgentBuilderAgent
from agents.agent_builder.schemas import (
    AgentSpec,
    Capability,
    CapabilityCategory,
    PersonalitySpec,
    PolicyAttachment,
    ReportingRelationship,
    TeamType,
)


def main():
    # Define a new agent specification
    spec = AgentSpec(
        name="market_analyst",
        display_name="Market Analyst",
        role="Analyze market trends and competitive landscape",
        team=TeamType.RESEARCH,
        capabilities=[
            Capability(
                name="market-research",
                category=CapabilityCategory.RESEARCH,
                description="Research market trends and dynamics",
            ),
            Capability(
                name="competitive-analysis",
                category=CapabilityCategory.ANALYSIS,
                description="Analyze competitive positioning",
                tools=["mcp__web__search"],
            ),
        ],
        reporting=ReportingRelationship(
            reports_to="cto_advisor",
            dotted_line_to=["ceo_advisor"],
            orchestrator="helio_orchestrator",
        ),
        personality=PersonalitySpec(
            description="Data-driven and insightful",
            response_style="Structured reports with charts and bullet points",
            collaboration_style="Provides market context to other agents",
        ),
        policy=PolicyAttachment(
            policy_bundle_id="research-v1",
            version="1.0",
        ),
        description=(
            "A market analyst agent that tracks industry trends, monitors "
            "competitors, and provides strategic market intelligence."
        ),
        tags=["market", "research", "competitive-analysis"],
    )

    # Initialize builder with existing agents
    builder = AgentBuilderAgent(existing_agents=["ceo_advisor", "cto_advisor"])

    # --- Step-by-step approach ---

    # Step 1: Validate the spec
    print("=== Step 1: Validation ===")
    errors = builder.validate(spec)
    if errors:
        print(f"Validation errors: {errors}")
        return
    print("Validation passed!")

    # Step 2: Run certification
    print("\n=== Step 2: Certification ===")
    report = builder.certify(spec)
    print(f"Score: {report.score:.0%}")
    print(f"Overall passed: {report.overall_passed}")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{check.severity:8}] {status} - {check.check_name}: {check.message}")

    if not report.overall_passed:
        print("\nCertification failed. Fix required checks and retry.")
        return

    # Step 3: Generate files
    print("\n=== Step 3: Code Generation ===")
    files = builder.generate(spec)
    for path, content in files.items():
        print(f"  Generated: {path} ({len(content)} bytes)")

    # Step 4: Register
    print("\n=== Step 4: Registration ===")
    from agents.agent_builder.schemas import RegistryEntry

    entry = RegistryEntry(
        name=spec.name,
        display_name=spec.display_name,
        capabilities=["market-research", "competitive-analysis"],
        team="research",
        specialization=spec.role,
    )
    builder.register(entry)
    print(f"Registered: {entry.name}")

    # Step 5: Wire hierarchy
    print("\n=== Step 5: Hierarchy Wiring ===")
    builder.wire_hierarchy(spec)
    hierarchy = builder.get_hierarchy()
    print(f"Hierarchy: {hierarchy}")

    # --- Or use the all-in-one onboard() method ---

    print("\n=== Full Onboarding (all-in-one) ===")
    builder2 = AgentBuilderAgent(existing_agents=["ceo_advisor", "cto_advisor"])
    result = builder2.onboard(spec)

    if result.success:
        print(f"Agent '{spec.name}' onboarded successfully!")
        print(f"Generated {len(result.generated_files)} files")
        print(f"Registry entry: {result.registry_entry.name}")
    else:
        print(f"Onboarding failed: {result.error}")


if __name__ == "__main__":
    main()
