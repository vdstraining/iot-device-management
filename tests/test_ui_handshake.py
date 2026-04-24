"""
Tests for handshake-specific logic in ui.py (AppUI).

Strategy: AppUI.__new__ is used to create a bare instance without running
__init__, which avoids launching a real Tk window.  All tkinter-derived
attributes (StringVar, IntVar, root, request_text, log_text) are replaced
with MagicMock objects so that only the pure Python business logic is under
test.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from ui import AppUI


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_app() -> AppUI:
    """
    Return an AppUI instance whose __init__ has been bypassed.
    Only the attributes required by the methods under test are populated.
    """
    app = AppUI.__new__(AppUI)

    # Tkinter StringVar / IntVar substitutes
    app.client_id_var = MagicMock()
    app.token_var = MagicMock()
    app.client_id_var.get.return_value = ""
    app.token_var.get.return_value = ""
    app.selected_option = MagicMock()

    # Handshake / connection state
    app.handshake_acknowledged = False
    app.ws_connected = False

    # Collaborator mocks
    app.logger = MagicMock()
    app.ws_manager = MagicMock()
    app.root = MagicMock()
    app.request_text = MagicMock()
    app.log_text = MagicMock()

    return app


# ---------------------------------------------------------------------------
# _resolve_dynamic_fields
# ---------------------------------------------------------------------------

class TestResolveDynamicFields:
    def test_replaces_client_id_placeholder(self):
        app = _make_app()
        app.client_id_var.get.return_value = "my-device-42"

        result = app._resolve_dynamic_fields("{{clientId}}")

        assert result == "my-device-42"

    def test_replaces_token_placeholder(self):
        app = _make_app()
        app.token_var.get.return_value = "s3cr3t"

        result = app._resolve_dynamic_fields("{{token}}")

        assert result == "s3cr3t"

    def test_leaves_unrecognised_string_unchanged(self):
        app = _make_app()

        assert app._resolve_dynamic_fields("hello") == "hello"
        assert app._resolve_dynamic_fields("{{unknown}}") == "{{unknown}}"

    def test_resolves_nested_dict_recursively(self):
        app = _make_app()
        app.client_id_var.get.return_value = "cid-1"
        app.token_var.get.return_value = "tok-1"

        result = app._resolve_dynamic_fields(
            {"clientId": "{{clientId}}", "token": "{{token}}", "action": "handshake"}
        )

        assert result == {"clientId": "cid-1", "token": "tok-1", "action": "handshake"}

    def test_resolves_list_recursively(self):
        app = _make_app()
        app.client_id_var.get.return_value = "cid-2"

        result = app._resolve_dynamic_fields(["{{clientId}}", "static"])

        assert result == ["cid-2", "static"]

    def test_non_string_scalar_is_returned_unchanged(self):
        app = _make_app()

        assert app._resolve_dynamic_fields(42) == 42
        assert app._resolve_dynamic_fields(True) is True
        assert app._resolve_dynamic_fields(None) is None


# ---------------------------------------------------------------------------
# _is_handshake_payload
# ---------------------------------------------------------------------------

class TestIsHandshakePayload:
    def test_true_when_action_is_handshake(self):
        app = _make_app()
        assert app._is_handshake_payload({"action": "handshake"}) is True

    def test_true_when_type_is_Handshake(self):
        app = _make_app()
        assert app._is_handshake_payload({"type": "Handshake"}) is True

    def test_false_for_ping_payload(self):
        app = _make_app()
        assert app._is_handshake_payload({"action": "ping"}) is False

    def test_false_for_empty_dict(self):
        app = _make_app()
        assert app._is_handshake_payload({}) is False

    def test_false_for_subscribe_payload(self):
        app = _make_app()
        assert app._is_handshake_payload({"action": "subscribe", "channel": "events"}) is False


# ---------------------------------------------------------------------------
# _validate_websocket_payload
# ---------------------------------------------------------------------------

class TestValidateWebSocketPayload:
    def _valid_handshake(self):
        return {
            "type": "Handshake",
            "action": "handshake",
            "clientId": "abc",
            "token": "xyz",
            "capabilities": ["ws"],
            "session": {"client": "test"},
        }

    def test_valid_handshake_payload_returns_true(self):
        app = _make_app()
        assert app._validate_websocket_payload(self._valid_handshake()) is True

    def test_non_handshake_payload_always_returns_true(self):
        app = _make_app()
        assert app._validate_websocket_payload({"action": "ping"}) is True
        assert app._validate_websocket_payload({"action": "subscribe", "channel": "e"}) is True

    def test_non_dict_returns_false_and_logs(self):
        app = _make_app()

        assert app._validate_websocket_payload("not-a-dict") is False

        app.logger.log.assert_called()

    def test_handshake_with_missing_type_returns_false(self):
        """action=handshake but no 'type' field must fail validation."""
        app = _make_app()
        payload = {"action": "handshake", "clientId": "a", "token": "b"}

        result = app._validate_websocket_payload(payload)

        assert result is False
        logged = " ".join(str(c) for c in app.logger.log.call_args_list)
        assert "type" in logged.lower()

    def test_handshake_with_wrong_type_value_returns_false(self):
        app = _make_app()
        payload = {**self._valid_handshake(), "type": "WrongType"}

        assert app._validate_websocket_payload(payload) is False

    def test_handshake_with_wrong_action_value_returns_false(self):
        app = _make_app()
        payload = {**self._valid_handshake(), "action": "wrong"}

        assert app._validate_websocket_payload(payload) is False

    def test_handshake_with_non_list_capabilities_returns_false(self):
        app = _make_app()
        payload = {**self._valid_handshake(), "capabilities": "ws"}

        assert app._validate_websocket_payload(payload) is False

    def test_handshake_with_non_dict_session_returns_false(self):
        app = _make_app()
        payload = {**self._valid_handshake(), "session": "bad"}

        assert app._validate_websocket_payload(payload) is False

    def test_handshake_without_optional_capabilities_and_session_is_valid(self):
        """capabilities and session are optional fields."""
        app = _make_app()
        payload = {"type": "Handshake", "action": "handshake", "clientId": "a", "token": "b"}

        assert app._validate_websocket_payload(payload) is True


# ---------------------------------------------------------------------------
# _handle_ws_message  (inbound server responses)
# ---------------------------------------------------------------------------

class TestHandleWsMessage:
    def test_type_Handshake_sets_acknowledged_true(self):
        app = _make_app()

        app._handle_ws_message(json.dumps({"type": "Handshake"}))

        assert app.handshake_acknowledged is True

    def test_type_HandshakeAck_sets_acknowledged_true(self):
        app = _make_app()

        app._handle_ws_message(json.dumps({"type": "HandshakeAck"}))

        assert app.handshake_acknowledged is True

    def test_other_message_type_does_not_set_acknowledged(self):
        app = _make_app()

        app._handle_ws_message(json.dumps({"type": "Ping"}))

        assert app.handshake_acknowledged is False

    def test_message_without_type_does_not_set_acknowledged(self):
        app = _make_app()

        app._handle_ws_message(json.dumps({"action": "echo"}))

        assert app.handshake_acknowledged is False

    def test_received_message_is_logged(self):
        app = _make_app()
        msg = json.dumps({"type": "Handshake"})

        app._handle_ws_message(msg)

        logged = " ".join(str(c) for c in app.logger.log.call_args_list)
        assert "WebSocket received" in logged

    def test_handshake_acknowledgement_is_logged(self):
        app = _make_app()

        app._handle_ws_message(json.dumps({"type": "HandshakeAck"}))

        logged = " ".join(str(c) for c in app.logger.log.call_args_list)
        assert "acknowledged" in logged.lower()

    def test_invalid_json_does_not_raise(self):
        app = _make_app()

        app._handle_ws_message("not valid json {{")

        assert app.handshake_acknowledged is False

    def test_json_array_does_not_set_acknowledged(self):
        """Top-level JSON array is valid JSON but not a dict — must not ack."""
        app = _make_app()

        app._handle_ws_message(json.dumps([{"type": "Handshake"}]))

        assert app.handshake_acknowledged is False


# ---------------------------------------------------------------------------
# _handle_ws_open  (WebSocket connection established callback)
# ---------------------------------------------------------------------------

class TestHandleWsOpen:
    def test_ws_open_schedules_send_handshake_via_root_after(self):
        app = _make_app()

        app._handle_ws_open()

        app.root.after.assert_called_once_with(0, app._send_handshake)


# ---------------------------------------------------------------------------
# _send_handshake
# ---------------------------------------------------------------------------

class TestSendHandshake:
    def test_send_handshake_calls_ws_manager_send_json(self):
        app = _make_app()
        app.client_id_var.get.return_value = "client-1"
        app.token_var.get.return_value = "token-1"

        app._send_handshake()

        app.ws_manager.send_json.assert_called_once()

    def test_send_handshake_payload_contains_resolved_client_id(self):
        app = _make_app()
        app.client_id_var.get.return_value = "device-xyz"
        app.token_var.get.return_value = "tok"

        app._send_handshake()

        sent_payload = app.ws_manager.send_json.call_args[0][0]
        assert sent_payload["clientId"] == "device-xyz"

    def test_send_handshake_payload_contains_resolved_token(self):
        app = _make_app()
        app.client_id_var.get.return_value = "cid"
        app.token_var.get.return_value = "my-secret-token"

        app._send_handshake()

        sent_payload = app.ws_manager.send_json.call_args[0][0]
        assert sent_payload["token"] == "my-secret-token"

    def test_send_handshake_payload_has_correct_type(self):
        app = _make_app()

        app._send_handshake()

        sent_payload = app.ws_manager.send_json.call_args[0][0]
        assert sent_payload["type"] == "Handshake"

    def test_send_handshake_resets_acknowledged_to_false(self):
        app = _make_app()
        app.handshake_acknowledged = True

        app._send_handshake()

        assert app.handshake_acknowledged is False

    def test_send_handshake_does_not_send_if_validation_fails(self):
        """When validation returns False the payload must NOT be forwarded."""
        app = _make_app()

        with patch.object(app, "_validate_websocket_payload", return_value=False):
            app._send_handshake()

        app.ws_manager.send_json.assert_not_called()

    def test_send_handshake_logs_error_when_validation_fails(self):
        app = _make_app()

        with patch.object(app, "_validate_websocket_payload", return_value=False):
            app._send_handshake()

        app.logger.log.assert_called()


# ---------------------------------------------------------------------------
# _handle_ws_status_change
# ---------------------------------------------------------------------------

class TestHandleWsStatusChange:
    def test_disconnect_resets_handshake_acknowledged(self):
        app = _make_app()
        app.handshake_acknowledged = True

        app._handle_ws_status_change(False)

        assert app.handshake_acknowledged is False

    def test_connect_does_not_reset_handshake_acknowledged(self):
        app = _make_app()
        app.handshake_acknowledged = True

        app._handle_ws_status_change(True)

        assert app.handshake_acknowledged is True

    def test_ws_connected_is_set_to_true_on_connect(self):
        app = _make_app()

        app._handle_ws_status_change(True)

        assert app.ws_connected is True

    def test_ws_connected_is_set_to_false_on_disconnect(self):
        app = _make_app()
        app.ws_connected = True

        app._handle_ws_status_change(False)

        assert app.ws_connected is False
