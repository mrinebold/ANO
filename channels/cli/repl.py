"""
CLI REPL

Interactive command-line REPL for testing agents locally.
"""

import asyncio
import sys
import logging
from typing import Any, Optional, Dict

from channels.base_channel import BaseChannel

logger = logging.getLogger(__name__)


class CLIRepl(BaseChannel):
    """Interactive CLI REPL for testing agents locally."""

    channel_name = "cli"

    def __init__(self, agent: Any = None, prompt: str = "> "):
        """
        Initialize CLI REPL.

        Args:
            agent: Optional agent to handle messages
            prompt: Prompt string for user input
        """
        super().__init__()
        self._agent = agent
        self.prompt = prompt
        self._running = False

    async def send_message(self, recipient_id: str, text: str, **kwargs) -> bool:
        """
        Send message (print to stdout).

        Args:
            recipient_id: Ignored for CLI
            text: Message text to print
            **kwargs: Additional options

        Returns:
            Always True
        """
        print(text)
        return True

    async def handle_message(
        self,
        sender_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle message from CLI user.

        Args:
            sender_id: CLI user ID (usually "cli_user")
            text: User input text
            metadata: Optional metadata

        Returns:
            Response text
        """
        metadata = metadata or {}

        # Route to agent
        if self._agent and hasattr(self._agent, "execute"):
            try:
                result = self._agent.execute(text, metadata)
                if hasattr(result, "__await__"):
                    result = await result
                return result
            except Exception as e:
                logger.error(f"[CLI] Agent execution error: {e}")
                return f"Error: {str(e)}"
        else:
            return "CLI REPL not configured with an agent."

    async def run(self, user_id: str = "cli_user") -> None:
        """
        Start interactive REPL loop.

        Reads from stdin, routes to agent, prints responses.

        Args:
            user_id: User ID for this REPL session
        """
        self._running = True
        print("ANO Agent REPL")
        print("Type 'quit' or 'exit' to stop, 'help' for commands.")
        print()

        while self._running:
            try:
                # Read user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: input(self.prompt)
                )

                # Strip whitespace
                user_input = user_input.strip()

                # Handle empty input
                if not user_input:
                    continue

                # Handle quit commands
                if user_input.lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                # Handle built-in commands
                if user_input.lower() == "help":
                    self._print_help()
                    continue

                if user_input.lower() == "clear":
                    self._clear_screen()
                    continue

                # Route to agent
                response = await self.handle_message(user_id, user_input)
                print(response)
                print()

            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
                continue

            except EOFError:
                print("\nGoodbye!")
                break

            except Exception as e:
                logger.error(f"[CLI] REPL error: {e}")
                print(f"Error: {str(e)}")
                print()

        self._running = False

    def stop(self) -> None:
        """Stop the REPL."""
        self._running = False

    def _print_help(self) -> None:
        """Print help message."""
        print("ANO Agent REPL Commands:")
        print("  quit, exit, q - Exit the REPL")
        print("  help          - Show this help message")
        print("  clear         - Clear the screen")
        print()
        print("Everything else is sent to the agent.")
        print()

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        # Works on Unix/Linux/Mac
        if sys.platform != "win32":
            print("\033[2J\033[H", end="")
        else:
            # Windows
            import os
            os.system("cls")


async def main():
    """Example CLI REPL usage."""
    # Example: Create a simple echo agent
    class EchoAgent:
        async def execute(self, text: str, metadata: dict) -> str:
            return f"Echo: {text}"

    agent = EchoAgent()
    repl = CLIRepl(agent=agent)
    await repl.run()


if __name__ == "__main__":
    asyncio.run(main())
