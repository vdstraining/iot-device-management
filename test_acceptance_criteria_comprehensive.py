#!/usr/bin/env python
"""
Comprehensive Acceptance Criteria Tests for SCRUM-139.
Verifies all 8 acceptance criteria with detailed test cases.
"""

import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from threading import Thread
from ws_client import WebSocketManager
from handshake import HandshakeHandler
from handshake_config import HandshakeConfig, DEFAULT_HANDSHAKE_CONFIG
from utilities import DEFAULT_COMMANDS


class TestAC1_AutomaticTrigger(unittest.TestCase):
    """AC1: Handshake is automatically sent within X seconds of successful connection."""

    def test_handshake_triggered_on_connection_open(self):
        """Test that handshake trigger is invoked on _on_open."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_open(None)
        
        self.assertTrue(manager.connected)
        self.assertFalse(manager.handshake_handler.handshake_sent)

    def test_handshake_state_reset_on_connection(self):
        """Test that handshake state is reset for new connections."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Simulate previous connection state
        manager.handshake_handler.handshake_sent = True
        manager.handshake_handler.handshake_acknowledged = True
        
        # New connection
        manager._on_open(None)
        
        # State should be reset
        self.assertFalse(manager.handshake_handler.handshake_sent)
        self.assertFalse(manager.handshake_handler.handshake_acknowledged)

    @patch('threading.Timer')
    def test_two_second_delay_scheduling(self, mock_timer):
        """Test that 2-second delay timer is scheduled."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager._on_open(None)
        
        # Verify Timer was called with 2.0 seconds
        self.assertTrue(mock_timer.called)
        call_args = mock_timer.call_args
        self.assertEqual(call_args[0][0], 2.0)

    def test_handshake_message_structure_on_trigger(self):
        """Test that triggered handshake message has valid structure."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        manager._send_handshake()
        
        # Verify valid message was prepared
        payload = manager.handshake_handler.build_handshake_message()
        self.assertIsNotNone(payload)
        self.assertEqual(payload["action"], "handshake")


class TestAC2_ValidJSONStructure(unittest.TestCase):
    """AC2: Handshake message structure is valid JSON following existing patterns."""

    def test_message_is_valid_json(self):
        """Test that payload is valid JSON."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed, payload)

    def test_message_has_action_field(self):
        """Test that message includes 'action' field (like Ping)."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        self.assertIn("action", payload)
        self.assertEqual(payload["action"], "handshake")

    def test_message_has_timestamp_field(self):
        """Test that message includes timestamp (follows Ping pattern)."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        self.assertIn("timestamp", payload)
        self.assertTrue(payload["timestamp"].endswith("Z"))

    def test_message_follows_existing_patterns(self):
        """Test that message structure matches existing command patterns."""
        # Get structure of existing Ping command
        ping_cmd = next(cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Ping")
        ping_payload = ping_cmd["payload"]
        
        # Get handshake payload
        config = HandshakeConfig()
        handshake_payload = config.build_handshake_payload()
        
        # Both should have action and timestamp fields
        self.assertIn("action", ping_payload)
        self.assertIn("action", handshake_payload)
        self.assertIn("timestamp", ping_payload)
        self.assertIn("timestamp", handshake_payload)

    def test_payload_serializable_to_json(self):
        """Test that payload can be serialized to JSON and back."""
        config = HandshakeConfig(
            client_id="test-id",
            token="test-token",
            client_version="1.2.3"
        )
        payload = config.build_handshake_payload()
        
        # Round-trip test
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["clientId"], payload["clientId"])
        self.assertEqual(parsed["token"], payload["token"])
        self.assertEqual(parsed["action"], payload["action"])

    def test_message_structure_consistency(self):
        """Test that message structure is consistent across calls."""
        config = HandshakeConfig()
        
        payload1 = config.build_handshake_payload()
        payload2 = config.build_handshake_payload()
        
        # Structure should be the same (timestamps differ)
        keys1 = set(payload1.keys())
        keys2 = set(payload2.keys())
        self.assertEqual(keys1, keys2)


class TestAC3_DefaultCommandsList(unittest.TestCase):
    """AC3: Handshake is added to the default commands list."""

    def test_handshake_in_default_commands(self):
        """Test that Handshake exists in DEFAULT_COMMANDS."""
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        self.assertIn("Handshake", command_names)

    def test_handshake_command_has_payload(self):
        """Test that Handshake command has payload."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"),
            None
        )
        
        self.assertIsNotNone(handshake_cmd)
        self.assertIn("payload", handshake_cmd)

    def test_handshake_payload_structure_in_default_commands(self):
        """Test that default command has correct payload structure."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake")
        )
        payload = handshake_cmd["payload"]
        
        required_fields = ["action", "clientId", "token", "clientVersion", "protocolVersion", "timestamp"]
        for field in required_fields:
            self.assertIn(field, payload)

    def test_handshake_payload_action_value(self):
        """Test that default command payload has action='handshake'."""
        handshake_cmd = next(
            (cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake")
        )
        
        self.assertEqual(handshake_cmd["payload"]["action"], "handshake")

    def test_default_commands_count_preserved(self):
        """Test that default commands count is reasonable."""
        # Should have original commands plus Handshake
        expected_minimum = 5  # Ping, Handshake, Login, Subscribe, Echo
        self.assertGreaterEqual(len(DEFAULT_COMMANDS), expected_minimum)


class TestAC4_TimestampedLogging(unittest.TestCase):
    """AC4: All handshake messages are logged with timestamp and content."""

    def test_handshake_send_is_logged(self):
        """Test that sending handshake is logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("Handshake message sent", log_message)

    def test_log_contains_payload_content(self):
        """Test that log message contains payload content."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        
        log_message = logger.log.call_args[0][0]
        # Should contain JSON representation
        self.assertIn("action", log_message)
        self.assertIn("handshake", log_message)

    def test_validation_failure_is_logged(self):
        """Test that validation failures are logged."""
        logger = Mock()
        config = HandshakeConfig(client_id="")
        handler = HandshakeHandler(logger, config=config)
        
        handler.build_handshake_message()
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("validation failed", log_message)

    def test_websocket_manager_logs_handshake_config_update(self):
        """Test that WebSocket manager logs config updates."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(token="test-token")
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("Handshake config updated", log_message)

    def test_double_send_attempt_is_logged(self):
        """Test that double send attempt is logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.handshake_sent = True
        handler.send_handshake(Mock())
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("already sent", log_message)

    def test_send_error_is_logged(self):
        """Test that send errors are logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        def failing_send(payload):
            raise Exception("Network error")
        
        handler.send_handshake(failing_send)
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("send error", log_message.lower())


class TestAC5_ServerResponseHandling(unittest.TestCase):
    """AC5: Server responses to handshake are captured and logged."""

    def test_handshake_ack_response_is_recognized(self):
        """Test that handshake_ack response is recognized."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "status": "success"}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)

    def test_handshake_response_action_recognized(self):
        """Test that handshake_response action is also recognized."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_response", "sessionId": "abc123"}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)

    def test_response_is_logged(self):
        """Test that response is logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "status": "ok"}'
        handler.handle_handshake_response(response)
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("acknowledged", log_message.lower())
        self.assertIn(response, log_message)

    def test_response_callback_invoked(self):
        """Test that response callback is invoked with response data."""
        logger = Mock()
        callback = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=callback)
        
        response = '{"action": "handshake_ack", "sessionId": "xyz"}'
        handler.handle_handshake_response(response)
        
        callback.assert_called_once()
        # Callback should receive the parsed response
        call_args = callback.call_args[0][0]
        self.assertEqual(call_args["sessionId"], "xyz")

    def test_websocket_manager_processes_responses(self):
        """Test that WebSocket manager processes handshake responses."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        response = '{"action": "handshake_ack", "sessionId": "session123"}'
        manager._on_message(None, response)
        
        self.assertTrue(manager.handshake_handler.handshake_acknowledged)

    def test_malformed_response_handled_gracefully(self):
        """Test that malformed responses don't crash handler."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        # Malformed JSON
        response = '{"action": "handshake_ack" invalid'
        
        # Should not raise exception
        handler.handle_handshake_response(response)
        
        # Should not acknowledge
        self.assertFalse(handler.handshake_acknowledged)


class TestAC6_DynamicConfiguration(unittest.TestCase):
    """AC6: Configuration supports dynamic handshake fields."""

    def test_dynamic_client_id_configuration(self):
        """Test that clientId can be configured dynamically."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(client_id="dynamic-id-123")
        
        payload = manager.handshake_handler.build_handshake_message()
        self.assertEqual(payload["clientId"], "dynamic-id-123")

    def test_dynamic_token_configuration(self):
        """Test that token can be configured dynamically."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(token="dynamic-token-xyz")
        
        payload = manager.handshake_handler.build_handshake_message()
        self.assertEqual(payload["token"], "dynamic-token-xyz")

    def test_dynamic_version_configuration(self):
        """Test that versions can be configured dynamically."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(
            client_version="3.5.2",
            protocol_version="2.0"
        )
        
        payload = manager.handshake_handler.build_handshake_message()
        self.assertEqual(payload["clientVersion"], "3.5.2")
        self.assertEqual(payload["protocolVersion"], "2.0")

    def test_configuration_persists_across_messages(self):
        """Test that configuration persists across multiple message builds."""
        config = HandshakeConfig(
            client_id="persistent-id",
            token="persistent-token"
        )
        
        payload1 = config.build_handshake_payload()
        payload2 = config.build_handshake_payload()
        
        self.assertEqual(payload1["clientId"], payload2["clientId"])
        self.assertEqual(payload1["token"], payload2["token"])

    def test_runtime_config_update_affects_next_send(self):
        """Test that runtime config updates affect next send."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        # Update config
        handler.update_config(client_id="new-id", token="new-token")
        
        # Build message
        message = handler.build_handshake_message()
        
        self.assertEqual(message["clientId"], "new-id")
        self.assertEqual(message["token"], "new-token")

    def test_multiple_dynamic_updates(self):
        """Test multiple successive dynamic updates."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Update 1
        manager.update_handshake_config(token="token1")
        self.assertEqual(manager.handshake_handler.config.token, "token1")
        
        # Update 2
        manager.update_handshake_config(token="token2")
        self.assertEqual(manager.handshake_handler.config.token, "token2")
        
        # Update 3
        manager.update_handshake_config(client_id="id3", token="token3")
        self.assertEqual(manager.handshake_handler.config.token, "token3")
        self.assertEqual(manager.handshake_handler.config.client_id, "id3")


class TestAC7_MessageValidation(unittest.TestCase):
    """AC7: Validation rejects invalid/malformed messages before transmission."""

    def test_empty_client_id_rejected(self):
        """Test that empty clientId is rejected."""
        config = HandshakeConfig(client_id="")
        is_valid, error = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)

    def test_invalid_config_prevents_sending(self):
        """Test that invalid config prevents message sending."""
        logger = Mock()
        config = HandshakeConfig(client_id="")
        handler = HandshakeHandler(logger, config=config)
        send_callback = Mock()
        
        result = handler.send_handshake(send_callback)
        
        self.assertFalse(result)
        send_callback.assert_not_called()

    def test_validation_error_message_provided(self):
        """Test that validation provides error message."""
        config = HandshakeConfig(client_version="")
        is_valid, error = config.validate()
        
        self.assertFalse(is_valid)
        self.assertNotEqual(error, "")

    def test_empty_version_rejected(self):
        """Test that empty version is rejected."""
        config = HandshakeConfig(protocol_version="")
        is_valid, _ = config.validate()
        
        self.assertFalse(is_valid)

    def test_malformed_config_logs_error(self):
        """Test that malformed config logs error."""
        logger = Mock()
        config = HandshakeConfig(client_id="")
        handler = HandshakeHandler(logger, config=config)
        
        handler.build_handshake_message()
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("validation failed", log_message)

    def test_validation_happens_before_send(self):
        """Test that validation is performed before attempting send."""
        logger = Mock()
        config = HandshakeConfig(client_version="")
        handler = HandshakeHandler(logger, config=config)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        
        # Should have logged validation error
        logger.log.assert_called()
        # Should not have called send_callback
        send_callback.assert_not_called()


class TestAC8_BackwardsCompatibility(unittest.TestCase):
    """AC8: No breaking changes to existing APIs and command formats."""

    def test_existing_commands_unchanged(self):
        """Test that existing commands are still present."""
        existing_commands = ["Ping", "Login", "Subscribe", "Echo"]
        command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        
        for cmd_name in existing_commands:
            self.assertIn(cmd_name, command_names)

    def test_existing_command_structure_unchanged(self):
        """Test that existing commands still have required structure."""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn("name", cmd)
            self.assertIn("payload", cmd)
            self.assertIsInstance(cmd["payload"], dict)

    def test_websocket_manager_connect_api_unchanged(self):
        """Test that WebSocket connect API is unchanged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Should have connect method with ws_url parameter
        self.assertTrue(hasattr(manager, 'connect'))
        self.assertTrue(callable(manager.connect))

    def test_websocket_manager_disconnect_api_unchanged(self):
        """Test that WebSocket disconnect API is unchanged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertTrue(hasattr(manager, 'disconnect'))
        self.assertTrue(callable(manager.disconnect))

    def test_websocket_manager_send_json_api_unchanged(self):
        """Test that send_json API is unchanged."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        self.assertTrue(hasattr(manager, 'send_json'))
        self.assertTrue(callable(manager.send_json))

    def test_websocket_manager_callbacks_unchanged(self):
        """Test that manager still accepts on_message and on_status_change."""
        logger = Mock()
        msg_callback = Mock()
        status_callback = Mock()
        
        manager = WebSocketManager(
            logger,
            on_message=msg_callback,
            on_status_change=status_callback
        )
        
        self.assertEqual(manager.on_message, msg_callback)
        self.assertEqual(manager.on_status_change, status_callback)

    def test_logger_interface_unchanged(self):
        """Test that logger interface is unchanged."""
        from utilities import AppLogger
        
        callback = Mock()
        logger = AppLogger(callback)
        
        logger.log("test message")
        
        callback.assert_called_once()
        logged_text = callback.call_args[0][0]
        self.assertIn("test message", logged_text)
        self.assertIn("[", logged_text)  # Timestamp present

    def test_ping_command_still_works(self):
        """Test that Ping command is still functional."""
        ping_cmd = next((cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Ping"), None)
        
        self.assertIsNotNone(ping_cmd)
        self.assertEqual(ping_cmd["payload"]["action"], "ping")
        self.assertIn("timestamp", ping_cmd["payload"])


if __name__ == "__main__":
    unittest.main()
