import json
from typing import Optional, List


class HandshakeManager:
    """Manages handshake message creation, validation, and payload generation."""

    def __init__(
        self,
        logger,
        client_id: str = "client-001",
        version: str = "1.0",
        capabilities: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize HandshakeManager.

        Args:
            logger: AppLogger instance for logging
            client_id: Client identifier
            version: Client version
            capabilities: List of supported capabilities
        """
        self.logger = logger
        self.client_id = client_id
        self.version = version
        self.capabilities = capabilities or ["ping", "subscribe", "echo"]
        self.token: Optional[str] = None
        self.metadata: dict = {"platform": "tkinter"}

    def set_client_id(self, client_id: str) -> None:
        """Set the client ID."""
        self.client_id = client_id

    def set_version(self, version: str) -> None:
        """Set the client version."""
        self.version = version

    def set_token(self, token: Optional[str]) -> None:
        """Set the authentication token."""
        self.token = token

    def set_capabilities(self, capabilities: List[str]) -> None:
        """Set the list of capabilities."""
        self.capabilities = capabilities

    def set_metadata(self, metadata: dict) -> None:
        """Set additional metadata."""
        self.metadata = metadata

    def validate(self) -> bool:
        """
        Validate handshake payload structure.

        Returns:
            True if payload is valid, False otherwise
        """
        if not self.client_id:
            self.logger.log("Handshake validation failed: client_id is required.")
            return False

        if not self.version:
            self.logger.log("Handshake validation failed: version is required.")
            return False

        if not isinstance(self.capabilities, list) or len(self.capabilities) == 0:
            self.logger.log("Handshake validation failed: capabilities must be a non-empty list.")
            return False

        return True

    def get_payload(self) -> Optional[dict]:
        """
        Get the formatted handshake payload.

        Returns:
            Handshake payload dict if valid, None otherwise
        """
        if not self.validate():
            return None

        payload = {
            "action": "handshake",
            "clientId": self.client_id,
            "version": self.version,
            "capabilities": self.capabilities,
            "token": self.token,
            "metadata": self.metadata,
        }

        return payload

    @staticmethod
    def build_payload_template() -> dict:
        """
        Get a template for handshake payload.

        Returns:
            Handshake payload template
        """
        return {
            "action": "handshake",
            "clientId": "client-001",
            "version": "1.0",
            "capabilities": ["ping", "subscribe", "echo"],
            "token": None,
            "metadata": {"platform": "tkinter"},
        }
