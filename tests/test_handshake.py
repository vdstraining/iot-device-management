"""
Comprehensive test suite for SCRUM-78: WebSocket Handshake Message Mechanism.

Test Coverage:
- Unit tests for get_handshake_payload() function
- Unit tests for _validate_handshake_payload() method
- Integration tests for handshake auto-send on connection
- UI tests for 6-command layout
- Environment variable configuration tests
- Negative tests for invalid payloads
"""

import json
import os
import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call

import pytest

from utilities import get_handshake_payload, DEFAULT_COMMANDS, AppLogger
from ws_client import WebSocketManager


class TestGetHandshakePayload:
    """Unit tests for get_handshake_payload() function."""

    def test_handshake_payload_structure(self):
        """Test that handshake payload contains all required fields."""
        payload = get_handshake_payload()

        assert isinstance(payload, dict)
        assert "action" in payload
        assert "clientId" in payload
        assert "token" in payload
        assert "timestamp" in payload

    def test_handshake_action_is_handshake(self):
        """Test that action field is 'handshake'."""
        payload = get_handshake_payload()
        assert payload["action"] == "handshake"

    def test_handshake_default_client_id(self):
        """Test default client ID when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            payload = get_handshake_payload()
            assert payload["clientId"] == "iot-device-client"

    def test_handshake_default_token(self):
        """Test default token when environment variable is not set."""
        with patch.dict(os.environ, {}, clear=True):
            payload = get_handshake_payload()
            assert payload["token"] == "demo-token"

    def test_handshake_custom_client_id(self):
        """Test custom client ID from environment variable."""
        custom_id = "custom-client-123"
        with patch.dict(os.environ, {"IOT_CLIENT_ID": custom_id}, clear=True):
            payload = get_handshake_payload()
            assert payload["clientId"] == custom_id

    def test_handshake_custom_token(self):
        """Test custom token from environment variable."""
        custom_token = "custom-token-xyz"
        with patch.dict(os.environ, {"IOT_CLIENT_TOKEN": custom_token}, clear=True):
            payload = get_handshake_payload()
            assert payload["token"] == custom_token

    def test_handshake_both_env_vars(self):
        """Test both environment variables set."""
        env_vars = {
            "IOT_CLIENT_ID": "prod-client",
            "IOT_CLIENT_TOKEN": "prod-token-secure"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            payload = get_handshake_payload()
            assert payload["clientId"] == "prod-client"
            assert payload["token"] == "prod-token-secure"

    def test_handshake_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO format with Z suffix."""
        payload = get_handshake_payload()
        timestamp = payload["timestamp"]

        # Should end with Z
        assert timestamp.endswith("Z")

        # Should be parseable as ISO format (without Z)
        try:
            datetime.fromisoformat(timestamp[:-1])
        except ValueError:
            pytest.fail(f"Timestamp {timestamp} is not in ISO format")

    def test_handshake_timestamp_is_recent(self):
        """Test that timestamp is recent (within last 5 seconds)."""
        before = datetime.now()
        payload = get_handshake_payload()
        after = datetime.now()

        timestamp_str = payload["timestamp"][:-1]  # Remove Z
        timestamp = datetime.fromisoformat(timestamp_str)

        # Timestamp should be within 5 seconds of call time
        assert before <= timestamp <= after + __import__("datetime").timedelta(seconds=5)

    def test_handshake_payload_immutability(self):
        """Test that multiple calls generate independent payloads."""
        payload1 = get_handshake_payload()
        time.sleep(0.01)
        payload2 = get_handshake_payload()

        # Timestamps should be different (different generation times)
        assert payload1["timestamp"] != payload2["timestamp"]

        # Other fields should be the same
        assert payload1["action"] == payload2["action"]
        assert payload1["clientId"] == payload2["clientId"]
        assert payload1["token"] == payload2["token"]


class TestValidateHandshakePayload:
    """Unit tests for _validate_handshake_payload() method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock()
        self.ws_manager = WebSocketManager(logger=self.mock_logger)

    def test_validate_valid_handshake(self):
        """Test validation of valid handshake payload."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "token": "test-token",
            "timestamp": "2026-05-18T10:30:00Z"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is True
        self.mock_logger.log.assert_not_called()

    def test_validate_missing_action(self):
        """Test validation fails when action field is missing."""
        payload = {
            "clientId": "test-client",
            "token": "test-token",
            "timestamp": "2026-05-18T10:30:00Z"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is False
        self.mock_logger.log.assert_called()

    def test_validate_missing_clientid(self):
        """Test validation fails when clientId field is missing."""
        payload = {
            "action": "handshake",
            "token": "test-token",
            "timestamp": "2026-05-18T10:30:00Z"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is False

    def test_validate_missing_token(self):
        """Test validation fails when token field is missing."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "timestamp": "2026-05-18T10:30:00Z"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is False

    def test_validate_missing_timestamp(self):
        """Test validation fails when timestamp field is missing."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "token": "test-token"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is False

    def test_validate_multiple_missing_fields(self):
        """Test validation fails with multiple missing fields."""
        payload = {
            "action": "handshake"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is False
        # Should log missing fields
        call_args = self.mock_logger.log.call_args
        assert "missing fields" in str(call_args).lower()

    def test_validate_non_dict_payload(self):
        """Test validation fails for non-dict payload."""
        assert self.ws_manager._validate_handshake_payload("not a dict") is False
        assert self.ws_manager._validate_handshake_payload([]) is False
        assert self.ws_manager._validate_handshake_payload(None) is False

    def test_validate_logs_error_on_invalid_type(self):
        """Test validation logs error for non-dict payload."""
        self.ws_manager._validate_handshake_payload("invalid")
        self.mock_logger.log.assert_called()
        call_args = str(self.mock_logger.log.call_args)
        assert "not a dict" in call_args.lower()

    def test_validate_extra_fields_allowed(self):
        """Test validation passes with extra fields."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "token": "test-token",
            "timestamp": "2026-05-18T10:30:00Z",
            "extra_field": "extra_value"
        }
        assert self.ws_manager._validate_handshake_payload(payload) is True

    def test_validate_empty_dict(self):
        """Test validation fails for empty dict."""
        assert self.ws_manager._validate_handshake_payload({}) is False


class TestHandshakeAutoSend:
    """Integration tests for handshake auto-send on connection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = MagicMock()
        self.ws_manager = WebSocketManager(logger=self.mock_logger)
        self.mock_ws = MagicMock()

    def test_on_open_sets_connected_true(self):
        """Test that _on_open sets connected to True."""
        self.ws_manager._on_open(self.mock_ws)
        assert self.ws_manager.connected is True

    def test_on_open_logs_connection_message(self):
        """Test that _on_open logs connection message."""
        self.ws_manager._on_open(self.mock_ws)
        assert self.mock_logger.log.call_count >= 1
        call_args = str(self.mock_logger.log.call_args_list[0])
        assert "connected" in call_args.lower()

    def test_on_open_calls_status_change_callback(self):
        """Test that _on_open triggers status change callback."""
        callback = MagicMock()
        ws_manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=callback
        )
        ws_manager._on_open(self.mock_ws)
        callback.assert_called_once_with(True)

    def test_on_open_sends_handshake(self):
        """Test that _on_open sends handshake message."""
        self.ws_manager.ws_app = self.mock_ws
        with patch('ws_client.get_handshake_payload') as mock_handshake:
            mock_handshake.return_value = {
                "action": "handshake",
                "clientId": "test-client",
                "token": "test-token",
                "timestamp": "2026-05-18T10:30:00Z"
            }
            self.ws_manager._on_open(self.mock_ws)
            self.mock_ws.send.assert_called_once()

    def test_on_open_logs_handshake_sent(self):
        """Test that _on_open logs handshake message sent."""
        self.ws_manager.ws_app = self.mock_ws
        with patch('ws_client.get_handshake_payload') as mock_handshake:
            mock_handshake.return_value = {
                "action": "handshake",
                "clientId": "test-client",
                "token": "test-token",
                "timestamp": "2026-05-18T10:30:00Z"
            }
            self.ws_manager._on_open(self.mock_ws)
            # Should log "Sent handshake message"
            log_calls = [str(call) for call in self.mock_logger.log.call_args_list]
            assert any("handshake" in call.lower() for call in log_calls)

    def test_on_open_handles_invalid_handshake(self):
        """Test that _on_open handles invalid handshake gracefully."""
        self.ws_manager.ws_app = self.mock_ws
        with patch('ws_client.get_handshake_payload') as mock_handshake:
            mock_handshake.return_value = {"action": "handshake"}  # Missing required fields
            self.ws_manager._on_open(self.mock_ws)
            # Should not send invalid handshake
            self.mock_ws.send.assert_not_called()
            # Should log validation failure
            log_calls = str(self.mock_logger.log.call_args_list)
            assert "validation" in log_calls.lower()

    def test_on_open_handles_send_exception(self):
        """Test that _on_open handles send exceptions gracefully."""
        self.ws_manager.ws_app = self.mock_ws
        self.mock_ws.send.side_effect = Exception("Send failed")

        with patch('ws_client.get_handshake_payload') as mock_handshake:
            mock_handshake.return_value = {
                "action": "handshake",
                "clientId": "test-client",
                "token": "test-token",
                "timestamp": "2026-05-18T10:30:00Z"
            }
            # Should not raise exception
            self.ws_manager._on_open(self.mock_ws)
            # Should log error
            log_calls = str(self.mock_logger.log.call_args_list)
            assert "failed" in log_calls.lower() or "error" in log_calls.lower()

    def test_handshake_message_is_json(self):
        """Test that handshake message sent is valid JSON."""
        self.ws_manager.ws_app = self.mock_ws
        with patch('ws_client.get_handshake_payload') as mock_handshake:
            mock_handshake.return_value = {
                "action": "handshake",
                "clientId": "test-client",
                "token": "test-token",
                "timestamp": "2026-05-18T10:30:00Z"
            }
            self.ws_manager._on_open(self.mock_ws)

            # Get the data sent to ws_app.send
            sent_data = self.mock_ws.send.call_args[0][0]
            # Verify it's valid JSON
            parsed = json.loads(sent_data)
            assert parsed["action"] == "handshake"
            assert parsed["clientId"] == "test-client"


class TestDefaultCommandsUI:
    """Tests for 6-command layout in UI."""

    def test_default_commands_count(self):
        """Test that there are 6 default commands."""
        assert len(DEFAULT_COMMANDS) == 6

    def test_default_commands_have_required_fields(self):
        """Test that all commands have 'name' field."""
        for cmd in DEFAULT_COMMANDS:
            assert "name" in cmd
            assert isinstance(cmd["name"], str)
            assert len(cmd["name"]) > 0

    def test_handshake_command_exists(self):
        """Test that handshake command exists in DEFAULT_COMMANDS."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        assert handshake_cmd is not None

    def test_handshake_command_payload_is_none(self):
        """Test that handshake command payload is None (dynamic)."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        assert handshake_cmd["payload"] is None

    def test_all_commands_have_unique_names(self):
        """Test that all command names are unique."""
        names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert len(names) == len(set(names))

    def test_command_names_are_non_empty(self):
        """Test that all command names are non-empty strings."""
        for cmd in DEFAULT_COMMANDS:
            assert isinstance(cmd["name"], str)
            assert len(cmd["name"].strip()) > 0

    def test_first_five_commands_have_payloads(self):
        """Test that first 5 commands have payload objects (not None)."""
        for i in range(5):
            assert DEFAULT_COMMANDS[i]["payload"] is not None
            assert isinstance(DEFAULT_COMMANDS[i]["payload"], dict)

    def test_commands_order(self):
        """Test that commands are in expected order."""
        expected_order = ["Ping", "Login", "Subscribe", "Echo", "HTTP POST sample", "Handshake"]
        actual_order = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert actual_order == expected_order


class TestUILoadDefaultCommand:
    """Tests for _load_default_command() with handshake."""

    def test_load_handshake_dynamic_payload_content(self):
        """Test that handshake command index points to handshake."""
        # Find handshake command index
        handshake_index = next(
            (i for i, cmd in enumerate(DEFAULT_COMMANDS) if cmd["name"] == "Handshake"),
            -1
        )
        assert handshake_index == 5  # Should be last (6th) command

        # Verify it's handled as dynamic
        command = DEFAULT_COMMANDS[handshake_index]
        assert command["name"] == "Handshake"
        assert command["payload"] is None

    def test_load_handshake_generates_valid_payload(self):
        """Test that handshake payload generation works correctly."""
        # Simulate what _load_default_command does for handshake
        handshake_index = 5
        command = DEFAULT_COMMANDS[handshake_index]

        if command["name"] == "Handshake":
            payload = get_handshake_payload()
        else:
            payload = command["payload"]

        # Verify it has handshake structure
        assert payload["action"] == "handshake"
        assert "clientId" in payload
        assert "token" in payload
        assert "timestamp" in payload

    def test_non_handshake_command_static_payload(self):
        """Test that non-handshake commands use static payload."""
        # Test ping command (index 0)
        ping_index = 0
        command = DEFAULT_COMMANDS[ping_index]

        if command["name"] == "Handshake":
            payload = get_handshake_payload()
        else:
            payload = command["payload"]

        # Verify it's the static ping payload
        assert payload["action"] == "ping"
        assert "timestamp" in payload


class TestEnvironmentVariableIntegration:
    """Tests for environment variable handling in handshake."""

    def test_handshake_respects_client_id_env(self):
        """Test handshake uses IOT_CLIENT_ID environment variable."""
        test_client_id = "test-iot-device-123"
        with patch.dict(os.environ, {"IOT_CLIENT_ID": test_client_id}):
            payload = get_handshake_payload()
            assert payload["clientId"] == test_client_id

    def test_handshake_respects_token_env(self):
        """Test handshake uses IOT_CLIENT_TOKEN environment variable."""
        test_token = "test-secret-token-xyz"
        with patch.dict(os.environ, {"IOT_CLIENT_TOKEN": test_token}):
            payload = get_handshake_payload()
            assert payload["token"] == test_token

    def test_handshake_with_empty_env_vars(self):
        """Test handshake with empty string environment variables."""
        with patch.dict(os.environ, {"IOT_CLIENT_ID": "", "IOT_CLIENT_TOKEN": ""}, clear=True):
            payload = get_handshake_payload()
            # Should use empty strings, not defaults
            assert payload["clientId"] == ""
            assert payload["token"] == ""

    def test_handshake_env_precedence(self):
        """Test that environment variables take precedence over defaults."""
        env_vars = {
            "IOT_CLIENT_ID": "env-client",
            "IOT_CLIENT_TOKEN": "env-token"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            payload = get_handshake_payload()
            assert payload["clientId"] == "env-client"
            assert payload["token"] == "env-token"


class TestErrorHandling:
    """Tests for error handling in handshake mechanism."""

    def test_invalid_payload_type_list(self):
        """Test validation with list payload."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)
        assert ws_manager._validate_handshake_payload([1, 2, 3]) is False

    def test_invalid_payload_type_string(self):
        """Test validation with string payload."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)
        assert ws_manager._validate_handshake_payload("invalid") is False

    def test_invalid_payload_type_number(self):
        """Test validation with number payload."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)
        assert ws_manager._validate_handshake_payload(42) is False

    def test_payload_with_null_values(self):
        """Test validation with null values in payload."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)
        payload = {
            "action": None,
            "clientId": "test",
            "token": "test",
            "timestamp": "2026-05-18T10:30:00Z"
        }
        # Should still pass validation (fields exist, even if None)
        assert ws_manager._validate_handshake_payload(payload) is True

    def test_payload_with_empty_string_values(self):
        """Test validation with empty string values."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)
        payload = {
            "action": "",
            "clientId": "",
            "token": "",
            "timestamp": ""
        }
        # Should pass validation (fields exist, structure is valid)
        assert ws_manager._validate_handshake_payload(payload) is True

    def test_handshake_json_serialization(self):
        """Test that handshake payload can be JSON serialized."""
        payload = get_handshake_payload()
        # Should not raise exception
        json_str = json.dumps(payload)
        # Should be deserializable
        parsed = json.loads(json_str)
        assert parsed["action"] == "handshake"


class TestAppLogger:
    """Tests for AppLogger functionality."""

    def test_app_logger_logs_with_timestamp(self):
        """Test that AppLogger adds timestamp to logs."""
        logs = []
        logger = AppLogger(logs.append)
        logger.log("Test message")

        assert len(logs) == 1
        log_entry = logs[0]
        assert "Test message" in log_entry
        assert "[" in log_entry  # Timestamp bracket
        assert "]" in log_entry

    def test_app_logger_timestamp_format(self):
        """Test that AppLogger timestamp is in correct format."""
        logs = []
        logger = AppLogger(logs.append)
        logger.log("Test")

        log_entry = logs[0]
        # Extract timestamp part [YYYY-MM-DD HH:MM:SS]
        timestamp_part = log_entry.split("]")[0] + "]"
        assert len(timestamp_part) > 0


class TestWebSocketManagerIntegration:
    """Integration tests for WebSocketManager with handshake."""

    def test_ws_manager_initialization(self):
        """Test WebSocketManager initialization."""
        mock_logger = MagicMock()
        ws_manager = WebSocketManager(logger=mock_logger)

        assert ws_manager.connected is False
        assert ws_manager.ws_app is None
        assert ws_manager.ws_thread is None

    def test_ws_manager_with_callbacks(self):
        """Test WebSocketManager with callback functions."""
        mock_logger = MagicMock()
        on_message = MagicMock()
        on_status = MagicMock()

        ws_manager = WebSocketManager(
            logger=mock_logger,
            on_message=on_message,
            on_status_change=on_status
        )

        assert ws_manager.on_message is on_message
        assert ws_manager.on_status_change is on_status

    def test_set_connected_triggers_callback(self):
        """Test that _set_connected triggers status change callback."""
        mock_logger = MagicMock()
        on_status = MagicMock()

        ws_manager = WebSocketManager(
            logger=mock_logger,
            on_status_change=on_status
        )

        ws_manager._set_connected(True)
        on_status.assert_called_with(True)

        ws_manager._set_connected(False)
        on_status.assert_called_with(False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
