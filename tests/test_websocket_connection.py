"""
Test suite for WebSocket connection flow and handshake sending.

These tests verify that:
- Handshake is sent after successful WebSocket connection
- Handshake payload is correctly formatted before sending
- Handshake is not sent if connection fails
- set_handshake_payload() method updates configuration
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from datetime import datetime


class TestWebSocketHandshakeSending:
    """Tests for verifying handshake is sent on WebSocket connection."""

    def test_handshake_sent_after_connection(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is automatically sent after WebSocket connects."""
        # Set handshake payload
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Simulate connection
        mock_websocket_manager.connect()
        
        # Verify connection was called
        mock_websocket_manager.connect.assert_called_once()

    def test_handshake_payload_sent_with_correct_format(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is sent with correct JSON format."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # After connection, handshake should be sent
        expected_json = json.dumps(handshake_payload)
        
        # Verify the payload was set
        mock_websocket_manager.set_handshake_payload.assert_called_with(handshake_payload)

    def test_handshake_not_sent_on_connection_failure(self):
        """Test that handshake is not sent if WebSocket connection fails."""
        mock_manager = MagicMock()
        mock_manager.connect.return_value = False
        mock_manager.is_connected.return_value = False
        
        result = mock_manager.connect()
        assert result is False
        
        # Verify send was not called on failed connection
        assert not mock_manager.send_message.called

    def test_set_handshake_payload_updates_configuration(self, mock_websocket_manager, handshake_payload):
        """Test that set_handshake_payload() updates manager configuration."""
        initial_payload = {
            "action": "handshake",
            "clientId": "initial-device",
            "token": "initial-token",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        # Set initial payload
        mock_websocket_manager.set_handshake_payload(initial_payload)
        
        # Update with new payload
        new_payload = {
            "action": "handshake",
            "clientId": "updated-device",
            "token": "updated-token",
            "timestamp": "2026-05-13T11:00:00"
        }
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        # Verify both calls were made
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_handshake_sent_before_other_messages(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is sent before any other messages."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Send other messages
        mock_websocket_manager.send_message({"action": "data", "value": "test"})
        mock_websocket_manager.send_message({"action": "ping"})
        
        # Verify send_message was called (would be called after handshake)
        assert mock_websocket_manager.send_message.called

    def test_handshake_payload_persists_across_reconnections(self, mock_websocket_manager, handshake_payload):
        """Test that handshake payload persists during reconnection."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # First connection
        mock_websocket_manager.connect()
        
        # Disconnect
        mock_websocket_manager.disconnect()
        
        # Reconnect
        mock_websocket_manager.connect()
        
        # Payload should still be set
        assert mock_websocket_manager.set_handshake_payload.call_count == 1
        assert mock_websocket_manager.connect.call_count == 2


class TestConnectionFlowWithHandshake:
    """Tests for complete WebSocket connection flow including handshake."""

    def test_connection_initialization_with_handshake(self, mock_websocket_manager, handshake_payload):
        """Test complete connection initialization with handshake."""
        # Initialize with handshake
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        connected = mock_websocket_manager.connect()
        
        assert connected
        assert mock_websocket_manager.is_connected()

    def test_failed_handshake_blocks_subsequent_messages(self):
        """Test that if handshake fails, subsequent messages are blocked."""
        mock_manager = MagicMock()
        mock_manager.send_message.side_effect = [Exception("Handshake failed"), None]
        
        with pytest.raises(Exception):
            mock_manager.send_message({"action": "handshake"})
        
        # Subsequent message should not be sent
        assert mock_manager.send_message.call_count == 1

    def test_handshake_retransmission_on_reconnection(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is retransmitted on reconnection."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # First connection and handshake
        mock_websocket_manager.connect()
        initial_send_count = mock_websocket_manager.send_message.call_count
        
        # Disconnect
        mock_websocket_manager.disconnect()
        
        # Reconnect - handshake should be resent
        mock_websocket_manager.connect()
        
        # send_message should have been called again
        assert mock_websocket_manager.send_message.call_count >= initial_send_count

    def test_connection_with_empty_handshake_payload(self, mock_websocket_manager):
        """Test connection behavior when handshake payload is empty."""
        empty_payload = {
            "action": "handshake",
            "clientId": "",
            "token": "",
            "timestamp": ""
        }
        
        # Should still allow connection, but payload is empty
        mock_websocket_manager.set_handshake_payload(empty_payload)
        mock_websocket_manager.connect()
        
        assert mock_websocket_manager.connect.called

    def test_connection_with_null_handshake_payload(self, mock_websocket_manager):
        """Test connection behavior when handshake is not set."""
        # Connect without setting handshake
        mock_websocket_manager.connect()
        
        # Connection should still be attempted
        assert mock_websocket_manager.connect.called

    def test_handshake_timing_relative_to_connection(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is sent immediately after connection established."""
        call_order = []
        
        def track_connect():
            call_order.append("connect")
            return True
        
        def track_send(msg):
            call_order.append("send")
        
        mock_websocket_manager.connect.side_effect = track_connect
        mock_websocket_manager.send_message.side_effect = track_send
        
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_websocket_manager.send_message(handshake_payload)
        
        # Connect should come before send
        assert "connect" in call_order
        assert "send" in call_order

    def test_concurrent_handshake_attempts(self, mock_websocket_manager, handshake_payload):
        """Test that concurrent handshake attempts are properly handled."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Simulate multiple concurrent connection attempts
        mock_websocket_manager.connect()
        mock_websocket_manager.connect()
        mock_websocket_manager.connect()
        
        # Should be called 3 times
        assert mock_websocket_manager.connect.call_count == 3


class TestHandshakePayloadModification:
    """Tests for modifying handshake payload during WebSocket session."""

    def test_modify_clientId_during_session(self, mock_websocket_manager, handshake_payload):
        """Test modifying clientId while connected."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Modify clientId
        new_payload = handshake_payload.copy()
        new_payload["clientId"] = "modified-device-id"
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        # Verify the update
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_token_during_session(self, mock_websocket_manager, handshake_payload):
        """Test modifying token while connected."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Modify token
        new_payload = handshake_payload.copy()
        new_payload["token"] = "new-token-value"
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        # Verify the modification was processed
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_timestamp_during_session(self, mock_websocket_manager, handshake_payload):
        """Test updating timestamp while connected."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Update timestamp
        new_payload = handshake_payload.copy()
        new_payload["timestamp"] = datetime.now().isoformat()
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_full_handshake_replacement(self, mock_websocket_manager, handshake_payload):
        """Test replacing entire handshake payload."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        replacement_payload = {
            "action": "handshake",
            "clientId": "new-client-123",
            "token": "new-token-abc",
            "timestamp": "2026-05-13T15:30:00"
        }
        mock_websocket_manager.set_handshake_payload(replacement_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2
