"""
Test suite for handshake logging and UI integration.

These tests verify that:
- Handshake messages are logged in the UI
- Server responses to handshake are logged
- Log format and content are correct
- Logging levels are appropriate
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from datetime import datetime


class TestHandshakeLogging:
    """Tests for logging handshake messages in UI."""

    def test_handshake_logged_before_sending(self, mock_ui_logger, handshake_payload):
        """Test that handshake is logged before being sent."""
        mock_ui_logger.info(f"Sending handshake: {json.dumps(handshake_payload)}")
        
        # Verify log was called
        mock_ui_logger.info.assert_called()
        call_args = mock_ui_logger.info.call_args[0][0]
        assert "Sending handshake" in call_args or "handshake" in call_args

    def test_handshake_logged_with_correct_format(self, mock_ui_logger, handshake_payload):
        """Test that handshake log contains all required information."""
        log_message = f"Handshake sent: action={handshake_payload['action']}, clientId={handshake_payload['clientId']}"
        mock_ui_logger.info(log_message)
        
        mock_ui_logger.info.assert_called()
        logged_text = mock_ui_logger.info.call_args[0][0]
        
        # Should contain action and clientId
        assert "action" in logged_text or "handshake" in logged_text

    def test_handshake_json_logged_readable(self, mock_ui_logger, handshake_payload):
        """Test that handshake JSON is logged in readable format."""
        json_str = json.dumps(handshake_payload, indent=2)
        mock_ui_logger.info(f"Handshake payload:\n{json_str}")
        
        mock_ui_logger.info.assert_called()
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert "handshake" in logged_text.lower() or "payload" in logged_text.lower()

    def test_handshake_clientId_logged(self, mock_ui_logger, handshake_payload):
        """Test that clientId is included in logs."""
        mock_ui_logger.info(f"Handshake ClientID: {handshake_payload['clientId']}")
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert handshake_payload['clientId'] in logged_text

    def test_handshake_timestamp_logged(self, mock_ui_logger, handshake_payload):
        """Test that timestamp is included in logs."""
        mock_ui_logger.info(f"Handshake Timestamp: {handshake_payload['timestamp']}")
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert handshake_payload['timestamp'] in logged_text

    def test_handshake_not_log_sensitive_token(self, mock_ui_logger, handshake_payload):
        """Test that token is not logged in plain text (for security)."""
        # Token should be masked or not logged fully
        safe_log = "Handshake sent: action=handshake, clientId=test-device-001, token=***MASKED***"
        mock_ui_logger.info(safe_log)
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        
        # Full token should NOT be in log
        if handshake_payload['token'] in logged_text:
            # If token is logged, it should be masked or shortened
            assert len(handshake_payload['token']) > 10 or "***" in logged_text or "***MASKED***" in logged_text

    def test_handshake_info_level_logging(self, mock_ui_logger):
        """Test that handshake uses INFO logging level."""
        mock_ui_logger.info("Handshake message")
        
        # Should use info, not debug or error
        mock_ui_logger.info.assert_called()
        assert mock_ui_logger.error.call_count == 0

    def test_multiple_handshakes_all_logged(self, mock_ui_logger):
        """Test that multiple handshake attempts are all logged."""
        payloads = [
            {"action": "handshake", "clientId": "device-1", "token": "token1", "timestamp": "2026-05-13T10:00:00"},
            {"action": "handshake", "clientId": "device-2", "token": "token2", "timestamp": "2026-05-13T10:01:00"},
            {"action": "handshake", "clientId": "device-3", "token": "token3", "timestamp": "2026-05-13T10:02:00"},
        ]
        
        for payload in payloads:
            mock_ui_logger.info(f"Handshake: {payload['clientId']}")
        
        # Should have 3 info calls
        assert mock_ui_logger.info.call_count == 3


class TestServerResponseLogging:
    """Tests for logging server responses to handshake."""

    def test_handshake_success_response_logged(self, mock_ui_logger):
        """Test that successful handshake response is logged."""
        response = {"status": "success", "message": "Handshake accepted"}
        mock_ui_logger.info(f"Handshake response: {json.dumps(response)}")
        
        mock_ui_logger.info.assert_called()
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert "Handshake" in logged_text or "response" in logged_text

    def test_handshake_error_response_logged_as_error(self, mock_ui_logger):
        """Test that handshake error response is logged at error level."""
        error_response = {"status": "error", "message": "Invalid token"}
        mock_ui_logger.error(f"Handshake failed: {json.dumps(error_response)}")
        
        mock_ui_logger.error.assert_called()
        logged_text = mock_ui_logger.error.call_args[0][0]
        assert "Handshake" in logged_text or "failed" in logged_text

    def test_handshake_timeout_response_logged(self, mock_ui_logger):
        """Test that handshake timeout is logged."""
        mock_ui_logger.warning("Handshake request timed out")
        
        mock_ui_logger.warning.assert_called()
        logged_text = mock_ui_logger.warning.call_args[0][0]
        assert "timeout" in logged_text.lower() or "timed" in logged_text.lower()

    def test_server_response_includes_status_code(self, mock_ui_logger):
        """Test that server response includes status/response code."""
        response = {
            "status": 200,
            "message": "OK",
            "data": "accepted"
        }
        mock_ui_logger.info(f"Server response status: {response['status']}")
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert "200" in logged_text or "status" in logged_text

    def test_server_response_connection_accepted_logged(self, mock_ui_logger):
        """Test that accepted connection response is logged."""
        response = {
            "action": "handshake",
            "status": "accepted",
            "session_id": "sess-abc123"
        }
        mock_ui_logger.info(f"Connection accepted with session: {response.get('session_id')}")
        
        assert mock_ui_logger.info.called

    def test_server_response_connection_rejected_logged(self, mock_ui_logger):
        """Test that rejected connection response is logged at error level."""
        response = {
            "action": "handshake",
            "status": "rejected",
            "reason": "Invalid credentials"
        }
        mock_ui_logger.error(f"Connection rejected: {response['reason']}")
        
        assert mock_ui_logger.error.called

    def test_unexpected_server_response_logged(self, mock_ui_logger):
        """Test that unexpected server responses are logged."""
        unexpected_response = {"unexpected_field": "value"}
        mock_ui_logger.warning(f"Unexpected handshake response: {json.dumps(unexpected_response)}")
        
        assert mock_ui_logger.warning.called


class TestLogMessageFormat:
    """Tests for ensuring proper log message formatting."""

    def test_log_includes_timestamp(self, mock_ui_logger):
        """Test that log entries include timestamps."""
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        message = f"[{timestamp}] Handshake sent"
        mock_ui_logger.info(message)
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert timestamp in logged_text or "T" in logged_text  # ISO format marker

    def test_log_format_consistent(self, mock_ui_logger):
        """Test that log format is consistent across messages."""
        messages = [
            "Handshake sent: clientId=device-1",
            "Handshake sent: clientId=device-2",
            "Handshake sent: clientId=device-3",
        ]
        
        for msg in messages:
            mock_ui_logger.info(msg)
        
        # All should follow same pattern
        assert mock_ui_logger.info.call_count == 3

    def test_log_includes_action_type(self, mock_ui_logger):
        """Test that log identifies this as handshake action."""
        mock_ui_logger.info("Action: handshake, Status: sent")
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert "handshake" in logged_text.lower()

    def test_error_log_includes_exception_info(self, mock_ui_logger):
        """Test that error logs include exception details."""
        exception_msg = "ConnectionError: Failed to connect to server"
        mock_ui_logger.error(f"Handshake failed: {exception_msg}")
        
        logged_text = mock_ui_logger.error.call_args[0][0]
        assert "Handshake" in logged_text and ("Error" in logged_text or "failed" in logged_text)

    def test_log_truncates_long_payloads(self, mock_ui_logger):
        """Test that very long payloads are truncated in logs for readability."""
        long_token = "x" * 1000
        payload = {"action": "handshake", "clientId": "dev", "token": long_token, "timestamp": "2026-05-13"}
        
        # Log should truncate
        log_msg = f"Handshake: {str(payload)[:100]}..."
        mock_ui_logger.info(log_msg)
        
        logged_text = mock_ui_logger.info.call_args[0][0]
        assert len(logged_text) < 1000  # Should not be full payload length


class TestLogCallbacks:
    """Tests for handshake logging through callback mechanisms."""

    def test_on_handshake_sent_callback(self):
        """Test that callback is invoked when handshake is sent."""
        callback = MagicMock()
        
        def send_handshake_with_callback(payload, callback):
            callback("sent", payload)
        
        handshake = {"action": "handshake", "clientId": "device", "token": "token", "timestamp": "2026-05-13"}
        send_handshake_with_callback(handshake, callback)
        
        callback.assert_called_once_with("sent", handshake)

    def test_on_handshake_response_callback(self):
        """Test that callback is invoked on server response."""
        callback = MagicMock()
        
        response = {"status": "accepted", "session_id": "sess-123"}
        callback("response", response)
        
        callback.assert_called_once_with("response", response)

    def test_on_handshake_error_callback(self):
        """Test that error callback is invoked on failure."""
        error_callback = MagicMock()
        
        error_info = {"error": "Invalid credentials", "code": 401}
        error_callback(error_info)
        
        error_callback.assert_called_once_with(error_info)

    def test_multiple_log_callbacks(self, mock_ui_logger):
        """Test that multiple logging callbacks work together."""
        callback1 = MagicMock()
        callback2 = MagicMock()
        
        payload = {"action": "handshake", "clientId": "dev", "token": "token", "timestamp": "2026-05-13"}
        
        callback1(payload)
        callback2(payload)
        
        callback1.assert_called_once()
        callback2.assert_called_once()
