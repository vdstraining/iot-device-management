import unittest

from ws_client import WebSocketManager


class DummyLogger:
    def __init__(self):
        self.messages = []

    def log(self, message):
        self.messages.append(message)


class DummyWebSocket:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


class TestWebSocketManager(unittest.TestCase):
    def test_send_json_logs_when_not_connected(self):
        logger = DummyLogger()
        manager = WebSocketManager(logger=logger)
        manager.send_json({"action": "handshake"})

        self.assertIn("Cannot send via WebSocket: not connected.", logger.messages[-1])

    def test_send_json_sends_serialized_payload_when_connected(self):
        logger = DummyLogger()
        manager = WebSocketManager(logger=logger)
        manager.ws_app = DummyWebSocket()
        manager.connected = True

        manager.send_json({"action": "handshake"})

        self.assertEqual(manager.ws_app.sent, ["{\"action\": \"handshake\"}"])
        self.assertIn("Sent WebSocket message:", logger.messages[-1])


if __name__ == "__main__":
    unittest.main()
