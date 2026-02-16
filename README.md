# ANO Foundation

**A framework for building Agent-Native Organizations** — organizations where AI agents operate as first-class team members with governance, onboarding, and deployment channels.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)

---

## What is an Agent-Native Organization?

An **Agent-Native Organization (ANO)** is an organizational model where AI agents are first-class participants — not just tools, but team members with defined roles, capabilities, reporting relationships, and governance. Unlike agent *orchestration* frameworks that focus on task routing, ANO Foundation models an *organization*:

- **HR & Onboarding** — The Agent Builder certifies and registers new agents
- **Governance** — 7 policy gates enforce quality, security, and approval requirements
- **Hierarchy** — Agents have teams, reporting relationships, and dotted-line structures
- **Deployment Channels** — Deploy any agent as a Telegram bot, web chat widget, or CLI tool
- **Working Memory** — Agents maintain persistent state across sessions
- **Profile/Plugin System** — Single-toggle configuration with no conditional sprawl

## Quick Start

### Installation

```bash
# Basic installation
pip install ano-foundation

# With all optional dependencies (OpenAI, Telegram, web chat)
pip install ano-foundation[all]

# Development
pip install ano-foundation[dev]
```

### Your First Agent

```python
from agent_framework.base_agent import BaseAgent
from ano_core.types import AgentContext, AgentInput, AgentOutput, OrgProfile

class GreeterAgent(BaseAgent):
    agent_name = "greeter"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return "You are a friendly greeter for the organization."

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        name = input_data.data.get("name", "World")
        org = input_data.context.org_profile.org_name
        response = await self.call_llm(f"Greet {name} on behalf of {org}")
        return AgentOutput(
            result={"greeting": response},
            metadata=self.get_metadata(),
        )
```

### Register and Use It

```python
from registry.agent_registry import AgentRegistry, AgentMetadataEntry

registry = AgentRegistry()
registry.register(GreeterAgent, AgentMetadataEntry(
    name="greeter",
    team="communications",
    version="1.0.0",
    capabilities=["greeting", "welcome"],
))
```

### Build a Pipeline

```python
from pipeline.pipeline import Pipeline, Stage

pipeline = Pipeline("onboarding-flow", [
    Stage(name="welcome", agents=["greeter"]),
    Stage(name="assessment", agents=["researcher", "analyst"], parallel=True),
    Stage(name="review", agents=["ceo-advisor"], required=True),
])
```

### Deploy to Telegram

```python
from channels.telegram import TelegramBotService, TelegramConfig

config = TelegramConfig(bot_token="YOUR_BOT_TOKEN")
bot = TelegramBotService(config=config, agent=my_agent)
bot.register_command("start", start_handler, "Start the bot")
```

## Architecture

```
ano-foundation/
├── ano_core/           # Settings, types, errors, environment, logging
├── agent_framework/    # BaseAgent, LLM backends (Anthropic/OpenAI/local), context, IO
├── registry/           # Agent + capability registry, auto-discovery
├── policy/             # PolicyEngine, 7 gates, tier enforcement, hooks
├── pipeline/           # Declarative multi-stage pipelines, coordinator
├── memory/             # Agent working memory (structured, persistent)
├── channels/           # Deployment: Telegram, web chat, CLI REPL
├── profiles/           # Profile loader + minimal default profile
├── plugins/msr/        # Example plugin: AI policy advisory presets
├── agents/             # CEO, CTO, AgentBuilder, ChatAdvisor
├── examples/           # Runnable examples
├── tests/              # 201 tests
└── docs/               # Architecture, guides
```

### Module Overview

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `ano_core` | Foundation layer | `AnoSettings`, `AgentContext`, `OrgProfile`, `EnvironmentTier` |
| `agent_framework` | Agent abstraction | `BaseAgent`, `LLMBackend`, `AnthropicBackend`, `OpenAIBackend` |
| `registry` | Agent discovery | `AgentRegistry`, `CapabilityRegistry`, `@register_agent` |
| `policy` | Governance | `PolicyEngine`, `PolicyGate`, 7 built-in gates |
| `pipeline` | Orchestration | `Pipeline`, `Stage`, `PipelineCoordinator` |
| `memory` | Persistence | `WorkingMemory`, `WorkingState`, `TaskInfo` |
| `channels` | Deployment | `TelegramBotService`, `WebChatHandler`, `CLIRepl` |
| `profiles` | Configuration | `ProfileRegistry`, `load_profile()`, `PolicyPreset` |
| `agents` | Built-in agents | `CEOAdvisorAgent`, `AgentBuilderAgent`, `CTOAdvisorAgent` |

### Profile System

ANO Foundation uses a **profile/plugin system** instead of conditional logic:

```bash
# Default: 4 agents, permissive policy, generic config
export ANO_PROFILE=minimal

# AI policy advisory: 5 org-type presets, enhanced compliance
export ANO_PROFILE=msr

# Fine-grained feature toggles
export ANO_FEATURES="+audit_trail,-policy_enforcement"
```

### Policy Gates

The policy engine enforces 7 gates across three tiers:

| Gate | What It Checks |
|------|---------------|
| `test-success` | All automated tests pass |
| `file-verification` | Required files exist with correct integrity |
| `branch-policy` | Operations target correct branch for environment |
| `documentation` | Changes include appropriate documentation |
| `code-quality` | Code passes linting and type checks |
| `security-validation` | No security vulnerabilities or exposed secrets |
| `approval` | Human approval granted for sensitive operations |

**Tier enforcement:**
- **Development** — Warnings only, always allows
- **Test** — Enforced, blocks on failure
- **Production** — Strict enforcement, blocks on failure

### LLM Backends

Pluggable LLM support with three built-in backends:

```python
from agent_framework.llm import AnthropicBackend, OpenAIBackend, LocalBackend

# Anthropic (default)
backend = AnthropicBackend()  # Uses ANTHROPIC_API_KEY

# OpenAI
backend = OpenAIBackend()  # Uses OPENAI_API_KEY

# Local (for testing)
backend = LocalBackend()  # No API key needed
```

## Examples

| Example | Description | Run |
|---------|-------------|-----|
| `examples/cli_repl.py` | Interactive CLI agent | `python examples/cli_repl.py` |
| `examples/telegram_bot.py` | Telegram bot deployment | `python examples/telegram_bot.py` |
| `examples/web_chat.py` | Web chat API | `python examples/web_chat.py` |
| `examples/registry_policy_demo.py` | Registry + policy governance | `python examples/registry_policy_demo.py` |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANO_PROFILE` | `minimal` | Deployment profile (`minimal`, `msr`) |
| `ANO_ENV` | `development` | Environment tier (`development`, `test`, `production`) |
| `ANO_FEATURES` | `""` | Comma-separated feature flags |
| `ANO_DEBUG` | `false` | Enable debug mode |
| `ANO_LOG_LEVEL` | `INFO` | Logging level |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `DEFAULT_LLM_PROVIDER` | `anthropic` | Default LLM provider |
| `DEFAULT_LLM_MODEL` | `claude-sonnet-4-5-20250929` | Default model |

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific module
pytest tests/test_policy.py
```

201 tests covering all modules.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design, module dependencies, data flow
- [Getting Started](docs/GETTING_STARTED.md) — Installation, configuration, first agent
- [Agent Builder](docs/AGENT_BUILDER.md) — Onboarding, certification, templates
- [Profiles & Plugins](docs/PROFILES_AND_PLUGINS.md) — Profile system, custom plugins
- [Policy Engine](docs/POLICY_ENGINE.md) — Gates, tiers, custom gates
- [Deployment Channels](docs/DEPLOYMENT_CHANNELS.md) — Telegram, web, CLI

## How It Compares

| Feature | ANO Foundation | CrewAI | AutoGen | Swarms |
|---------|---------------|--------|---------|--------|
| Organizational model | Yes | No | No | No |
| Agent onboarding/HR | Yes | No | No | No |
| Policy governance | 7 gates, 3 tiers | No | No | No |
| Working memory | Yes | No | Partial | No |
| Profile/plugin system | Yes | No | No | No |
| Telegram deployment | Built-in | No | No | No |
| Web chat deployment | Built-in | No | No | No |
| Agent certification | 12 checks | No | No | No |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Run the test suite (`pytest`)
5. Run linting (`ruff check .`)
6. Submit a pull request

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.
