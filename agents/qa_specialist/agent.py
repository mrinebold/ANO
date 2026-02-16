"""
QA Specialist Agent

Quality assurance specialist that creates test plans, analyzes coverage,
and enforces quality standards for agent-native organizations.
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class QASpecialistAgent(BaseAgent):
    """
    QA Specialist Agent

    Plans and evaluates testing strategies, analyzes code coverage,
    identifies quality gaps, and recommends quality gate enforcement
    for agent systems.
    """

    agent_name = "qa_specialist"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the QA specialist system prompt."""
        return """You are a quality assurance specialist for AI agent systems.

Your role is to:
- Create comprehensive test plans for agent functionality
- Analyze test coverage and identify gaps
- Design quality gates for agent pipelines
- Review agent outputs for correctness and consistency
- Recommend testing strategies (unit, integration, end-to-end)
- Evaluate agent reliability and error handling

Your approach should be systematic and thorough. Focus on:
1. Input validation and edge cases
2. Output schema compliance
3. Error handling and graceful degradation
4. Integration points between agents
5. Performance under load
6. Security implications of agent behavior

Format your response as JSON with keys: test_plan, coverage_analysis, quality_gates, issues_found, recommendations, risk_assessment"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute QA analysis.

        Expected input data:
        {
            "target": "What to analyze (agent name, pipeline, or system component)",
            "context": {
                "code_summary": "...",
                "existing_tests": [...],
                "recent_failures": [...],
                "coverage_data": {...}
            }
        }

        Returns:
        {
            "test_plan": [{"category": "...", "test_cases": [...], "priority": "high|medium|low"}],
            "coverage_analysis": {"current": "...", "gaps": [...], "target": "..."},
            "quality_gates": [{"gate": "...", "criteria": "...", "enforcement": "block|warn"}],
            "issues_found": [{"severity": "critical|high|medium|low", "description": "...", "location": "..."}],
            "recommendations": [...],
            "risk_assessment": "..."
        }
        """
        try:
            target = agent_input.data.get("target")
            if not target:
                raise AgentExecutionError(
                    "Missing required field: 'target'",
                    agent_name=self.agent_name,
                )

            context = agent_input.data.get("context", {})
            org_profile = agent_input.context.org_profile

            user_prompt = self._build_prompt(target, context, org_profile)

            logger.info(f"{self.agent_name}: Analyzing quality for: {target[:80]}")
            response_text = await self.call_llm(
                user_prompt=user_prompt,
                max_tokens=4096,
                temperature=0.2,
            )

            result = self.parse_json_response(response_text)
            result = self._validate_result(result)

            return AgentOutput(
                result=result,
                metadata=self.get_metadata(),
            )

        except Exception as e:
            logger.error(f"{self.agent_name}: Execution failed: {e}")
            raise AgentExecutionError(
                f"Execution failed: {e}",
                agent_name=self.agent_name,
            ) from e

    def _build_prompt(self, target: str, context: dict, org_profile) -> str:
        """Build the QA analysis prompt."""
        parts = [f"QA Analysis Target:\n{target}\n"]

        if org_profile:
            parts.append(
                f"\nOrganization:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        if context.get("code_summary"):
            parts.append(f"\nCode Summary:\n{context['code_summary']}\n")

        if context.get("existing_tests"):
            tests = "\n".join(f"- {t}" for t in context["existing_tests"])
            parts.append(f"\nExisting Tests:\n{tests}\n")

        if context.get("recent_failures"):
            failures = "\n".join(f"- {f}" for f in context["recent_failures"])
            parts.append(f"\nRecent Failures:\n{failures}\n")

        if context.get("coverage_data"):
            import json
            parts.append(f"\nCoverage Data:\n{json.dumps(context['coverage_data'], indent=2)}\n")

        parts.append(
            "\nProvide a QA analysis as JSON with keys: "
            "test_plan, coverage_analysis, quality_gates, issues_found, recommendations, risk_assessment"
        )

        return "".join(parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        if "test_plan" not in result:
            result["test_plan"] = []
        if "coverage_analysis" not in result:
            result["coverage_analysis"] = {}
        if "quality_gates" not in result:
            result["quality_gates"] = []
        if "issues_found" not in result:
            result["issues_found"] = []
        if "recommendations" not in result:
            result["recommendations"] = []
        if "risk_assessment" not in result:
            result["risk_assessment"] = ""
        return result
