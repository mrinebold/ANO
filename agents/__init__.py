"""
Reference Agents

Provides 9 reference agent implementations demonstrating the ANO framework:
- CEOAdvisorAgent: Strategic leadership and organizational guidance
- CTOAdvisorAgent: Technical strategy and architecture decisions
- AgentBuilderAgent: HR department for onboarding and certifying agents
- ChatAdvisorAgent: Knowledge-grounded conversational advisor
- ResearcherAgent: General-purpose research and analysis
- OptimizerAgent: Performance and cost optimization
- QASpecialistAgent: Quality assurance and test planning
- SecurityReviewerAgent: Security assessment and vulnerability review
- TechnicalWriterAgent: Documentation generation and review
"""

from agents.agent_builder import AgentBuilderAgent, AgentSpec, CertificationReport, OnboardingResult
from agents.ceo import CEOAdvisorAgent
from agents.chat_advisor import ChatAdvisorAgent
from agents.cto import CTOAdvisorAgent
from agents.optimizer import OptimizerAgent
from agents.qa_specialist import QASpecialistAgent
from agents.researcher import ResearcherAgent
from agents.security_reviewer import SecurityReviewerAgent
from agents.technical_writer import TechnicalWriterAgent

__all__ = [
    "CEOAdvisorAgent",
    "CTOAdvisorAgent",
    "AgentBuilderAgent",
    "ChatAdvisorAgent",
    "ResearcherAgent",
    "OptimizerAgent",
    "QASpecialistAgent",
    "SecurityReviewerAgent",
    "TechnicalWriterAgent",
    "AgentSpec",
    "CertificationReport",
    "OnboardingResult",
]
