"""
Command Registry

Registry for /command handlers in Telegram bots.
"""

from typing import Callable, Optional, List, Tuple, Dict, Any


class CommandRegistry:
    """Registry for /command handlers."""

    def __init__(self):
        """Initialize command registry."""
        self.commands: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        command: str,
        handler: Callable,
        description: str = "",
        required_tier: str = "free"
    ) -> None:
        """
        Register a command handler.

        Args:
            command: Command name (without leading /)
            handler: Callable that handles the command
            description: Human-readable description
            required_tier: Minimum tier required to use this command
        """
        self.commands[command] = {
            "handler": handler,
            "description": description,
            "required_tier": required_tier,
        }

    def get_handler(self, command: str) -> Optional[Callable]:
        """
        Get handler for a command.

        Args:
            command: Command name (without leading /)

        Returns:
            Handler callable, or None if command not found
        """
        cmd_data = self.commands.get(command)
        return cmd_data["handler"] if cmd_data else None

    def list_commands(self, user_tier: str = "free") -> List[Dict[str, Any]]:
        """
        List all commands accessible to a tier.

        Args:
            user_tier: User's tier name

        Returns:
            List of command info dicts with keys: command, description, required_tier
        """
        # This is a simple implementation - in production, you'd want to
        # integrate with TelegramAuth to check hierarchical tier access
        return [
            {
                "command": cmd,
                "description": data["description"],
                "required_tier": data["required_tier"],
            }
            for cmd, data in self.commands.items()
        ]

    @staticmethod
    def parse_command(text: str) -> Tuple[Optional[str], str]:
        """
        Parse '/command args' into (command, args).

        Args:
            text: Message text

        Returns:
            (command, args) tuple. Returns (None, text) if not a command.

        Examples:
            "/start abc123" -> ("start", "abc123")
            "/help" -> ("help", "")
            "hello world" -> (None, "hello world")
            "/start@botname args" -> ("start", "args")  # handles bot mentions
        """
        if not text.startswith('/'):
            return (None, text)

        # Split into command and args
        parts = text.split(maxsplit=1)
        command_part = parts[0].lstrip('/')
        args = parts[1] if len(parts) > 1 else ""

        # Handle bot mentions (e.g., /start@botname)
        command = command_part.split('@')[0].lower()

        return (command, args)
