"""
Researcher Agent

General-purpose research analyst that investigates topics, gathers findings,
and produces structured research reports with citations and recommendations.
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """
    Researcher Agent

    Investigates topics, synthesizes information from provided sources,
    and produces structured research reports with findings, analysis,
    and actionable recommendations.
    """

    agent_name = "researcher"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the researcher system prompt."""
        return """You are a research analyst for an organization.

Your role is to:
- Investigate topics thoroughly using provided sources and context
- Identify key findings, trends, and patterns
- Synthesize information into clear, structured analysis
- Provide evidence-based recommendations
- Flag gaps in available information
- Cite sources when making claims

Your analysis should be:
1. Objective and evidence-based
2. Structured with clear sections
3. Actionable with concrete recommendations
4. Transparent about confidence levels and information gaps

Format your response as JSON with keys: summary, findings, analysis, recommendations, sources_used, confidence"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute research analysis on a given topic.

        Expected input data:
        {
            "topic": "Research topic or question",
            "context": {
                "sources": [{"title": "...", "content": "...", "url": "..."}],
                "scope": "narrow|standard|broad",
                "focus_areas": ["area1", "area2"]
            }
        }

        Returns:
        {
            "summary": "Executive summary of findings",
            "findings": [{"finding": "...", "evidence": "...", "confidence": "high|medium|low"}],
            "analysis": "Detailed analysis narrative",
            "recommendations": [{"action": "...", "priority": "high|medium|low", "rationale": "..."}],
            "sources_used": ["source1", "source2"],
            "confidence": "high|medium|low"
        }
        """
        try:
            topic = agent_input.data.get("topic")
            if not topic:
                raise AgentExecutionError(
                    "Missing required field: 'topic'",
                    agent_name=self.agent_name,
                )

            context = agent_input.data.get("context", {})
            org_profile = agent_input.context.org_profile

            user_prompt = self._build_prompt(topic, context, org_profile)

            logger.info(f"{self.agent_name}: Researching topic: {topic[:80]}")
            response_text = await self.call_llm(
                user_prompt=user_prompt,
                max_tokens=4096,
                temperature=0.3,
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

    def _build_prompt(self, topic: str, context: dict, org_profile) -> str:
        """Build the research prompt with topic and context."""
        parts = [f"Research Topic:\n{topic}\n"]

        if org_profile:
            parts.append(
                f"\nOrganization Context:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        sources = context.get("sources", [])
        if sources:
            parts.append("\nAvailable Sources:\n")
            for i, src in enumerate(sources, 1):
                title = src.get("title", f"Source {i}")
                content = src.get("content", "")
                url = src.get("url", "")
                parts.append(f"\n[{i}] {title}")
                if url:
                    parts.append(f" ({url})")
                parts.append(f"\n{content}\n")

        scope = context.get("scope", "standard")
        parts.append(f"\nResearch Scope: {scope}\n")

        focus_areas = context.get("focus_areas", [])
        if focus_areas:
            areas = "\n".join(f"- {a}" for a in focus_areas)
            parts.append(f"\nFocus Areas:\n{areas}\n")

        parts.append(
            "\nProvide a structured research report as JSON with keys: "
            "summary, findings, analysis, recommendations, sources_used, confidence"
        )

        return "".join(parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        if "summary" not in result and "raw_text" in result:
            result["summary"] = result["raw_text"]
        if "summary" not in result:
            result["summary"] = ""
        if "findings" not in result:
            result["findings"] = []
        if "analysis" not in result:
            result["analysis"] = ""
        if "recommendations" not in result:
            result["recommendations"] = []
        if "sources_used" not in result:
            result["sources_used"] = []
        if "confidence" not in result:
            result["confidence"] = "medium"
        return result
