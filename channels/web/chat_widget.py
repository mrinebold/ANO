"""
Web Chat Widget Handler

HTTP-based chat handler for web widgets.
Provides a simple REST API for chat interactions.
"""

import logging
import uuid
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from channels.base_channel import BaseChannel

logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    """Chat message request model."""
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """Chat response model."""
    session_id: str
    response: str
    timestamp: str


class WebChatHandler(BaseChannel):
    """HTTP-based chat handler for web widgets."""

    channel_name = "web"

    def __init__(self, agent: Any = None):
        """
        Initialize web chat handler.

        Args:
            agent: Optional agent to handle messages
        """
        super().__init__()
        self._agent = agent

        # Simple in-memory session storage
        # In production, use Redis or similar
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._session_ttl = timedelta(hours=24)

    def _cleanup_sessions(self) -> None:
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            sid for sid, data in self._sessions.items()
            if now - data.get("last_activity", now) > self._session_ttl
        ]
        for sid in expired:
            del self._sessions[sid]

    def _get_or_create_session(self, session_id: Optional[str]) -> str:
        """
        Get existing session or create new one.

        Args:
            session_id: Optional session ID

        Returns:
            Session ID
        """
        self._cleanup_sessions()

        if session_id and session_id in self._sessions:
            # Update last activity
            self._sessions[session_id]["last_activity"] = datetime.utcnow()
            return session_id

        # Create new session
        new_session_id = str(uuid.uuid4())
        self._sessions[new_session_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "history": [],
        }
        return new_session_id

    async def send_message(self, session_id: str, text: str, **kwargs) -> bool:
        """
        Send message (store in session history).

        Args:
            session_id: Session ID
            text: Message text
            **kwargs: Additional options

        Returns:
            True if successful
        """
        if session_id not in self._sessions:
            logger.warning(f"[WebChat] Session not found: {session_id}")
            return False

        self._sessions[session_id]["history"].append({
            "role": "assistant",
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return True

    async def handle_message(
        self,
        session_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Handle incoming message from web client.

        Args:
            session_id: Session ID
            text: Message text
            metadata: Optional metadata

        Returns:
            Response text
        """
        metadata = metadata or {}

        # Get or create session
        session_id = self._get_or_create_session(session_id)

        # Store user message
        if session_id in self._sessions:
            self._sessions[session_id]["history"].append({
                "role": "user",
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
            })

            # Add session history to metadata
            metadata["session_history"] = self._sessions[session_id]["history"]

        # Route to agent
        if self._agent and hasattr(self._agent, "execute"):
            try:
                result = self._agent.execute(text, metadata)
                if hasattr(result, "__await__"):
                    result = await result
                return result
            except Exception as e:
                logger.error(f"[WebChat] Agent execution error: {e}")
                return "Sorry, I encountered an error processing your message."
        else:
            return "Chat handler not configured with an agent."


def create_web_chat_app(handler: WebChatHandler) -> FastAPI:
    """
    Create FastAPI app with /chat endpoint.

    Args:
        handler: WebChatHandler instance

    Returns:
        FastAPI application

    Example:
        ```python
        handler = WebChatHandler(agent=my_agent)
        app = create_web_chat_app(handler)

        # Run with uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
        ```
    """
    app = FastAPI(title="ANO Web Chat", version="1.0.0")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "ok"}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(message: ChatMessage):
        """
        Process chat message.

        Args:
            message: ChatMessage with session_id and message text

        Returns:
            ChatResponse with session_id, response, and timestamp
        """
        if not message.message or not message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        try:
            # Get or create session
            session_id = handler._get_or_create_session(message.session_id)

            # Handle message
            response = await handler.handle_message(session_id, message.message)

            # Store response
            await handler.send_message(session_id, response)

            return ChatResponse(
                session_id=session_id,
                response=response,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"[WebChat] Chat error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/session/{session_id}")
    async def get_session(session_id: str):
        """
        Get session history.

        Args:
            session_id: Session ID

        Returns:
            Session data including history
        """
        if session_id not in handler._sessions:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "session_id": session_id,
            "created_at": handler._sessions[session_id]["created_at"].isoformat(),
            "last_activity": handler._sessions[session_id]["last_activity"].isoformat(),
            "history": handler._sessions[session_id]["history"],
        }

    return app
