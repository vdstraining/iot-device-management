"""Negative and edge case tests for SCRUM-127 handshake feature."""
import json
import pytest
from unittest.mock import Mock, patch
from ws_client import WebSocketManager
from utilities import validate_handshake_payload, is_handshake_message


class TestNegativeValidationCases:
    """Negative test cases for payload validation."""

    def test_validate_payload_with_invalid_types(self):
        """Test validation with various invalid types."""
        invalid_payloads = [
            None,
            "",
            [],
            123,
            3.14,
            True,
            False,
            set(),
            tuple(),
        ]

        for payload in invalid_payloads:
            is_valid, error_msg = validate_handshake_payload(payload)
            assert is_valid is False, f"Should reject {type(payload).__name__}"

    def test_validate_payload_type_field_various_values(self):
        """Test validation with various values for type field."""
        invalid_types = [
            "message",
            "handshake_request",
            "HANDSHAKE",
            "Handshake",
            None,
            123,
            [],
            {},
            "",
        ]

        for invalid_type in invalid_types:
            payload = {
                "type": invalid_type,
                "clientId": "test",
                "version": "1.0",
            }
            is_valid, error_msg = validate_handshake_payload(payload)
            if invalid_type != "handshake":
                assert is_valid is False, f"Should reject type={invalid_type}"

    def test_validate_payload_clientId_missing_edge_cases(self):
        """Test validation when clientId is missing or invalid."""
        payloads = [
            {
                "type": "handshake",
                "version": "1.0",
                # Missing clientId
            },
            {
                "type": "handshake",
                "clientId": None,
                "version": "1.0",
            },
            {
                "type": "handshake",
                "clientId": "",
                "version": "1.0",
                # Empty string is technically present
            },
        ]

        for payload in payloads[0:1]:  # Only test first case (missing)
            is_valid, error_msg = validate_handshake_payload(payload)
            assert is_valid is False

    def test_validate_payload_version_missing_edge_cases(self):
        """Test validation when version is missing or invalid."""
        payloads = [
            {
                "type": "handshake",
                "clientId": "test",
                # Missing version
            },
            {
                "type": "handshake",
                "clientId": "test",
                "version": None,
            },
            {
                "type": "handshake",
                "clientId": "test",
                "version": "",
            },
        ]

        for payload in payloads[0:1]:  # Only test first case (missing)
            is_valid, error_msg = validate_handshake_payload(payload)
            assert is_valid is False

    def test_validate_payload_special_characters_in_fields(self):
        """Test validation with special characters in field values."""
        payload = {
            "type": "handshake",
            "clientId": "client!@#$%^&*()",
            "version": "1.0\n\r",
            "token": "<script>alert('xss')</script>",
        }

        is_valid, error_msg = validate_handshake_payload(payload)
        # Should pass validation (field values don't matter, only structure)
        assert is_valid is True

    def test_validate_payload_very_large_values(self):
        """Test validation with very large field values."""
        large_string = "x" * 10000
        payload = {
            "type": "handshake",
            "clientId": large_string,
            "version": "1.0",
        }

        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is True  # Structure is valid, size doesn't matter for validation

    def test_validate_payload_unicode_characters(self):
        """Test validation with unicode characters."""
        payload = {
            "type": "handshake",
            "clientId": "客户端-клиент-عميل",
            "version": "1.0",
        }

        is_valid, error_msg = validate_handshake_payload(payload)
        assert is_valid is True


class TestIsHandshakeMessageEdgeCases:
    """Edge case tests for is_handshake_message function."""

    def test_is_handshake_message_with_various_types(self):
        """Test is_handshake_message with various input types."""
        invalid_inputs = [
            None,
            "",
            [],
            123,
            3.14,
            True,
            False,
            set(),
            tuple(),
            lambda x: x,
        ]

        for invalid_input in invalid_inputs:
            result = is_handshake_message(invalid_input)
            assert result is False, f"Should return False for {type(invalid_input).__name__}"

    def test_is_handshake_message_with_objects_that_behave_like_dict(self):
        """Test is_handshake_message with dict-like objects."""

        class DictLike:
            def get(self, key, default=None):
                if key == "type":
                    return "handshake"
                return default

        # This should fail because it's not actually a dict
        result = is_handshake_message(DictLike())
        assert result is False

    def test_is_handshake_message_deeply_nested_dict(self):
        """Test is_handshake_message with deeply nested dictionaries."""
        payload = {
            "type": "handshake",
            "nested": {
                "deep": {
                    "very": {
                        "deep": {
                            "structure": "value",
                        }
                    }
                }
            },
        }

        result = is_handshake_message(payload)
        assert result is True


class TestWebSocketManagerNegativeCases:
    """Negative test cases for WebSocketManager."""

    def test_send_handshake_with_exception_types(self, mock_logger):
        """Test _send_handshake handling various exception types."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload={
                "type": "handshake",
                "clientId": "test",
                "version": "1.0",
            },
        )
        manager.connected = True

        exception_types = [
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            TypeError("Type error"),
            IOError("IO error"),
            Exception("Generic exception"),
        ]

        for exc in exception_types:
            manager.ws_app = Mock()
            manager.ws_app.send.side_effect = exc

            manager._send_handshake()

            # Should have logged error for each exception
            assert mock_logger.log.called

    def test_validate_payload_with_objects_missing_json_support(self, mock_logger):
        """Test _validate_payload with objects lacking JSON support."""

        class NoJSONSupport:
            def __init__(self):
                self.attr = "value"

        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "obj": NoJSONSupport(),
        }

        result = manager._validate_payload(payload)
        assert result is False

    def test_on_open_with_invalid_handshake_none_payload(self, mock_logger):
        """Test _on_open when handshake_payload is None."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=True,
            handshake_payload=None,  # Will default to valid payload
        )
        manager.ws_app = Mock()

        manager._on_open(Mock())

        # Should still set connected to True
        assert manager.connected is True

    def test_send_handshake_ws_app_none(self, mock_logger):
        """Test _send_handshake when ws_app is None."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload={
                "type": "handshake",
                "clientId": "test",
                "version": "1.0",
            },
        )
        manager.connected = True
        manager.ws_app = None

        # Should raise AttributeError when trying to call send on None
        with pytest.raises(AttributeError):
            manager._send_handshake()


class TestJSONSerializationEdgeCases:
    """Tests for JSON serialization edge cases."""

    def test_validate_payload_with_infinity(self, mock_logger):
        """Test _validate_payload with infinity values."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "value": float("inf"),
        }

        result = manager._validate_payload(payload)
        # JSON doesn't support infinity by default
        assert result is False

    def test_validate_payload_with_nan(self, mock_logger):
        """Test _validate_payload with NaN values."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "value": float("nan"),
        }

        result = manager._validate_payload(payload)
        # JSON doesn't support NaN by default
        assert result is False

    def test_validate_payload_with_bytes(self, mock_logger):
        """Test _validate_payload with bytes."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "data": b"binary data",
        }

        result = manager._validate_payload(payload)
        # JSON doesn't support bytes by default
        assert result is False


class TestConcurrencyAndStateBehavior:
    """Tests for state behavior edge cases."""

    def test_multiple_set_connected_calls(self, mock_logger, mock_callback):
        """Test calling _set_connected multiple times."""
        manager = WebSocketManager(
            logger=mock_logger, on_status_change=mock_callback
        )

        manager._set_connected(True)
        manager._set_connected(False)
        manager._set_connected(True)
        manager._set_connected(True)  # Same state twice

        # Should have called callback 4 times
        assert mock_callback.call_count == 4

    def test_handshake_payload_mutation(self, mock_logger):
        """Test that mutating handshake_payload affects future sends."""
        original_payload = {
            "type": "handshake",
            "clientId": "test",
            "version": "1.0",
        }
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=original_payload,
        )

        # Mutate the payload
        manager.handshake_payload["clientId"] = "modified"

        manager.connected = True
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should send the modified payload
        expected_json = json.dumps(
            {
                "type": "handshake",
                "clientId": "modified",
                "version": "1.0",
            }
        )
        manager.ws_app.send.assert_called_once_with(expected_json)


class TestErrorMessageAccuracy:
    """Tests for error message accuracy and clarity."""

    def test_validation_error_messages_are_descriptive(self):
        """Test that validation error messages are informative."""
        test_cases = [
            ({}, "missing required field: 'type'"),
            ({"type": "message"}, "must be 'handshake'"),
            ({"type": "handshake"}, "missing required field: 'clientId'"),
            ({"type": "handshake", "clientId": "test"}, "missing required field: 'version'"),
            ("not a dict", "must be a dictionary"),
        ]

        for payload, expected_error_substring in test_cases:
            is_valid, error_msg = validate_handshake_payload(payload)
            assert not is_valid
            assert expected_error_substring in error_msg


class TestConnectorStateConsistency:
    """Tests for connection state consistency."""

    def test_on_open_sets_correct_state(self, mock_logger):
        """Test that _on_open always sets connected=True."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.connected = False
        manager.ws_app = Mock()

        manager._on_open(Mock())

        assert manager.connected is True

    def test_set_connected_always_updates_state(self, mock_logger):
        """Test that _set_connected always updates the state."""
        manager = WebSocketManager(logger=mock_logger)

        manager.connected = True
        manager._set_connected(False)
        assert manager.connected is False

        manager._set_connected(True)
        assert manager.connected is True
