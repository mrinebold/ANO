# Deployment Channels

ANO Foundation provides three built-in channels for deploying agents to end users: **Telegram**, **Web Chat**, and **CLI REPL**. All channels implement the `BaseChannel` interface, making it easy to swap or extend deployment targets.

## Base Channel Interface

Every channel implements this abstract interface:

```python
from channels.base_channel import BaseChannel

class BaseChannel(ABC):
    channel_name: str = "base"

    async def send_message(self, recipient_id: str, text: str, **kwargs) -> bool:
        """Send a message to a recipient. Returns True on success."""
        ...

    async def handle_message(self, sender_id: str, text: str, metadata: dict = None) -> str:
        """Handle an incoming message. Returns response text."""
        ...

    def set_agent(self, agent: Any) -> None:
        """Set the agent that handles messages on this channel."""
        ...
```

## Telegram Bot

The Telegram channel provides a full-featured bot with command routing, rate limiting, tier-based authentication, and webhook support.

### Quick Start

```python
from channels.telegram.config import TelegramConfig
from channels.telegram.bot_service import TelegramBotService
from channels.telegram.webhook import create_webhook_app

# 1. Configure
config = TelegramConfig(
    bot_token="YOUR_BOT_TOKEN",
    webhook_secret="your-secret",
    rate_limit_per_minute=10,
    max_message_length=4096,
    parse_mode="Markdown",
)

# Or load from environment variables
config = TelegramConfig.from_env()

# 2. Create bot service with your agent
bot = TelegramBotService(config, agent=my_agent)

# 3. Register commands
bot.register_command("start", handle_start, "Start the bot", required_tier="free")
bot.register_command("analyze", handle_analyze, "Run analysis", required_tier="basic")

# 4. Create webhook app and deploy
app = create_webhook_app(bot, config)
# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

### Configuration

`TelegramConfig` can be loaded from environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | Yes | — | Telegram Bot API token |
| `TELEGRAM_WEBHOOK_SECRET` | No | `""` | Secret for webhook validation |
| `TELEGRAM_WEBHOOK_URL` | No | `""` | URL where webhook is hosted |
| `TELEGRAM_RATE_LIMIT` | No | `10` | Max messages per user per minute |
| `TELEGRAM_MAX_MESSAGE_LENGTH` | No | `4096` | Max outgoing message length |
| `TELEGRAM_PARSE_MODE` | No | `Markdown` | Default parse mode |

### Command Registry

Register `/command` handlers with tier-based access control:

```python
from channels.telegram.commands import CommandRegistry

registry = CommandRegistry()

# Register a command
registry.register("help", help_handler, "Show help", required_tier="free")
registry.register("export", export_handler, "Export data", required_tier="premium")

# Parse incoming messages
command, args = registry.parse_command("/help")
# ("help", "")

command, args = registry.parse_command("/analyze quarterly revenue")
# ("analyze", "quarterly revenue")

command, args = registry.parse_command("/start@mybotname hello")
# ("start", "hello")  — handles bot mentions

command, args = registry.parse_command("just a regular message")
# (None, "just a regular message")

# List all commands
commands = registry.list_commands()
```

### Tier-Based Authentication

`TelegramAuth` provides hierarchical access control:

```python
from channels.telegram.auth import TelegramAuth, TierConfig

# Use default tiers (free, basic, premium)
auth = TelegramAuth()

# Or define custom tiers
auth = TelegramAuth(tiers=[
    TierConfig("free", 0, ["help", "start", "info"]),
    TierConfig("basic", 1, ["help", "start", "info", "query", "analyze"]),
    TierConfig("premium", 2, ["help", "start", "info", "query", "analyze", "export", "custom"]),
])

# Check access — by feature name
auth.check_access("basic", "analyze")   # True (feature in tier)
auth.check_access("free", "analyze")    # False (feature not in tier)

# Check access — by tier hierarchy
auth.check_access("premium", "basic")   # True (premium level 2 >= basic level 1)
auth.check_access("free", "basic")      # False (free level 0 < basic level 1)

# Get the default (lowest) tier
auth.get_default_tier()  # "free"
```

### Default Tiers

| Tier | Level | Features |
|------|-------|----------|
| `free` | 0 | help, start, info |
| `basic` | 1 | help, start, info, query, analyze |
| `premium` | 2 | help, start, info, query, analyze, export, custom |

### Rate Limiting

Built into `TelegramBotService` — enforces a per-user sliding window (default: 10 messages per minute). When exceeded, the user receives a throttle message.

### Webhook Setup

The webhook endpoint validates the `X-Telegram-Bot-Api-Secret-Token` header and routes updates to the bot service:

```python
from channels.telegram.webhook import create_webhook_app

app = create_webhook_app(bot, config)
# Endpoints:
#   GET  /health   — Health check
#   POST /webhook  — Receives Telegram updates

# Set the webhook with Telegram
await bot.set_webhook("https://your-domain.com/webhook")
```

### Message Handling Flow

```
Telegram Update (POST /webhook)
    │
    ├── Validate webhook secret
    ├── Parse update JSON
    └── bot_service.handle_update(update)
        │
        ├── Extract user info + message text
        ├── Check rate limit
        ├── Parse command
        │   ├── /command → CommandRegistry → handler(sender_id, args, metadata)
        │   │                                   └── Check tier access first
        │   └── plain text → message_handler or agent.execute()
        └── Send response via Telegram API
```

### Custom Message Handler

For non-command messages, you can set a custom handler instead of (or in addition to) an agent:

```python
async def my_handler(text: str, metadata: dict) -> str:
    return f"You said: {text}"

bot.set_message_handler(my_handler)
```

## Web Chat

A FastAPI-based HTTP chat widget with session management.

### Quick Start

```python
from channels.web.chat_widget import WebChatHandler, create_web_chat_app

# Create handler with your agent
handler = WebChatHandler(agent=my_agent)

# Create FastAPI app
app = create_web_chat_app(handler)
# Run with: uvicorn app:app --host 0.0.0.0 --port 8000
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Send a chat message |
| `GET` | `/session/{session_id}` | Get session history |

### Chat Request/Response

```python
# POST /chat
# Request body:
{
    "session_id": "optional-existing-session-id",
    "message": "Hello, how can you help?"
}

# Response:
{
    "session_id": "uuid-assigned-or-existing",
    "response": "I can help with AI governance...",
    "timestamp": "2025-01-15T10:30:00.000000"
}
```

### Session Management

- Sessions are created automatically on first message
- Each session has a 24-hour TTL (expired sessions are cleaned up automatically)
- Session history is stored in memory (use Redis or similar in production)
- History is passed to the agent via `metadata["session_history"]`

```python
# GET /session/{session_id}
# Response:
{
    "session_id": "abc-123",
    "created_at": "2025-01-15T09:00:00.000000",
    "last_activity": "2025-01-15T10:30:00.000000",
    "history": [
        {"role": "user", "text": "Hello", "timestamp": "..."},
        {"role": "assistant", "text": "Hi there!", "timestamp": "..."}
    ]
}
```

## CLI REPL

Interactive command-line REPL for local testing and development.

### Quick Start

```python
from channels.cli.repl import CLIRepl

class MyAgent:
    async def execute(self, text: str, metadata: dict) -> str:
        return f"Analyzing: {text}"

repl = CLIRepl(agent=MyAgent(), prompt="agent> ")
await repl.run()
```

### Built-in Commands

| Command | Action |
|---------|--------|
| `quit`, `exit`, `q` | Exit the REPL |
| `help` | Show available commands |
| `clear` | Clear the terminal screen |

Everything else is routed to the configured agent.

### Example Session

```
ANO Agent REPL
Type 'quit' or 'exit' to stop, 'help' for commands.

agent> What are the key AI governance risks?
Analyzing: What are the key AI governance risks?

agent> help
ANO Agent REPL Commands:
  quit, exit, q - Exit the REPL
  help          - Show this help message
  clear         - Clear the screen

Everything else is sent to the agent.

agent> quit
Goodbye!
```

## Creating a Custom Channel

Subclass `BaseChannel` and implement the two abstract methods:

```python
from channels.base_channel import BaseChannel
from typing import Any, Optional


class SlackChannel(BaseChannel):
    """Example: Deploy an agent to Slack."""

    channel_name = "slack"

    def __init__(self, slack_token: str, agent: Any = None):
        super().__init__()
        self._agent = agent
        self.slack_token = slack_token

    async def send_message(self, channel_id: str, text: str, **kwargs) -> bool:
        """Send a message to a Slack channel."""
        # Use Slack API to send message
        # response = await slack_client.chat_postMessage(channel=channel_id, text=text)
        # return response["ok"]
        return True

    async def handle_message(
        self,
        user_id: str,
        text: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Handle an incoming Slack message."""
        if self._agent and hasattr(self._agent, "execute"):
            result = self._agent.execute(text, metadata or {})
            if hasattr(result, "__await__"):
                result = await result
            return result
        return "Agent not configured."
```

### Channel Checklist

When implementing a custom channel:

1. Subclass `BaseChannel`
2. Set `channel_name` to a unique identifier
3. Implement `send_message()` for outbound messages
4. Implement `handle_message()` for inbound message routing
5. Use `self._agent` (set via `set_agent()`) for agent execution
6. Handle both sync and async agent results (`hasattr(result, "__await__")`)
7. Add error handling and logging
