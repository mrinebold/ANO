"""
MSR Plugin Profile

Optional profile for AI policy advisory patterns.
Registers organization type presets, extended configuration, and policy presets.
Contains NO proprietary business logic.

This profile demonstrates how to configure ANO for multi-organization-type
policy advisory workflows with enhanced governance and compliance features.
"""

from typing import TYPE_CHECKING

from ano_core.logging import get_agent_logger

if TYPE_CHECKING:
    from profiles.loader import ProfileRegistry, PolicyPreset

logger = get_agent_logger(__name__)


def register(registry: "ProfileRegistry") -> None:
    """
    Register MSR profile: AI policy advisory configuration.

    Args:
        registry: ProfileRegistry to populate
    """
    from profiles.loader import PolicyPreset

    logger.info("Registering MSR plugin profile")

    # Override configuration for policy advisory use case
    registry.set_config_defaults({
        "max_concurrent_agents": 8,
        "policy_enforcement": True,
        "agent_timeout_seconds": 600,
        "pipeline_retry_attempts": 2,
        "enable_memory_persistence": True,
        "memory_base_dir": ".ano/agents",
    })

    # Register policy presets for different organization types
    registry.register_policy_preset(
        PolicyPreset(
            name="municipal",
            description="Municipal government AI policy advisory",
            org_types=["municipal", "city", "county", "regional"],
            regulatory_contexts=[
                "public_records",
                "procurement_law",
                "accessibility_requirements",
                "data_sovereignty",
            ],
            config={
                "require_public_comment_period": True,
                "mandate_accessibility_compliance": True,
                "enforce_procurement_transparency": True,
                "data_residency_requirements": True,
            },
        )
    )

    registry.register_policy_preset(
        PolicyPreset(
            name="enterprise",
            description="Enterprise AI policy advisory",
            org_types=["enterprise", "corporation", "business"],
            regulatory_contexts=[
                "data_protection",
                "industry_standards",
                "risk_management",
                "compliance_reporting",
            ],
            config={
                "require_risk_assessment": True,
                "mandate_audit_trail": True,
                "enforce_data_governance": True,
                "enable_compliance_monitoring": True,
            },
        )
    )

    registry.register_policy_preset(
        PolicyPreset(
            name="nonprofit",
            description="Nonprofit organization AI policy advisory",
            org_types=["nonprofit", "ngo", "foundation"],
            regulatory_contexts=[
                "donor_privacy",
                "mission_alignment",
                "grant_compliance",
                "transparency_standards",
            ],
            config={
                "require_mission_alignment_check": True,
                "enforce_donor_privacy": True,
                "mandate_transparency_reporting": True,
                "enable_impact_tracking": True,
            },
        )
    )

    registry.register_policy_preset(
        PolicyPreset(
            name="education",
            description="Educational institution AI policy advisory",
            org_types=["education", "university", "k12", "research"],
            regulatory_contexts=[
                "ferpa_compliance",
                "student_privacy",
                "research_ethics",
                "accessibility_standards",
            ],
            config={
                "require_ferpa_compliance": True,
                "enforce_student_privacy": True,
                "mandate_accessibility": True,
                "enable_research_ethics_review": True,
            },
        )
    )

    registry.register_policy_preset(
        PolicyPreset(
            name="healthcare",
            description="Healthcare organization AI policy advisory",
            org_types=["healthcare", "hospital", "clinic", "medical"],
            regulatory_contexts=[
                "hipaa_compliance",
                "patient_privacy",
                "clinical_safety",
                "medical_ethics",
            ],
            config={
                "require_hipaa_compliance": True,
                "enforce_patient_privacy": True,
                "mandate_clinical_safety_review": True,
                "enable_medical_ethics_oversight": True,
            },
        )
    )

    # Enable MSR-specific features
    registry.set_feature("policy_presets", True)
    registry.set_feature("multi_org_type", True)
    registry.set_feature("enhanced_compliance", True)
    registry.set_feature("audit_trail", True)

    # Set profile metadata
    registry.set_metadata("profile_name", "msr")
    registry.set_metadata("profile_version", "1.0.0")
    registry.set_metadata(
        "profile_description",
        "AI policy advisory profile with multi-org-type support"
    )

    logger.info(
        f"MSR profile registration complete - "
        f"{len(registry.list_policy_presets())} policy presets registered"
    )
