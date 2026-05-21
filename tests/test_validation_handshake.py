"""
Tests for validation and edge cases of handshake functionality (SCRUM-53).
"""

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS


class TestHandshakePayloadValidation(TestCase):
    """Test handshake payload structure and validation."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_payload_has_all_required_fields(self) -> None:
        """Test that handshake payload contains all required fields."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        required_fields = ["action", "clientId", "capabilities", "version"]
        for field in required_fields:
            self.assertIn(field, payload, f"Missing required field: {field}")

    def test_handshake_action_is_string(self) -> None:
        """Test that action field is a string."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertIsInstance(payload["action"], str)

    def test_handshake_action_is_handshake(self) -> None:
        """Test that action field is exactly 'handshake'."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["action"], "handshake")

    def test_handshake_client_id_is_string(self) -> None:
        """Test that clientId field is a string."""
        manager = WebSocketManager(logger=self.logger, client_id="device-001")
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertIsInstance(payload["clientId"], str)

    def test_handshake_capabilities_is_dict(self) -> None:
        """Test that capabilities field is a dictionary."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertIsInstance(payload["capabilities"], dict)

    def test_handshake_version_is_string(self) -> None:
        """Test that version field is a string."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertIsInstance(payload["version"], str)

    def test_handshake_version_is_1_0(self) -> None:
        """Test that version is exactly '1.0'."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["version"], "1.0")

    def test_handshake_no_extra_fields(self) -> None:
        """Test that handshake payload doesn't have unexpected fields."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        expected_fields = {"action", "clientId", "capabilities", "version"}
        actual_fields = set(payload.keys())
        
        self.assertEqual(actual_fields, expected_fields)

    def test_handshake_payload_is_serializable(self) -> None:
        """Test that handshake payload can be serialized and deserialized."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        
        # Should be able to round-trip
        payload1 = json.loads(sent_str)
        str_again = json.dumps(payload1)
        payload2 = json.loads(str_again)
        
        self.assertEqual(payload1, payload2)


class TestLoggingValidation(TestCase):
    """Test that handshake logging is correct."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_logs_on_success(self) -> None:
        """Test that handshake success is logged."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        self.logger.log.assert_called_once()

    def test_handshake_success_log_contains_handshake_keyword(self) -> None:
        """Test that success log message contains 'handshake'."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        log_msg = self.logger.log.call_args[0][0]
        self.assertIn("handshake", log_msg.lower())

    def test_handshake_success_log_contains_action_indication(self) -> None:
        """Test that success log indicates message was sent."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        log_msg = self.logger.log.call_args[0][0]
        self.assertTrue(
            any(word in log_msg.lower() for word in ["sent", "send", "sending"]),
            "Log message should indicate action was sent"
        )

    def test_handshake_error_log_on_exception(self) -> None:
        """Test that error is logged when sending fails."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = ConnectionError("Connection lost")
        
        manager._send_handshake()
        
        log_msg = self.logger.log.call_args[0][0]
        self.assertIn("error", log_msg.lower())

    def test_handshake_error_log_contains_handshake_keyword(self) -> None:
        """Test that error log mentions handshake."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = Exception("Send failed")
        
        manager._send_handshake()
        
        log_msg = self.logger.log.call_args[0][0]
        self.assertIn("handshake", log_msg.lower())


class TestConnectionStateValidation(TestCase):
    """Test handshake behavior with different connection states."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_works_when_connected_true(self) -> None:
        """Test that handshake works when connected is True."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.connected = True
        
        manager._send_handshake()
        
        manager.ws_app.send.assert_called_once()

    def test_handshake_works_when_connected_false(self) -> None:
        """Test that _send_handshake sends even when connected is False."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.connected = False
        
        # _send_handshake should still attempt to send
        manager._send_handshake()
        
        manager.ws_app.send.assert_called_once()

    def test_on_open_sets_connected_before_handshake(self) -> None:
        """Test that _on_open sets connected=True before calling handshake."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        original_connected = manager.connected
        manager._on_open(manager.ws_app)
        
        # connected should have changed
        self.assertNotEqual(manager.connected, original_connected)
        self.assertTrue(manager.connected)

    def test_handshake_logged_payload_contains_json(self) -> None:
        """Test that logged message contains the actual JSON payload."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        log_msg = self.logger.log.call_args[0][0]
        
        # Log message should contain JSON-like content
        self.assertTrue(any(char in log_msg for char in ['{', '"', ':']),
                       "Log message should contain JSON structure")


class TestClientIdSpecialCases(TestCase):
    """Test handshake with various client_id values."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_with_very_long_client_id(self) -> None:
        """Test handshake with very long client_id."""
        long_id = "device-" + "x" * 1000
        manager = WebSocketManager(logger=self.logger, client_id=long_id)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["clientId"], long_id)

    def test_handshake_with_numeric_client_id(self) -> None:
        """Test handshake with numeric-only client_id."""
        numeric_id = "123456789"
        manager = WebSocketManager(logger=self.logger, client_id=numeric_id)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["clientId"], numeric_id)

    def test_handshake_with_uuid_client_id(self) -> None:
        """Test handshake with UUID format client_id."""
        uuid_id = "550e8400-e29b-41d4-a716-446655440000"
        manager = WebSocketManager(logger=self.logger, client_id=uuid_id)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["clientId"], uuid_id)

    def test_handshake_with_url_like_client_id(self) -> None:
        """Test handshake with URL-like client_id."""
        url_id = "https://example.com/device/001"
        manager = WebSocketManager(logger=self.logger, client_id=url_id)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["clientId"], url_id)

    def test_handshake_with_spaces_in_client_id(self) -> None:
        """Test handshake with spaces in client_id."""
        spaces_id = "device 001 test"
        manager = WebSocketManager(logger=self.logger, client_id=spaces_id)
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        payload = json.loads(sent_str)
        
        self.assertEqual(payload["clientId"], spaces_id)


class TestExceptionHandling(TestCase):
    """Test exception handling in handshake flow."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_handles_attribute_error(self) -> None:
        """Test that AttributeError during send is logged."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = AttributeError("No send method")
        
        # Should not raise
        manager._send_handshake()
        
        # Should log error
        self.logger.log.assert_called_once()

    def test_handshake_handles_runtime_error(self) -> None:
        """Test that RuntimeError during send is logged."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = RuntimeError("WebSocket error")
        
        # Should not raise
        manager._send_handshake()
        
        # Should log error
        self.logger.log.assert_called_once()

    def test_handshake_handles_timeout_error(self) -> None:
        """Test that TimeoutError during send is logged."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = TimeoutError("Send timeout")
        
        # Should not raise
        manager._send_handshake()
        
        # Should log error
        self.logger.log.assert_called_once()

    def test_handshake_handles_generic_exception(self) -> None:
        """Test that generic exceptions are caught and logged."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = Exception("Generic error")
        
        # Should not raise
        try:
            manager._send_handshake()
        except Exception:
            self.fail("_send_handshake should not raise exceptions")
        
        # Should log error
        self.logger.log.assert_called_once()
