import json
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

from ws_client import WebSocketManager
from utilities import AppLogger, DEFAULT_COMMANDS


class TestHandshakeMessageStructure(unittest.TestCase):
    """Test handshake message structure and payload."""

    def test_handshake_in_default_commands(self):
        """Verify handshake command is in DEFAULT_COMMANDS."""
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"]
        self.assertEqual(len(handshake_commands), 1, "Handshake command should be in DEFAULT_COMMANDS")

    def test_handshake_payload_structure(self):
        """Verify handshake payload has required fields."""
        handshake = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"][0]
        payload = handshake["payload"]
        
        self.assertEqual(payload["action"], "handshake")
        self.assertIn("clientId", payload)
        self.assertIn("clientVersion", payload)
        self.assertIn("capabilities", payload)
        self.assertIn("timestamp", payload)

    def test_handshake_capabilities(self):
        """Verify handshake includes expected capabilities."""
        handshake = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"][0]
        payload = handshake["payload"]
        
        capabilities = payload["capabilities"]
        self.assertIn("WebSocket", capabilities)
        self.assertIn("HTTP", capabilities)


class TestWebSocketManagerHandshake(unittest.TestCase):
    """Test WebSocketManager handshake functionality."""

    def setUp(self):
        """Setup mock logger and WebSocketManager."""
        self.mock_logger = Mock(spec=AppLogger)
        self.ws_manager = WebSocketManager(
            logger=self.mock_logger,
            on_handshake_sent=Mock()
        )

    def test_handshake_config_initialization(self):
        """Verify handshake config initializes with defaults."""
        self.assertIn("clientId", self.ws_manager.handshake_config)
        self.assertIn("clientVersion", self.ws_manager.handshake_config)
        self.assertIn("capabilities", self.ws_manager.handshake_config)
        self.assertEqual(self.ws_manager.handshake_config["clientId"], "default-client")

    def test_set_handshake_config(self):
        """Test updating handshake config."""
        new_config = {
            "clientId": "custom-client",
            "token": "abc123"
        }
        self.ws_manager.set_handshake_config(new_config)
        
        self.assertEqual(self.ws_manager.handshake_config["clientId"], "custom-client")
        self.assertEqual(self.ws_manager.handshake_config["token"], "abc123")
        self.mock_logger.log.assert_called()

    def test_auto_send_handshake_enabled_by_default(self):
        """Verify auto-send handshake is enabled by default."""
        self.assertTrue(self.ws_manager.auto_send_handshake)

    def test_set_auto_send_handshake_disabled(self):
        """Test disabling auto-send handshake."""
        self.ws_manager.set_auto_send_handshake(False)
        self.assertFalse(self.ws_manager.auto_send_handshake)
        self.mock_logger.log.assert_called()

    def test_build_handshake_payload(self):
        """Test building handshake payload."""
        payload = self.ws_manager._build_handshake_payload()
        
        self.assertEqual(payload["action"], "handshake")
        self.assertEqual(payload["clientId"], "default-client")
        self.assertIn("timestamp", payload)
        self.assertIsInstance(payload["capabilities"], list)

    def test_build_handshake_payload_with_custom_config(self):
        """Test building handshake payload with custom config."""
        self.ws_manager.set_handshake_config({"clientId": "my-device"})
        payload = self.ws_manager._build_handshake_payload()
        
        self.assertEqual(payload["clientId"], "my-device")

    def test_send_handshake_not_connected(self):
        """Test send_handshake when not connected."""
        self.ws_manager.connected = False
        self.ws_manager.send_handshake()
        
        self.mock_logger.log.assert_called_with("Cannot send handshake: WebSocket not connected.")

    @patch.object(WebSocketManager, 'send_json')
    def test_send_handshake_when_connected(self, mock_send_json):
        """Test send_handshake when connected."""
        self.ws_manager.connected = True
        self.ws_manager.ws_app = MagicMock()
        
        self.ws_manager.send_handshake()
        
        mock_send_json.assert_called_once()
        self.ws_manager.on_handshake_sent.assert_called_once()

    def test_on_open_sends_handshake_auto(self):
        """Test that _on_open sends handshake when auto_send_handshake is True."""
        with patch.object(self.ws_manager, 'send_handshake') as mock_send:
            self.ws_manager.auto_send_handshake = True
            self.ws_manager._on_open(None)
            
            mock_send.assert_called_once()

    def test_on_open_no_handshake_when_disabled(self):
        """Test that _on_open does not send handshake when auto_send_handshake is False."""
        with patch.object(self.ws_manager, 'send_handshake') as mock_send:
            self.ws_manager.auto_send_handshake = False
            self.ws_manager._on_open(None)
            
            mock_send.assert_not_called()

    def test_on_message_recognizes_handshake_response(self):
        """Test that _on_message recognizes handshake response."""
        response_msg = json.dumps({"action": "handshake_response", "status": "success"})
        
        with patch.object(self.ws_manager, 'on_message') as mock_on_msg:
            self.ws_manager._on_message(None, response_msg)
            mock_on_msg.assert_called_once()


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake functionality."""

    def test_handshake_json_serializable(self):
        """Test that handshake payload is JSON serializable."""
        handshake = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"][0]
        try:
            json_str = json.dumps(handshake["payload"])
            parsed = json.loads(json_str)
            self.assertEqual(parsed["action"], "handshake")
        except (TypeError, json.JSONDecodeError):
            self.fail("Handshake payload should be JSON serializable")

    def test_handshake_timestamp_format(self):
        """Test handshake timestamp is in ISO format."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        payload = ws_manager._build_handshake_payload()
        
        timestamp_str = payload["timestamp"]
        try:
            # Try to parse as ISO format with Z suffix
            datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"Timestamp '{timestamp_str}' is not in valid ISO format")

    def test_multiple_handshakes_have_different_timestamps(self):
        """Test that multiple handshakes have different timestamps."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        payload1 = ws_manager._build_handshake_payload()
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        payload2 = ws_manager._build_handshake_payload()
        
        self.assertNotEqual(payload1["timestamp"], payload2["timestamp"])


class TestHandshakeConfiguration(unittest.TestCase):
    """Test handshake configuration support."""

    def test_dynamic_clientid_configuration(self):
        """Test dynamic clientId configuration."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        ws_manager.set_handshake_config({"clientId": "device-12345"})
        payload = ws_manager._build_handshake_payload()
        
        self.assertEqual(payload["clientId"], "device-12345")

    def test_dynamic_version_configuration(self):
        """Test dynamic clientVersion configuration."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        ws_manager.set_handshake_config({"clientVersion": "2.0.0"})
        payload = ws_manager._build_handshake_payload()
        
        self.assertEqual(payload["clientVersion"], "2.0.0")

    def test_dynamic_capabilities_configuration(self):
        """Test dynamic capabilities configuration."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        new_caps = ["WebSocket", "HTTP", "MQTT"]
        ws_manager.set_handshake_config({"capabilities": new_caps})
        payload = ws_manager._build_handshake_payload()
        
        self.assertEqual(payload["capabilities"], new_caps)

    def test_additional_fields_in_config(self):
        """Test that additional fields can be added to config."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        ws_manager.set_handshake_config({"token": "secret-token", "sessionId": "sess-123"})
        
        self.assertEqual(ws_manager.handshake_config["token"], "secret-token")
        self.assertEqual(ws_manager.handshake_config["sessionId"], "sess-123")


if __name__ == "__main__":
    unittest.main()
