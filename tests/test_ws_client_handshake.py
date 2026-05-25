"""
Unit tests for WebSocket handshake functionality (SCRUM-53).

Tests the _send_handshake() method and its integration with _on_open().
"""

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from ws_client import WebSocketManager


class TestWebSocketHandshakeSend(TestCase):
    """Test _send_handshake() method functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        # Mock the WebSocketApp
        self.ws_manager.ws_app = MagicMock()
        self.ws_manager.connected = True

    def test_handshake_payload_structure(self) -> None:
        """Test that _send_handshake() constructs correct JSON payload."""
        self.ws_manager._send_handshake()

        # Verify ws_app.send was called once
        self.ws_manager.ws_app.send.assert_called_once()
        
        # Extract the payload that was sent
        sent_payload_str = self.ws_manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)

        # Verify payload structure
        self.assertEqual(sent_payload["action"], "handshake")
        self.assertEqual(sent_payload["clientId"], "test-device-001")
        self.assertIn("capabilities", sent_payload)
        self.assertEqual(sent_payload["capabilities"], {})
        self.assertEqual(sent_payload["version"], "1.0")

    def test_handshake_uses_client_id_parameter(self) -> None:
        """Test that _send_handshake() uses the correct client_id value."""
        # Create manager with specific client_id
        custom_client_id = "device-custom-123"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=custom_client_id
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()

        sent_payload_str = manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)
        
        self.assertEqual(sent_payload["clientId"], custom_client_id)

    def test_handshake_default_client_id(self) -> None:
        """Test that _send_handshake() uses default client_id when not specified."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()

        sent_payload_str = manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)
        
        self.assertEqual(sent_payload["clientId"], "device-001")

    def test_handshake_logs_success_message(self) -> None:
        """Test that _send_handshake() logs success message when payload is sent."""
        self.ws_manager._send_handshake()

        # Verify logger was called with success message
        self.logger.log.assert_called_once()
        log_message = self.logger.log.call_args[0][0]
        
        self.assertIn("handshake", log_message.lower())
        self.assertIn("sent", log_message.lower())

    def test_handshake_logs_error_on_exception(self) -> None:
        """Test that _send_handshake() logs error message if sending fails."""
        # Make ws_app.send raise an exception
        self.ws_manager.ws_app.send.side_effect = Exception("Send failed")
        
        self.ws_manager._send_handshake()

        # Verify logger was called with error message
        self.logger.log.assert_called_once()
        log_message = self.logger.log.call_args[0][0]
        
        self.assertIn("error", log_message.lower())
        self.assertIn("handshake", log_message.lower())

    def test_handshake_json_validity(self) -> None:
        """Test that handshake payload produces valid JSON."""
        self.ws_manager._send_handshake()

        sent_payload_str = self.ws_manager.ws_app.send.call_args[0][0]
        
        # Should not raise json.JSONDecodeError
        try:
            json.loads(sent_payload_str)
        except json.JSONDecodeError:
            self.fail("Handshake payload is not valid JSON")

    def test_handshake_with_ws_app_none(self) -> None:
        """Test that _send_handshake() handles None ws_app gracefully."""
        self.ws_manager.ws_app = None
        
        # Should not raise an exception
        try:
            self.ws_manager._send_handshake()
        except AttributeError:
            self.fail("_send_handshake() should handle None ws_app")
        
        # Should log error
        self.logger.log.assert_called_once()
        log_message = self.logger.log.call_args[0][0]
        self.assertIn("error", log_message.lower())

    def test_handshake_payload_is_json_string(self) -> None:
        """Test that the payload sent to ws_app.send is a JSON string."""
        self.ws_manager._send_handshake()

        sent_payload_str = self.ws_manager.ws_app.send.call_args[0][0]
        
        # Verify it's a string
        self.assertIsInstance(sent_payload_str, str)
        
        # Verify it's valid JSON
        parsed = json.loads(sent_payload_str)
        self.assertIsInstance(parsed, dict)


class TestWebSocketHandshakeOnOpen(TestCase):
    """Test _send_handshake() integration with _on_open()."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        self.ws_manager.ws_app = MagicMock()

    def test_handshake_called_on_open(self) -> None:
        """Test that _send_handshake() is called when _on_open() is triggered."""
        with patch.object(self.ws_manager, '_send_handshake') as mock_handshake:
            self.ws_manager._on_open(self.ws_manager.ws_app)
            
            # Verify _send_handshake was called
            mock_handshake.assert_called_once()

    def test_on_open_sets_connected_true_before_handshake(self) -> None:
        """Test that _on_open() sets connected=True and triggers handshake."""
        self.ws_manager._on_open(self.ws_manager.ws_app)
        
        # Verify connected flag is set
        self.assertTrue(self.ws_manager.connected)
        
        # Verify handshake was sent (ws_app.send was called)
        self.ws_manager.ws_app.send.assert_called_once()

    def test_on_open_logs_connection_message(self) -> None:
        """Test that _on_open() logs a connection message."""
        self.ws_manager._on_open(self.ws_manager.ws_app)
        
        # Logger should be called with connection message and handshake message
        self.assertGreaterEqual(self.logger.log.call_count, 1)
        
        # Check that one of the messages mentions connection
        log_calls = [call_args[0][0] for call_args in self.logger.log.call_args_list]
        connection_logged = any("connected" in msg.lower() for msg in log_calls)
        self.assertTrue(connection_logged)

    def test_on_open_with_status_change_callback(self) -> None:
        """Test that _on_open() calls on_status_change callback with True."""
        status_change_callback = MagicMock()
        manager = WebSocketManager(
            logger=self.logger,
            on_status_change=status_change_callback,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        manager._on_open(manager.ws_app)
        
        # Verify on_status_change was called with True
        status_change_callback.assert_called_with(True)

    def test_on_open_calls_handshake_after_connected(self) -> None:
        """Test that handshake is called after connected flag is set."""
        call_order = []
        
        def track_connected_change(*args):
            call_order.append(('connected', self.ws_manager.connected))
        
        def track_handshake_call(*args):
            call_order.append(('handshake', self.ws_manager.connected))
        
        self.ws_manager.ws_app.send = track_handshake_call
        self.logger.log.side_effect = track_connected_change
        
        self.ws_manager._on_open(self.ws_manager.ws_app)
        
        # Verify connected was set before handshake
        self.assertTrue(any(item[1] for item in call_order if item[0] == 'connected'))


class TestHandshakeEdgeCases(TestCase):
    """Test edge cases and error conditions."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_with_empty_client_id(self) -> None:
        """Test handshake with empty client_id."""
        manager = WebSocketManager(
            logger=self.logger,
            client_id=""
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_payload_str = manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)
        
        self.assertEqual(sent_payload["clientId"], "")

    def test_handshake_with_special_characters_in_client_id(self) -> None:
        """Test handshake with special characters in client_id."""
        special_client_id = "device-@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=special_client_id
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_payload_str = manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)
        
        self.assertEqual(sent_payload["clientId"], special_client_id)

    def test_handshake_with_unicode_client_id(self) -> None:
        """Test handshake with unicode characters in client_id."""
        unicode_client_id = "设备-001-ñoño"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=unicode_client_id
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_payload_str = manager.ws_app.send.call_args[0][0]
        sent_payload = json.loads(sent_payload_str)
        
        self.assertEqual(sent_payload["clientId"], unicode_client_id)

    def test_handshake_multiple_calls(self) -> None:
        """Test calling _send_handshake() multiple times."""
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        # Call handshake multiple times
        manager._send_handshake()
        manager._send_handshake()
        manager._send_handshake()
        
        # Verify ws_app.send was called three times
        self.assertEqual(manager.ws_app.send.call_count, 3)
        
        # Verify all payloads are identical and valid
        for call_args in manager.ws_app.send.call_args_list:
            sent_payload_str = call_args[0][0]
            sent_payload = json.loads(sent_payload_str)
            self.assertEqual(sent_payload["action"], "handshake")
            self.assertEqual(sent_payload["clientId"], "test-device-001")

    def test_handshake_with_message_callback(self) -> None:
        """Test that handshake works with on_message callback."""
        message_callback = MagicMock()
        manager = WebSocketManager(
            logger=self.logger,
            on_message=message_callback,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        # on_message callback should not be called during handshake send
        message_callback.assert_not_called()
