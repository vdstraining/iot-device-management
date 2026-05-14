from datetime import datetime


def build_handshake_payload(
    client_id: str,
    token: str,
    capabilities: str,
    session_id: str,
) -> dict:
    return {
        "action": "handshake",
        "clientId": client_id or "client-001",
        "capabilities": [item.strip() for item in capabilities.split(",") if item.strip()] or ["ping", "subscribe"],
        "metadata": {
            "sessionId": session_id or "session-001",
        },
        "auth": {
            "token": token or "replace-me",
        },
    }


def validate_handshake_payload(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("action") != "handshake":
        return False
    if not payload.get("clientId"):
        return False
    if not payload.get("auth") or not payload["auth"].get("token"):
        return False
    if not isinstance(payload.get("capabilities"), list):
        return False
    return True


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
        "name": "Handshake",
        "payload": build_handshake_payload(
            client_id="demo_client",
            token="replace-me",
            capabilities="ping,subscribe",
            session_id="demo_session",
        ),
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
