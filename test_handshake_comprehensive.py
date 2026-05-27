#!/usr/bin/env python
"""
Comprehensive unit tests for handshake module (handshake.py).
Tests message generation, validation, response handling, and state management.
"""

import json
import unittest
from unittest.mock import Mock, MagicMock, call
from handshake import HandshakeHandler
from handshake_config import HandshakeConfig


class TestHandshakeConfigValidation(unittest.TestCase):
    """Test HandshakeConfig validation logic."""

    def test_valid_config_with_defaults(self):
        """Test that default config passes validation."""
        config = HandshakeConfig()
        is_valid, error = config.validate()
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_valid_config_with_custom_values(self):
        """Test that config with custom values passes validation."""
        config = HandshakeConfig(
            client_id="custom-id-123",
            token="auth-token-xyz",
            client_version="2.0.0",
            protocol_version="2.0"
        )
        is_valid, error = config.validate()
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_invalid_config_empty_client_id(self):
        """Test validation rejects empty clientId."""
        config = HandshakeConfig(client_id="")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)
        self.assertIn("non-empty", error)

    def test_invalid_config_none_client_id(self):
        """Test validation rejects None clientId (should use uuid instead)."""
        # Note: HandshakeConfig automatically generates uuid for None,
        # so we need to set it to None after creation
        config = HandshakeConfig()
        config.client_id = None
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)

    def test_invalid_config_whitespace_client_id(self):
        """Test validation rejects whitespace-only clientId."""
        config = HandshakeConfig(client_id="   ")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)

    def test_invalid_config_empty_client_version(self):
        """Test validation rejects empty clientVersion."""
        config = HandshakeConfig(client_version="")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientVersion", error)

    def test_invalid_config_whitespace_client_version(self):
        """Test validation rejects whitespace-only clientVersion."""
        config = HandshakeConfig(client_version="   ")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientVersion", error)

    def test_invalid_config_empty_protocol_version(self):
        """Test validation rejects empty protocolVersion."""
        config = HandshakeConfig(protocol_version="")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("protocolVersion", error)

    def test_invalid_config_whitespace_protocol_version(self):
        """Test validation rejects whitespace-only protocolVersion."""
        config = HandshakeConfig(protocol_version="   ")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("protocolVersion", error)

    def test_config_auto_generates_uuid(self):
        """Test that None clientId is auto-generated as UUID."""
        config = HandshakeConfig(client_id=None)
        self.assertIsNotNone(config.client_id)
        self.assertNotEqual(config.client_id, "")
        # UUID format check: should be string with hyphens
        self.assertIn("-", config.client_id)

    def test_config_empty_token_allowed(self):
        """Test that empty token is allowed."""
        config = HandshakeConfig(token="")
        is_valid, error = config.validate()
        self.assertTrue(is_valid)


class TestHandshakePayloadGeneration(unittest.TestCase):
    """Test handshake message payload generation."""

    def test_payload_has_all_required_fields(self):
        """Test that generated payload contains all required fields."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        required_fields = ["action", "clientId", "token", "clientVersion", "protocolVersion", "timestamp"]
        for field in required_fields:
            self.assertIn(field, payload, f"Missing field: {field}")

    def test_payload_action_is_handshake(self):
        """Test that payload action is 'handshake'."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        self.assertEqual(payload["action"], "handshake")

    def test_payload_clientId_matches_config(self):
        """Test that clientId in payload matches config."""
        client_id = "test-client-123"
        config = HandshakeConfig(client_id=client_id)
        payload = config.build_handshake_payload()
        self.assertEqual(payload["clientId"], client_id)

    def test_payload_token_matches_config(self):
        """Test that token in payload matches config."""
        token = "auth-token-xyz"
        config = HandshakeConfig(token=token)
        payload = config.build_handshake_payload()
        self.assertEqual(payload["token"], token)

    def test_payload_clientVersion_matches_config(self):
        """Test that clientVersion in payload matches config."""
        version = "3.2.1"
        config = HandshakeConfig(client_version=version)
        payload = config.build_handshake_payload()
        self.assertEqual(payload["clientVersion"], version)

    def test_payload_protocolVersion_matches_config(self):
        """Test that protocolVersion in payload matches config."""
        version = "2.5"
        config = HandshakeConfig(protocol_version=version)
        payload = config.build_handshake_payload()
        self.assertEqual(payload["protocolVersion"], version)

    def test_payload_timestamp_format(self):
        """Test that timestamp is in ISO format with Z suffix."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        self.assertIn("timestamp", payload)
        # Check ISO format and Z suffix
        self.assertTrue(payload["timestamp"].endswith("Z"))
        self.assertIn("T", payload["timestamp"])  # ISO format has T

    def test_payload_is_json_serializable(self):
        """Test that payload can be serialized to JSON."""
        config = HandshakeConfig()
        payload = config.build_handshake_payload()
        
        # Should not raise exception
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["action"], "handshake")

    def test_multiple_payloads_have_different_timestamps(self):
        """Test that consecutive payloads have different timestamps."""
        import time
        config = HandshakeConfig()
        
        payload1 = config.build_handshake_payload()
        time.sleep(0.01)  # Small delay to ensure different timestamps
        payload2 = config.build_handshake_payload()
        
        # Timestamps should be different (or at least not identical)
        self.assertNotEqual(payload1["timestamp"], payload2["timestamp"])


class TestHandshakeHandlerInitialization(unittest.TestCase):
    """Test HandshakeHandler initialization and state."""

    def test_handler_initializes_with_logger(self):
        """Test that handler initializes with logger."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        self.assertEqual(handler.logger, logger)

    def test_handler_creates_default_config(self):
        """Test that handler creates default config if none provided."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        self.assertIsNotNone(handler.config)
        self.assertIsInstance(handler.config, HandshakeConfig)

    def test_handler_accepts_custom_config(self):
        """Test that handler accepts custom config."""
        logger = Mock()
        custom_config = HandshakeConfig(client_id="custom-id")
        handler = HandshakeHandler(logger, config=custom_config)
        
        self.assertEqual(handler.config, custom_config)
        self.assertEqual(handler.config.client_id, "custom-id")

    def test_handler_initial_state(self):
        """Test that handler starts in correct state."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        self.assertFalse(handler.handshake_sent)
        self.assertFalse(handler.handshake_acknowledged)

    def test_handler_accepts_response_callback(self):
        """Test that handler accepts callback for response handling."""
        logger = Mock()
        callback = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=callback)
        
        self.assertEqual(handler.on_handshake_response, callback)

    def test_handler_initializes_without_callback(self):
        """Test that handler initializes correctly with None callback."""
        logger = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=None)
        
        self.assertIsNone(handler.on_handshake_response)


class TestHandshakeMessageBuilding(unittest.TestCase):
    """Test building and validating handshake messages."""

    def test_build_handshake_message_success(self):
        """Test successful handshake message building."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        message = handler.build_handshake_message()
        
        self.assertIsNotNone(message)
        self.assertEqual(message["action"], "handshake")
        logger.log.assert_not_called()  # No error logs on success

    def test_build_handshake_message_with_invalid_config_logs_error(self):
        """Test that invalid config logs error."""
        logger = Mock()
        config = HandshakeConfig(client_id="")  # Invalid
        handler = HandshakeHandler(logger, config=config)
        
        message = handler.build_handshake_message()
        
        self.assertIsNone(message)
        logger.log.assert_called()
        error_log = logger.log.call_args[0][0]
        self.assertIn("validation failed", error_log)

    def test_build_handshake_message_returns_none_for_invalid_config(self):
        """Test that invalid config returns None."""
        logger = Mock()
        config = HandshakeConfig(client_version="")
        handler = HandshakeHandler(logger, config=config)
        
        message = handler.build_handshake_message()
        self.assertIsNone(message)

    def test_build_handshake_message_contains_all_fields(self):
        """Test that built message contains all required fields."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        message = handler.build_handshake_message()
        
        required_fields = ["action", "clientId", "token", "clientVersion", "protocolVersion", "timestamp"]
        for field in required_fields:
            self.assertIn(field, message)


class TestHandshakeSending(unittest.TestCase):
    """Test sending handshake messages."""

    def test_send_handshake_success(self):
        """Test successful handshake sending."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        result = handler.send_handshake(send_callback)
        
        self.assertTrue(result)
        send_callback.assert_called_once()
        self.assertTrue(handler.handshake_sent)

    def test_send_handshake_calls_callback_with_valid_payload(self):
        """Test that send callback is called with valid payload."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        
        # Get the payload that was passed to callback
        call_args = send_callback.call_args[0][0]
        self.assertEqual(call_args["action"], "handshake")
        self.assertIn("clientId", call_args)

    def test_send_handshake_logs_message(self):
        """Test that sending logs the message."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        
        # Should have logged the send event
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("Handshake message sent", log_message)

    def test_send_handshake_prevents_double_send(self):
        """Test that handshake can't be sent twice on same connection."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        # First send should succeed
        result1 = handler.send_handshake(send_callback)
        self.assertTrue(result1)
        
        # Second send should fail
        result2 = handler.send_handshake(send_callback)
        self.assertFalse(result2)
        
        # Callback should only be called once
        self.assertEqual(send_callback.call_count, 1)

    def test_send_handshake_logs_double_send_attempt(self):
        """Test that double send attempt is logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.send_handshake(send_callback)
        logger.reset_mock()
        
        handler.send_handshake(send_callback)
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("already sent", log_message)

    def test_send_handshake_with_invalid_config_returns_false(self):
        """Test that invalid config prevents sending."""
        logger = Mock()
        config = HandshakeConfig(client_id="")
        handler = HandshakeHandler(logger, config=config)
        send_callback = Mock()
        
        result = handler.send_handshake(send_callback)
        
        self.assertFalse(result)
        send_callback.assert_not_called()

    def test_send_handshake_handles_callback_exception(self):
        """Test that callback exceptions are caught and logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        def failing_callback(payload):
            raise ValueError("Network error")
        
        result = handler.send_handshake(failing_callback)
        
        self.assertFalse(result)
        logger.log.assert_called()
        error_log = logger.log.call_args[0][0]
        self.assertIn("send error", error_log)


class TestHandshakeResponseHandling(unittest.TestCase):
    """Test handling server responses to handshake."""

    def test_handle_handshake_ack_response(self):
        """Test handling handshake_ack response."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "status": "success"}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)
        logger.log.assert_called()

    def test_handle_handshake_response_action(self):
        """Test handling handshake_response action."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_response", "clientId": "abc123"}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)

    def test_handle_response_calls_callback(self):
        """Test that callback is called on valid response."""
        logger = Mock()
        callback = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=callback)
        
        response = '{"action": "handshake_ack", "status": "success"}'
        handler.handle_handshake_response(response)
        
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        self.assertEqual(call_args["action"], "handshake_ack")

    def test_handle_response_ignores_non_handshake_action(self):
        """Test that non-handshake responses are ignored."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "ping_response", "data": "pong"}'
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)
        logger.log.assert_not_called()

    def test_handle_response_ignores_malformed_json(self):
        """Test that malformed JSON doesn't crash handler."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", invalid json'
        # Should not raise exception
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_response_logs_successful_ack(self):
        """Test that successful ack is logged."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "status": "ok"}'
        handler.handle_handshake_response(response)
        
        logger.log.assert_called()
        log_message = logger.log.call_args[0][0]
        self.assertIn("acknowledged", log_message)
        self.assertIn(response, log_message)


class TestHandshakeStateManagement(unittest.TestCase):
    """Test state management and reset."""

    def test_reset_for_new_connection(self):
        """Test that state is reset for new connection."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        # Simulate sent and acknowledged state
        handler.handshake_sent = True
        handler.handshake_acknowledged = True
        
        # Reset
        handler.reset_for_new_connection()
        
        self.assertFalse(handler.handshake_sent)
        self.assertFalse(handler.handshake_acknowledged)

    def test_reset_allows_resending_on_new_connection(self):
        """Test that handshake can be sent again after reset."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        # Send on first connection
        handler.send_handshake(send_callback)
        self.assertEqual(send_callback.call_count, 1)
        
        # Reset for new connection
        handler.reset_for_new_connection()
        
        # Send on second connection should succeed
        result = handler.send_handshake(send_callback)
        self.assertTrue(result)
        self.assertEqual(send_callback.call_count, 2)


class TestHandshakeConfigurationUpdate(unittest.TestCase):
    """Test updating handshake configuration at runtime."""

    def test_update_config_client_id(self):
        """Test updating clientId."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.update_config(client_id="new-client-id")
        
        self.assertEqual(handler.config.client_id, "new-client-id")

    def test_update_config_token(self):
        """Test updating token."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.update_config(token="new-token")
        
        self.assertEqual(handler.config.token, "new-token")

    def test_update_config_client_version(self):
        """Test updating clientVersion."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.update_config(client_version="2.5.0")
        
        self.assertEqual(handler.config.client_version, "2.5.0")

    def test_update_config_protocol_version(self):
        """Test updating protocolVersion."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.update_config(protocol_version="2.0")
        
        self.assertEqual(handler.config.protocol_version, "2.0")

    def test_update_config_multiple_fields(self):
        """Test updating multiple fields at once."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        handler.update_config(
            client_id="new-id",
            token="new-token",
            client_version="3.0.0"
        )
        
        self.assertEqual(handler.config.client_id, "new-id")
        self.assertEqual(handler.config.token, "new-token")
        self.assertEqual(handler.config.client_version, "3.0.0")

    def test_update_config_ignores_invalid_fields(self):
        """Test that invalid field names are ignored."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        original_id = handler.config.client_id
        
        # Update with non-existent field
        handler.update_config(invalid_field="should-be-ignored")
        
        # Client ID should be unchanged
        self.assertEqual(handler.config.client_id, original_id)

    def test_update_config_then_send(self):
        """Test that updated config is used in sending."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.update_config(client_id="updated-id", token="updated-token")
        handler.send_handshake(send_callback)
        
        # Check payload sent has updated values
        payload = send_callback.call_args[0][0]
        self.assertEqual(payload["clientId"], "updated-id")
        self.assertEqual(payload["token"], "updated-token")


if __name__ == "__main__":
    unittest.main()
