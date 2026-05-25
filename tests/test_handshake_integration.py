import json
import time

from ws_client import WebSocketManager


class MockLogger:
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)


class FakeWSApp:
    def __init__(self, manager: WebSocketManager):
        self.manager = manager

    def send(self, raw_payload: str) -> None:
        # simulate server receiving handshake and responding
        try:
            parsed = json.loads(raw_payload)
        except Exception:
            return
        if parsed.get("type") == "handshake":
            resp = {"type": "handshake_response", "status": "ok", "token": "server-secret-xyz"}
            # call manager message handler
            self.manager._on_message(None, json.dumps(resp))


def test_end_to_end_handshake_simulated():
    logger = MockLogger()
    wm = WebSocketManager(logger=logger, runtime_config={"handshake.clientId": "int-client", "handshake.token": "clienttok1234", "handshake.autoSend": False, "handshake.applyResponseToState": True})
    fake = FakeWSApp(wm)
    wm.ws_app = fake
    wm.connected = True

    # trigger manual handshake send
    wm.send_handshake()
    time.sleep(0.05)

    outs = " ".join(logger.messages)
    assert "Outgoing" in outs or "Sent WebSocket message" in outs
    assert "Incoming" in outs or "WebSocket received" in outs
    assert "handshakeResponse" in wm.connection_state
    assert wm.connection_state["handshakeResponse"]["status"] == "ok"
