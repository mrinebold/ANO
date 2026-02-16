"""
Policy Module

Policy enforcement system for the ANO framework. Provides gate-based
validation, hooks for custom logic, and tier-specific policy configurations.

Components:
- PolicyEngine: Orchestrates gate evaluation and decision making
- PolicyGate: Individual validation gates (tests, security, quality, etc.)
- PolicyHook: Extension points for custom enforcement logic
- Tier Policies: Pre-configured policies for dev/test/prod environments
"""

from policy.engine import PolicyDecision, PolicyEngine
from policy.gates import (
    GATE_REGISTRY,
    ApprovalGate,
    BranchPolicyGate,
    CodeQualityGate,
    DocumentationGate,
    FileVerificationGate,
    GateResult,
    PolicyGate,
    SecurityValidationGate,
    TestSuccessGate,
    get_gate,
)
from policy.hooks import (
    AuditLoggingHook,
    CostTrackingHook,
    DataSanitizationHook,
    HookResult,
    PolicyHook,
    RateLimitHook,
)
from policy.tier_policy import (
    get_custom_policy,
    get_minimal_policy,
    get_quality_policy,
    get_security_policy,
    get_tier_policy,
)

__all__ = [
    # Engine
    "PolicyEngine",
    "PolicyDecision",
    # Gates
    "PolicyGate",
    "GateResult",
    "TestSuccessGate",
    "FileVerificationGate",
    "BranchPolicyGate",
    "DocumentationGate",
    "CodeQualityGate",
    "SecurityValidationGate",
    "ApprovalGate",
    "GATE_REGISTRY",
    "get_gate",
    # Hooks
    "PolicyHook",
    "HookResult",
    "AuditLoggingHook",
    "DataSanitizationHook",
    "RateLimitHook",
    "CostTrackingHook",
    # Tier policies
    "get_tier_policy",
    "get_custom_policy",
    "get_minimal_policy",
    "get_quality_policy",
    "get_security_policy",
]
