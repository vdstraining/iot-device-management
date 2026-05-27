#!/usr/bin/env python
"""
Edge case and error handling tests for SCRUM-139 handshake mechanism.
Tests boundary conditions, malformed inputs, and error scenarios.
"""

import json
import unittest
from unittest.mock import Mock, MagicMock
from handshake import HandshakeHandler
from handshake_config import HandshakeConfig
from ws_client import WebSocketManager


class TestNullAndEmptyHandling(unittest.TestCase):
    """Test handling of null, empty, and undefined values."""

    def test_none_client_id_auto_generates_uuid(self):
        """Test that None clientId is auto-generated."""
        config = HandshakeConfig(client_id=None)
        
        self.assertIsNotNone(config.client_id)
        self.assertNotEqual(config.client_id, "")
        self.assertNotEqual(config.client_id, "None")

    def test_empty_token_allowed(self):
        """Test that empty token is valid."""
        config = HandshakeConfig(token="")
        is_valid, _ = config.validate()
        self.assertTrue(is_valid)

    def test_empty_client_id_invalid(self):
        """Test that empty clientId is invalid."""
        config = HandshakeConfig(client_id="")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)

    def test_none_token_becomes_empty_string(self):
        """Test that None token becomes empty string."""
        config = HandshakeConfig(token=None)
        self.assertEqual(config.token, "")

    def test_whitespace_only_client_id_invalid(self):
        """Test that whitespace-only clientId is invalid."""
        config = HandshakeConfig(client_id="   \t\n  ")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)

    def test_whitespace_only_version_invalid(self):
        """Test that whitespace-only version is invalid."""
        config = HandshakeConfig(client_version="  ")
        is_valid, error = config.validate()
        self.assertFalse(is_valid)


class TestMalformedJsonHandling(unittest.TestCase):
    """Test handling of malformed JSON responses."""

    def test_handle_response_missing_action_field(self):
        """Test handling response without action field."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"status": "ok", "data": {}}'
        handler.handle_handshake_response(response)
        
        # Should not acknowledge (no action field)
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_response_null_action(self):
        """Test handling response with null action."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": null}'
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_response_wrong_action(self):
        """Test handling response with wrong action."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "ping_ack"}'
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_empty_json_object(self):
        """Test handling empty JSON object."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{}'
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_empty_string_response(self):
        """Test handling empty string response."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        # Should not crash
        handler.handle_handshake_response("")
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_response_with_extra_fields(self):
        """Test handling response with extra fields."""
        logger = Mock()
        callback = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=callback)
        
        response = '{"action": "handshake_ack", "extra": "field", "nested": {"data": 123}}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)
        # Callback should receive full response
        callback.assert_called_once()

    def test_handle_response_unicode_characters(self):
        """Test handling response with unicode characters."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "message": "成功 ✓"}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)

    def test_handle_truncated_json(self):
        """Test handling truncated JSON response."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "data": '
        # Should not crash
        handler.handle_handshake_response(response)
        
        self.assertFalse(handler.handshake_acknowledged)

    def test_handle_response_with_escaped_quotes(self):
        """Test handling response with escaped quotes."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "handshake_ack", "message": "Say \\"hello\\""}'
        handler.handle_handshake_response(response)
        
        self.assertTrue(handler.handshake_acknowledged)

    def test_handle_response_case_sensitivity(self):
        """Test that action matching is case-sensitive."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        response = '{"action": "HANDSHAKE_ACK"}'
        handler.handle_handshake_response(response)
        
        # Should not match (case-sensitive)
        self.assertFalse(handler.handshake_acknowledged)


class TestLargePayloadsAndLimits(unittest.TestCase):
    """Test handling of large payloads and boundary conditions."""

    def test_very_long_client_id(self):
        """Test handling of very long clientId."""
        long_id = "x" * 10000
        config = HandshakeConfig(client_id=long_id)
        is_valid, _ = config.validate()
        
        # Should be valid (no length limit specified)
        self.assertTrue(is_valid)

    def test_very_long_token(self):
        """Test handling of very long token."""
        long_token = "y" * 100000
        config = HandshakeConfig(token=long_token)
        
        payload = config.build_handshake_payload()
        self.assertEqual(payload["token"], long_token)

    def test_payload_with_special_characters(self):
        """Test payload building with special characters."""
        special_id = "client-!@#$%^&*()_+-=[]{}|;':\",./<>?"
        config = HandshakeConfig(client_id=special_id)
        
        payload = config.build_handshake_payload()
        json_str = json.dumps(payload)
        
        # Should be JSON serializable
        parsed = json.loads(json_str)
        self.assertEqual(parsed["clientId"], special_id)

    def test_payload_with_newlines_in_values(self):
        """Test payload with newline characters."""
        config = HandshakeConfig(token="token\nwith\nnewlines")
        
        payload = config.build_handshake_payload()
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        
        self.assertIn("\n", parsed["token"])


class TestConcurrencyAndRaceConditions(unittest.TestCase):
    """Test concurrent operations and race conditions."""

    def test_rapid_config_updates(self):
        """Test rapid configuration updates."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        # Rapid updates
        for i in range(100):
            handler.update_config(token=f"token-{i}")
        
        # Last update should be applied
        self.assertEqual(handler.config.token, "token-99")

    def test_send_immediately_after_reset(self):
        """Test sending immediately after reset."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        send_callback = Mock()
        
        handler.handshake_sent = True
        handler.reset_for_new_connection()
        
        # Should be able to send immediately
        result = handler.send_handshake(send_callback)
        self.assertTrue(result)

    def test_config_update_after_failed_send(self):
        """Test that config update works after failed send."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        # Invalid config
        handler.config.client_id = ""
        
        send_callback = Mock()
        result = handler.send_handshake(send_callback)
        self.assertFalse(result)
        
        # Fix config and try again (after reset)
        handler.reset_for_new_connection()
        handler.update_config(client_id="valid-id")
        
        result = handler.send_handshake(send_callback)
        self.assertTrue(result)


class TestWebSocketManagerEdgeCases(unittest.TestCase):
    """Test WebSocket manager edge cases."""

    def test_send_json_with_empty_payload(self):
        """Test sending empty JSON object."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        manager.send_json({})
        
        manager.ws_app.send.assert_called_once()

    def test_send_json_with_nested_payload(self):
        """Test sending deeply nested payload."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.connected = True
        
        payload = {
            "action": "test",
            "nested": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            }
        }
        
        manager.send_json(payload)
        manager.ws_app.send.assert_called_once()

    def test_on_message_with_empty_string(self):
        """Test message handler with empty string."""
        logger = Mock()
        callback = Mock()
        manager = WebSocketManager(logger, on_message=callback)
        
        manager._on_message(None, "")
        
        callback.assert_called_once_with("")

    def test_on_message_with_whitespace_only(self):
        """Test message handler with whitespace only."""
        logger = Mock()
        callback = Mock()
        manager = WebSocketManager(logger, on_message=callback)
        
        manager._on_message(None, "   \n\t  ")
        
        callback.assert_called_once()

    def test_update_handshake_config_with_empty_values(self):
        """Test updating config with empty string values."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        manager.update_handshake_config(token="", client_version="")
        
        self.assertEqual(manager.handshake_handler.config.token, "")
        self.assertEqual(manager.handshake_handler.config.client_version, "")

    def test_disconnect_without_connection(self):
        """Test disconnecting when not connected."""
        logger = Mock()
        manager = WebSocketManager(logger)
        
        # Should not crash
        manager.disconnect()
        
        logger.log.assert_called()

    def test_disconnect_with_exception_handling(self):
        """Test disconnect handles exceptions."""
        logger = Mock()
        manager = WebSocketManager(logger)
        manager.ws_app = Mock()
        manager.ws_app.close.side_effect = Exception("Close error")
        
        # Should not crash
        manager.disconnect()
        
        logger.log.assert_called()


class TestVersionAndCompatibility(unittest.TestCase):
    """Test version handling and compatibility."""

    def test_version_format_flexibility(self):
        """Test that various version formats are accepted."""
        versions = [
            "1.0",
            "1.0.0",
            "1.0.0-alpha",
            "1.0.0+build",
            "2021.12.25",
            "v1.0.0",
        ]
        
        for version in versions:
            config = HandshakeConfig(client_version=version)
            is_valid, _ = config.validate()
            # All should be valid (no strict format requirement)
            self.assertTrue(is_valid)

    def test_timestamp_format_consistency(self):
        """Test that timestamp is always in ISO format with Z."""
        config = HandshakeConfig()
        
        for _ in range(10):
            payload = config.build_handshake_payload()
            timestamp = payload["timestamp"]
            
            # ISO format check
            self.assertIn("T", timestamp)
            self.assertTrue(timestamp.endswith("Z"))


class TestResponseCallbackEdgeCases(unittest.TestCase):
    """Test response callback handling edge cases."""

    def test_callback_with_exception_propagates(self):
        """Test that callback exceptions propagate to caller.
        
        Note: Callback implementations should handle their own exceptions.
        The handler doesn't wrap callback invocation to allow caller to decide
        how to handle callback errors.
        """
        logger = Mock()
        
        def failing_callback(data):
            raise ValueError("Callback error")
        
        handler = HandshakeHandler(logger, on_handshake_response=failing_callback)
        
        response = '{"action": "handshake_ack"}'
        # Exception should propagate - caller is responsible for callback error handling
        with self.assertRaises(ValueError):
            handler.handle_handshake_response(response)

    def test_callback_receives_correct_data(self):
        """Test that callback receives correct data."""
        logger = Mock()
        received_data = {}
        
        def capture_callback(data):
            received_data.update(data)
        
        handler = HandshakeHandler(logger, on_handshake_response=capture_callback)
        
        response_obj = {"action": "handshake_ack", "session_id": "123", "expires": 3600}
        response = json.dumps(response_obj)
        handler.handle_handshake_response(response)
        
        self.assertEqual(received_data["session_id"], "123")
        self.assertEqual(received_data["expires"], 3600)

    def test_callback_called_only_once_per_response(self):
        """Test that callback is called exactly once per response."""
        logger = Mock()
        callback = Mock()
        handler = HandshakeHandler(logger, on_handshake_response=callback)
        
        response = '{"action": "handshake_ack"}'
        handler.handle_handshake_response(response)
        
        self.assertEqual(callback.call_count, 1)


class TestValidationErrorMessages(unittest.TestCase):
    """Test that validation error messages are helpful."""

    def test_error_message_for_empty_client_id(self):
        """Test error message is descriptive for empty clientId."""
        config = HandshakeConfig(client_id="")
        is_valid, error = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn("clientId", error)
        self.assertIn("non-empty", error)

    def test_error_message_for_empty_client_version(self):
        """Test error message is descriptive for empty clientVersion."""
        config = HandshakeConfig(client_version="")
        is_valid, error = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn("clientVersion", error)

    def test_error_message_for_empty_protocol_version(self):
        """Test error message is descriptive for empty protocolVersion."""
        config = HandshakeConfig(protocol_version="")
        is_valid, error = config.validate()
        
        self.assertFalse(is_valid)
        self.assertIn("protocolVersion", error)


class TestStateConsistency(unittest.TestCase):
    """Test that state remains consistent across operations."""

    def test_failed_send_doesnt_change_state(self):
        """Test that failed send doesn't change state."""
        logger = Mock()
        config = HandshakeConfig(client_id="")  # Invalid
        handler = HandshakeHandler(logger, config=config)
        
        initial_state = (handler.handshake_sent, handler.handshake_acknowledged)
        
        handler.send_handshake(Mock())
        
        final_state = (handler.handshake_sent, handler.handshake_acknowledged)
        self.assertEqual(initial_state, final_state)

    def test_non_handshake_response_doesnt_change_state(self):
        """Test that non-handshake responses don't change state."""
        logger = Mock()
        handler = HandshakeHandler(logger)
        
        initial_state = (handler.handshake_sent, handler.handshake_acknowledged)
        
        handler.handle_handshake_response('{"action": "other_response"}')
        
        final_state = (handler.handshake_sent, handler.handshake_acknowledged)
        self.assertEqual(initial_state, final_state)

    def test_config_immutability_after_payload_build(self):
        """Test that config doesn't change after building payload."""
        config = HandshakeConfig(
            client_id="id1",
            token="token1",
            client_version="1.0"
        )
        
        original_id = config.client_id
        original_token = config.token
        original_version = config.client_version
        
        # Build multiple payloads
        for _ in range(5):
            config.build_handshake_payload()
        
        # Config should be unchanged
        self.assertEqual(config.client_id, original_id)
        self.assertEqual(config.token, original_token)
        self.assertEqual(config.client_version, original_version)


if __name__ == "__main__":
    unittest.main()
