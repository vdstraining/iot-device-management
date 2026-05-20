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
        on_handshake_sent: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.logger = logger
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.on_handshake_sent = on_handshake_sent
        self.ws_app = None
        self.ws_thread = None
        self.connected = False
        self.handshake_config = {
            "clientId": "default-client",
            "clientVersion": "1.0.0",
            "capabilities": ["WebSocket", "HTTP"],
        }
        self.auto_send_handshake = True

    def set_handshake_config(self, config: dict) -> None:
        """Update handshake configuration with dynamic values."""
        self.handshake_config.update(config)
        self.logger.log(f"Handshake config updated: {self.handshake_config}")

    def set_auto_send_handshake(self, enabled: bool) -> None:
        """Enable/disable automatic handshake sending on connection."""
        self.auto_send_handshake = enabled
        self.logger.log(f"Auto-send handshake: {'enabled' if enabled else 'disabled'}")

    def send_handshake(self) -> None:
        """Manually send a handshake message."""
        if not self.connected or self.ws_app is None:
            self.logger.log("Cannot send handshake: WebSocket not connected.")
            return

        handshake_payload = self._build_handshake_payload()
        self.send_json(handshake_payload)
        
        if self.on_handshake_sent:
            self.on_handshake_sent(handshake_payload)
        
        self.logger.log(f"Handshake sent: {json.dumps(handshake_payload)}")

    def _build_handshake_payload(self) -> dict:
        """Build handshake message payload."""
        from datetime import datetime
        return {
            "action": "handshake",
            "clientId": self.handshake_config.get("clientId", "default-client"),
            "clientVersion": self.handshake_config.get("clientVersion", "1.0.0"),
            "capabilities": self.handshake_config.get("capabilities", ["WebSocket", "HTTP"]),
            "timestamp": datetime.utcnow().isoformat() + "Z",
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

    def _set_connected(self, value: bool) -> None:
        self.connected = value
        if self.on_status_change:
            self.on_status_change(value)

    def _on_open(self, _ws) -> None:
        self._set_connected(True)
        self.logger.log("WebSocket connected.")
        
        # Auto-send handshake after successful connection
        if self.auto_send_handshake:
            self.send_handshake()

    def _on_message(self, _ws, message: str) -> None:
        # Handle handshake response
        try:
            msg_data = json.loads(message)
            if msg_data.get("action") == "handshake_response" or msg_data.get("action") == "handshake":
                self.logger.log(f"Handshake response received: {message}")
        except json.JSONDecodeError:
            pass
        
        if self.on_message:
            self.on_message(message)
        else:
            self.logger.log(f"WebSocket received: {message}")

    def _on_error(self, _ws, error) -> None:
        self.logger.log(f"WebSocket error: {error}")

    def _on_close(self, _ws, close_status_code, close_msg) -> None:
        self._set_connected(False)
        self.logger.log(f"WebSocket closed. code={close_status_code}, message={close_msg}")
