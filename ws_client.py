import json
import threading
from typing import Callable, Optional, Any, Dict

from websocket import WebSocketApp

from jsonschema import validate, ValidationError
from config import get_config


class WebSocketManager:
    def __init__(
        self,
        logger,
        on_message: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
        runtime_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.logger = logger
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.ws_app = None
        self.ws_thread = None
        self.connected = False
        self.config = get_config(runtime_config)
        self.connection_state: Dict[str, Any] = {}

        # Handshake JSON schema
        self._handshake_schema = {
            "type": "object",
            "properties": {
                "type": {"const": "handshake"},
                "clientId": {"type": "string"},
                "capabilities": {"type": "object"},
                "token": {"type": "string"},
            },
            "required": ["type", "clientId"],
            "additionalProperties": True,
        }

    def connect(self, ws_url: str) -> None:
        if self.connected:
            self.logger.log("WebSocket is already connected.")
            return

        if not ws_url:
            self.logger.log("WebSocket URL is empty.")
            return

        self.logger.log(f"Connecting to WebSocket: {ws_url}")

        def run_ws() -> None:
            self.ws_app = WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            try:
                self.ws_app.run_forever()
            except Exception as exc:
                self.logger.log(f"WebSocket run_forever exception: {exc}")

        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()

    def disconnect(self) -> None:
        if self.ws_app is None:
            self.logger.log("No active WebSocket connection.")
            return

        self.logger.log("Disconnecting WebSocket...")
        try:
            self.ws_app.close()
        except Exception as exc:
            self.logger.log(f"Disconnect error: {exc}")

    def send_json(self, payload: dict) -> None:
        if not self.connected or self.ws_app is None:
            self.logger.log("Cannot send via WebSocket: not connected.")
            return

        try:
            raw_payload = json.dumps(payload)
            self.ws_app.send(raw_payload)
            self.logger.log(f"Sent WebSocket message: {raw_payload}")
        except Exception as exc:
            self.logger.log(f"WebSocket send error: {exc}")

    def send_handshake(self, runtime_config: Optional[Dict[str, Any]] = None) -> None:
        """Build, validate, and send the handshake message using config precedence.
        runtime_config: optional overrides for this send.
        """
        cfg = get_config(runtime_config or {})

        payload = {
            "type": "handshake",
            "clientId": cfg.get("handshake.clientId"),
        }
        if cfg.get("handshake.token"):
            payload["token"] = cfg.get("handshake.token")

        # validate schema
        try:
            validate(instance=payload, schema=self._handshake_schema)
        except ValidationError as exc:
            self.logger.log(f"Handshake validation failed: {exc.message}")
            return

        # log outgoing with redacted token
        logged = self._mask_token_in_obj(payload)
        try:
            raw_payload = json.dumps(payload)
            self.ws_app.send(raw_payload)
            self.logger.log(f"Outgoing -> {json.dumps(logged)}")
        except Exception as exc:
            self.logger.log(f"WebSocket handshake send error: {exc}")

    def _mask_token_in_obj(self, obj: Any) -> Any:
        """Return a copy of obj with 'token' fields masked (first 4 chars + '***')."""
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if k == "token" and isinstance(v, str) and v:
                    out[k] = v[:4] + "***"
                else:
                    out[k] = self._mask_token_in_obj(v)
            return out
        if isinstance(obj, list):
            return [self._mask_token_in_obj(i) for i in obj]
        return obj

    def _set_connected(self, value: bool) -> None:
        self.connected = value
        if self.on_status_change:
            self.on_status_change(value)

    def _on_open(self, _ws) -> None:
        self._set_connected(True)
        self.logger.log("WebSocket connected.")
        # Auto-send handshake if enabled
        try:
            if self.config.get("handshake.autoSend", True):
                # send after open
                self.send_handshake()
        except Exception:
            # do not crash on handshake send failure
            pass

    def _on_message(self, _ws, message: str) -> None:
        # Attempt to parse JSON and mask token before logging
        try:
            parsed = json.loads(message)
        except Exception:
            parsed = None

        if parsed is not None and isinstance(parsed, dict):
            # mask token for logging
            logged = self._mask_token_in_obj(parsed)
            self.logger.log(f"Incoming <- {json.dumps(logged)}")
            # optionally apply to connection state
            if self.config.get("handshake.applyResponseToState"):
                # store entire parsed object
                self.connection_state["handshakeResponse"] = parsed
        else:
            self.logger.log(f"WebSocket received: {message}")

        if self.on_message:
            self.on_message(message)

    def _on_error(self, _ws, error) -> None:
        self.logger.log(f"WebSocket error: {error}")

    def _on_close(self, _ws, close_status_code, close_msg) -> None:
        self._set_connected(False)
        self.logger.log(f"WebSocket closed. code={close_status_code}, message={close_msg}")
