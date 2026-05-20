import os
from datetime import datetime


DEFAULT_COMMANDS = [
    {
        "name": "Handshake",
        "payload": {
            "type": "handshake",
            "clientId": os.getenv("IOT_CLIENT_ID", "iot-device-simulator"),
            "version": "1.0",
            "token": os.getenv("IOT_AUTH_TOKEN", ""),
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


def validate_handshake_payload(payload: dict) -> tuple[bool, str]:
    """
    Validate handshake message structure.
    
    Args:
        payload: Payload dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(payload, dict):
        return False, "Handshake payload must be a dictionary"
    
    if "type" not in payload:
        return False, "Handshake payload missing required field: 'type'"
    
    if payload.get("type") != "handshake":
        return False, "Handshake 'type' field must be 'handshake'"
    
    if "clientId" not in payload:
        return False, "Handshake payload missing required field: 'clientId'"
    
    if "version" not in payload:
        return False, "Handshake payload missing required field: 'version'"
    
    return True, ""


def is_handshake_message(payload: dict) -> bool:
    """
    Check if a message is a handshake message.
    
    Args:
        payload: Message payload to check
        
    Returns:
        True if message type is 'handshake', False otherwise
    """
    try:
        return isinstance(payload, dict) and payload.get("type") == "handshake"
    except (TypeError, AttributeError):
        return False


class AppLogger:
    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
