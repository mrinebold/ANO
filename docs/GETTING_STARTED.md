# Getting Started

This guide walks you through installing ANO Foundation, creating your first agent, and running it.

## Prerequisites

- Python 3.11 or later
- An Anthropic API key (or OpenAI, or use the local backend for testing)

## Installation

```bash
# Clone the repository
git clone https://github.com/ano-foundation/ano-foundation.git
cd ano-foundation

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install with development dependencies
pip install -e ".[dev]"

# Or install with all optional dependencies
pip install -e ".[all,dev]"
```

## Configuration

Create a `.env` file in the project root:

```bash
# Required for LLM calls
ANTHROPIC_API_KEY=sk-ant-...

# Optional overrides
ANO_PROFILE=minimal          # or "msr" for AI policy presets
ANO_ENV=development           # development | test | production
ANO_LOG_LEVEL=INFO           # DEBUG | INFO | WARNING | ERROR
```

## Creating Your First Agent

### 1. Define the Agent

Create a file `my_agent.py`:

```python
from agent_framework.base_agent import BaseAgent
from ano_core.types import AgentInput, AgentOutput


class ResearchAgent(BaseAgent):
    agent_name = "researcher"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return (
            "You are a research analyst. Given a topic, provide a concise "
            "analysis with key findings, trends, and recommendations. "
            "Format your response as JSON with keys: summary, findings, recommendations."
        )

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        topic = input_data.data.get("topic", "general research")
        org = input_data.context.org_profile.org_name

        prompt = f"Research topic: {topic}\nOrganization: {org}"
        response = await self.call_llm(prompt, max_tokens=2048)
        result = self.parse_json_response(response)

        return AgentOutput(
            result=result,
            metadata=self.get_metadata(),
        )
```

### 2. Run the Agent

```python
import asyncio
from ano_core.types import AgentContext, AgentInput, OrgProfile
from agent_framework.llm.anthropic_backend import AnthropicBackend

async def main():
    # Set up context
    org = OrgProfile(org_name="Acme Corp", org_type="enterprise")
    context = AgentContext(org_profile=org)

    # Create agent with LLM backend
    backend = AnthropicBackend()
    agent = ResearchAgent(context=context, llm=backend)

    # Execute
    input_data = AgentInput(
        data={"topic": "AI governance best practices"},
        context=context,
    )
    output = await agent.execute(input_data)
    print(output.result)

asyncio.run(main())
```

### 3. Register the Agent

```python
from registry.agent_registry import AgentRegistry, AgentMetadataEntry

registry = AgentRegistry()
registry.register(ResearchAgent, AgentMetadataEntry(
    name="researcher",
    team="research",
    version="1.0.0",
    capabilities=["research", "analysis"],
    description="Analyzes topics and provides structured findings",
))

# Look it up
agent_class = registry.get("researcher")
agents = registry.list_agents(team="research")
```

## Building a Pipeline

Pipelines connect multiple agents into a multi-stage workflow:

```python
from pipeline.pipeline import Pipeline, Stage

# Define a 3-stage pipeline
pipeline = Pipeline("research-review", [
    Stage(
        name="research",
        agents=["researcher"],
        description="Gather research on the topic",
    ),
    Stage(
        name="analysis",
        agents=["analyst", "compliance-checker"],
        parallel=True,  # Run both agents simultaneously
        description="Analyze findings and check compliance",
    ),
    Stage(
        name="executive-review",
        agents=["ceo-advisor"],
        required=True,  # Pipeline fails if this stage fails
        description="Executive sign-off",
    ),
])

print(pipeline.stage_names)  # ['research', 'analysis', 'executive-review']
print(pipeline.total_agents)  # 4
```

## Adding Policy Enforcement

```python
from policy.engine import PolicyEngine
from policy.gates import TestSuccessGate, SecurityValidationGate, ApprovalGate
from ano_core.environment import EnvironmentTier

# Create engine with gates for test environment
gates = [TestSuccessGate(), SecurityValidationGate(), ApprovalGate()]
engine = PolicyEngine(gates, EnvironmentTier.TEST)

# Evaluate before execution
decision = await engine.evaluate_pre("researcher", {
    "tests_passed": True,
    "security_scan_passed": True,
    "approval_granted": True,
})

if decision.allowed:
    print("Execution approved")
else:
    for violation in decision.violations:
        print(f"BLOCKED: {violation.gate} - {violation.message}")
```

## Using Working Memory

```python
from memory.working_memory import WorkingMemory

# Initialize memory for an agent
memory = WorkingMemory("researcher", "/tmp/agent-memory/researcher")

# Set a task
memory.set_task("Research AI governance", "Comprehensive analysis needed")

# Track progress
memory.add_context("Focus area: municipal government")
memory.add_next_step("Review existing frameworks")
memory.update_session("Started research", "Found 12 relevant sources")

# Load state in a later session
state = memory.load()
print(f"Current task: {state.current_task.title}")
print(f"Status: {state.current_task.status}")
```

## Deploying to CLI

The fastest way to test an agent interactively:

```python
from channels.cli.repl import CLIRepl

class SimpleAgent:
    async def execute(self, text, metadata):
        return f"You said: {text}"

repl = CLIRepl(agent=SimpleAgent(), prompt="agent> ")
await repl.run()
```

## Running Tests

```bash
# All tests
pytest

# Verbose
pytest -v

# Single module
pytest tests/test_policy.py

# With coverage (if pytest-cov installed)
pytest --cov=ano_core --cov=agent_framework
```

## Next Steps

- [Architecture](ARCHITECTURE.md) — Understand the full system design
- [Agent Builder](AGENT_BUILDER.md) — Use the HR system to onboard agents properly
- [Profiles & Plugins](PROFILES_AND_PLUGINS.md) — Configure for your organization type
- [Policy Engine](POLICY_ENGINE.md) — Set up governance gates
- [Deployment Channels](DEPLOYMENT_CHANNELS.md) — Deploy to Telegram, web, or CLI
