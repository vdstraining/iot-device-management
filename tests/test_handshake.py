#!/usr/bin/env python3
"""
Comprehensive tests for SCRUM-81: Handshake message implementation.

Tests cover:
- Unit tests for handshake payload validation
- Tests for send_handshake() method
- Tests for auto_handshake parameter
- DEFAULT_COMMANDS integration tests
- Logging verification
- Integration tests
- Edge case tests
"""

import json
import pytest
import threading
import time
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call
from typing import List

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ws_client import WebSocketManager
from utilities import AppLogger, DEFAULT_COMMANDS


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=AppLogger)
    logger.log = Mock()
    return logger


@pytest.fixture
def captured_logs(mock_logger):
    """Fixture to capture log messages."""
    logs = []
    
    def capture_log(message: str) -> None:
        logs.append(message)
    
    mock_logger.log.side_effect = capture_log
    return logs


@pytest.fixture
def ws_manager(mock_logger):
    """Create a WebSocketManager instance with mock logger."""
    return WebSocketManager(logger=mock_logger)


@pytest.fixture
def ws_manager_with_auto_handshake(mock_logger):
    """Create a WebSocketManager with auto_handshake enabled."""
    return WebSocketManager(logger=mock_logger, auto_handshake=True)


@pytest.fixture
def ws_manager_with_callbacks(mock_logger):
    """Create a WebSocketManager with message and status callbacks."""
    on_message_callback = Mock()
    on_status_callback = Mock()
    
    manager = WebSocketManager(
        logger=mock_logger,
        on_message=on_message_callback,
        on_status_change=on_status_callback,
    )
    
    return manager, on_message_callback, on_status_callback


# ============================================================================
# UNIT TESTS: Handshake Payload Validation
# ============================================================================


class TestHandshakePayloadValidation:
    """Tests for validating handshake message structure and content."""

    def test_handshake_payload_has_all_required_fields(self, mock_logger):
        """Verify handshake message contains all required fields."""
        manager = WebSocketManager(logger=mock_logger)
        
        # Mock send_json to capture the payload
        sent_payloads = []
        manager.ws_app = Mock()
        manager.connected = True
        
        original_send_json = manager.send_json
        
        def mock_send_json(payload):
            sent_payloads.append(payload)
        
        manager.send_json = mock_send_json
        manager.send_handshake()
        
        assert len(sent_payloads) == 1
        payload = sent_payloads[0]
        
        # Verify required fields
        assert "action" in payload
        assert "clientId" in payload
        assert "capabilities" in payload
        assert "protocolVersion" in payload
        assert "timestamp" in payload

    def test_handshake_action_is_handshake(self, mock_logger):
        """Verify action field is set to 'handshake'."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        
        def mock_send_json(payload):
            sent_payloads.append(payload)
        
        manager.send_json = mock_send_json
        manager.send_handshake()
        
        assert sent_payloads[0]["action"] == "handshake"

    def test_handshake_default_clientid(self, mock_logger):
        """Verify default clientId is 'client_001'."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake()
        
        assert sent_payloads[0]["clientId"] == "client_001"

    def test_handshake_custom_clientid(self, mock_logger):
        """Verify custom clientId parameter works."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake(client_id="my_device_42")
        
        assert sent_payloads[0]["clientId"] == "my_device_42"

    def test_handshake_capabilities_list(self, mock_logger):
        """Verify capabilities field contains expected values."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake()
        
        payload = sent_payloads[0]
        assert isinstance(payload["capabilities"], list)
        assert "websocket" in payload["capabilities"]
        assert "http" in payload["capabilities"]

    def test_handshake_protocol_version(self, mock_logger):
        """Verify protocolVersion field."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake()
        
        assert sent_payloads[0]["protocolVersion"] == "1.0"

    def test_handshake_timestamp_iso8601_format(self, mock_logger):
        """Verify timestamp is in ISO 8601 format with Z suffix."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake()
        
        timestamp = sent_payloads[0]["timestamp"]
        assert timestamp.endswith("Z"), "Timestamp should end with 'Z'"
        
        # Verify it's parseable as ISO 8601
        # Remove trailing Z and parse
        dt_str = timestamp.rstrip("Z")
        try:
            parsed_dt = datetime.fromisoformat(dt_str)
            assert parsed_dt is not None
        except ValueError:
            pytest.fail(f"Timestamp not in valid ISO 8601 format: {timestamp}")

    def test_handshake_payload_is_valid_json(self, mock_logger):
        """Verify handshake payload is valid JSON serializable."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        manager.send_handshake()
        
        payload = sent_payloads[0]
        # Should be serializable to JSON without error
        json_str = json.dumps(payload)
        assert isinstance(json_str, str)
        
        # Should be deserializable back
        deserialized = json.loads(json_str)
        assert deserialized == payload


# ============================================================================
# UNIT TESTS: send_handshake() Method
# ============================================================================


class TestSendHandshakeMethod:
    """Tests for the send_handshake() method functionality."""

    def test_send_handshake_method_exists(self, ws_manager):
        """Verify send_handshake method exists and is callable."""
        assert hasattr(ws_manager, "send_handshake")
        assert callable(ws_manager.send_handshake)

    def test_send_handshake_default_parameters(self, mock_logger):
        """Verify send_handshake() can be called with default parameters."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        # Should not raise any exception
        manager.send_handshake()
        assert len(sent_payloads) == 1

    def test_send_handshake_with_custom_client_id(self, mock_logger):
        """Verify send_handshake() accepts custom client_id."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        # Should accept client_id parameter
        manager.send_handshake(client_id="test_client")
        assert sent_payloads[0]["clientId"] == "test_client"

    def test_send_handshake_various_client_ids(self, mock_logger):
        """Verify send_handshake() works with various clientId values."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        test_ids = [
            "client_001",
            "device_sensor_01",
            "iot_gateway_primary",
            "temp_sensor_kitchen",
            "123456",
            "test-device-001",
        ]
        
        for test_id in test_ids:
            sent_payloads = []
            manager.send_json = lambda payload: sent_payloads.append(payload)
            
            manager.send_handshake(client_id=test_id)
            assert sent_payloads[0]["clientId"] == test_id

    def test_send_handshake_logging(self, mock_logger):
        """Verify send_handshake() produces logging output."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        manager.send_json = Mock()
        
        manager.send_handshake(client_id="test_id")
        
        # Should have called logger.log
        assert mock_logger.log.called
        # Check that it logged the handshake
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("handshake" in msg.lower() for msg in logged_messages)

    def test_send_handshake_calls_send_json(self, mock_logger):
        """Verify send_handshake() calls send_json()."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        manager.send_json = Mock()
        
        manager.send_handshake()
        
        assert manager.send_json.called
        # Verify it was called with a dict payload
        call_args = manager.send_json.call_args
        assert call_args is not None
        payload = call_args[0][0]
        assert isinstance(payload, dict)
        assert payload["action"] == "handshake"


# ============================================================================
# UNIT TESTS: auto_handshake Parameter
# ============================================================================


class TestAutoHandshakeParameter:
    """Tests for auto_handshake parameter functionality."""

    def test_auto_handshake_default_is_false(self, mock_logger):
        """Verify auto_handshake defaults to False."""
        manager = WebSocketManager(logger=mock_logger)
        assert manager.auto_handshake is False

    def test_auto_handshake_parameter_accepted(self, mock_logger):
        """Verify WebSocketManager accepts auto_handshake parameter."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        assert manager.auto_handshake is True

    def test_auto_handshake_true_value(self, mock_logger):
        """Verify auto_handshake can be set to True."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        assert manager.auto_handshake is True

    def test_auto_handshake_false_value(self, mock_logger):
        """Verify auto_handshake can be set to False."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        assert manager.auto_handshake is False

    def test_auto_handshake_trigger_on_connection(self, mock_logger):
        """Verify handshake is triggered on connection when auto_handshake=True."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        manager.send_handshake = Mock()
        
        # Simulate connection opened
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Should have called send_handshake
        assert manager.send_handshake.called

    def test_no_auto_handshake_when_disabled(self, mock_logger):
        """Verify handshake is NOT triggered when auto_handshake=False."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.send_handshake = Mock()
        
        # Simulate connection opened
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Should NOT have called send_handshake
        assert not manager.send_handshake.called

    def test_auto_handshake_still_allows_manual_send(self, mock_logger):
        """Verify manual send_handshake() works even with auto_handshake=True."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        # Manual handshake should work
        manager.send_handshake(client_id="manual_test")
        
        assert len(sent_payloads) == 1
        assert sent_payloads[0]["clientId"] == "manual_test"


# ============================================================================
# UNIT TESTS: DEFAULT_COMMANDS Integration
# ============================================================================


class TestDefaultCommandsIntegration:
    """Tests for handshake integration in DEFAULT_COMMANDS."""

    def test_handshake_in_default_commands(self):
        """Verify handshake preset exists in DEFAULT_COMMANDS."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in command_names

    def test_handshake_command_structure(self):
        """Verify handshake command has correct structure."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        assert handshake_cmd is not None
        assert "payload" in handshake_cmd
        assert isinstance(handshake_cmd["payload"], dict)

    def test_handshake_payload_structure(self):
        """Verify handshake payload has all required fields."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        payload = handshake_cmd["payload"]
        
        required_fields = [
            "action",
            "clientId",
            "capabilities",
            "protocolVersion",
            "timestamp",
        ]
        
        for field in required_fields:
            assert field in payload, f"Missing field: {field}"

    def test_handshake_command_is_valid_json(self):
        """Verify handshake command is valid JSON."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        payload = handshake_cmd["payload"]
        
        # Should be serializable to JSON
        json_str = json.dumps(payload)
        assert isinstance(json_str, str)
        
        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized == payload

    def test_default_commands_count(self):
        """Verify DEFAULT_COMMANDS has 5 preset commands."""
        assert len(DEFAULT_COMMANDS) == 5, \
            f"Expected 5 default commands, got {len(DEFAULT_COMMANDS)}"

    def test_default_commands_all_have_name_and_payload(self):
        """Verify all default commands have name and payload."""
        for cmd in DEFAULT_COMMANDS:
            assert "name" in cmd, "Command missing 'name' field"
            assert "payload" in cmd, "Command missing 'payload' field"
            assert isinstance(cmd["name"], str), "Command name should be string"
            assert isinstance(cmd["payload"], dict), "Command payload should be dict"

    def test_handshake_appears_in_correct_position(self):
        """Verify handshake appears as second command (index 1)."""
        # Note: This verifies the order mentioned in requirements
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        
        assert command_names[1] == "Handshake", \
            f"Expected Handshake at index 1, got {command_names[1]}"


# ============================================================================
# UNIT TESTS: Logging Integration
# ============================================================================


class TestLoggingIntegration:
    """Tests for logging functionality related to handshake."""

    def test_send_handshake_logs_message(self, mock_logger):
        """Verify send_handshake produces log message."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        manager.send_json = Mock()
        
        manager.send_handshake()
        
        assert mock_logger.log.called

    def test_send_handshake_logs_include_client_id(self, mock_logger):
        """Verify log message includes clientId."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        manager.send_json = Mock()
        
        manager.send_handshake(client_id="my_device")
        
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("my_device" in msg for msg in logged_messages)

    def test_connection_logged_when_auto_handshake_enabled(self, mock_logger):
        """Verify logging when connection established with auto_handshake."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        manager.send_handshake = Mock()
        manager.on_status_change = Mock()
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Should have logged the automatic handshake
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("handshake" in msg.lower() for msg in logged_messages)

    def test_json_send_logged(self, mock_logger):
        """Verify JSON send via send_json is logged."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        payload = {"action": "test", "data": "sample"}
        manager.send_json(payload)
        
        # Should have logged the send
        assert mock_logger.log.called
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("Sent WebSocket message" in msg for msg in logged_messages)

    def test_error_logged_when_not_connected(self, mock_logger):
        """Verify error is logged when attempting to send while disconnected."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = None
        manager.connected = False
        
        payload = {"action": "test"}
        manager.send_json(payload)
        
        # Should have logged error
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("not connected" in msg.lower() for msg in logged_messages)


# ============================================================================
# INTEGRATION TESTS: Connection Flow
# ============================================================================


class TestConnectionFlow:
    """Integration tests for connection flow with handshake."""

    def test_handshake_triggers_on_successful_connection_with_auto_handshake(
        self, mock_logger
    ):
        """Verify handshake triggers automatically on successful connection."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        manager.send_handshake = Mock()
        manager.send_json = Mock()
        
        # Simulate successful connection
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify send_handshake was called
        assert manager.send_handshake.called

    def test_no_auto_handshake_when_disabled_on_connection(self, mock_logger):
        """Verify no automatic handshake when auto_handshake is False."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.send_handshake = Mock()
        
        # Simulate connection
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify send_handshake was NOT called
        assert not manager.send_handshake.called

    def test_manual_handshake_at_any_time(self, mock_logger):
        """Verify manual send_handshake() works at any time when connected."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        # Send multiple handshakes
        manager.send_handshake(client_id="client_1")
        manager.send_handshake(client_id="client_2")
        manager.send_handshake()  # default
        
        assert len(sent_payloads) == 3
        assert sent_payloads[0]["clientId"] == "client_1"
        assert sent_payloads[1]["clientId"] == "client_2"
        assert sent_payloads[2]["clientId"] == "client_001"

    def test_connection_status_set_on_open(self, mock_logger):
        """Verify connection status is set when connection opens."""
        manager = WebSocketManager(logger=mock_logger)
        assert manager.connected is False
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        assert manager.connected is True

    def test_connection_status_cleared_on_close(self, mock_logger):
        """Verify connection status is cleared when connection closes."""
        manager = WebSocketManager(logger=mock_logger)
        manager.connected = True
        
        mock_ws = Mock()
        manager._on_close(mock_ws, 1000, "Normal closure")
        
        assert manager.connected is False


# ============================================================================
# INTEGRATION TESTS: Message Transmission
# ============================================================================


class TestMessageTransmission:
    """Integration tests for handshake message transmission."""

    def test_handshake_message_properly_formatted(self, mock_logger):
        """Verify handshake message is properly formatted JSON."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        captured_messages = []
        
        def capture_send(msg):
            captured_messages.append(msg)
        
        manager.ws_app.send = capture_send
        manager.send_handshake()
        
        # Should have captured one message
        assert len(captured_messages) == 1
        
        # Message should be valid JSON
        msg_json = json.loads(captured_messages[0])
        assert isinstance(msg_json, dict)
        assert msg_json["action"] == "handshake"

    def test_handshake_sent_through_websocket(self, mock_logger):
        """Verify handshake is sent through WebSocket."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        manager.send_handshake()
        
        # Verify ws_app.send was called
        assert manager.ws_app.send.called

    def test_multiple_handshakes_sent_independently(self, mock_logger):
        """Verify multiple handshakes can be sent independently."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        captured_messages = []
        manager.ws_app.send = lambda msg: captured_messages.append(msg)
        
        manager.send_handshake(client_id="device_1")
        manager.send_handshake(client_id="device_2")
        
        assert len(captured_messages) == 2
        
        msg1 = json.loads(captured_messages[0])
        msg2 = json.loads(captured_messages[1])
        
        assert msg1["clientId"] == "device_1"
        assert msg2["clientId"] == "device_2"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_client_id(self, mock_logger):
        """Test handshake with empty clientId."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        manager.send_handshake(client_id="")
        
        assert sent_payloads[0]["clientId"] == ""

    def test_special_characters_in_client_id(self, mock_logger):
        """Test handshake with special characters in clientId."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        special_ids = [
            "client-001",
            "client_001-v2",
            "device.sensor.01",
            "iot/device/01",
            "client@domain.com",
        ]
        
        for special_id in special_ids:
            sent_payloads = []
            manager.send_json = lambda payload: sent_payloads.append(payload)
            
            manager.send_handshake(client_id=special_id)
            
            assert sent_payloads[0]["clientId"] == special_id
            # Verify it's still valid JSON
            json.dumps(sent_payloads[0])

    def test_very_long_client_id(self, mock_logger):
        """Test handshake with very long clientId."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        long_id = "x" * 1000
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        manager.send_handshake(client_id=long_id)
        
        assert sent_payloads[0]["clientId"] == long_id

    def test_multiple_handshakes_in_succession(self, mock_logger):
        """Test sending multiple handshakes in rapid succession."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        for i in range(10):
            manager.send_handshake(client_id=f"client_{i}")
        
        assert len(sent_payloads) == 10
        for i, payload in enumerate(sent_payloads):
            assert payload["clientId"] == f"client_{i}"

    def test_handshake_before_connection_established(self, mock_logger):
        """Test attempting handshake before connection is established."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = None
        manager.connected = False
        
        sent_payloads = []
        
        def capture_send(payload):
            sent_payloads.append(payload)
        
        manager.send_json = capture_send
        manager.send_handshake()
        
        # send_json should be called but will log error due to not connected
        # The send_json method checks connected status
        assert mock_logger.log.called
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("not connected" in msg.lower() for msg in logged_messages)

    def test_handshake_after_disconnection(self, mock_logger):
        """Test attempting handshake after connection is closed."""
        manager = WebSocketManager(logger=mock_logger)
        
        # Simulate connection then disconnection
        manager.ws_app = Mock()
        manager.connected = True
        
        manager.disconnect()
        
        # Try to send handshake - should fail
        manager.send_handshake()
        
        assert mock_logger.log.called

    def test_unicode_in_client_id(self, mock_logger):
        """Test handshake with unicode characters in clientId."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        unicode_id = "клиент_001_设备"
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload)
        
        manager.send_handshake(client_id=unicode_id)
        
        assert sent_payloads[0]["clientId"] == unicode_id
        # Verify JSON serialization works
        json_str = json.dumps(sent_payloads[0])
        assert isinstance(json_str, str)

    def test_handshake_payload_immutability(self, mock_logger):
        """Test that handshake payload creation doesn't modify external data."""
        manager = WebSocketManager(logger=mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        test_id = "test_device"
        sent_payloads = []
        manager.send_json = lambda payload: sent_payloads.append(payload.copy())
        
        manager.send_handshake(client_id=test_id)
        manager.send_handshake(client_id=test_id)
        
        # Both payloads should have independent timestamps
        # (though they might be very close)
        assert sent_payloads[0]["action"] == "handshake"
        assert sent_payloads[1]["action"] == "handshake"


# ============================================================================
# PYTEST CONFIGURATION / MARKERS
# ============================================================================


def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "edge_case: mark test as an edge case test"
    )


# Mark test classes with appropriate markers
pytest.mark.unit(TestHandshakePayloadValidation)
pytest.mark.unit(TestSendHandshakeMethod)
pytest.mark.unit(TestAutoHandshakeParameter)
pytest.mark.unit(TestDefaultCommandsIntegration)
pytest.mark.unit(TestLoggingIntegration)
pytest.mark.integration(TestConnectionFlow)
pytest.mark.integration(TestMessageTransmission)
pytest.mark.edge_case(TestEdgeCases)
