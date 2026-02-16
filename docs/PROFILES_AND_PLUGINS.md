# Profiles and Plugins

ANO Foundation uses a **profile/plugin system** to manage configuration without conditional sprawl. Instead of `if profile == "msr"` checks throughout the codebase, profiles register their configuration into a central `ProfileRegistry` that core code reads from.

## How It Works

```
ANO_PROFILE=msr  →  load_profile("msr")  →  ProfileRegistry
                          │                        │
                          ├── Load minimal first    ├── Agent classes
                          └── Layer msr on top      ├── Config values
                                                    ├── Policy presets
                                                    ├── Integration hooks
                                                    └── Feature flags
```

1. The `minimal` profile is **always loaded first** as the base layer
2. If a different profile is requested, it is **layered on top** (overrides take precedence)
3. `ANO_FEATURES` environment variable applies final feature flag overrides
4. Core code reads from `ProfileRegistry` — never checks which profile is active

## Built-in Profiles

### Minimal (Default)

The base profile with permissive defaults. Always loaded first.

```python
# Configuration defaults
max_concurrent_agents: 3
default_llm_provider: "anthropic"
default_llm_model: "claude-sonnet-4-5-20250929"
agent_timeout_seconds: 300
policy_enforcement: False

# Policy presets: 1 (base — permissive)
# Features: none
```

### MSR Plugin

AI policy advisory profile with multi-organization-type support.

```python
# Configuration overrides
max_concurrent_agents: 8
policy_enforcement: True
agent_timeout_seconds: 600
pipeline_retry_attempts: 2

# Policy presets: 6
#   base, municipal, enterprise, nonprofit, education, healthcare

# Features enabled:
#   policy_presets, multi_org_type, enhanced_compliance, audit_trail
```

## Using Profiles

### Loading a Profile

```python
from profiles.loader import load_profile

# Load from environment variable (ANO_PROFILE)
registry = load_profile()

# Load explicitly
registry = load_profile("minimal")
registry = load_profile("msr")
```

### Reading Configuration

```python
# Get config values with fallbacks
timeout = registry.get_config("agent_timeout_seconds", 300)
max_agents = registry.get_config("max_concurrent_agents", 3)
provider = registry.get_config("default_llm_provider", "anthropic")
```

### Working with Policy Presets

```python
# List all presets
presets = registry.list_policy_presets()
for name, preset in presets.items():
    print(f"{name}: {preset.description}")
    print(f"  Org types: {preset.org_types}")
    print(f"  Regulatory: {preset.regulatory_contexts}")

# Get a specific preset
municipal = registry.get_policy_preset("municipal")
if municipal:
    print(municipal.config)
    # {"require_public_comment_period": True, ...}
```

### Checking Features

```python
if registry.has_feature("audit_trail"):
    # Enable audit logging
    pass

if registry.has_feature("policy_presets"):
    # Use org-type-specific presets
    pass
```

### Agent Classes

```python
# Register agent classes in a profile
registry.register_agent_class("researcher", ResearcherAgent)

# Look up agent classes
agent_cls = registry.get_agent_class("researcher")
all_agents = registry.list_agent_classes()
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANO_PROFILE` | Profile to load | `minimal`, `msr` |
| `ANO_FEATURES` | Feature flag overrides | `+audit_trail,-policy_enforcement` |

### Feature Flag Syntax

```bash
# Enable a feature
ANO_FEATURES="+audit_trail"

# Disable a feature
ANO_FEATURES="-policy_enforcement"

# Multiple flags
ANO_FEATURES="+audit_trail,-policy_enforcement,+custom_feature"

# The + prefix is optional for enabling
ANO_FEATURES="audit_trail"  # Same as "+audit_trail"
```

## Creating a Custom Profile

### 1. Create the Module

Create a Python module with a `register(registry)` function:

```python
# plugins/my_org/__init__.py
"""
My Organization Profile

Custom profile for our specific organization.
"""

from profiles.loader import PolicyPreset


def register(registry):
    """Register my organization's profile."""

    # Override configuration
    registry.set_config("max_concurrent_agents", 5)
    registry.set_config("policy_enforcement", True)
    registry.set_config("custom_api_url", "https://api.myorg.com")

    # Register policy presets
    registry.register_policy_preset(PolicyPreset(
        name="internal",
        description="Internal operations preset",
        org_types=["internal"],
        regulatory_contexts=["data_governance", "access_control"],
        config={
            "require_mfa": True,
            "audit_all_actions": True,
        },
    ))

    # Enable features
    registry.set_feature("custom_dashboards", True)
    registry.set_feature("advanced_analytics", True)

    # Set metadata
    registry.set_metadata("profile_name", "my_org")
    registry.set_metadata("profile_version", "1.0.0")
```

### 2. Register the Module

Add the profile to the module map in `profiles/loader.py`:

```python
PROFILE_MODULES = {
    "minimal": "profiles.minimal",
    "msr": "plugins.msr",
    "my_org": "plugins.my_org",  # Add your profile
}
```

### 3. Use It

```bash
export ANO_PROFILE=my_org
```

```python
registry = load_profile("my_org")
print(registry.summary())
```

## Integration Hooks

Profiles can register hooks for extending framework behavior:

```python
from profiles.loader import IntegrationHook

def create_slack_notifier():
    """Factory function for Slack notification hook."""
    return SlackNotifier(webhook_url="...")

registry.register_hook(IntegrationHook(
    name="slack-notifications",
    hook_type="notification",
    factory=create_slack_notifier,
    priority=10,  # Higher = executes first
))

# Retrieve hooks by type
hooks = registry.get_hooks("notification")
for hook in hooks:
    notifier = hook.factory()
    notifier.send("Agent completed task")
```

### Hook Types

- `llm_provider` — Custom LLM providers
- `storage_backend` — Custom storage integrations
- `notification` — Notification channels
- `channel` — Deployment channel extensions

## Profile Registry Summary

```python
summary = registry.summary()
# {
#     "profile_name": "msr",
#     "profile_version": "1.0.0",
#     "agent_classes": 4,
#     "policy_presets": 6,
#     "hooks": 0,
#     "features_enabled": 4,
#     "config_keys": 8,
# }
```
