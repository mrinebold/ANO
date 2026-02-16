"""
Telegram Bot Service

Core service for handling Telegram bot interactions.
Routes messages to configured agent and manages rate limiting, authentication.
"""

import httpx
import logging
import time
from typing import Any, Callable, Optional
from collections import defaultdict

from channels.base_channel import BaseChannel
from channels.telegram.config import TelegramConfig
from channels.telegram.auth import TelegramAuth
from channels.telegram.commands import CommandRegistry

logger = logging.getLogger(__name__)


class TelegramBotService(BaseChannel):
    """Telegram bot that routes messages to an agent."""

    channel_name = "telegram"

    def __init__(
        self,
        config: TelegramConfig,
        agent: Any = None,
        auth: Optional[TelegramAuth] = None
    ):
        """
        Initialize Telegram bot service.

        Args:
            config: Telegram configuration
            agent: Optional agent to handle messages
            auth: Optional authentication/authorization handler
        """
        super().__init__()
        self.config = config
        self._agent = agent
        self.auth = auth or TelegramAuth()
        self.commands = CommandRegistry()

        # Rate limiting: user_id -> list of timestamps
        self._rate_limits: dict[int, list[float]] = defaultdict(list)

        # Message handler for non-command messages
        self._message_handler: Optional[Callable[[str, dict], str]] = None

    def set_message_handler(self, handler: Callable[[str, dict], str]) -> None:
        """
        Set a custom message handler for non-command messages.

        Args:
            handler: Callable that takes (text, metadata) and returns response text
        """
        self._message_handler = handler

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """
        Send message via Telegram Bot API using httpx.

        Args:
            chat_id: Telegram chat ID
            text: Message text to send
            parse_mode: Optional parse mode override (Markdown, HTML, or None)

        Returns:
            True if message was sent successfully, False otherwise
        """
        if not self.config.bot_token:
            logger.error("[Telegram] Bot token not configured")
            return False

        # Truncate message if needed
        if len(text) > self.config.max_message_length:
            text = text[:self.config.max_message_length - 50] + "\n\n[Message truncated]"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage",
                    json={
                        "chat_id": int(chat_id) if chat_id.isdigit() else chat_id,
                        "text": text,
                        "parse_mode": parse_mode or self.config.parse_mode,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    logger.debug(f"[Telegram] Message sent to {chat_id}")
                    return True
                else:
                    logger.error(
                        f"[Telegram] Failed to send message: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"[Telegram] Failed to send message: {e}")
            return False

    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Check if user is within rate limit.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is within rate limit, False otherwise
        """
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Remove timestamps outside the window
        self._rate_limits[user_id] = [
            ts for ts in self._rate_limits[user_id]
            if ts > window_start
        ]

        # Check if over limit
        if len(self._rate_limits[user_id]) >= self.config.rate_limit_per_minute:
            return False

        # Add current timestamp
        self._rate_limits[user_id].append(now)
        return True

    async def handle_message(
        self,
        sender_id: str,
        text: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Route message to agent or command handler, return response text.

        Args:
            sender_id: Telegram user ID
            text: Message text
            metadata: Optional metadata (username, first_name, etc.)

        Returns:
            Response text
        """
        metadata = metadata or {}
        user_id = int(sender_id)

        # Check rate limit
        if not self._check_rate_limit(user_id):
            return "You're sending messages too fast. Please wait a moment."

        # Parse command
        cmd_tuple = self.commands.parse_command(text)
        command = cmd_tuple[0]
        args = cmd_tuple[1]

        if command:
            # Handle as command
            handler = self.commands.get_handler(command)
            if handler:
                try:
                    # Check tier access if auth is configured
                    user_tier = metadata.get("tier", self.auth.get_default_tier())
                    required_tier = self.commands.commands.get(command, {}).get("required_tier", "free")

                    if not self.auth.check_access(user_tier, required_tier):
                        return (
                            f"The /{command} command requires {required_tier} tier access. "
                            f"Your current tier: {user_tier}"
                        )

                    # Call command handler
                    result = handler(sender_id, args, metadata)
                    if hasattr(result, "__await__"):
                        result = await result
                    return result

                except Exception as e:
                    logger.error(f"[Telegram] Command handler error: {e}")
                    return f"Error processing command: {str(e)}"
            else:
                return (
                    f"Unknown command: /{command}\n\n"
                    "Type /help to see available commands."
                )
        else:
            # Handle as natural language message
            if self._message_handler:
                try:
                    result = self._message_handler(text, metadata)
                    if hasattr(result, "__await__"):
                        result = await result
                    return result
                except Exception as e:
                    logger.error(f"[Telegram] Message handler error: {e}")
                    return "Sorry, I encountered an error processing your message."

            elif self._agent and hasattr(self._agent, "execute"):
                try:
                    result = self._agent.execute(text, metadata)
                    if hasattr(result, "__await__"):
                        result = await result
                    return result
                except Exception as e:
                    logger.error(f"[Telegram] Agent execution error: {e}")
                    return "Sorry, I encountered an error processing your message."

            else:
                return (
                    "I don't understand. Please use a command like /help, "
                    "or configure a message handler for this bot."
                )

    async def handle_update(self, update: dict[str, Any]) -> dict[str, bool]:
        """
        Process a raw Telegram update (from webhook).

        Args:
            update: Telegram update dictionary

        Returns:
            {"ok": True} on success
        """
        # Extract message
        message = update.get("message")
        if not message or not message.get("text"):
            return {"ok": True}

        chat_id = message["chat"]["id"]
        from_user = message.get("from", {})
        user_id = from_user.get("id")
        username = from_user.get("username", "")
        first_name = from_user.get("first_name", "")
        text = message["text"]

        if not user_id:
            return {"ok": True}

        logger.info(f"[Telegram] Message from {user_id}: {text[:50]}")

        # Build metadata
        metadata = {
            "username": username,
            "first_name": first_name,
            "chat_id": chat_id,
        }

        # Route to handler
        response = await self.handle_message(str(user_id), text, metadata)

        # Send response
        await self.send_message(str(chat_id), response)

        return {"ok": True}

    def register_command(
        self,
        command: str,
        handler: Callable[[str, str, dict], str],
        description: str = "",
        required_tier: str = "free"
    ) -> None:
        """
        Register a /command handler.

        Args:
            command: Command name (without leading /)
            handler: Callable that takes (sender_id, args, metadata) and returns response
            description: Human-readable description
            required_tier: Minimum tier required to use this command
        """
        self.commands.register(command, handler, description, required_tier)

    async def set_webhook(self, url: str) -> bool:
        """
        Call Telegram setWebhook API.

        Args:
            url: Webhook URL

        Returns:
            True if webhook was set successfully, False otherwise
        """
        if not self.config.bot_token:
            logger.error("[Telegram] Bot token not configured")
            return False

        try:
            payload: dict[str, Any] = {"url": url}

            # Add secret token if configured
            if self.config.webhook_secret:
                payload["secret_token"] = self.config.webhook_secret

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.config.bot_token}/setWebhook",
                    json=payload,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        logger.info(f"[Telegram] Webhook set to {url}")
                        return True
                    else:
                        logger.error(f"[Telegram] Webhook API error: {data}")
                        return False
                else:
                    logger.error(
                        f"[Telegram] Failed to set webhook: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"[Telegram] Failed to set webhook: {e}")
            return False
