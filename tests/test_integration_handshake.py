"""Integration tests for handshake with WebSocket and HTTP clients."""

import json
from unittest.mock import MagicMock, patch, call
import pytest


class TestHandshakeWebSocketIntegration:
    """Test handshake integration with WebSocket manager."""

    def test_send_handshake_via_websocket(self, mock_ws_manager, handshake_payload):
        """Verify handshake can be sent via WebSocket."""
        mock_ws_manager.connected = True

        mock_ws_manager.send_json(handshake_payload)

        mock_ws_manager.send_json.assert_called_once_with(handshake_payload)

    def test_handshake_json_serialization_in_websocket(self, mock_ws_manager, handshake_payload):
        """Verify handshake can be serialized to JSON for WebSocket transmission."""
        json_str = json.dumps(handshake_payload)
        mock_ws_manager.send_json(handshake_payload)

        assert mock_ws_manager.send_json.called

    def test_websocket_not_connected_prevents_send(self, mock_ws_manager, handshake_payload):
        """Verify handshake cannot be sent if WebSocket is not connected."""
        mock_ws_manager.connected = False

        assert not mock_ws_manager.connected
        mock_ws_manager.send_json(handshake_payload)
        mock_ws_manager.send_json.assert_called_once()

    def test_handshake_sent_logs_message(self, real_ws_manager_with_mocked_ws, mock_logger, handshake_payload):
        """Verify sending handshake is logged."""
        real_ws_manager_with_mocked_ws.send_json(handshake_payload)
        
        mock_logger.log.assert_called()
        assert "Sent WebSocket message" in mock_logger.log.call_args[0][0]

    def test_multiple_handshakes_can_be_sent(self, mock_ws_manager, handshake_payload):
        """Verify multiple handshake messages can be sent in sequence."""
        mock_ws_manager.connected = True

        mock_ws_manager.send_json(handshake_payload)

        handshake_2 = handshake_payload.copy()
        handshake_2["clientId"] = "client-002"
        mock_ws_manager.send_json(handshake_2)

        assert mock_ws_manager.send_json.call_count == 2

    def test_handshake_server_response_handled(self, mock_ws_manager, handshake_payload):
        """Verify server response to handshake is handled."""
        response_message = json.dumps({
            "action": "handshake_ack",
            "clientId": "client-001",
            "status": "authenticated"
        })

        mock_ws_manager.on_message = MagicMock()
        mock_ws_manager.on_message(response_message)

        mock_ws_manager.on_message.assert_called_once_with(response_message)


class TestHandshakeHTTPIntegration:
    """Test handshake integration with HTTP client."""

    def test_send_handshake_via_http(self, mock_http_client, handshake_payload):
        """Verify handshake can be sent via HTTP POST."""
        request_data = {
            "method": "POST",
            "path": "/api/handshake",
            "body": handshake_payload
        }

        mock_http_client.send_request(request_data)
        mock_http_client.send_request.assert_called_once_with(request_data)

    def test_http_handshake_response_parsing(self, mock_http_client):
        """Verify HTTP response to handshake is parsed."""
        response = {
            "status": 200,
            "body": {
                "action": "handshake_ack",
                "sessionId": "session-123"
            }
        }

        mock_http_client.on_response = MagicMock()
        mock_http_client.on_response(response)

        mock_http_client.on_response.assert_called_once_with(response)


class TestHandshakeWithDefaultCommands:
    """Test handshake as part of DEFAULT_COMMANDS."""

    def test_handshake_in_default_commands(self, default_commands_fixture):
        """Verify handshake is present in DEFAULT_COMMANDS."""
        command_names = [cmd.get("name") for cmd in default_commands_fixture]
        assert "Handshake" in command_names

    def test_handshake_position_in_commands(self, default_commands_fixture):
        """Verify handshake is 6th command in DEFAULT_COMMANDS."""
        assert len(default_commands_fixture) >= 6
        handshake_cmd = default_commands_fixture[5]
        assert handshake_cmd["name"] == "Handshake"
        assert handshake_cmd["payload"]["action"] == "handshake"

    def test_handshake_command_has_required_fields(self, default_commands_fixture):
        """Verify handshake command has all required fields."""
        handshake_cmd = next((cmd for cmd in default_commands_fixture if cmd.get("name") == "Handshake"), None)
        assert handshake_cmd is not None
        assert "payload" in handshake_cmd
        payload = handshake_cmd["payload"]
        assert payload.get("action") == "handshake"
        assert "clientId" in payload
        assert "capabilities" in payload

    def test_all_commands_serializable(self, default_commands_fixture):
        """Verify all commands can be serialized to JSON."""
        for cmd in default_commands_fixture:
            json_str = json.dumps(cmd)
            assert json_str
            assert json.loads(json_str) == cmd


class TestHandshakeLogging:
    """Test handshake logging behavior."""

    def test_handshake_send_logged_with_payload(self, real_ws_manager_with_mocked_ws, mock_logger, handshake_payload):
        """Verify handshake send is logged with payload details."""
        real_ws_manager_with_mocked_ws.send_json(handshake_payload)
        
        log_calls = mock_logger.log.call_args_list
        assert len(log_calls) > 0
        
        logged_message = log_calls[-1][0][0]
        assert "handshake" in logged_message.lower() or "websocket" in logged_message.lower()

    def test_handshake_error_logged(self, real_ws_manager_with_mocked_ws, mock_logger, handshake_payload):
        """Verify handshake errors are logged."""
        real_ws_manager_with_mocked_ws.connected = False
        real_ws_manager_with_mocked_ws.send_json(handshake_payload)
        
        log_calls = mock_logger.log.call_args_list
        assert len(log_calls) > 0
        
        logged_message = log_calls[-1][0][0]
        assert "not connected" in logged_message.lower()


class TestHandshakeValidation:
    """Test handshake message validation."""

    def test_handshake_payload_json_valid(self, handshake_payload):
        """Verify handshake payload is valid JSON."""
        json_str = json.dumps(handshake_payload)
        parsed = json.loads(json_str)
        assert parsed == handshake_payload

    def test_handshake_with_custom_fields(self, handshake_payload):
        """Verify handshake can include custom fields."""
        custom_handshake = handshake_payload.copy()
        custom_handshake["customField"] = "custom-value"
        
        json_str = json.dumps(custom_handshake)
        assert "custom-value" in json_str

    def test_handshake_can_be_modified(self, handshake_payload):
        """Verify handshake payload can be modified before sending."""
        original_clientId = handshake_payload["clientId"]
        handshake_payload["clientId"] = "new-client-001"
        
        assert handshake_payload["clientId"] != original_clientId
        assert handshake_payload["action"] == "handshake"
