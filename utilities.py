import os
from datetime import datetime


def get_handshake_payload():
    """Generate handshake payload with dynamic fields from environment variables."""
    client_id = os.getenv("IOT_CLIENT_ID", "iot-device-client")
    token = os.getenv("IOT_CLIENT_TOKEN", "demo-token")
    timestamp = datetime.now().isoformat() + "Z"
    return {
        "action": "handshake",
        "clientId": client_id,
        "token": token,
        "timestamp": timestamp,
    }


DEFAULT_COMMANDS = [
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
    {
        "name": "Handshake",
        "payload": None,  # Dynamically populated by get_handshake_payload()
    },
]


class AppLogger:
    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
