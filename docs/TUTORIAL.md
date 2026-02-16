# Tutorial: Build Your First ANO

This tutorial walks you through building a complete **Agent-Native Organization** — a 5-agent research team with a pipeline, policy gates, and CLI deployment. No API key needed (uses the local LLM backend).

**Time**: ~15 minutes
**Prerequisites**: Python 3.11+, ANO Foundation installed (`pip install -e ".[dev]"`)

---

## What You'll Build

A research organization called **"Acme Research Lab"** with 5 agents:

| Agent | Role | Stage |
|-------|------|-------|
| Researcher | Investigate the topic | 1. Research |
| QA Specialist | Validate findings | 2. Quality (parallel) |
| Security Reviewer | Check for data risks | 2. Quality (parallel) |
| Technical Writer | Produce the final report | 3. Report |
| CEO Advisor | Executive sign-off | 4. Review |

They'll run in a 4-stage pipeline with policy enforcement.

---

## Step 1: Set Up the Project

```bash
mkdir acme-research && cd acme-research
python3.11 -m venv .venv
source .venv/bin/activate
pip install ano-foundation[dev]
```

Create a `.env` file:

```bash
ANO_PROFILE=minimal
ANO_ENV=development
```

## Step 2: Create the Organization Context

Create `run.py`:

```python
import asyncio
from ano_core.types import AgentContext, AgentInput, OrgProfile

# Define your organization
org = OrgProfile(
    org_name="Acme Research Lab",
    org_type="enterprise",
    industry="Technology Research",
)
context = AgentContext(org_profile=org)
```

## Step 3: Use Pre-Built Agents

ANO Foundation ships with operational agents you can use directly. Import and instantiate them with the **LocalBackend** (no API key needed — returns deterministic test responses):

```python
from agent_framework.llm.local_backend import LocalBackend
from agents.researcher import ResearcherAgent
from agents.qa_specialist import QASpecialistAgent
from agents.security_reviewer import SecurityReviewerAgent
from agents.technical_writer import TechnicalWriterAgent
from agents.ceo import CEOAdvisorAgent

# LocalBackend returns structured test responses — no API key needed
backend = LocalBackend()

# Instantiate your team
researcher = ResearcherAgent(context=context, llm=backend)
qa = QASpecialistAgent(context=context, llm=backend)
security = SecurityReviewerAgent(context=context, llm=backend)
writer = TechnicalWriterAgent(context=context, llm=backend)
ceo = CEOAdvisorAgent(context=context, llm=backend)
```

## Step 4: Run a Single Agent

Before building the pipeline, test one agent:

```python
async def test_researcher():
    input_data = AgentInput(
        data={
            "topic": "Current trends in LLM cost optimization",
            "context": {
                "scope": "standard",
                "focus_areas": ["prompt caching", "model selection", "batching"],
            },
        },
        context=context,
    )
    output = await researcher.execute(input_data)
    print(f"Researcher output: {output.result}")
    print(f"Metadata: {output.metadata.agent_name} v{output.metadata.version}")

asyncio.run(test_researcher())
```

## Step 5: Register Agents in the Registry

The registry enables discovery and pipeline orchestration:

```python
from registry.agent_registry import AgentRegistry, AgentMetadataEntry

registry = AgentRegistry()

agents_to_register = [
    ("researcher", ResearcherAgent, "research", ["research", "analysis"]),
    ("qa_specialist", QASpecialistAgent, "development", ["testing", "quality"]),
    ("security_reviewer", SecurityReviewerAgent, "development", ["security", "audit"]),
    ("technical_writer", TechnicalWriterAgent, "operations", ["documentation"]),
    ("ceo_advisor", CEOAdvisorAgent, "executive", ["strategy", "leadership"]),
]

for name, cls, team, caps in agents_to_register:
    registry.register(cls, AgentMetadataEntry(
        name=name,
        team=team,
        version="1.0.0",
        capabilities=caps,
    ))

# Verify
print(f"Registered agents: {[a.name for a in registry.list_agents()]}")
# → ['researcher', 'qa_specialist', 'security_reviewer', 'technical_writer', 'ceo_advisor']
```

## Step 6: Build a Pipeline

Connect your agents into a multi-stage workflow:

```python
from pipeline.pipeline import Pipeline, Stage

pipeline = Pipeline("research-report", [
    Stage(
        name="research",
        agents=["researcher"],
        description="Investigate the topic and gather findings",
    ),
    Stage(
        name="quality-check",
        agents=["qa_specialist", "security_reviewer"],
        parallel=True,  # Run QA and security simultaneously
        description="Validate findings and check for risks",
    ),
    Stage(
        name="report",
        agents=["technical_writer"],
        description="Produce the final research report",
    ),
    Stage(
        name="executive-review",
        agents=["ceo_advisor"],
        required=True,  # Pipeline fails if CEO review fails
        description="Executive sign-off on the report",
    ),
])

print(f"Pipeline: {pipeline.name}")
print(f"Stages: {pipeline.stage_names}")
print(f"Total agents: {pipeline.total_agents}")
# → Pipeline: research-report
# → Stages: ['research', 'quality-check', 'report', 'executive-review']
# → Total agents: 5
```

## Step 7: Add Policy Enforcement

Add governance gates to enforce quality standards:

```python
from policy.engine import PolicyEngine
from policy.gates import TestSuccessGate, SecurityValidationGate, DocumentationGate
from ano_core.environment import EnvironmentTier

# Development tier = warnings only (won't block execution)
gates = [TestSuccessGate(), SecurityValidationGate(), DocumentationGate()]
engine = PolicyEngine(gates, EnvironmentTier.DEVELOPMENT)

# Check if an agent is allowed to execute
decision = await engine.evaluate_pre("researcher", {
    "tests_passed": True,
    "security_scan_passed": True,
    "documentation_exists": True,
})

print(f"Allowed: {decision.allowed}")  # → True
print(f"Gates passed: {len(decision.gates_passed)}")
```

To enforce gates strictly, switch to `EnvironmentTier.TEST` or `EnvironmentTier.PRODUCTION`.

## Step 8: Add Runtime Hooks

Hooks run before/after each agent execution for logging, sanitization, and cost tracking:

```python
from policy.hooks import AuditLoggingHook, CostTrackingHook, RateLimitHook

hooks = [
    AuditLoggingHook(),           # Log all agent executions
    CostTrackingHook(budget=10.0), # Track LLM costs against budget
    RateLimitHook(max_rpm=60),     # Rate limit agent calls
]
```

These hooks integrate with the `PipelineCoordinator` (see [Policy Engine docs](POLICY_ENGINE.md) for details).

## Step 9: Deploy to CLI

Test your agents interactively:

```python
from channels.cli.repl import CLIRepl

async def run_cli():
    repl = CLIRepl(agent=researcher, prompt="research> ")
    await repl.run()

asyncio.run(run_cli())
```

This gives you an interactive REPL where you can send messages to the researcher agent.

## Step 10: Use Working Memory

Give your agents persistent memory across sessions:

```python
from memory.working_memory import WorkingMemory

# Initialize memory for the researcher
memory = WorkingMemory("researcher", "/tmp/acme-research/memory/researcher")

# Set current task
memory.set_task(
    "LLM Cost Optimization Research",
    "Comprehensive analysis of cost optimization strategies",
)

# Track progress
memory.add_context("Focus: prompt caching, model selection, batching")
memory.add_next_step("Review industry benchmarks")
memory.update_session("Started research", "Identified 3 key optimization areas")

# In a later session, load state
state = memory.load()
print(f"Current task: {state.current_task.title}")
print(f"Context: {state.context}")
```

---

## Complete Example

Here's the full `run.py` putting it all together:

```python
"""Acme Research Lab — A complete ANO example."""

import asyncio

from agent_framework.llm.local_backend import LocalBackend
from agents.ceo import CEOAdvisorAgent
from agents.qa_specialist import QASpecialistAgent
from agents.researcher import ResearcherAgent
from agents.security_reviewer import SecurityReviewerAgent
from agents.technical_writer import TechnicalWriterAgent
from ano_core.types import AgentContext, AgentInput, OrgProfile
from pipeline.pipeline import Pipeline, Stage
from registry.agent_registry import AgentRegistry, AgentMetadataEntry


async def main():
    # 1. Organization
    org = OrgProfile(org_name="Acme Research Lab", org_type="enterprise")
    context = AgentContext(org_profile=org)
    backend = LocalBackend()

    # 2. Agents
    researcher = ResearcherAgent(context=context, llm=backend)

    # 3. Registry
    registry = AgentRegistry()
    for name, cls, team, caps in [
        ("researcher", ResearcherAgent, "research", ["research"]),
        ("qa_specialist", QASpecialistAgent, "development", ["testing"]),
        ("security_reviewer", SecurityReviewerAgent, "development", ["security"]),
        ("technical_writer", TechnicalWriterAgent, "operations", ["documentation"]),
        ("ceo_advisor", CEOAdvisorAgent, "executive", ["strategy"]),
    ]:
        registry.register(cls, AgentMetadataEntry(
            name=name, team=team, version="1.0.0", capabilities=caps,
        ))

    # 4. Pipeline
    pipeline = Pipeline("research-report", [
        Stage(name="research", agents=["researcher"]),
        Stage(name="quality", agents=["qa_specialist", "security_reviewer"], parallel=True),
        Stage(name="report", agents=["technical_writer"]),
        Stage(name="review", agents=["ceo_advisor"], required=True),
    ])

    # 5. Execute a single agent
    output = await researcher.execute(AgentInput(
        data={
            "topic": "LLM cost optimization trends",
            "context": {"scope": "standard"},
        },
        context=context,
    ))

    print(f"Agent: {output.metadata.agent_name}")
    print(f"Result: {output.result}")
    print(f"\nPipeline '{pipeline.name}' ready with {pipeline.total_agents} agents")
    print(f"Stages: {' → '.join(pipeline.stage_names)}")


asyncio.run(main())
```

Run it:

```bash
python run.py
```

---

## Next Steps

- **Use a real LLM**: Replace `LocalBackend()` with `AnthropicBackend()` or `OpenAIBackend()` and set your API key
- **Deploy to Telegram**: See [Deployment Channels](DEPLOYMENT_CHANNELS.md) to make your agents available as bots
- **Add custom agents**: Use the [Agent Builder](AGENT_BUILDER.md) to onboard new agents with certification
- **Enforce governance**: Switch to `EnvironmentTier.TEST` to enforce policy gates
- **Build a custom agent**: Subclass `BaseAgent` with your own `get_system_prompt()` and `execute()` methods
