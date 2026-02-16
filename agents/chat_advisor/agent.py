"""
Chat Advisor Agent

Provides knowledge-grounded conversational assistance. Designed to be deployed
via Telegram bots, web chat widgets, or other messaging channels.
"""

import json
import logging
from datetime import datetime

from ano_core.errors import AgentExecutionError
from ano_core.types import AgentInput, AgentOutput
from agent_framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ChatAdvisorAgent(BaseAgent):
    """
    Chat Advisor Agent

    Provides conversational assistance grounded in provided documents and
    organizational knowledge. Can be deployed via:
    - Telegram bot
    - Web chat widget
    - Slack bot
    - Other messaging platforms

    Key features:
    - Document-grounded responses
    - Contextual conversation history
    - Clear citation of sources
    - Graceful handling of out-of-scope questions
    """

    agent_name = "chat_advisor"
    version = "1.0.0"

    def get_system_prompt(self) -> str:
        """Return the chat advisor system prompt."""
        return """You are a knowledgeable advisor providing assistance through a conversational interface.

Your role is to:
- Answer user questions clearly and accurately
- Ground your responses in provided documents and context
- Cite sources when making claims or providing information
- Admit when you don't know something or when a question is outside your knowledge base
- Maintain a helpful, professional, and friendly tone
- Provide actionable guidance when appropriate

When answering:
1. Check if the provided context contains relevant information
2. If yes, answer based on that context and cite the source
3. If no, clearly state that the question is outside your current knowledge
4. Never make up information or speculate beyond what's in the context

Your communication style is conversational yet professional, concise yet thorough."""

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute conversational response generation.

        Expected input data structure:
        {
            "message": "User's question or message",
            "context": {
                "documents": [
                    {
                        "title": "Document title",
                        "content": "Document content",
                        "source": "URL or identifier"
                    }
                ],
                "conversation_history": [
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."}
                ]
            }
        }

        Returns:
        {
            "response": "The agent's conversational response",
            "sources_cited": ["source1", "source2"],
            "confidence": "high|medium|low",
            "suggested_followups": ["question1", "question2"]
        }

        Args:
            agent_input: Input containing user message and context

        Returns:
            AgentOutput with conversational response

        Raises:
            AgentExecutionError: If execution fails
        """
        started_at = datetime.utcnow()

        try:
            # Extract message
            message = agent_input.data.get("message")
            if not message:
                raise AgentExecutionError(
                    "Missing required field: 'message'",
                    agent_name=self.agent_name,
                )

            context = agent_input.data.get("context", {})

            # Build user prompt with context
            user_prompt = self._build_prompt(message, context)

            # Call LLM
            logger.info(f"{self.agent_name}: Processing user message")
            response_text = await self.call_llm(
                user_prompt=user_prompt,
                max_tokens=2048,
                temperature=0.5,  # Slightly higher for conversational tone
            )

            # Parse response
            result = self.parse_json_response(response_text)

            # Validate and structure result
            result = self._validate_result(result, response_text)

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

    def _build_prompt(self, message: str, context: dict) -> str:
        """Build the user prompt with message and context."""
        prompt_parts = [f"User Question:\n{message}\n"]

        # Add document context if available
        documents = context.get("documents", [])
        if documents:
            prompt_parts.append("\nAvailable Knowledge:\n")
            for i, doc in enumerate(documents, 1):
                title = doc.get("title", f"Document {i}")
                content = doc.get("content", "")
                source = doc.get("source", "")

                prompt_parts.append(f"\n[{i}] {title}")
                if source:
                    prompt_parts.append(f" (Source: {source})")
                prompt_parts.append(f"\n{content}\n")

        # Add conversation history if available
        history = context.get("conversation_history", [])
        if history:
            prompt_parts.append("\nConversation History:\n")
            for turn in history[-5:]:  # Last 5 turns
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                prompt_parts.append(f"{role.capitalize()}: {content}\n")

        # Add response instructions
        prompt_parts.append(
            "\nProvide a helpful response to the user's question. "
            "Format your response as JSON with keys:\n"
            "- response: Your conversational answer\n"
            "- sources_cited: Array of sources you referenced (if any)\n"
            "- confidence: Your confidence level (high/medium/low)\n"
            "- suggested_followups: 2-3 suggested follow-up questions (optional)\n"
        )

        return "".join(prompt_parts)

    def _validate_result(self, result: dict, raw_text: str) -> dict:
        """Validate and structure the parsed result."""
        # Handle raw text fallback
        if "raw_text" in result and "response" not in result:
            result["response"] = result["raw_text"]

        # Ensure response exists
        if "response" not in result:
            result["response"] = raw_text

        # Ensure sources_cited is a list
        if "sources_cited" not in result:
            result["sources_cited"] = []
        elif not isinstance(result["sources_cited"], list):
            result["sources_cited"] = [result["sources_cited"]]

        # Ensure confidence exists
        if "confidence" not in result:
            result["confidence"] = "medium"

        # Ensure suggested_followups is a list
        if "suggested_followups" not in result:
            result["suggested_followups"] = []
        elif not isinstance(result["suggested_followups"], list):
            result["suggested_followups"] = []

        return result
