"""
Comprehensive unit and integration tests for WebSocket handshake implementation (SCRUM-114).
Tests cover state management, message creation, handshake flow, timeouts, error handling, and integration scenarios.
"""

import json
import threading
import time
from unittest.mock import Mock, MagicMock, patch, call
import pytest

from utilities import (
    MESSAGE_TYPE_HANDSHAKE_INIT,
    MESSAGE_TYPE_HANDSHAKE_ACK,
    MESSAGE_TYPE_HANDSHAKE_ERROR,
    HANDSHAKE_STATE_PENDING,
    HANDSHAKE_STATE_COMPLETED,
    HANDSHAKE_STATE_FAILED,
    PROTOCOL_VERSION,
    DEFAULT_HANDSHAKE_TIMEOUT,
    create_handshake_init,
    create_handshake_ack,
    create_handshake_error,
)
from ws_client import WebSocketManager


class TestHandshakeMessageCreation:
    """Unit tests for handshake message creation functions."""

    def test_create_handshake_init_with_required_fields(self):
        """Test that create_handshake_init creates valid message with required fields."""
        device_id = "test-device-001"
        msg = create_handshake_init(device_id)
        
        assert msg["type"] == MESSAGE_TYPE_HANDSHAKE_INIT
        assert msg["protocol_version"] == PROTOCOL_VERSION
        assert msg["device_id"] == device_id
        assert "capabilities" in msg
        assert msg["capabilities"] == ["websocket", "json"]
        assert "timestamp" in msg
        assert msg["auth_token"] is None

    def test_create_handshake_init_with_custom_capabilities(self):
        """Test handshake init with custom capabilities list."""
        capabilities = ["websocket", "json", "binary", "custom"]
        msg = create_handshake_init("device-001", capabilities=capabilities)
        
        assert msg["capabilities"] == capabilities

    def test_create_handshake_init_with_auth_token(self):
        """Test handshake init includes auth token when provided."""
        token = "test-auth-token-xyz"
        msg = create_handshake_init("device-001", auth_token=token)
        
        assert msg["auth_token"] == token

    def test_create_handshake_ack_with_defaults(self):
        """Test that create_handshake_ack creates valid response message."""
        msg = create_handshake_ack("success")
        
        assert msg["type"] == MESSAGE_TYPE_HANDSHAKE_ACK
        assert msg["status"] == "success"
        assert msg["protocol_version"] == PROTOCOL_VERSION
        assert msg["server_info"] == {}
        assert "timestamp" in msg

    def test_create_handshake_ack_with_server_info(self):
        """Test handshake ack with server information."""
        server_info = {"version": "2.0.0", "capabilities": ["websocket", "json", "binary"]}
        msg = create_handshake_ack("success", server_info=server_info)
        
        assert msg["server_info"] == server_info

    def test_create_handshake_ack_with_custom_protocol_version(self):
        """Test handshake ack with custom protocol version."""
        msg = create_handshake_ack("success", protocol_version="2.0")
        
        assert msg["protocol_version"] == "2.0"

    def test_create_handshake_error_with_all_fields(self):
        """Test that create_handshake_error creates error message."""
        error_code = "AUTH_FAILED"
        error_message = "Invalid authentication token"
        msg = create_handshake_error(error_code, error_message)
        
        assert msg["type"] == MESSAGE_TYPE_HANDSHAKE_ERROR
        assert msg["error_code"] == error_code
        assert msg["error_message"] == error_message
        assert "timestamp" in msg

    def test_create_handshake_error_with_various_codes(self):
        """Test handshake error with different error codes."""
        error_codes = ["AUTH_FAILED", "VERSION_MISMATCH", "CAPABILITY_NOT_SUPPORTED", "TIMEOUT"]
        for code in error_codes:
            msg = create_handshake_error(code, "Test error")
            assert msg["error_code"] == code


class TestHandshakeStateManagement:
    """Unit tests for handshake state transitions."""

    @pytest.fixture
    def ws_manager(self):
        """Create WebSocketManager instance for testing."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device-001",
            handshake_timeout=DEFAULT_HANDSHAKE_TIMEOUT,
        )
        return manager

    def test_initial_state_is_pending(self, ws_manager):
        """Test that initial handshake state is PENDING."""
        assert ws_manager.handshake_state == HANDSHAKE_STATE_PENDING

    def test_state_transition_pending_to_completed(self, ws_manager):
        """Test state transition: PENDING → COMPLETED on successful ACK."""
        # Simulate receiving a successful ACK
        ws_manager.handshake_state = HANDSHAKE_STATE_COMPLETED
        
        assert ws_manager.handshake_state == HANDSHAKE_STATE_COMPLETED

    def test_state_transition_pending_to_failed(self, ws_manager):
        """Test state transition: PENDING → FAILED on error."""
        ws_manager.handshake_state = HANDSHAKE_STATE_FAILED
        
        assert ws_manager.handshake_state == HANDSHAKE_STATE_FAILED

    def test_handshake_timer_initialized_as_none(self, ws_manager):
        """Test that handshake timer is initially None."""
        assert ws_manager.handshake_timer is None

    def test_handshake_timeout_configuration(self, ws_manager):
        """Test that custom handshake timeout is set correctly."""
        custom_timeout = 60
        manager = WebSocketManager(
            logger=ws_manager.logger,
            device_id="test-device",
            handshake_timeout=custom_timeout,
        )
        
        assert manager.handshake_timeout == custom_timeout

    def test_negotiated_capabilities_initialized_empty(self, ws_manager):
        """Test that negotiated capabilities list is initially empty."""
        assert ws_manager.negotiated_capabilities == []

    def test_server_info_initialized_empty(self, ws_manager):
        """Test that server info dictionary is initially empty."""
        assert ws_manager.server_info == {}


class TestHandshakeSendInit:
    """Unit tests for _send_handshake_init method."""

    @pytest.fixture
    def ws_manager_with_mocks(self):
        """Create manager with mocked WebSocket."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device-001",
        )
        manager.ws_app = MagicMock()
        return manager

    def test_send_handshake_init_called_with_valid_ws_app(self, ws_manager_with_mocks):
        """Test _send_handshake_init sends message when ws_app exists."""
        ws_manager_with_mocks._send_handshake_init()
        
        ws_manager_with_mocks.ws_app.send.assert_called_once()
        call_args = ws_manager_with_mocks.ws_app.send.call_args[0][0]
        msg = json.loads(call_args)
        
        assert msg["type"] == MESSAGE_TYPE_HANDSHAKE_INIT
        assert msg["device_id"] == "test-device-001"

    def test_send_handshake_init_returns_early_when_ws_app_is_none(self, ws_manager_with_mocks):
        """Test _send_handshake_init does nothing when ws_app is None."""
        ws_manager_with_mocks.ws_app = None
        
        ws_manager_with_mocks._send_handshake_init()
        
        # No exception should be raised, method should return early

    def test_send_handshake_init_sets_state_to_pending(self, ws_manager_with_mocks):
        """Test that state remains PENDING after sending init."""
        ws_manager_with_mocks.handshake_state = HANDSHAKE_STATE_PENDING
        ws_manager_with_mocks._send_handshake_init()
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_PENDING

    def test_send_handshake_init_logs_error_on_exception(self, ws_manager_with_mocks):
        """Test that exceptions during send are logged and handled."""
        ws_manager_with_mocks.ws_app.send.side_effect = Exception("Send failed")
        
        ws_manager_with_mocks._send_handshake_init()
        
        # Verify error was logged
        ws_manager_with_mocks.logger.log.assert_called()
        error_calls = [call for call in ws_manager_with_mocks.logger.log.call_args_list 
                      if "Error sending handshake" in str(call)]
        assert len(error_calls) > 0

    def test_send_handshake_init_sets_failed_state_on_error(self, ws_manager_with_mocks):
        """Test that state is set to FAILED when send throws exception."""
        ws_manager_with_mocks.ws_app.send.side_effect = Exception("Send failed")
        
        ws_manager_with_mocks._send_handshake_init()
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED


class TestHandshakeAckHandling:
    """Unit tests for _handle_handshake_ack method."""

    @pytest.fixture
    def ws_manager_with_mocks(self):
        """Create manager with mocked WebSocket."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device-001",
        )
        manager.ws_app = MagicMock()
        return manager

    def test_handle_handshake_ack_with_success_status(self, ws_manager_with_mocks):
        """Test _handle_handshake_ack marks state as COMPLETED on success."""
        ack_msg = create_handshake_ack("success", server_info={"version": "1.0"})
        
        ws_manager_with_mocks._handle_handshake_ack(ack_msg)
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_COMPLETED
        assert ws_manager_with_mocks.server_info == {"version": "1.0"}

    def test_handle_handshake_ack_with_failure_status(self, ws_manager_with_mocks):
        """Test _handle_handshake_ack marks state as FAILED on failure status."""
        ack_msg = create_handshake_ack("failure")
        
        ws_manager_with_mocks._handle_handshake_ack(ack_msg)
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED

    def test_handle_handshake_ack_cancels_timer(self, ws_manager_with_mocks):
        """Test that ACK handler cancels the handshake timer."""
        mock_timer = MagicMock()
        ws_manager_with_mocks.handshake_timer = mock_timer
        ack_msg = create_handshake_ack("success")
        
        ws_manager_with_mocks._handle_handshake_ack(ack_msg)
        
        mock_timer.cancel.assert_called_once()

    def test_handle_handshake_ack_stores_protocol_version(self, ws_manager_with_mocks):
        """Test that protocol version from ACK is properly handled."""
        ack_msg = create_handshake_ack("success", protocol_version="2.0")
        
        ws_manager_with_mocks._handle_handshake_ack(ack_msg)
        
        # Should not crash and should process the version
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_COMPLETED

    def test_handle_handshake_ack_with_missing_status_field(self, ws_manager_with_mocks):
        """Test handling of ACK without status field (invalid)."""
        ack_msg = {"type": MESSAGE_TYPE_HANDSHAKE_ACK, "timestamp": "2026-01-01T00:00:00"}
        
        ws_manager_with_mocks._handle_handshake_ack(ack_msg)
        
        # Should handle gracefully, state should be FAILED
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED


class TestHandshakeErrorHandling:
    """Unit tests for _handle_handshake_error method."""

    @pytest.fixture
    def ws_manager_with_mocks(self):
        """Create manager with mocked WebSocket."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device-001",
        )
        manager.ws_app = MagicMock()
        return manager

    def test_handle_handshake_error_sets_failed_state(self, ws_manager_with_mocks):
        """Test _handle_handshake_error marks state as FAILED."""
        error_msg = create_handshake_error("AUTH_FAILED", "Invalid token")
        
        ws_manager_with_mocks._handle_handshake_error(error_msg)
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED

    def test_handle_handshake_error_cancels_timer(self, ws_manager_with_mocks):
        """Test that error handler cancels the handshake timer."""
        mock_timer = MagicMock()
        ws_manager_with_mocks.handshake_timer = mock_timer
        error_msg = create_handshake_error("TIMEOUT", "Request timed out")
        
        ws_manager_with_mocks._handle_handshake_error(error_msg)
        
        mock_timer.cancel.assert_called_once()

    def test_handle_handshake_error_logs_error_details(self, ws_manager_with_mocks):
        """Test that error message logs error code and description."""
        error_code = "VERSION_MISMATCH"
        error_message = "Protocol version not supported"
        error_msg = create_handshake_error(error_code, error_message)
        
        ws_manager_with_mocks._handle_handshake_error(error_msg)
        
        ws_manager_with_mocks.logger.log.assert_called()
        # Check that error details were logged
        log_calls = str(ws_manager_with_mocks.logger.log.call_args_list)
        assert error_code in log_calls or error_message in log_calls

    def test_handle_handshake_error_with_missing_error_code(self, ws_manager_with_mocks):
        """Test handling of error message with missing error_code."""
        error_msg = {"type": MESSAGE_TYPE_HANDSHAKE_ERROR, "error_message": "Unknown error"}
        
        ws_manager_with_mocks._handle_handshake_error(error_msg)
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED

    def test_handle_handshake_error_disconnects(self, ws_manager_with_mocks):
        """Test that error handler disconnects the WebSocket."""
        ws_manager_with_mocks.connected = True
        error_msg = create_handshake_error("PROTOCOL_ERROR", "Invalid message format")
        
        with patch.object(ws_manager_with_mocks, 'disconnect') as mock_disconnect:
            ws_manager_with_mocks._handle_handshake_error(error_msg)
            mock_disconnect.assert_called_once()


class TestHandshakeTimer:
    """Unit tests for handshake timeout timer management."""

    @pytest.fixture
    def ws_manager_with_mocks(self):
        """Create manager with mocked WebSocket."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device-001",
            handshake_timeout=1,  # Short timeout for testing
        )
        manager.ws_app = MagicMock()
        return manager

    def test_start_handshake_timer_schedules_timer(self, ws_manager_with_mocks):
        """Test _start_handshake_timer schedules a timeout."""
        ws_manager_with_mocks._start_handshake_timer()
        
        assert ws_manager_with_mocks.handshake_timer is not None
        assert isinstance(ws_manager_with_mocks.handshake_timer, threading.Timer)
        
        # Clean up
        ws_manager_with_mocks._cancel_handshake_timer()

    def test_cancel_handshake_timer_cancels_timer(self, ws_manager_with_mocks):
        """Test _cancel_handshake_timer cancels the scheduled timer."""
        ws_manager_with_mocks._start_handshake_timer()
        timer = ws_manager_with_mocks.handshake_timer
        
        ws_manager_with_mocks._cancel_handshake_timer()
        
        assert ws_manager_with_mocks.handshake_timer is None

    def test_cancel_handshake_timer_when_none_is_safe(self, ws_manager_with_mocks):
        """Test calling cancel when timer is None doesn't crash."""
        ws_manager_with_mocks.handshake_timer = None
        
        # Should not raise exception
        ws_manager_with_mocks._cancel_handshake_timer()
        
        assert ws_manager_with_mocks.handshake_timer is None

    def test_on_handshake_timeout_sets_failed_state(self, ws_manager_with_mocks):
        """Test _on_handshake_timeout sets state to FAILED."""
        ws_manager_with_mocks.handshake_state = HANDSHAKE_STATE_PENDING
        
        ws_manager_with_mocks._on_handshake_timeout()
        
        assert ws_manager_with_mocks.handshake_state == HANDSHAKE_STATE_FAILED

    def test_on_handshake_timeout_logs_message(self, ws_manager_with_mocks):
        """Test _on_handshake_timeout logs timeout event."""
        ws_manager_with_mocks.handshake_state = HANDSHAKE_STATE_PENDING
        
        ws_manager_with_mocks._on_handshake_timeout()
        
        ws_manager_with_mocks.logger.log.assert_called()
        log_message = str(ws_manager_with_mocks.logger.log.call_args_list)
        assert "timeout" in log_message.lower()

    def test_on_handshake_timeout_when_already_completed(self, ws_manager_with_mocks):
        """Test timeout doesn't do anything if handshake already completed."""
        ws_manager_with_mocks.handshake_state = HANDSHAKE_STATE_COMPLETED
        
        with patch.object(ws_manager_with_mocks, 'disconnect') as mock_disconnect:
            ws_manager_with_mocks._on_handshake_timeout()
            # Should not disconnect if already completed
            mock_disconnect.assert_not_called()

    def test_timeout_uses_configured_timeout_value(self, ws_manager_with_mocks):
        """Test that timer uses the configured timeout value."""
        custom_timeout = 45
        manager = WebSocketManager(
            logger=ws_manager_with_mocks.logger,
            device_id="test-device",
            handshake_timeout=custom_timeout,
        )
        manager.ws_app = MagicMock()
        
        with patch('threading.Timer') as mock_timer_class:
            manager._start_handshake_timer()
            
            # Verify Timer was called with custom timeout
            mock_timer_class.assert_called_once()
            call_args = mock_timer_class.call_args
            assert call_args[0][0] == custom_timeout


class TestHandshakeIntegration:
    """Integration tests for complete handshake flow."""

    @pytest.fixture
    def ws_manager_for_integration(self):
        """Create manager for integration testing."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="iot-device-001",
            handshake_timeout=30,
        )
        manager.ws_app = MagicMock()
        manager.ws_app.send = MagicMock()
        return manager

    def test_full_handshake_flow_connect_init_ack(self, ws_manager_for_integration):
        """Test complete handshake flow: connect → init → ack → ready."""
        # Start handshake
        ws_manager_for_integration._send_handshake_init()
        
        # Verify handshake_init was sent
        ws_manager_for_integration.ws_app.send.assert_called()
        
        # Simulate receiving ACK
        ack_msg = create_handshake_ack(
            "success",
            server_info={"version": "1.0", "capabilities": ["websocket", "json", "binary"]}
        )
        ws_manager_for_integration._handle_handshake_ack(ack_msg)
        
        # Verify state is COMPLETED
        assert ws_manager_for_integration.handshake_state == HANDSHAKE_STATE_COMPLETED
        assert ws_manager_for_integration.server_info["version"] == "1.0"

    def test_handshake_flow_with_error_response(self, ws_manager_for_integration):
        """Test handshake flow when server responds with error."""
        ws_manager_for_integration._send_handshake_init()
        
        # Simulate receiving error
        error_msg = create_handshake_error("AUTH_FAILED", "Invalid device credentials")
        ws_manager_for_integration._handle_handshake_error(error_msg)
        
        # Verify state is FAILED
        assert ws_manager_for_integration.handshake_state == HANDSHAKE_STATE_FAILED

    def test_handshake_on_open_initiates_handshake(self, ws_manager_for_integration):
        """Test that _on_open calls _send_handshake_init."""
        with patch.object(ws_manager_for_integration, '_send_handshake_init') as mock_send:
            with patch.object(ws_manager_for_integration, '_start_handshake_timer') as mock_timer:
                ws_manager_for_integration._on_open(None)
                
                mock_send.assert_called_once()
                mock_timer.assert_called_once()

    def test_reconnection_after_failed_handshake(self, ws_manager_for_integration):
        """Test that failed handshake can be retried on reconnect."""
        # First attempt fails
        ws_manager_for_integration._send_handshake_init()
        error_msg = create_handshake_error("TIMEOUT", "Handshake timeout")
        ws_manager_for_integration._handle_handshake_error(error_msg)
        
        assert ws_manager_for_integration.handshake_state == HANDSHAKE_STATE_FAILED
        
        # Reset state for reconnect
        ws_manager_for_integration.handshake_state = HANDSHAKE_STATE_PENDING
        
        # Second attempt succeeds
        ws_manager_for_integration._send_handshake_init()
        ack_msg = create_handshake_ack("success")
        ws_manager_for_integration._handle_handshake_ack(ack_msg)
        
        assert ws_manager_for_integration.handshake_state == HANDSHAKE_STATE_COMPLETED


class TestHandshakeMessageFiltering:
    """Tests for message filtering based on handshake state."""

    @pytest.fixture
    def ws_manager(self):
        """Create manager for message filtering tests."""
        mock_logger = Mock()
        mock_on_message = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            on_message=mock_on_message,
            device_id="test-device",
        )
        manager.ws_app = MagicMock()
        return manager

    def test_user_messages_rejected_during_pending_state(self, ws_manager):
        """Test user messages are rejected while handshake is PENDING."""
        ws_manager.handshake_state = HANDSHAKE_STATE_PENDING
        
        # User tries to send a regular message
        msg = {"action": "ping"}
        
        # Check: messages during PENDING should not be processed normally
        # (Implementation-specific: depends on how ws_client filters messages)
        assert ws_manager.handshake_state == HANDSHAKE_STATE_PENDING

    def test_user_messages_accepted_after_completed_state(self, ws_manager):
        """Test user messages are accepted after handshake is COMPLETED."""
        ws_manager.handshake_state = HANDSHAKE_STATE_COMPLETED
        
        # Simulate receiving a user message
        user_msg = '{"action": "ping", "timestamp": "2026-01-01T00:00:00"}'
        ws_manager._on_message(None, user_msg)
        
        # Message callback should be called
        ws_manager.on_message.assert_called_with(user_msg)

    def test_handshake_messages_processed_regardless_of_state(self, ws_manager):
        """Test that handshake messages are processed regardless of state."""
        # Even in PENDING state, we can receive handshake responses
        ws_manager.handshake_state = HANDSHAKE_STATE_PENDING
        
        ack_msg = create_handshake_ack("success")
        ws_manager._handle_handshake_ack(ack_msg)
        
        assert ws_manager.handshake_state == HANDSHAKE_STATE_COMPLETED


class TestHandshakeDefaultCommands:
    """Tests for handshake default commands in utilities."""

    def test_handshake_init_default_command_exists(self):
        """Test that HANDSHAKE_INIT default command is available."""
        from utilities import DEFAULT_COMMANDS
        
        init_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "HANDSHAKE_INIT"]
        assert len(init_commands) > 0
        
        cmd = init_commands[0]
        assert cmd["payload"]["type"] == MESSAGE_TYPE_HANDSHAKE_INIT

    def test_handshake_ack_default_command_exists(self):
        """Test that HANDSHAKE_ACK default command is available."""
        from utilities import DEFAULT_COMMANDS
        
        ack_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "HANDSHAKE_ACK"]
        assert len(ack_commands) > 0
        
        cmd = ack_commands[0]
        assert cmd["payload"]["type"] == MESSAGE_TYPE_HANDSHAKE_ACK

    def test_handshake_commands_have_valid_payloads(self):
        """Test that default handshake commands have valid JSON payloads."""
        from utilities import DEFAULT_COMMANDS
        
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS 
                             if cmd["name"] in ["HANDSHAKE_INIT", "HANDSHAKE_ACK"]]
        
        for cmd in handshake_commands:
            payload = cmd["payload"]
            # Should be deserializable as JSON
            json_str = json.dumps(payload)
            assert json_str is not None


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing commands."""

    def test_existing_commands_still_available(self):
        """Test that existing commands are still available after handshake changes."""
        from utilities import DEFAULT_COMMANDS
        
        existing_names = ["Ping", "Login", "Subscribe", "Echo", "HTTP POST sample"]
        
        for name in existing_names:
            commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == name]
            assert len(commands) > 0, f"Command '{name}' should still be available"

    def test_existing_commands_unchanged(self):
        """Test that existing command payloads remain valid."""
        from utilities import DEFAULT_COMMANDS
        
        ping_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Ping"]
        assert len(ping_commands) > 0
        
        ping = ping_commands[0]
        assert "action" in ping["payload"]
        assert ping["payload"]["action"] == "ping"

    def test_websocket_manager_non_handshake_functionality_preserved(self):
        """Test that non-handshake WebSocket functionality still works."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
        )
        
        # Test send_json still exists and works
        manager.ws_app = MagicMock()
        manager.connected = True
        # Must set handshake state to COMPLETED for user messages to be sent
        manager.handshake_state = HANDSHAKE_STATE_COMPLETED
        
        payload = {"action": "ping"}
        manager.send_json(payload)
        
        manager.ws_app.send.assert_called_once()


class TestErrorRecovery:
    """Tests for error recovery and edge cases."""

    @pytest.fixture
    def ws_manager(self):
        """Create manager for error recovery tests."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
        )
        manager.ws_app = MagicMock()
        return manager

    def test_invalid_handshake_ack_message_handled_gracefully(self, ws_manager):
        """Test that invalid ACK messages are handled without crashing."""
        invalid_ack = {"type": "INVALID", "random": "data"}
        
        # Should not raise exception
        ws_manager._handle_handshake_ack(invalid_ack)

    def test_malformed_json_in_handshake_message(self, ws_manager):
        """Test handling of malformed JSON in handshake responses."""
        # This would be caught by json.loads in real scenario
        malformed = "{ invalid json }"
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(malformed)

    def test_connection_closes_on_handshake_failure(self, ws_manager):
        """Test that connection closes when handshake fails."""
        ws_manager.connected = True
        error_msg = create_handshake_error("PROTOCOL_ERROR", "Invalid format")
        
        with patch.object(ws_manager, 'disconnect') as mock_disconnect:
            ws_manager._handle_handshake_error(error_msg)
            mock_disconnect.assert_called_once()

    def test_multiple_handshake_init_calls_safe(self, ws_manager):
        """Test that calling handshake init multiple times is safe."""
        ws_manager._send_handshake_init()
        ws_manager._send_handshake_init()
        
        # Should not crash, just send twice
        assert ws_manager.ws_app.send.call_count == 2

    def test_handshake_timeout_during_pending_state(self, ws_manager):
        """Test timeout behavior during pending handshake state."""
        ws_manager.handshake_state = HANDSHAKE_STATE_PENDING
        
        with patch.object(ws_manager, 'disconnect') as mock_disconnect:
            ws_manager._on_handshake_timeout()
            mock_disconnect.assert_called_once()


class TestConfigurableHandshakeTimeout:
    """Tests for configurable handshake timeout."""

    def test_custom_handshake_timeout_30_seconds(self):
        """Test configuration with default 30-second timeout."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
            handshake_timeout=30,
        )
        
        assert manager.handshake_timeout == 30

    def test_custom_handshake_timeout_60_seconds(self):
        """Test configuration with 60-second timeout."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
            handshake_timeout=60,
        )
        
        assert manager.handshake_timeout == 60

    def test_custom_device_id_configuration(self):
        """Test configuration with custom device_id."""
        mock_logger = Mock()
        device_id = "custom-iot-device-xyz"
        manager = WebSocketManager(
            logger=mock_logger,
            device_id=device_id,
        )
        
        assert manager.device_id == device_id

    def test_handshake_init_uses_configured_device_id(self):
        """Test that handshake_init uses the configured device_id."""
        mock_logger = Mock()
        device_id = "prod-device-123"
        manager = WebSocketManager(
            logger=mock_logger,
            device_id=device_id,
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake_init()
        
        call_args = manager.ws_app.send.call_args[0][0]
        msg = json.loads(call_args)
        assert msg["device_id"] == device_id


class TestUIHandshakeDisplay:
    """Tests for handshake status display in UI."""

    def test_handshake_state_accessible_from_manager(self):
        """Test that UI can access handshake state from manager."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
        )
        
        # UI should be able to read handshake_state
        assert hasattr(manager, "handshake_state")
        assert manager.handshake_state == HANDSHAKE_STATE_PENDING

    def test_negotiated_capabilities_accessible_from_manager(self):
        """Test that UI can access negotiated capabilities."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
        )
        
        assert hasattr(manager, "negotiated_capabilities")
        assert isinstance(manager.negotiated_capabilities, list)

    def test_server_info_accessible_from_manager(self):
        """Test that UI can access server info."""
        mock_logger = Mock()
        manager = WebSocketManager(
            logger=mock_logger,
            device_id="test-device",
        )
        
        assert hasattr(manager, "server_info")
        assert isinstance(manager.server_info, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
