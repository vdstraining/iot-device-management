import json
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS


class FakeLogger:
    def __init__(self):
        self.messages = []

    def log(self, msg):
        self.messages.append(msg)

    def has_message(self, substr):
        return any(substr in m for m in self.messages)


def make_manager(payload=None, on_message=None):
    logger = FakeLogger()
    mgr = WebSocketManager(logger=logger, handshake_payload=payload, on_message=on_message)
    mgr.connected = True
    mgr.ws_app = MagicMock()
    return mgr, logger


class TestSendHandshake(unittest.TestCase):
    def test_happy_path(self):
        payload = {"action": "handshake", "clientId": "test-client", "capabilities": []}
        mgr, logger = make_manager(payload=payload)
        mgr.send_handshake()
        mgr.ws_app.send.assert_called_once()
        sent = json.loads(mgr.ws_app.send.call_args[0][0])
        self.assertEqual(sent["action"], "handshake")
        self.assertEqual(sent["clientId"], "test-client")

    def test_missing_clientId(self):
        mgr, logger = make_manager(payload={"action": "handshake"})
        mgr.send_handshake()
        mgr.ws_app.send.assert_not_called()
        self.assertTrue(logger.has_message("clientId"))

    def test_missing_action(self):
        mgr, logger = make_manager(payload={"clientId": "test-client"})
        mgr.send_handshake()
        mgr.ws_app.send.assert_not_called()
        self.assertTrue(logger.has_message("action"))

    def test_no_payload(self):
        mgr, logger = make_manager(payload=None)
        mgr.send_handshake()
        mgr.ws_app.send.assert_not_called()
        self.assertEqual(logger.messages, [])


class TestOnOpen(unittest.TestCase):
    def test_on_open_triggers_handshake(self):
        payload = {"action": "handshake", "clientId": "test-client"}
        mgr, logger = make_manager(payload=payload)
        mgr.connected = False
        with patch.object(mgr, "send_handshake") as mock_hs:
            mgr._on_open(None)
            mock_hs.assert_called_once()

    def test_on_open_sets_connected(self):
        mgr, _ = make_manager()
        mgr.connected = False
        mgr._on_open(None)
        self.assertTrue(mgr.connected)


class TestOnMessage(unittest.TestCase):
    def test_handshake_ack_logged(self):
        received = []
        mgr, logger = make_manager(on_message=received.append)
        mgr._on_message(None, json.dumps({"action": "handshakeAck"}))
        self.assertTrue(logger.has_message("handshake acknowledged"))
        self.assertEqual(len(received), 1)

    def test_non_ack_not_logged_as_ack(self):
        received = []
        mgr, logger = make_manager(on_message=received.append)
        mgr._on_message(None, json.dumps({"action": "ping"}))
        self.assertFalse(logger.has_message("handshake acknowledged"))
        self.assertEqual(len(received), 1)

    def test_invalid_json_no_crash(self):
        received = []
        mgr, logger = make_manager(on_message=received.append)
        mgr._on_message(None, "not-json")
        self.assertEqual(len(received), 1)
        self.assertFalse(logger.has_message("handshake acknowledged"))


class TestDefaultCommandsHandshake(unittest.TestCase):
    def test_handshake_entry_exists(self):
        entries = [c for c in DEFAULT_COMMANDS if c["name"] == "Handshake"]
        self.assertEqual(len(entries), 1)

    def test_handshake_payload_fields(self):
        entry = next(c for c in DEFAULT_COMMANDS if c["name"] == "Handshake")
        self.assertEqual(entry["payload"]["action"], "handshake")
        self.assertEqual(entry["payload"]["clientId"], "iot-device-simulator")

    def test_handshake_order_after_subscribe(self):
        names = [c["name"] for c in DEFAULT_COMMANDS]
        subscribe_idx = names.index("Subscribe")
        handshake_idx = names.index("Handshake")
        self.assertGreater(handshake_idx, subscribe_idx)


if __name__ == "__main__":
    unittest.main()
