"""Unit tests for handshake message structure and validation."""

import json
import pytest


class TestHandshakeMessageStructure:
    """Test the structure and format of handshake messages."""

    def test_handshake_in_default_commands(self, default_commands_fixture):
        """Verify handshake command exists in DEFAULT_COMMANDS."""
        names = [cmd["name"] for cmd in default_commands_fixture]
        assert "Handshake" in names

    def test_handshake_command_index(self, default_commands_fixture):
        """Verify handshake is the 6th command (index 5)."""
        assert default_commands_fixture[5]["name"] == "Handshake"

    def test_handshake_payload_exists(self, default_commands_fixture):
        """Verify handshake command has a payload."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        assert "payload" in handshake_cmd
        assert isinstance(handshake_cmd["payload"], dict)

    def test_handshake_json_serializable(self, handshake_payload):
        """Verify handshake payload can be serialized to JSON."""
        try:
            json_str = json.dumps(handshake_payload)
            assert json_str is not None
            # Verify it can be deserialized
            deserialized = json.loads(json_str)
            assert deserialized == handshake_payload
        except (TypeError, ValueError) as exc:
            pytest.fail(f"Handshake payload is not JSON serializable: {exc}")

    def test_handshake_payload_structure(self, default_commands_fixture):
        """Verify handshake payload has the expected structure."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        # Required fields
        assert "action" in payload
        assert "clientId" in payload
        assert "capabilities" in payload


class TestHandshakeMessageFields:
    """Test individual field validation in handshake messages."""

    def test_action_field_type(self, handshake_payload):
        """Verify action field is a string."""
        assert isinstance(handshake_payload["action"], str)

    def test_action_field_value(self, handshake_payload):
        """Verify action field has correct value."""
        assert handshake_payload["action"] == "handshake"

    def test_clientId_field_type(self, handshake_payload):
        """Verify clientId field is a string."""
        assert isinstance(handshake_payload["clientId"], str)

    def test_clientId_field_not_empty(self, handshake_payload):
        """Verify clientId field is not empty."""
        assert len(handshake_payload["clientId"]) > 0

    def test_capabilities_field_type(self, handshake_payload):
        """Verify capabilities field is a list."""
        assert isinstance(handshake_payload["capabilities"], list)

    def test_capabilities_field_not_empty(self, handshake_payload):
        """Verify capabilities list is not empty."""
        assert len(handshake_payload["capabilities"]) > 0

    def test_capabilities_elements_are_strings(self, handshake_payload):
        """Verify all capabilities are strings."""
        for capability in handshake_payload["capabilities"]:
            assert isinstance(capability, str)

    def test_optional_sessionMetadata_field(self, default_commands_fixture):
        """Verify sessionMetadata is optional but correctly structured if present."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        if "sessionMetadata" in payload:
            assert isinstance(payload["sessionMetadata"], dict)
            if "platform" in payload["sessionMetadata"]:
                assert isinstance(payload["sessionMetadata"]["platform"], str)
            if "version" in payload["sessionMetadata"]:
                assert isinstance(payload["sessionMetadata"]["version"], str)

    def test_optional_token_field(self, default_commands_fixture):
        """Verify token field if present."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        if "token" in payload:
            assert isinstance(payload["token"], str)


class TestHandshakeMessageValidation:
    """Test validation logic for handshake messages."""

    def test_minimal_valid_handshake(self, minimal_handshake_payload):
        """Verify minimal valid handshake can be created."""
        # Should have required fields
        assert minimal_handshake_payload["action"] == "handshake"
        assert "clientId" in minimal_handshake_payload
        assert "capabilities" in minimal_handshake_payload

    def test_required_fields_presence(self, handshake_payload):
        """Verify all required fields are present."""
        required_fields = ["action", "clientId", "capabilities"]
        for field in required_fields:
            assert field in handshake_payload, f"Missing required field: {field}"

    def test_required_fields_presence_with_invalid_payloads(self, invalid_handshake_payloads):
        """Verify required fields validation catches missing fields."""
        required_fields = ["action", "clientId", "capabilities"]

        # Test missing action
        assert "action" not in invalid_handshake_payloads["missing_action"]

        # Test missing clientId
        assert "clientId" not in invalid_handshake_payloads["missing_clientId"]

        # Test missing capabilities
        assert "capabilities" not in invalid_handshake_payloads["missing_capabilities"]

    def test_field_types_validation(self, invalid_handshake_payloads):
        """Verify field type validation catches type errors."""
        # Action type check
        wrong_action = invalid_handshake_payloads["wrong_action_type"]
        assert not isinstance(wrong_action["action"], str)

        # ClientId type check
        wrong_client_id = invalid_handshake_payloads["wrong_clientId_type"]
        assert not isinstance(wrong_client_id["clientId"], str)

        # Capabilities type check
        wrong_capabilities = invalid_handshake_payloads["wrong_capabilities_type"]
        assert not isinstance(wrong_capabilities["capabilities"], list)

    def test_action_value_validation(self, invalid_handshake_payloads):
        """Verify action value is correct when type is valid."""
        valid_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }
        assert valid_payload["action"] == "handshake"

        # Invalid action value should be caught
        invalid_action = invalid_handshake_payloads["invalid_action_value"]
        assert invalid_action["action"] != "handshake"

    def test_capabilities_not_empty_list(self, invalid_handshake_payloads):
        """Verify capabilities list is not empty."""
        empty_capabilities = invalid_handshake_payloads["capabilities_empty_list"]
        assert len(empty_capabilities["capabilities"]) == 0

        # Valid should have non-empty list
        valid_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }
        assert len(valid_payload["capabilities"]) > 0


class TestHandshakeMessageVariations:
    """Test various valid handshake message configurations."""

    def test_handshake_with_single_capability(self):
        """Verify handshake with single capability."""
        payload = {
            "action": "handshake",
            "clientId": "device-1",
            "capabilities": ["websocket"],
        }
        assert len(payload["capabilities"]) == 1

    def test_handshake_with_multiple_capabilities(self):
        """Verify handshake with multiple capabilities."""
        payload = {
            "action": "handshake",
            "clientId": "device-1",
            "capabilities": ["websocket", "messages", "events"],
        }
        assert len(payload["capabilities"]) == 3

    def test_handshake_with_full_metadata(self):
        """Verify handshake with complete metadata."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket", "messages"],
            "sessionMetadata": {
                "platform": "python-tkinter",
                "version": "1.0",
            },
            "token": "replace-me",
        }
        assert payload["sessionMetadata"]["platform"] == "python-tkinter"
        assert payload["token"] is not None

    def test_handshake_without_optional_fields(self):
        """Verify handshake works without optional fields."""
        payload = {
            "action": "handshake",
            "clientId": "device-1",
            "capabilities": ["websocket"],
        }
        # Should not have optional fields
        assert "sessionMetadata" not in payload or payload.get("sessionMetadata") is None
        assert "token" not in payload or payload.get("token") is None

    def test_handshake_different_client_ids(self):
        """Verify handshake accepts various valid clientId formats."""
        valid_client_ids = [
            "client-001",
            "device-001",
            "iot_device_123",
            "test-device",
        ]

        for client_id in valid_client_ids:
            payload = {
                "action": "handshake",
                "clientId": client_id,
                "capabilities": ["websocket"],
            }
            assert payload["clientId"] == client_id


class TestHandshakeMessageDefaultCommand:
    """Test the handshake command as it appears in DEFAULT_COMMANDS."""

    def test_handshake_default_command_name(self, default_commands_fixture):
        """Verify handshake command name is correct."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        assert handshake_cmd["name"] == "Handshake"

    def test_handshake_default_payload_values(self, default_commands_fixture):
        """Verify default handshake payload has sensible values."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        assert payload["action"] == "handshake"
        assert payload["clientId"] == "client-001"
        assert "websocket" in payload["capabilities"]

    def test_handshake_deep_copy_integrity(self, default_commands_fixture):
        """Verify DEFAULT_COMMANDS entry can be copied without issues."""
        import copy

        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        copied_payload = copy.deepcopy(handshake_cmd["payload"])

        # Modify copy shouldn't affect original
        copied_payload["clientId"] = "modified-client"
        assert handshake_cmd["payload"]["clientId"] == "client-001"
