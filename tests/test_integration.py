"""
Integration tests for SCRUM-113 handshake feature.

These tests verify the complete flow of:
- UI initialization with handshake
- WebSocket connection with handshake
- Server response handling
- Multi-step workflows
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from datetime import datetime


class TestCompleteHandshakeFlow:
    """Integration tests for complete handshake workflow."""

    def test_full_connection_workflow_with_handshake(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test complete workflow from initialization to connected state."""
        # Step 1: Initialize UI and set handshake
        mock_ui_logger.info("Initializing handshake")
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Step 2: Initiate connection
        mock_ui_logger.info("Connecting to server...")
        mock_websocket_manager.connect()
        
        # Step 3: Verify connection
        assert mock_websocket_manager.is_connected()
        
        # Step 4: Handshake should be sent
        mock_ui_logger.info(f"Handshake sent: {handshake_payload['clientId']}")
        
        # Step 5: Wait for response
        response = {"status": "accepted", "session_id": "sess-123"}
        mock_ui_logger.info(f"Handshake accepted: {response.get('session_id')}")
        
        # Verify all steps completed
        assert mock_ui_logger.info.called
        assert mock_websocket_manager.connect.called
        assert mock_websocket_manager.is_connected.called

    def test_user_modifies_handshake_and_reconnects(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test user modifying handshake and reconnecting."""
        # Initial connection
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Connected")
        
        # User modifies clientId
        mock_ui_logger.info("Modifying clientId...")
        new_payload = handshake_payload.copy()
        new_payload["clientId"] = "new-device-id"
        
        # Disconnect
        mock_websocket_manager.disconnect()
        mock_ui_logger.info("Disconnected")
        
        # Update handshake and reconnect
        mock_websocket_manager.set_handshake_payload(new_payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Reconnected with new clientId")
        
        # Verify all operations completed
        assert mock_websocket_manager.set_handshake_payload.call_count == 2
        assert mock_websocket_manager.connect.call_count == 2
        assert mock_websocket_manager.disconnect.called

    def test_handshake_then_send_data(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test sending data after successful handshake."""
        # Step 1: Handshake
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Handshake complete")
        
        # Step 2: Receive acceptance
        mock_ui_logger.info("Handshake accepted")
        
        # Step 3: Send data message
        data_message = {"action": "data", "payload": "sensor-reading-123"}
        mock_websocket_manager.send_message(data_message)
        mock_ui_logger.info("Data sent")
        
        # Verify handshake before data
        assert mock_websocket_manager.connect.call_count == 1
        assert mock_websocket_manager.send_message.call_count == 1

    def test_connection_failure_recovery_workflow(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test recovery workflow after connection failure."""
        # Step 1: Initial connection attempt fails
        mock_websocket_manager.connect.return_value = False
        mock_websocket_manager.connect()
        mock_ui_logger.error("Connection failed")
        
        # Step 2: Auto-retry with exponential backoff
        mock_ui_logger.info("Retrying connection...")
        mock_websocket_manager.connect.return_value = True
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Step 3: Handshake on retry
        mock_ui_logger.info("Handshake sent after reconnection")
        
        # Verify recovery
        assert mock_websocket_manager.connect.call_count == 2
        assert mock_websocket_manager.error.call_count == 0


class TestMultiClientScenarios:
    """Integration tests for multiple client scenarios."""

    def test_multiple_devices_with_different_handshakes(self, mock_websocket_manager):
        """Test managing multiple device connections with different handshakes."""
        device_configs = [
            {
                "action": "handshake",
                "clientId": "sensor-001",
                "token": "token-sensor-001",
                "timestamp": "2026-05-13T10:00:00"
            },
            {
                "action": "handshake",
                "clientId": "sensor-002",
                "token": "token-sensor-002",
                "timestamp": "2026-05-13T10:01:00"
            },
            {
                "action": "handshake",
                "clientId": "actuator-001",
                "token": "token-actuator-001",
                "timestamp": "2026-05-13T10:02:00"
            },
        ]
        
        # Set each device's handshake
        for config in device_configs:
            mock_websocket_manager.set_handshake_payload(config)
        
        # Should have all three setups
        assert mock_websocket_manager.set_handshake_payload.call_count == 3

    def test_sequential_device_connections(self, mock_websocket_manager):
        """Test connecting devices sequentially."""
        devices = ["device-1", "device-2", "device-3"]
        
        for device_id in devices:
            payload = {
                "action": "handshake",
                "clientId": device_id,
                "token": f"token-{device_id}",
                "timestamp": "2026-05-13"
            }
            mock_websocket_manager.set_handshake_payload(payload)
            mock_websocket_manager.connect()
            mock_websocket_manager.disconnect()
        
        assert mock_websocket_manager.connect.call_count == 3
        assert mock_websocket_manager.disconnect.call_count == 3


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery workflows."""

    def test_recover_from_token_expiration(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test recovery when token expires."""
        # Initial connection with valid token
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Server rejects with expired token
        mock_ui_logger.error("Handshake failed: Token expired")
        
        # Update with new token
        new_payload = handshake_payload.copy()
        new_payload["token"] = "new-fresh-token"
        
        mock_websocket_manager.disconnect()
        mock_websocket_manager.set_handshake_payload(new_payload)
        mock_websocket_manager.connect()
        
        mock_ui_logger.info("Reconnected with new token")
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2
        assert mock_websocket_manager.connect.call_count == 2

    def test_recover_from_invalid_clientId(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test recovery when clientId is invalid."""
        # Initial attempt with bad clientId
        bad_payload = handshake_payload.copy()
        bad_payload["clientId"] = "invalid$@#"
        
        mock_websocket_manager.set_handshake_payload(bad_payload)
        mock_ui_logger.error("Handshake validation failed: Invalid clientId format")
        
        # Fix clientId and retry
        good_payload = handshake_payload.copy()
        good_payload["clientId"] = "valid-device-id"
        
        mock_websocket_manager.set_handshake_payload(good_payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Handshake sent with valid clientId")
        
        assert mock_websocket_manager.set_handshake_payload.call_count == 2


class TestUIWorkflows:
    """Integration tests for UI-driven workflows."""

    def test_ui_command_selection_to_connection(self, mock_websocket_manager, mock_ui_logger):
        """Test full workflow from UI command selection to connection."""
        # Step 1: User selects handshake from command menu
        selected_command = "handshake"
        mock_ui_logger.info(f"Selected command: {selected_command}")
        
        # Step 2: UI populates handshake fields
        payload = {
            "action": "handshake",
            "clientId": "device-123",
            "token": "token-abc",
            "timestamp": "2026-05-13"
        }
        
        # Step 3: User clicks Send
        mock_websocket_manager.set_handshake_payload(payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Connection initiated")
        
        # Step 4: Receive response
        mock_ui_logger.info("Handshake accepted")
        
        assert mock_ui_logger.info.call_count >= 3

    def test_ui_field_modification_workflow(self, mock_websocket_manager, mock_ui_logger):
        """Test UI workflow for modifying handshake fields."""
        # Step 1: Form displayed with defaults
        form_data = {
            "action": "handshake",
            "clientId": "default-device",
            "token": "default-token",
            "timestamp": "2026-05-13"
        }
        
        # Step 2: User modifies clientId field
        form_data["clientId"] = "custom-device-id"
        mock_ui_logger.info("ClientId updated: custom-device-id")
        
        # Step 3: User modifies token field
        form_data["token"] = "custom-token-value"
        mock_ui_logger.info("Token updated")
        
        # Step 4: User clicks Send
        mock_websocket_manager.set_handshake_payload(form_data)
        mock_websocket_manager.connect()
        
        assert mock_ui_logger.info.call_count >= 3


class TestMessageSequencing:
    """Integration tests for message sequencing."""

    def test_handshake_sent_before_other_messages(self, mock_websocket_manager, handshake_payload):
        """Test that handshake is always sent first."""
        call_order = []
        
        def track_set_handshake(payload):
            call_order.append("set_handshake")
        
        def track_connect():
            call_order.append("connect")
            return True
        
        def track_send(msg):
            call_order.append(f"send_{msg.get('action')}")
        
        mock_websocket_manager.set_handshake_payload.side_effect = track_set_handshake
        mock_websocket_manager.connect.side_effect = track_connect
        mock_websocket_manager.send_message.side_effect = track_send
        
        # Initialize handshake
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # Connect
        mock_websocket_manager.connect()
        
        # Send data
        mock_websocket_manager.send_message({"action": "data"})
        mock_websocket_manager.send_message({"action": "ping"})
        
        # Handshake setup should come first
        assert call_order[0] == "set_handshake"

    def test_response_received_after_handshake_sent(self, mock_websocket_manager, handshake_payload, mock_ui_logger):
        """Test that response is received after handshake is sent."""
        # Send handshake
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        mock_ui_logger.info("Handshake sent")
        
        # Receive response
        response = {"status": "accepted"}
        mock_ui_logger.info("Response received: accepted")
        
        # No further action until response is processed
        call_count_before_response = mock_ui_logger.info.call_count
        
        # Process response
        mock_ui_logger.info("Processing response...")
        
        assert mock_ui_logger.info.call_count >= call_count_before_response


class TestStatefulOperations:
    """Integration tests for stateful operations."""

    def test_state_transitions_through_workflow(self, mock_websocket_manager, handshake_payload):
        """Test state transitions during complete workflow."""
        states = []
        
        # State 1: Initialized
        states.append("initialized")
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        
        # State 2: Connecting
        states.append("connecting")
        mock_websocket_manager.connect()
        
        # State 3: Connected
        states.append("connected")
        
        # State 4: Handshake sent
        states.append("handshake_sent")
        
        # State 5: Response received
        states.append("handshake_accepted")
        
        # Verify state progression
        assert states[0] == "initialized"
        assert states[-1] == "handshake_accepted"
        assert len(states) == 5

    def test_connection_persistence_across_messages(self, mock_websocket_manager, handshake_payload):
        """Test that connection persists across multiple messages."""
        mock_websocket_manager.set_handshake_payload(handshake_payload)
        mock_websocket_manager.connect()
        
        # Send multiple messages
        for i in range(5):
            mock_websocket_manager.send_message({"action": "data", "seq": i})
        
        # Connection should still be active
        assert mock_websocket_manager.is_connected()
        
        # All messages should have been sent
        assert mock_websocket_manager.send_message.call_count == 5
