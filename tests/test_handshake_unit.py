import time
import json

from ws_client import WebSocketManager


class DummyWSApp:
    def __init__(self):
        self.sent = []

    def send(self, raw):
        self.sent.append(raw)


class MockLogger:
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        # strip timestamp for easier assertions
        self.messages.append(message)


def test_send_handshake_auto_and_masking():
    logger = MockLogger()
    dummy = DummyWSApp()
    wm = WebSocketManager(logger=logger, runtime_config={"handshake.clientId": "abc123", "handshake.token": "secrettoken123", "handshake.autoSend": False})
    wm.ws_app = dummy
    wm.connected = True

    wm.send_handshake()

    # ensure message sent
    assert len(dummy.sent) == 1
    sent_obj = json.loads(dummy.sent[0])
    assert sent_obj["type"] == "handshake"
    assert sent_obj["clientId"] == "abc123"
    assert sent_obj["token"] == "secrettoken123"

    # ensure masking in logger
    assert any("secr***" in m or "secr***" in m for m in logger.messages)


def test_send_handshake_validation_failure():
    logger = MockLogger()
    dummy = DummyWSApp()
    # invalid clientId type (int)
    wm = WebSocketManager(logger=logger, runtime_config={"handshake.clientId": 123, "handshake.autoSend": False})
    wm.ws_app = dummy
    wm.connected = True

    wm.send_handshake()

    # no message sent due to validation
    assert len(dummy.sent) == 0
    assert any("Handshake validation failed" in m for m in logger.messages)
