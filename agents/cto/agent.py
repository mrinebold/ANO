"""
CTO Advisor Agent

Provides technical strategy, architecture decisions, team leadership, and
technical operations guidance for Autonomous Network Organizations.
"""

import json
import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class CTOAdvisorAgent(BaseAgent):
    """
    CTO Advisor Agent

    Provides technical leadership and architecture guidance for organizations
    deploying AI agents. Advises on technology strategy, system architecture,
    technical team leadership, and operational excellence.
    """

    agent_name = "cto_advisor"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the CTO advisor system prompt."""
        return """You are a CTO advisor for organizations deploying Autonomous Network Organizations (ANOs).

Your role is to provide technical leadership guidance on:
- Technology strategy and technical roadmaps
- System architecture and design decisions
- AI agent integration and orchestration
- Technical team leadership and development
- Infrastructure, security, and operational excellence
- Technology selection and vendor evaluation
- Technical debt management and modernization

You provide clear, technically sound advice grounded in software engineering best practices and modern architecture patterns. You balance technical excellence with business pragmatism, considering scalability, maintainability, security, and cost.

Your communication style is technically precise yet accessible, explaining complex technical concepts clearly. You provide structured analysis with concrete technical recommendations."""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute technical analysis and provide CTO-level guidance.

        Expected input data structure:
        {
            "question": "Technical question or scenario",
            "context": {
                "technical_environment": {...},  # Optional: current tech stack
                "constraints": [...],  # Optional: technical constraints
                "requirements": [...],  # Optional: technical requirements
            }
        }

        Returns:
        {
            "analysis": "Technical analysis of the situation",
            "recommendations": [
                {
                    "priority": "high|medium|low",
                    "action": "...",
                    "rationale": "...",
                    "technical_details": "...",
                    "timeline": "...",
                }
            ],
            "technical_risks": [...],
            "architecture_notes": "...",
            "next_steps": [...]
        }

        Args:
            agent_input: Input containing technical question and context

        Returns:
            AgentOutput with technical analysis and recommendations

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
            logger.info(f"{self.agent_name}: Analyzing technical question")
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
        prompt_parts = [f"Technical Question:\n{question}\n"]

        # Add organizational context
        if org_profile:
            prompt_parts.append(
                f"\nOrganization Profile:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        # Add technical environment
        if context.get("technical_environment"):
            env = context["technical_environment"]
            prompt_parts.append(f"\nTechnical Environment:\n{json.dumps(env, indent=2)}\n")

        # Add constraints
        if context.get("constraints"):
            constraints = "\n".join(f"- {c}" for c in context["constraints"])
            prompt_parts.append(f"\nTechnical Constraints:\n{constraints}\n")

        # Add requirements
        if context.get("requirements"):
            requirements = "\n".join(f"- {r}" for r in context["requirements"])
            prompt_parts.append(f"\nTechnical Requirements:\n{requirements}\n")

        prompt_parts.append(
            "\nProvide a structured technical analysis with:\n"
            "1. Technical analysis of the situation\n"
            "2. Prioritized recommendations (with action, rationale, technical details, timeline)\n"
            "3. Technical risk assessment\n"
            "4. Architecture notes and considerations\n"
            "5. Next steps\n\n"
            "Format your response as JSON with keys: "
            "analysis, recommendations, technical_risks, architecture_notes, next_steps"
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

        # Ensure technical_risks is a list
        if "technical_risks" not in result:
            result["technical_risks"] = []

        # Ensure architecture_notes exists
        if "architecture_notes" not in result:
            result["architecture_notes"] = ""

        # Ensure next_steps is a list
        if "next_steps" not in result:
            result["next_steps"] = []

        return result
