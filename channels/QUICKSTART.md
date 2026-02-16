# ANO Channels - Quick Start

## 30-Second Start

### Telegram Bot
```python
from channels.telegram import TelegramConfig, TelegramBotService, create_webhook_app

config = TelegramConfig.from_env()  # Needs TELEGRAM_BOT_TOKEN
bot = TelegramBotService(config, agent=my_agent)
app = create_webhook_app(bot, config)

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Web Chat
```python
from channels.web import WebChatHandler, create_web_chat_app

handler = WebChatHandler(agent=my_agent)
app = create_web_chat_app(handler)

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

### CLI REPL
```python
from channels.cli import CLIRepl
import asyncio

repl = CLIRepl(agent=my_agent)
asyncio.run(repl.run())
```

## Agent Contract

Your agent must implement:
```python
class MyAgent:
    async def execute(self, text: str, metadata: dict) -> str:
        # Process input, return response
        return f"Response to: {text}"
```

Or synchronous:
```python
class MyAgent:
    def execute(self, text: str, metadata: dict) -> str:
        return f"Response to: {text}"
```

## Environment Variables

### Telegram
```bash
TELEGRAM_BOT_TOKEN=your-bot-token          # Required
TELEGRAM_WEBHOOK_SECRET=your-secret        # Recommended
TELEGRAM_WEBHOOK_URL=https://your.site/webhook  # Optional
TELEGRAM_RATE_LIMIT=10                     # Optional (messages/min)
```

## Complete Examples

See:
- `examples/telegram_bot.py` - Full Telegram bot with commands
- `examples/web_chat.py` - Full web chat with CORS
- `examples/cli_repl.py` - Full CLI REPL with state

## Common Tasks

### Add Telegram Command
```python
def handle_help(sender_id: str, args: str, metadata: dict) -> str:
    return "Help text here"

bot.register_command("help", handle_help, "Show help", "free")
```

### Tier-Based Access
```python
from channels.telegram.auth import TelegramAuth, TierConfig

tiers = [
    TierConfig("free", 0, ["help", "start"]),
    TierConfig("pro", 1, ["help", "start", "export"]),
]

auth = TelegramAuth(tiers=tiers)
bot = TelegramBotService(config, agent=my_agent, auth=auth)

bot.register_command("export", export_handler, required_tier="pro")
```

### Custom Message Handler
```python
async def my_handler(text: str, metadata: dict) -> str:
    return f"Custom: {text}"

bot.set_message_handler(my_handler)
```

### Web Chat with CORS
```python
from fastapi.middleware.cors import CORSMiddleware

app = create_web_chat_app(handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["POST", "GET"],
)
```

## Testing

```bash
# Install dependencies
pip install httpx fastapi pydantic uvicorn

# Test imports
python3 -c "from channels import *; print('✅ OK')"

# Run examples
python3 examples/cli_repl.py           # No setup needed
python3 examples/web_chat.py           # Runs on :8000
TELEGRAM_BOT_TOKEN=xxx python3 examples/telegram_bot.py  # Needs token
```

## API Endpoints

### Telegram Webhook
- `POST /webhook` - Telegram updates
- `GET /health` - Health check

### Web Chat
- `POST /chat` - Send message
  - Request: `{"session_id": "optional", "message": "text"}`
  - Response: `{"session_id": "uuid", "response": "text", "timestamp": "iso"}`
- `GET /session/{session_id}` - Get history
- `GET /health` - Health check

## Production Checklist

### Telegram
- [ ] Set `TELEGRAM_BOT_TOKEN`
- [ ] Set `TELEGRAM_WEBHOOK_SECRET`
- [ ] Use HTTPS for webhook URL
- [ ] Call `bot.set_webhook(url)` after deployment
- [ ] Monitor rate limits

### Web Chat
- [ ] Configure CORS properly
- [ ] Add authentication
- [ ] Replace in-memory sessions with Redis
- [ ] Add rate limiting

### CLI
- [ ] Local use only (not for production)

## Need Help?

1. Read `README.md` - Complete documentation
2. Check `examples/` - Three complete examples
3. See `IMPLEMENTATION.md` - Architecture details

## Architecture

```
User Input → Channel → Agent → Response → Channel → User Output

Channel Types:
- Telegram: Bot API + Webhook
- Web: REST API + Session Management
- CLI: REPL + Stdin/Stdout

All channels implement BaseChannel interface.
```

---

**Quick Test**: `python3 examples/cli_repl.py` (works without any setup!)
