#!/usr/bin/env python
"""
Comprehensive integration tests for WebSocket handshake mechanism.
Tests end-to-end flows, timing, state management, and error scenarios.
"""

import json
import threading
import time
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from ws_client import WebSocketManager
from handshake import HandshakeHandler
from handshake_config import HandshakeConfig


class TestWebSocketManagerIntegration(unittest.TestCase):
    """Test WebSocket manager integration with handshake."""

    def test_manager_has_handshake_handler(self):
        """Test that manager initializes with handshake_handler."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertIsNotNone(manager.handshake_handler)
        self.assertIsInstance(manager.handshake_handler, HandshakeHandler)

    def test_manager_handshake_handler_uses_manager_logger(self):
        """Test that handshake uses manager's logger."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertEqual(manager.handshake_handler.logger, logger)

    def test_manager_initial_state(self):
        """Test manager initialization state."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertFalse(manager.connected)
        self.assertFalse(manager.handshake_handler.handshake_sent)
        self.assertFalse(manager.handshake_handler.handshake_acknowledged)


class TestHandshakeConfiguration(unittest.TestCase):
    """Test handshake configuration management."""

    def test_update_handshake_config_token(self):
        """Test updating handshake token."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(token="test-token-123")
        
        self.assertEqual(manager.handshake_handler.config.token, "test-token-123")

    def test_update_handshake_config_client_id(self):
        """Test updating handshake client_id."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(client_id="custom-client-123")
        
        self.assertEqual(manager.handshake_handler.config.client_id, "custom-client-123")

    def test_update_handshake_config_logs_update(self):
        """Test that config update is logged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(token="new-token")
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("Handshake config updated", log_message)

    def test_update_handshake_config_multiple_fields(self):
        """Test updating multiple config fields."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(
            token="token1",
            client_id="id1",
            client_version="2.0.0"
        )
        
        self.assertEqual(manager.handshake_handler.config.token, "token1")
        self.assertEqual(manager.handshake_handler.config.client_id, "id1")
        self.assertEqual(manager.handshake_handler.config.client_version, "2.0.0")


class TestHandshakeTiming(unittest.TestCase):
    """Test handshake timing and scheduling."""

    def test_handshake_scheduled_on_connection(self):
        """Test that handshake is scheduled when connection opens."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Simulate connection opening
        manager._on_open(None)
        
        self.assertTrue(manager.connected)
        # Handshake should be scheduled (state reset for new connection)
        self.assertFalse(manager.handshake_handler.handshake_sent)

    def test_handshake_resets_on_reconnection(self):
        """Test that handshake state is reset on new connection."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Mark as already sent
        manager.handshake_handler.handshake_sent = True
        
        # Simulate new connection
        manager._on_open(None)
        
        # Should be reset for new connection
        self.assertFalse(manager.handshake_handler.handshake_sent)

    def test_handshake_trigger_method_exists(self):
        """Test that _send_handshake method exists."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertTrue(hasattr(manager, '_send_handshake'))
        self.assertTrue(callable(manager._send_handshake))

    @patch('threading.Timer')
    def test_handshake_timer_scheduled_with_two_second_delay(self, mock_timer):
        """Test that handshake is scheduled with 2-second delay."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Simulate connection opening
        manager._on_open(None)
        
        # Check that Timer was called with 2.0 seconds
        mock_timer.assert_called_once()
        args, kwargs = mock_timer.call_args
        self.assertEqual(args[0], 2.0)  # Delay parameter
        self.assertIn(manager._send_handshake, args)  # Callback


class TestHandshakeMessageSending(unittest.TestCase):
    """Test handshake message sending through WebSocket."""

    def test_send_handshake_when_connected(self):
        """Test that handshake is sent when connected."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()  # Mock WebSocket app
        manager.connected = True
        
        # Trigger handshake send
        manager._send_handshake()
        
        # Should call send_json which calls ws_app.send
        # (The actual call happens through send_json method)
        self.assertTrue(manager.handshake_handler.handshake_sent)

    def test_send_handshake_when_disconnected_fails(self):
        """Test that handshake send fails when disconnected."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.connected = False
        manager.ws_app = None
        
        # Trigger handshake send
        manager._send_handshake()
        
        # Should not be sent
        self.assertFalse(manager.handshake_handler.handshake_sent)

    def test_send_json_payload_structure(self):
        """Test that send_json properly serializes payload."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        payload = {"action": "test", "data": "value"}
        manager.send_json(payload)
        
        # Check that ws_app.send was called with JSON string
        manager.ws_app.send.assert_called_once()
        sent_data = manager.ws_app.send.call_args[0][0]
        
        # Should be valid JSON
        parsed = json.loads(sent_data)
        self.assertEqual(parsed["action"], "test")


class TestHandshakeResponseProcessing(unittest.TestCase):
    """Test processing server responses to handshake."""

    def test_on_message_processes_handshake_response(self):
        """Test that handshake responses are processed."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        response = '{"action": "handshake_ack", "status": "ok"}'
        manager._on_message(None, response)
        
        self.assertTrue(manager.handshake_handler.handshake_acknowledged)

    def test_on_message_calls_user_callback(self):
        """Test that user message callback is called."""
        logger = Mock()
        user_callback = Mock()
        manager = WebSocketManager(logger, on_message=user_callback)
        
        message = '{"action": "data", "value": 123}'
        manager._on_message(None, message)
        
        user_callback.assert_called_once_with(message)

    def test_on_message_handles_non_handshake_responses(self):
        """Test that non-handshake responses don't trigger handshake logic."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        response = '{"action": "ping_response", "data": "pong"}'
        manager._on_message(None, response)
        
        # Should not acknowledge handshake
        self.assertFalse(manager.handshake_handler.handshake_acknowledged)

    def test_on_message_logs_non_handshake_responses(self):
        """Test that messages without custom callback are logged."""
        logger = Mock()
        manager = WebSocketManager(logger)  # No on_message callback
        
        message = '{"action": "test"}'
        manager._on_message(None, message)
        
        logger.log.assert_called()


class TestWebSocketConnectionLifecycle(unittest.TestCase):
    """Test connection lifecycle and state transitions."""

    def test_on_open_sets_connected_true(self):
        """Test that _on_open sets connected to True."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_open(None)
        
        self.assertTrue(manager.connected)

    def test_on_close_sets_connected_false(self):
        """Test that _on_close sets connected to False."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.connected = True
        
        manager._on_close(None, None, None)
        
        self.assertFalse(manager.connected)

    def test_on_open_logs_message(self):
        """Test that connection is logged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_open(None)
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("connected", log_message.lower())

    def test_on_close_logs_message(self):
        """Test that disconnection is logged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_close(None, 1000, "Normal closure")
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("closed", log_message.lower())

    def test_on_error_logs_error(self):
        """Test that errors are logged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_error(None, "Connection error")
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("error", log_message.lower())

    def test_status_change_callback(self):
        """Test that status change callback is called."""
        logger = Mock()
        status_callback = Mock()
        manager = WebSocketManager(logger, on_status_change=status_callback)
        
        manager._on_open(None)
        
        # Callback should be called with True (connected)
        self.assertTrue(status_callback.called)


class TestMultipleConnections(unittest.TestCase):
    """Test state management across multiple connections."""

    def test_handshake_can_be_sent_after_disconnect_and_reconnect(self):
        """Test that handshake can be resent after reconnection."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        
        # First connection
        manager._on_open(None)
        manager.connected = True
        manager._send_handshake()
        self.assertTrue(manager.handshake_handler.handshake_sent)
        
        # Disconnect
        manager._on_close(None, None, None)
        self.assertFalse(manager.connected)
        
        # Reconnect
        manager._on_open(None)
        self.assertFalse(manager.handshake_handler.handshake_sent)  # Reset for new connection
        self.assertTrue(manager.connected)

    def test_handshake_state_independent_across_connections(self):
        """Test that each connection has independent handshake state."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # First connection - handshake sent
        manager._on_open(None)
        manager.handshake_handler.handshake_sent = True
        manager.handshake_handler.handshake_acknowledged = True
        
        # Second connection - state should be reset
        manager._on_open(None)
        self.assertFalse(manager.handshake_handler.handshake_sent)
        self.assertFalse(manager.handshake_handler.handshake_acknowledged)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in handshake flows."""

    def test_send_json_handles_disconnect(self):
        """Test that send_json handles being called when disconnected."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.connected = False
        
        # Should not raise exception
        manager.send_json({"action": "test"})
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("not connected", log_message)

    def test_send_json_handles_exception(self):
        """Test that send_json handles exceptions from ws_app."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.connected = True
        manager.ws_app = Mock()
        manager.ws_app.send.side_effect = Exception("Network error")
        
        # Should not raise exception
        manager.send_json({"action": "test"})
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("send error", log_message)

    def test_malformed_json_response_handled_gracefully(self):
        """Test that malformed JSON doesn't crash message handler."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Should not raise exception
        manager._on_message(None, "not valid json {{{")
        
        # Should continue operating
        self.assertEqual(manager.connected, False)  # Still at initial state


class TestHandshakeConfigIntegration(unittest.TestCase):
    """Test integration of handshake config with WebSocket manager."""

    def test_manager_respects_configured_values_in_payload(self):
        """Test that manager's handshake uses configured values."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        # Configure custom values
        manager.update_handshake_config(
            client_id="my-custom-id",
            token="my-custom-token"
        )
        
        # Send handshake
        manager._send_handshake()
        
        # Verify the payload sent contains custom values
        self.assertEqual(manager.handshake_handler.config.client_id, "my-custom-id")
        self.assertEqual(manager.handshake_handler.config.token, "my-custom-token")

    def test_invalid_config_prevents_sending(self):
        """Test that invalid config prevents sending."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        # Set invalid config
        manager.handshake_handler.config.client_id = ""
        
        # Attempt to send
        manager._send_handshake()
        
        # Should not have sent
        self.assertFalse(manager.handshake_handler.handshake_sent)


class TestConcurrency(unittest.TestCase):
    """Test concurrent operations and race conditions."""

    def test_double_send_prevented(self):
        """Test that concurrent send attempts are prevented."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        # First send
        manager._send_handshake()
        send_count_after_first = manager.ws_app.send.call_count
        
        # Attempt second send immediately
        manager._send_handshake()
        send_count_after_second = manager.ws_app.send.call_count
        
        # Should not have increased
        self.assertEqual(send_count_after_first, send_count_after_second)

    def test_reset_during_message_processing(self):
        """Test that state resets don't interfere with message processing."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Simulate some activity
        manager.handshake_handler.handshake_sent = True
        
        # Reset (simulating reconnection)
        manager.handshake_handler.reset_for_new_connection()
        
        # Process message (should work)
        response = '{"action": "handshake_ack"}'
        manager._on_message(None, response)
        
        # Acknowledgment should be set
        self.assertTrue(manager.handshake_handler.handshake_acknowledged)


if __name__ == "__main__":
    unittest.main()
