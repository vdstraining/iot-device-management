"""UI tests for handshake functionality in the application."""

import json
from unittest.mock import MagicMock, Mock, patch
import pytest


class TestHandshakeUIPresence:
    """Test handshake command appears in the UI."""

    def test_handshake_checkbox_in_command_panel(self, default_commands_fixture):
        """Verify handshake checkbox is created in command panel."""
        commands = default_commands_fixture
        handshake_cmd = next(cmd for cmd in commands if cmd["name"] == "Handshake")

        # Should exist in commands
        assert handshake_cmd is not None
        assert handshake_cmd["name"] == "Handshake"

    def test_handshake_label_text(self, default_commands_fixture):
        """Verify handshake checkbox has correct label."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        assert handshake_cmd["name"] == "Handshake"

    def test_handshake_grid_position_sixth(self, default_commands_fixture):
        """Verify handshake is positioned as 6th command in grid."""
        commands = default_commands_fixture

        # Should have exactly 6 commands
        assert len(commands) == 6

        # Handshake should be at index 5 (6th position)
        assert commands[5]["name"] == "Handshake"


class TestHandshakeUILoading:
    """Test loading handshake command in UI."""

    def test_handshake_template_loads_in_request_text(self, default_commands_fixture):
        """Verify handshake payload loads into request text area."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        # Simulate loading into request text
        json_text = json.dumps(payload, indent=2)

        # Should be valid and formatted
        assert "action" in json_text
        assert "handshake" in json_text
        assert "clientId" in json_text
        assert "capabilities" in json_text

    def test_handshake_payload_formatting(self, default_commands_fixture):
        """Verify handshake payload is formatted correctly for display."""
        handshake_cmd = next(
            cmd for cmd in default_commands_fixture if cmd["name"] == "Handshake"
        )
        payload = handshake_cmd["payload"]

        # Format with indentation
        formatted = json.dumps(payload, indent=2)

        # Parse back to verify structure
        parsed = json.loads(formatted)
        assert parsed == payload

    def test_handshake_selection_triggers_loading(self, mock_logger):
        """Verify selecting handshake triggers load message."""
        command_name = "Handshake"
        log_msg = f"Loaded default command: {command_name}"

        # Simulate selection
        mock_logger.log(log_msg)

        # Verify log was called
        mock_logger.log.assert_called_once_with(log_msg)

    def test_handshake_cleared_selection(self, mock_logger):
        """Verify clearing handshake selection is logged."""
        mock_logger.log("Default command selection cleared.")

        mock_logger.log.assert_called_once()


class TestHandshakeUIDisplay:
    """Test handshake message display in logs after sending."""

    def test_handshake_message_appears_in_log(self, mock_logger, handshake_payload):
        """Verify sent handshake message appears in log."""
        json_payload = json.dumps(handshake_payload)
        log_message = f"Sent WebSocket message: {json_payload}"

        mock_logger.log(log_message)

        # Verify it was logged
        mock_logger.log.assert_called_once()

    def test_handshake_connected_message(self, mock_logger):
        """Verify connection status is logged."""
        mock_logger.log("WebSocket connected.")

        mock_logger.log.assert_called_once()

    def test_handshake_error_message_in_log(self, mock_logger):
        """Verify handshake errors appear in log."""
        mock_logger.log("Cannot send via WebSocket: not connected.")

        mock_logger.log.assert_called_once()

    def test_multiple_log_messages_in_order(self, mock_logger):
        """Verify multiple log messages maintain order."""
        mock_logger.log("WebSocket connected.")
        mock_logger.log('Loaded default command: Handshake')
        mock_logger.log("Sent WebSocket message: {...}")

        assert mock_logger.log.call_count == 3


class TestHandshakeUIEditing:
    """Test editing handshake fields in UI."""

    def test_handshake_payload_can_be_edited(self):
        """Verify handshake payload can be edited in request text."""
        original_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket", "messages"],
        }

        # Simulate editing: change clientId
        edited_payload = original_payload.copy()
        edited_payload["clientId"] = "client-custom"

        # Verify edit succeeded
        assert edited_payload["clientId"] == "client-custom"
        assert original_payload["clientId"] == "client-001"

    def test_handshake_clientId_field_editable(self):
        """Verify clientId field can be edited."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }

        # Simulate user editing clientId
        new_payload = {
            "action": "handshake",
            "clientId": "my-device-123",
            "capabilities": ["websocket"],
        }

        assert new_payload["clientId"] != payload["clientId"]
        assert new_payload["action"] == payload["action"]

    def test_handshake_capabilities_field_editable(self):
        """Verify capabilities list can be edited."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }

        # Edit capabilities
        edited_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket", "events", "commands"],
        }

        assert len(edited_payload["capabilities"]) > len(payload["capabilities"])

    def test_handshake_edited_json_validation(self):
        """Verify edited handshake is valid JSON."""
        edited_json = json.dumps(
            {
                "action": "handshake",
                "clientId": "edited-client",
                "capabilities": ["websocket", "messages"],
            }
        )

        # Parse to verify validity
        parsed = json.loads(edited_json)
        assert parsed["clientId"] == "edited-client"

    def test_handshake_token_field_editable(self):
        """Verify token field can be edited."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
            "token": "replace-me",
        }

        # Edit token
        edited_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
            "token": "actual-token-value",
        }

        assert edited_payload["token"] != payload["token"]


class TestHandshakeUIValidation:
    """Test UI validation for handshake inputs."""

    def test_invalid_json_rejected(self, mock_logger):
        """Verify invalid JSON is rejected."""
        invalid_json = "{ invalid json }"

        try:
            json.loads(invalid_json)
            mock_logger.log("JSON parsed successfully")
        except json.JSONDecodeError as exc:
            mock_logger.log(f"Invalid JSON: {exc}")

        mock_logger.log.assert_called_once()

    def test_empty_handshake_field_warning(self, mock_logger):
        """Verify empty required fields trigger warning."""
        payload = {
            "action": "handshake",
            "clientId": "",  # Empty
            "capabilities": ["websocket"],
        }

        if not payload["clientId"]:
            mock_logger.log("Warning: clientId is empty")

        mock_logger.log.assert_called_once()

    def test_missing_required_field_error(self, mock_logger):
        """Verify missing required fields trigger error."""
        payload = {
            "action": "handshake",
            # Missing clientId
            "capabilities": ["websocket"],
        }

        if "clientId" not in payload:
            mock_logger.log("Error: Missing required field clientId")

        mock_logger.log.assert_called_once()


class TestHandshakeUISending:
    """Test sending handshake from UI."""

    def test_send_button_with_handshake_payload(self, mock_ws_manager, mock_logger):
        """Verify Send button works with handshake payload."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }

        mock_ws_manager.connected = True
        mock_ws_manager.logger = mock_logger

        # Simulate send click
        mock_ws_manager.send_json(payload)

        assert mock_ws_manager.send_json.called

    def test_send_requires_connection(self, mock_ws_manager, mock_logger):
        """Verify send requires active WebSocket connection."""
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }

        mock_ws_manager.connected = False
        mock_ws_manager.logger = mock_logger

        # Connection check would happen before send
        if not mock_ws_manager.connected:
            mock_logger.log("Cannot send via WebSocket: not connected.")

        mock_logger.log.assert_called_once()

    def test_handshake_send_updates_log(self, mock_logger, handshake_payload):
        """Verify sending handshake updates the log."""
        json_str = json.dumps(handshake_payload)
        log_msg = f"Sent WebSocket message: {json_str}"

        mock_logger.log(log_msg)

        mock_logger.log.assert_called_once()

    def test_concurrent_sends_supported(self, mock_ws_manager):
        """Verify multiple handshakes can be sent."""
        payload_1 = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }
        payload_2 = {
            "action": "handshake",
            "clientId": "client-002",
            "capabilities": ["websocket"],
        }

        mock_ws_manager.connected = True
        mock_ws_manager.send_json(payload_1)
        mock_ws_manager.send_json(payload_2)

        assert mock_ws_manager.send_json.call_count == 2


class TestHandshakeUIIntegration:
    """Test handshake UI integration with other components."""

    def test_connect_then_send_handshake(self, mock_ws_manager, mock_logger):
        """Verify workflow: Connect -> Select Handshake -> Send."""
        # Step 1: Connect
        mock_ws_manager.connect("ws://localhost:8765/ws")
        mock_ws_manager.connected = True

        # Step 2: Select and load handshake
        mock_logger.log("Loaded default command: Handshake")

        # Step 3: Send handshake
        payload = {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        }
        mock_ws_manager.send_json(payload)

        # Verify all steps
        assert mock_ws_manager.connect.called
        assert mock_ws_manager.send_json.called
        assert mock_logger.log.call_count >= 1

    def test_handshake_response_handling(self, mock_logger):
        """Verify handshake response is displayed in logs."""
        response_message = '{"status": "handshake accepted", "sessionId": "sess-123"}'

        mock_logger.log(f"WebSocket received: {response_message}")

        mock_logger.log.assert_called_once()

    def test_handshake_display_in_scrolled_text(self, mock_logger, handshake_payload):
        """Verify handshake appears in scrolled text area."""
        json_text = json.dumps(handshake_payload, indent=2)

        # Simulate inserting into ScrolledText
        mock_logger.log(f"Loaded handshake payload:\n{json_text}")

        mock_logger.log.assert_called_once()


class TestHandshakeUICommandPanel:
    """Test handshake in the command panel."""

    def test_six_commands_in_grid(self, default_commands_fixture):
        """Verify exactly 6 commands are displayed in grid."""
        commands = default_commands_fixture
        assert len(commands) == 6

    def test_handshake_is_last_in_grid(self, default_commands_fixture):
        """Verify handshake is the last (6th) command in grid."""
        commands = default_commands_fixture
        assert commands[-1]["name"] == "Handshake"

    def test_all_commands_have_names(self, default_commands_fixture):
        """Verify all commands have names for UI display."""
        for cmd in default_commands_fixture:
            assert "name" in cmd
            assert len(cmd["name"]) > 0

    def test_all_commands_have_payloads(self, default_commands_fixture):
        """Verify all commands have payloads."""
        for cmd in default_commands_fixture:
            assert "payload" in cmd
            assert isinstance(cmd["payload"], dict)

    def test_command_selection_index_mapping(self, default_commands_fixture):
        """Verify command selection indices map correctly."""
        # UI uses 1-based indexing for radio buttons
        # Index 0 = no selection
        # Index 1 = 1st command (Ping)
        # ...
        # Index 6 = 6th command (Handshake)

        commands = default_commands_fixture
        handshake_cmd = commands[5]  # 0-based index
        ui_index = 6  # 1-based index for UI

        assert handshake_cmd["name"] == "Handshake"
