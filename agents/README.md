# ANO Reference Agents

This module provides 4 reference agent implementations demonstrating the ANO framework:

## Agents

### 1. CEO Advisor (`ceo_advisor`)
**Team**: Executive
**Capabilities**: strategy, leadership, governance, stakeholder_management

Strategic leadership advisor providing organizational guidance, board relations, and stakeholder management advice.

**Files**:
- `agents/ceo/agent.py` - CEOAdvisorAgent class
- `agents/ceo/skill.md` - Detailed capability documentation

### 2. CTO Advisor (`cto_advisor`)
**Team**: Executive
**Capabilities**: technology_strategy, architecture, team_leadership, technical_operations

Technical strategy advisor providing architecture guidance, technology selection, and technical team leadership.

**Files**:
- `agents/cto/agent.py` - CTOAdvisorAgent class
- `agents/cto/skill.md` - Detailed capability documentation

### 3. Agent Builder (`agent_builder`)
**Team**: Coordination
**Role**: HR Department

Handles agent onboarding, certification, registration, and organizational hierarchy management.

**Files**:
- `agents/agent_builder/agent.py` - AgentBuilderAgent class
- `agents/agent_builder/schemas.py` - Pydantic models (AgentSpec, CertificationReport, etc.)
- `agents/agent_builder/certification.py` - CertificationEngine with 12 checks
- `agents/agent_builder/templates/` - Code generation templates

**Key Features**:
- Agent specification validation
- 12-point certification system (6 required, 5 advisory, 1 info)
- Skeleton code generation from templates
- Registry management
- Organizational hierarchy tracking

### 4. Chat Advisor (`chat_advisor`)
**Team**: Communications
**Capabilities**: knowledge_qa, document_reference, contextual_coaching

Knowledge-grounded conversational advisor designed for deployment via Telegram, web chat, or other messaging channels.

**Files**:
- `agents/chat_advisor/agent.py` - ChatAdvisorAgent class
- `agents/chat_advisor/skill.md` - Detailed capability documentation

## Usage

### Import Agents

```python
from agents import (
    CEOAdvisorAgent,
    CTOAdvisorAgent,
    AgentBuilderAgent,
    ChatAdvisorAgent,
)

from agents.agent_builder import (
    AgentSpec,
    CertificationReport,
    OnboardingResult,
    TeamType,
    CapabilityCategory,
    Capability,
)
```

### Onboard a New Agent

```python
from agents import AgentBuilderAgent
from agents.agent_builder import (
    AgentSpec,
    TeamType,
    Capability,
    CapabilityCategory,
    PersonalitySpec,
)

# Create agent builder
builder = AgentBuilderAgent(existing_agents=["ceo_advisor", "cto_advisor"])

# Define new agent
spec = AgentSpec(
    name="data_analyst",
    display_name="Data Analyst Agent",
    role="Data analysis and insight generation",
    team=TeamType.RESEARCH,
    capabilities=[
        Capability(
            name="data_analysis",
            category=CapabilityCategory.ANALYSIS,
            description="Analyze datasets and generate insights",
            tools=["mcp__database__query"],
        )
    ],
    personality=PersonalitySpec(
        description="Analytical and detail-oriented",
        response_style="Structured with data visualizations",
    ),
    description="Analyzes organizational data to generate actionable insights",
)

# Onboard agent
result = builder.onboard(spec)

if result.success:
    print(f"✅ Agent {spec.name} onboarded successfully!")
    print(f"Certification score: {result.certification.score:.2%}")
    print(f"Generated files: {list(result.generated_files.keys())}")
else:
    print(f"❌ Onboarding failed: {result.error}")
```

### Use an Advisor Agent

```python
from ano_core.types import AgentInput, AgentContext, OrgProfile

# Create context
context = AgentContext(
    org_profile=OrgProfile(
        org_name="Example Organization",
        org_type="nonprofit",
    )
)

# Create input
agent_input = AgentInput(
    data={
        "question": "How should we structure our AI governance?",
        "context": {
            "current_situation": "We're deploying 5 AI agents...",
            "constraints": ["Limited budget", "6-month timeline"],
        }
    },
    context=context,
)

# Execute CEO advisor
ceo = CEOAdvisorAgent(context=context)
output = await ceo.execute(agent_input)

print(output.result["analysis"])
for rec in output.result["recommendations"]:
    print(f"- [{rec['priority']}] {rec['action']}")
```

## Architecture

All agents inherit from `BaseAgent` which provides:
- LLM backend integration
- Token tracking and metadata
- JSON response parsing
- Policy attachment hooks

Agents implement two key methods:
1. `get_system_prompt()` - Define agent personality and role
2. `execute(agent_input)` - Perform agent's primary task

## Design Principles

1. **Generic & Reusable**: No proprietary names or organization-specific logic
2. **Production Ready**: Type hints, logging, error handling throughout
3. **Well-Documented**: Comprehensive skill.md files and inline docs
4. **Framework-Native**: Uses ano_core types and agent_framework base classes
5. **Clean Separation**: Each agent is self-contained with clear interfaces

## Templates

The Agent Builder includes templates for generating new agents:

- `templates/basic_agent.py.tmpl` - Python agent skeleton
- `templates/agent_skill.md.tmpl` - Skill documentation template

Templates use `{{VAR}}` substitution for:
- `{{AGENT_NAME}}` - Agent identifier (e.g., "data_analyst")
- `{{DISPLAY_NAME}}` - Human-readable name
- `{{CLASS_NAME}}` - Python class name
- `{{ROLE}}` - Agent role description
- `{{TEAM}}` - Team assignment
- `{{CAPABILITIES}}` - Capability list
- `{{PERSONALITY}}` - Personality description
- `{{REPORTS_TO}}` - Supervisor name
- `{{CREATED_DATE}}` - Generation timestamp
