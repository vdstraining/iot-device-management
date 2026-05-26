from datetime import datetime
from enum import Enum


# Handshake Message Types
MESSAGE_TYPE_HANDSHAKE_INIT = "HANDSHAKE_INIT"
MESSAGE_TYPE_HANDSHAKE_ACK = "HANDSHAKE_ACK"
MESSAGE_TYPE_HANDSHAKE_ERROR = "HANDSHAKE_ERROR"

# Handshake States
HANDSHAKE_STATE_PENDING = "PENDING"
HANDSHAKE_STATE_COMPLETED = "COMPLETED"
HANDSHAKE_STATE_FAILED = "FAILED"

# Protocol version
PROTOCOL_VERSION = "1.0"
DEFAULT_HANDSHAKE_TIMEOUT = 30  # seconds


def create_handshake_init(device_id: str, capabilities: list = None, auth_token: str = None) -> dict:
    """Create a HANDSHAKE_INIT message."""
    if capabilities is None:
        capabilities = ["websocket", "json"]
    
    return {
        "type": MESSAGE_TYPE_HANDSHAKE_INIT,
        "protocol_version": PROTOCOL_VERSION,
        "device_id": device_id,
        "capabilities": capabilities,
        "auth_token": auth_token,
        "timestamp": datetime.now().isoformat(),
    }


def create_handshake_ack(status: str, protocol_version: str = None, server_info: dict = None) -> dict:
    """Create a HANDSHAKE_ACK message (server response)."""
    return {
        "type": MESSAGE_TYPE_HANDSHAKE_ACK,
        "status": status,
        "protocol_version": protocol_version or PROTOCOL_VERSION,
        "server_info": server_info or {},
        "timestamp": datetime.now().isoformat(),
    }


def create_handshake_error(error_code: str, error_message: str) -> dict:
    """Create a HANDSHAKE_ERROR message."""
    return {
        "type": MESSAGE_TYPE_HANDSHAKE_ERROR,
        "error_code": error_code,
        "error_message": error_message,
        "timestamp": datetime.now().isoformat(),
    }


DEFAULT_COMMANDS = [
    {
        "name": "HANDSHAKE_INIT",
        "payload": {
            "type": "HANDSHAKE_INIT",
            "protocol_version": "1.0",
            "device_id": "device-001",
            "capabilities": ["websocket", "json"],
            "auth_token": "replace-me",
            "timestamp": "2026-03-27T12:00:00Z",
        },
    },
    {
        "name": "HANDSHAKE_ACK",
        "payload": {
            "type": "HANDSHAKE_ACK",
            "status": "success",
            "protocol_version": "1.0",
            "server_info": {
                "version": "1.0.0",
                "capabilities": ["websocket", "json", "binary"],
            },
            "timestamp": "2026-03-27T12:00:00Z",
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
