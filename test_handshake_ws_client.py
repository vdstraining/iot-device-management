"""
Unit tests for ws_client.py - WebSocketManager handshake callback verification.

Tests verify:
- on_connect_handshake callback parameter accepted
- Callback is invoked during _on_open()
- Callback is called exactly once per connection
- Callback integration with connection lifecycle
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from ws_client import WebSocketManager


class TestWebSocketManagerHandshakeCallback(unittest.TestCase):
    """Test WebSocketManager handshake callback functionality."""

    def setUp(self):
        """Prepare test fixtures."""
        self.mock_logger = Mock()
        self.mock_callback = Mock()
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_on_connect_handshake_parameter_accepted(self):
        """Verify WebSocketManager accepts on_connect_handshake parameter."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
            on_connect_handshake=self.mock_callback,
        )
        self.assertEqual(manager.on_connect_handshake, self.mock_callback)

    def test_on_connect_handshake_parameter_optional(self):
        """Verify on_connect_handshake parameter is optional (can be None)."""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertIsNone(manager.on_connect_handshake)

    def test_on_connect_handshake_default_none(self):
        """Verify on_connect_handshake defaults to None when not provided."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
        )
        self.assertIsNone(manager.on_connect_handshake)

    def test_callback_is_stored_correctly(self):
        """Verify callback is stored as instance attribute."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        self.assertTrue(hasattr(manager, "on_connect_handshake"))
        self.assertEqual(manager.on_connect_handshake, self.mock_callback)

    def test_on_open_calls_handshake_callback(self):
        """Verify _on_open calls on_connect_handshake callback."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        # Simulate WebSocket opening
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify callback was called
        self.mock_callback.assert_called_once()

    def test_on_open_sets_connected_before_callback(self):
        """Verify connection is established before callback invoked."""
        callback_connected_state = None
        
        def capture_callback():
            nonlocal callback_connected_state
            callback_connected_state = manager.connected
        
        callback_with_capture = Mock(side_effect=capture_callback)
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=callback_with_capture,
        )
        
        # Simulate WebSocket opening
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify connected was True when callback was called
        self.assertTrue(callback_connected_state)
        self.assertTrue(manager.connected)

    def test_on_open_invokes_callback_without_args(self):
        """Verify callback is invoked without arguments."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify callback was called with no arguments
        self.mock_callback.assert_called_once_with()

    def test_on_open_without_callback_doesnt_fail(self):
        """Verify _on_open doesn't fail when callback is None."""
        manager = WebSocketManager(logger=self.mock_logger)
        
        mock_ws = Mock()
        # Should not raise exception
        manager._on_open(mock_ws)
        
        self.assertTrue(manager.connected)

    def test_status_change_callback_called_on_open(self):
        """Verify on_status_change is called when connection opens."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=self.mock_on_status_change,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify status change callback was called with True
        self.mock_on_status_change.assert_called_with(True)

    def test_callback_and_status_change_both_called(self):
        """Verify both handshake and status_change callbacks are called."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=self.mock_on_status_change,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify both were called
        self.mock_callback.assert_called_once()
        self.mock_on_status_change.assert_called_once_with(True)

    def test_on_close_sets_connected_false(self):
        """Verify _on_close sets connected to False."""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = True
        
        mock_ws = Mock()
        manager._on_close(mock_ws, 1000, "Normal closure")
        
        self.assertFalse(manager.connected)

    def test_multiple_connections_invoke_callback_each_time(self):
        """Verify callback is invoked for each new connection (multiple opens)."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        
        # First connection
        manager._on_open(mock_ws)
        self.assertEqual(self.mock_callback.call_count, 1)
        
        # Simulate close
        manager._on_close(mock_ws, 1000, "Normal closure")
        
        # Second connection
        manager._on_open(mock_ws)
        self.assertEqual(self.mock_callback.call_count, 2)

    def test_logger_called_on_open(self):
        """Verify logger is called when connection opens."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Verify logger was called
        self.assertTrue(self.mock_logger.log.called)
        log_calls = self.mock_logger.log.call_args_list
        # Should log "WebSocket connected."
        self.assertTrue(
            any("connected" in str(call).lower() for call in log_calls)
        )

    def test_callback_exception_doesnt_break_connection(self):
        """Verify exception in callback doesn't break connection state."""
        def failing_callback():
            raise RuntimeError("Callback error")
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=failing_callback,
        )
        
        mock_ws = Mock()
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            manager._on_open(mock_ws)


class TestWebSocketManagerCallbackIntegration(unittest.TestCase):
    """Test WebSocketManager callback with other lifecycle events."""

    def setUp(self):
        """Prepare test fixtures."""
        self.mock_logger = Mock()
        self.mock_callback = Mock()
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_message_callback_independent_of_handshake_callback(self):
        """Verify message callback is independent of handshake callback."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        manager._on_message(mock_ws, '{"type": "response"}')
        
        # Both should be called
        self.mock_callback.assert_called_once()
        self.mock_on_message.assert_called_once()

    def test_error_callback_independent_of_handshake_callback(self):
        """Verify error callback doesn't interfere with handshake callback."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        self.assertEqual(self.mock_callback.call_count, 1)
        
        # Simulate error
        manager._on_error(mock_ws, Exception("Test error"))
        
        # Handshake callback should not be called again
        self.assertEqual(self.mock_callback.call_count, 1)

    def test_initialization_without_callback_doesnt_raise(self):
        """Verify WebSocketManager can be initialized safely without callback."""
        # Should not raise exception
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertIsNone(manager.on_connect_handshake)

    def test_send_json_before_connection_logs_error(self):
        """Verify send_json handles disconnected state gracefully."""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=self.mock_callback,
        )
        
        # Try to send before connecting
        manager.send_json({"test": "data"})
        
        # Should log error message
        self.assertTrue(self.mock_logger.log.called)
        log_message = str(self.mock_logger.log.call_args_list)
        self.assertIn("not connected", log_message.lower())

    def test_callback_called_before_further_operations(self):
        """Verify callback is called early in connection lifecycle."""
        call_order = []
        
        def track_handshake():
            call_order.append("handshake")
        
        def track_status(status):
            call_order.append(f"status_{status}")
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=track_status,
            on_connect_handshake=track_handshake,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        # Status change should be called first, then handshake
        # (based on _on_open implementation)
        self.assertEqual(call_order[0], "status_True")
        self.assertEqual(call_order[1], "handshake")


class TestWebSocketManagerCallbackSignature(unittest.TestCase):
    """Test callback parameter flexibility and signature."""

    def setUp(self):
        """Prepare test fixtures."""
        self.mock_logger = Mock()

    def test_callback_accepts_callable(self):
        """Verify callback accepts any callable."""
        def my_callback():
            pass
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=my_callback,
        )
        self.assertEqual(manager.on_connect_handshake, my_callback)

    def test_callback_accepts_lambda(self):
        """Verify callback accepts lambda functions."""
        callback = lambda: None
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=callback,
        )
        self.assertEqual(manager.on_connect_handshake, callback)

    def test_callback_with_side_effects(self):
        """Verify callback with side effects is executed."""
        side_effect_tracker = []
        
        def callback_with_side_effect():
            side_effect_tracker.append("executed")
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_connect_handshake=callback_with_side_effect,
        )
        
        mock_ws = Mock()
        manager._on_open(mock_ws)
        
        self.assertEqual(side_effect_tracker, ["executed"])


if __name__ == "__main__":
    unittest.main()
