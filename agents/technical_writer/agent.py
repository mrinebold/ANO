"""
Technical Writer Agent

Documentation specialist that generates and reviews technical documentation,
API references, and user guides for agent-native organizations.
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TechnicalWriterAgent(BaseAgent):
    """
    Technical Writer Agent

    Generates and reviews technical documentation including API references,
    architecture docs, user guides, and changelogs. Ensures documentation
    is clear, accurate, and maintainable.
    """

    agent_name = "technical_writer"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the technical writer system prompt."""
        return """You are a technical documentation specialist for AI agent systems.

Your role is to:
- Generate clear, accurate technical documentation
- Write API references with examples and edge cases
- Create user guides and tutorials
- Review existing documentation for accuracy and completeness
- Maintain consistent documentation style and structure
- Generate changelogs and release notes

Your documentation style:
1. Clear and concise — no unnecessary jargon
2. Structured with headers, code examples, and tables
3. Task-oriented — organized around what users need to do
4. Complete — covers prerequisites, steps, expected outcomes, and troubleshooting
5. Versioned — notes which version features apply to

Format your response as JSON with keys: document, doc_type, sections, review_notes, suggested_improvements, metadata"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute documentation task.

        Expected input data:
        {
            "task": "generate|review|update",
            "subject": "What to document (API, module, feature, process)",
            "context": {
                "source_code": "...",
                "existing_docs": "...",
                "audience": "developer|operator|end-user",
                "format": "markdown|restructuredtext"
            }
        }

        Returns:
        {
            "document": "The generated or reviewed documentation content",
            "doc_type": "api_reference|user_guide|tutorial|architecture|changelog",
            "sections": [{"title": "...", "summary": "..."}],
            "review_notes": [{"location": "...", "issue": "...", "suggestion": "..."}],
            "suggested_improvements": [...],
            "metadata": {"word_count": N, "code_examples": N, "audience": "..."}
        }
        """
        try:
            task = agent_input.data.get("task")
            subject = agent_input.data.get("subject")
            if not task or not subject:
                missing = []
                if not task:
                    missing.append("'task'")
                if not subject:
                    missing.append("'subject'")
                raise AgentExecutionError(
                    f"Missing required field(s): {', '.join(missing)}",
                    agent_name=self.agent_name,
                )

            context = agent_input.data.get("context", {})
            org_profile = agent_input.context.org_profile

            user_prompt = self._build_prompt(task, subject, context, org_profile)

            logger.info(f"{self.agent_name}: {task} documentation for: {subject[:80]}")
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

    def _build_prompt(self, task: str, subject: str, context: dict, org_profile) -> str:
        """Build the documentation task prompt."""
        parts = [f"Documentation Task: {task}\nSubject: {subject}\n"]

        if org_profile:
            parts.append(
                f"\nOrganization:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        audience = context.get("audience", "developer")
        parts.append(f"\nTarget Audience: {audience}\n")

        doc_format = context.get("format", "markdown")
        parts.append(f"Output Format: {doc_format}\n")

        if context.get("source_code"):
            parts.append(f"\nSource Code:\n```\n{context['source_code']}\n```\n")

        if context.get("existing_docs"):
            parts.append(f"\nExisting Documentation:\n{context['existing_docs']}\n")

        parts.append(
            "\nProvide documentation output as JSON with keys: "
            "document, doc_type, sections, review_notes, suggested_improvements, metadata"
        )

        return "".join(parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        if "document" not in result and "raw_text" in result:
            result["document"] = result["raw_text"]
        if "document" not in result:
            result["document"] = ""
        if "doc_type" not in result:
            result["doc_type"] = "general"
        if "sections" not in result:
            result["sections"] = []
        if "review_notes" not in result:
            result["review_notes"] = []
        if "suggested_improvements" not in result:
            result["suggested_improvements"] = []
        if "metadata" not in result:
            result["metadata"] = {}
        return result
