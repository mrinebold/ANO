"""
Example: CLI REPL

Demonstrates how to create a CLI REPL using the channels module.
"""

import asyncio
import logging
from channels.cli import CLIRepl


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example agent with state
class StatefulAgent:
    """Simple stateful agent for demonstration."""

    def __init__(self):
        self.conversation_count = 0
        self.user_name = None

    async def execute(self, text: str, metadata: dict) -> str:
        """
        Process user input with internal state.

        Args:
            text: User message text
            metadata: Channel metadata

        Returns:
            Response text
        """
        self.conversation_count += 1

        # Handle name setting
        if text.lower().startswith("my name is "):
            self.user_name = text[11:].strip()
            return f"Nice to meet you, {self.user_name}!"

        # Personalized greeting
        if self.user_name:
            greeting = f"Hello {self.user_name}!"
        else:
            greeting = "Hello! (Tell me your name with 'my name is [name]')"

        # Show conversation count
        return f"{greeting} This is message #{self.conversation_count}. You said: {text}"


async def main():
    """Main entry point."""
    try:
        # Create agent
        agent = StatefulAgent()
        logger.info("Agent created")

        # Create CLI REPL
        repl = CLIRepl(agent=agent, prompt="chat> ")
        logger.info("CLI REPL created")

        # Run REPL
        await repl.run()

        logger.info("REPL session ended")

    except Exception as e:
        logger.error(f"REPL error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
