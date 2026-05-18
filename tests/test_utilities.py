import pytest
from utilities import DEFAULT_COMMANDS, AppLogger


def test_default_commands_structure():
    assert isinstance(DEFAULT_COMMANDS, list)
    assert any(cmd.get("name") == "Ping" for cmd in DEFAULT_COMMANDS)


def test_app_logger_calls_callback():
    messages = []
    logger = AppLogger(lambda s: messages.append(s))
    logger.log("hello")
    assert len(messages) == 1
    assert "hello" in messages[0]
    assert messages[0].startswith("[")
    assert messages[0].endswith("\n")
