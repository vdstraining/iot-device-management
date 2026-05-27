from datetime import datetime
import uuid


def generate_handshake(
    client_id: str = None,
    version: str = "1.0",
    capabilities: list = None,
    metadata: dict = None
) -> dict:
    """
    Generate a handshake message to establish client-server communication.
    
    Args:
        client_id: Unique client identifier (auto-generated if not provided)
        version: Protocol version (default: "1.0")
        capabilities: List of supported features (default: basic list)
        metadata: Optional context/session metadata
        
    Returns:
        Dictionary containing handshake payload
    """
    if client_id is None:
        client_id = str(uuid.uuid4())
    
    if capabilities is None:
        capabilities = ["websocket", "json", "ping", "echo"]
    
    if metadata is None:
        metadata = {}
    
    return {
        "action": "handshake",
        "type": "client-init",
        "clientId": client_id,
        "version": version,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "capabilities": capabilities,
        "metadata": metadata,
    }


DEFAULT_COMMANDS = [
    {
        "name": "Handshake",
        "payload": {
            "action": "handshake",
            "type": "client-init",
            "clientId": "client-" + str(uuid.uuid4())[:8],
            "version": "1.0",
            "timestamp": "2026-03-27T12:00:00Z",
            "capabilities": ["websocket", "json", "ping", "echo"],
            "metadata": {},
        },
    },
    {
        "name": "Ping",
        "payload": {
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z",
        },
    },
    {
        "name": "Login",
        "payload": {
            "action": "login",
            "username": "demo_user",
            "token": "replace-me",
        },
    },
    {
        "name": "Subscribe",
        "payload": {
            "action": "subscribe",
            "channel": "events",
        },
    },
    {
        "name": "Echo",
        "payload": {
            "action": "echo",
            "message": "hello from tkinter client",
        },
    },
    {
        "name": "HTTP POST sample",
        "payload": {
            "method": "POST",
            "path": "/api/commands",
            "headers": {
                "Content-Type": "application/json",
            },
            "body": {
                "action": "status",
            },
            "timeout": 10,
        },
    },
]


class AppLogger:
    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
