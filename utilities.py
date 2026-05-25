import json
import os
from datetime import datetime


DEFAULT_COMMANDS = [
    {
        "name": "Handshake",
        "payload": {
            "action": "handshake",
            "clientId": "iot-device-simulator-001",
            "capabilities": [
                "websocket",
                "http",
                "json-messaging",
                "command-execution",
            ],
            "session_metadata": {
                "version": "1.0",
                "application": "IoT Device Simulator",
                "platform": "Tkinter",
            },
            "authentication_context": {
                "auth_type": "bearer",
                "token": "",
            },
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


def load_handshake_config(config_file: str = "handshake_config.json") -> dict:
    """
    Load handshake configuration from JSON file.
    
    Args:
        config_file: Path to the handshake configuration file
        
    Returns:
        Dictionary containing handshake configuration, or defaults if file not found
    """
    default_config = {
        "enabled": True,
        "auto_trigger": True,
        "clientId": "iot-device-simulator-001",
        "capabilities": [
            "websocket",
            "http",
            "json-messaging",
            "command-execution",
        ],
        "session_metadata": {
            "version": "1.0",
            "application": "IoT Device Simulator",
            "platform": "Tkinter",
        },
        "authentication_context": {
            "auth_type": "bearer",
            "token": "",
        },
    }
    
    if not os.path.exists(config_file):
        return default_config
    
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        # Merge with defaults to ensure all required keys exist
        return {**default_config, **config}
    except Exception:
        return default_config


class AppLogger:

    def __init__(self, callback) -> None:
        self.callback = callback

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.callback(f"[{timestamp}] {message}\n")
