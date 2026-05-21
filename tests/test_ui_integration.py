"""Integration tests for UI handshake functionality."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from utilities import DEFAULT_COMMANDS, is_handshake_message


class TestUIHandshakeIntegration:
    """Tests for UI integration with handshake functionality."""

    def test_default_commands_includes_handshake(self):
        """Test that UI loads Handshake as a default command."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in command_names

    def test_handshake_command_first_in_list(self):
        """Test that Handshake is the first command in the list."""
        assert DEFAULT_COMMANDS[0]["name"] == "Handshake"

    def test_handshake_command_payload_structure(self):
        """Test that Handshake command has proper payload structure."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake_cmd is not None

        payload = handshake_cmd["payload"]
        assert payload.get("type") == "handshake"
        assert "clientId" in payload
        assert "version" in payload
        assert "token" in payload

    def test_handle_ws_message_detects_handshake_response(self):
        """Test that _handle_ws_message can detect handshake responses."""
        handshake_response = {
            "type": "handshake",
            "status": "success",
            "sessionId": "sess-123",
        }
        message_json = json.dumps(handshake_response)

        # Simulate the logic in _handle_ws_message
        try:
            payload = json.loads(message_json)
            is_hs = is_handshake_message(payload)
            assert is_hs is True
        except json.JSONDecodeError:
            pytest.fail("Should be able to parse valid JSON")

    def test_handle_ws_message_ignores_non_handshake_messages(self):
        """Test that _handle_ws_message ignores non-handshake messages."""
        ping_message = {
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z",
        }
        message_json = json.dumps(ping_message)

        # Simulate the logic in _handle_ws_message
        try:
            payload = json.loads(message_json)
            is_hs = is_handshake_message(payload)
            assert is_hs is False
        except json.JSONDecodeError:
            pytest.fail("Should be able to parse valid JSON")

    def test_handle_ws_message_handles_non_json_messages(self):
        """Test that _handle_ws_message handles non-JSON messages gracefully."""
        plain_text_message = "Hello, server!"

        # Simulate the logic in _handle_ws_message
        try:
            payload = json.loads(plain_text_message)
            is_hs = is_handshake_message(payload)
            # If we reach here, the message was JSON
        except json.JSONDecodeError:
            # This is expected for non-JSON messages
            pass


class TestUIHandshakeDetection:
    """Tests for handshake detection in UI message handling."""

    @pytest.mark.parametrize(
        "message,should_detect",
        [
            # Valid handshake responses
            (
                json.dumps({"type": "handshake", "status": "success"}),
                True,
            ),
            (
                json.dumps({"type": "handshake", "status": "error", "error": "auth failed"}),
                True,
            ),
            (
                json.dumps(
                    {
                        "type": "handshake",
                        "sessionId": "xyz",
                        "metadata": {"key": "value"},
                    }
                ),
                True,
            ),
            # Non-handshake messages
            (json.dumps({"type": "message", "data": "hello"}), False),
            (json.dumps({"action": "ping"}), False),
            (json.dumps({"type": "response"}), False),
            # Non-JSON messages
            ("plain text response", False),
            ("", False),
            # Special characters
            ("!@#$%^&*()", False),
        ],
    )
    def test_handshake_message_detection_variations(self, message, should_detect):
        """Test handshake detection with various message formats."""
        try:
            payload = json.loads(message)
            result = is_handshake_message(payload)
        except json.JSONDecodeError:
            result = False

        assert result == should_detect


class TestEnvironmentVariableSupport:
    """Tests for environment variable support in handshake."""

    def test_handshake_command_uses_default_client_id(self):
        """Test that Handshake command has a default clientId."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake_cmd is not None
        assert handshake_cmd["payload"]["clientId"] is not None
        assert len(handshake_cmd["payload"]["clientId"]) > 0

    def test_handshake_command_has_token_field(self):
        """Test that Handshake command includes token field."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert "token" in handshake_cmd["payload"]


class TestUIDefaultCommandsRendering:
    """Tests for UI rendering of default commands section."""

    def test_default_commands_has_name_and_payload(self):
        """Test all default commands have name and payload fields."""
        for cmd in DEFAULT_COMMANDS:
            assert "name" in cmd, f"Command missing 'name' field"
            assert "payload" in cmd, f"Command missing 'payload' field"

    def test_default_commands_payload_is_dict(self):
        """Test all default commands have dict payloads."""
        for cmd in DEFAULT_COMMANDS:
            assert isinstance(
                cmd["payload"], dict
            ), f"Payload for {cmd['name']} is not a dict"

    def test_default_commands_payload_is_json_serializable(self):
        """Test all default commands payloads are JSON serializable."""
        for cmd in DEFAULT_COMMANDS:
            try:
                json.dumps(cmd["payload"])
            except (TypeError, ValueError) as e:
                pytest.fail(f"Command '{cmd['name']}' payload is not JSON serializable: {e}")


class TestHandshakeMessageEdgeCases:
    """Tests for edge cases in handshake message handling."""

    def test_empty_message(self):
        """Test handling of empty JSON object as message."""
        message = "{}"
        try:
            payload = json.loads(message)
            result = is_handshake_message(payload)
            assert result is False
        except json.JSONDecodeError:
            pytest.fail("Should handle empty JSON object")

    def test_message_with_null_type(self):
        """Test handling of message with null type."""
        message = json.dumps({"type": None})
        payload = json.loads(message)
        result = is_handshake_message(payload)
        assert result is False

    def test_message_with_empty_string_type(self):
        """Test handling of message with empty string type."""
        message = json.dumps({"type": ""})
        payload = json.loads(message)
        result = is_handshake_message(payload)
        assert result is False

    def test_case_sensitive_type_field(self):
        """Test that type matching is case-sensitive."""
        message = json.dumps({"type": "Handshake"})  # Uppercase H
        payload = json.loads(message)
        result = is_handshake_message(payload)
        assert result is False  # Should be False because 'Handshake' != 'handshake'

    def test_message_with_extra_fields(self):
        """Test handshake detection with extra fields."""
        message = json.dumps(
            {
                "type": "handshake",
                "status": "success",
                "sessionId": "123",
                "metadata": {"extra": "data"},
                "customField": "value",
            }
        )
        payload = json.loads(message)
        result = is_handshake_message(payload)
        assert result is True
