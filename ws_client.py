import json
import threading
from typing import Callable, Optional

from websocket import WebSocketApp


class WebSocketManager:
    def __init__(
        self,
        logger,
        on_message: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
    ) -> None:
        self.logger = logger
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.ws_app = None
        self.ws_thread = None
        self.connected = False
        self.handshake_sent = False

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

    def _set_connected(self, value: bool) -> None:
        self.connected = value
        self.handshake_sent = False if not value else self.handshake_sent
        if self.on_status_change:
            self.on_status_change(value)

    def _on_open(self, _ws) -> None:
        self._set_connected(True)
        self.logger.log("WebSocket connected.")
        self._send_handshake()

    def _send_handshake(self) -> None:
        """Automatically send handshake message after connection."""
        if self.handshake_sent or not self.connected:
            return

        handshake_payload = {
            "action": "handshake",
            "clientId": "client-001",
            "token": "auth-token-here",
        }

        if not self._validate_handshake(handshake_payload):
            self.logger.log("Handshake validation failed. Skipping auto-send.")
            return

        try:
            raw_payload = json.dumps(handshake_payload)
            self.ws_app.send(raw_payload)
            self.handshake_sent = True
            self.logger.log(f"Handshake sent: {raw_payload}")
        except Exception as exc:
            self.logger.log(f"Handshake send error: {exc}")

    @staticmethod
    def _validate_handshake(payload: dict) -> bool:
        """Validate handshake message structure."""
        if not isinstance(payload, dict):
            return False

        required_keys = ["action", "clientId", "token"]
        for key in required_keys:
            if key not in payload:
                return False
            if payload[key] is None or (isinstance(payload[key], str) and not payload[key].strip()):
                return False

        if payload.get("action") != "handshake":
            return False

        return True

    def _on_message(self, _ws, message: str) -> None:
        if self.on_message:
            self.on_message(message)
        else:
            self.logger.log(f"WebSocket received: {message}")
        
        # Log handshake responses
        try:
            data = json.loads(message)
            if data.get("action") == "handshake_response" or data.get("action") == "handshake_ack":
                self.logger.log(f"Handshake response received: {message}")
        except (json.JSONDecodeError, AttributeError):
            pass

    def _on_error(self, _ws, error) -> None:
        self.logger.log(f"WebSocket error: {error}")

    def _on_close(self, _ws, close_status_code, close_msg) -> None:
        self._set_connected(False)
        self.logger.log(f"WebSocket closed. code={close_status_code}, message={close_msg}")
