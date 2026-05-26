"""
Comprehensive test suite for SCRUM-126: Handshake Feature

Tests cover:
1. Handshake auto-send on WebSocket connection
2. Handshake in DEFAULT_COMMANDS
3. Manual handshake send
4. Handshake logging with timestamps
5. JSON validation
6. Reconnect behavior
7. Custom handshake configuration
8. Server error handling and responses
"""

import json
import threading
import time
import unittest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, call

from utilities import DEFAULT_COMMANDS, AppLogger
from ws_client import WebSocketManager


class TestHandshakeDefaults(unittest.TestCase):
    """Test Suite 1: Verify Handshake in DEFAULT_COMMANDS"""

    def test_handshake_in_default_commands(self):
        """Verify 'Handshake' command appears in DEFAULT_COMMANDS"""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        self.assertIn("Handshake", command_names)

    def test_handshake_payload_structure(self):
        """Verify handshake payload contains required fields"""
        handshake_cmd = next(
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        # Verify required fields
        self.assertIn("action", payload)
        self.assertIn("clientId", payload)
        self.assertIn("timestamp", payload)
        self.assertIn("version", payload)

    def test_handshake_action_value(self):
        """Verify handshake action is set correctly"""
        handshake_cmd = next(
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        )
        self.assertEqual(handshake_cmd["payload"]["action"], "handshake")

    def test_handshake_payload_types(self):
        """Verify handshake payload field types"""
        handshake_cmd = next(
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        self.assertIsInstance(payload["action"], str)
        self.assertIsInstance(payload["clientId"], str)
        self.assertIsInstance(payload["timestamp"], str)
        self.assertIsInstance(payload["version"], str)

    def test_handshake_clientid_not_empty(self):
        """Verify clientId is not empty"""
        handshake_cmd = next(
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        )
        self.assertTrue(len(handshake_cmd["payload"]["clientId"]) > 0)

    def test_handshake_version_not_empty(self):
        """Verify version is not empty"""
        handshake_cmd = next(
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        )
        self.assertTrue(len(handshake_cmd["payload"]["version"]) > 0)


class TestHandshakeAutoSend(unittest.TestCase):
    """Test Suite 2: Verify Handshake Auto-Send on Connection"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_handshake_sent_on_open(self):
        """Verify handshake is sent when WebSocket connection opens"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            # Simulate connection open
            self.ws_manager._on_open(None)

            # Verify handshake was sent
            mock_ws_app.send.assert_called_once()

    def test_handshake_payload_format_on_send(self):
        """Verify handshake payload is valid JSON when sent"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Verify payload is valid JSON
            self.assertEqual(len(sent_payloads), 1)
            parsed = json.loads(sent_payloads[0])
            self.assertEqual(parsed["action"], "handshake")

    def test_handshake_contains_action_on_send(self):
        """Verify sent handshake contains action field"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            parsed = json.loads(sent_payloads[0])
            self.assertIn("action", parsed)

    def test_connection_status_set_before_handshake(self):
        """Verify connected status is True before handshake send"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # After _on_open, connected should be True
            self.assertTrue(self.ws_manager.connected)

    def test_handshake_send_error_handling(self):
        """Verify error handling when handshake send fails"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock(side_effect=Exception("Send failed"))
            self.ws_manager.ws_app = mock_ws_app

            # Should not raise exception
            self.ws_manager._on_open(None)

            # Verify error was logged
            self.assertTrue(
                any("Handshake send error" in msg for msg in self.log_messages)
            )

    def test_handshake_sent_with_correct_fields(self):
        """Verify auto-sent handshake contains all required fields"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            parsed = json.loads(sent_payloads[0])
            self.assertIn("clientId", parsed)
            self.assertIn("timestamp", parsed)
            self.assertIn("version", parsed)


class TestHandshakeSendJson(unittest.TestCase):
    """Test Suite 3: Manual Handshake Send via send_json()"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )
        self.ws_manager.connected = True

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_manual_handshake_send_when_connected(self):
        """Verify user can manually send handshake from UI"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            handshake_payload = next(
                cmd["payload"] for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
            )

            self.ws_manager.send_json(handshake_payload)

            mock_ws_app.send.assert_called_once()

    def test_manual_handshake_not_sent_when_disconnected(self):
        """Verify handshake cannot be sent when disconnected"""
        self.ws_manager.connected = False
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            handshake_payload = next(
                cmd["payload"] for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
            )

            self.ws_manager.send_json(handshake_payload)

            # Should not be called when disconnected
            mock_ws_app.send.assert_not_called()

            # Verify error logged
            self.assertTrue(
                any("not connected" in msg for msg in self.log_messages)
            )

    def test_manual_handshake_logged_on_send(self):
        """Verify manual handshake send is logged"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            handshake_payload = next(
                cmd["payload"] for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
            )

            self.ws_manager.send_json(handshake_payload)

            # Verify send message logged
            self.assertTrue(
                any("Sent WebSocket message" in msg for msg in self.log_messages)
            )


class TestHandshakeLogging(unittest.TestCase):
    """Test Suite 4: Verify Handshake Logging with Timestamps"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_auto_handshake_send_logged(self):
        """Verify auto-sent handshake message is logged"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Verify handshake sent was logged
            self.assertTrue(
                any("Auto-sent handshake" in msg for msg in self.log_messages)
            )

    def test_handshake_log_contains_timestamp(self):
        """Verify logged messages contain timestamps"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Verify timestamp format in logs
            timestamp_found = any(
                "[" in msg and "]" in msg for msg in self.log_messages
            )
            self.assertTrue(timestamp_found)

    def test_handshake_response_logged(self):
        """Verify handshake response from server is logged"""
        response_message = '{"status": "ok", "clientId": "iot-client-001"}'

        self.ws_manager._on_message(None, response_message)

        # Verify response was logged
        self.assertTrue(
            any("WebSocket received" in msg for msg in self.log_messages)
        )

    def test_handshake_response_contains_payload(self):
        """Verify handshake response log contains full payload"""
        response_message = '{"status": "ok", "clientId": "iot-client-001"}'

        self.ws_manager._on_message(None, response_message)

        # Verify full response is in logs
        self.assertTrue(any(response_message in msg for msg in self.log_messages))

    def test_connection_status_logged(self):
        """Verify connection status change is logged"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Verify connection log
            self.assertTrue(any("WebSocket connected" in msg for msg in self.log_messages))


class TestHandshakeJsonValidation(unittest.TestCase):
    """Test Suite 5: JSON Validation for Handshake"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )
        self.ws_manager.connected = True

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_valid_handshake_json_sent(self):
        """Verify valid handshake JSON is sent successfully"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            valid_payload = {
                "action": "handshake",
                "clientId": "test-client",
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
            }

            self.ws_manager.send_json(valid_payload)

            mock_ws_app.send.assert_called_once()

    def test_handshake_sent_as_json_string(self):
        """Verify handshake is sent as JSON string, not dict"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            payload = {
                "action": "handshake",
                "clientId": "test-client",
            }

            self.ws_manager.send_json(payload)

            # Verify sent as string
            self.assertIsInstance(sent_payloads[0], str)
            # Verify it's valid JSON
            json.loads(sent_payloads[0])

    def test_handshake_with_extra_fields_sent(self):
        """Verify handshake with extra fields is still sent"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            payload_with_extra = {
                "action": "handshake",
                "clientId": "test-client",
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
                "extra_field": "extra_value",
            }

            self.ws_manager.send_json(payload_with_extra)

            mock_ws_app.send.assert_called_once()

    def test_handshake_receive_valid_json_response(self):
        """Verify valid JSON response is processed without error"""
        valid_response = '{"status": "accepted", "clientId": "iot-client-001"}'

        # Should not raise exception
        self.ws_manager._on_message(None, valid_response)

        # Verify logged
        self.assertTrue(any(valid_response in msg for msg in self.log_messages))

    def test_handshake_receive_invalid_json_response(self):
        """Verify invalid JSON response is handled gracefully"""
        invalid_response = "{ invalid json }"

        # Should not raise exception
        self.ws_manager._on_message(None, invalid_response)

        # Should still log the response as-is
        self.assertTrue(any(invalid_response in msg for msg in self.log_messages))


class TestHandshakeReconnect(unittest.TestCase):
    """Test Suite 6: Verify Handshake on Reconnection"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_handshake_resent_on_reconnect(self):
        """Verify handshake is re-sent on reconnection"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            # First connection
            self.ws_manager._on_open(None)
            self.assertEqual(mock_ws_app.send.call_count, 1)

            # Simulate disconnection
            self.ws_manager._on_close(None, 1000, "Normal closure")
            self.assertFalse(self.ws_manager.connected)

            # Reset the mock for reconnect test
            mock_ws_app.reset_mock()
            self.ws_manager.ws_app = mock_ws_app

            # Reconnect
            self.ws_manager._on_open(None)
            self.assertEqual(mock_ws_app.send.call_count, 1)

    def test_multiple_reconnects_send_handshake(self):
        """Verify multiple reconnects each trigger handshake"""
        send_count = 0

        def count_send(payload):
            nonlocal send_count
            send_count += 1

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = count_send
            self.ws_manager.ws_app = mock_ws_app

            # First connection
            self.ws_manager._on_open(None)
            self.assertEqual(send_count, 1)

            # Close and reconnect multiple times
            for _ in range(3):
                self.ws_manager._on_close(None, 1000, "Normal closure")
                self.ws_manager._on_open(None)

            self.assertEqual(send_count, 4)  # 1 initial + 3 reconnects

    def test_connection_status_after_reconnect(self):
        """Verify connection status is correct after reconnect"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)
            self.assertTrue(self.ws_manager.connected)

            self.ws_manager._on_close(None, 1000, "Normal closure")
            self.assertFalse(self.ws_manager.connected)

            self.ws_manager._on_open(None)
            self.assertTrue(self.ws_manager.connected)


class TestHandshakeConfiguration(unittest.TestCase):
    """Test Suite 7: Verify Custom Handshake Configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )
        self.ws_manager.connected = True

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_custom_client_id_respected(self):
        """Verify custom clientId values are respected"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            custom_payload = {
                "action": "handshake",
                "clientId": "custom-device-123",
                "timestamp": "2026-05-25T14:30:00Z",
                "version": "2.0",
            }

            self.ws_manager.send_json(custom_payload)

            parsed = json.loads(sent_payloads[0])
            self.assertEqual(parsed["clientId"], "custom-device-123")

    def test_custom_version_respected(self):
        """Verify custom version values are respected"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            custom_payload = {
                "action": "handshake",
                "clientId": "device-001",
                "timestamp": "2026-05-25T14:30:00Z",
                "version": "3.0.1",
            }

            self.ws_manager.send_json(custom_payload)

            parsed = json.loads(sent_payloads[0])
            self.assertEqual(parsed["version"], "3.0.1")

    def test_custom_timestamp_respected(self):
        """Verify custom timestamp values are respected"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            custom_ts = "2025-12-31T23:59:59Z"
            custom_payload = {
                "action": "handshake",
                "clientId": "device-001",
                "timestamp": custom_ts,
                "version": "1.0",
            }

            self.ws_manager.send_json(custom_payload)

            parsed = json.loads(sent_payloads[0])
            self.assertEqual(parsed["timestamp"], custom_ts)

    def test_payload_immutability(self):
        """Verify sending handshake doesn't modify original payload"""
        original_payload = {
            "action": "handshake",
            "clientId": "device-001",
            "timestamp": "2026-05-25T14:30:00Z",
            "version": "1.0",
        }
        payload_copy = original_payload.copy()

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager.send_json(original_payload)

            # Original should not be modified
            self.assertEqual(original_payload, payload_copy)


class TestHandshakeServerResponse(unittest.TestCase):
    """Test Suite 8: Server Rejection and Error Handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_server_rejection_response_logged(self):
        """Verify server rejection response is logged"""
        error_response = '{"status": "error", "reason": "invalid_clientId"}'

        self.ws_manager._on_message(None, error_response)

        # Verify error response logged
        self.assertTrue(any(error_response in msg for msg in self.log_messages))

    def test_server_accepted_response_logged(self):
        """Verify server acceptance response is logged"""
        success_response = '{"status": "accepted", "clientId": "iot-client-001", "sessionId": "sess-12345"}'

        self.ws_manager._on_message(None, success_response)

        # Verify success response logged
        self.assertTrue(any(success_response in msg for msg in self.log_messages))

    def test_websocket_error_during_handshake(self):
        """Verify WebSocket error during handshake is handled"""
        error_msg = "Connection refused"

        self.ws_manager._on_error(None, error_msg)

        # Verify error was logged
        self.assertTrue(any("WebSocket error" in msg for msg in self.log_messages))
        self.assertTrue(any(error_msg in msg for msg in self.log_messages))

    def test_connection_close_after_handshake(self):
        """Verify connection close after handshake is logged"""
        close_code = 1000
        close_msg = "Normal closure"

        self.ws_manager._on_close(None, close_code, close_msg)

        # Verify close was logged
        self.assertTrue(any("WebSocket closed" in msg for msg in self.log_messages))

    def test_handshake_response_with_extra_fields(self):
        """Verify server response with extra fields is handled"""
        response = (
            '{"status": "accepted", "clientId": "iot-client-001", '
            '"extra": "data", "nested": {"field": "value"}}'
        )

        self.ws_manager._on_message(None, response)

        # Should handle without error and log it
        self.assertTrue(any(response in msg for msg in self.log_messages))

    def test_handshake_send_failure_does_not_disconnect(self):
        """Verify handshake send failure doesn't cause disconnection"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock(side_effect=Exception("Send failed"))
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Connection should still be established
            self.assertTrue(self.ws_manager.connected)

    def test_websocket_error_does_not_affect_handshake_on_reconnect(self):
        """Verify error doesn't prevent handshake on next connection"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            # Error occurs
            self.ws_manager._on_error(None, "Network error")

            # Reset mock for reconnect
            mock_ws_app.reset_mock()
            self.ws_manager.ws_app = mock_ws_app

            # Reconnect should work
            self.ws_manager._on_open(None)
            mock_ws_app.send.assert_called_once()


class TestHandshakeIntegration(unittest.TestCase):
    """Integration Tests: End-to-end Handshake Scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_full_handshake_flow(self):
        """Test complete handshake flow: connect, send, receive response"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            # Connection opens -> handshake auto-sent
            self.ws_manager._on_open(None)
            self.assertTrue(self.ws_manager.connected)
            self.assertEqual(len(sent_payloads), 1)

            # Server responds to handshake
            server_response = '{"status": "accepted", "clientId": "iot-client-001"}'
            self.ws_manager._on_message(None, server_response)

            # Verify full flow is logged
            logs_str = "\n".join(self.log_messages)
            self.assertIn("Auto-sent handshake", logs_str)
            self.assertIn(server_response, logs_str)

    def test_manual_handshake_after_auto_handshake(self):
        """Test sending manual handshake after auto-handshake"""
        send_count = 0

        def count_send(payload):
            nonlocal send_count
            send_count += 1

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = count_send
            self.ws_manager.ws_app = mock_ws_app

            # Auto-send on open
            self.ws_manager._on_open(None)
            self.assertEqual(send_count, 1)

            # Manually send another handshake
            handshake = next(
                cmd["payload"] for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
            )
            self.ws_manager.send_json(handshake)
            self.assertEqual(send_count, 2)

    def test_handshake_then_other_messages(self):
        """Test handshake followed by other WebSocket messages"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            # Auto-handshake
            self.ws_manager._on_open(None)

            # Send other commands
            ping_payload = {"action": "ping", "timestamp": "2026-05-25T12:00:00Z"}
            self.ws_manager.send_json(ping_payload)

            echo_payload = {"action": "echo", "message": "hello"}
            self.ws_manager.send_json(echo_payload)

            # All should be sent
            self.assertEqual(len(sent_payloads), 3)
            self.assertIn("handshake", sent_payloads[0])

    def test_status_callback_during_handshake(self):
        """Test status change callback is called during handshake"""
        status_changes = []

        def status_callback(connected):
            status_changes.append(connected)

        ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=status_callback,
        )

        with patch.object(ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            ws_manager.ws_app = mock_ws_app

            ws_manager._on_open(None)

            # Status callback should have been called
            self.assertIn(True, status_changes)

    def test_concurrent_messages_after_handshake(self):
        """Test multiple messages sent after handshake without blocking"""
        sent_payloads = []

        def capture_send(payload):
            sent_payloads.append(payload)
            time.sleep(0.01)  # Simulate network delay

        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = capture_send
            self.ws_manager.ws_app = mock_ws_app

            self.ws_manager._on_open(None)

            # Send multiple messages quickly
            for i in range(3):
                payload = {"action": f"message_{i}", "index": i}
                self.ws_manager.send_json(payload)

            # All should be sent (synchronously in this test)
            self.assertEqual(len(sent_payloads), 4)  # 1 handshake + 3 messages


class TestHandshakeEdgeCases(unittest.TestCase):
    """Test Suite: Edge Cases and Boundary Conditions"""

    def setUp(self):
        """Set up test fixtures"""
        self.log_messages = []
        self.logger = AppLogger(self._capture_log)
        self.ws_manager = WebSocketManager(
            logger=self.logger,
            on_message=None,
            on_status_change=None,
        )
        self.ws_manager.connected = True

    def _capture_log(self, message: str):
        """Capture log messages for verification"""
        self.log_messages.append(message)

    def test_empty_response_message(self):
        """Test handling of empty response message"""
        self.ws_manager._on_message(None, "")

        # Should handle without error
        self.assertTrue(len(self.log_messages) >= 0)

    def test_null_byte_in_message(self):
        """Test handling of null bytes in message"""
        message_with_null = "test\x00message"

        self.ws_manager._on_message(None, message_with_null)

        # Should handle without error
        self.assertTrue(any(message_with_null in msg for msg in self.log_messages))

    def test_unicode_in_handshake(self):
        """Test Unicode characters in handshake payload"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            unicode_payload = {
                "action": "handshake",
                "clientId": "設備-001",
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
            }

            self.ws_manager.send_json(unicode_payload)

            mock_ws_app.send.assert_called_once()

    def test_very_long_clientid(self):
        """Test handling of very long clientId"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            long_id = "x" * 1000
            payload = {
                "action": "handshake",
                "clientId": long_id,
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
            }

            self.ws_manager.send_json(payload)

            mock_ws_app.send.assert_called_once()

    def test_special_characters_in_fields(self):
        """Test special characters in handshake fields"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            payload = {
                "action": "handshake",
                "clientId": 'device-"001"-special',
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
            }

            self.ws_manager.send_json(payload)

            mock_ws_app.send.assert_called_once()

    def test_handshake_with_null_ws_app(self):
        """Test handshake when ws_app is None"""
        self.ws_manager.ws_app = None

        # Should not raise exception
        self.ws_manager._on_open(None)

        # Connected should still be set
        self.assertTrue(self.ws_manager.connected)

    def test_handshake_payload_without_action(self):
        """Test sending handshake-like payload without action field"""
        with patch.object(self.ws_manager, "ws_app") as mock_ws_app:
            mock_ws_app.send = Mock()
            self.ws_manager.ws_app = mock_ws_app

            payload = {
                "clientId": "device-001",
                "timestamp": "2026-05-25T12:00:00Z",
                "version": "1.0",
            }

            self.ws_manager.send_json(payload)

            # Should still send (no validation at send level)
            mock_ws_app.send.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
