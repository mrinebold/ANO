"""
CEO Advisor Agent

Provides strategic leadership guidance, organizational planning, board relations,
and stakeholder management advice for Autonomous Network Organizations.
"""

import json
import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CEOAdvisorAgent(BaseAgent):
    """
    CEO Advisor Agent

    Provides executive-level strategic guidance for organizations deploying
    AI agents. Advises on organizational strategy, leadership, governance,
    and stakeholder management.
    """

    agent_name = "ceo_advisor"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the CEO advisor system prompt."""
        return """You are a CEO advisor for organizations deploying Autonomous Network Organizations (ANOs).

Your role is to provide strategic leadership guidance on:
- Organizational strategy and long-term planning
- Leadership and executive decision-making
- Board relations and governance
- Stakeholder management and communication
- Change management and organizational transformation
- Risk assessment and mitigation at the organizational level

You provide clear, actionable advice grounded in business best practices and organizational leadership principles. You balance strategic vision with practical execution, considering both organizational goals and stakeholder interests.

Your communication style is professional, direct, and focused on outcomes. You provide structured analysis with clear recommendations."""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute strategic analysis and provide CEO-level guidance.

        Expected input data structure:
        {
            "question": "Strategic question or scenario",
            "context": {
                "org_profile": {...},  # Optional: organization details
                "current_situation": "...",  # Optional: current state
                "constraints": [...],  # Optional: constraints to consider
            }
        }

        Returns:
        {
            "analysis": "Strategic analysis of the situation",
            "recommendations": [
                {
                    "priority": "high|medium|low",
                    "action": "...",
                    "rationale": "...",
                    "timeline": "...",
                }
            ],
            "risks": [...],
            "next_steps": [...]
        }

        Args:
            agent_input: Input containing strategic question and context

        Returns:
            AgentOutput with strategic analysis and recommendations

        Raises:
            AgentExecutionError: If execution fails
        """
        started_at = datetime.utcnow()

        try:
            # Extract question and context
            question = agent_input.data.get("question")
            if not question:
                raise AgentExecutionError(
                    "Missing required field: 'question'",
                    agent_name=self.agent_name,
                )

            context = agent_input.data.get("context", {})
            org_profile = agent_input.context.org_profile

            # Build user prompt
            user_prompt = self._build_prompt(question, context, org_profile)

            # Call LLM
            logger.info(f"{self.agent_name}: Analyzing strategic question")
            response_text = await self.call_llm(
                user_prompt=user_prompt,
                max_tokens=4096,
                temperature=0.3,
            )

            # Parse response
            result = self.parse_json_response(response_text)

            # Validate and structure result
            result = self._validate_result(result)

            # Create metadata
            metadata = self.get_metadata()

            return AgentOutput(
                result=result,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"{self.agent_name}: Execution failed: {e}")
            raise AgentExecutionError(
                f"Execution failed: {e}",
                agent_name=self.agent_name,
            ) from e

    def _build_prompt(
        self,
        question: str,
        context: dict,
        org_profile: any,
    ) -> str:
        """Build the user prompt with question and context."""
        prompt_parts = [f"Strategic Question:\n{question}\n"]

        # Add organizational context
        if org_profile:
            prompt_parts.append(
                f"\nOrganization Profile:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        # Add additional context
        if context.get("current_situation"):
            prompt_parts.append(
                f"\nCurrent Situation:\n{context['current_situation']}\n"
            )

        if context.get("constraints"):
            constraints = "\n".join(f"- {c}" for c in context["constraints"])
            prompt_parts.append(f"\nConstraints:\n{constraints}\n")

        prompt_parts.append(
            "\nProvide a structured analysis with:\n"
            "1. Strategic analysis of the situation\n"
            "2. Prioritized recommendations (with action, rationale, timeline)\n"
            "3. Risk assessment\n"
            "4. Next steps\n\n"
            "Format your response as JSON with keys: "
            "analysis, recommendations, risks, next_steps"
        )

        return "".join(prompt_parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        # Ensure required fields exist
        if "analysis" not in result and "raw_text" in result:
            result["analysis"] = result["raw_text"]

        if "analysis" not in result:
            result["analysis"] = ""

        # Ensure recommendations is a list
        if "recommendations" not in result:
            result["recommendations"] = []

        # Ensure risks is a list
        if "risks" not in result:
            result["risks"] = []

        # Ensure next_steps is a list
        if "next_steps" not in result:
            result["next_steps"] = []

        return result
