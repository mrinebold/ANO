# Agent Builder

The Agent Builder is the **HR department** of an Agent-Native Organization. It handles agent onboarding, certification, code generation, registration, and organizational hierarchy management.

## Overview

When you add a new agent to your ANO, the Agent Builder runs a structured pipeline:

```
validate → certify → generate → register → wire_hierarchy
```

Each step ensures the agent meets organizational standards before becoming active.

## Agent Specification

Every agent starts with an `AgentSpec` — a complete description of the agent's identity, capabilities, and organizational role.

```python
from agents.agent_builder.schemas import (
    AgentSpec,
    Capability,
    CapabilityCategory,
    PersonalitySpec,
    PolicyAttachment,
    ReportingRelationship,
    TeamType,
)

spec = AgentSpec(
    name="data_analyst",                    # Unique, lowercase, 3-50 chars
    display_name="Data Analyst",            # Human-readable
    role="Analyze datasets and generate insights",
    team=TeamType.DEVELOPMENT,
    capabilities=[
        Capability(
            name="data-analysis",
            category=CapabilityCategory.ANALYSIS,
            description="Analyze structured datasets",
            tools=["mcp__database__query"],   # MCP tools used
        ),
        Capability(
            name="visualization",
            category=CapabilityCategory.ANALYSIS,
            description="Generate data visualizations",
        ),
    ],
    reporting=ReportingRelationship(
        reports_to="cto_advisor",
        dotted_line_to=["ceo_advisor"],
        orchestrator="helio_orchestrator",
    ),
    personality=PersonalitySpec(
        description="Analytical and detail-oriented",
        response_style="Structured with tables and bullet points",
        collaboration_style="Provides data-driven input to other agents",
    ),
    policy=PolicyAttachment(
        policy_bundle_id="data-governance-v1",
        version="1.0",
    ),
    description="A data analyst agent that processes datasets, identifies trends, and generates actionable insights for the organization.",
    tags=["analytics", "data", "insights"],
)
```

### Name Requirements

- 3-50 characters
- Lowercase only
- Alphanumeric, hyphens (`-`), and underscores (`_`) allowed
- Cannot be a reserved name: `base`, `system`, `admin`, `root`, `agent`, `builder`, `registry`

### Team Types

| Team | Value | Description |
|------|-------|-------------|
| `EXECUTIVE` | `executive` | Leadership and strategy |
| `DEVELOPMENT` | `development` | Engineering and technical |
| `OPERATIONS` | `operations` | Ops, DevOps, infrastructure |
| `RESEARCH` | `research` | Research and analysis |
| `COMMUNICATIONS` | `communications` | Marketing, PR, comms |
| `COORDINATION` | `coordination` | Orchestration, workflow |
| `CUSTOM` | `custom` | Custom team types |

### Capability Categories

`RESEARCH`, `WRITING`, `ANALYSIS`, `COMPLIANCE`, `COMMUNICATION`, `DEVELOPMENT`, `TESTING`, `SECURITY`, `CUSTOM`

## Certification Engine

The certification engine runs **12 checks** against each agent specification:

### Required Checks (6) — Must Pass

| Check | What It Validates |
|-------|-------------------|
| `name_format` | Name is lowercase, 3-50 chars, valid characters |
| `name_uniqueness` | Name not already registered |
| `name_not_reserved` | Name not in reserved list |
| `has_capabilities` | At least one capability defined |
| `has_role` | Role field is non-empty |
| `has_team` | Team assignment present |

### Advisory Checks (5) — Warnings

| Check | What It Validates |
|-------|-------------------|
| `has_personality` | Personality specification defined |
| `has_reporting` | Reporting structure defined |
| `has_description` | Extended description (>20 chars) |
| `has_policy` | Policy bundle attached |
| `capability_tools` | At least one capability defines tools |

### Info Checks (1)

| Check | What It Validates |
|-------|-------------------|
| `mcp_servers` | Lists any MCP servers referenced in tools |

**Scoring**: Score = passed checks / total checks. Overall pass requires all 6 required checks to pass. Advisory failures produce warnings but don't block onboarding.

## Using the Agent Builder

### Full Onboarding

```python
from agents.agent_builder.agent import AgentBuilderAgent

# Initialize with existing agents (to check uniqueness)
builder = AgentBuilderAgent(existing_agents=["ceo_advisor", "cto_advisor"])

# Run full onboarding pipeline
result = builder.onboard(spec)

if result.success:
    print(f"Agent '{spec.name}' onboarded successfully!")
    print(f"Generated {len(result.generated_files)} files:")
    for path, content in result.generated_files.items():
        print(f"  {path}")
    print(f"Registry entry: {result.registry_entry.name}")
else:
    print(f"Onboarding failed: {result.error}")
    for check in result.certification.checks:
        if not check.passed:
            print(f"  [{check.severity}] {check.check_name}: {check.message}")
```

### Step-by-Step

You can also run each step individually:

```python
builder = AgentBuilderAgent()

# Step 1: Validate
errors = builder.validate(spec)
if errors:
    print("Validation errors:", errors)

# Step 2: Certify
report = builder.certify(spec)
print(f"Score: {report.score:.2f}, Passed: {report.overall_passed}")

# Step 3: Generate files
files = builder.generate(spec)
# Returns: {"agents/data_analyst/agent.py": "...", "agents/data_analyst/__init__.py": "...", "agents/data_analyst/skill.md": "..."}

# Step 4: Register
from agents.agent_builder.schemas import RegistryEntry
entry = RegistryEntry(
    name=spec.name,
    display_name=spec.display_name,
    capabilities=["data-analysis", "visualization"],
    team="development",
    specialization=spec.role,
)
builder.register(entry)

# Step 5: Wire hierarchy
builder.wire_hierarchy(spec)
print(builder.get_hierarchy())
# {"cto_advisor": ["data_analyst"]}
```

## Generated Files

The Agent Builder generates three files per agent:

### `agents/{name}/agent.py`

A Python agent module based on `BaseAgent`:

```python
class DataAnalystAgent(BaseAgent):
    agent_name = "data_analyst"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "Analytical and detail-oriented"

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        raise NotImplementedError("Agent execution not yet implemented")
```

### `agents/{name}/__init__.py`

Package init with class export.

### `agents/{name}/skill.md`

A Markdown skill definition documenting the agent's role, capabilities, reporting structure, and personality.

## Templates

The Agent Builder uses templates from `agents/agent_builder/templates/`:

- `basic_agent.py.tmpl` — Python agent file template
- `agent_skill.md.tmpl` — Skill documentation template

Template variables: `{{AGENT_NAME}}`, `{{DISPLAY_NAME}}`, `{{CLASS_NAME}}`, `{{ROLE}}`, `{{TEAM}}`, `{{CAPABILITIES}}`, `{{PERSONALITY}}`, `{{REPORTS_TO}}`, `{{CREATED_DATE}}`

If templates are not found, the builder falls back to inline templates.

## Organizational Hierarchy

The Agent Builder maintains a hierarchy mapping of supervisor -> direct reports:

```python
builder = AgentBuilderAgent()
builder.onboard(researcher_spec)  # reports_to: "cto_advisor"
builder.onboard(analyst_spec)     # reports_to: "cto_advisor"
builder.onboard(writer_spec)      # reports_to: "ceo_advisor"

hierarchy = builder.get_hierarchy()
# {
#     "cto_advisor": ["researcher", "analyst"],
#     "ceo_advisor": ["writer"],
# }
```
