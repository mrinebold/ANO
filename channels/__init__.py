"""
ANO Foundation Channels Module

Deployment channels for agents — Telegram, web chat, CLI.
Provides a unified interface for agents to communicate across different platforms.
"""

from channels.base_channel import BaseChannel
from channels.telegram import TelegramBotService, TelegramConfig, create_webhook_app

__all__ = [
    "BaseChannel",
    "TelegramBotService",
    "TelegramConfig",
    "create_webhook_app",
]
