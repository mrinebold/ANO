# ANO Foundation: A Framework for Building Agent-Native Organizations

**Abstract.** As large language model (LLM) agents transition from isolated tools to persistent organizational participants, existing orchestration frameworks focus narrowly on task execution while neglecting the structural, governance, and lifecycle concerns that arise when agents become first-class members of an organization. We introduce the *Agent-Native Organization* (ANO) — an organizational model where AI agents hold defined roles, report through management hierarchies, undergo formal onboarding, and operate under tiered policy governance. We present **ANO Foundation**, an open-source Python framework that operationalizes this model through seven composable modules: a core type system, pluggable LLM backends, agent and capability registries, a 7-gate policy engine with three-tier enforcement, multi-stage pipelines with parallel and sequential orchestration, persistent working memory, and deployment channels. The framework ships with nine prebuilt agents spanning advisory, research, optimization, QA, and security review roles. We describe the profile/plugin architecture that enables the same framework to serve different organizational contexts without conditional sprawl. Drawing on experience operating a 34-agent organization in production, we report lessons learned on certification-driven onboarding, tier-based policy enforcement, and the organizational primitives that distinguish agent-native design from conventional orchestration. We conclude with a comparison to existing multi-agent frameworks and directions for future work in agent governance, inter-organizational agent collaboration, and adaptive policy systems.

---

## 1. Introduction

The deployment of LLM-based agents has evolved rapidly from single-prompt interactions to multi-agent systems capable of research, analysis, code generation, and decision support [17]. Frameworks such as AutoGen [1], CrewAI [3], MetaGPT [2], and LangGraph [4] have demonstrated that collections of specialized agents can solve complex tasks through collaboration. However, these frameworks primarily address *task orchestration* — the mechanics of routing messages between agents — while treating organizational concerns as external.

When organizations deploy dozens of agents in production, new challenges emerge that orchestration alone does not address:

- **Identity and onboarding.** Who is this agent? What are its capabilities? Has it been certified to operate?
- **Governance and policy.** What checks must pass before an agent executes? Do the rules differ between development and production?
- **Organizational structure.** Who does this agent report to? What team is it on? How do agents collaborate across team boundaries?
- **Lifecycle management.** How are agents registered, discovered, versioned, and retired?
- **Deployment flexibility.** Can the same agent serve users via a Telegram bot, a web widget, or a CLI without modification?

We argue that addressing these concerns requires a shift from thinking about *multi-agent systems* to thinking about *Agent-Native Organizations* — organizations where agents are first-class members with roles, responsibilities, reporting structures, and governance frameworks analogous to those applied to human employees.

This paper makes three contributions:

1. **A definition and model** for Agent-Native Organizations that extends existing multi-agent paradigms with organizational primitives (Section 2).
2. **ANO Foundation**, an open-source framework that operationalizes the ANO model through seven composable modules and nine prebuilt agents (Sections 3–10).
3. **Lessons learned** from operating a 34-agent ANO in production, including insights on certification, policy enforcement, and organizational scaling (Section 11).

## 2. The Agent-Native Organization Model

### 2.1 Definition

An **Agent-Native Organization (ANO)** is a software system in which AI agents are treated as first-class organizational members — not merely as tools invoked on demand, but as persistent entities with defined roles, team assignments, reporting relationships, capability declarations, and governance constraints.

This definition draws on and extends three bodies of work:

1. **Agency theory applied to AI.** Humberd and Latham [10] trace the evolution of AI from a passive tool to an active "agent of the firm," applying principal-agent theory to examine delegation, monitoring, and accountability when AI acts on behalf of an organization.
2. **The agentic organization.** McKinsey's analysis of "agentic organizations" [11] describes a paradigm where AI-first workflows replace traditional process chains, with agents operating as autonomous team members rather than automation scripts.
3. **Generative agents.** Park et al. [16] demonstrate that LLM agents with memory, reflection, and planning can simulate believable social behavior — a prerequisite for agents functioning as organizational participants rather than stateless responders.

### 2.2 Organizational Primitives

An ANO extends multi-agent orchestration with six primitives:

| Primitive | Description | Framework Module |
|-----------|-------------|-----------------|
| **Role** | A named function within the organization (e.g., "research analyst") | Agent Builder |
| **Team** | A grouping of related roles (executive, development, research, etc.) | Agent Builder |
| **Hierarchy** | Reporting relationships between agents (reports-to, dotted-line) | Agent Builder |
| **Certification** | Formal validation that an agent meets organizational standards | Certification Engine |
| **Policy** | Governance gates that control agent execution by environment tier | Policy Engine |
| **Registry** | A discoverable directory of agents and their capabilities | Agent Registry |

These primitives are not merely metadata — they influence runtime behavior. A policy gate may check whether an agent's certification is current. A pipeline may route outputs through a reporting hierarchy. A registry query may filter agents by team for capability-based dispatch.

**Roles and Teams** provide the structural vocabulary for an ANO. A role is a named function — not a task assignment, but a persistent organizational identity. An agent assigned the role "security reviewer" retains that role across all sessions, pipelines, and channels. Teams group related roles into functional units (e.g., a development team containing agents for frontend, backend, QA, and security). The `TeamType` enum defines seven categories: `EXECUTIVE`, `DEVELOPMENT`, `OPERATIONS`, `RESEARCH`, `COMMUNICATIONS`, `COORDINATION`, and `CUSTOM`. This taxonomy emerged from observing recurring patterns in production deployments where ad hoc team naming led to inconsistent categorization.

**Hierarchy** introduces reporting relationships that model delegation and escalation. An agent's `ReportingRelationship` specifies a primary `reports_to` supervisor, optional `dotted_line_to` secondary relationships, and an assigned `orchestrator` for pipeline coordination. These relationships are not merely documentation — they determine how the Agent Builder wires agents into the organizational graph, and they enable downstream systems to route escalations, aggregate team outputs, and enforce approval chains.

**Certification** formalizes the transition from "code that exists" to "agent that is authorized to operate." Without certification, organizations accumulate agents with missing capabilities, conflicting names, and incomplete specifications. The certification engine's 12-check suite provides a quality gate that catches these issues before an agent enters the registry. The distinction between required checks (which block onboarding) and advisory checks (which produce warnings) reflects a deliberate design choice: minimum standards are enforced, while best practices are encouraged without creating friction.

**Policy** governs what agents can do at runtime, varying by environment tier. This is the mechanism that prevents a development-mode agent from accidentally executing production operations, and that ensures production agents pass all governance checks before acting. Policy is the runtime complement to certification's build-time validation.

**Registry** provides discoverability — the ability for pipelines, coordinators, and operators to find agents by name, capability, or team. Without a registry, agent discovery depends on convention (file naming, import paths) rather than declaration, making it fragile and opaque.

### 2.3 Comparison to Existing Paradigms

| Paradigm | Agents as... | Governance | Structure | Lifecycle |
|----------|-------------|-----------|-----------|-----------|
| **Tool Calling** | Functions | None | Flat | Implicit |
| **Multi-Agent Chat** | Conversation participants | Implicit | Ad hoc | Session-scoped |
| **Orchestration** | Pipeline stages | External | DAG-defined | Deployment-scoped |
| **Agent-Native Org** | Organizational members | Policy engine, tiered | Hierarchy, teams | Onboarding → registry → retirement |

## 3. Architecture Overview

ANO Foundation is structured as seven composable modules with a strict dependency hierarchy:

```
                    ┌─────────────┐
                    │   ano_core   │  Types, Settings, Errors, Environment
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──┐  ┌──────▼─────┐  ┌──▼──────────┐
     │  registry  │  │   policy   │  │agent_framework│
     └─────┬──────┘  └──────┬─────┘  └──────┬───────┘
           │                │               │
           └────────┬───────┘               │
                    │                       │
              ┌─────▼──────┐          ┌─────▼──────┐
              │  pipeline   │          │   memory    │
              └─────┬──────┘          └────────────┘
                    │
              ┌─────▼──────┐
              │  profiles   │
              └─────┬──────┘
                    │
           ┌────────┼────────┐
           │        │        │
     ┌─────▼──┐ ┌───▼───┐ ┌─▼──────┐
     │ agents  │ │plugins│ │channels│
     └────────┘ └───────┘ └────────┘
```

**Design principle: no conditional sprawl.** The architecture enforces a strict separation between *what the framework can do* (defined by modules) and *how it is configured* (defined by profiles). Core module code never checks which profile is active — it reads from a `ProfileRegistry` that profiles populate at startup. This eliminates the `if profile == "X"` conditionals that typically accumulate in multi-tenant systems.

### 3.1 Module Summary

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `ano_core` | Shared types, settings, errors, environment detection | `AnoSettings`, `OrgProfile`, `AgentContext`, `EnvironmentTier` |
| `agent_framework` | Agent base class, LLM abstraction, I/O validation | `BaseAgent`, `LLMBackend`, `AnthropicBackend`, `OpenAIBackend` |
| `registry` | Agent and capability discovery | `AgentRegistry`, `CapabilityRegistry`, `@register_agent` |
| `policy` | Governance gates, tier enforcement | `PolicyEngine`, `PolicyGate`, 7 built-in gates |
| `pipeline` | Multi-stage orchestration | `Pipeline`, `Stage`, `PipelineCoordinator` |
| `memory` | Persistent working state | `WorkingMemory`, `WorkingState`, `TaskInfo` |
| `channels` | End-user deployment | `BaseChannel`, `TelegramBotService`, `WebChatHandler`, `CLIRepl` |

### 3.2 Prebuilt Agents

ANO Foundation ships with nine agents that demonstrate framework capabilities and serve as starting points for organizational customization:

| Agent | Role | Category |
|-------|------|----------|
| `CEOAdvisorAgent` | Strategic leadership guidance | Advisory |
| `CTOAdvisorAgent` | Technical strategy and architecture | Advisory |
| `AgentBuilderAgent` | Onboarding, certification, registry management | Meta/HR |
| `ChatAdvisorAgent` | Generic conversational advisory | Advisory |
| `ResearcherAgent` | Topic investigation and structured reports | Operational |
| `OptimizerAgent` | LLM cost and performance optimization analysis | Operational |
| `QASpecialistAgent` | Test planning, coverage analysis, quality gates | Operational |
| `SecurityReviewerAgent` | Vulnerability assessment and security audit | Operational |
| `TechnicalWriterAgent` | Documentation generation and review | Operational |

These agents are fully functional implementations (not stubs) that pass the certification engine's 12-check suite. They serve a dual purpose: as ready-to-use capabilities for common organizational functions, and as reference implementations for developers building custom agents.

## 4. Core Type System

The `ano_core` module establishes the data contracts that all other modules depend on. Following Pydantic's validation model, every inter-module boundary is defined by typed models. This design ensures that data flowing between modules is validated at each boundary, catching integration errors at parse time rather than at runtime deep within agent logic.

### 4.1 Organization and Context Models

**`OrgProfile`** describes the organization context — name, type, regulatory context, and extensible metadata. This model enables agents to adapt behavior based on organizational characteristics without hard-coding organizational knowledge. For example, a compliance-checking agent serving a healthcare organization can adjust its analysis based on the `regulatory_context` field without the agent code containing any healthcare-specific conditionals. The organizational knowledge lives in the profile, not in the agent.

**`AgentContext`** is the runtime context passed to every agent execution. It carries the `OrgProfile`, upstream pipeline outputs from prior stages, and any additional metadata that the execution environment provides. The `upstream_outputs` dictionary is the mechanism by which pipeline stages communicate — each agent receives the accumulated outputs of all agents that executed before it. This design eliminates the need for agents to know about each other directly; they simply consume structured data from their context.

### 4.2 Agent I/O Models

**`AgentInput`** wraps the data provided to an agent's `execute()` method. Beyond the raw input data, it carries metadata about the request — who initiated it, what channel it arrived through, and what upstream context is available. This metadata enables agents to adjust their behavior based on the execution context (e.g., providing more concise responses for Telegram channels with message length limits versus detailed analysis for web chat sessions).

**`AgentOutput`** wraps the agent's response with structured metadata via `AgentMetadata`: the agent's name and version, execution timestamps (`started_at`, `completed_at`), LLM call count, and total tokens consumed. This metadata is essential for operational visibility — operators can track which agents are consuming the most resources, which are slowest, and which are producing the most value.

### 4.3 Environment Tier

**`EnvironmentTier`** is an enum with three values: `DEVELOPMENT`, `TEST`, and `PRODUCTION`. This seemingly simple type has outsized influence on framework behavior. The tier controls:

- **Policy enforcement strictness** — Development warns; Test blocks; Production strictly blocks
- **Logging verbosity** — Development enables debug logging; Production restricts to warnings and errors
- **Feature availability** — Experimental features can be gated to Development only
- **Gate configuration** — `get_tier_policy()` returns different gate sets per tier (Development: test + security; Test: test + file + quality + security; Production: all 7 gates)

The tier is detected automatically via the `detect_environment()` function, which reads the `ANO_ENV` environment variable, with `DEVELOPMENT` as the default. The associated `TierRestrictions` dataclass captures the specific constraints for each tier.

### 4.4 Error Hierarchy

The error hierarchy roots at `ANOError` with six domain-specific subclasses:

| Error | Module | When Raised |
|-------|--------|-------------|
| `AgentExecutionError` | `agent_framework` | Agent's `execute()` or `call_llm()` fails |
| `LLMBackendError` | `agent_framework.llm` | LLM API call fails (timeout, auth, rate limit) |
| `PolicyViolationError` | `policy` | Agent execution blocked by policy gate |
| `RegistryError` | `registry` | Agent not found, duplicate registration |
| `ConfigurationError` | `ano_core` | Invalid settings, missing API keys, bad profile |
| `ChannelError` | `channels` | Message delivery failure, webhook validation error |

This hierarchy enables precise error handling at module boundaries. A `PipelineCoordinator` can catch `PolicyViolationError` separately from `AgentExecutionError`, applying different recovery strategies (skip vs. abort) depending on the error type and the stage's `required` flag.

### 4.5 Settings Management

`AnoSettings` extends Pydantic's `BaseSettings` to provide configuration management with environment variable support. It loads from `.env` files and optional TOML configuration, providing typed access to `ANO_PROFILE`, `ANO_ENV`, `ANO_FEATURES`, LLM API keys (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`), and framework parameters. The settings object is a singleton accessed via `ano_core.settings.settings`, ensuring consistent configuration across all modules.

## 5. Pluggable LLM Backends

Agent code should not be coupled to a specific LLM provider. ANO Foundation defines an `LLMBackend` abstract base class with a single method:

```python
class LLMBackend(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str,
                       max_tokens: int = 4096, temperature: float = 0.3,
                       **kwargs: Any) -> LLMResponse:
        ...
```

Three backends ship with the framework:

| Backend | Provider | Use Case |
|---------|----------|----------|
| `AnthropicBackend` | Anthropic Claude | Production agents |
| `OpenAIBackend` | OpenAI GPT | Alternative provider |
| `LocalBackend` | Deterministic responses | Testing, development |

The `LocalBackend` deserves special mention: it returns configurable static responses, enabling the entire agent test suite to run without API calls. This is critical for CI/CD pipelines where LLM calls would introduce cost, latency, and non-determinism.

`BaseAgent.call_llm()` delegates to whatever backend is injected at construction time, and `parse_json_response()` provides safe JSON extraction with fallback handling — stripping markdown code fences, parsing JSON, and falling back to `{"raw_text": text}` on decode errors rather than raising exceptions. This pattern ensures that switching from Claude to GPT (or to a local model for testing) requires changing a single constructor argument, not modifying agent logic.

### 5.1 Response Tracking

Every LLM call returns an `LLMResponse` dataclass containing not just the generated text but also operational metadata:

- **`model`** — The specific model identifier used (e.g., `claude-sonnet-4-5-20250929`)
- **`input_tokens` / `output_tokens`** — Token counts for cost tracking
- **`latency_ms`** — Round-trip time for performance monitoring
- **`metadata`** — Extensible dictionary for provider-specific data

`BaseAgent` automatically aggregates these metrics across calls, maintaining `_llm_call_count`, `_total_input_tokens`, and `_total_output_tokens` counters that are exposed via `get_metadata()`. This enables pipeline-level cost attribution — the `PipelineCoordinator` can report total token consumption per stage and per agent, supporting the economic modeling discussed in Section 13.

### 5.2 Backend Selection

The `get_default_backend()` factory function reads the `DEFAULT_LLM_PROVIDER` setting and returns the appropriate backend instance. It uses lazy imports to avoid requiring all provider SDKs at install time — only the configured provider's SDK must be installed. If the configured provider's API key is missing, it raises a `ConfigurationError` with a clear message rather than failing later during agent execution with an opaque authentication error.

### 5.3 Testing Without LLM Calls

The `LocalBackend` is arguably the most important backend for framework development. It returns configurable static responses with zero latency, enabling the full test suite (215 tests across all modules) to run deterministically without API calls. This eliminates three sources of test fragility: cost (API charges per test run), latency (seconds per call vs. microseconds for local), and non-determinism (LLM outputs vary across calls). In CI/CD pipelines, the `LocalBackend` is the default, ensuring that tests validate framework logic rather than LLM behavior.

## 6. Agent Builder: Onboarding as a First-Class Concern

### 6.1 Motivation

In traditional multi-agent frameworks, adding a new agent means writing code and hoping it integrates correctly. There is no formal process for validating that the agent has the required attributes, follows naming conventions, declares capabilities, or fits into the organizational structure.

The Agent Builder addresses this gap by treating agent onboarding as a structured pipeline — analogous to HR onboarding in a human organization:

```
validate → certify → generate → register → wire_hierarchy
```

### 6.2 Agent Specification

Every agent begins as an `AgentSpec` — a declarative description that captures:

- **Identity**: name (3–50 chars, lowercase, no reserved words), display name, description
- **Role and Team**: what the agent does and which team it belongs to (executive, development, research, operations, communications, coordination, custom)
- **Capabilities**: named capabilities with categories (research, writing, analysis, compliance, communication, development, testing, security) and optional MCP tool declarations
- **Reporting**: who the agent reports to, dotted-line relationships, assigned orchestrator
- **Personality**: description, response style, collaboration style — guiding prompt engineering
- **Policy**: attached policy bundle ID and version

### 6.3 Certification Engine

The certification engine runs **12 checks** against each specification:

| Category | Count | Behavior |
|----------|-------|----------|
| **Required** | 6 | Must pass: name format, uniqueness, not reserved, has capabilities, has role, has team |
| **Advisory** | 5 | Warnings: has personality, has reporting, has description, has policy, capability tools |
| **Info** | 1 | Informational: lists MCP servers referenced in tools |

The scoring formula is straightforward: `score = passed / total`. Overall pass requires all 6 required checks. Advisory failures produce warnings but do not block onboarding, allowing rapid iteration during development while ensuring minimum standards.

### 6.4 Code Generation

Upon successful certification, the builder generates three files from templates:

- `agents/{name}/agent.py` — Python module extending `BaseAgent`
- `agents/{name}/__init__.py` — Package init with class export
- `agents/{name}/skill.md` — Markdown documentation of the agent's role, capabilities, and personality

Templates use simple variable substitution (`{{AGENT_NAME}}`, `{{CLASS_NAME}}`, `{{ROLE}}`, etc.) with inline fallbacks if template files are missing. This approach is deliberately simple — avoiding template engines like Jinja2 keeps the dependency footprint minimal.

### 6.5 Hierarchy Wiring

After registration, the builder wires the agent into the organizational hierarchy based on the `reporting.reports_to` field in the spec. This produces a supervisor-to-reports mapping that downstream systems can use for routing, escalation, and organizational queries.

## 7. Policy Engine: Governance by Design

### 7.1 Design Philosophy

Governance in agent systems is frequently an afterthought — added as external monitoring after agents are already running in production. ANO Foundation inverts this by making policy evaluation a built-in, pre-execution concern.

The policy engine is inspired by the "policy-as-code" movement exemplified by Open Policy Agent [18], but specialized for agent execution contexts. Rather than a general-purpose policy language, it provides domain-specific gates that evaluate agent-relevant conditions.

### 7.2 Gate Architecture

A **gate** is a single check that returns pass or fail with context:

```python
class PolicyGate(ABC):
    @abstractmethod
    async def evaluate(self, context: dict) -> GateResult:
        ...
```

Seven gates ship with the framework:

| Gate | What It Checks |
|------|---------------|
| **Test Success** | Automated tests have passed |
| **File Verification** | Required files exist with correct integrity |
| **Branch Policy** | Operations target the correct branch for the environment |
| **Documentation** | Changes include appropriate documentation |
| **Code Quality** | Code passes linting and type checking |
| **Security Validation** | No security vulnerabilities or exposed secrets |
| **Approval** | Human approval has been granted for sensitive operations |

These seven gates are **build-time gates** — they evaluate static context such as test results, branch names, and approval records. The framework also provides **runtime gates** implemented as policy hooks (`AuditLoggingHook`, `DataSanitizationHook`, `RateLimitHook`, `CostTrackingHook`) that intercept the agent execution lifecycle with live operational concerns like rate limiting, PII sanitization, cost tracking, and audit logging. Both categories are invoked by the `PipelineCoordinator`, with hooks running before and after the build-time gate evaluations to provide defense-in-depth governance.

### 7.3 Three-Tier Enforcement

The engine's behavior varies by environment tier, implementing a graduated enforcement model:

| Tier | On Gate Failure | Rationale |
|------|----------------|-----------|
| **Development** | Log warning, allow execution | Enables rapid iteration without blocking |
| **Test** | Block execution | Catches issues before production |
| **Production** | Strictly block, log error | Maximum safety for live systems |

This design reflects a pragmatic insight: requiring all gates to pass in development would cripple iteration speed, while allowing failures in production would undermine trust. The three-tier model provides a smooth ramp from experimentation to deployment.

### 7.4 Pre and Post Evaluation

The engine supports both pre-execution checks (validate inputs, permissions, environment state) and post-execution checks (validate outputs, security, quality). When used with the `PipelineCoordinator`, the full lifecycle includes both hook and gate evaluation:

```python
from policy.hooks import AuditLoggingHook, RateLimitHook

coordinator = PipelineCoordinator(
    pipeline=my_pipeline,
    registry=registry,
    policy_engine=engine,
    hooks=[AuditLoggingHook(), RateLimitHook(max_executions_per_minute=30)],
)
# Lifecycle per agent: hooks.before → engine.evaluate_pre → execute → engine.evaluate_post → hooks.after
result = await coordinator.run(input_data, context)
```

### 7.5 Runtime Policy Hooks

While the seven build-time gates evaluate static context, the four runtime hooks intercept the live agent execution lifecycle:

**`AuditLoggingHook`** logs all agent inputs and outputs to a structured JSONL file, providing a compliance-grade audit trail. Every execution is recorded with timestamps, agent identity, input data, output data, and execution duration. This hook is essential for organizations subject to regulatory requirements that mandate auditability of AI-driven decisions. The hook accepts a configurable `log_path` and writes entries that are both human-readable and machine-parseable.

**`DataSanitizationHook`** inspects agent inputs and outputs for personally identifiable information (PII) and credentials, redacting them before they reach the agent or leave the system. This provides a defense-in-depth layer — even if an agent's system prompt does not explicitly instruct PII avoidance, the sanitization hook catches sensitive data at the framework level.

**`RateLimitHook`** enforces per-agent execution rate limits using configurable `max_per_minute` and `max_per_hour` thresholds. When an agent exceeds its rate limit, the hook blocks execution before the agent's `execute()` method is called, preventing runaway loops and protecting LLM API budgets. The rate limiter uses a sliding window algorithm that tracks execution timestamps per agent name.

**`CostTrackingHook`** monitors LLM token consumption and estimated costs per agent execution. It reads the `AgentMetadata` produced by `BaseAgent.get_metadata()` after each execution and maintains cumulative cost records. This hook provides the data foundation for the economic models discussed in Section 13 — without per-agent cost tracking, organizations cannot make informed decisions about resource allocation.

All four hooks implement the `PolicyHook` abstract base class, which defines `before_execute(agent_name, input_data, context)` and `after_execute(agent_name, output, context)` methods. The `before_execute` method returns a result that can either allow execution (optionally with modified input data), or block it entirely. This gives hooks the power to both observe and intervene in the execution lifecycle.

### 7.6 Violations and Remediation

When a gate fails, the engine produces a `PolicyViolation` with four fields: `gate` (which gate failed), `severity` (error level), `message` (what went wrong), and `remediation` (how to fix it). Remediation guidance is tier-specific:

- **Development**: Base remediation only (e.g., "Run the test suite before proceeding")
- **Test**: Base remediation plus a note about approval workflows (e.g., "... or obtain explicit approval to bypass this gate")
- **Production**: Base remediation plus strict compliance language (e.g., "Strict compliance required in production. No bypasses permitted without documented exception")

This graduated messaging helps developers understand not just *what* failed but *how seriously* it matters in the current context. A test failure in development is informational; the same failure in production is a hard stop with explicit remediation steps.

## 8. Pipeline Orchestration

### 8.1 Declarative Pipeline Definition

ANO Foundation provides a declarative pipeline system that orchestrates multi-agent workflows through ordered stages. A `Pipeline` is composed of `Stage` objects, each specifying which agents participate and whether they execute in parallel or sequentially:

```python
from pipeline.pipeline import Pipeline, Stage

pipeline = Pipeline(name="research-pipeline", stages=[
    Stage(name="gather", agents=["researcher"], required=True),
    Stage(name="analyze", agents=["optimizer", "security-reviewer"], parallel=True),
    Stage(name="report", agents=["technical-writer"], required=True),
])
```

Each `Stage` declares:
- **`agents`** — One or more agent names (must exist in the registry)
- **`parallel`** — Whether agents in the stage execute concurrently via `asyncio.gather` (default: sequential)
- **`required`** — Whether stage failure aborts the pipeline (default: `True`)

The `Pipeline` validates its structure on construction (at least one stage, no duplicate stage names) and can validate agent availability against a registry before execution.

### 8.2 The Pipeline Coordinator

The `PipelineCoordinator` is the runtime engine that executes pipelines with full policy integration. For each agent in each stage, it performs a five-step execution lifecycle:

1. **Pre-hooks** — Run `before_execute()` on all registered `PolicyHook` instances. Any hook can block execution or modify input data.
2. **Pre-policy** — Evaluate build-time gates via `PolicyEngine.evaluate_pre()`.
3. **Execute** — Run the agent's `execute()` method with an `AgentInput` constructed from stage input data.
4. **Post-policy** — Evaluate build-time gates via `PolicyEngine.evaluate_post()`.
5. **Post-hooks** — Run `after_execute()` on all hooks. Any hook can reject the output.

This five-step lifecycle ensures that every agent execution — whether in a pipeline or standalone — passes through the same governance checks.

### 8.3 Data Flow Between Stages

The coordinator manages inter-stage data flow through `context.upstream_outputs`, a dictionary that accumulates agent outputs as the pipeline progresses. Each stage receives the merged outputs of all preceding stages, enabling downstream agents to build on upstream results without explicit wiring:

```python
# Stage 1 output: {"researcher": {...}}
# Stage 2 receives: context.upstream_outputs = {"researcher": {...}}
# Stage 2 output: {"optimizer": {...}, "security-reviewer": {...}}
# Stage 3 receives: context.upstream_outputs = {"researcher": {...}, "optimizer": {...}, "security-reviewer": {...}}
```

For parallel stages, all agents receive the same input snapshot and their outputs are merged after completion. For sequential stages, each agent receives the cumulative outputs of prior agents within the same stage.

### 8.4 Pipeline Results

A `PipelineResult` captures the outcome of a pipeline run:

- **`success`** — `True` if no required stages failed
- **`stages_completed` / `stages_failed`** — Lists of stage names
- **`outputs`** — Dictionary of agent name to output, accessible via `get_agent_output(agent_name)`
- **`duration_ms`** — Total pipeline execution time

Optional (non-required) stages that fail produce warnings but do not abort the pipeline, enabling graceful degradation in workflows where some analysis steps are best-effort.

## 9. Profile/Plugin Architecture

### 9.1 The Conditional Sprawl Problem

Multi-tenant systems commonly accumulate conditional logic: `if client == "A": ...` scattered across the codebase. Each new client adds more branches, making the code harder to test, reason about, and maintain. ANO Foundation avoids this through a profile/plugin architecture.

### 9.2 How Profiles Work

```
ANO_PROFILE=msr  →  load_profile("msr")  →  ProfileRegistry
                          │                        │
                          ├── Load minimal first    ├── Agent classes
                          └── Layer on top          ├── Config values
                                                    ├── Policy presets
                                                    ├── Integration hooks
                                                    └── Feature flags
```

1. The `minimal` profile is **always loaded first** as a base layer with permissive defaults.
2. If a different profile is requested, it is **layered on top** — its values override minimal's.
3. `ANO_FEATURES` environment variable applies final feature flag overrides.
4. Core code reads from `ProfileRegistry` — it never checks which profile is active.

### 9.3 Profile Registry

The `ProfileRegistry` is a typed container that profiles populate:

- **Configuration values** — Key-value pairs (timeout, max agents, LLM model, etc.)
- **Policy presets** — Named configurations for different organizational contexts
- **Agent classes** — Registered agent implementations
- **Integration hooks** — Factory functions for extending framework behavior (LLM providers, storage backends, notification channels)
- **Feature flags** — Boolean toggles for optional capabilities

### 9.4 Plugin Example

A profile is simply a Python module with a `register(registry)` function:

```python
def register(registry):
    registry.set_config("max_concurrent_agents", 8)
    registry.set_config("policy_enforcement", True)
    registry.register_policy_preset(PolicyPreset(
        name="enterprise",
        description="Enterprise compliance preset",
        org_types=["enterprise"],
        regulatory_contexts=["sox", "gdpr"],
        config={"require_audit_trail": True},
    ))
    registry.set_feature("audit_trail", True)
```

This approach means adding support for a new organization type requires creating a single module — no changes to core framework code.

## 10. Deployment Channels

### 10.1 Channel Abstraction

The `BaseChannel` interface decouples agent logic from deployment targets:

```python
class BaseChannel(ABC):
    async def send_message(self, recipient_id: str, text: str, **kwargs) -> bool: ...
    async def handle_message(self, sender_id: str, text: str, metadata: dict = None) -> str: ...
    def set_agent(self, agent: Any) -> None: ...
```

An agent written once can be deployed to any channel without modification.

### 10.2 Telegram Channel

The Telegram channel is the most fully featured deployment target, reflecting the reality that messaging platforms are often the most natural interface for organizational agents. The implementation comprises five components:

**`TelegramBotService`** handles message routing with built-in rate limiting. The rate limiter uses a per-user sliding window algorithm — it tracks message timestamps for each user and rejects messages when the count within the sliding window exceeds a configurable threshold (default: 10 messages per minute). When a user is rate-limited, they receive a throttle message rather than a silent failure.

**`CommandRegistry`** provides `/command` parsing with support for bot-mention syntax (`/start@mybotname args`). Commands are registered with a name, handler function, description, and required access tier. The registry parses incoming messages to extract the command name and arguments, stripping bot mentions when present. Non-command messages are routed to either a custom message handler or the attached agent's `execute()` method.

**`TelegramAuth`** implements tier-based access control with three default tiers:

| Tier | Level | Features |
|------|-------|----------|
| `free` | 0 | help, start, info |
| `basic` | 1 | + query, analyze |
| `premium` | 2 | + export, custom |

Access checks work bidirectionally: by feature name (does this tier include the "analyze" feature?) and by tier hierarchy (is the user's tier level >= the required tier level?). Custom tiers can be defined via `TierConfig` objects, enabling organizations to model their specific access control requirements.

**`TelegramConfig`** centralizes configuration via environment variables: `TELEGRAM_BOT_TOKEN` (required), `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_WEBHOOK_URL`, `TELEGRAM_RATE_LIMIT` (default: 10/min), `TELEGRAM_MAX_MESSAGE_LENGTH` (4096), and `TELEGRAM_PARSE_MODE` (Markdown).

**`create_webhook_app()`** generates a FastAPI application with `GET /health` and `POST /webhook` endpoints. The webhook endpoint validates the `X-Telegram-Bot-Api-Secret-Token` header before processing updates, preventing unauthorized message injection.

The full message handling flow is: webhook receives update → validate secret → parse JSON → extract user info and text → check rate limit → parse command (if `/command`, route to `CommandRegistry` with tier check; otherwise, route to agent) → send response via Telegram API.

### 10.3 Web Chat Channel

The web chat channel provides a REST API suitable for embedding in web widgets and single-page applications:

- **`WebChatHandler`** manages sessions with automatic creation, 24-hour TTL, and periodic cleanup. Each session maintains a conversation history that is passed to the agent via `metadata["session_history"]`, enabling contextual multi-turn conversations. Sessions are stored in memory by default, with the expectation that production deployments will substitute a persistent backend (Redis, database).

- **`create_web_chat_app()`** produces a FastAPI application with three endpoints: `POST /chat` (send a message, receive a response with session ID), `GET /session/{session_id}` (retrieve session history), and `GET /health` (health check). The chat endpoint automatically creates new sessions for first-time messages and appends to existing sessions for returning users.

### 10.4 CLI REPL Channel

The CLI REPL provides zero-configuration local testing of any agent:

```python
repl = CLIRepl(agent=my_agent, prompt="agent> ")
await repl.run()
```

Built-in commands (`quit`/`exit`/`q`, `help`, `clear`) are handled locally; all other input is routed to the configured agent. The REPL is intentionally minimal — its purpose is to enable developers to test agent behavior interactively without setting up Telegram bots or web servers.

### 10.5 Custom Channels

Adding a new channel (e.g., Slack, Discord, email) requires subclassing `BaseChannel` and implementing two methods: `send_message()` for outbound messages and `handle_message()` for inbound routing. The framework normalizes async/sync agent results — implementations can call `hasattr(result, "__await__")` to handle both synchronous and asynchronous agents without separate code paths. A `channel_name` class attribute provides identity for logging and debugging. The `set_agent()` method allows runtime agent swapping, enabling scenarios like load balancing across agents or A/B testing different agent versions on the same channel.

## 11. Lessons from a Production ANO

This section draws on experience operating an ANO with 34 agents organized into multiple teams (development, research, coordination, executive advisory). Details are anonymized to protect proprietary aspects of the deployment.

### 11.1 Certification Prevents Configuration Drift

Before introducing the certification engine, agents were added ad hoc — a new Python file, a manual registry entry, and hope that the name, capabilities, and reporting structure were consistent. Over time, inconsistencies accumulated: agents without team assignments, capabilities without tool declarations, names that conflicted with reserved words.

The 12-check certification engine reduced these issues to near zero. The key insight is that **advisory checks matter as much as required checks** — they don't block onboarding but create visible warnings that encourage completeness. In our deployment, advisory compliance rose from ~40% to ~90% within weeks of introducing the certification engine, without any enforcement mandate.

### 11.2 Three-Tier Enforcement Is Essential

Early deployments used a single policy mode (effectively "always enforce"). This created two problems:

1. **Development friction.** Developers couldn't iterate quickly because every test run required passing all policy gates.
2. **Production false confidence.** When policies were relaxed to reduce friction, production environments lost their safety guarantees.

The three-tier model resolved both issues. Development environments warn but never block, preserving iteration speed. Production environments strictly enforce, preserving safety. Test environments serve as the validation bridge between the two.

### 11.3 Working Memory Enables Session Continuity

Agents that operate across sessions (e.g., a research agent that gathers sources over multiple days) need persistent state. The `WorkingMemory` module, which serializes state to Markdown files, proved surprisingly effective. The Markdown format is human-readable (operators can inspect an agent's state by reading a file), version-controllable, and parseable without specialized tooling.

Key fields that proved essential: current task (title, status, description), context notes (accumulated knowledge), next steps (planned actions), blockers (issues requiring external resolution), and session history (timestamped log of activities).

### 11.4 Profiles Prevent Organizational Lock-In

The profile/plugin system was introduced after encountering the conditional sprawl problem at scale. The original codebase contained over 40 conditional checks for organization-specific behavior. Migrating to profiles eliminated all of them, replacing scattered conditionals with a single `load_profile()` call that configures the entire framework.

The layered loading model (minimal first, then overlay) proved critical — it ensures that every configuration key has a sensible default even if a profile forgets to set it.

### 11.5 Agent Teams Need Explicit Coordination

Organizing agents into teams (development, research, coordination) improved discoverability and capability routing. However, cross-team coordination required explicit orchestration — agents did not naturally discover or collaborate with agents on other teams. The pipeline system addressed this by enabling multi-stage workflows that span teams, with the `PipelineCoordinator` managing data flow and policy enforcement across stage boundaries.

### 11.6 Markdown as a Persistence Format

The choice to persist agent working memory as Markdown files (rather than JSON, YAML, or a database) was initially a pragmatic shortcut, but it proved to be a genuine advantage. Markdown files are human-readable without tooling — an operator can `cat` an agent's WORKING.md to understand its current state, blockers, and recent actions. They are version-controllable — changes to agent state can be tracked in git, providing a history of state transitions. And they are parseable with simple string processing — the `parse_working_state()` and `render_working_state()` functions handle serialization without external dependencies. The tradeoff is that Markdown is less structured than JSON, making complex queries difficult. For the fields that working memory tracks (current task, context, next steps, blockers, session history, files modified, decisions made), the flat Markdown structure proved sufficient.

### 11.7 Local Testing Backend Is Non-Negotiable

The most impactful architectural decision for development velocity was providing a `LocalBackend` that returns deterministic responses without API calls. Before this existed, running the test suite required active API keys, cost real money, took minutes instead of seconds, and produced non-deterministic results that made test failures ambiguous (was it the code or the LLM?). After introducing `LocalBackend`, the test suite runs in under 10 seconds with zero API cost. The lesson: any framework that wraps LLM calls must provide a local testing mode as a first-class feature, not an afterthought.

### 11.8 Error Boundaries at Module Interfaces

The typed error hierarchy (`ANOError` → domain-specific subclasses) proved essential for composability. When a pipeline stage fails, the `PipelineCoordinator` needs to distinguish between a policy violation (potentially recoverable by changing environment tier or obtaining approval), an agent execution error (the agent's logic failed), and an LLM backend error (the API is down). Each requires a different recovery strategy: policy violations may be waived in development; agent errors may indicate a bug to fix; backend errors may resolve with a retry. Without typed errors, all failures look the same, forcing operators to parse error messages for root cause analysis.

### 11.9 Registry Discovery at Scale

With 34 agents, manual registry management becomes unsustainable. The `discover_agents()` function, which recursively scans packages for `BaseAgent` subclasses, eliminated the need for a hand-maintained registry file. Combined with the `@register_agent` decorator, agents self-register when imported. This pattern scales well — adding a new agent requires no changes to any central configuration file. The `CapabilityRegistry`'s many-to-many mapping between agents and capabilities enabled capability-based dispatch: "find me an agent that can do security analysis" returns results regardless of which team the agent belongs to.

## 12. Related Work

### 12.1 Multi-Agent Frameworks

**AutoGen** [1] pioneered the conversable agent paradigm, enabling customizable agents to interact through multi-turn conversations. Its strength is flexibility; its limitation is the lack of organizational primitives — agents are conversation participants, not organizational members.

**MetaGPT** [2] introduces Standard Operating Procedures (SOPs) into multi-agent workflows, assigning roles like "product manager" and "engineer" to agents. This represents a step toward organizational modeling, though the roles are task-pipeline specific rather than persistent organizational identities.

**CrewAI** [3] provides role-based orchestration with crews, tasks, and delegation. Its crew metaphor aligns with ANO teams, but it lacks formal onboarding, policy governance, and multi-tenant profile support.

**LangGraph** [4] offers graph-based agent orchestration with durable execution and human-in-the-loop support. Its stateful execution model is complementary to ANO Foundation's pipeline system, though it does not address organizational structure or policy enforcement.

**OpenAI Swarm** [5] demonstrates lightweight agent handoff patterns. Its simplicity is intentional (educational framework), but it highlights the design space between minimal orchestration and full organizational modeling.

**AWS Multi-Tenant Agentic AI** [19] addresses multi-tenancy for agentic systems at the infrastructure level, providing guidance on isolation, resource management, and cost allocation across tenants. ANO Foundation's profile system addresses the same multi-tenancy concern at the application level — different organizations (tenants) are served by different profiles, with shared framework code.

### 12.1.1 Feature Comparison

| Feature | AutoGen | MetaGPT | CrewAI | LangGraph | Swarm | **ANO Foundation** |
|---------|---------|---------|--------|-----------|-------|-------------------|
| Agent roles | Implicit | SOP-defined | Crew roles | Node-defined | Function-scoped | Persistent, typed |
| Team structure | None | Pipeline-implicit | Crews | Graph-implicit | None | Explicit teams, hierarchy |
| Agent onboarding | Manual | Manual | Manual | Manual | Manual | 12-check certification |
| Policy governance | None | None | None | Human-in-loop | None | 7 gates + 4 hooks, tiered |
| Multi-tenant | None | None | None | None | None | Profile/plugin system |
| LLM abstraction | Provider-specific | Provider-specific | Provider-specific | Provider-specific | OpenAI only | Pluggable backends |
| Deployment channels | Custom | Custom | Custom | Custom | None | Telegram, Web, CLI |
| Working memory | External | External | External | Checkpoints | None | Markdown-based |
| Testing without LLM | Manual mocks | Manual mocks | Manual mocks | Manual mocks | Manual mocks | `LocalBackend` built-in |
| Agent discovery | Import-based | Import-based | Import-based | Graph-defined | Import-based | Registry + decorator |

The table reveals that ANO Foundation's primary differentiators are in the organizational layer — certification, policy, multi-tenancy, and hierarchy — rather than in core orchestration capabilities, where overlap with existing frameworks is expected and intentional.

### 12.2 Governance Frameworks

The NIST AI Risk Management Framework [6] provides a voluntary governance structure with four functions (Govern, Map, Measure, Manage). ANO Foundation's policy engine operationalizes similar principles at the agent execution level — policy gates correspond to specific risk controls.

The EU AI Act [7] introduces risk-based classification for AI systems. ANO Foundation's three-tier enforcement model (development/test/production) provides a natural mapping for implementing risk-proportionate governance.

The OECD AI Principles [9] emphasize transparency, accountability, and robustness. The policy engine's violation tracking and remediation guidance support auditability, while the certification engine enforces minimum standards.

The World Economic Forum's framework for agent evaluation and governance [20] identifies dimensions of autonomy, efficacy, and generality that align with ANO Foundation's capability and policy models.

### 12.3 Agent Architecture Patterns

The ReAct pattern [13] (reasoning and acting interleaved) underpins most modern LLM agent architectures. ANO Foundation's `BaseAgent.call_llm()` supports ReAct-style execution through iterative prompt-response cycles.

Chain-of-thought prompting [15] and tool use [14] are foundational techniques that ANO agents leverage through their system prompts and LLM backend calls.

Park et al.'s generative agents [16] demonstrate that agents with memory and reflection can simulate believable organizational behavior — a key validation of the ANO premise that agents can function as persistent organizational members.

The survey by Wang et al. [17] provides a comprehensive taxonomy of LLM agent construction, application, and evaluation, situating ANO Foundation within the broader agent landscape.

### 12.4 Organizational Theory

Humberd and Latham [10] apply agency theory to examine AI as an "agent of the firm," tracing the evolution from tool to delegate to autonomous actor. Their analysis directly supports the ANO model's treatment of agents as organizational members with delegated authority and accountability requirements.

Constitutional AI [12] introduces principle-based self-alignment for AI systems. ANO Foundation's policy engine implements a complementary approach — external governance constraints rather than internal alignment — and the two approaches are synergistic.

## 13. Future Directions

### 13.1 Inter-Organizational Agent Collaboration

Current ANO deployments are single-organization. A natural extension is enabling agents from different ANOs to collaborate — a research agent in one organization requesting analysis from a specialist agent in another. This raises questions about trust, credential exchange, and cross-organizational policy enforcement.

### 13.2 Adaptive Policy Systems

The current policy engine uses static gates with fixed evaluation logic. Future work could introduce adaptive policies that learn from violation patterns, adjust thresholds based on agent track records, or recommend gate configurations based on organizational risk profiles.

### 13.3 Agent Performance Evaluation

ANOs currently lack formal mechanisms for evaluating agent performance over time. A performance management system — analogous to human performance reviews — could track output quality, policy compliance rates, resource consumption, and collaboration effectiveness, enabling data-driven decisions about agent roles and assignments.

> **Implementation note (2026-02-19):** MSR Research has implemented a concrete instantiation of this direction as the **Agent Autonomy Measurement Framework**. The framework records per-workflow-run scorecards in a shared `agent_autonomy_runs` table across two platforms (MSRResearch and CivicGrantsAI), computing a 1–10 autonomy score per run based on human interventions, tool error rate, reversibility, uncertainty signals, and recovery success. A four-mode Control Dial (Observer/Copilot/Operator/Night-Run) maps to existing policy gates, and a post-run eval harness measures completion rate, cost efficiency, and behavioral compliance (via Bloom violations). This provides an early data point for the agent performance evaluation systems described above. See PRD: `2026-02-19-1042_agent-autonomy-measurement-framework.prd.md`.

### 13.4 Economic Models for Agent Organizations

As agents consume computational resources (LLM tokens, API calls, storage), organizations need economic models for budgeting, cost allocation, and ROI measurement at the agent level. The policy engine's cost tracking hook provides a foundation, but comprehensive agent economics remains an open problem.

> **Implementation note (2026-02-19):** The Autonomy Measurement Framework addresses this gap partially by recording `cost_estimate_usd`, `token_usage_total`, and `token_usage_by_stage` per workflow run, enabling cost-per-run trending and budget gate enforcement. MSR Research's combined monthly LLM spend (~$112/month across two platforms) is now visible in a unified dashboard, with the OpenClaw heartbeat budget gate extended to cover all workflow costs (not just heartbeat session costs).

### 13.5 Formal Verification of Agent Policies

The current policy engine evaluates gates at runtime. Formal verification techniques could enable static analysis of policy configurations — proving, for example, that a given gate configuration guarantees certain safety properties before any agent executes.

## 14. Conclusion

Agent-Native Organizations represent a paradigm shift from viewing AI agents as tools to treating them as organizational members. This shift introduces challenges — onboarding, governance, hierarchy, lifecycle management — that existing orchestration frameworks do not address.

ANO Foundation provides a concrete, open-source implementation of this paradigm through seven composable modules and nine prebuilt agents. The framework comprises approximately 4,500 lines of production code and 5,200 lines of tests (215 tests across all modules), with four core dependencies (`pydantic`, `pydantic-settings`, `httpx`, `python-json-logger`) and optional dependencies for specific LLM providers and deployment channels. The minimal dependency footprint reflects a deliberate design choice: framework adoption should not require accepting a large transitive dependency graph.

The framework's key design decisions — profile-driven configuration, certification-based onboarding, three-tier policy enforcement, and channel-agnostic deployment — emerged from practical experience operating a 34-agent organization in production. Each decision addressed a specific pain point: profiles eliminated conditional sprawl across 40+ organization-specific checks; certification reduced configuration drift to near zero; three-tier enforcement resolved the tension between development velocity and production safety; and channel abstraction enabled the same agents to serve users via Telegram, web chat, and CLI without modification.

The feature comparison in Section 12 reveals that ANO Foundation's primary contribution is not in core orchestration — where AutoGen, CrewAI, MetaGPT, and LangGraph are capable — but in the organizational layer that sits above orchestration. Certification, policy governance, hierarchical structure, multi-tenant profiles, and persistent working memory are the primitives that enable the transition from "a collection of agents" to "an organization of agents."

We believe the ANO model will become increasingly relevant as organizations scale from a handful of experimental agents to dozens or hundreds of production agents. The organizational primitives that ANO Foundation provides — roles, teams, hierarchies, certification, policy, and registries — are not luxuries for large deployments; they are necessities that prevent the chaos of ungoverned agent proliferation.

ANO Foundation is available as open-source software under the Apache 2.0 License at `https://github.com/ano-foundation/ano-foundation`.

---

## References

[1] Q. Wu, G. Bansal, J. Zhang, Y. Wu, S. Zhang, E. Zhu, B. Li, L. Jiang, X. Zhang, and C. Wang, "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation," *arXiv preprint arXiv:2308.08155*, 2023. Available: https://arxiv.org/abs/2308.08155

[2] S. Hong, M. Zhuge, J. Chen, X. Zheng, Y. Cheng, C. Zhang, J. Wang, Z. Wang, S. K. S. Yau, Z. Lin, L. Zhou, C. Ran, L. Xiao, C. Wu, and J. Schmidhuber, "MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework," *arXiv preprint arXiv:2308.00352*, 2023. Available: https://arxiv.org/abs/2308.00352

[3] J. Moura, "CrewAI: Framework for Orchestrating Role-Playing, Autonomous AI Agents," Open-source software, 2024. Available: https://github.com/crewAIInc/crewAI

[4] LangChain, Inc., "LangGraph: Low-Level Orchestration Framework for Stateful Agents," Open-source software, 2024. Available: https://github.com/langchain-ai/langgraph

[5] OpenAI, "Swarm: Educational Framework Exploring Ergonomic, Lightweight Multi-Agent Orchestration," Open-source software, 2024. Available: https://github.com/openai/swarm

[6] E. Tabassi, "Artificial Intelligence Risk Management Framework (AI RMF 1.0)," National Institute of Standards and Technology, NIST AI 100-1, 2023. DOI: 10.6028/NIST.AI.100-1. Available: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10

[7] European Parliament and Council, "Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)," *Official Journal of the European Union*, L 2024/1689, 2024. Available: https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng

[8] IEEE, "IEEE 7000-2021: Model Process for Addressing Ethical Concerns During System Design," IEEE Standards Association, 2021. Available: https://standards.ieee.org/ieee/7000/6781/

[9] OECD, "Recommendation of the Council on Artificial Intelligence," OECD/LEGAL/0449, 2019 (updated 2024). Available: https://oecd.ai/en/ai-principles

[10] B. K. Humberd and S. F. Latham, "When AI Becomes an Agent of the Firm: Examining the Evolution of AI in Organizations Through an Agency Theory Lens," *Journal of Management Studies*, 2025. DOI: 10.1111/joms.13274. Available: https://onlinelibrary.wiley.com/doi/full/10.1111/joms.13274

[11] A. Sukharevsky, A. Krivkovich, A. Gast, A. Storozhev, D. Maor, D. Mahadevan, L. Hamalainen, and S. Durth, "The Agentic Organization: Contours of the Next Paradigm for the AI Era," McKinsey & Company, 2025. Available: https://www.mckinsey.com/capabilities/people-and-organizational-performance/our-insights/the-agentic-organization-contours-of-the-next-paradigm-for-the-ai-era

[12] Y. Bai, S. Kadavath, S. Kundu, A. Askell, J. Kernion, A. Jones, A. Chen, A. Goldie, et al., "Constitutional AI: Harmlessness from AI Feedback," *arXiv preprint arXiv:2212.08073*, 2022. Available: https://arxiv.org/abs/2212.08073

[13] S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao, "ReAct: Synergizing Reasoning and Acting in Language Models," in *Proc. 11th International Conference on Learning Representations (ICLR)*, 2023. Available: https://arxiv.org/abs/2210.03629

[14] T. Schick, J. Dwivedi-Yu, R. Dessi, R. Raileanu, M. Lomeli, L. Zettlemoyer, N. Cancedda, and T. Scialom, "Toolformer: Language Models Can Teach Themselves to Use Tools," in *Advances in Neural Information Processing Systems 36 (NeurIPS)*, 2023. Available: https://arxiv.org/abs/2302.04761

[15] J. Wei, X. Wang, D. Schuurmans, M. Bosma, B. Ichter, F. Xia, E. Chi, Q. V. Le, and D. Zhou, "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models," in *Advances in Neural Information Processing Systems 35 (NeurIPS)*, 2022. Available: https://arxiv.org/abs/2201.11903

[16] J. S. Park, J. C. O'Brien, C. J. Cai, M. R. Morris, P. Liang, and M. S. Bernstein, "Generative Agents: Interactive Simulacra of Human Behavior," in *Proc. 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)*, 2023. DOI: 10.1145/3586183.3606763. Available: https://arxiv.org/abs/2304.03442

[17] L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, J. Zhang, Z. Chen, J. Tang, X. Chen, Y. Lin, W. X. Zhao, Z. Wei, and J. Wen, "A Survey on Large Language Model based Autonomous Agents," *Frontiers of Computer Science*, vol. 18, no. 6, 2024. Available: https://arxiv.org/abs/2308.11432

[18] Cloud Native Computing Foundation, "Open Policy Agent (OPA)," 2020. Available: https://www.openpolicyagent.org/

[19] Amazon Web Services, "Building Multi-Tenant Architectures for Agentic AI on AWS," AWS Prescriptive Guidance, 2025. Available: https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-multitenant/

[20] World Economic Forum, "AI Agents in Action: Foundations for Evaluation and Governance," 2025. Available: https://reports.weforum.org/docs/WEF_AI_Agents_in_Action_Foundations_for_Evaluation_and_Governance_2025.pdf
