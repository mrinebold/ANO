"""
Base Channel Interface

Abstract interface for all deployment channels (Telegram, web, CLI, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseChannel(ABC):
    """Interface for all deployment channels (Telegram, web, CLI, etc.)."""

    channel_name: str = "base"

    def __init__(self):
        self._agent: Any = None

    @abstractmethod
    async def send_message(self, recipient_id: str, text: str, **kwargs) -> bool:
        """
        Send a message to a recipient on this channel.

        Args:
            recipient_id: Channel-specific recipient identifier (chat_id, session_id, etc.)
            text: Message text to send
            **kwargs: Channel-specific options (parse_mode, buttons, etc.)

        Returns:
            True if message was sent successfully, False otherwise
        """
        pass

    @abstractmethod
    async def handle_message(
        self,
        sender_id: str,
        text: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Handle an incoming message from a user.

        Args:
            sender_id: Channel-specific sender identifier
            text: Message text from sender
            metadata: Optional channel-specific metadata (username, first_name, etc.)

        Returns:
            Response text to send back to sender
        """
        pass

    def set_agent(self, agent: Any) -> None:
        """
        Set the agent that handles messages on this channel.

        Args:
            agent: An agent instance with an execute() or similar method
        """
        self._agent = agent
