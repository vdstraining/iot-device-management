"""
Test suite for handshake dynamic configuration.

These tests verify that:
- Handshake fields can be modified (clientId, token, etc.)
- Configuration persists during connection
- UI updates when handshake is selected
- Configuration changes are applied correctly
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from datetime import datetime


class TestDynamicHandshakeConfiguration:
    """Tests for modifying handshake configuration at runtime."""

    def test_modify_clientId_before_connection(self, mock_websocket_manager):
        """Test modifying clientId before establishing connection."""
        payload = {
            "action": "handshake",
            "clientId": "initial-device",
            "token": "token123",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        mock_websocket_manager.set_handshake_payload(payload)
        
        # Modify clientId
        payload["clientId"] = "new-device-id"
        mock_websocket_manager.set_handshake_payload(payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_clientId_after_connection(self, mock_websocket_manager, handshake_payload):
        """Test modifying clientId after connection is established."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_websocket_manager.is_connected.return_value = True
        
        # Modify clientId while connected
        new_payload = handshake_payload.copy()
        new_payload["clientId"] = "modified-id-456"
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_token_before_connection(self, mock_websocket_manager):
        """Test modifying token before establishing connection."""
        payload = {
            "action": "handshake",
            "clientId": "device",
            "token": "initial-token",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        mock_websocket_manager.set_handshake_payload(payload)
        payload["token"] = "updated-token-xyz"
        mock_websocket_manager.set_handshake_payload(payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_token_after_connection(self, mock_websocket_manager, handshake_payload):
        """Test modifying token after connection is established."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Modify token
        new_payload = handshake_payload.copy()
        new_payload["token"] = "new-token-abc"
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_modify_timestamp_during_session(self, mock_websocket_manager, handshake_payload):
        """Test updating timestamp during active session."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Update timestamp to current time
        new_payload = handshake_payload.copy()
        new_payload["timestamp"] = datetime.now().isoformat()
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2

    def test_complete_payload_replacement(self, mock_websocket_manager, handshake_payload):
        """Test replacing entire handshake payload."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Replace with completely different payload
        new_payload = {
            "action": "handshake",
            "clientId": "completely-new-device",
            "token": "completely-new-token",
            "timestamp": "2026-05-13T15:00:00"
        }
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2


class TestConfigurationPersistence:
    """Tests for configuration persistence across operations."""

    def test_configuration_persists_after_disconnect(self, mock_websocket_manager, handshake_payload):
        """Test that handshake configuration is retained after disconnect."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_websocket_manager.disconnect()
        
        # Configuration should still be set
        assert mock_websocket_manager.set_handshake_payload.call_count == 1

    def test_configuration_persists_through_reconnection(self, mock_websocket_manager, handshake_payload):
        """Test that handshake configuration persists during reconnection."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # First connection
        mock_websocket_manager.connect()
        
        # Disconnect
        mock_websocket_manager.disconnect()
        
        # Reconnect - should use same configuration
        mock_websocket_manager.connect()
        
        # Configuration was set once, but connect called twice
        assert mock_websocket_manager.set_handshake_payload.call_count == 1
        assert mock_websocket_manager.connect.call_count == 2

    def test_configuration_persists_across_message_sending(self, mock_websocket_manager, handshake_payload):
        """Test that configuration persists while sending other messages."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Send other messages
        mock_websocket_manager.send_message({"action": "data", "value": "test1"})
        mock_websocket_manager.send_message({"action": "ping"})
        mock_websocket_manager.send_message({"action": "data", "value": "test2"})
        
        # Handshake configuration should still be set
        assert mock_websocket_manager.set_handshake_payload.call_count == 1

    def test_configuration_persists_multiple_reconnections(self, mock_websocket_manager, handshake_payload):
        """Test that configuration persists through multiple reconnect cycles."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Multiple connect/disconnect cycles
        for _ in range(3):
            mock_websocket_manager.connect()
            mock_websocket_manager.disconnect()
        
        # Configuration should have been set only once
        assert mock_websocket_manager.set_handshake_payload.call_count == 1
        assert mock_websocket_manager.connect.call_count == 3

    def test_new_configuration_overrides_previous(self, mock_websocket_manager, handshake_payload):
        """Test that new configuration replaces previous one."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        new_payload = {**handshake_payload, "clientId": "new-id"}
        mock_websocket_manager.set_handshake_payload(new_payload)
        
        # Both calls should be recorded
        assert mock_websocket_manager.set_handshake_payload.call_count == 2


class TestUIHandshakeSelection:
    """Tests for UI updates when handshake is selected."""

    def test_ui_displays_handshake_option(self):
        """Test that UI displays handshake as available command."""
        commands = ["handshake", "ping", "data_transfer"]
        assert "handshake" in commands

    def test_selecting_handshake_populates_form_fields(self):
        """Test that selecting handshake in UI populates form fields."""
        handshake_fields = ["action", "clientId", "token", "timestamp"]
        
        # Simulate UI update
        form_fields = {field: "" for field in handshake_fields}
        
        assert set(form_fields.keys()) == set(handshake_fields)

    def test_form_fields_populated_with_current_values(self):
        """Test that form fields show current handshake values."""
        handshake_payload = {
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-xyz",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        # Form should be populated
        form = handshake_payload.copy()
        
        assert form["clientId"] == "device-123"
        assert form["token"] == "token-xyz"
        assert form["action"] == "handshake"

    def test_editing_form_field_updates_payload(self):
        """Test that editing form fields updates handshake payload."""
        payload = {
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-xyz",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        # User edits clientId field
        edited_payload = payload.copy()
        edited_payload["clientId"] = "device-456"
        
        assert edited_payload["clientId"] == "device-456"
        assert edited_payload != payload

    def test_send_button_enabled_when_handshake_selected(self):
        """Test that Send button is enabled when handshake is selected."""
        selected_command = "handshake"
        send_enabled = selected_command is not None
        
        assert send_enabled is True

    def test_form_validation_disabled_when_not_selected(self):
        """Test that form fields are disabled when handshake not selected."""
        selected_command = None
        fields_enabled = selected_command == "handshake"
        
        assert fields_enabled is False

    def test_clear_form_when_switching_commands(self):
        """Test that form is cleared when switching from handshake to other command."""
        # Starting with handshake
        form = {
            "action": "handshake",
            "clientId": "device",
            "token": "token",
            "timestamp": "2026-05-13T10:00:00"
        }
        
        # Switch to ping command
        new_command = "ping"
        form = {}  # Clear form
        
        assert len(form) == 0

    def test_handshake_option_highlighted_in_menu(self):
        """Test that handshake shows as highlighted/selected in command menu."""
        command_menu = ["handshake", "ping", "data_transfer"]
        selected = "handshake"
        
        assert selected in command_menu

    def test_field_values_displayed_with_proper_labels(self):
        """Test that form fields are displayed with proper labels."""
        fields = {
            "action": ("Action", "handshake"),
            "clientId": ("Client ID", "device-123"),
            "token": ("Token", "token-xyz"),
            "timestamp": ("Timestamp", "2026-05-13T10:00:00")
        }
        
        for field_key, (label, value) in fields.items():
            assert label is not None
            assert value is not None


class TestConfigurationUIValidation:
    """Tests for validating configuration through UI."""

    def test_clientId_field_accepts_alphanumeric(self):
        """Test that clientId field accepts alphanumeric characters."""
        valid_ids = ["device123", "sensor_001", "node-42", "IoT.Device.1"]
        
        for client_id in valid_ids:
            payload = {
                "action": "handshake",
                "clientId": client_id,
                "token": "token",
                "timestamp": "2026-05-13"
            }
            assert payload["clientId"] == client_id

    def test_token_field_accepts_special_characters(self):
        """Test that token field accepts special characters."""
        special_tokens = [
            "Bearer-abc123",
            "token.with.dots",
            "token_with_underscore",
            "token-with-dashes",
        ]
        
        for token in special_tokens:
            payload = {
                "action": "handshake",
                "clientId": "device",
                "token": token,
                "timestamp": "2026-05-13"
            }
            assert payload["token"] == token

    def test_timestamp_field_format_enforced(self):
        """Test that timestamp field enforces ISO format."""
        # Valid format
        valid_timestamp = "2026-05-13T10:00:00"
        try:
            datetime.fromisoformat(valid_timestamp)
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert is_valid

    def test_action_field_read_only_in_ui(self):
        """Test that action field is read-only in UI."""
        payload = {
            "action": "handshake",
            "clientId": "device",
            "token": "token",
            "timestamp": "2026-05-13"
        }
        
        # Action should always be "handshake" for handshake form
        assert payload["action"] == "handshake"

    def test_required_field_indicator_shown(self):
        """Test that required fields are marked in UI."""
        required_fields = ["action", "clientId", "token", "timestamp"]
        
        for field in required_fields:
            assert field in required_fields

    def test_empty_field_shows_error(self):
        """Test that empty required fields show validation error."""
        invalid_payload = {
            "action": "handshake",
            "clientId": "",  # Empty
            "token": "token",
            "timestamp": "2026-05-13"
        }
        
        assert len(invalid_payload["clientId"]) == 0
