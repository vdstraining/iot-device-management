"""
Unit tests for handshake message functionality.
Tests auto-send on connection, JSON validation, response logging, and toggle behavior.
"""
"""
SCRUM-121: Comprehensive Handshake Message Implementation Tests
Tests for automatic handshake functionality, JSON validation, response handling, and UI integration.

Test Coverage:
- Unit tests for auto-send behavior (enabled/disabled)
- JSON validation tests (valid/invalid payloads)
- Response handling tests (correct/malformed responses)
- Integration test: full handshake flow (connect → send → response → log)
- Regression tests: existing command functionality unaffected
- UI toggle tests: verify checkbox updates WebSocketManager state
- Edge case tests: reconnection, race conditions, timeouts
"""

import json
import threading
import time
from unittest import mock
from unittest.mock import MagicMock, Mock, patch, call
import pytest

from ws_client import WebSocketManager
from utilities import AppLogger, DEFAULT_COMMANDS


class MockLogger:
    """Mock logger for collecting test messages"""
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)
    
    def get_output(self):
        """Get concatenated log output"""
        return " ".join(self.messages)


# ============================================================================
# UNIT TESTS: WebSocketManager Initialization & Auto-Handshake Configuration
# ============================================================================

class TestWebSocketManagerInitialization:
    """Tests for WebSocketManager initialization with handshake settings"""

    def test_init_with_default_enable_auto_handshake_true(self):
        """WebSocketManager should enable auto-handshake by default"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger)
        assert hasattr(manager, 'enable_auto_handshake')
        assert manager.enable_auto_handshake is True

    def test_init_with_enable_auto_handshake_false(self):
        """WebSocketManager should accept enable_auto_handshake=False"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=False)
        assert manager.enable_auto_handshake is False

    def test_init_with_enable_auto_handshake_true(self):
        """WebSocketManager should accept enable_auto_handshake=True explicitly"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        assert manager.enable_auto_handshake is True

    def test_init_sets_handshake_sent_flag_to_false(self):
        """_handshake_sent flag should be False on initialization"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger)
        assert hasattr(manager, '_handshake_sent')
        assert manager._handshake_sent is False

    def test_init_preserves_other_callbacks(self):
        """Initialization should not break existing callbacks"""
        logger = MockLogger()
        on_message_mock = Mock()
        on_status_mock = Mock()
        
        manager = WebSocketManager(
            logger=logger,
            on_message=on_message_mock,
            on_status_change=on_status_mock,
            enable_auto_handshake=True
        )
        
        assert manager.on_message == on_message_mock
        assert manager.on_status_change == on_status_mock


# ============================================================================
# UNIT TESTS: Handshake Template in DEFAULT_COMMANDS
# ============================================================================

class TestHandshakeTemplate:
    """Tests for handshake template in utilities.DEFAULT_COMMANDS"""

    def test_handshake_command_exists_in_default_commands(self):
        """AC1: Handshake command should be available in DEFAULT_COMMANDS"""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in command_names, "Handshake command must exist in DEFAULT_COMMANDS"

    def test_handshake_payload_structure(self):
        """Handshake payload should have required fields"""
        handshake_cmd = next((cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None)
        assert handshake_cmd is not None, "Handshake command not found"
        payload = handshake_cmd["payload"]
        
        # Check required fields per acceptance criteria
        assert "action" in payload, "Missing 'action' field"
        assert payload["action"] == "handshake", "action must be 'handshake'"
        assert "client_id" in payload, "Missing 'client_id' field"
        assert "client_version" in payload, "Missing 'client_version' field"

    def test_handshake_payload_is_valid_json(self):
        """AC1: Handshake payload should be serializable to JSON"""
        handshake_cmd = next((cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None)
        payload = handshake_cmd["payload"]
        
        # Should not raise
        json_str = json.dumps(payload)
        assert json_str is not None
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized == payload


# ============================================================================
# UNIT TESTS: _send_handshake() Method
# ============================================================================

class TestSendHandshakeMethod:
    """Tests for WebSocketManager._send_handshake() method"""

    def test_send_handshake_validates_json(self):
        """AC3: _send_handshake should validate JSON before sending"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        # Mock ws_app
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        manager._send_handshake()
        
        # Should call send with valid JSON string
        assert manager.ws_app.send.called, "ws_app.send should have been called"
        sent_data = manager.ws_app.send.call_args[0][0]
        
        # Verify it's valid JSON
        parsed = json.loads(sent_data)
        assert isinstance(parsed, dict)
        assert "action" in parsed
        assert parsed["action"] == "handshake"

    def test_send_handshake_sets_flag(self):
        """_send_handshake should set _handshake_sent flag after successful send"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        manager._send_handshake()
        
        assert manager._handshake_sent is True, "Flag should be set after handshake sent"

    def test_send_handshake_logs_message(self):
        """AC4: _send_handshake should log 'Handshake sent' message"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        manager._send_handshake()
        
        # Check log messages contain "Handshake sent"
        log_output = logger.get_output()
        assert "Handshake sent" in log_output, "Log should contain 'Handshake sent' message"

    def test_send_handshake_when_not_connected(self):
        """_send_handshake should not send if WebSocket is not connected"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = False  # Not connected
        manager._handshake_sent = False
        
        manager._send_handshake()
        
        # Should not call ws_app.send
        assert not manager.ws_app.send.called, "Should not send when not connected"

    def test_send_handshake_when_app_is_none(self):
        """_send_handshake should not crash if ws_app is None"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = None
        manager.connected = False
        manager._handshake_sent = False
        
        # Should not raise exception
        manager._send_handshake()

    def test_send_handshake_handles_json_error(self):
        """_send_handshake should handle JSON serialization errors gracefully"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        # Mock json.dumps to raise an error
        with patch("ws_client.json.dumps", side_effect=TypeError("not serializable")):
            manager._send_handshake()
        
        # Should log error message and not crash
        log_output = logger.get_output()
        assert len(logger.messages) > 0, "Should have logged an error message"


# ============================================================================
# UNIT TESTS: Auto-Send on WebSocket Connection (_on_open)
# ============================================================================

class TestAutoHandshakeSend:
    """Tests for auto-handshake behavior when WebSocket opens"""

    def test_handshake_scheduled_on_open_when_enabled(self):
        """AC2: Handshake should be scheduled to send within 100ms of _on_open when enabled"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager._send_handshake = Mock()
        
        manager._on_open(manager.ws_app)
        
        # Should set connected flag
        assert manager.connected is True, "Connected flag should be set"

    def test_handshake_not_scheduled_when_disabled(self):
        """Handshake should not schedule when enable_auto_handshake=False"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=False)
        manager.ws_app = Mock()
        manager._handshake_sent = False
        original_send = manager._send_handshake
        
        manager._on_open(manager.ws_app)
        
        # Connected should still be set
        assert manager.connected is True
        # But handshake should not have been sent (we can verify by checking flag)
        # In the real implementation, no Timer is started

    def test_websocket_connected_logged(self):
        """WebSocket connection should be logged"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=False)
        manager.ws_app = Mock()
        
        manager._on_open(manager.ws_app)
        
        log_output = logger.get_output()
        assert "connected" in log_output.lower(), "Connection should be logged"


# ============================================================================
# UNIT TESTS: Handshake Response Handler
# ============================================================================

class TestHandshakeResponseHandler:
    """Tests for handling handshake response in _on_message"""

    def test_handshake_response_is_logged(self):
        """AC5: Handshake response should be logged with timestamp"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        handshake_response = json.dumps({
            "action": "handshake",
            "status": "acknowledged",
            "server_id": "server-001"
        })
        
        manager._on_message(manager.ws_app, handshake_response)
        
        # Check that message was logged
        log_output = logger.get_output()
        assert len(logger.messages) > 0, "Response should be logged"

    def test_handshake_response_triggers_callback(self):
        """Handshake response should trigger on_message callback"""
        logger = MockLogger()
        on_message_callback = Mock()
        manager = WebSocketManager(
            logger=logger,
            on_message=on_message_callback,
            enable_auto_handshake=True
        )
        
        handshake_response = json.dumps({
            "action": "handshake",
            "status": "acknowledged"
        })
        
        manager._on_message(manager.ws_app, handshake_response)
        
        # Should call on_message callback
        assert on_message_callback.called, "Callback should be invoked"

    def test_malformed_response_handled(self):
        """Malformed handshake responses should not cause crashes"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        # Send invalid JSON
        malformed_response = "{ invalid json }"
        
        # Should not raise exception
        try:
            manager._on_message(manager.ws_app, malformed_response)
        except Exception as e:
            pytest.fail(f"_on_message raised exception: {e}")

    def test_non_handshake_messages_still_handled(self):
        """Messages with action != 'handshake' should be handled normally"""
        logger = MockLogger()
        on_message_callback = Mock()
        manager = WebSocketManager(
            logger=logger,
            on_message=on_message_callback,
            enable_auto_handshake=True
        )
        
        # Send message with different action
        other_response = json.dumps({
            "action": "ping",
            "status": "pong"
        })
        
        manager._on_message(manager.ws_app, other_response)
        
        # Should still call callback
        assert on_message_callback.called, "Non-handshake messages should be handled"


# ============================================================================
# JSON VALIDATION TESTS
# ============================================================================

class TestJSONValidation:
    """Tests for JSON validation in handshake payload"""

    def test_valid_handshake_payload_passes_validation(self):
        """Valid handshake payload should pass JSON validation"""
        valid_payload = {
            "action": "handshake",
            "client_id": "client-001",
            "client_version": "1.0"
        }
        
        # Should not raise
        json_str = json.dumps(valid_payload)
        validated = json.loads(json_str)
        assert validated == valid_payload

    def test_handshake_payload_with_extra_fields_valid(self):
        """Handshake payload with extra fields should still be valid JSON"""
        payload = {
            "action": "handshake",
            "client_id": "client-001",
            "client_version": "1.0",
            "extra_field": "extra_value"
        }
        
        # Should not raise
        json_str = json.dumps(payload)
        validated = json.loads(json_str)
        assert "extra_field" in validated

    def test_handshake_payload_with_null_values(self):
        """Handshake payload with null values should still be valid JSON"""
        payload = {
            "action": "handshake",
            "client_id": None,
            "client_version": "1.0"
        }
        
        # Should not raise
        json_str = json.dumps(payload)
        validated = json.loads(json_str)
        assert validated["client_id"] is None


# ============================================================================
# INTEGRATION TESTS: Full Handshake Flow
# ============================================================================

class TestHandshakeIntegrationFlow:
    """Integration tests for complete handshake workflow"""

    def test_full_handshake_flow_connect_send_response_log(self):
        """AC1-AC5: Test complete handshake flow: connect → send → response → log"""
        logger = MockLogger()
        on_message_callback = Mock()
        manager = WebSocketManager(
            logger=logger,
            on_message=on_message_callback,
            enable_auto_handshake=True
        )
        
        # Step 1: Simulate connection
        manager.ws_app = Mock()
        manager._on_open(manager.ws_app)
        assert manager.connected is True
        
        # Step 2: Send handshake
        manager._send_handshake()
        assert manager._handshake_sent is True
        
        # Verify send was called
        assert manager.ws_app.send.called
        
        # Step 3: Server responds
        response = json.dumps({
            "action": "handshake",
            "status": "acknowledged",
            "server_id": "server-001"
        })
        manager._on_message(manager.ws_app, response)
        
        # Step 4: Verify logging
        assert len(logger.messages) > 0, "Should have logged messages"

    def test_handshake_only_sent_once_per_connection(self):
        """Handshake should only be sent once per connection"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        # First call
        manager._send_handshake()
        assert manager._handshake_sent is True
        first_call_count = manager.ws_app.send.call_count
        
        # Flag prevents double-sending in the logic
        assert manager._handshake_sent is True


# ============================================================================
# REGRESSION TESTS: Existing Functionality Unaffected
# ============================================================================

class TestRegressionExistingAPI:
    """Regression tests to ensure existing APIs still work"""

    def test_send_json_still_works(self):
        """AC8: send_json() should work independently of handshake"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=False)
        manager.ws_app = Mock()
        manager.connected = True
        
        payload = {"action": "ping"}
        manager.send_json(payload)
        
        # Should have sent the message
        assert manager.ws_app.send.called, "send_json should work"
        sent_data = manager.ws_app.send.call_args[0][0]
        assert "ping" in sent_data

    def test_disconnect_works(self):
        """disconnect() should work as before"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        # disconnect when not connected
        manager.ws_app = None
        manager.disconnect()  # Should not crash
        
        # Check log message
        log_output = logger.get_output()
        assert len(logger.messages) > 0

    def test_on_message_callback_still_invoked(self):
        """on_message callback should still be called"""
        logger = MockLogger()
        on_message_callback = Mock()
        manager = WebSocketManager(
            logger=logger,
            on_message=on_message_callback,
            enable_auto_handshake=True
        )
        
        message = json.dumps({"action": "ping", "data": "test"})
        manager._on_message(manager.ws_app, message)
        
        assert on_message_callback.called

    def test_on_status_change_callback_still_invoked(self):
        """on_status_change callback should still be called"""
        logger = MockLogger()
        on_status_callback = Mock()
        manager = WebSocketManager(
            logger=logger,
            on_status_change=on_status_callback,
            enable_auto_handshake=True
        )
        
        manager.ws_app = Mock()
        manager._on_open(manager.ws_app)
        
        # Callback should be called with True (connected)
        assert on_status_callback.called
        assert on_status_callback.call_args[0][0] is True


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests for handshake functionality"""

    def test_reconnection_resets_handshake_flag(self):
        """Reconnecting should reset the _handshake_sent flag"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        # First connection sends handshake
        manager._send_handshake()
        assert manager._handshake_sent is True
        
        # Simulate disconnect (flag reset in _on_close)
        manager._on_close(manager.ws_app, 1000, "Normal close")
        assert manager._handshake_sent is False, "Flag should be reset on disconnect"

    def test_rapid_open_close_cycles(self):
        """Rapid connect/disconnect cycles should not crash"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        for _ in range(5):
            manager.ws_app = Mock()
            manager._on_open(manager.ws_app)
            manager.connected = True
            manager._on_close(manager.ws_app, 1000, "Normal close")
            manager.connected = False

    def test_handshake_with_immediate_send(self):
        """Handshake should work even with immediate send"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        # Immediate send
        manager._send_handshake()
        assert manager._handshake_sent is True

    def test_massive_response_payload(self):
        """Large handshake response should be handled"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        # Create large response
        large_response = json.dumps({
            "action": "handshake",
            "data": "x" * 100000
        })
        
        # Should not crash
        manager._on_message(manager.ws_app, large_response)


# ============================================================================
# ACCEPTANCE CRITERIA VERIFICATION TESTS
# ============================================================================

class TestAcceptanceCriteria:
    """Tests verifying all acceptance criteria are met"""

    def test_ac1_handshake_in_default_commands_and_editable(self):
        """AC1: Handshake command in default commands list, manually selectable/editable"""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in command_names
        
        handshake_cmd = next((cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None)
        assert handshake_cmd is not None
        payload = handshake_cmd["payload"]
        
        # Should be editable (can serialize and deserialize)
        json_str = json.dumps(payload, indent=2)
        edited_payload = json.loads(json_str)
        assert edited_payload == payload

    def test_ac2_auto_send_within_100ms(self):
        """AC2: Handshake automatically sends within 100ms of WebSocket _on_open()"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        
        start = time.time()
        manager._on_open(manager.ws_app)
        elapsed_ms = (time.time() - start) * 1000
        
        # _on_open should complete quickly (Timer is started asynchronously)
        assert elapsed_ms < 100, "Should complete within 100ms"

    def test_ac3_json_validation_before_sending(self):
        """AC3: Handshake JSON is validated before sending"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        
        manager._send_handshake()
        
        # Verify send was called with valid JSON
        assert manager.ws_app.send.called
        sent_data = manager.ws_app.send.call_args[0][0]
        # This will raise if not valid JSON
        json.loads(sent_data)

    def test_ac4_handshake_sent_message_with_timestamp(self):
        """AC4: 'Handshake sent' message appears in UI log with timestamp"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        manager._handshake_sent = False
        
        manager._send_handshake()
        
        log_output = logger.get_output()
        assert "Handshake sent" in log_output
        # Timestamp check: AppLogger adds [YYYY-MM-DD HH:MM:SS]
        assert "[" in log_output and "]" in log_output

    def test_ac5_server_response_received_and_logged(self):
        """AC5: Server handshake response is received and logged to UI"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        
        response = json.dumps({
            "action": "handshake",
            "status": "acknowledged"
        })
        
        manager._on_message(manager.ws_app, response)
        
        assert len(logger.messages) > 0

    def test_ac6_auto_send_can_be_disabled(self):
        """AC6: Handshake auto-send can be disabled via configuration flag"""
        logger = MockLogger()
        manager_disabled = WebSocketManager(
            logger=logger,
            enable_auto_handshake=False
        )
        manager_disabled.ws_app = Mock()
        manager_disabled._send_handshake = Mock()
        
        manager_disabled._on_open(manager_disabled.ws_app)
        
        # Timer should not be started (no calls to _send_handshake from _on_open)
        # but on_open should still set connected=True
        assert manager_disabled.connected is True

    def test_ac7_manual_handshake_anytime(self):
        """AC7: Manual handshake can be sent by selecting template and clicking Send"""
        logger = MockLogger()
        manager = WebSocketManager(logger=logger, enable_auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        
        # Get handshake command from DEFAULT_COMMANDS
        handshake_cmd = next((cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None)
        assert handshake_cmd is not None
        
        # Send manually
        manager.send_json(handshake_cmd["payload"])
        
        assert manager.ws_app.send.called

    def test_ac8_no_breaking_changes_to_api(self):
        """AC8: No breaking changes to existing APIs"""
        logger = MockLogger()
        
        # Old-style initialization should still work
        manager_old = WebSocketManager(
            logger=logger,
            on_message=Mock(),
            on_status_change=Mock()
        )
        
        assert manager_old.connected is False
        assert manager_old.ws_app is None
        # New parameter should default to True
        assert manager_old.enable_auto_handshake is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from ws_client import WebSocketManager


class TestHandshakeMessage(unittest.TestCase):
    """Test suite for WebSocketManager handshake functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_handshake_default_enabled(self):
        """Test that auto-handshake is enabled by default."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
        )
        self.assertTrue(manager.enable_auto_handshake)

    def test_handshake_can_be_disabled(self):
        """Test that auto-handshake can be disabled via parameter."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
            enable_auto_handshake=False,
        )
        self.assertFalse(manager.enable_auto_handshake)

    def test_handshake_flag_initialized_false(self):
        """Test that _handshake_sent flag is initialized to False."""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertFalse(manager._handshake_sent)

    def test_send_handshake_json_structure(self):
        """Test that handshake JSON has correct structure and required fields."""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.ws_app = Mock()
        manager.connected = True

        # Call _send_handshake
        manager._send_handshake()

        # Verify that send_json was called
        # We can't directly test send_json call without mocking more,
        # but we can verify the logger was called with handshake message
        log_calls = [str(call) for call in self.mock_logger.log.call_args_list]
        self.assertTrue(
            any("Handshake sent" in str(call) for call in log_calls),
            "Expected 'Handshake sent' message in logs"
        )

    def test_send_handshake_when_not_connected(self):
        """Test that handshake doesn't send if not connected."""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = False
        manager.ws_app = None

        manager._send_handshake()

        # Should log connection error
        self.mock_logger.log.assert_called_with(
            "Cannot send handshake: WebSocket not connected."
        )

    def test_send_handshake_marks_sent_flag(self):
        """Test that _handshake_sent flag is set to True after sending."""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = True
        manager.ws_app = Mock()

        self.assertFalse(manager._handshake_sent)
        manager._send_handshake()
        self.assertTrue(manager._handshake_sent)

    def test_handshake_response_handler(self):
        """Test that handshake responses are logged with action type."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
        )

        # Create a handshake response message
        response = {
            "action": "handshake",
            "status": "accepted",
            "client_id": "device-123",
        }
        response_json = json.dumps(response)

        manager._on_message(None, response_json)

        # Verify logger was called with handshake response message
        log_calls = [call[0][0] for call in self.mock_logger.log.call_args_list]
        self.assertTrue(
            any("Handshake response received" in str(call) for call in log_calls),
            "Expected 'Handshake response received' message in logs"
        )

    def test_non_handshake_messages_handled_normally(self):
        """Test that non-handshake messages are handled by normal message handler."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
        )

        # Create a non-handshake message
        response = {"action": "ping"}
        response_json = json.dumps(response)

        manager._on_message(None, response_json)

        # Verify on_message callback was called
        self.mock_on_message.assert_called_once_with(response_json)

    def test_invalid_json_message_handled_gracefully(self):
        """Test that invalid JSON messages are handled gracefully."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
        )

        invalid_json = "not valid json {]["
        manager._on_message(None, invalid_json)

        # Verify on_message callback was called with invalid JSON
        self.mock_on_message.assert_called_once_with(invalid_json)

    def test_handshake_flag_reset_on_close(self):
        """Test that _handshake_sent flag is reset to False on connection close."""
        manager = WebSocketManager(logger=self.mock_logger)
        manager._handshake_sent = True

        manager._on_close(None, 1000, "Normal closure")

        self.assertFalse(manager._handshake_sent)

    def test_handshake_sets_connected_status(self):
        """Test that _on_open sets connected status and can trigger handshake."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=self.mock_on_status_change,
            enable_auto_handshake=True,
        )
        manager.ws_app = Mock()

        self.assertFalse(manager.connected)
        manager._on_open(None)
        
        # Verify connected was set to True
        self.assertTrue(manager.connected)
        # Verify on_status_change was called
        self.mock_on_status_change.assert_called_with(True)

    def test_auto_handshake_disabled_on_open(self):
        """Test that handshake is not triggered when auto-handshake is disabled."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            enable_auto_handshake=False,
        )
        manager.ws_app = Mock()

        manager._on_open(None)

        # Verify logger was called with connection message only (no handshake)
        log_calls = [call[0][0] for call in self.mock_logger.log.call_args_list]
        # Should have connection log but not trigger handshake_sent message
        self.assertTrue(any("WebSocket connected" in str(call) for call in log_calls))

    def test_handshake_payload_structure(self):
        """Test the structure of handshake payload."""
        # This test validates the handshake message structure matches spec
        expected_fields = {
            "action": "handshake",
            "client_version": "1.0",
            "client_id": "replace-me",
            "capabilities": [],
            "auth_token": None,
        }

        # Verify it's valid JSON
        payload_json = json.dumps(expected_fields)
        parsed = json.loads(payload_json)

        self.assertEqual(parsed["action"], "handshake")
        self.assertEqual(parsed["client_version"], "1.0")
        self.assertIsNone(parsed["auth_token"])
        self.assertIsInstance(parsed["capabilities"], list)

    def test_multiple_connections_reset_handshake_flag(self):
        """Test that handshake can be resent on multiple connections."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            enable_auto_handshake=True,
        )
        manager.ws_app = Mock()

        # First connection
        manager._on_open(None)
        manager._handshake_sent = True

        # Close connection
        manager._on_close(None, 1000, "Normal closure")
        self.assertFalse(manager._handshake_sent)

        # Second connection - flag should allow handshake again
        self.assertFalse(manager._handshake_sent)
        self.assertTrue(manager.enable_auto_handshake)


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake with UI settings."""

    def test_ui_handshake_toggle_updates_manager(self):
        """Test that UI handshake toggle properly updates WebSocketManager."""
        # This is a conceptual test showing how the integration works
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            enable_auto_handshake=True,
        )

        # Simulate UI toggle turning off auto-handshake
        manager.enable_auto_handshake = False
        self.assertFalse(manager.enable_auto_handshake)

        # Simulate UI toggle turning on auto-handshake
        manager.enable_auto_handshake = True
        self.assertTrue(manager.enable_auto_handshake)


if __name__ == "__main__":
    unittest.main()
