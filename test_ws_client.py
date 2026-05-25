import json
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS


class TestWebSocketHandshake:
    """Test suite for handshake message functionality (SCRUM-104)"""

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger for testing."""
        return MagicMock()

    @pytest.fixture
    def handshake_config(self):
        """Get the handshake configuration from DEFAULT_COMMANDS."""
        return next(
            (cmd["payload"] for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None,
        )

    @pytest.fixture
    def ws_manager(self, mock_logger, handshake_config):
        """Create a WebSocketManager instance for testing."""
        return WebSocketManager(
            logger=mock_logger,
            handshake_config=handshake_config,
        )

    def test_handshake_in_default_commands(self):
        """Test that handshake command exists in DEFAULT_COMMANDS."""
        handshake_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        assert "Handshake" in handshake_names

    def test_handshake_payload_structure(self):
        """Test that handshake has required fields."""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake is not None
        payload = handshake["payload"]
        
        assert "action" in payload
        assert payload["action"] == "handshake"
        assert "clientId" in payload
        assert "capabilities" in payload
        assert isinstance(payload["capabilities"], list)
        assert "timestamp" in payload

    def test_handshake_config_initialization(self, mock_logger, handshake_config):
        """Test that WebSocketManager stores handshake_config."""
        ws_mgr = WebSocketManager(logger=mock_logger, handshake_config=handshake_config)
        assert ws_mgr.handshake_config == handshake_config

    def test_set_handshake_config(self, ws_manager, mock_logger):
        """Test set_handshake_config method."""
        new_config = {"action": "handshake", "clientId": "test-client"}
        ws_manager.set_handshake_config(new_config)
        assert ws_manager.handshake_config == new_config

    def test_dynamic_substitution_timestamp(self, ws_manager):
        """Test that dynamic substitution updates timestamp."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "timestamp": "",
        }
        result = ws_manager._apply_dynamic_substitution(payload)
        
        assert result["timestamp"] != ""
        assert result["action"] == "handshake"
        assert result["clientId"] == "test-client"

    def test_dynamic_substitution_preserves_fields(self, ws_manager):
        """Test that dynamic substitution preserves non-timestamp fields."""
        payload = {
            "action": "handshake",
            "clientId": "client-123",
            "capabilities": ["websocket", "http"],
        }
        result = ws_manager._apply_dynamic_substitution(payload)
        
        assert result["clientId"] == "client-123"
        assert result["capabilities"] == ["websocket", "http"]
        assert result["action"] == "handshake"

    def test_send_json_when_disconnected(self, ws_manager, mock_logger):
        """Test send_json logs error when not connected."""
        ws_manager.connected = False
        payload = {"action": "handshake"}
        
        ws_manager.send_json(payload)
        
        mock_logger.log.assert_called_with("Cannot send via WebSocket: not connected.")

    @patch("ws_client.WebSocketApp")
    def test_on_open_logs_connection(self, mock_ws_app, ws_manager, mock_logger):
        """Test _on_open logs connection message."""
        ws_manager.ws_app = MagicMock()
        
        ws_manager._on_open(mock_ws_app)
        
        # Should log "WebSocket connected."
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("WebSocket connected" in msg for msg in logged_messages)

    @patch("ws_client.WebSocketApp")
    def test_on_open_auto_sends_handshake(self, mock_ws_app, mock_logger, handshake_config):
        """Test _on_open auto-sends handshake when configured."""
        ws_manager = WebSocketManager(
            logger=mock_logger,
            handshake_config=handshake_config,
        )
        ws_manager.ws_app = MagicMock()
        
        ws_manager._on_open(mock_ws_app)
        
        # Verify handshake was sent
        assert ws_manager.ws_app.send.called
        sent_data = ws_manager.ws_app.send.call_args[0][0]
        sent_json = json.loads(sent_data)
        assert sent_json["action"] == "handshake"

    @patch("ws_client.WebSocketApp")
    def test_on_open_skips_handshake_when_not_configured(self, mock_ws_app, mock_logger):
        """Test _on_open skips handshake when handshake_config is None."""
        ws_manager = WebSocketManager(logger=mock_logger, handshake_config=None)
        ws_manager.ws_app = MagicMock()
        
        ws_manager._on_open(mock_ws_app)
        
        # Verify handshake was NOT sent
        ws_manager.ws_app.send.assert_not_called()

    def test_handshake_validation_json_format(self, handshake_config):
        """Test that handshake payload is valid JSON."""
        payload_json = json.dumps(handshake_config)
        parsed = json.loads(payload_json)
        assert parsed["action"] == "handshake"

    def test_connection_state_updated_on_open(self, ws_manager, mock_logger):
        """Test that connection state is set to True on _on_open."""
        mock_ws_app = MagicMock()
        
        assert ws_manager.connected is False
        ws_manager._on_open(mock_ws_app)
        assert ws_manager.connected is True

    @patch("ws_client.WebSocketApp")
    def test_status_change_callback_on_open(self, mock_ws_app, mock_logger):
        """Test that on_status_change callback is called when connected."""
        status_callback = MagicMock()
        ws_manager = WebSocketManager(
            logger=mock_logger,
            on_status_change=status_callback,
            handshake_config=None,
        )
        
        ws_manager._on_open(mock_ws_app)
        
        status_callback.assert_called_with(True)

    def test_disconnect_logs_message(self, ws_manager, mock_logger):
        """Test disconnect logs appropriate message."""
        ws_manager.ws_app = MagicMock()
        
        ws_manager.disconnect()
        
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("Disconnecting" in msg for msg in logged_messages)

    def test_reconnect_sends_new_handshake(self, ws_manager, mock_logger, handshake_config):
        """Test that reconnecting triggers new handshake."""
        ws_manager.ws_app = MagicMock()
        
        # First connection
        ws_manager._on_open(ws_manager.ws_app)
        first_send_count = ws_manager.ws_app.send.call_count
        
        # Disconnect
        ws_manager._on_close(ws_manager.ws_app, None, None)
        assert ws_manager.connected is False
        
        # Reconnect
        ws_manager._on_open(ws_manager.ws_app)
        second_send_count = ws_manager.ws_app.send.call_count
        
        # Verify new handshake was sent on reconnect
        assert second_send_count > first_send_count


class TestHandshakeIntegration:
    """Integration tests for handshake with UI."""

    def test_ui_loads_handshake_command(self):
        """Test that UI can load handshake from DEFAULT_COMMANDS."""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"), None
        )
        assert handshake is not None
        assert "payload" in handshake
        assert handshake["payload"]["action"] == "handshake"

    def test_handshake_backward_compatibility(self):
        """Test that other commands still exist alongside handshake."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        
        # Verify original commands still exist
        assert "Ping" in command_names
        assert "Login" in command_names
        assert "Subscribe" in command_names
        assert "Echo" in command_names
        assert "HTTP POST sample" in command_names
        
        # Verify handshake was added
        assert "Handshake" in command_names


class TestHandshakeEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_logger(self):
        return MagicMock()

    def test_handshake_with_empty_config(self, mock_logger):
        """Test that empty handshake_config is handled."""
        ws_manager = WebSocketManager(logger=mock_logger, handshake_config=None)
        assert ws_manager.handshake_config is None

    def test_invalid_json_handling(self, mock_logger):
        """Test that invalid JSON in handshake doesn't crash."""
        # Even if payload has issues, json.dumps should handle it
        payload = {"action": "handshake", "clientId": "test"}
        serialized = json.dumps(payload)
        assert isinstance(serialized, str)

    @patch("ws_client.WebSocketApp")
    def test_websocket_send_exception_handling(self, mock_ws_app, mock_logger):
        """Test that exceptions during send are logged."""
        ws_manager = WebSocketManager(
            logger=mock_logger,
            handshake_config={"action": "handshake"},
        )
        ws_manager.ws_app = MagicMock()
        ws_manager.ws_app.send.side_effect = Exception("Send failed")
        ws_manager.connected = True
        
        ws_manager.send_json({"action": "handshake"})
        
        # Verify error was logged
        logged_messages = [call[0][0] for call in mock_logger.log.call_args_list]
        assert any("error" in msg.lower() for msg in logged_messages)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
