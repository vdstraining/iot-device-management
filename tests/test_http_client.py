from unittest.mock import Mock
from http_client import HttpClient

class DummyLogger:
    def __init__(self):
        self.logs = []
    def log(self, msg):
        self.logs.append(msg)


def test_send_request_empty_baseurl_logs():
    logger = DummyLogger()
    client = HttpClient(logger)
    client.send_request("", {"method": "GET"})
    assert any("HTTP Base URL is empty." in m for m in logger.logs)


def test_send_request_runs_requests(monkeypatch):
    logger = DummyLogger()
    client = HttpClient(logger)

    fake_response = Mock()
    fake_response.text = "response body"
    fake_response.status_code = 200
    fake_response.reason = "OK"

    def fake_request(method, url, headers=None, json=None, timeout=None):
        return fake_response

    monkeypatch.setattr('http_client.requests.request', fake_request)

    class SyncThread:
        def __init__(self, target, daemon=True):
            self._target = target
        def start(self):
            self._target()

    monkeypatch.setattr('http_client.threading.Thread', SyncThread)

    client.send_request("http://example.com", {"method": "POST", "path": "/api", "body": {"a": 1}})

    assert any("Sending HTTP request" in m for m in logger.logs)
    assert any("HTTP response: status=200" in m for m in logger.logs)
