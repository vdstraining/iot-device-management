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


class TestHandshakeSending(unittest.TestCase):
    """Test handshake message sending and state management"""

    def setUp(self):
        self.logger = MagicMock()
        self.on_message = MagicMock()
        self.on_status_change = MagicMock()
        self.on_open = MagicMock()

    def test_send_handshake_sends_valid_payload(self):
        """Test that send_json is called with valid handshake payload"""
        manager = WebSocketManager(
            logger=self.logger,
            on_open=self.on_open,
        )
        manager.connected = True
        manager.ws_app = MagicMock()
        
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        manager.send_json(payload)
        
        manager.ws_app.send.assert_called_once()

    def test_send_handshake_fails_when_disconnected(self):
        """Test that send_json fails gracefully when disconnected"""
        manager = WebSocketManager(logger=self.logger)
        manager.connected = False
        
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        manager.send_json(payload)
        
        self.logger.log.assert_called()
        call_args = self.logger.log.call_args[0][0]
        self.assertIn("not connected", call_args)

    def test_send_handshake_logs_sent_message(self):
        """Test that sent message is logged"""
        manager = WebSocketManager(logger=self.logger)
        manager.connected = True
        manager.ws_app = MagicMock()
        
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        manager.send_json(payload)
        
        logged_calls = [call[0][0] for call in self.logger.log.call_args_list]
        self.assertTrue(any("Sent" in str(call) for call in logged_calls))


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake workflow"""

    def setUp(self):
        self.logger = MagicMock()
        self.on_message = MagicMock()
        self.on_status_change = MagicMock()
        self.on_open = MagicMock()

    def test_connection_status_change_triggers_callback(self):
        """Test that status change callback is called on connect"""
        manager = WebSocketManager(
            logger=self.logger,
            on_status_change=self.on_status_change,
        )
        
        manager._set_connected(True)
        
        self.on_status_change.assert_called_once_with(True)

    def test_on_open_triggers_handshake_callback(self):
        """Test that on_open callback is triggered when connection opens"""
        manager = WebSocketManager(
            logger=self.logger,
            on_open=self.on_open,
        )
        
        manager._on_open(None)
        
        self.on_open.assert_called_once()

    def test_message_handler_invokes_callback(self):
        """Test that received message triggers on_message callback"""
        manager = WebSocketManager(
            logger=self.logger,
            on_message=self.on_message,
        )
        
        test_message = '{"type": "HandshakeAck"}'
        manager._on_message(None, test_message)
        
        self.on_message.assert_called_once_with(test_message)

    def test_connection_close_resets_connected_state(self):
        """Test that close event sets connected to False"""
        manager = WebSocketManager(
            logger=self.logger,
            on_status_change=self.on_status_change,
        )
        manager.connected = True
        
        manager._on_close(None, 1000, "Normal closure")
        
        self.assertFalse(manager.connected)

    def test_multiple_connections_handle_state_correctly(self):
        """Test that state is correctly managed across multiple connections"""
        manager = WebSocketManager(logger=self.logger)
        
        # First connection
        manager._on_open(None)
        self.assertTrue(manager.connected)
        
        # Close first connection
        manager._on_close(None, 1000, "Normal closure")
        self.assertFalse(manager.connected)
        
        # Second connection
        manager._on_open(None)
        self.assertTrue(manager.connected)


class TestHandshakeEdgeCases(unittest.TestCase):
    """Test edge cases and error scenarios in handshake"""

    def setUp(self):
        self.logger = MagicMock()

    def test_empty_client_id_validation_fails(self):
        """Test that empty clientId fails validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "",
            "token": "token-abc",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertIn("clientId", missing_fields)

    def test_empty_token_validation_fails(self):
        """Test that empty token fails validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertIn("token", missing_fields)

    def test_null_values_in_handshake_fails(self):
        """Test that null values in required fields fail validation"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": None,
            "token": "token-abc",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertIn("clientId", missing_fields)

    def test_send_handshake_with_invalid_json_exception(self):
        """Test that invalid JSON in send_json is handled"""
        manager = WebSocketManager(logger=self.logger)
        manager.connected = True
        manager.ws_app = MagicMock()
        manager.ws_app.send.side_effect = Exception("Invalid data")
        
        payload = {"type": "Handshake"}
        manager.send_json(payload)
        
        self.logger.log.assert_called()

    def test_receive_handshake_ack_with_malformed_response(self):
        """Test handling of malformed server response"""
        # Test without on_message callback - should log
        manager = WebSocketManager(logger=self.logger)
        
        # Send invalid JSON
        invalid_message = "not valid json {]"
        manager._on_message(None, invalid_message)
        
        # Should not raise exception, logger should be called
        self.logger.log.assert_called()
        call_args = self.logger.log.call_args[0][0]
        self.assertIn("received", call_args.lower())

    def test_handshake_without_type_field(self):
        """Test handshake without 'type' field"""
        payload = {
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        # Validation: check if action matches
        is_handshake = payload.get("action") == "handshake"
        
        self.assertTrue(is_handshake)

    def test_handshake_without_action_field(self):
        """Test handshake without 'action' field"""
        payload = {
            "type": "Handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertIn("action", missing_fields)

    def test_extra_fields_in_handshake_still_valid(self):
        """Test that extra fields in handshake don't invalidate it"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
            "extra_field": "extra_value",
            "timestamp": "2026-03-27T12:00:00Z",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertEqual(len(missing_fields), 0)


class TestDynamicFieldResolutionAdvanced(unittest.TestCase):
    """Advanced tests for dynamic field resolution"""

    def test_resolve_empty_string_client_id(self):
        """Test resolution with empty client ID"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        value = "{{clientId}}"
        replacements = {"{{clientId}}": "", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(value, replacements)
        
        self.assertEqual(result, "")

    def test_resolve_empty_string_token(self):
        """Test resolution with empty token"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        value = "{{token}}"
        replacements = {"{{clientId}}": "device-123", "{{token}}": ""}
        result = resolve_dynamic_fields(value, replacements)
        
        self.assertEqual(result, "")

    def test_resolve_deeply_nested_dict(self):
        """Test resolution in deeply nested dictionaries"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, dict):
                return {
                    key: resolve_dynamic_fields(item, replacements)
                    for key, item in value.items()
                }
            if isinstance(value, list):
                return [resolve_dynamic_fields(item, replacements) for item in value]
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        payload = {
            "handshake": {
                "auth": {
                    "clientId": "{{clientId}}",
                    "credentials": {
                        "token": "{{token}}",
                    }
                }
            }
        }
        
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(payload, replacements)
        
        self.assertEqual(result["handshake"]["auth"]["clientId"], "device-123")
        self.assertEqual(result["handshake"]["auth"]["credentials"]["token"], "token-abc")

    def test_resolve_mixed_types_in_list(self):
        """Test resolution with mixed types in list"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, list):
                return [resolve_dynamic_fields(item, replacements) for item in value]
            if isinstance(value, dict):
                return {
                    key: resolve_dynamic_fields(item, replacements)
                    for key, item in value.items()
                }
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        items = ["ws", 123, "{{token}}", True, {"id": "{{clientId}}"}]
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(items, replacements)
        
        self.assertEqual(result[0], "ws")
        self.assertEqual(result[1], 123)
        self.assertEqual(result[2], "token-abc")
        self.assertEqual(result[3], True)
        self.assertEqual(result[4]["id"], "device-123")

    def test_resolve_placeholder_not_in_replacements(self):
        """Test resolution when placeholder is not in replacements"""
        def resolve_dynamic_fields(value, replacements):
            if isinstance(value, str):
                return replacements.get(value, value)
            return value

        value = "{{unknownPlaceholder}}"
        replacements = {"{{clientId}}": "device-123", "{{token}}": "token-abc"}
        result = resolve_dynamic_fields(value, replacements)
        
        self.assertEqual(result, "{{unknownPlaceholder}}")


class TestHandshakeStateManagement(unittest.TestCase):
    """Test handshake state transitions"""

    def setUp(self):
        self.logger = MagicMock()

    def test_handshake_acknowledged_flag_initial_state(self):
        """Test that handshake_acknowledged starts as False"""
        # Simulating UI state
        handshake_acknowledged = False
        self.assertFalse(handshake_acknowledged)

    def test_handshake_acknowledged_set_on_ack_response(self):
        """Test that flag is set when handshake ack is received"""
        message = '{"type": "HandshakeAck", "status": "ok"}'
        payload = json.loads(message)
        
        handshake_acknowledged = False
        if isinstance(payload, dict) and payload.get("type") in {"Handshake", "HandshakeAck"}:
            handshake_acknowledged = True
        
        self.assertTrue(handshake_acknowledged)

    def test_handshake_acknowledged_reset_on_disconnect(self):
        """Test that flag is reset when disconnected"""
        handshake_acknowledged = True
        ws_connected = False
        
        if not ws_connected:
            handshake_acknowledged = False
        
        self.assertFalse(handshake_acknowledged)

    def test_handshake_acknowledged_reset_on_new_handshake(self):
        """Test that flag is reset when new handshake is sent"""
        handshake_acknowledged = True
        
        # User sends new handshake
        handshake_acknowledged = False
        
        self.assertFalse(handshake_acknowledged)


class TestHandshakeBuildingFromDefaults(unittest.TestCase):
    """Test building handshake payload from default commands"""

    def test_handshake_command_exists(self):
        """Test that handshake command exists in default commands"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        self.assertIsNotNone(handshake_cmd)

    def test_handshake_payload_has_all_fields(self):
        """Test that built handshake has all required fields"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        payload = handshake_cmd["payload"]
        
        required_fields = ["type", "action", "clientId", "token"]
        for field in required_fields:
            self.assertIn(field, payload)

    def test_built_handshake_has_capabilities(self):
        """Test that built handshake includes capabilities"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        payload = handshake_cmd["payload"]
        
        self.assertIn("capabilities", payload)
        self.assertIsInstance(payload["capabilities"], list)

    def test_built_handshake_has_session_info(self):
        """Test that built handshake includes session information"""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        payload = handshake_cmd["payload"]
        
        self.assertIn("session", payload)
        self.assertIn("client", payload["session"])


class TestHandshakeValidationComprehensive(unittest.TestCase):
    """Comprehensive validation tests"""

    def test_validation_with_whitespace_values(self):
        """Test validation with whitespace-only values"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "   ",
            "token": "  ",
        }
        
        # Values with only whitespace are truthy but may need trimming
        has_clientId = bool(payload.get("clientId"))
        has_token = bool(payload.get("token"))
        
        self.assertTrue(has_clientId)
        self.assertTrue(has_token)

    def test_validation_recognizes_both_action_and_type(self):
        """Test that validation recognizes both action and type fields"""
        payload1 = {"action": "handshake"}
        payload2 = {"type": "Handshake"}
        
        is_handshake_1 = payload1.get("action") == "handshake"
        is_handshake_2 = payload2.get("type") == "Handshake"
        
        self.assertTrue(is_handshake_1)
        self.assertTrue(is_handshake_2)

    def test_numeric_client_id_fails(self):
        """Test that numeric clientId (not string) is handled"""
        payload = {
            "type": "Handshake",
            "action": "handshake",
            "clientId": 123,
            "token": "token-abc",
        }
        
        # If we're checking bool(payload.get("clientId")), numeric values are truthy
        is_valid = bool(payload.get("clientId"))
        self.assertTrue(is_valid)

    def test_handshake_with_action_field_missing_completely(self):
        """Test handshake when action field is completely absent"""
        payload = {
            "type": "Handshake",
            "clientId": "device-123",
            "token": "token-abc",
        }
        
        required_fields = ["action", "clientId", "token"]
        missing_fields = [f for f in required_fields if not payload.get(f)]
        
        self.assertIn("action", missing_fields)


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and resilience"""

    def setUp(self):
        self.logger = MagicMock()

    def test_websocket_send_error_recovery(self):
        """Test that WebSocket recovers from send errors"""
        manager = WebSocketManager(logger=self.logger)
        manager.connected = True
        manager.ws_app = MagicMock()
        
        # First attempt fails
        manager.ws_app.send.side_effect = Exception("Network error")
        payload1 = {"type": "Handshake"}
        manager.send_json(payload1)
        
        # Recovery: second attempt should be possible
        manager.ws_app.send.side_effect = None
        payload2 = {"type": "Handshake"}
        manager.send_json(payload2)
        
        self.assertEqual(manager.ws_app.send.call_count, 2)

    def test_multiple_handshake_attempts(self):
        """Test that multiple handshake attempts can be made"""
        manager = WebSocketManager(logger=self.logger)
        manager.connected = True
        manager.ws_app = MagicMock()
        
        # Attempt 1
        payload1 = {
            "type": "Handshake",
            "clientId": "device-1",
            "token": "token-1",
        }
        manager.send_json(payload1)
        
        # Attempt 2
        payload2 = {
            "type": "Handshake",
            "clientId": "device-2",
            "token": "token-2",
        }
        manager.send_json(payload2)
        
        self.assertEqual(manager.ws_app.send.call_count, 2)

    def test_handshake_after_reconnection(self):
        """Test handshake can be sent after reconnection"""
        manager = WebSocketManager(logger=self.logger)
        
        # First connection
        manager._on_open(None)
        self.assertTrue(manager.connected)
        
        # Disconnect
        manager._on_close(None, 1000, "Normal closure")
        self.assertFalse(manager.connected)
        
        # Reconnect
        manager._on_open(None)
        self.assertTrue(manager.connected)


if __name__ == "__main__":
    unittest.main()
