"""
Reference Agents

Provides 4 reference agent implementations demonstrating the ANO framework:
- CEOAdvisorAgent: Strategic leadership and organizational guidance
- CTOAdvisorAgent: Technical strategy and architecture decisions
- AgentBuilderAgent: HR department for onboarding and certifying agents
- ChatAdvisorAgent: Knowledge-grounded conversational advisor
"""

from agents.agent_builder import AgentBuilderAgent, AgentSpec, CertificationReport, OnboardingResult
from agents.ceo import CEOAdvisorAgent
from agents.chat_advisor import ChatAdvisorAgent
from agents.cto import CTOAdvisorAgent

__all__ = [
    "CEOAdvisorAgent",
    "CTOAdvisorAgent",
    "AgentBuilderAgent",
    "ChatAdvisorAgent",
    "AgentSpec",
    "CertificationReport",
    "OnboardingResult",
]
