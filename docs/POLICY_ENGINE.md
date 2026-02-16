# Policy Engine

The policy engine enforces quality, security, and operational standards for agent execution. It evaluates a set of **policy gates** before and after agent execution, with enforcement behavior determined by the **environment tier**.

## Concepts

- **Gate** — A single check (e.g., "tests must pass"). Returns pass/fail with context.
- **Engine** — Orchestrates multiple gates, aggregates results into a decision.
- **Decision** — Allow or deny, with detailed violation tracking.
- **Tier** — Environment tier (development, test, production) controls enforcement strictness.

## Quick Start

```python
from policy.engine import PolicyEngine
from policy.gates import TestSuccessGate, SecurityValidationGate
from ano_core.environment import EnvironmentTier

# Create engine with selected gates
gates = [TestSuccessGate(), SecurityValidationGate()]
engine = PolicyEngine(gates, EnvironmentTier.TEST)

# Evaluate before agent execution
decision = await engine.evaluate_pre("my-agent", {
    "tests_passed": True,
    "security_scan_passed": True,
})

print(decision.allowed)       # True
print(decision.gates_passed)  # ["test-success", "security-validation"]
print(decision.gates_failed)  # []
```

## Built-in Gates

### Gate 1: Test Success

Checks that automated tests have passed.

```python
# Context keys:
{"tests_passed": True}                    # Pass
{"tests_passed": False, "test_results": {"failed": 3}}  # Fail
```

### Gate 2: File Verification

Checks that required files exist with correct integrity.

```python
{"files_verified": True}                                  # Pass
{"files_verified": False, "missing_files": ["README.md"]} # Fail
```

### Gate 3: Branch Policy

Checks operations target the correct branch for the environment.

```python
{"current_branch": "main", "allowed_branches": ["main", "develop"]}  # Pass
{"current_branch": "hack", "allowed_branches": ["main"]}             # Fail
```

### Gate 4: Documentation

Checks that changes include appropriate documentation.

```python
{"documentation_updated": True, "documentation_score": 0.95}         # Pass
{"documentation_updated": False, "missing_docs": ["API.md"]}         # Fail
```

### Gate 5: Code Quality

Checks that code passes linting and type checking.

```python
{"lint_passed": True, "type_check_passed": True}    # Pass
{"lint_passed": False, "type_check_passed": True}    # Fail (linting)
```

### Gate 6: Security Validation

Checks for security vulnerabilities and exposed secrets.

```python
{"security_scan_passed": True}                                        # Pass
{"security_scan_passed": False, "vulnerabilities_found": 3}          # Fail
```

### Gate 7: Approval

Checks that human approval has been granted for sensitive operations.

```python
{"approval_granted": True, "approver": "admin"}     # Pass
{"approval_granted": False}                          # Fail
```

## Tier Enforcement

The engine's behavior depends on the environment tier:

| Tier | On Failure | Use Case |
|------|-----------|----------|
| **Development** | Logs warning, **always allows** | Local development, rapid iteration |
| **Test** | **Blocks execution** | CI/CD, validation before production |
| **Production** | **Strictly blocks**, logs error | Live systems, maximum safety |

```python
# Development: failures produce warnings but execution continues
engine = PolicyEngine(gates, EnvironmentTier.DEVELOPMENT)
decision = await engine.evaluate_pre("agent", {"tests_passed": False})
assert decision.allowed is True  # Always allows in dev

# Test: failures block execution
engine = PolicyEngine(gates, EnvironmentTier.TEST)
decision = await engine.evaluate_pre("agent", {"tests_passed": False})
assert decision.allowed is False  # Blocks in test

# Production: strict enforcement
engine = PolicyEngine(gates, EnvironmentTier.PRODUCTION)
decision = await engine.evaluate_pre("agent", {"tests_passed": False})
assert decision.allowed is False  # Strict block in prod
```

## Pre and Post Evaluation

The engine supports both pre-execution and post-execution checks:

```python
# Before agent runs — validate inputs, permissions, environment
pre_decision = await engine.evaluate_pre("agent-name", {
    "tests_passed": True,
    "approval_granted": True,
})

if pre_decision.allowed:
    # Run the agent
    output = await agent.execute(input_data)

    # After agent runs — validate outputs, security, quality
    post_decision = await engine.evaluate_post("agent-name", {
        "security_scan_passed": True,
        "documentation_updated": True,
    })

    if not post_decision.allowed:
        # Handle post-execution violations
        for violation in post_decision.violations:
            print(f"Post-check failed: {violation.gate} - {violation.message}")
```

## Violations and Remediation

When a gate fails, the engine creates a `PolicyViolation` with remediation guidance:

```python
decision = await engine.evaluate_pre("agent", {"tests_passed": False})

for violation in decision.violations:
    print(f"Gate: {violation.gate}")
    print(f"Severity: {violation.severity}")
    print(f"Message: {violation.message}")
    print(f"Remediation: {violation.remediation}")

# Output:
# Gate: test-success
# Severity: error
# Message: Tests failed (failed count: unknown)
# Remediation: Run tests locally and fix failures before retrying. Production requires strict compliance.
```

Remediation messages are tier-specific:
- **Development** — Base remediation only
- **Test** — Adds "Approval may be required in test environment."
- **Production** — Adds "Production requires strict compliance."

## Using the Gate Registry

All 7 built-in gates are available via the gate registry:

```python
from policy.gates import get_gate, GATE_REGISTRY

# Get a gate by name
gate = get_gate("test-success")

# List all available gates
print(list(GATE_REGISTRY.keys()))
# ['test-success', 'file-verification', 'branch-policy',
#  'documentation', 'code-quality', 'security-validation', 'approval']

# Create engine with all gates
all_gates = [get_gate(name) for name in GATE_REGISTRY]
engine = PolicyEngine(all_gates, EnvironmentTier.PRODUCTION)
```

## Creating Custom Gates

Subclass `PolicyGate` and implement the `evaluate()` method:

```python
from policy.gates import PolicyGate, GateResult

class BudgetGate(PolicyGate):
    """Check that operation is within budget."""

    def __init__(self):
        super().__init__(
            name="budget-check",
            description="Operation must be within approved budget",
        )

    async def evaluate(self, context: dict) -> GateResult:
        estimated_cost = context.get("estimated_cost", 0)
        budget_limit = context.get("budget_limit", 100)

        if estimated_cost <= budget_limit:
            return GateResult(
                passed=True,
                gate_name=self.name,
                message=f"Within budget (${estimated_cost} / ${budget_limit})",
                severity="info",
            )

        return GateResult(
            passed=False,
            gate_name=self.name,
            message=f"Over budget: ${estimated_cost} exceeds ${budget_limit}",
            severity="error",
        )

# Use it
gates = [TestSuccessGate(), BudgetGate()]
engine = PolicyEngine(gates, EnvironmentTier.TEST)
decision = await engine.evaluate_pre("expensive-agent", {
    "tests_passed": True,
    "estimated_cost": 150,
    "budget_limit": 100,
})
```

## Policy Hooks

The policy module also provides hooks for cross-cutting concerns:

| Hook | Purpose |
|------|---------|
| `AuditHook` | Log all policy evaluations for audit trail |
| `SanitizationHook` | Sanitize agent inputs/outputs |
| `RateLimitHook` | Enforce rate limits on agent execution |
| `CostTrackingHook` | Track LLM costs per agent |

```python
from policy.hooks import AuditHook, RateLimitHook

audit = AuditHook(log_path="/var/log/ano/policy-audit.jsonl")
rate_limit = RateLimitHook(max_per_minute=10, max_per_hour=100)
```

## Tier Policies

Use `get_tier_policy()` to get a pre-configured set of gates for each tier:

```python
from policy.tier_policy import get_tier_policy
from ano_core.environment import EnvironmentTier

# Development: minimal gates (test + security only)
dev_gates = get_tier_policy(EnvironmentTier.DEVELOPMENT)

# Test: more gates (test + file + quality + security)
test_gates = get_tier_policy(EnvironmentTier.TEST)

# Production: all 7 gates
prod_gates = get_tier_policy(EnvironmentTier.PRODUCTION)
```
