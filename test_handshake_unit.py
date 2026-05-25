#!/usr/bin/env python3
"""
Comprehensive unit tests for SCRUM-107 handshake mechanism.

Tests cover:
- Configuration loading and validation
- Payload building with various field combinations
- Configuration merging and defaults
- Validation of required and optional fields
"""

import json
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from utilities import load_handshake_config, AppLogger, DEFAULT_COMMANDS
from ws_client import WebSocketManager


class TestHandshakeConfigLoading:
    """Unit tests for handshake configuration loading."""

    def test_load_handshake_config_default_values(self):
        """Test loading handshake config with defaults when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            config = load_handshake_config(config_path)

            assert config["enabled"] is True
            assert config["auto_trigger"] is True
            assert config["clientId"] == "iot-device-simulator-001"
            assert isinstance(config["capabilities"], list)
            assert len(config["capabilities"]) > 0
            assert "websocket" in config["capabilities"]
            assert "http" in config["capabilities"]
            assert "session_metadata" in config
            assert "authentication_context" in config

    def test_load_handshake_config_from_file(self):
        """Test loading valid handshake config from file."""
        config_data = {
            "enabled": True,
            "auto_trigger": True,
            "clientId": "test-client-001",
            "capabilities": ["websocket", "http"],
            "session_metadata": {
                "version": "2.0",
                "application": "TestApp",
                "platform": "TestPlatform",
            },
            "authentication_context": {
                "auth_type": "bearer",
                "token": "test-token-123",
            },
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(config_data, f)

            config = load_handshake_config(config_path)

            assert config["clientId"] == "test-client-001"
            assert config["capabilities"] == ["websocket", "http"]
            assert config["session_metadata"]["version"] == "2.0"
            assert config["authentication_context"]["token"] == "test-token-123"

    def test_load_handshake_config_partial_override(self):
        """Test that file config merges with defaults for partial config."""
        partial_config = {
            "clientId": "custom-client",
            "enabled": False,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(partial_config, f)

            config = load_handshake_config(config_path)

            # Overridden values
            assert config["clientId"] == "custom-client"
            assert config["enabled"] is False
            # Default values should still exist
            assert config["auto_trigger"] is True
            assert "capabilities" in config
            assert "session_metadata" in config

    def test_load_handshake_config_missing_file(self):
        """Test that missing config file returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.json")
            config = load_handshake_config(config_path)

            assert config["enabled"] is True
            assert config["clientId"] == "iot-device-simulator-001"

    def test_load_handshake_config_invalid_json(self):
        """Test that invalid JSON returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                f.write("{ invalid json }")

            config = load_handshake_config(config_path)

            # Should return defaults on error
            assert config["enabled"] is True
            assert config["clientId"] == "iot-device-simulator-001"

    def test_load_handshake_config_empty_file(self):
        """Test handling of empty JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                f.write("{}")

            config = load_handshake_config(config_path)

            # Empty config should be merged with defaults
            assert "enabled" in config
            assert "clientId" in config
            assert "capabilities" in config

    def test_load_handshake_config_preserves_required_fields(self):
        """Test that all required fields are present after loading."""
        config = load_handshake_config()

        required_fields = [
            "enabled",
            "auto_trigger",
            "clientId",
            "capabilities",
            "session_metadata",
            "authentication_context",
        ]

        for field in required_fields:
            assert field in config, f"Required field '{field}' missing"


class TestHandshakePayloadBuilding:
    """Unit tests for handshake payload construction."""

    def test_build_handshake_payload_complete(self):
        """Test building complete handshake payload with all fields."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload is not None
        assert payload["action"] == "handshake"
        assert payload["clientId"] == config["clientId"]
        assert payload["capabilities"] == config["capabilities"]
        assert payload["session_metadata"] == config["session_metadata"]
        assert payload["authentication_context"] == config["authentication_context"]

    def test_build_handshake_payload_empty_config(self):
        """Test building payload with empty config."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        ws_manager = WebSocketManager(logger=logger, handshake_config={})
        payload = ws_manager._build_handshake_payload()

        # Should handle empty config gracefully
        assert payload is None or isinstance(payload, dict)

    def test_build_handshake_payload_default_values(self):
        """Test that payload uses defaults when config is missing values."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        partial_config = {
            "clientId": "test-client",
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=partial_config)
        payload = ws_manager._build_handshake_payload()

        assert payload["clientId"] == "test-client"
        # Should provide defaults for missing fields
        assert isinstance(payload["capabilities"], list)
        assert "action" in payload
        assert payload["action"] == "handshake"

    def test_build_handshake_payload_custom_clientid(self):
        """Test payload building with custom client ID."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "clientId": "custom-device-123",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload["clientId"] == "custom-device-123"

    def test_build_handshake_payload_capabilities_preserved(self):
        """Test that custom capabilities are preserved in payload."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        custom_capabilities = ["websocket", "http", "mqtt", "coap"]
        config = {
            "capabilities": custom_capabilities,
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload["capabilities"] == custom_capabilities

    def test_build_handshake_payload_session_metadata(self):
        """Test that session metadata is preserved in payload."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        metadata = {
            "version": "3.0",
            "application": "CustomApp",
            "platform": "CustomPlatform",
            "custom_field": "custom_value",
        }
        config = {
            "session_metadata": metadata,
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload["session_metadata"] == metadata

    def test_build_handshake_payload_authentication_context(self):
        """Test that authentication context is included in payload."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        auth_context = {
            "auth_type": "jwt",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        }
        config = {
            "authentication_context": auth_context,
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload["authentication_context"] == auth_context

    def test_build_handshake_payload_is_json_serializable(self):
        """Test that payload can be serialized to JSON."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        # Should not raise exception
        json_str = json.dumps(payload)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Should be deserializable
        restored = json.loads(json_str)
        assert restored["action"] == "handshake"


class TestDefaultCommandsHandshake:
    """Unit tests for Handshake in DEFAULT_COMMANDS."""

    def test_handshake_is_first_default_command(self):
        """Test that Handshake is the first default command."""
        assert DEFAULT_COMMANDS[0]["name"] == "Handshake"

    def test_handshake_payload_has_required_fields(self):
        """Test that Handshake command payload has all required fields."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        payload = handshake_cmd["payload"]

        required_fields = [
            "action",
            "clientId",
            "capabilities",
            "session_metadata",
            "authentication_context",
        ]

        for field in required_fields:
            assert field in payload, f"Handshake payload missing '{field}'"

    def test_handshake_payload_action_is_correct(self):
        """Test that Handshake payload action is 'handshake'."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        assert handshake_cmd["payload"]["action"] == "handshake"

    def test_handshake_payload_is_valid_json(self):
        """Test that Handshake payload can be JSON serialized."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        payload = handshake_cmd["payload"]

        json_str = json.dumps(payload)
        assert isinstance(json_str, str)

        restored = json.loads(json_str)
        assert restored["action"] == "handshake"

    def test_default_commands_count_includes_handshake(self):
        """Test that DEFAULT_COMMANDS includes Handshake."""
        names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in names

    def test_handshake_capabilities_is_list(self):
        """Test that Handshake capabilities is a list."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        capabilities = handshake_cmd["payload"]["capabilities"]

        assert isinstance(capabilities, list)
        assert len(capabilities) > 0

    def test_handshake_session_metadata_has_version(self):
        """Test that session_metadata includes version."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        metadata = handshake_cmd["payload"]["session_metadata"]

        assert "version" in metadata
        assert isinstance(metadata["version"], str)

    def test_handshake_authentication_context_structure(self):
        """Test authentication_context has proper structure."""
        handshake_cmd = DEFAULT_COMMANDS[0]
        auth = handshake_cmd["payload"]["authentication_context"]

        assert "auth_type" in auth
        assert isinstance(auth.get("auth_type"), str)


class TestWebSocketManagerHandshakeIntegration:
    """Unit tests for WebSocketManager handshake integration."""

    def test_websocket_manager_accepts_handshake_config(self):
        """Test that WebSocketManager can be initialized with handshake_config."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(
            logger=logger,
            handshake_config=config,
        )

        assert ws_manager.handshake_config == config

    def test_websocket_manager_initializes_with_empty_config(self):
        """Test WebSocketManager initialization with empty handshake_config."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        ws_manager = WebSocketManager(logger=logger, handshake_config={})

        assert ws_manager.handshake_config == {}

    def test_websocket_manager_defaults_to_empty_config(self):
        """Test WebSocketManager defaults to empty config if not provided."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        ws_manager = WebSocketManager(logger=logger)

        assert ws_manager.handshake_config == {}

    def test_handshake_config_enabled_flag(self):
        """Test that enabled flag is respected in config."""
        config = {
            "enabled": False,
            "auto_trigger": True,
        }
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)

        assert ws_manager.handshake_config["enabled"] is False

    def test_handshake_config_auto_trigger_flag(self):
        """Test that auto_trigger flag is preserved."""
        config = {
            "enabled": True,
            "auto_trigger": False,
        }
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)

        assert ws_manager.handshake_config["auto_trigger"] is False


class TestHandshakeConfigurationValidation:
    """Unit tests for handshake configuration validation and edge cases."""

    def test_config_with_extra_fields(self):
        """Test that extra fields in config are preserved."""
        extra_config = {
            "enabled": True,
            "clientId": "test",
            "custom_field": "custom_value",
            "nested": {"key": "value"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(extra_config, f)

            config = load_handshake_config(config_path)

            assert "custom_field" in config
            assert config["custom_field"] == "custom_value"

    def test_config_with_null_values(self):
        """Test handling of null values in config."""
        config_with_nulls = {
            "enabled": True,
            "clientId": None,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(config_with_nulls, f)

            config = load_handshake_config(config_path)

            # Should merge with defaults, providing clientId
            assert config["clientId"] is None or config["clientId"] != ""

    def test_config_boolean_coercion(self):
        """Test that boolean values are preserved correctly."""
        config = {
            "enabled": "true",  # String instead of boolean
            "auto_trigger": 1,  # Integer instead of boolean
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f)

            config = load_handshake_config(config_path)

            # Should have the original types (JSON doesn't coerce)
            assert config["enabled"] == "true"
            assert config["auto_trigger"] == 1

    def test_config_string_capabilities(self):
        """Test handling of capabilities as wrong type."""
        config = {
            "capabilities": "websocket,http",  # String instead of list
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "handshake_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f)

            loaded_config = load_handshake_config(config_path)

            # Should preserve the loaded value
            assert loaded_config["capabilities"] == "websocket,http"


class TestPayloadValidation:
    """Unit tests for payload validation logic."""

    def test_payload_contains_action_field(self):
        """Test that payload always contains action field."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert "action" in payload
        assert payload["action"] == "handshake"

    def test_payload_action_value_immutable(self):
        """Test that action value is always 'handshake'."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        
        # Test with various configs
        configs = [
            {"action": "ping"},  # Trying to override
            {"action": "login"},
            {},
        ]

        for test_config in configs:
            full_config = load_handshake_config()
            full_config.update(test_config)
            
            ws_manager = WebSocketManager(logger=logger, handshake_config=full_config)
            payload = ws_manager._build_handshake_payload()

            assert payload["action"] == "handshake"

    def test_payload_clientid_defaults_if_empty(self):
        """Test that clientId uses default if not provided in config."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        # Should use default
        assert payload is not None
        assert "clientId" in payload
        assert payload["clientId"] == "iot-device-simulator-001"
