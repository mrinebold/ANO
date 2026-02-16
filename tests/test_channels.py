"""Tests for channels module — BaseChannel, CLI REPL, Telegram auth/commands."""

from __future__ import annotations

import pytest

from channels.base_channel import BaseChannel
from channels.cli.repl import CLIRepl
from channels.telegram.auth import TelegramAuth, TierConfig
from channels.telegram.commands import CommandRegistry


# --- BaseChannel ---


class TestBaseChannel:
    def test_abstract(self):
        """BaseChannel cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseChannel()

    def test_set_agent(self):
        """Concrete channels can set agents."""
        repl = CLIRepl()
        agent = object()
        repl.set_agent(agent)
        assert repl._agent is agent


# --- CLIRepl ---


class TestCLIRepl:
    def test_init(self):
        repl = CLIRepl()
        assert repl.channel_name == "cli"
        assert repl._agent is None
        assert repl.prompt == "> "

    def test_init_with_agent(self):
        agent = object()
        repl = CLIRepl(agent=agent, prompt="$ ")
        assert repl._agent is agent
        assert repl.prompt == "$ "

    @pytest.mark.asyncio
    async def test_send_message(self, capsys):
        repl = CLIRepl()
        result = await repl.send_message("user", "Hello!")
        assert result is True
        captured = capsys.readouterr()
        assert "Hello!" in captured.out

    @pytest.mark.asyncio
    async def test_handle_message_no_agent(self):
        repl = CLIRepl()
        response = await repl.handle_message("user", "test")
        assert "not configured" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_message_with_agent(self):
        class MockAgent:
            async def execute(self, text, metadata):
                return f"Response: {text}"

        repl = CLIRepl(agent=MockAgent())
        response = await repl.handle_message("user", "hello")
        assert response == "Response: hello"

    def test_stop(self):
        repl = CLIRepl()
        repl._running = True
        repl.stop()
        assert repl._running is False


# --- CommandRegistry ---


class TestCommandRegistry:
    def test_register_and_get(self):
        registry = CommandRegistry()
        handler = lambda: "test"
        registry.register("start", handler, "Start the bot")
        assert registry.get_handler("start") is handler

    def test_get_handler_not_found(self):
        registry = CommandRegistry()
        assert registry.get_handler("nonexistent") is None

    def test_list_commands(self):
        registry = CommandRegistry()
        registry.register("start", lambda: None, "Start")
        registry.register("help", lambda: None, "Help")
        commands = registry.list_commands()
        assert len(commands) == 2
        assert commands[0]["command"] == "start"

    def test_parse_command(self):
        assert CommandRegistry.parse_command("/start abc123") == ("start", "abc123")
        assert CommandRegistry.parse_command("/help") == ("help", "")
        assert CommandRegistry.parse_command("hello world") == (None, "hello world")

    def test_parse_command_with_bot_mention(self):
        assert CommandRegistry.parse_command("/start@botname args") == ("start", "args")

    def test_parse_command_case_insensitive(self):
        cmd, args = CommandRegistry.parse_command("/START")
        assert cmd == "start"

    def test_register_with_tier(self):
        registry = CommandRegistry()
        registry.register("export", lambda: None, "Export data", required_tier="premium")
        cmd_data = registry.commands["export"]
        assert cmd_data["required_tier"] == "premium"


# --- TelegramAuth ---


class TestTelegramAuth:
    def test_default_tiers(self):
        auth = TelegramAuth()
        assert len(auth.tiers) == 3
        default = auth.get_default_tier()
        assert default == "free"

    def test_custom_tiers(self):
        tiers = [
            TierConfig("basic", 0, ["read"]),
            TierConfig("admin", 10, ["read", "write", "delete"]),
        ]
        auth = TelegramAuth(tiers=tiers)
        assert len(auth.tiers) == 2

    def test_check_access_by_feature(self):
        auth = TelegramAuth()
        assert auth.check_access("free", "help") is True
        assert auth.check_access("free", "export") is False

    def test_check_access_by_tier_level(self):
        auth = TelegramAuth()
        # Premium (level 2) can access basic-tier features (level 1)
        assert auth.check_access("premium", "basic") is True
        # Free (level 0) cannot access premium-tier features (level 2)
        assert auth.check_access("free", "premium") is False

    def test_check_access_unknown_user_tier(self):
        auth = TelegramAuth()
        assert auth.check_access("unknown_tier", "help") is False

    def test_tier_config(self):
        config = TierConfig("test", 5, ["feature1", "feature2"])
        assert config.name == "test"
        assert config.level == 5
        assert len(config.features) == 2
