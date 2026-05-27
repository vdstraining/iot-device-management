import json
import threading
from typing import Callable, Optional

from websocket import WebSocketApp
from utilities import (
    MESSAGE_TYPE_HANDSHAKE_INIT,
    MESSAGE_TYPE_HANDSHAKE_ACK,
    MESSAGE_TYPE_HANDSHAKE_ERROR,
    HANDSHAKE_STATE_PENDING,
    HANDSHAKE_STATE_COMPLETED,
    HANDSHAKE_STATE_FAILED,
    DEFAULT_HANDSHAKE_TIMEOUT,
    PROTOCOL_VERSION,
    create_handshake_init,
)


class WebSocketManager:
    def __init__(
        self,
        logger,
        on_message: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[bool], None]] = None,
        device_id: str = "device-001",
        handshake_timeout: int = DEFAULT_HANDSHAKE_TIMEOUT,
    ) -> None:
        self.logger = logger
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.ws_app = None
        self.ws_thread = None
        self.connected = False
        
        # Handshake configuration
        self.device_id = device_id
        self.handshake_timeout = handshake_timeout
        self.handshake_state = HANDSHAKE_STATE_PENDING
        self.handshake_timer = None
        self.negotiated_capabilities = []
        self.server_info = {}

    def connect(self, ws_url: str) -> None:
        if self.connected:
            self.logger.log("WebSocket is already connected.")
            return

        if not ws_url:
            self.logger.log("WebSocket URL is empty.")
            return

        self.logger.log(f"Connecting to WebSocket: {ws_url}")
        self.handshake_state = HANDSHAKE_STATE_PENDING

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
        self._cancel_handshake_timer()
        try:
            self.ws_app.close()
        except Exception as exc:
            self.logger.log(f"Disconnect error: {exc}")

    def send_json(self, payload: dict) -> None:
        if not self.connected or self.ws_app is None:
            self.logger.log("Cannot send via WebSocket: not connected.")
            return

        # Reject user messages during handshake if they're not handshake messages
        if self.handshake_state == HANDSHAKE_STATE_PENDING:
            msg_type = payload.get("type")
            if msg_type not in (MESSAGE_TYPE_HANDSHAKE_INIT, MESSAGE_TYPE_HANDSHAKE_ACK):
                self.logger.log("Cannot send message: handshake in progress. Wait for completion.")
                return

        try:
            raw_payload = json.dumps(payload)
            self.ws_app.send(raw_payload)
            self.logger.log(f"Sent WebSocket message: {raw_payload}")
        except Exception as exc:
            self.logger.log(f"WebSocket send error: {exc}")

    def _set_connected(self, value: bool) -> None:
        # Only notify UI if handshake is completed or connection is being closed
        if value and self.handshake_state != HANDSHAKE_STATE_COMPLETED:
            # Connection established, but handshake not yet complete
            return
        self.connected = value
        if self.on_status_change:
            self.on_status_change(value)

    def _on_open(self, _ws) -> None:
        self.logger.log("WebSocket connected. Initiating handshake...")
        self.handshake_state = HANDSHAKE_STATE_PENDING
        self._send_handshake_init()
        self._start_handshake_timer()

    def _on_message(self, _ws, message: str) -> None:
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # Route handshake messages separately
            if msg_type == MESSAGE_TYPE_HANDSHAKE_ACK:
                self._handle_handshake_ack(data)
                return
            elif msg_type == MESSAGE_TYPE_HANDSHAKE_ERROR:
                self._handle_handshake_error(data)
                return
            
            # Process user messages only if handshake is completed
            if self.handshake_state != HANDSHAKE_STATE_COMPLETED:
                self.logger.log(f"Ignoring message during handshake: {message}")
                return
            
            if self.on_message:
                self.on_message(message)
            else:
                self.logger.log(f"WebSocket received: {message}")
        except json.JSONDecodeError:
            # If not JSON, pass it through anyway
            if self.on_message:
                self.on_message(message)
            else:
                self.logger.log(f"WebSocket received: {message}")

    def _on_error(self, _ws, error) -> None:
        self.logger.log(f"WebSocket error: {error}")

    def _on_close(self, _ws, close_status_code, close_msg) -> None:
        self._cancel_handshake_timer()
        self.connected = False
        self.handshake_state = HANDSHAKE_STATE_PENDING
        if self.on_status_change:
            self.on_status_change(False)
        self.logger.log(f"WebSocket closed. code={close_status_code}, message={close_msg}")

    def _send_handshake_init(self) -> None:
        """Send HANDSHAKE_INIT message to server."""
        if self.ws_app is None:
            return
        
        handshake_msg = create_handshake_init(
            device_id=self.device_id,
            capabilities=["websocket", "json"],
            auth_token=None,
        )
        
        try:
            raw_payload = json.dumps(handshake_msg)
            self.ws_app.send(raw_payload)
            self.logger.log(f"Sent handshake init: {raw_payload}")
        except Exception as exc:
            self.logger.log(f"Error sending handshake init: {exc}")
            self.handshake_state = HANDSHAKE_STATE_FAILED
            self._cancel_handshake_timer()
            self.disconnect()

    def _handle_handshake_ack(self, data: dict) -> None:
        """Handle HANDSHAKE_ACK message from server."""
        self._cancel_handshake_timer()
        
        status = data.get("status", "unknown")
        protocol_version = data.get("protocol_version", PROTOCOL_VERSION)
        server_info = data.get("server_info", {})
        
        if status.lower() == "success":
            self.handshake_state = HANDSHAKE_STATE_COMPLETED
            self.server_info = server_info
            self.negotiated_capabilities = server_info.get("capabilities", ["websocket", "json"])
            self.logger.log(f"Handshake completed successfully. Protocol: {protocol_version}, Capabilities: {self.negotiated_capabilities}")
            
            # Now mark connection as ready
            self.connected = True
            if self.on_status_change:
                self.on_status_change(True)
        else:
            self.logger.log(f"Handshake ACK failed with status: {status}")
            self.handshake_state = HANDSHAKE_STATE_FAILED
            self.disconnect()

    def _handle_handshake_error(self, data: dict) -> None:
        """Handle HANDSHAKE_ERROR message from server."""
        self._cancel_handshake_timer()
        
        error_code = data.get("error_code", "UNKNOWN")
        error_message = data.get("error_message", "Unknown error")
        
        self.logger.log(f"Handshake error: {error_code} - {error_message}")
        self.handshake_state = HANDSHAKE_STATE_FAILED
        self.disconnect()

    def _start_handshake_timer(self) -> None:
        """Start handshake timeout timer."""
        self._cancel_handshake_timer()
        self.handshake_timer = threading.Timer(
            self.handshake_timeout,
            self._on_handshake_timeout
        )
        self.handshake_timer.daemon = True
        self.handshake_timer.start()

    def _cancel_handshake_timer(self) -> None:
        """Cancel handshake timeout timer."""
        if self.handshake_timer is not None:
            self.handshake_timer.cancel()
            self.handshake_timer = None

    def _on_handshake_timeout(self) -> None:
        """Handle handshake timeout."""
        if self.handshake_state == HANDSHAKE_STATE_PENDING:
            self.logger.log(f"Handshake timeout after {self.handshake_timeout} seconds. Closing connection.")
            self.handshake_state = HANDSHAKE_STATE_FAILED
            self.disconnect()
