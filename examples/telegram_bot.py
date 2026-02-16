"""
Example: Simple Telegram Bot

Demonstrates how to create a Telegram bot using the channels module.
"""

import asyncio
import logging
from channels.telegram import TelegramConfig, TelegramBotService, create_webhook_app


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Example agent that echoes messages
class EchoAgent:
    """Simple echo agent for demonstration."""

    async def execute(self, text: str, metadata: dict) -> str:
        """
        Process user input.

        Args:
            text: User message text
            metadata: Channel metadata (username, chat_id, etc.)

        Returns:
            Response text
        """
        username = metadata.get("username", "unknown")
        return f"Hello @{username}! You said: {text}"


# Command handlers
def handle_start(sender_id: str, args: str, metadata: dict) -> str:
    """Handle /start command."""
    first_name = metadata.get("first_name", "there")
    if args:
        return f"Welcome, {first_name}! You provided: {args}"
    return f"Welcome, {first_name}! Use /help to see available commands."


def handle_help(sender_id: str, args: str, metadata: dict) -> str:
    """Handle /help command."""
    return """
Available commands:

/start - Start the bot
/help - Show this help message
/echo [text] - Echo your message
/about - About this bot

Or just send any message and I'll echo it back!
"""


def handle_echo(sender_id: str, args: str, metadata: dict) -> str:
    """Handle /echo command."""
    if not args:
        return "Usage: /echo [text to echo]"
    return f"Echo: {args}"


def handle_about(sender_id: str, args: str, metadata: dict) -> str:
    """Handle /about command."""
    return """
This is an example Telegram bot built with ANO Foundation channels.

- Clean Python 3.11+ codebase
- Type hints throughout
- Production logging
- Rate limiting built-in
- Tier-based access control

Built with the ANO Foundation framework.
"""


async def main():
    """Main entry point."""
    try:
        # Load configuration from environment
        config = TelegramConfig.from_env()
        logger.info("Telegram config loaded")

        # Create agent
        agent = EchoAgent()
        logger.info("Agent created")

        # Create bot service
        bot = TelegramBotService(config, agent=agent)
        logger.info("Bot service created")

        # Register commands
        bot.register_command("start", handle_start, "Start the bot", "free")
        bot.register_command("help", handle_help, "Show help", "free")
        bot.register_command("echo", handle_echo, "Echo a message", "free")
        bot.register_command("about", handle_about, "About this bot", "free")
        logger.info("Commands registered")

        # Create webhook app
        app = create_webhook_app(bot, config)
        logger.info("Webhook app created")

        # Set webhook if URL is configured
        if config.webhook_url:
            success = await bot.set_webhook(config.webhook_url)
            if success:
                logger.info(f"Webhook set to {config.webhook_url}")
            else:
                logger.error("Failed to set webhook")

        # Run with uvicorn
        logger.info("Starting server on http://0.0.0.0:8000")
        logger.info("Webhook endpoint: POST /webhook")

        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Make sure TELEGRAM_BOT_TOKEN is set in your environment")
        return 1

    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
