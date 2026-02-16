"""
Telegram Webhook Handler

FastAPI webhook endpoint for receiving Telegram updates.
"""

import logging
from fastapi import FastAPI, Request, HTTPException

from channels.telegram.bot_service import TelegramBotService
from channels.telegram.config import TelegramConfig

logger = logging.getLogger(__name__)


def create_webhook_app(
    bot_service: TelegramBotService,
    config: TelegramConfig
) -> FastAPI:
    """
    Create a FastAPI app with Telegram webhook endpoint.

    Args:
        bot_service: Telegram bot service instance
        config: Telegram configuration

    Returns:
        FastAPI application

    Example:
        ```python
        config = TelegramConfig.from_env()
        bot = TelegramBotService(config, agent=my_agent)
        app = create_webhook_app(bot, config)

        # Run with uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```
    """
    app = FastAPI(title="ANO Telegram Bot", version="1.0.0")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    @app.post("/webhook")
    async def telegram_webhook(request: Request):
        """
        Receive Telegram updates.

        Validates webhook secret from X-Telegram-Bot-Api-Secret-Token header,
        parses update JSON, and routes to bot service.
        """
        # Validate webhook secret if configured
        if config.webhook_secret:
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if secret != config.webhook_secret:
                logger.warning("[Telegram] Invalid webhook secret")
                raise HTTPException(status_code=401, detail="Invalid webhook secret")

        # Parse update
        try:
            update = await request.json()
        except Exception as e:
            logger.error(f"[Telegram] Invalid JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Route to bot service
        try:
            result = await bot_service.handle_update(update)
            return result
        except Exception as e:
            logger.error(f"[Telegram] Update handling error: {e}")
            # Still return 200 to Telegram to avoid retries
            return {"ok": True}

    return app
