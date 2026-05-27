"""
Handshake message handling for WebSocket connections.
Manages building, sending, and responding to handshake messages.
"""

import json
from typing import Optional, Callable, Dict, Any

from handshake_config import HandshakeConfig


class HandshakeHandler:
    """Manages WebSocket handshake communication."""

    def __init__(
        self,
        logger,
        config: Optional[HandshakeConfig] = None,
        on_handshake_response: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        """
        Initialize handshake handler.

        Args:
            logger: Logger instance for logging handshake events
            config: HandshakeConfig instance (uses defaults if None)
            on_handshake_response: Optional callback for handshake response handling
        """
        self.logger = logger
        self.config = config or HandshakeConfig()
        self.on_handshake_response = on_handshake_response
        self.handshake_sent = False
        self.handshake_acknowledged = False

    def build_handshake_message(self) -> Optional[dict]:
        """
        Build and validate handshake message.

        Returns:
            Handshake payload dict if valid, None if validation fails
        """
        is_valid, error_msg = self.config.validate()
        if not is_valid:
            self.logger.log(f"Handshake validation failed: {error_msg}")
            return None

        payload = self.config.build_handshake_payload()
        return payload

    def send_handshake(self, send_callback: Callable[[dict], None]) -> bool:
        """
        Send handshake message to server.

        Args:
            send_callback: Function to call to send the message (e.g., ws_manager.send_json)

        Returns:
            True if handshake was sent successfully, False otherwise
        """
        if self.handshake_sent:
            self.logger.log("Handshake already sent in this connection.")
            return False

        payload = self.build_handshake_message()
        if payload is None:
            return False

        try:
            send_callback(payload)
            self.handshake_sent = True
            self.logger.log(f"Handshake message sent: {json.dumps(payload)}")
            return True
        except Exception as exc:
            self.logger.log(f"Handshake send error: {exc}")
            return False

    def handle_handshake_response(self, message: str) -> None:
        """
        Process server response to handshake.

        Args:
            message: Raw message from server
        """
        try:
            data = json.loads(message)
            if data.get("action") == "handshake_ack" or data.get("action") == "handshake_response":
                self.logger.log(f"Handshake acknowledged by server: {message}")
                self.handshake_acknowledged = True
                if self.on_handshake_response:
                    self.on_handshake_response(data)
        except json.JSONDecodeError:
            pass

    def reset_for_new_connection(self) -> None:
        """Reset handshake state for a new connection."""
        self.handshake_sent = False
        self.handshake_acknowledged = False

    def update_config(self, **kwargs) -> None:
        """
        Update handshake configuration fields.

        Args:
            **kwargs: Configuration fields to update (client_id, token, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
