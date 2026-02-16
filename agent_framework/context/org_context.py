"""
Organization Context Rendering

Provides generic context string builders for organization profiles.
OrgTypePlugins can override these to provide specialized context.
"""

from ano_core.types import OrgProfile


def render_org_context(profile: OrgProfile) -> str:
    """
    Generate a generic context string from an organization profile.

    Formats the organization's basic information into a readable context
    string that agents can use in their prompts. OrgTypePlugins can
    override this for org-type-specific formatting.

    Args:
        profile: Organization profile to render

    Returns:
        Formatted context string
    """
    lines = [
        f"Organization Type: {profile.org_type}",
        f"Organization: {profile.org_name}",
    ]

    if profile.state:
        lines.append(f"State: {profile.state}")

    if profile.industry:
        lines.append(f"Industry: {profile.industry}")

    if profile.size:
        lines.append(f"Size: {profile.size}")

    if profile.population:
        lines.append(f"Population: {profile.population}")

    if profile.budget:
        lines.append(f"Budget: {profile.budget}")

    if profile.website:
        lines.append(f"Website: {profile.website}")

    if profile.departments:
        lines.append(f"Departments: {', '.join(profile.departments)}")

    if profile.concerns:
        lines.append(f"Key Concerns: {', '.join(profile.concerns)}")

    if profile.contact_email:
        lines.append(f"Contact: {profile.contact_email}")

    return "\n".join(lines)


def render_regulatory_context(profile: OrgProfile) -> str:
    """
    Generate generic regulatory hints based on organization type.

    Provides baseline regulatory context for common org types.
    OrgTypePlugins can override this for specialized regulatory guidance.

    Args:
        profile: Organization profile

    Returns:
        Regulatory context hints
    """
    org_type = profile.org_type.lower()

    if org_type == "municipal":
        return (
            "Focus on: State AI legislation, NIST AI RMF, ADA/Section 508 accessibility, "
            "FOIA/open records, procurement regulations, civil rights protections, "
            "local ordinances (e.g., NYC Local Law 144)."
        )

    elif org_type == "enterprise":
        return (
            "Focus on: Industry-specific regulations (SOX, PCI-DSS, GDPR, CCPA), "
            "SEC AI disclosure requirements, FTC algorithmic fairness guidance, "
            "EEOC guidance on AI in hiring, NIST AI RMF, ISO/IEC 42001."
        )

    elif org_type == "nonprofit":
        return (
            "Focus on: Grant compliance requirements, donor data protection, "
            "IRS tax-exempt status implications, state attorney general oversight, "
            "NIST AI RMF, accessibility requirements, beneficiary data protections."
        )

    elif org_type == "education":
        return (
            "Focus on: FERPA, COPPA (if K-12), state student data privacy laws, "
            "Title IX implications, ADA/Section 508, accreditation standards, "
            "academic integrity policies, NIST AI RMF."
        )

    elif org_type == "healthcare":
        return (
            "Focus on: HIPAA, HITECH Act, FDA AI/ML guidance, CMS conditions of participation, "
            "state medical practice acts, clinical decision support regulations, "
            "21st Century Cures Act, NIST AI RMF, patient consent requirements."
        )

    else:
        return "Focus on: General AI governance best practices and NIST AI RMF."
