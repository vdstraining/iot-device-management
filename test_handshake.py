import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

from utilities import generate_handshake, DEFAULT_COMMANDS
from ws_client import WebSocketManager


class TestHandshakeGeneration(unittest.TestCase):
    """Test suite for handshake message generation"""

    def test_generate_handshake_default_values(self):
        """Test handshake generation with default parameters"""
        handshake = generate_handshake()
        
        self.assertEqual(handshake["action"], "handshake")
        self.assertEqual(handshake["type"], "client-init")
        self.assertEqual(handshake["version"], "1.0")
        self.assertIsNotNone(handshake["clientId"])
        self.assertIsNotNone(handshake["timestamp"])
        self.assertIsInstance(handshake["capabilities"], list)
        self.assertIsInstance(handshake["metadata"], dict)

    def test_generate_handshake_custom_client_id(self):
        """Test handshake with custom client ID"""
        custom_id = "test-client-123"
        handshake = generate_handshake(client_id=custom_id)
        
        self.assertEqual(handshake["clientId"], custom_id)

    def test_generate_handshake_custom_version(self):
        """Test handshake with custom protocol version"""
        custom_version = "2.0"
        handshake = generate_handshake(version=custom_version)
        
        self.assertEqual(handshake["version"], custom_version)

    def test_generate_handshake_custom_capabilities(self):
        """Test handshake with custom capabilities list"""
        custom_capabilities = ["websocket", "http", "custom-feature"]
        handshake = generate_handshake(capabilities=custom_capabilities)
        
        self.assertEqual(handshake["capabilities"], custom_capabilities)

    def test_generate_handshake_custom_metadata(self):
        """Test handshake with custom metadata"""
        custom_metadata = {"user": "test_user", "session": "abc123"}
        handshake = generate_handshake(metadata=custom_metadata)
        
        self.assertEqual(handshake["metadata"], custom_metadata)

    def test_generate_handshake_timestamp_format(self):
        """Test that timestamp is in ISO format with Z suffix"""
        handshake = generate_handshake()
        timestamp = handshake["timestamp"]
        
        self.assertTrue(timestamp.endswith("Z"))
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(timestamp.rstrip("Z"))

    def test_generate_handshake_is_valid_json(self):
        """Test that generated handshake can be serialized to JSON"""
        handshake = generate_handshake()
        json_str = json.dumps(handshake)
        
        self.assertIsInstance(json_str, str)
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        self.assertEqual(parsed, handshake)

    def test_generate_handshake_unique_client_ids(self):
        """Test that auto-generated client IDs are unique"""
        handshake1 = generate_handshake()
        handshake2 = generate_handshake()
        
        self.assertNotEqual(handshake1["clientId"], handshake2["clientId"])


class TestDefaultCommandsHandshake(unittest.TestCase):
    """Test suite for handshake in DEFAULT_COMMANDS"""

    def test_handshake_in_default_commands(self):
        """Test that Handshake is in DEFAULT_COMMANDS list"""
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"]
        
        self.assertEqual(len(handshake_commands), 1)
        handshake = handshake_commands[0]
        self.assertEqual(handshake["name"], "Handshake")

    def test_handshake_command_structure(self):
        """Test Handshake command has proper structure"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        self.assertIsNotNone(handshake_cmd)
        payload = handshake_cmd["payload"]
        
        required_fields = ["action", "type", "clientId", "version", "timestamp", "capabilities", "metadata"]
        for field in required_fields:
            self.assertIn(field, payload)

    def test_handshake_is_first_command(self):
        """Test that Handshake command is first in the list"""
        self.assertEqual(DEFAULT_COMMANDS[0]["name"], "Handshake")

    def test_other_commands_still_present(self):
        """Test that existing commands are still in the list"""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        
        self.assertIn("Ping", command_names)
        self.assertIn("Login", command_names)
        self.assertIn("Subscribe", command_names)
        self.assertIn("Echo", command_names)


class TestWebSocketHandshake(unittest.TestCase):
    """Test suite for WebSocket handshake integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        self.mock_logger.log = Mock()

    def test_websocket_manager_has_handshake_callback(self):
        """Test that WebSocketManager accepts handshake response callback"""
        mock_callback = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_response=mock_callback
        )
        
        self.assertEqual(manager.on_handshake_response, mock_callback)

    def test_websocket_manager_auto_handshake_enabled_by_default(self):
        """Test that auto_handshake is enabled by default"""
        manager = WebSocketManager(logger=self.mock_logger)
        
        self.assertTrue(manager.auto_handshake)

    def test_websocket_manager_auto_handshake_can_be_disabled(self):
        """Test that auto_handshake can be disabled"""
        manager = WebSocketManager(logger=self.mock_logger, auto_handshake=False)
        
        self.assertFalse(manager.auto_handshake)

    @patch('ws_client.WebSocketApp')
    def test_handshake_sent_on_connection(self, mock_ws_app):
        """Test that handshake is sent when WebSocket connects"""
        manager = WebSocketManager(logger=self.mock_logger)
        
        # Simulate connection by calling _on_open
        manager._on_open(None)
        
        # Verify connection status changed
        self.assertTrue(manager.connected)
        self.mock_logger.log.assert_called()

    def test_handshake_response_handling(self):
        """Test that handshake responses are properly handled"""
        mock_callback = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_response=mock_callback
        )
        
        # Simulate receiving a handshake response
        handshake_response = json.dumps({
            "action": "handshake",
            "status": "accepted",
            "serverId": "server-001"
        })
        
        manager._on_message(None, handshake_response)
        
        # Verify callback was invoked with parsed response
        mock_callback.assert_called_once()
        called_data = mock_callback.call_args[0][0]
        self.assertEqual(called_data["action"], "handshake")
        self.assertEqual(called_data["status"], "accepted")

    def test_non_handshake_messages_not_triggering_callback(self):
        """Test that non-handshake messages don't trigger handshake callback"""
        mock_callback = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_response=mock_callback
        )
        
        # Simulate receiving a regular message
        regular_message = json.dumps({
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z"
        })
        
        manager._on_message(None, regular_message)
        
        # Handshake callback should not be called
        mock_callback.assert_not_called()

    def test_malformed_json_response_handling(self):
        """Test that malformed JSON responses are handled gracefully"""
        mock_callback = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_response=mock_callback,
            on_message=Mock()
        )
        
        # Simulate receiving malformed JSON
        malformed_message = "{ invalid json }"
        
        # Should not raise exception
        manager._on_message(None, malformed_message)
        
        # on_message callback should still be called with raw message
        manager.on_message.assert_called_once_with(malformed_message)

    @patch('utilities.generate_handshake')
    def test_send_handshake_uses_generate_function(self, mock_generate):
        """Test that _send_handshake uses the generate_handshake function"""
        test_handshake = {"action": "handshake", "clientId": "test-123"}
        mock_generate.return_value = test_handshake
        
        manager = WebSocketManager(logger=self.mock_logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        # Mock json.dumps to track calls
        with patch('ws_client.json.dumps', return_value='{}'):
            manager._send_handshake()
        
        # Verify generate_handshake was called
        mock_generate.assert_called_once()


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake feature"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock()
        self.mock_logger.log = Mock()

    def test_handshake_message_format_compatibility(self):
        """Test that generated handshake matches expected message format"""
        handshake = generate_handshake(
            client_id="integration-test-client",
            metadata={"app": "test-app", "version": "1.0"}
        )
        
        # Verify required fields
        required = ["action", "type", "clientId", "version", "timestamp", "capabilities", "metadata"]
        for field in required:
            self.assertIn(field, handshake, f"Missing required field: {field}")
        
        # Verify field values
        self.assertEqual(handshake["action"], "handshake")
        self.assertEqual(handshake["type"], "client-init")
        self.assertEqual(handshake["clientId"], "integration-test-client")
        self.assertEqual(handshake["version"], "1.0")
        self.assertIn("app", handshake["metadata"])

    def test_full_handshake_flow_simulation(self):
        """Test a simulated full handshake flow"""
        # Create manager with callbacks
        handshake_responses = []
        
        def on_handshake(response):
            handshake_responses.append(response)
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_response=on_handshake,
            auto_handshake=True
        )
        
        # Verify manager is initialized correctly
        self.assertTrue(manager.auto_handshake)
        
        # Simulate server responding to handshake
        server_response = json.dumps({
            "action": "handshake",
            "status": "accepted",
            "serverId": "server-001",
            "protocolVersion": "1.0"
        })
        
        manager._on_message(None, server_response)
        
        # Verify response was captured
        self.assertEqual(len(handshake_responses), 1)
        self.assertEqual(handshake_responses[0]["status"], "accepted")


if __name__ == "__main__":
    unittest.main()
