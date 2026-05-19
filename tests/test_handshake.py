import unittest
from unittest.mock import Mock

from utilities import DEFAULT_COMMANDS
from ui import build_handshake_payload
from ws_client import WebSocketManager


class DummyLogger:
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)


class TestHandshake(unittest.TestCase):
    def test_default_commands_includes_handshake(self):
        self.assertTrue(
            any(
                cmd["name"] == "Handshake" and cmd["payload"].get("action") == "handshake"
                for cmd in DEFAULT_COMMANDS
            )
        )

    def test_build_handshake_payload_valid(self):
        logger = DummyLogger()
        payload = build_handshake_payload("test-client", "secret-token", logger=logger)

        self.assertEqual(
            payload,
            {
                "action": "handshake",
                "clientId": "test-client",
                "token": "secret-token",
            },
        )
        self.assertTrue(any("Prepared handshake payload" in message for message in logger.messages))

    def test_build_handshake_payload_invalid(self):
        logger = DummyLogger()
        payload = build_handshake_payload("", "", logger=logger)

        self.assertIsNone(payload)
        self.assertTrue(any("Handshake validation failed" in message for message in logger.messages))

    def test_ws_manager_send_json_logs_description(self):
        logger = DummyLogger()
        ws = WebSocketManager(logger=logger)
        ws.ws_app = Mock()
        ws.connected = True

        ws.send_json({"action": "handshake"}, description="handshake")

        self.assertTrue(any("Sent WebSocket handshake:" in message for message in logger.messages))

    def test_ws_manager_on_open_invokes_callback(self):
        logger = DummyLogger()
        ws = WebSocketManager(logger=logger, on_open=lambda: logger.log("open called"))

        ws._on_open(Mock())

        self.assertTrue(any("open called" in message for message in logger.messages))


if __name__ == "__main__":
    unittest.main()
