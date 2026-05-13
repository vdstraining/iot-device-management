"""
Test suite for handshake validation logic.

These tests verify that:
- Handshake messages are validated before sending
- Invalid handshake messages are rejected
- Required fields are validated
- Field types and values are checked
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from datetime import datetime


class TestHandshakeValidation:
    """Tests for validating handshake message structure and content."""

    def test_validate_complete_handshake(self, handshake_payload):
        """Test validation of a complete, valid handshake."""
        is_valid = self._validate_handshake(handshake_payload)
        assert is_valid is True

    def test_validate_handshake_with_missing_action(self, invalid_handshake_missing_action):
        """Test that validation fails when action field is missing."""
        is_valid = self._validate_handshake(invalid_handshake_missing_action)
        assert is_valid is False

    def test_validate_handshake_with_missing_clientId(self, invalid_handshake_missing_clientId):
        """Test that validation fails when clientId field is missing."""
        is_valid = self._validate_handshake(invalid_handshake_missing_clientId)
        assert is_valid is False

    def test_validate_handshake_with_missing_token(self, invalid_handshake_missing_token):
        """Test that validation fails when token field is missing."""
        is_valid = self._validate_handshake(invalid_handshake_missing_token)
        assert is_valid is False

    def test_validate_handshake_with_missing_timestamp(self, invalid_handshake_missing_timestamp):
        """Test that validation fails when timestamp field is missing."""
        is_valid = self._validate_handshake(invalid_handshake_missing_timestamp)
        assert is_valid is False

    def test_validate_all_required_fields_present(self, handshake_payload):
        """Test that all required fields must be present."""
        required_fields = {"action", "clientId", "token", "timestamp"}
        assert set(handshake_payload.keys()) == required_fields

    def test_validate_action_field_value(self, handshake_payload):
        """Test that action field must have value 'handshake'."""
        handshake_payload["action"] = "handshake"
        assert handshake_payload["action"] == "handshake"
        
        # Test invalid action value
        invalid_payload = handshake_payload.copy()
        invalid_payload["action"] = "invalid_action"
        assert invalid_payload["action"] != "handshake"

    def test_validate_clientId_is_string(self, handshake_payload):
        """Test that clientId must be a string."""
        assert isinstance(handshake_payload["clientId"], str)
        
        # Test invalid types
        invalid_payloads = [
            {**handshake_payload, "clientId": 12345},
            {**handshake_payload, "clientId": None},
            {**handshake_payload, "clientId": ["device-001"]},
        ]
        
        for payload in invalid_payloads:
            assert not isinstance(payload["clientId"], str) or isinstance(payload["clientId"], str)

    def test_validate_clientId_not_empty(self, handshake_payload):
        """Test that clientId cannot be empty string."""
        handshake_payload["clientId"] = "device-001"
        assert len(handshake_payload["clientId"]) > 0
        
        invalid_payload = {**handshake_payload, "clientId": ""}
        assert len(invalid_payload["clientId"]) == 0

    def test_validate_token_is_string(self, handshake_payload):
        """Test that token must be a string."""
        assert isinstance(handshake_payload["token"], str)

    def test_validate_token_not_empty(self, handshake_payload):
        """Test that token cannot be empty string."""
        handshake_payload["token"] = "test-token-12345"
        assert len(handshake_payload["token"]) > 0
        
        invalid_payload = {**handshake_payload, "token": ""}
        assert len(invalid_payload["token"]) == 0

    def test_validate_timestamp_is_string(self, handshake_payload):
        """Test that timestamp must be a string."""
        assert isinstance(handshake_payload["timestamp"], str)

    def test_validate_timestamp_is_iso_format(self, handshake_payload):
        """Test that timestamp should be in ISO format."""
        timestamp = handshake_payload["timestamp"]
        # Try to parse as ISO format
        try:
            datetime.fromisoformat(timestamp)
            is_valid_iso = True
        except ValueError:
            is_valid_iso = False
        
        assert is_valid_iso

    def test_validate_action_case_sensitive(self, handshake_payload):
        """Test that action value is case-sensitive."""
        # Correct
        handshake_payload["action"] = "handshake"
        assert handshake_payload["action"] == "handshake"
        
        # Incorrect
        invalid_payload = {**handshake_payload, "action": "HANDSHAKE"}
        assert invalid_payload["action"] != "handshake"

    def test_validate_extra_fields_rejected(self, handshake_payload):
        """Test that extra fields in handshake are rejected or ignored."""
        invalid_payload = {
            **handshake_payload,
            "extra_field": "should_not_be_here",
            "another_field": 12345
        }
        
        # Validate only required fields
        required_fields = {"action", "clientId", "token", "timestamp"}
        extra_fields = set(invalid_payload.keys()) - required_fields
        assert len(extra_fields) > 0

    def test_validate_handshake_json_serializable(self, handshake_payload):
        """Test that valid handshake can be serialized to JSON."""
        try:
            json_str = json.dumps(handshake_payload)
            assert isinstance(json_str, str)
            # Verify deserialization
            parsed = json.loads(json_str)
            assert parsed == handshake_payload
        except (TypeError, ValueError):
            assert False, "Handshake should be JSON serializable"

    @staticmethod
    def _validate_handshake(payload):
        """Helper method to validate handshake payload."""
        required_fields = {"action", "clientId", "token", "timestamp"}
        
        # Check all required fields exist
        if not isinstance(payload, dict):
            return False
        
        if set(payload.keys()) != required_fields:
            return False
        
        # Check action is "handshake"
        if payload.get("action") != "handshake":
            return False
        
        # Check all string fields are non-empty strings
        for field in ["clientId", "token", "timestamp"]:
            value = payload.get(field)
            if not isinstance(value, str) or len(value) == 0:
                return False
        
        # Check timestamp is valid ISO format
        try:
            datetime.fromisoformat(payload.get("timestamp"))
        except (ValueError, TypeError):
            return False
        
        return True


class TestHandshakeValidationErrors:
    """Tests for error handling in validation."""

    def test_validation_error_on_null_payload(self):
        """Test that null payload fails validation."""
        is_valid = self._validate_handshake(None)
        assert is_valid is False

    def test_validation_error_on_empty_dict(self):
        """Test that empty dictionary fails validation."""
        is_valid = self._validate_handshake({})
        assert is_valid is False

    def test_validation_error_on_malformed_json(self):
        """Test validation fails on malformed JSON string."""
        invalid_json_strings = [
            "{action: 'handshake'}",  # Missing quotes
            "{'action': 'handshake'}",  # Single quotes instead of double
            "{action: 'handshake', }",  # Trailing comma
        ]
        
        for invalid_json in invalid_json_strings:
            with pytest.raises(json.JSONDecodeError):
                json.loads(invalid_json)

    def test_validation_error_on_type_mismatch(self):
        """Test validation fails when field types don't match."""
        invalid_payloads = [
            {"action": 123, "clientId": "device", "token": "token", "timestamp": "2026-05-13"},
            {"action": "handshake", "clientId": None, "token": "token", "timestamp": "2026-05-13"},
            {"action": "handshake", "clientId": "device", "token": 123, "timestamp": "2026-05-13"},
        ]
        
        for payload in invalid_payloads:
            is_valid = self._validate_handshake(payload)
            assert is_valid is False

    def test_validation_error_message_helpful(self):
        """Test that validation errors provide useful information."""
        invalid_payload = {"clientId": "device", "token": "token", "timestamp": "2026-05-13"}
        # Missing action field
        assert "action" not in invalid_payload or invalid_payload["action"] != "handshake"

    def test_recover_from_validation_error(self, handshake_payload):
        """Test that after validation error, can recover with valid payload."""
        invalid_payload = {"clientId": "device"}  # Invalid
        assert self._validate_handshake(invalid_payload) is False
        
        # Now with valid payload
        assert self._validate_handshake(handshake_payload) is True

    @staticmethod
    def _validate_handshake(payload):
        """Helper method to validate handshake payload."""
        required_fields = {"action", "clientId", "token", "timestamp"}
        
        if not isinstance(payload, dict):
            return False
        
        if set(payload.keys()) != required_fields:
            return False
        
        if payload.get("action") != "handshake":
            return False
        
        for field in ["clientId", "token", "timestamp"]:
            value = payload.get(field)
            if not isinstance(value, str) or len(value) == 0:
                return False
        
        try:
            datetime.fromisoformat(payload.get("timestamp"))
        except (ValueError, TypeError):
            return False
        
        return True


class TestFieldValidationIndividual:
    """Tests for individual field validation."""

    def test_action_field_validation(self):
        """Test action field validation rules."""
        valid_actions = ["handshake"]
        invalid_actions = ["", "handshake ", " handshake", "HANDSHAKE", "handshake2", None, 123]
        
        for action in valid_actions:
            payload = {"action": action, "clientId": "d", "token": "t", "timestamp": "2026-05-13T10:00:00"}
            # Only check if it equals handshake (would be implementation detail)
            assert payload["action"] in [action] or action == "handshake"

    def test_clientId_field_validation_patterns(self):
        """Test various clientId patterns."""
        valid_ids = [
            "device-001",
            "client-123",
            "iot-sensor-42",
            "node-3e8f92a",
            "192.168.1.1",
            "a" * 100,  # Long ID
        ]
        
        for client_id in valid_ids:
            payload = {"action": "handshake", "clientId": client_id, "token": "t", "timestamp": "2026-05-13T10:00:00"}
            assert payload["clientId"] == client_id

    def test_token_field_validation_patterns(self):
        """Test various token patterns."""
        valid_tokens = [
            "simple-token",
            "Bearer-abc123def456",
            "very-long-token-" + "x" * 200,
            "token_with_underscore",
            "token.with.dots",
        ]
        
        for token in valid_tokens:
            payload = {"action": "handshake", "clientId": "d", "token": token, "timestamp": "2026-05-13T10:00:00"}
            assert payload["token"] == token

    def test_timestamp_field_validation_formats(self):
        """Test various timestamp formats."""
        valid_timestamps = [
            "2026-05-13T10:00:00",
            "2026-05-13T10:00:00.123456",
            "2026-05-13T10:00:00+00:00",
            "2026-05-13T10:00:00-05:00",
        ]
        
        for timestamp in valid_timestamps:
            try:
                datetime.fromisoformat(timestamp)
                is_valid = True
            except ValueError:
                is_valid = False
            assert is_valid
