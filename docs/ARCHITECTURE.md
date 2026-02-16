# Architecture

ANO Foundation is a modular Python framework for building Agent-Native Organizations. This document describes the system design, module dependencies, and data flow.

## Design Principles

1. **Organization, not just orchestration** — Models teams, hierarchy, onboarding, and governance
2. **Profile-driven configuration** — Core code reads from `ProfileRegistry`, never checks which profile is active
3. **Pluggable LLM backends** — Swap between Anthropic, OpenAI, or local models without changing agent code
4. **Three-tier enforcement** — Development (permissive), Test (enforced), Production (strict)
5. **No conditional sprawl** — Profiles register capabilities; core code is profile-agnostic

## Module Dependency Graph

```
                    ┌─────────────┐
                    │   ano_core   │  Settings, Types, Errors, Environment, Logging
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──┐  ┌──────▼─────┐  ┌──▼──────────┐
     │  registry  │  │   policy   │  │agent_framework│
     │            │  │            │  │              │
     │AgentRegistry│  │PolicyEngine│  │  BaseAgent   │
     │Capabilities│  │  7 Gates   │  │ LLM Backends │
     └─────┬──────┘  └──────┬─────┘  └──────┬───────┘
           │                │               │
           └────────┬───────┘               │
                    │                       │
              ┌─────▼──────┐          ┌─────▼──────┐
              │  pipeline   │          │   memory    │
              │            │          │            │
              │  Pipeline  │          │WorkingMemory│
              │Coordinator │          │WorkingState │
              └─────┬──────┘          └────────────┘
                    │
              ┌─────▼──────┐
              │  profiles   │
              │            │
              │ProfileRegistry│
              │ load_profile │
              └─────┬──────┘
                    │
           ┌────────┼────────┐
           │        │        │
     ┌─────▼──┐ ┌───▼───┐ ┌─▼──────┐
     │ agents  │ │plugins│ │channels│
     │        │ │       │ │        │
     │CEO, CTO│ │MSR    │ │Telegram│
     │Builder │ │plugin │ │Web Chat│
     │Advisor │ │       │ │CLI REPL│
     └────────┘ └───────┘ └────────┘
```

## Module Descriptions

### ano_core (Foundation Layer)

The base layer that all other modules depend on.

- **`settings.py`** — `AnoSettings` (Pydantic BaseSettings), loads from `.env` and optional TOML, provides `ANO_PROFILE`, `ANO_ENV`, `ANO_FEATURES`, LLM keys
- **`types.py`** — Core Pydantic models: `OrgProfile`, `AgentContext`, `AgentInput`, `AgentOutput`, `AgentMetadata`, `PolicyViolation`, `PolicyReport`
- **`errors.py`** — Exception hierarchy rooted at `ANOError`: `AgentExecutionError`, `LLMBackendError`, `PolicyViolationError`, `RegistryError`, `ConfigurationError`, `ChannelError`
- **`environment.py`** — `EnvironmentTier` enum (development/test/production), `TierRestrictions` dataclass, `detect_environment()`, `get_tier_restrictions()`
- **`logging.py`** — `setup_logging()`, `get_agent_logger()`, `JsonFormatter` for structured logging

### agent_framework (Agent Abstraction)

Provides the base class and LLM integration layer.

- **`base_agent.py`** — `BaseAgent` ABC with `get_system_prompt()`, `execute()`, `call_llm()`, `parse_json_response()`, `attach_policy()`, `get_metadata()`
- **`llm/`** — Pluggable backends: `LLMBackend` ABC, `LLMResponse` dataclass, `AnthropicBackend`, `OpenAIBackend`, `LocalBackend`, `get_default_backend()`
- **`context/`** — `ContextBuilder`, `render_org_context()`, `render_regulatory_context()` for building agent prompts
- **`io/`** — `validate_input()`, `validate_output()` for schema-based I/O validation

### registry (Agent Discovery)

Central registration system for agents and capabilities.

- **`agent_registry.py`** — `AgentRegistry` (register, get, list, unregister), `AgentMetadataEntry` dataclass, `@register_agent` decorator, global singleton via `get_registry()`
- **`capability_registry.py`** — `CapabilityRegistry` (many-to-many agent<->capability mapping), `CapabilityEntry`, category-based filtering
- **`discovery.py`** — `discover_agents()` (recursive package scanning), `auto_register_agents()`, `discover_from_modules()`

### policy (Governance)

Policy enforcement engine with 7 built-in gates.

- **`gates.py`** — `PolicyGate` ABC, `GateResult` dataclass, 7 concrete gates (TestSuccess, FileVerification, BranchPolicy, Documentation, CodeQuality, SecurityValidation, Approval), `GATE_REGISTRY`, `get_gate()`
- **`engine.py`** — `PolicyEngine` (evaluate_pre, evaluate_post), `PolicyDecision` dataclass, tier-based decision logic (dev=allow, test=block, prod=strict)
- **`hooks.py`** — `PolicyHook` ABC, 4 built-in hooks (Audit, Sanitization, RateLimit, CostTracking)
- **`tier_policy.py`** — `get_tier_policy()` returns appropriate gate configuration per tier

### pipeline (Orchestration)

Multi-stage agent execution with sequential and parallel support.

- **`pipeline.py`** — `Stage` (name, agents, parallel, required), `Pipeline` (validation, structure), `PipelineResult` (success, outputs, timing)
- **`coordinator.py`** — `PipelineCoordinator` (instantiates agents from registry, manages data flow via `context.upstream_outputs`, runs policy pre/post checks, handles parallel execution)

### memory (Persistence)

Persistent working memory for agents across sessions.

- **`working_memory.py`** — `WorkingMemory` (load/save WORKING.md), `WorkingState`, `TaskInfo`, `BlockerInfo`, `SessionEntry`
- **`template.py`** — `render_working_state()`, `parse_working_state()` for Markdown serialization

### channels (Deployment)

Deploy agents to end-user channels.

- **`base_channel.py`** — `BaseChannel` ABC with `send_message()`, `handle_message()`, `set_agent()`
- **`telegram/`** — `TelegramBotService`, `TelegramConfig`, `TelegramAuth` (tier-based access), `CommandRegistry`, `create_webhook_app()` (FastAPI)
- **`web/`** — `WebChatHandler`, `create_web_chat_app()` (FastAPI with session management)
- **`cli/`** — `CLIRepl` (interactive REPL for local testing)

### profiles (Configuration)

Profile loading and plugin system.

- **`loader.py`** — `ProfileRegistry` (agent classes, config, presets, hooks, features, metadata), `load_profile()` (always loads minimal first, then layers requested profile), `PolicyPreset`, `IntegrationHook`
- **`minimal/`** — Base profile: permissive defaults, core config

### plugins (Extensions)

- **`msr/`** — Example plugin: AI policy advisory with 5 organization type presets (municipal, enterprise, nonprofit, education, healthcare)

### agents (Built-in)

**Advisory/Meta Agents:**
- **`ceo/`** — `CEOAdvisorAgent` — Strategic leadership guidance
- **`cto/`** — `CTOAdvisorAgent` — Technical strategy and architecture
- **`agent_builder/`** — `AgentBuilderAgent` — HR: onboarding, certification, registration. Includes `CertificationEngine` (12 checks) and `AgentSpec`/`OnboardingResult` schemas
- **`chat_advisor/`** — `ChatAdvisorAgent` — Generic chat advisory pattern

**Operational Agents:**
- **`researcher/`** — `ResearcherAgent` — Topic investigation and structured research reports
- **`optimizer/`** — `OptimizerAgent` — LLM cost/performance optimization analysis
- **`qa_specialist/`** — `QASpecialistAgent` — Test planning, coverage analysis, quality gates
- **`security_reviewer/`** — `SecurityReviewerAgent` — Vulnerability assessment and security audit
- **`technical_writer/`** — `TechnicalWriterAgent` — Documentation generation and review

## Data Flow

### Agent Execution

```
AgentInput (data + context + policy_attachments)
    │
    ▼
BaseAgent.execute()
    │
    ├── call_llm() → LLMBackend.complete() → LLMResponse
    ├── parse_json_response()
    └── get_metadata()
    │
    ▼
AgentOutput (result + metadata + policy_report)
```

### Pipeline Execution

```
initial_input + AgentContext
    │
    ▼
PipelineCoordinator.run()
    │
    ├── Stage 1: [agent_a] → output_a → context.upstream_outputs
    ├── Stage 2: [agent_b, agent_c] (parallel) → output_b, output_c
    └── Stage 3: [agent_d] (required) → output_d
    │
    ▼
PipelineResult (success, outputs, timing, errors)
```

### Policy Evaluation

```
PolicyEngine.evaluate_pre(agent_name, input_data)
    │
    ├── Gate 1: TestSuccessGate → GateResult (pass/fail)
    ├── Gate 2: SecurityValidationGate → GateResult
    ├── ...
    └── Gate 7: ApprovalGate → GateResult
    │
    ▼
PolicyDecision (allowed, gates_passed, gates_failed, violations)
    │
    ├── Development tier: allowed = True (warnings only)
    ├── Test tier: allowed = (no failures)
    └── Production tier: allowed = (no failures, strict)
```

## Extension Points

1. **Custom agents** — Subclass `BaseAgent`, implement `get_system_prompt()` and `execute()`
2. **Custom LLM backends** — Subclass `LLMBackend`, implement `complete()`
3. **Custom policy gates** — Subclass `PolicyGate`, implement `evaluate()`
4. **Custom profiles** — Create a module with `register(registry)` function
5. **Custom channels** — Subclass `BaseChannel`, implement `send_message()` and `handle_message()`
