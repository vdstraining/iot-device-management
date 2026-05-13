from unittest.mock import Mock
from ws_client import WebSocketManager

class DummyLogger:
    def __init__(self):
        self.logs = []
    def log(self, msg):
        self.logs.append(msg)


def test_connect_empty_url_logs():
    logger = DummyLogger()
    manager = WebSocketManager(logger)
    manager.connect("")
    assert any("WebSocket URL is empty." in m for m in logger.logs)


def test_on_open_and_message_and_send(monkeypatch):
    logger = DummyLogger()
    messages = []
    status = []
    manager = WebSocketManager(logger, on_message=lambda m: messages.append(m), on_status_change=lambda s: status.append(s))

    class FakeWSApp:
        def __init__(self, url, on_open, on_message, on_error, on_close):
            self.url = url
            self._on_open = on_open
            self._on_message = on_message
            self._on_error = on_error
            self._on_close = on_close
            self.sent = []
        def run_forever(self):
            self._on_open(self)
            self._on_message(self, "hello")
            self._on_close(self, 1000, "normal")
        def send(self, data):
            self.sent.append(data)
        def close(self):
            pass

    monkeypatch.setattr('ws_client.WebSocketApp', FakeWSApp)

    class SyncThread:
        def __init__(self, target, daemon=True):
            self._target = target
        def start(self):
            self._target()

    monkeypatch.setattr('ws_client.threading.Thread', SyncThread)

    manager.connect("ws://example.com")

    assert status[0] is True
    assert messages == ["hello"]

    manager.send_json({"a": 1})
    assert any("Cannot send via WebSocket" in m for m in logger.logs)
