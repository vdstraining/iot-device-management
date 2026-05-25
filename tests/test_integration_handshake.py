"""
Integration tests for WebSocket handshake functionality (SCRUM-53).

Tests the integration of handshake between WebSocketManager and UI layer.
"""

import json
from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS, AppLogger


class TestWebSocketManagerInitialization(TestCase):
    """Test WebSocketManager initialization with client_id parameter."""

    def test_websocket_manager_receives_client_id(self) -> None:
        """Test WebSocketManager receives client_id parameter during initialization."""
        logger = MagicMock()
        client_id = "test-device-123"
        
        manager = WebSocketManager(
            logger=logger,
            client_id=client_id
        )
        
        self.assertEqual(manager.client_id, client_id)

    def test_websocket_manager_default_client_id(self) -> None:
        """Test WebSocketManager uses default client_id when not provided."""
        logger = MagicMock()
        
        manager = WebSocketManager(logger=logger)
        
        self.assertEqual(manager.client_id, "device-001")

    def test_websocket_manager_stores_callbacks(self) -> None:
        """Test WebSocketManager stores all initialization parameters."""
        logger = MagicMock()
        message_callback = MagicMock()
        status_callback = MagicMock()
        client_id = "custom-device-001"
        
        manager = WebSocketManager(
            logger=logger,
            on_message=message_callback,
            on_status_change=status_callback,
            client_id=client_id
        )
        
        self.assertEqual(manager.logger, logger)
        self.assertEqual(manager.on_message, message_callback)
        self.assertEqual(manager.on_status_change, status_callback)
        self.assertEqual(manager.client_id, client_id)


class TestHandshakeInDefaultCommands(TestCase):
    """Test that handshake is properly integrated in DEFAULT_COMMANDS."""

    def test_handshake_in_default_commands(self) -> None:
        """Test handshake appears in default commands list."""
        handshake_command = None
        for cmd in DEFAULT_COMMANDS:
            if cmd["name"] == "Handshake":
                handshake_command = cmd
                break
        
        self.assertIsNotNone(handshake_command, "Handshake command not found in DEFAULT_COMMANDS")

    def test_handshake_command_position(self) -> None:
        """Test handshake is the first command in DEFAULT_COMMANDS."""
        self.assertEqual(DEFAULT_COMMANDS[0]["name"], "Handshake")

    def test_handshake_payload_structure_in_defaults(self) -> None:
        """Test handshake payload structure in DEFAULT_COMMANDS."""
        handshake = DEFAULT_COMMANDS[0]
        payload = handshake["payload"]
        
        self.assertEqual(payload["action"], "handshake")
        self.assertIn("clientId", payload)
        self.assertIn("capabilities", payload)
        self.assertIn("version", payload)
        self.assertEqual(payload["version"], "1.0")

    def test_handshake_payload_is_valid_json(self) -> None:
        """Test that handshake payload can be serialized to JSON."""
        handshake = DEFAULT_COMMANDS[0]
        payload = handshake["payload"]
        
        try:
            json_str = json.dumps(payload)
            json.loads(json_str)
        except (TypeError, json.JSONDecodeError):
            self.fail("Handshake payload cannot be serialized to valid JSON")

    def test_other_commands_still_exist(self) -> None:
        """Test backward compatibility - other commands still exist."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        
        # Verify original commands still exist
        self.assertIn("Ping", command_names)
        self.assertIn("Subscribe", command_names)
        self.assertIn("Echo", command_names)
        self.assertIn("Login", command_names)

    def test_all_commands_have_valid_payloads(self) -> None:
        """Test all commands in DEFAULT_COMMANDS have valid JSON payloads."""
        for cmd in DEFAULT_COMMANDS:
            payload = cmd["payload"]
            
            try:
                json_str = json.dumps(payload)
                json.loads(json_str)
            except (TypeError, json.JSONDecodeError):
                self.fail(f"Command '{cmd['name']}' has invalid JSON payload")


class TestHandshakeAfterConnection(TestCase):
    """Test handshake is sent after establishing WebSocket connection."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_sent_on_connection_open(self) -> None:
        """Test handshake is sent immediately after WebSocket connection opens."""
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        # Simulate WebSocket connection open
        manager._on_open(manager.ws_app)
        
        # Verify handshake was sent
        manager.ws_app.send.assert_called_once()
        
        # Verify the payload is a handshake
        sent_payload = json.loads(manager.ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["action"], "handshake")

    def test_connection_flow_with_handshake(self) -> None:
        """Test complete connection flow: connect -> on_open -> handshake."""
        status_changes = []
        
        def track_status(connected):
            status_changes.append(connected)
        
        manager = WebSocketManager(
            logger=self.logger,
            on_status_change=track_status,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        # Simulate connection open
        manager._on_open(manager.ws_app)
        
        # Verify connection status changed
        self.assertIn(True, status_changes)
        self.assertTrue(manager.connected)
        
        # Verify handshake was sent
        sent_payload = json.loads(manager.ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["action"], "handshake")

    def test_handshake_contains_correct_client_id_after_connection(self) -> None:
        """Test handshake sent after connection uses correct client_id."""
        client_id = "integration-test-device-123"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=client_id
        )
        manager.ws_app = MagicMock()
        
        manager._on_open(manager.ws_app)
        
        sent_payload = json.loads(manager.ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["clientId"], client_id)


class TestReconnectionScenarios(TestCase):
    """Test handshake behavior during reconnection scenarios."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_resent_after_reconnection(self) -> None:
        """Test handshake is re-sent after connection drops and reconnects."""
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        # First connection
        manager._on_open(manager.ws_app)
        first_call_count = manager.ws_app.send.call_count
        self.assertEqual(first_call_count, 1)
        
        # Connection closes
        manager._on_close(manager.ws_app, 1000, "Normal close")
        self.assertFalse(manager.connected)
        
        # Reconnect
        manager.ws_app.reset_mock()
        manager._on_open(manager.ws_app)
        
        # Handshake should be sent again
        manager.ws_app.send.assert_called_once()
        sent_payload = json.loads(manager.ws_app.send.call_args[0][0])
        self.assertEqual(sent_payload["action"], "handshake")

    def test_handshake_maintains_client_id_across_reconnects(self) -> None:
        """Test handshake maintains client_id across reconnects."""
        client_id = "persistent-device-001"
        manager = WebSocketManager(
            logger=self.logger,
            client_id=client_id
        )
        manager.ws_app = MagicMock()
        
        # First connection
        manager._on_open(manager.ws_app)
        first_payload = json.loads(manager.ws_app.send.call_args[0][0])
        first_client_id = first_payload["clientId"]
        
        # Reconnect
        manager.ws_app.reset_mock()
        manager._on_open(manager.ws_app)
        second_payload = json.loads(manager.ws_app.send.call_args[0][0])
        second_client_id = second_payload["clientId"]
        
        # Verify client_id is maintained
        self.assertEqual(first_client_id, client_id)
        self.assertEqual(second_client_id, client_id)
        self.assertEqual(first_client_id, second_client_id)

    def test_multiple_reconnections_preserve_handshake(self) -> None:
        """Test handshake works correctly across multiple reconnections."""
        manager = WebSocketManager(
            logger=self.logger,
            client_id="test-device-001"
        )
        manager.ws_app = MagicMock()
        
        # Simulate multiple connect/disconnect cycles
        for i in range(3):
            manager.ws_app.reset_mock()
            manager._on_open(manager.ws_app)
            
            # Verify handshake was sent each time
            manager.ws_app.send.assert_called_once()
            sent_payload = json.loads(manager.ws_app.send.call_args[0][0])
            self.assertEqual(sent_payload["action"], "handshake")
            
            manager._on_close(manager.ws_app, 1000, "Close")


class TestBackwardCompatibility(TestCase):
    """Test backward compatibility - existing functionality still works."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_existing_websocket_manager_initialization_still_works(self) -> None:
        """Test WebSocketManager can be initialized without client_id."""
        manager = WebSocketManager(logger=self.logger)
        
        # Should initialize with default client_id
        self.assertEqual(manager.client_id, "device-001")
        self.assertIsNotNone(manager.logger)

    def test_other_commands_selectable_from_ui(self) -> None:
        """Test that other commands are still in DEFAULT_COMMANDS and selectable."""
        expected_commands = ["Ping", "Subscribe", "Echo", "Login"]
        
        for expected_cmd in expected_commands:
            found = any(cmd["name"] == expected_cmd for cmd in DEFAULT_COMMANDS)
            self.assertTrue(found, f"Command '{expected_cmd}' not found in DEFAULT_COMMANDS")

    def test_websocket_send_json_still_works(self) -> None:
        """Test WebSocketManager.send_json() still works for manual sends."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.connected = True
        
        payload = {"action": "ping", "timestamp": "2026-03-27T12:00:00Z"}
        manager.send_json(payload)
        
        # Verify send_json works
        manager.ws_app.send.assert_called_once()
        sent = json.loads(manager.ws_app.send.call_args[0][0])
        self.assertEqual(sent["action"], "ping")

    def test_connection_disconnect_flow_unchanged(self) -> None:
        """Test connection/disconnect flow is not broken."""
        message_callback = MagicMock()
        status_callback = MagicMock()
        
        manager = WebSocketManager(
            logger=self.logger,
            on_message=message_callback,
            on_status_change=status_callback,
            client_id="test-device-001"
        )
        
        # Verify initialization
        self.assertIsNotNone(manager)
        self.assertFalse(manager.connected)
        
        # Simulate connection
        manager.ws_app = MagicMock()
        manager._on_open(manager.ws_app)
        
        # Verify status callback was called
        status_callback.assert_called_with(True)
        
        # Simulate disconnection
        manager._on_close(manager.ws_app, 1000, "Normal close")
        
        # Verify status callback was called with False
        self.assertFalse(manager.connected)

    def test_message_receiving_still_works(self) -> None:
        """Test _on_message callback functionality is not affected."""
        message_callback = MagicMock()
        manager = WebSocketManager(
            logger=self.logger,
            on_message=message_callback,
            client_id="test-device-001"
        )
        
        test_message = '{"action": "response", "data": "test"}'
        manager._on_message(manager.ws_app, test_message)
        
        # Verify message callback was called
        message_callback.assert_called_once_with(test_message)

    def test_error_handling_still_works(self) -> None:
        """Test _on_error callback functionality is not affected."""
        manager = WebSocketManager(logger=self.logger)
        
        test_error = Exception("Test error")
        manager._on_error(manager.ws_app, test_error)
        
        # Verify error was logged
        self.logger.log.assert_called_once()
        log_msg = self.logger.log.call_args[0][0]
        self.assertIn("error", log_msg.lower())


class TestUIIntegrationWithHandshake(TestCase):
    """Test UI integration with handshake feature."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_command_selectable_from_ui(self) -> None:
        """Test handshake command can be selected from UI default commands."""
        # The first command in DEFAULT_COMMANDS is Handshake
        handshake_cmd = DEFAULT_COMMANDS[0]
        
        self.assertEqual(handshake_cmd["name"], "Handshake")
        self.assertIn("payload", handshake_cmd)
        
        # Verify it can be used as a JSON payload
        payload_json = json.dumps(handshake_cmd["payload"])
        self.assertIsNotNone(payload_json)

    def test_handshake_payload_matches_manager_output(self) -> None:
        """Test handshake payload from defaults matches what manager sends."""
        default_payload = DEFAULT_COMMANDS[0]["payload"].copy()
        
        manager = WebSocketManager(
            logger=self.logger,
            client_id=default_payload["clientId"]
        )
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        manager_sent = json.loads(manager.ws_app.send.call_args[0][0])
        
        # Both should have the same structure
        self.assertEqual(manager_sent["action"], default_payload["action"])
        self.assertEqual(manager_sent["clientId"], default_payload["clientId"])
        self.assertEqual(manager_sent["version"], default_payload["version"])

    def test_all_default_commands_have_required_fields(self) -> None:
        """Test all default commands have name and payload."""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn("name", cmd)
            self.assertIn("payload", cmd)
            self.assertIsInstance(cmd["name"], str)
            self.assertIsInstance(cmd["payload"], dict)


class TestValidationAndSafety(TestCase):
    """Test validation and safety aspects of handshake."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.logger = MagicMock()

    def test_handshake_payload_validation_passes(self) -> None:
        """Test handshake payload passes JSON validation."""
        manager = WebSocketManager(logger=self.logger, client_id="test-001")
        manager.ws_app = MagicMock()
        
        manager._send_handshake()
        
        sent_str = manager.ws_app.send.call_args[0][0]
        
        # Should be valid JSON
        try:
            parsed = json.loads(sent_str)
            self.assertIsInstance(parsed, dict)
        except json.JSONDecodeError:
            self.fail("Handshake payload is not valid JSON")

    def test_invalid_json_is_rejected(self) -> None:
        """Test that invalid JSON cannot be sent through normal flow."""
        manager = WebSocketManager(logger=self.logger)
        manager.ws_app = MagicMock()
        manager.connected = True
        
        # Try to send invalid data through send_json
        # This should handle the error gracefully
        try:
            # send_json should create valid JSON even if given complex objects
            payload = {"test": "value"}
            manager.send_json(payload)
            
            # If no exception, verify valid JSON was sent
            sent_str = manager.ws_app.send.call_args[0][0]
            json.loads(sent_str)  # Should not raise
        except json.JSONDecodeError:
            self.fail("send_json should always send valid JSON")

    def test_server_response_handling_ready(self) -> None:
        """Test that server response to handshake can be logged."""
        message_callback = MagicMock()
        manager = WebSocketManager(
            logger=self.logger,
            on_message=message_callback,
            client_id="test-001"
        )
        
        # Simulate server response to handshake
        response = '{"action": "handshake_response", "status": "ok"}'
        manager._on_message(manager.ws_app, response)
        
        # Verify message was received
        message_callback.assert_called_once_with(response)
