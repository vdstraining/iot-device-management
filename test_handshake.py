import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from ws_client import WebSocketManager
from utilities import validate_handshake, AppLogger, DEFAULT_COMMANDS


class TestHandshakeValidation:
    """Test handshake message validation."""

    def test_valid_handshake(self):
        """Test that valid handshake payload passes validation."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "token": "auth-token",
        }
        assert validate_handshake(payload) is True

    def test_missing_action(self):
        """Test that missing action field fails validation."""
        payload = {
            "clientId": "client-001",
            "token": "auth-token",
        }
        assert validate_handshake(payload) is False

    def test_missing_clientId(self):
        """Test that missing clientId field fails validation."""
        payload = {
            "action": "handshake",
            "token": "auth-token",
        }
        assert validate_handshake(payload) is False

    def test_missing_token(self):
        """Test that missing token field fails validation."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
        }
        assert validate_handshake(payload) is False

    def test_empty_clientId(self):
        """Test that empty clientId fails validation."""
        payload = {
            "action": "handshake",
            "clientId": "",
            "token": "auth-token",
        }
        assert validate_handshake(payload) is False

    def test_empty_token(self):
        """Test that empty token fails validation."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "token": "",
        }
        assert validate_handshake(payload) is False

    def test_none_clientId(self):
        """Test that None clientId fails validation."""
        payload = {
            "action": "handshake",
            "clientId": None,
            "token": "auth-token",
        }
        assert validate_handshake(payload) is False

    def test_wrong_action(self):
        """Test that wrong action fails validation."""
        payload = {
            "action": "ping",
            "clientId": "client-001",
            "token": "auth-token",
        }
        assert validate_handshake(payload) is False

    def test_non_dict_payload(self):
        """Test that non-dict payload fails validation."""
        assert validate_handshake("not a dict") is False
        assert validate_handshake(None) is False
        assert validate_handshake([]) is False


class TestWebSocketHandshake:
    """Test WebSocket handshake functionality."""

    def test_handshake_sent_on_connection(self):
        """Test that handshake is sent automatically after connection."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        with patch.object(ws_manager, "ws_app") as mock_ws:
            mock_ws.send = Mock()
            ws_manager.connected = True
            ws_manager._send_handshake()
            
            assert ws_manager.handshake_sent is True
            mock_ws.send.assert_called_once()

    def test_handshake_not_sent_if_already_sent(self):
        """Test that handshake is not sent twice."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        with patch.object(ws_manager, "ws_app") as mock_ws:
            mock_ws.send = Mock()
            ws_manager.connected = True
            ws_manager.handshake_sent = True
            
            ws_manager._send_handshake()
            mock_ws.send.assert_not_called()

    def test_handshake_reset_on_disconnect(self):
        """Test that handshake_sent flag is reset on disconnect."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        ws_manager.handshake_sent = True
        ws_manager._set_connected(False)
        
        assert ws_manager.handshake_sent is False
        assert ws_manager.connected is False

    def test_handshake_validation_in_send(self):
        """Test that handshake validation is checked before sending."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        with patch.object(ws_manager, "_validate_handshake", return_value=False):
            with patch.object(ws_manager, "ws_app") as mock_ws:
                mock_ws.send = Mock()
                ws_manager.connected = True
                ws_manager._send_handshake()
                
                mock_ws.send.assert_not_called()
                mock_logger.log.assert_called()

    def test_handshake_payload_structure(self):
        """Test that handshake payload has correct structure."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        with patch.object(ws_manager, "ws_app") as mock_ws:
            mock_ws.send = Mock()
            ws_manager.connected = True
            ws_manager._send_handshake()
            
            call_args = mock_ws.send.call_args
            sent_payload = json.loads(call_args[0][0])
            
            assert sent_payload["action"] == "handshake"
            assert "clientId" in sent_payload
            assert "token" in sent_payload

    def test_handshake_response_logging(self):
        """Test that handshake responses are logged."""
        mock_logger = Mock(spec=AppLogger)
        on_message_callback = Mock()
        
        ws_manager = WebSocketManager(
            logger=mock_logger,
            on_message=on_message_callback
        )
        
        handshake_response = json.dumps({
            "action": "handshake_ack",
            "status": "success"
        })
        
        ws_manager._on_message(None, handshake_response)
        
        assert mock_logger.log.called
        assert on_message_callback.called

    def test_on_open_calls_handshake(self):
        """Test that _on_open calls _send_handshake."""
        mock_logger = Mock(spec=AppLogger)
        ws_manager = WebSocketManager(logger=mock_logger)
        
        with patch.object(ws_manager, "_send_handshake") as mock_send:
            ws_manager._on_open(None)
            mock_send.assert_called_once()
            assert ws_manager.connected is True


class TestDefaultCommands:
    """Test DEFAULT_COMMANDS list."""

    def test_handshake_in_default_commands(self):
        """Test that handshake is in DEFAULT_COMMANDS."""
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"]
        assert len(handshake_commands) == 1

    def test_handshake_command_structure(self):
        """Test handshake command has correct structure."""
        handshake_cmd = next(cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake")
        
        assert "name" in handshake_cmd
        assert "payload" in handshake_cmd
        assert handshake_cmd["payload"]["action"] == "handshake"
        assert "clientId" in handshake_cmd["payload"]
        assert "token" in handshake_cmd["payload"]

    def test_handshake_is_first_command(self):
        """Test that handshake is the first command in the list."""
        assert DEFAULT_COMMANDS[0]["name"] == "Handshake"


class TestWebSocketManagerValidation:
    """Test WebSocketManager validation method."""

    def test_validate_handshake_valid(self):
        """Test static validation method with valid payload."""
        payload = {
            "action": "handshake",
            "clientId": "test-client",
            "token": "test-token",
        }
        assert WebSocketManager._validate_handshake(payload) is True

    def test_validate_handshake_invalid_action(self):
        """Test validation with invalid action."""
        payload = {
            "action": "wrong",
            "clientId": "test-client",
            "token": "test-token",
        }
        assert WebSocketManager._validate_handshake(payload) is False

    def test_validate_handshake_whitespace_only(self):
        """Test validation rejects whitespace-only values."""
        payload = {
            "action": "handshake",
            "clientId": "   ",
            "token": "test-token",
        }
        assert WebSocketManager._validate_handshake(payload) is False
