"""
Security Reviewer Agent

Security review specialist that assesses vulnerabilities, audits dependencies,
and enforces security best practices for agent-native organizations.
"""

import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SecurityReviewerAgent(BaseAgent):
    """
    Security Reviewer Agent

    Performs security assessments of agent code, configurations, and
    dependencies. Identifies vulnerabilities, reviews access controls,
    and recommends security hardening measures.
    """

    agent_name = "security_reviewer"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the security reviewer system prompt."""
        return """You are a security review specialist for AI agent systems.

Your role is to:
- Review agent code and configurations for security vulnerabilities
- Audit dependency chains for known CVEs
- Assess access control and authentication mechanisms
- Evaluate data handling practices (PII, secrets, encryption)
- Review API security (input validation, rate limiting, authentication)
- Check for prompt injection and LLM-specific attack vectors
- Recommend security hardening measures

Your analysis should follow security best practices:
1. OWASP Top 10 for web applications
2. LLM-specific threats (prompt injection, data exfiltration, jailbreaking)
3. Supply chain security (dependencies, build pipeline)
4. Secrets management (API keys, credentials, tokens)
5. Principle of least privilege for agent permissions

Severity levels: critical (immediate action), high (fix within 24h), medium (fix within sprint), low (track and plan).

Format your response as JSON with keys: assessment, vulnerabilities, dependency_audit, recommendations, compliance_notes, risk_score"""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute security review.

        Expected input data:
        {
            "target": "What to review (code, config, dependency, system)",
            "context": {
                "code_content": "...",
                "dependencies": [...],
                "configuration": {...},
                "access_patterns": [...]
            }
        }

        Returns:
        {
            "assessment": "Overall security assessment narrative",
            "vulnerabilities": [{"severity": "critical|high|medium|low", "title": "...", "description": "...", "remediation": "..."}],
            "dependency_audit": {"total": N, "vulnerable": N, "details": [...]},
            "recommendations": [{"priority": "high|medium|low", "action": "...", "rationale": "..."}],
            "compliance_notes": [...],
            "risk_score": "critical|high|medium|low"
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

            logger.info(f"{self.agent_name}: Security review of: {target[:80]}")
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
        """Build the security review prompt."""
        parts = [f"Security Review Target:\n{target}\n"]

        if org_profile:
            parts.append(
                f"\nOrganization:\n"
                f"- Name: {org_profile.org_name}\n"
                f"- Type: {org_profile.org_type}\n"
            )

        if context.get("code_content"):
            parts.append(f"\nCode to Review:\n```\n{context['code_content']}\n```\n")

        if context.get("dependencies"):
            deps = "\n".join(f"- {d}" for d in context["dependencies"])
            parts.append(f"\nDependencies:\n{deps}\n")

        if context.get("configuration"):
            import json
            parts.append(f"\nConfiguration:\n{json.dumps(context['configuration'], indent=2)}\n")

        if context.get("access_patterns"):
            patterns = "\n".join(f"- {p}" for p in context["access_patterns"])
            parts.append(f"\nAccess Patterns:\n{patterns}\n")

        parts.append(
            "\nProvide a security review as JSON with keys: "
            "assessment, vulnerabilities, dependency_audit, recommendations, compliance_notes, risk_score"
        )

        return "".join(parts)

    def _validate_result(self, result: dict) -> dict:
        """Validate and structure the parsed result."""
        if "assessment" not in result and "raw_text" in result:
            result["assessment"] = result["raw_text"]
        if "assessment" not in result:
            result["assessment"] = ""
        if "vulnerabilities" not in result:
            result["vulnerabilities"] = []
        if "dependency_audit" not in result:
            result["dependency_audit"] = {}
        if "recommendations" not in result:
            result["recommendations"] = []
        if "compliance_notes" not in result:
            result["compliance_notes"] = []
        if "risk_score" not in result:
            result["risk_score"] = "medium"
        return result
