"""
Web Chat Channel Module

HTTP-based chat handler for web widgets and chat interfaces.
"""

from channels.web.chat_widget import WebChatHandler, create_web_chat_app

__all__ = [
    "WebChatHandler",
    "create_web_chat_app",
]
