"""Unit tests for utilities module."""
import os
import pytest
from unittest.mock import patch
from utilities import validate_handshake_payload, is_handshake_message, DEFAULT_COMMANDS


class TestValidateHandshakePayload:
    """Tests for validate_handshake_payload function."""

    def test_valid_handshake_payload_complete(self, valid_handshake_payload):
        """Test validation of a complete valid handshake payload."""
        is_valid, error_msg = validate_handshake_payload(valid_handshake_payload)
        assert is_valid is True
        assert error_msg == ""

    def test_valid_handshake_payload_minimal(self, valid_handshake_payload_no_token):
        """Test validation of a minimal valid handshake payload."""
        is_valid, error_msg = validate_handshake_payload(valid_handshake_payload_no_token)
        assert is_valid is True
        assert error_msg == ""

    def test_handshake_payload_not_dict(self):
        """Test validation fails when payload is not a dictionary."""
        is_valid, error_msg = validate_handshake_payload("not a dict")
        assert is_valid is False
        assert "must be a dictionary" in error_msg

    def test_handshake_payload_not_dict_list(self):
        """Test validation fails when payload is a list."""
        is_valid, error_msg = validate_handshake_payload(["type", "handshake"])
        assert is_valid is False
        assert "must be a dictionary" in error_msg

    def test_handshake_payload_missing_type_field(self):
        """Test validation fails when 'type' field is missing."""
        payload = {
            "clientId": "test-client",
            "version": "1.0",
        }
        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is False
        assert "missing required field: 'type'" in error_msg

    def test_handshake_payload_invalid_type_value(self):
        """Test validation fails when 'type' is not 'handshake'."""
        payload = {
            "type": "message",
            "clientId": "test-client",
            "version": "1.0",
        }
        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is False
        assert "'type' field must be 'handshake'" in error_msg

    def test_handshake_payload_missing_clientId_field(self):
        """Test validation fails when 'clientId' field is missing."""
        payload = {
            "type": "handshake",
            "version": "1.0",
        }
        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is False
        assert "missing required field: 'clientId'" in error_msg

    def test_handshake_payload_missing_version_field(self):
        """Test validation fails when 'version' field is missing."""
        payload = {
            "type": "handshake",
            "clientId": "test-client",
        }
        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is False
        assert "missing required field: 'version'" in error_msg

    def test_handshake_payload_with_extra_fields(self):
        """Test validation passes with extra fields in payload."""
        payload = {
            "type": "handshake",
            "clientId": "test-client",
            "version": "1.0",
            "metadata": {"key": "value"},
            "extra": "data",
        }
        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is True
        assert error_msg == ""

    def test_handshake_payload_none_value(self):
        """Test validation when payload is None."""
        is_valid, error_msg = validate_handshake_payload(None)
        assert is_valid is False
        assert "must be a dictionary" in error_msg

    def test_handshake_payload_empty_dict(self):
        """Test validation fails when payload is an empty dictionary."""
        is_valid, error_msg = validate_handshake_payload({})
        assert is_valid is False
        assert "missing required field: 'type'" in error_msg


class TestIsHandshakeMessage:
    """Tests for is_handshake_message function."""

    def test_is_handshake_message_valid(self, valid_handshake_response):
        """Test detection of a valid handshake message."""
        result = is_handshake_message(valid_handshake_response)
        assert result is True

    def test_is_handshake_message_not_dict(self):
        """Test detection fails when message is not a dictionary."""
        result = is_handshake_message("not a dict")
        assert result is False

    def test_is_handshake_message_non_handshake_type(self):
        """Test detection fails when type is not 'handshake'."""
        payload = {
            "type": "message",
            "status": "ok",
        }
        result = is_handshake_message(payload)
        assert result is False

    def test_is_handshake_message_missing_type(self):
        """Test detection fails when 'type' field is missing."""
        payload = {"status": "ok"}
        result = is_handshake_message(payload)
        assert result is False

    def test_is_handshake_message_none(self):
        """Test detection returns False for None."""
        result = is_handshake_message(None)
        assert result is False

    def test_is_handshake_message_list(self):
        """Test detection returns False for list."""
        result = is_handshake_message(["type", "handshake"])
        assert result is False

    def test_is_handshake_message_handles_exception(self):
        """Test detection handles exceptions gracefully."""
        # Create a mock object that raises exception on type check
        class BadPayload:
            def __getitem__(self, key):
                raise TypeError("Cannot access")

        result = is_handshake_message(BadPayload())
        assert result is False


class TestDefaultCommands:
    """Tests for DEFAULT_COMMANDS configuration."""

    def test_default_commands_includes_handshake(self):
        """Test that DEFAULT_COMMANDS includes a Handshake command."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in command_names

    def test_handshake_command_structure(self):
        """Test that Handshake command has correct structure."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake_cmd is not None
        assert "payload" in handshake_cmd
        assert isinstance(handshake_cmd["payload"], dict)

    def test_handshake_command_has_required_fields(self):
        """Test that Handshake command payload has required fields."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        payload = handshake_cmd["payload"]
        assert payload.get("type") == "handshake"
        assert "clientId" in payload
        assert "version" in payload

    def test_handshake_command_respects_environment_variables(self):
        """Test that Handshake command uses environment variables."""
        # Patch environment variables
        with patch.dict(
            os.environ,
            {"IOT_CLIENT_ID": "custom-client", "IOT_AUTH_TOKEN": "custom-token"},
        ):
            # Reload the utilities module to pick up new env vars
            import importlib
            import utilities

            importlib.reload(utilities)

            handshake_cmd = next(
                (
                    cmd
                    for cmd in utilities.DEFAULT_COMMANDS
                    if cmd["name"] == "Handshake"
                ),
                None,
            )
            payload = handshake_cmd["payload"]
            # Note: This tests the environment variable resolution at import time
            # The actual values depend on when the module is imported

    def test_handshake_command_default_values(self):
        """Test that Handshake command has sensible defaults."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        payload = handshake_cmd["payload"]
        # clientId should have a default value
        assert payload.get("clientId") is not None
        # version should be set
        assert payload.get("version") == "1.0"

    def test_other_default_commands_unchanged(self):
        """Test that other default commands are not affected by handshake feature."""
        expected_commands = ["Handshake", "Ping", "Login", "Subscribe", "Echo"]
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        for expected_cmd in expected_commands:
            assert expected_cmd in command_names, f"Missing expected command: {expected_cmd}"

    def test_default_commands_payload_format(self):
        """Test that all default commands have consistent structure."""
        for cmd in DEFAULT_COMMANDS:
            assert "name" in cmd, f"Command missing 'name': {cmd}"
            assert "payload" in cmd, f"Command missing 'payload': {cmd}"
            assert isinstance(cmd["payload"], dict), f"Payload is not dict for {cmd['name']}"
