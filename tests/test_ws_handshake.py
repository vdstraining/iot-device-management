import json
import unittest

from utilities import DEFAULT_COMMANDS, AppLogger
from ws_client import WebSocketManager


class DummyWsApp:
    def __init__(self):
        self.sent_messages = []

    def send(self, message: str) -> None:
        self.sent_messages.append(message)


class DummyLogger(AppLogger):
    def __init__(self):
        self.messages = []
        super().__init__(self._capture)

    def _capture(self, message: str) -> None:
        self.messages.append(message)


class TestWebSocketHandshake(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = DummyLogger()
        self.ws = WebSocketManager(logger=self.logger)
        self.ws.ws_app = DummyWsApp()

    def test_default_commands_includes_handshake(self) -> None:
        names = [item["name"] for item in DEFAULT_COMMANDS]
        self.assertIn("Handshake", names)

    def test_send_handshake_requires_connection(self) -> None:
        self.ws.connected = False
        self.ws.send_handshake({"action": "handshake"})
        self.assertTrue(any("not connected" in msg for msg in self.logger.messages))

    def test_send_handshake_requires_dict_payload(self) -> None:
        self.ws.connected = True
        self.ws.send_handshake("not-a-dict")  # type: ignore[arg-type]
        self.assertTrue(any("must be a JSON object" in msg for msg in self.logger.messages))

    def test_send_handshake_requires_action_handshake(self) -> None:
        self.ws.connected = True
        self.ws.send_handshake({"action": "ping"})
        self.assertTrue(any("must include action: handshake" in msg for msg in self.logger.messages))

    def test_send_handshake_sends_valid_payload(self) -> None:
        self.ws.connected = True
        payload = {"action": "handshake", "clientId": "test", "token": "abc"}
        self.ws.send_handshake(payload)
        self.assertEqual(len(self.ws.ws_app.sent_messages), 1)
        sent = json.loads(self.ws.ws_app.sent_messages[0])
        self.assertEqual(sent, payload)
        self.assertTrue(any("Sent handshake message" in msg for msg in self.logger.messages))


if __name__ == "__main__":
    unittest.main()
