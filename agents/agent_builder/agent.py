"""
Agent Builder Agent

The HR department of an ANO. Handles agent onboarding, certification,
registration, and organizational hierarchy management.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.agent_builder.certification import CertificationEngine
from agents.agent_builder.schemas import (
    AgentSpec,
    CertificationReport,
    OnboardingResult,
    RegistryEntry,
)

logger = logging.getLogger(__name__)


class AgentBuilderAgent:
    """
    Agent Builder - The HR Department of an ANO

    Responsible for:
    - Validating agent specifications
    - Certifying agents meet organizational standards
    - Generating agent skeleton code and documentation
    - Registering agents in the central registry
    - Wiring organizational hierarchy
    - Managing reporting relationships
    """

    agent_name = "agent_builder"
    version = "1.0.0"

    def __init__(self, existing_agents: Optional[list[str]] = None):
        """
        Initialize the Agent Builder.

        Args:
            existing_agents: List of already-registered agent names
        """
        self.existing_agents = set(existing_agents or [])
        self.certification_engine = CertificationEngine(
            existing_agent_names=list(self.existing_agents)
        )
        self.hierarchy: dict[str, list[str]] = {}  # supervisor -> [reports]
        logger.info(f"Initialized {self.agent_name} v{self.version}")

    def validate(self, spec: AgentSpec) -> list[str]:
        """
        Validate an agent specification.

        Args:
            spec: Agent specification to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        try:
            # Pydantic will raise on invalid data
            _ = AgentSpec.model_validate(spec.model_dump())
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def certify(self, spec: AgentSpec) -> CertificationReport:
        """
        Run certification checks on an agent specification.

        Args:
            spec: Agent specification to certify

        Returns:
            CertificationReport with check results
        """
        logger.info(f"Certifying agent: {spec.name}")
        return self.certification_engine.certify(spec)

    def generate(self, spec: AgentSpec) -> dict[str, str]:
        """
        Generate skeleton files for a new agent.

        Args:
            spec: Agent specification

        Returns:
            Dictionary mapping file paths to content
        """
        logger.info(f"Generating files for agent: {spec.name}")

        generated_files = {}

        # Generate Python agent file
        agent_file_content = self._generate_agent_file(spec)
        generated_files[f"agents/{spec.name}/agent.py"] = agent_file_content

        # Generate __init__.py
        init_content = self._generate_init_file(spec)
        generated_files[f"agents/{spec.name}/__init__.py"] = init_content

        # Generate skill.md
        skill_content = self._generate_skill_file(spec)
        generated_files[f"agents/{spec.name}/skill.md"] = skill_content

        logger.info(f"Generated {len(generated_files)} files for {spec.name}")
        return generated_files

    def register(self, entry: RegistryEntry) -> bool:
        """
        Register an agent in the registry.

        Args:
            entry: Registry entry to add

        Returns:
            True if registration succeeded
        """
        if entry.name in self.existing_agents:
            logger.warning(f"Agent {entry.name} is already registered")
            return False

        self.existing_agents.add(entry.name)
        logger.info(f"Registered agent: {entry.name}")
        return True

    def wire_hierarchy(self, spec: AgentSpec) -> dict[str, Any]:
        """
        Wire the agent into the organizational hierarchy.

        Args:
            spec: Agent specification with reporting structure

        Returns:
            Dictionary describing the hierarchy changes
        """
        hierarchy_changes = {
            "agent": spec.name,
            "reports_to": spec.reporting.reports_to,
            "dotted_lines": spec.reporting.dotted_line_to,
            "orchestrator": spec.reporting.orchestrator,
        }

        # Update hierarchy mapping
        if spec.reporting.reports_to:
            if spec.reporting.reports_to not in self.hierarchy:
                self.hierarchy[spec.reporting.reports_to] = []
            self.hierarchy[spec.reporting.reports_to].append(spec.name)

        logger.info(f"Wired {spec.name} into hierarchy")
        return hierarchy_changes

    def onboard(self, spec: AgentSpec) -> OnboardingResult:
        """
        Full onboarding pipeline for a new agent.

        Steps:
        1. Validate specification
        2. Run certification checks
        3. Generate skeleton files
        4. Create registry entry
        5. Register agent
        6. Wire into hierarchy

        Args:
            spec: Complete agent specification

        Returns:
            OnboardingResult with all outcomes
        """
        logger.info(f"Starting onboarding for agent: {spec.name}")

        try:
            # Step 1: Validate
            validation_errors = self.validate(spec)
            if validation_errors:
                return OnboardingResult(
                    spec=spec,
                    certification=CertificationReport(
                        agent_name=spec.name,
                        checks=[],
                        overall_passed=False,
                    ),
                    success=False,
                    error=f"Validation failed: {'; '.join(validation_errors)}",
                )

            # Step 2: Certify
            certification = self.certify(spec)
            if not certification.overall_passed:
                return OnboardingResult(
                    spec=spec,
                    certification=certification,
                    success=False,
                    error="Certification failed - agent does not meet standards",
                )

            # Step 3: Generate files
            generated_files = self.generate(spec)

            # Step 4: Create registry entry
            registry_entry = RegistryEntry(
                name=spec.name,
                display_name=spec.display_name,
                capabilities=[cap.name for cap in spec.capabilities],
                team=spec.team.value,
                specialization=spec.role,
                reporting_to=spec.reporting.reports_to,
                module_path=f"agents.{spec.name}.agent",
                is_active=True,
            )

            # Step 5: Register
            registration_success = self.register(registry_entry)
            if not registration_success:
                return OnboardingResult(
                    spec=spec,
                    certification=certification,
                    generated_files=generated_files,
                    success=False,
                    error="Registration failed - agent name already exists",
                )

            # Step 6: Wire hierarchy
            self.wire_hierarchy(spec)

            logger.info(f"Successfully onboarded agent: {spec.name}")
            return OnboardingResult(
                spec=spec,
                certification=certification,
                registry_entry=registry_entry,
                generated_files=generated_files,
                success=True,
            )

        except Exception as e:
            logger.error(f"Onboarding failed for {spec.name}: {e}")
            return OnboardingResult(
                spec=spec,
                certification=CertificationReport(
                    agent_name=spec.name,
                    checks=[],
                    overall_passed=False,
                ),
                success=False,
                error=f"Onboarding error: {e}",
            )

    def get_hierarchy(self) -> dict[str, list[str]]:
        """
        Get the current organizational hierarchy.

        Returns:
            Dictionary mapping supervisors to their direct reports
        """
        return self.hierarchy.copy()

    def _generate_agent_file(self, spec: AgentSpec) -> str:
        """Generate the agent Python file from template."""
        template_path = Path(__file__).parent / "templates" / "basic_agent.py.tmpl"

        try:
            template = template_path.read_text()
        except Exception as e:
            logger.warning(f"Could not read template: {e}, using inline template")
            template = self._get_inline_agent_template()

        # Generate class name (e.g., "data_analyst" -> "DataAnalystAgent")
        class_name = "".join(word.capitalize() for word in spec.name.split("_")) + "Agent"

        # Prepare capabilities list
        capabilities_list = [cap.name for cap in spec.capabilities]

        # Prepare personality description
        personality = spec.personality.description if spec.personality else "You are a helpful AI agent."

        # Simple template variable replacement
        content = template
        content = content.replace("{{AGENT_NAME}}", spec.name)
        content = content.replace("{{DISPLAY_NAME}}", spec.display_name)
        content = content.replace("{{CLASS_NAME}}", class_name)
        content = content.replace("{{ROLE}}", spec.role)
        content = content.replace("{{TEAM}}", spec.team.value)
        content = content.replace("{{CAPABILITIES}}", str(capabilities_list))
        content = content.replace("{{PERSONALITY}}", personality)

        return content

    def _generate_init_file(self, spec: AgentSpec) -> str:
        """Generate the __init__.py file."""
        class_name = "".join(word.capitalize() for word in spec.name.split("_")) + "Agent"
        module_name = spec.name

        return f'''"""
{spec.display_name}

{spec.role}
"""

from agents.{module_name}.agent import {class_name}

__all__ = ["{class_name}"]
'''

    def _generate_skill_file(self, spec: AgentSpec) -> str:
        """Generate the skill.md file from template."""
        template_path = Path(__file__).parent / "templates" / "agent_skill.md.tmpl"

        try:
            template = template_path.read_text()
        except Exception as e:
            logger.warning(f"Could not read template: {e}, using inline template")
            template = self._get_inline_skill_template()

        # Prepare capabilities section
        capabilities_text = "\n".join(
            f"- **{cap.name}** ({cap.category.value}): {cap.description or 'No description provided'}"
            for cap in spec.capabilities
        )

        # Prepare reporting structure
        reports_to = spec.reporting.reports_to or "Not specified"

        # Prepare personality
        personality = spec.personality.description if spec.personality else "No personality defined"

        # Simple template variable replacement
        content = template
        content = content.replace("{{AGENT_NAME}}", spec.name)
        content = content.replace("{{DISPLAY_NAME}}", spec.display_name)
        content = content.replace("{{TEAM}}", spec.team.value.capitalize())
        content = content.replace("{{ROLE}}", spec.role)
        content = content.replace("{{CAPABILITIES}}", capabilities_text)
        content = content.replace("{{REPORTS_TO}}", reports_to)
        content = content.replace("{{PERSONALITY}}", personality)
        content = content.replace("{{CREATED_DATE}}", datetime.utcnow().strftime("%Y-%m-%d"))

        return content

    def _get_inline_agent_template(self) -> str:
        """Fallback inline agent template."""
        return '''"""
{{DISPLAY_NAME}}

{{ROLE}}
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class {{CLASS_NAME}}(BaseAgent):
    """{{DISPLAY_NAME}}"""

    agent_name = "{{AGENT_NAME}}"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        return """{{PERSONALITY}}"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Implementation needed
        raise NotImplementedError("Agent execution not yet implemented")
'''

    def _get_inline_skill_template(self) -> str:
        """Fallback inline skill template."""
        return '''# {{DISPLAY_NAME}}

**Agent Name**: `{{AGENT_NAME}}`
**Team**: {{TEAM}}
**Version**: 1.0.0

## Role

{{ROLE}}

## Capabilities

{{CAPABILITIES}}

## Reporting

Reports to: {{REPORTS_TO}}

## Personality

{{PERSONALITY}}
'''
