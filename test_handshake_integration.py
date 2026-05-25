#!/usr/bin/env python3
"""
Comprehensive integration tests for SCRUM-107 handshake mechanism.

Tests cover:
- WebSocket auto-trigger handshake
- Manual handshake trigger
- Handshake logging
- Error scenarios (malformed response, connection errors, timeout)
- Concurrent operations
- Configuration hot-reload
"""

import json
import time
import threading
import tempfile
import os
import pytest
from unittest.mock import Mock, MagicMock, patch, call

from utilities import load_handshake_config, AppLogger, DEFAULT_COMMANDS
from ws_client import WebSocketManager
from ui import AppUI


class MockWebSocket:
    """Mock WebSocket for testing."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_status = None

    def send(self, message):
        """Record sent messages."""
        self.sent_messages.append(message)

    def close(self):
        """Mark as closed."""
        self.closed = True


class TestHandshakeAutoTrigger:
    """Integration tests for automatic handshake trigger."""

    def test_auto_trigger_handshake_on_open(self):
        """Test that handshake is auto-triggered when WebSocket connects."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "enabled": True,
            "auto_trigger": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {"version": "1.0"},
            "authentication_context": {"auth_type": "bearer"},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        # Mock WebSocket
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        # Call _on_open
        ws_manager._on_open(None)

        # Should have sent handshake
        assert len(mock_ws.sent_messages) > 0
        sent_msg = mock_ws.sent_messages[0]
        payload = json.loads(sent_msg)
        assert payload["action"] == "handshake"

    def test_auto_trigger_disabled(self):
        """Test that handshake is NOT auto-triggered when disabled."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "enabled": True,
            "auto_trigger": False,  # Disabled
            "clientId": "test-device",
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        ws_manager._on_open(None)

        # Should NOT have sent handshake
        assert len(mock_ws.sent_messages) == 0

    def test_auto_trigger_when_handshake_disabled(self):
        """Test that auto-trigger respects enabled flag."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "enabled": False,  # Handshake disabled
            "auto_trigger": True,
            "clientId": "test-device",
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        ws_manager._on_open(None)

        # Should NOT trigger (handshake disabled)
        assert len(mock_ws.sent_messages) == 0

    def test_auto_trigger_logs_connection_established(self):
        """Test that connection message is logged."""
        logs = []
        def mock_log(msg):
            logs.append(msg)

        logger = AppLogger(mock_log)
        config = {
            "enabled": True,
            "auto_trigger": True,
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        ws_manager._on_open(None)

        # Should log connection and handshake
        logged_messages = [log for log in logs if "connected" in log.lower()]
        assert len(logged_messages) > 0

    def test_auto_trigger_sets_connected_flag(self):
        """Test that connected flag is set after _on_open."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        ws_manager._on_open(None)

        assert ws_manager.connected is True

    def test_auto_trigger_calls_status_callback(self):
        """Test that on_status_change callback is invoked."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {"enabled": True, "auto_trigger": True}

        status_callback = Mock()
        ws_manager = WebSocketManager(
            logger=logger,
            handshake_config=config,
            on_status_change=status_callback,
        )

        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False

        ws_manager._on_open(None)

        # Callback should be called with True
        status_callback.assert_called_with(True)


class TestManualHandshakeTrigger:
    """Integration tests for manual handshake trigger via send_handshake()."""

    def test_send_handshake_when_connected(self):
        """Test that send_handshake() works when connected."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "enabled": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {"version": "1.0"},
            "authentication_context": {"auth_type": "bearer"},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        assert len(mock_ws.sent_messages) > 0
        payload = json.loads(mock_ws.sent_messages[0])
        assert payload["action"] == "handshake"
        assert payload["clientId"] == "test-device"

    def test_send_handshake_when_not_connected(self):
        """Test that send_handshake() fails gracefully when not connected."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        ws_manager.ws_app = None
        ws_manager.connected = False

        logs = []
        logger.callback = lambda msg: logs.append(msg)

        ws_manager.send_handshake()

        # Should log error about not being connected
        error_logs = [log for log in logs if "not connected" in log.lower()]
        assert len(error_logs) > 0

    def test_send_handshake_disabled(self):
        """Test that send_handshake() respects enabled flag."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {
            "enabled": False,
            "clientId": "test-device",
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Should not send
        assert len(mock_ws.sent_messages) == 0

    def test_send_handshake_logs_sent_message(self):
        """Test that sent handshake is logged."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Should log the handshake message
        handshake_logs = [log for log in logs if "handshake" in log.lower()]
        assert len(handshake_logs) > 0


class TestHandshakeLogging:
    """Integration tests for handshake message logging."""

    def test_handshake_message_logged(self):
        """Test that handshake messages are logged to UI."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Should have logged the message
        assert any("handshake" in log.lower() for log in logs)

    def test_received_handshake_response_logged(self):
        """Test that received handshake responses are logged."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))

        ws_manager = WebSocketManager(logger=logger)

        response = {
            "action": "handshake_ack",
            "status": "success",
            "sessionId": "sess-123",
        }
        response_str = json.dumps(response)

        ws_manager._on_message(None, response_str)

        # Response should be logged
        assert any("handshake_ack" in log or "sessionId" in log for log in logs)

    def test_handshake_error_logged(self):
        """Test that handshake errors are logged."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        ws_manager.connected = False
        ws_manager.ws_app = None

        ws_manager.send_handshake()

        # Error should be logged
        assert any("not connected" in log.lower() for log in logs)

    def test_log_format_includes_timestamp(self):
        """Test that logs include timestamps."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))

        logger.log("Test message")

        # Should have timestamp
        assert len(logs) > 0
        assert "[" in logs[0] and "]" in logs[0]  # Timestamp markers

    def test_log_contains_json_payload(self):
        """Test that log contains JSON payload information."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "device-001",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Log should contain payload info
        logged_text = "\n".join(logs)
        assert "device-001" in logged_text or "clientId" in logged_text


class TestErrorHandling:
    """Integration tests for error scenarios."""

    def test_handle_malformed_json_response(self):
        """Test handling of malformed JSON response."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))

        ws_manager = WebSocketManager(logger=logger)
        mock_message = "{ invalid json }"

        ws_manager._on_message(None, mock_message)

        # Should handle gracefully (log received message)
        assert len(logs) > 0

    def test_handle_websocket_error(self):
        """Test handling of WebSocket errors."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))

        ws_manager = WebSocketManager(logger=logger)
        error = Exception("Connection refused")

        ws_manager._on_error(None, error)

        # Error should be logged
        error_logs = [log for log in logs if "error" in log.lower()]
        assert len(error_logs) > 0

    def test_handle_websocket_close(self):
        """Test handling of WebSocket close."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        ws_manager.connected = True

        ws_manager._on_close(None, 1000, "Normal close")

        # Should log close and set connected to False
        assert ws_manager.connected is False
        close_logs = [log for log in logs if "closed" in log.lower()]
        assert len(close_logs) > 0

    def test_send_handshake_with_missing_ws_app(self):
        """Test send_handshake when ws_app is None."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        ws_manager.ws_app = None
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Should handle gracefully
        assert len(logs) > 0

    def test_send_handshake_exception_handling(self):
        """Test that send_handshake handles exceptions gracefully."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "test",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        
        # Mock ws_app that raises on send
        mock_ws = Mock()
        mock_ws.send.side_effect = Exception("Send failed")
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        ws_manager.send_handshake()

        # Should log error
        error_logs = [log for log in logs if "error" in log.lower()]
        assert len(error_logs) > 0


class TestHandshakeWithDefaultCommands:
    """Integration tests for Handshake as a DEFAULT_COMMAND."""

    def test_handshake_payload_matches_default_command(self):
        """Test that built payload matches DEFAULT_COMMANDS Handshake."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        
        # Get default Handshake command
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake_cmd is not None

        # Build from WebSocketManager
        config = load_handshake_config()
        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        built_payload = ws_manager._build_handshake_payload()

        # Should have same action
        assert built_payload["action"] == handshake_cmd["payload"]["action"]
        assert built_payload["action"] == "handshake"

    def test_default_command_handshake_can_be_selected(self):
        """Test that Handshake can be selected from default commands."""
        # This would be tested in UI, but we can verify the data
        assert DEFAULT_COMMANDS[0]["name"] == "Handshake"
        assert "payload" in DEFAULT_COMMANDS[0]
        assert "action" in DEFAULT_COMMANDS[0]["payload"]

    def test_handshake_default_command_index(self):
        """Test that Handshake is at expected index in DEFAULT_COMMANDS."""
        # First command should be Handshake
        names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert names[0] == "Handshake"

    def test_other_commands_unaffected_by_handshake(self):
        """Test that other default commands are unaffected."""
        expected_commands = ["Handshake", "Ping", "Login", "Subscribe", "Echo", "HTTP POST sample"]
        actual_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]

        for expected in expected_commands:
            assert expected in actual_names


class TestConcurrentOperations:
    """Integration tests for concurrent operations."""

    def test_concurrent_handshake_and_message_send(self):
        """Test that handshake and message send can work concurrently."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        # Send both handshake and regular message
        ws_manager.send_handshake()
        ws_manager.send_json({"action": "ping"})

        # Both should be sent
        assert len(mock_ws.sent_messages) >= 2

    def test_multiple_handshake_calls(self):
        """Test multiple calls to send_handshake()."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))
        config = {
            "enabled": True,
            "clientId": "test-device",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        # Send multiple handshakes
        ws_manager.send_handshake()
        ws_manager.send_handshake()
        ws_manager.send_handshake()

        # All should be sent
        assert len(mock_ws.sent_messages) >= 3
        for msg in mock_ws.sent_messages:
            payload = json.loads(msg)
            assert payload["action"] == "handshake"


class TestBackwardCompatibility:
    """Integration tests for backward compatibility."""

    def test_websocket_manager_without_handshake_config(self):
        """Test that WebSocketManager works without handshake_config."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        # Initialize without handshake_config (should default to {})
        ws_manager = WebSocketManager(logger=logger)

        assert ws_manager.handshake_config == {}

    def test_websocket_manager_without_config_file(self):
        """Test behavior when handshake_config.json doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use non-existent path
            config_path = os.path.join(tmpdir, "nonexistent.json")
            
            config = load_handshake_config(config_path)

            # Should return defaults
            assert config["enabled"] is True
            assert "clientId" in config

    def test_send_json_still_works(self):
        """Test that send_json() still works independently."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = {"enabled": True}

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        payload = {"action": "ping", "timestamp": "2026-03-27T12:00:00Z"}
        ws_manager.send_json(payload)

        assert len(mock_ws.sent_messages) > 0
        sent = json.loads(mock_ws.sent_messages[0])
        assert sent["action"] == "ping"

    def test_existing_on_message_callback(self):
        """Test that existing on_message callback still works."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        
        message_received = []
        def on_message(msg):
            message_received.append(msg)

        ws_manager = WebSocketManager(
            logger=logger,
            on_message=on_message,
        )

        test_message = '{"action":"ping"}'
        ws_manager._on_message(None, test_message)

        assert len(message_received) > 0
        assert message_received[0] == test_message


class TestConfigurationHotReload:
    """Integration tests for configuration updates."""

    def test_config_change_updates_payload(self):
        """Test that changing config updates generated payload."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)

        config1 = {
            "clientId": "device-001",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config1)
        payload1 = ws_manager._build_handshake_payload()

        # Update config
        config2 = {
            "clientId": "device-002",
            "capabilities": ["websocket", "http"],
            "session_metadata": {},
            "authentication_context": {},
        }
        ws_manager.handshake_config = config2
        payload2 = ws_manager._build_handshake_payload()

        assert payload1["clientId"] == "device-001"
        assert payload2["clientId"] == "device-002"
        assert payload1["capabilities"] != payload2["capabilities"]

    def test_enable_disable_handshake(self):
        """Test enabling/disabling handshake."""
        logs = []
        logger = AppLogger(lambda msg: logs.append(msg))

        config = {
            "enabled": True,
            "clientId": "test",
            "capabilities": ["websocket"],
            "session_metadata": {},
            "authentication_context": {},
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        mock_ws = MockWebSocket()
        ws_manager.ws_app = mock_ws
        ws_manager.connected = True

        # Send with enabled=True
        ws_manager.send_handshake()
        sent_count_1 = len(mock_ws.sent_messages)

        # Disable and try to send
        ws_manager.handshake_config["enabled"] = False
        ws_manager.send_handshake()
        sent_count_2 = len(mock_ws.sent_messages)

        # Should not send second handshake
        assert sent_count_1 > 0
        assert sent_count_2 == sent_count_1  # No additional message


class TestPayloadContent:
    """Integration tests for payload content validation."""

    def test_handshake_payload_structure(self):
        """Test that handshake payload has correct structure."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        # Verify structure
        assert isinstance(payload, dict)
        assert "action" in payload
        assert "clientId" in payload
        assert "capabilities" in payload
        assert isinstance(payload["capabilities"], list)
        assert "session_metadata" in payload
        assert isinstance(payload["session_metadata"], dict)
        assert "authentication_context" in payload
        assert isinstance(payload["authentication_context"], dict)

    def test_handshake_payload_json_size(self):
        """Test that handshake payload is reasonably sized."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        config = load_handshake_config()

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()
        
        json_str = json.dumps(payload)
        size = len(json_str)

        # Should be reasonable size (not gigabytes!)
        assert size > 0
        assert size < 10000  # Less than 10KB

    def test_handshake_payload_contains_capabilities(self):
        """Test that capabilities are included in payload."""
        mock_logger = Mock()
        logger = AppLogger(mock_logger)
        capabilities = ["websocket", "http", "mqtt"]
        config = {
            "capabilities": capabilities,
        }

        ws_manager = WebSocketManager(logger=logger, handshake_config=config)
        payload = ws_manager._build_handshake_payload()

        assert payload["capabilities"] == capabilities
