"""Unit tests for ws_client module."""
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from ws_client import WebSocketManager


class TestWebSocketManagerInit:
    """Tests for WebSocketManager initialization."""

    def test_init_with_default_parameters(self, mock_logger):
        """Test initialization with default parameters."""
        manager = WebSocketManager(logger=mock_logger)

        assert manager.logger is mock_logger
        assert manager.connected is False
        assert manager.auto_handshake is True
        assert manager.handshake_payload is not None

    def test_init_auto_handshake_true(self, mock_logger):
        """Test initialization with auto_handshake=True."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
        assert manager.auto_handshake is True

    def test_init_auto_handshake_false(self, mock_logger):
        """Test initialization with auto_handshake=False."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        assert manager.auto_handshake is False

    def test_init_with_custom_handshake_payload(self, mock_logger, valid_handshake_payload):
        """Test initialization with a custom handshake payload."""
        manager = WebSocketManager(
            logger=mock_logger, handshake_payload=valid_handshake_payload
        )
        assert manager.handshake_payload == valid_handshake_payload

    def test_init_default_handshake_payload_structure(self, mock_logger):
        """Test that default handshake payload has correct structure."""
        manager = WebSocketManager(logger=mock_logger)
        payload = manager.handshake_payload

        assert payload.get("type") == "handshake"
        assert "clientId" in payload
        assert "version" in payload

    def test_init_with_callbacks(self, mock_logger, mock_callback):
        """Test initialization with custom callbacks."""
        manager = WebSocketManager(
            logger=mock_logger,
            on_message=mock_callback,
            on_status_change=mock_callback,
        )

        assert manager.on_message is mock_callback
        assert manager.on_status_change is mock_callback

    def test_init_with_none_callbacks(self, mock_logger):
        """Test initialization with None callbacks."""
        manager = WebSocketManager(
            logger=mock_logger, on_message=None, on_status_change=None
        )

        assert manager.on_message is None
        assert manager.on_status_change is None


class TestValidatePayload:
    """Tests for _validate_payload method."""

    def test_validate_payload_valid_json_serializable(self, mock_logger):
        """Test validation of a valid JSON-serializable payload."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {"type": "test", "data": "value"}

        result = manager._validate_payload(payload)

        assert result is True
        # Should not log error
        mock_logger.log.assert_not_called()

    def test_validate_payload_with_nested_dict(self, mock_logger):
        """Test validation of nested dictionary."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "nested": {"key": "value", "number": 123},
        }

        result = manager._validate_payload(payload)

        assert result is True

    def test_validate_payload_with_list(self, mock_logger):
        """Test validation of payload with list."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {"type": "test", "items": [1, 2, 3]}

        result = manager._validate_payload(payload)

        assert result is True

    def test_validate_payload_with_numbers_and_booleans(self, mock_logger):
        """Test validation of various JSON-serializable types."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {
            "type": "test",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
        }

        result = manager._validate_payload(payload)

        assert result is True

    def test_validate_payload_with_non_serializable_object(self, mock_logger):
        """Test validation fails for non-JSON-serializable object."""
        manager = WebSocketManager(logger=mock_logger)

        class CustomObject:
            pass

        payload = {"type": "test", "obj": CustomObject()}

        result = manager._validate_payload(payload)

        assert result is False
        # Should log error
        mock_logger.log.assert_called()

    def test_validate_payload_with_circular_reference(self, mock_logger):
        """Test validation fails for circular references."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {"type": "test"}
        payload["self"] = payload  # Circular reference

        result = manager._validate_payload(payload)

        assert result is False

    def test_validate_payload_empty_dict(self, mock_logger):
        """Test validation of empty dictionary."""
        manager = WebSocketManager(logger=mock_logger)
        payload = {}

        result = manager._validate_payload(payload)

        assert result is True


class TestSendHandshake:
    """Tests for _send_handshake method."""

    def test_send_handshake_when_not_connected(self, mock_logger):
        """Test _send_handshake does nothing when not connected."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.connected = False
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should log that handshake was skipped
        mock_logger.log.assert_called_with("Handshake skipped: WebSocket not connected.")
        # Should not send
        manager.ws_app.send.assert_not_called()

    def test_send_handshake_with_valid_payload(self, mock_logger, valid_handshake_payload):
        """Test _send_handshake with valid payload."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=valid_handshake_payload,
        )
        manager.connected = True
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should send the handshake
        expected_json = json.dumps(valid_handshake_payload)
        manager.ws_app.send.assert_called_once_with(expected_json)
        # Should log success
        assert any(
            "Sent WebSocket handshake" in str(call)
            for call in mock_logger.log.call_args_list
        )

    def test_send_handshake_invalid_payload_structure(self, mock_logger):
        """Test _send_handshake with invalid payload structure."""
        invalid_payload = {
            "type": "invalid",  # Should be "handshake"
            "clientId": "test",
            "version": "1.0",
        }
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=invalid_payload,
        )
        manager.connected = True
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should not send due to validation failure
        manager.ws_app.send.assert_not_called()
        # Should log validation error
        assert any(
            "Handshake validation failed" in str(call)
            for call in mock_logger.log.call_args_list
        )

    def test_send_handshake_missing_required_field(self, mock_logger):
        """Test _send_handshake with missing required field."""
        invalid_payload = {
            "type": "handshake",
            # Missing clientId
            "version": "1.0",
        }
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=invalid_payload,
        )
        manager.connected = True
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should not send
        manager.ws_app.send.assert_not_called()
        # Should log validation error
        assert any(
            "Handshake validation failed" in str(call)
            for call in mock_logger.log.call_args_list
        )

    def test_send_handshake_non_serializable_payload(self, mock_logger):
        """Test _send_handshake with non-JSON-serializable payload."""

        class CustomObj:
            pass

        invalid_payload = {
            "type": "handshake",
            "clientId": "test",
            "version": "1.0",
            "obj": CustomObj(),
        }
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=invalid_payload,
        )
        manager.connected = True
        manager.ws_app = Mock()

        manager._send_handshake()

        # Should not send
        manager.ws_app.send.assert_not_called()

    def test_send_handshake_exception_handling(self, mock_logger, valid_handshake_payload):
        """Test _send_handshake handles send exceptions."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=valid_handshake_payload,
        )
        manager.connected = True
        manager.ws_app = Mock()
        manager.ws_app.send.side_effect = Exception("Network error")

        manager._send_handshake()

        # Should log the error
        assert any(
            "Handshake send error" in str(call)
            for call in mock_logger.log.call_args_list
        )


class TestOnOpen:
    """Tests for _on_open callback method."""

    def test_on_open_auto_handshake_enabled(self, mock_logger, valid_handshake_payload):
        """Test _on_open triggers handshake when auto_handshake=True."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=True,
            handshake_payload=valid_handshake_payload,
        )
        manager.ws_app = Mock()

        with patch.object(manager, "_send_handshake") as mock_send_handshake:
            manager._on_open(Mock())

            # Should set connected to True
            assert manager.connected is True
            # Should call _send_handshake
            mock_send_handshake.assert_called_once()

    def test_on_open_auto_handshake_disabled(self, mock_logger):
        """Test _on_open does not trigger handshake when auto_handshake=False."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.ws_app = Mock()

        with patch.object(manager, "_send_handshake") as mock_send_handshake:
            manager._on_open(Mock())

            # Should set connected to True
            assert manager.connected is True
            # Should NOT call _send_handshake
            mock_send_handshake.assert_not_called()

    def test_on_open_calls_status_callback(self, mock_logger, mock_callback):
        """Test _on_open calls on_status_change callback."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            on_status_change=mock_callback,
        )
        manager.ws_app = Mock()

        manager._on_open(Mock())

        # Should call status callback with True
        mock_callback.assert_called_once_with(True)

    def test_on_open_logs_message(self, mock_logger):
        """Test _on_open logs connection message."""
        manager = WebSocketManager(logger=mock_logger, auto_handshake=False)
        manager.ws_app = Mock()

        manager._on_open(Mock())

        # Should log connection message
        assert any(
            "WebSocket connected" in str(call) for call in mock_logger.log.call_args_list
        )


class TestSetConnected:
    """Tests for _set_connected method."""

    def test_set_connected_true(self, mock_logger, mock_callback):
        """Test _set_connected sets connected flag and calls callback."""
        manager = WebSocketManager(
            logger=mock_logger, on_status_change=mock_callback
        )

        manager._set_connected(True)

        assert manager.connected is True
        mock_callback.assert_called_once_with(True)

    def test_set_connected_false(self, mock_logger, mock_callback):
        """Test _set_connected to False."""
        manager = WebSocketManager(
            logger=mock_logger, on_status_change=mock_callback
        )
        manager.connected = True

        manager._set_connected(False)

        assert manager.connected is False
        mock_callback.assert_called_once_with(False)

    def test_set_connected_without_callback(self, mock_logger):
        """Test _set_connected without callback."""
        manager = WebSocketManager(logger=mock_logger, on_status_change=None)

        manager._set_connected(True)

        assert manager.connected is True


class TestHandshakeIntegration:
    """Integration tests for handshake functionality."""

    def test_auto_handshake_flow(self, mock_logger, valid_handshake_payload):
        """Test the complete auto-handshake flow on connection."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=True,
            handshake_payload=valid_handshake_payload,
        )
        manager.ws_app = Mock()

        # Simulate connection
        manager._on_open(Mock())

        # Should be connected
        assert manager.connected is True

        # Should have sent handshake
        expected_json = json.dumps(valid_handshake_payload)
        manager.ws_app.send.assert_called_once_with(expected_json)

    def test_manual_handshake_flow(self, mock_logger, valid_handshake_payload):
        """Test manual handshake call when auto_handshake=False."""
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=False,
            handshake_payload=valid_handshake_payload,
        )
        manager.ws_app = Mock()
        manager.connected = True

        # Manually call handshake
        manager._send_handshake()

        # Should have sent handshake
        expected_json = json.dumps(valid_handshake_payload)
        manager.ws_app.send.assert_called_once_with(expected_json)

    def test_connection_remains_established_on_handshake_failure(
        self, mock_logger
    ):
        """Test that connection remains if handshake validation fails."""
        invalid_payload = {
            "type": "invalid",  # Wrong type
            "clientId": "test",
            "version": "1.0",
        }
        manager = WebSocketManager(
            logger=mock_logger,
            auto_handshake=True,
            handshake_payload=invalid_payload,
        )
        manager.ws_app = Mock()

        # Call _on_open
        manager._on_open(Mock())

        # Should still be connected despite handshake failure
        assert manager.connected is True
        # But should not have sent anything
        manager.ws_app.send.assert_not_called()
