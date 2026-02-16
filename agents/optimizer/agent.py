"""
Optimizer Agent

Performance and cost optimization specialist that analyzes LLM usage patterns,
recommends model selections, and identifies efficiency improvements.
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class OptimizerAgent(BaseAgent):
    """
    Optimizer Agent

    Analyzes system performance, LLM token usage, model selection,
    and operational costs to recommend optimizations for agent-native
    organizations.
    """

    agent_name = "optimizer"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the optimizer system prompt."""
        return """You are a performance and cost optimization specialist for AI agent systems.

Your role is to:
- Analyze LLM token usage patterns and identify waste
- Recommend appropriate model selections (smaller models for simple tasks)
- Identify prompt optimization opportunities (caching, compression, batching)
- Evaluate cost-performance tradeoffs across different LLM providers
- Recommend infrastructure and operational efficiency improvements
- Quantify expected savings from proposed optimizations

Your analysis should be data-driven with specific, measurable recommendations. Always provide expected impact (cost savings, latency improvement, quality tradeoffs).

Format your response as JSON with keys: analysis, optimizations, model_recommendations, estimated_impact, risks, next_steps"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute optimization analysis.

        Expected input data:
        {
            "target": "What to optimize (e.g., 'token usage', 'latency', 'cost')",
            "context": {
                "current_usage": {...},
                "budget_constraints": "...",
                "quality_requirements": "...",
                "current_models": [{"agent": "...", "model": "...", "avg_tokens": N}]
            }
        }

        Returns:
        {
            "analysis": "Current state analysis",
            "optimizations": [{"area": "...", "action": "...", "expected_savings": "...", "priority": "high|medium|low"}],
            "model_recommendations": [{"agent": "...", "current": "...", "recommended": "...", "rationale": "..."}],
            "estimated_impact": {"cost_reduction": "...", "latency_change": "...", "quality_impact": "..."},
            "risks": [...],
            "next_steps": [...]
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

            logger.info(f"{self.agent_name}: Analyzing optimization target: {target[:80]}")
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
        """Build the optimization analysis prompt."""
        parts = [f"Optimization Target:\n{target}\n"]

        if org_profile:
            parts.append(
                f"\nOrganization:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        if context.get("current_usage"):
            import json
            parts.append(f"\nCurrent Usage Data:\n{json.dumps(context['current_usage'], indent=2)}\n")

        if context.get("current_models"):
            parts.append("\nCurrent Model Assignments:\n")
            for m in context["current_models"]:
                parts.append(f"- {m.get('agent', '?')}: {m.get('model', '?')} (avg {m.get('avg_tokens', '?')} tokens)\n")

        if context.get("budget_constraints"):
            parts.append(f"\nBudget Constraints: {context['budget_constraints']}\n")

        if context.get("quality_requirements"):
            parts.append(f"\nQuality Requirements: {context['quality_requirements']}\n")

        parts.append(
            "\nProvide optimization recommendations as JSON with keys: "
            "analysis, optimizations, model_recommendations, estimated_impact, risks, next_steps"
        )

        return "".join(parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        if "analysis" not in result and "raw_text" in result:
            result["analysis"] = result["raw_text"]
        if "analysis" not in result:
            result["analysis"] = ""
        if "optimizations" not in result:
            result["optimizations"] = []
        if "model_recommendations" not in result:
            result["model_recommendations"] = []
        if "estimated_impact" not in result:
            result["estimated_impact"] = {}
        if "risks" not in result:
            result["risks"] = []
        if "next_steps" not in result:
            result["next_steps"] = []
        return result
