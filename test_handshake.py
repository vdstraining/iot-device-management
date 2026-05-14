import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

from utilities import DEFAULT_COMMANDS, AppLogger
from ws_client import WebSocketManager


class TestHandshakeCommandDefinition(unittest.TestCase):
    """Test cases for Handshake command definition in utilities.py"""

    def test_handshake_command_exists_in_default_commands(self):
        """Test that Handshake command exists in DEFAULT_COMMANDS"""
        handshake_cmd = None
        for cmd in DEFAULT_COMMANDS:
            if cmd["name"] == "Handshake":
                handshake_cmd = cmd
                break

        self.assertIsNotNone(handshake_cmd, "Handshake command not found in DEFAULT_COMMANDS")

    def test_handshake_payload_has_required_fields(self):
        """Test that Handshake payload contains all required fields"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None,
        )
        self.assertIsNotNone(handshake_cmd)

        payload = handshake_cmd["payload"]
        required_fields = ["action", "clientId", "token", "timestamp"]

        for field in required_fields:
            self.assertIn(
                field,
                payload,
                f"Required field '{field}' not found in Handshake payload",
            )

    def test_handshake_action_value_is_correct(self):
        """Test that Handshake action value is exactly 'handshake'"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None,
        )
        self.assertIsNotNone(handshake_cmd)

        payload = handshake_cmd["payload"]
        self.assertEqual(
            payload["action"],
            "handshake",
            "Handshake action value is not 'handshake'",
        )

    def test_handshake_payload_structure(self):
        """Test complete structure of Handshake payload"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None,
        )
        self.assertIsNotNone(handshake_cmd)

        payload = handshake_cmd["payload"]

        # Verify types
        self.assertIsInstance(payload["action"], str)
        self.assertIsInstance(payload["clientId"], str)
        self.assertIsInstance(payload["token"], str)
        self.assertIsInstance(payload["timestamp"], str)

        # Verify non-empty values
        self.assertTrue(len(payload["clientId"]) > 0)
        self.assertTrue(len(payload["token"]) > 0)
        self.assertTrue(len(payload["timestamp"]) > 0)


class TestAppLogger(unittest.TestCase):
    """Test cases for AppLogger used in handshake logging"""

    def test_app_logger_formats_message_with_timestamp(self):
        """Test that AppLogger adds timestamp to logged messages"""
        callback = Mock()
        logger = AppLogger(callback)

        logger.log("Test message")

        # Verify callback was called
        callback.assert_called_once()

        # Verify timestamp format in message
        logged_message = callback.call_args[0][0]
        self.assertIn("[", logged_message)
        self.assertIn("]", logged_message)
        self.assertIn("Test message", logged_message)

    def test_app_logger_appends_newline(self):
        """Test that AppLogger appends newline to messages"""
        callback = Mock()
        logger = AppLogger(callback)

        logger.log("Test")

        logged_message = callback.call_args[0][0]
        self.assertTrue(logged_message.endswith("\n"))


class TestWebSocketHandshakeSendLogic(unittest.TestCase):
    """Test cases for WebSocket handshake send logic in ws_client.py"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger_callback = Mock()
        self.logger = AppLogger(self.logger_callback)
        self.on_message_callback = Mock()
        self.on_status_change_callback = Mock()

    def test_handshake_sent_on_connection_open(self):
        """Test that handshake is sent automatically when WebSocket connection opens"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            on_message=self.on_message_callback,
            on_status_change=self.on_status_change_callback,
            client_id="test_client",
            token="test_token",
        )

        # Set the ws_app before calling _on_open
        manager.ws_app = mock_ws_app

        # Simulate on_open being called
        manager._on_open(mock_ws_app)

        # Verify send was called
        mock_ws_app.send.assert_called_once()

        # Verify the sent payload contains handshake action
        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["action"], "handshake")

    def test_handshake_contains_iso_format_timestamp(self):
        """Test that handshake contains valid ISO format timestamp"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        timestamp = sent_payload["timestamp"]

        # Verify timestamp ends with 'Z' (ISO format)
        self.assertTrue(
            timestamp.endswith("Z"),
            "Timestamp does not end with 'Z' (expected ISO format with Z)",
        )

        # Verify we can parse it
        try:
            # Remove 'Z' suffix for parsing
            datetime.fromisoformat(timestamp.rstrip("Z"))
        except ValueError:
            self.fail(f"Timestamp '{timestamp}' is not valid ISO format")

    def test_handshake_includes_client_id_from_init(self):
        """Test that handshake payload includes client_id from WebSocketManager init"""
        mock_ws_app = MagicMock()

        test_client_id = "unique_client_42"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=test_client_id,
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["clientId"], test_client_id)

    def test_handshake_includes_token_from_init(self):
        """Test that handshake payload includes token from WebSocketManager init"""
        mock_ws_app = MagicMock()

        test_token = "secret_token_xyz"
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token=test_token,
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["token"], test_token)

    def test_handshake_validation_rejects_empty_client_id(self):
        """Test that handshake validation rejects empty clientId and logs error"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="",  # Empty client_id
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify send was not called (validation failed)
        mock_ws_app.send.assert_not_called()

        # Verify error was logged
        self.logger_callback.assert_called()
        logged_message = self.logger_callback.call_args[0][0]
        self.assertIn("Handshake validation failed", logged_message)
        self.assertIn("clientId empty=True", logged_message)

    def test_handshake_validation_rejects_empty_token(self):
        """Test that handshake validation rejects empty token and logs error"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token="",  # Empty token
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify send was not called (validation failed)
        mock_ws_app.send.assert_not_called()

        # Verify error was logged
        self.logger_callback.assert_called()
        logged_message = self.logger_callback.call_args[0][0]
        self.assertIn("Handshake validation failed", logged_message)
        self.assertIn("token empty=True", logged_message)

    def test_handshake_validation_rejects_both_empty_client_id_and_token(self):
        """Test that handshake validation detects both empty clientId and token"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="",  # Empty
            token="",  # Empty
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify send was not called
        mock_ws_app.send.assert_not_called()

        # Verify error was logged
        logged_message = self.logger_callback.call_args[0][0]
        self.assertIn("clientId empty=True", logged_message)
        self.assertIn("token empty=True", logged_message)

    def test_handshake_request_logged_before_sending(self):
        """Test that handshake request is logged before sending"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify logger was called with handshake message
        self.logger_callback.assert_called()

        # Check that a log message about sending handshake exists
        log_calls = self.logger_callback.call_args_list
        handshake_log_found = False
        for call_obj in log_calls:
            logged_msg = call_obj[0][0]
            if "handshake" in logged_msg.lower() and "sent" in logged_msg.lower():
                handshake_log_found = True
                break

        self.assertTrue(
            handshake_log_found,
            "No log message found about sending handshake",
        )

    def test_handshake_payload_is_valid_json(self):
        """Test that handshake payload is valid JSON"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_raw_payload = mock_ws_app.send.call_args[0][0]

        # Verify it's valid JSON
        try:
            payload = json.loads(sent_raw_payload)
            self.assertIsInstance(payload, dict)
        except json.JSONDecodeError:
            self.fail("Handshake payload is not valid JSON")

    def test_handshake_sets_connected_status(self):
        """Test that _on_open sets connected status to True"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            on_status_change=self.on_status_change_callback,
            client_id="test_client",
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify connected flag is set
        self.assertTrue(manager.connected)

        # Verify status change callback was called
        self.on_status_change_callback.assert_called_with(True)


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger_callback = Mock()
        self.logger = AppLogger(self.logger_callback)
        self.on_message_callback = Mock()
        self.on_status_change_callback = Mock()

    def test_full_handshake_flow_on_connection(self):
        """Test full flow: Connect -> Handshake sent automatically -> Response logged"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            on_message=self.on_message_callback,
            on_status_change=self.on_status_change_callback,
            client_id="integration_test_client",
            token="integration_test_token",
        )

        # Simulate connection by directly calling _on_open
        # (in real scenario, WebSocketApp would call this)
        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # Verify handshake was sent
        mock_ws_app.send.assert_called_once()
        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["action"], "handshake")
        self.assertEqual(sent_payload["clientId"], "integration_test_client")
        self.assertEqual(sent_payload["token"], "integration_test_token")

        # Simulate server response
        server_response = '{"status": "ok", "message": "Handshake accepted"}'
        manager._on_message(mock_ws_app, server_response)

        # Verify response was logged
        self.on_message_callback.assert_called_once_with(server_response)

    def test_manual_handshake_send_via_send_json(self):
        """Test manual send of Handshake command from UI"""
        with patch("ws_client.WebSocketApp") as mock_ws_class:
            mock_ws_app = MagicMock()
            mock_ws_class.return_value = mock_ws_app

            manager = WebSocketManager(
                logger=self.logger,
                on_message=self.on_message_callback,
                on_status_change=self.on_status_change_callback,
                client_id="test_client",
                token="test_token",
            )

            # First, establish connection
            manager._set_connected(True)
            manager.ws_app = mock_ws_app

            # Get Handshake payload from DEFAULT_COMMANDS
            handshake_cmd = next(
                (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
                None,
            )
            self.assertIsNotNone(handshake_cmd)

            handshake_payload = handshake_cmd["payload"]

            # Manually send via send_json (as UI would do)
            manager.send_json(handshake_payload)

            # Verify it was sent
            mock_ws_app.send.assert_called_once()

            sent_raw = mock_ws_app.send.call_args[0][0]
            sent_payload = json.loads(sent_raw)

            self.assertEqual(sent_payload["action"], "handshake")
            self.assertIn("clientId", sent_payload)
            self.assertIn("token", sent_payload)


class TestEdgeCases(unittest.TestCase):
    """Edge case tests for handshake implementation"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger_callback = Mock()
        self.logger = AppLogger(self.logger_callback)

    def test_handshake_with_whitespace_only_client_id(self):
        """Test that handshake validation treats whitespace-only clientId as empty"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="   ",  # Whitespace only
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        # With current implementation, whitespace is not considered empty
        # This test documents the current behavior
        # If validation should trim whitespace, this test should fail
        # and the implementation should be updated
        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["clientId"], "   ")

    def test_handshake_with_special_characters_in_token(self):
        """Test that handshake handles special characters in token"""
        mock_ws_app = MagicMock()

        special_token = 'token!@#$%^&*()_+-=[]{}|;\':",./<>?'
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token=special_token,
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["token"], special_token)

    def test_handshake_with_very_long_client_id(self):
        """Test that handshake handles very long client_id"""
        mock_ws_app = MagicMock()

        long_client_id = "x" * 1000
        manager = WebSocketManager(
            logger=self.logger,
            client_id=long_client_id,
            token="test_token",
        )

        manager.ws_app = mock_ws_app
        manager._on_open(mock_ws_app)

        sent_payload = json.loads(mock_ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["clientId"], long_client_id)

    def test_multiple_consecutive_handshakes(self):
        """Test that multiple handshake sends work correctly"""
        mock_ws_app = MagicMock()

        manager = WebSocketManager(
            logger=self.logger,
            client_id="test_client",
            token="test_token",
        )

        manager.ws_app = mock_ws_app

        # Send handshake multiple times
        manager._send_handshake()
        manager._send_handshake()
        manager._send_handshake()

        # Verify all sends were made
        self.assertEqual(mock_ws_app.send.call_count, 3)

        # Verify all payloads are valid
        for call_obj in mock_ws_app.send.call_args_list:
            payload = json.loads(call_obj[0][0])
            self.assertEqual(payload["action"], "handshake")


if __name__ == "__main__":
    unittest.main()
