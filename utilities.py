from datetime import datetime


DEFAULT_COMMANDS = [
    {
        "name": "Handshake",
        "payload": {
            "action": "handshake",
            "clientId": "client-001",
            "token": "auth-token-here",
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


def validate_handshake(payload: dict) -> bool:
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
