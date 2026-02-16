"""
ANO Logging Configuration

Provides structured logging setup with support for console and JSON formats,
agent-specific loggers, and integration with the ANO settings system.
"""

import json
import logging
import sys
from typing import Optional


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Include extra fields from LoggerAdapter
        if hasattr(record, "agent_name"):
            log_obj["agent_name"] = record.agent_name
        return json.dumps(log_obj)


def setup_logging(
    level: Optional[str] = None,
    json_format: bool = False,
) -> None:
    """
    Configure ANO framework logging.

    Sets up root logger with appropriate handlers and formatters based on
    the environment and configuration.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses ANO_LOG_LEVEL from settings.
        json_format: If True, output structured JSON logs.
                     If False, use human-readable console format.
    """
    from ano_core.settings import settings

    # Determine log level
    if level is None:
        level = settings.ANO_LOG_LEVEL

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Configure formatter
    if json_format:
        formatter = JsonFormatter(datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    root_logger.addHandler(handler)

    # Reduce noise from common third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_agent_logger(agent_name: str) -> logging.LoggerAdapter:
    """
    Get a logger configured for a specific agent.

    The returned logger automatically includes the agent name in all
    log records, making it easy to filter logs by agent in production.

    Args:
        agent_name: Name of the agent requesting the logger

    Returns:
        LoggerAdapter with agent context pre-configured
    """
    logger = logging.getLogger(f"ano.agent.{agent_name}")
    return logging.LoggerAdapter(logger, {"agent_name": agent_name})
