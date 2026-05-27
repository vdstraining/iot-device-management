import json
import unittest
from unittest.mock import MagicMock

from utilities import DEFAULT_COMMANDS
from ws_client import WebSocketManager


class DummyLogger:
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)


class HandshakeTests(unittest.TestCase):
    def test_default_commands_include_handshake(self):
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd.get("name") == "Handshake"]
        self.assertEqual(len(handshake_commands), 1)
        self.assertIsInstance(handshake_commands[0]["payload"], dict)
        self.assertEqual(handshake_commands[0]["payload"].get("action"), "handshake")

    def test_ws_manager_send_json_sends_when_connected(self):
        logger = DummyLogger()
        manager = WebSocketManager(logger=logger)
        manager.ws_app = MagicMock()
        manager.connected = True

        payload = {"action": "handshake", "client_id": "iot-simulator-001"}
        manager.send_json(payload)

        manager.ws_app.send.assert_called_once_with(json.dumps(payload))
        self.assertTrue(any("Sent WebSocket message" in msg for msg in logger.messages))

    def test_ws_manager_send_json_logs_when_not_connected(self):
        logger = DummyLogger()
        manager = WebSocketManager(logger=logger)
        manager.ws_app = None
        manager.connected = False

        manager.send_json({"action": "handshake"})

        self.assertTrue(any("not connected" in msg.lower() for msg in logger.messages))


if __name__ == "__main__":
    unittest.main()
