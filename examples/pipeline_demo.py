"""
Pipeline Demo

Demonstrates building and running a multi-stage agent pipeline
with sequential and parallel stages, policy enforcement, and
upstream data flow.
"""

import asyncio

from ano_core.types import AgentContext, AgentInput, AgentOutput, OrgProfile
from ano_core.environment import EnvironmentTier
from agent_framework.base_agent import BaseAgent
from agent_framework.llm.base_backend import LocalBackend
from pipeline.pipeline import Pipeline, Stage, PipelineResult
from pipeline.coordinator import PipelineCoordinator
from registry.agent_registry import AgentRegistry, AgentMetadataEntry
from policy.engine import PolicyEngine
from policy.gates import TestSuccessGate, SecurityValidationGate


# --- Define example agents ---


class ResearcherAgent(BaseAgent):
    """Gathers information on a topic."""

    agent_name = "researcher"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are a research analyst. Gather key findings on the given topic."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        topic = input_data.data.get("topic", "general")
        # In production, this would call an LLM
        return AgentOutput(
            result={
                "findings": [
                    f"Finding 1 about {topic}",
                    f"Finding 2 about {topic}",
                    f"Finding 3 about {topic}",
                ],
                "source_count": 12,
            },
            metadata=self.get_metadata(),
        )


class AnalystAgent(BaseAgent):
    """Analyzes research findings."""

    agent_name = "analyst"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are a data analyst. Synthesize findings into actionable insights."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        # Access upstream outputs from the research stage
        upstream = input_data.context.upstream_outputs or {}
        research = upstream.get("research", {})
        findings = research.get("findings", [])

        return AgentOutput(
            result={
                "insights": [f"Insight from: {f}" for f in findings],
                "confidence": 0.85,
            },
            metadata=self.get_metadata(),
        )


class ComplianceAgent(BaseAgent):
    """Checks compliance of analysis."""

    agent_name = "compliance_checker"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are a compliance checker. Verify outputs meet regulatory standards."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        return AgentOutput(
            result={
                "compliant": True,
                "checks_passed": ["data_privacy", "bias_review", "accuracy"],
            },
            metadata=self.get_metadata(),
        )


class ReviewerAgent(BaseAgent):
    """Executive review of final outputs."""

    agent_name = "reviewer"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are an executive reviewer. Provide final sign-off on deliverables."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        upstream = input_data.context.upstream_outputs or {}
        return AgentOutput(
            result={
                "approved": True,
                "summary": "Research and analysis meet quality standards.",
                "stages_reviewed": list(upstream.keys()),
            },
            metadata=self.get_metadata(),
        )


async def main():
    # --- Setup ---

    # Create organization context
    org = OrgProfile(org_name="Acme Corp", org_type="enterprise")
    context = AgentContext(org_profile=org)

    # Create a local LLM backend (deterministic, no API calls)
    backend = LocalBackend()

    # Register agents
    registry = AgentRegistry()
    agents = [
        (ResearcherAgent, "researcher", "research"),
        (AnalystAgent, "analyst", "research"),
        (ComplianceAgent, "compliance_checker", "operations"),
        (ReviewerAgent, "reviewer", "executive"),
    ]

    for agent_cls, name, team in agents:
        registry.register(
            agent_cls,
            AgentMetadataEntry(
                name=name,
                team=team,
                version="1.0.0",
                capabilities=[],
                description=agent_cls.__doc__ or "",
            ),
        )

    # --- Define Pipeline ---

    pipeline = Pipeline(
        "research-review",
        [
            Stage(
                name="research",
                agents=["researcher"],
                description="Gather research on the topic",
            ),
            Stage(
                name="analysis",
                agents=["analyst", "compliance_checker"],
                parallel=True,  # Run analyst and compliance in parallel
                description="Analyze findings and check compliance",
            ),
            Stage(
                name="executive-review",
                agents=["reviewer"],
                required=True,  # Pipeline fails if this stage fails
                description="Executive sign-off",
            ),
        ],
    )

    print(f"Pipeline: {pipeline.name}")
    print(f"Stages: {pipeline.stage_names}")
    print(f"Total agents: {pipeline.total_agents}")
    print()

    # --- Optional: Add Policy Enforcement ---

    gates = [TestSuccessGate(), SecurityValidationGate()]
    policy_engine = PolicyEngine(gates, EnvironmentTier.DEVELOPMENT)

    # Pre-execution policy check
    decision = await policy_engine.evaluate_pre(
        "research-review",
        {"tests_passed": True, "security_scan_passed": True},
    )
    print(f"Policy check: {'ALLOWED' if decision.allowed else 'BLOCKED'}")
    print(f"Gates passed: {decision.gates_passed}")
    print()

    # --- Run Pipeline ---

    coordinator = PipelineCoordinator(
        pipeline=pipeline,
        registry=registry,
        context=context,
        llm_backend=backend,
    )

    print("Running pipeline...")
    result: PipelineResult = await coordinator.run(
        initial_input={"topic": "AI governance best practices"}
    )

    print(f"\nPipeline completed: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")
    print()

    # Show outputs per stage
    for stage_name, output in result.stage_outputs.items():
        print(f"--- {stage_name} ---")
        if isinstance(output, dict):
            for key, value in output.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {output}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
