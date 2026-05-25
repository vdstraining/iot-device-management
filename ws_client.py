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
        handshake_config: Optional[dict] = None,
    ) -> None:
        self.logger = logger
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.handshake_config = handshake_config or {}
        self.ws_app = None
        self.ws_thread = None
        self.connected = False

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

    def _build_handshake_payload(self) -> dict:
        """Build handshake payload from configuration."""
        if not self.handshake_config:
            return None
        
        return {
            "action": "handshake",
            "clientId": self.handshake_config.get("clientId", "iot-device-simulator-001"),
            "capabilities": self.handshake_config.get(
                "capabilities", 
                ["websocket", "http", "json-messaging", "command-execution"]
            ),
            "session_metadata": self.handshake_config.get(
                "session_metadata",
                {
                    "version": "1.0",
                    "application": "IoT Device Simulator",
                    "platform": "Tkinter",
                },
            ),
            "authentication_context": self.handshake_config.get(
                "authentication_context",
                {"auth_type": "bearer", "token": ""},
            ),
        }

    def send_handshake(self) -> None:
        """Manually send handshake message."""
        if not self.connected or self.ws_app is None:
            self.logger.log("Cannot send handshake: WebSocket not connected.")
            return
        
        if not self.handshake_config.get("enabled", True):
            self.logger.log("Handshake is disabled in configuration.")
            return
        
        handshake_payload = self._build_handshake_payload()
        if handshake_payload:
            try:
                raw_payload = json.dumps(handshake_payload)
                self.ws_app.send(raw_payload)
                self.logger.log(f"Sent handshake message: {raw_payload}")
            except Exception as exc:
                self.logger.log(f"Handshake send error: {exc}")
        else:
            self.logger.log("Failed to build handshake payload.")

    def _set_connected(self, value: bool) -> None:

        self.connected = value
        if self.on_status_change:
            self.on_status_change(value)

    def _on_open(self, _ws) -> None:
        self._set_connected(True)
        self.logger.log("WebSocket connected.")
        
        # Auto-trigger handshake if enabled
        if self.handshake_config.get("enabled", True) and self.handshake_config.get("auto_trigger", True):
            self.send_handshake()

    def _on_message(self, _ws, message: str) -> None:
        if self.on_message:
            self.on_message(message)
        else:
            self.logger.log(f"WebSocket received: {message}")

    def _on_error(self, _ws, error) -> None:
        self.logger.log(f"WebSocket error: {error}")

    def _on_close(self, _ws, close_status_code, close_msg) -> None:
        self._set_connected(False)
        self.logger.log(f"WebSocket closed. code={close_status_code}, message={close_msg}")
