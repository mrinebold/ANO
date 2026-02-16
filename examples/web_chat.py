"""
Example: Web Chat Widget

Demonstrates how to create a web chat API using the channels module.
"""

import asyncio
import logging
from channels.web import WebChatHandler, create_web_chat_app


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example agent with conversation context
class ConversationalAgent:
    """Simple conversational agent for demonstration."""

    async def execute(self, text: str, metadata: dict) -> str:
        """
        Process user input with conversation history.

        Args:
            text: User message text
            metadata: Channel metadata including session_history

        Returns:
            Response text
        """
        # Get conversation history from metadata
        history = metadata.get("session_history", [])
        message_count = len([m for m in history if m.get("role") == "user"])

        # Simple responses based on conversation state
        if message_count == 1:
            return "Hi! I'm your AI assistant. How can I help you today?"

        if "hello" in text.lower() or "hi" in text.lower():
            return "Hello! What would you like to talk about?"

        if "bye" in text.lower() or "goodbye" in text.lower():
            return "Goodbye! Feel free to come back anytime."

        # Echo with context
        return f"I received your message: '{text}'. This is message #{message_count} in our conversation."


async def main():
    """Main entry point."""
    try:
        # Create agent
        agent = ConversationalAgent()
        logger.info("Agent created")

        # Create web chat handler
        handler = WebChatHandler(agent=agent)
        logger.info("Web chat handler created")

        # Create web app
        app = create_web_chat_app(handler)
        logger.info("Web app created")

        # Add CORS for development (remove or restrict in production)
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production: restrict to your domain
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS configured for development")

        # Run with uvicorn
        logger.info("Starting server on http://0.0.0.0:8000")
        logger.info("API endpoints:")
        logger.info("  POST /chat - Send message")
        logger.info("  GET /session/{session_id} - Get session history")
        logger.info("  GET /health - Health check")

        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
