import asyncio
import json
import threading
import time

import websockets

from ws_client import WebSocketManager


class MockLogger:
    def __init__(self):
        self.messages = []

    def log(self, message: str) -> None:
        self.messages.append(message)


async def ws_server_handler(websocket, path):
    try:
        msg = await websocket.recv()
        # respond with handshake response
        resp = {"type": "handshake_response", "status": "ok", "token": "server-secret-xyz"}
        await websocket.send(json.dumps(resp))
    except Exception:
        pass


def start_server(loop, stop_event):
    async def run():
        async with websockets.serve(ws_server_handler, "localhost", 8765):
            await stop_event.wait()

    loop.run_until_complete(run())


def test_end_to_end_handshake(tmp_path):
    # start server in background loop
    loop = asyncio.new_event_loop()
    stop_event = asyncio.Event()

    def server_thread():
        asyncio.set_event_loop(loop)
        loop.run_until_complete(websockets.serve(ws_server_handler, "localhost", 8765))
        loop.run_forever()

    t = threading.Thread(target=server_thread, daemon=True)
    t.start()
    time.sleep(0.2)

    logger = MockLogger()
    wm = WebSocketManager(logger=logger, runtime_config={"handshake.clientId": "int-client", "handshake.token": "clienttok1234", "handshake.autoSend": True, "handshake.applyResponseToState": True})

    try:
        wm.connect("ws://localhost:8765")
        # wait for connection and handshake exchange
        time.sleep(1.0)

        # check logs for outgoing and incoming
        outs = " ".join(logger.messages)
        assert "Outgoing" in outs or "Sent WebSocket message" in outs
        assert "Incoming" in outs or "WebSocket received" in outs

        # connection_state updated
        assert "handshakeResponse" in wm.connection_state
        assert wm.connection_state["handshakeResponse"]["status"] == "ok"
    finally:
        wm.disconnect()
        # stop server
        loop.call_soon_threadsafe(loop.stop)
