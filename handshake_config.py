"""
Handshake configuration and builder for WebSocket initial communication.
Supports dynamic field configuration for client identification and authentication.
"""

import uuid
from datetime import datetime
from typing import Optional


class HandshakeConfig:
    """Configuration for handshake message fields."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        token: Optional[str] = None,
        client_version: str = "1.0.0",
        protocol_version: str = "1.0",
    ) -> None:
        """
        Initialize handshake configuration.

        Args:
            client_id: Unique identifier for the client (auto-generated if None)
            token: Authentication token or session identifier
            client_version: Version of the client application
            protocol_version: Protocol version for compatibility
        """
        self.client_id = client_id if client_id is not None else str(uuid.uuid4())
        self.token = token if token is not None else ""
        self.client_version = client_version
        self.protocol_version = protocol_version

    def build_handshake_payload(self) -> dict:
        """
        Build the handshake message payload.

        Returns:
            Dictionary containing handshake message with action, clientId, and other metadata
        """
        return {
            "action": "handshake",
            "clientId": self.client_id,
            "token": self.token,
            "clientVersion": self.client_version,
            "protocolVersion": self.protocol_version,
            "timestamp": datetime.now().isoformat() + "Z",
        }

    def validate(self) -> tuple[bool, str]:
        """
        Validate handshake configuration.

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if configuration is valid
            - error_message: Empty string if valid, error description otherwise
        """
        if not self.client_id or not isinstance(self.client_id, str) or self.client_id.strip() == "":
            return False, "clientId must be a non-empty string"

        if not isinstance(self.client_version, str) or not self.client_version or self.client_version.strip() == "":
            return False, "clientVersion must be a non-empty string"

        if not isinstance(self.protocol_version, str) or not self.protocol_version or self.protocol_version.strip() == "":
            return False, "protocolVersion must be a non-empty string"

        return True, ""


# Default handshake configuration
DEFAULT_HANDSHAKE_CONFIG = HandshakeConfig()
