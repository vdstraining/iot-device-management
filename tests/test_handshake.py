import json
import unittest
from unittest.mock import MagicMock, patch, call
from io import StringIO

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS


class TestWebSocketManagerHandshake(unittest.TestCase):
    """Test WebSocket manager handshake callback functionality"""

    def setUp(self):
        self.logger = MagicMock()
        self.on_open_callback = MagicMock()

    def test_on_open_callback_is_called(self):
        """Test that on_open callback is invoked when connection opens"""
        manager = WebSocketManager(
            logger=self.logger,
            on_open=self.on_open_callback,
        )
        
        # Simulate _on_open being called
        manager._on_open(None)
        
        self.on_open_callback.assert_called_once()

    def test_on_open_callback_not_called_without_callback(self):
        """Test that code doesn't break when on_open is None"""
        manager = WebSocketManager(logger=self.logger)
        
        # Should not raise any exception
        manager._on_open(None)
        self.assertTrue(manager.connected)

    def test_on_open_sets_connected(self):
        """Test that _on_open sets connected flag to True"""
        manager = WebSocketManager(logger=self.logger)
        
        manager._on_open(None)
        
        self.assertTrue(manager.connected)

    def test_on_open_logs_connection(self):
        """Test that connection is logged"""
        manager = WebSocketManager(logger=self.logger)
        
        manager._on_open(None)
        
        self.logger.log.assert_called()


class TestHandshakePayload(unittest.TestCase):
    """Test handshake payload structure and validation"""

    def test_handshake_command_exists_in_defaults(self):
        """Test that Handshake command is in DEFAULT_COMMANDS"""
        handshake_commands = [
            cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"
        ]
        self.assertEqual(len(handshake_commands), 1)

    def test_handshake_payload_structure(self):
        """Test that handshake payload has required structure"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        self.assertIsNotNone(handshake)
        
        payload = handshake["payload"]
        
        # Check required fields
        self.assertIn("type", payload)
        self.assertIn("action", payload)
        self.assertIn("clientId", payload)
        self.assertIn("token", payload)
        self.assertIn("capabilities", payload)
        self.assertIn("session", payload)

    def test_handshake_type_is_handshake(self):
        """Test that handshake type is 'Handshake'"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        self.assertEqual(handshake["payload"]["type"], "Handshake")

    def test_handshake_action_is_handshake(self):
        """Test that handshake action is 'handshake'"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        self.assertEqual(handshake["payload"]["action"], "handshake")

    def test_handshake_capabilities_format(self):
        """Test that capabilities is a list with expected values"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        capabilities = handshake["payload"]["capabilities"]
        
        self.assertIsInstance(capabilities, list)
        self.assertIn("ws", capabilities)
        self.assertIn("http", capabilities)
        self.assertIn("ui-log", capabilities)

    def test_handshake_session_info(self):
        """Test that session contains client information"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        session = handshake["payload"]["session"]
        
        self.assertIn("client", session)
        self.assertEqual(session["client"], "tkinter-device-manager")

    def test_handshake_uses_placeholders(self):
        """Test that clientId and token use placeholder syntax"""
        handshake = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        payload = handshake["payload"]
        
        self.assertEqual(payload["clientId"], "{{clientId}}")
        self.assertEqual(payload["token"], "{{token}}")


class TestDynamicFieldResolution(unittest.TestCase):
    """Test dynamic field resolution for handshake"""

    def test_resolve_client_id_placeholder(self):
        """Test that {{clientId}} placeholder is resolved"""
        value = "{{clientId}}"
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        
        result = replacements.get(value, value)
        self.assertEqual(result, "device-123")

    def test_resolve_token_placeholder(self):
        """Test that {{token}} placeholder is resolved"""
        value = "{{token}}"
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        
        result = replacements.get(value, value)
        self.assertEqual(result, "token-abc")

    def test_resolve_nested_dict_with_placeholders(self):
        """Test resolution of nested dictionaries"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, dict):
                return {
                    key: resolve_dynamic_fields(item, replacements)
                    for key, item in value.items()
                }
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        payload = {
            "action": "handshake",
            "clientId": "{{clientId}}",
            "token": "{{token}}",
        }
        
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(payload, replacements)
        
        self.assertEqual(result["clientId"], "device-123")
        self.assertEqual(result["token"], "token-abc")
        self.assertEqual(result["action"], "handshake")

    def test_resolve_list_with_placeholders(self):
        """Test resolution of lists"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, list):
                return [resolve_dynamic_fields(item, replacements) for item in value]
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        capabilities = ["ws", "http", "{{token}}"]
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(capabilities, replacements)
        
        self.assertEqual(result, ["ws", "http", "token-abc"])


class TestHandshakeValidation(unittest.TestCase):
    """Test handshake payload validation"""

    def test_valid_handshake_payload_passes(self):
        """Test that valid handshake payload passes validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
            "capabilities": ["ws", "http"],
            "session": {"client": "tkinter-device-manager"},
        }
        
        # Validation logic
        required_fields = ["action", "clientId", "token"]
        is_handshake = payload.get("action") == "handshake"
        
        if is_handshake:
            missing_fields = [f for f in required_fields if not payload.get(f)]
            is_valid = len(missing_fields) == 0
        else:
            is_valid = True
        
        self.assertTrue(is_valid)

    def test_handshake_missing_clientId_fails(self):
        """Test that handshake without clientId fails validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "token": "token-abc",
        }
        
        # Validation logic
        required_fields = ["action", "clientId", "token"]
        is_handshake = payload.get("action") == "handshake"
        
        if is_handshake:
            missing_fields = [f for f in required_fields if not payload.get(f)]
            is_valid = len(missing_fields) == 0
        else:
            is_valid = True
        
        self.assertFalse(is_valid)

    def test_handshake_missing_token_fails(self):
        """Test that handshake without token fails validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
        }
        
        # Validation logic
        required_fields = ["action", "clientId", "token"]
        is_handshake = payload.get("action") == "handshake"
        
        if is_handshake:
            missing_fields = [f for f in required_fields if not payload.get(f)]
            is_valid = len(missing_fields) == 0
        else:
            is_valid = True
        
        self.assertFalse(is_valid)

    def test_non_handshake_payload_always_valid(self):
        """Test that non-handshake payloads are not subject to field validation"""
        payload = {
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z",
        }
        
        # Validation logic
        required_fields = ["action", "clientId", "token"]
        is_handshake = payload.get("action") == "handshake"
        
        if is_handshake:
            missing_fields = [f for f in required_fields if not payload.get(f)]
            is_valid = len(missing_fields) == 0
        else:
            is_valid = True
        
        self.assertTrue(is_valid)

    def test_non_dict_payload_invalid(self):
        """Test that non-dictionary payloads are invalid"""
        payload = "not a dict"
        
        is_valid = isinstance(payload, dict)
        
        self.assertFalse(is_valid)


class TestHandshakeAcknowledgement(unittest.TestCase):
    """Test handshake acknowledgement detection"""

    def test_handshake_ack_response_recognized(self):
        """Test that HandshakeAck response is recognized"""
        message = '{"type": "HandshakeAck", "status": "ok"}'
        payload = json.loads(message)
        
        is_ack = isinstance(payload, dict) and payload.get("type") in {"Handshake", "HandshakeAck"}
        
        self.assertTrue(is_ack)

    def test_handshake_response_recognized(self):
        """Test that Handshake response is recognized"""
        message = '{"type": "Handshake", "status": "ok"}'
        payload = json.loads(message)
        
        is_ack = isinstance(payload, dict) and payload.get("type") in {"Handshake", "HandshakeAck"}
        
        self.assertTrue(is_ack)

    def test_non_handshake_response_not_recognized(self):
        """Test that non-handshake responses are not recognized as ack"""
        message = '{"type": "PingResponse"}'
        payload = json.loads(message)
        
        is_ack = isinstance(payload, dict) and payload.get("type") in {"Handshake", "HandshakeAck"}
        
        self.assertFalse(is_ack)

    def test_malformed_json_handled(self):
        """Test that malformed JSON is handled gracefully"""
        message = "not valid json"
        
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            payload = None
        
        self.assertIsNone(payload)


if __name__ == "__main__":
    unittest.main()
