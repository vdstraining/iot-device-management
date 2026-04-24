"""
Tests for utilities.py
Covers: DEFAULT_COMMANDS structure (Handshake entry + existing commands), AppLogger.
"""
import pytest
from utilities import DEFAULT_COMMANDS, AppLogger


class TestDefaultCommandsHandshake:
    def test_handshake_is_first_command(self):
        assert DEFAULT_COMMANDS[0]["name"] == "Handshake"

    def test_handshake_payload_has_type_field(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert payload["type"] == "Handshake"

    def test_handshake_payload_has_action_field(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert payload["action"] == "handshake"

    def test_handshake_client_id_is_dynamic_placeholder(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert payload["clientId"] == "{{clientId}}"

    def test_handshake_token_is_dynamic_placeholder(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert payload["token"] == "{{token}}"

    def test_handshake_capabilities_is_a_list(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert isinstance(payload["capabilities"], list)
        assert len(payload["capabilities"]) > 0

    def test_handshake_session_is_a_dict(self):
        payload = DEFAULT_COMMANDS[0]["payload"]
        assert isinstance(payload["session"], dict)


class TestDefaultCommandsExistingEntries:
    """Existing commands must remain present and unaffected by the handshake addition."""

    def _command_by_name(self, name):
        return next((c for c in DEFAULT_COMMANDS if c["name"] == name), None)

    def test_ping_command_exists(self):
        assert self._command_by_name("Ping") is not None

    def test_subscribe_command_exists(self):
        assert self._command_by_name("Subscribe") is not None

    def test_ping_payload_unchanged(self):
        cmd = self._command_by_name("Ping")
        assert cmd["payload"]["action"] == "ping"

    def test_subscribe_payload_unchanged(self):
        cmd = self._command_by_name("Subscribe")
        assert cmd["payload"]["action"] == "subscribe"
        assert cmd["payload"]["channel"] == "events"

    def test_all_commands_have_name_and_payload(self):
        for cmd in DEFAULT_COMMANDS:
            assert "name" in cmd, f"Command missing 'name': {cmd}"
            assert "payload" in cmd, f"Command missing 'payload': {cmd}"


class TestAppLogger:
    def test_log_calls_callback(self):
        received = []
        logger = AppLogger(received.append)
        logger.log("test message")
        assert len(received) == 1

    def test_log_includes_original_message(self):
        received = []
        logger = AppLogger(received.append)
        logger.log("hello world")
        assert "hello world" in received[0]

    def test_log_includes_timestamp_prefix(self):
        received = []
        logger = AppLogger(received.append)
        logger.log("ping")
        # Timestamps are enclosed in brackets: [YYYY-MM-DD HH:MM:SS]
        assert received[0].startswith("[")

    def test_log_multiple_messages_each_reaches_callback(self):
        received = []
        logger = AppLogger(received.append)
        logger.log("first")
        logger.log("second")
        assert len(received) == 2
        assert "first" in received[0]
        assert "second" in received[1]
