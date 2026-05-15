import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

mock_tk = types.ModuleType("tkinter")
mock_tk.TclError = Exception
mock_tk.END = "end"
mock_tk.Tk = lambda *args, **kwargs: None
mock_tk.StringVar = lambda *args, **kwargs: types.SimpleNamespace(get=lambda: "", set=lambda value: None)
mock_tk.IntVar = lambda *args, **kwargs: types.SimpleNamespace(get=lambda: 0, set=lambda value: None)
sys.modules["tkinter"] = mock_tk
mock_ttk = types.ModuleType("tkinter.ttk")
mock_ttk.Style = lambda *args, **kwargs: None
mock_ttk.Label = lambda *args, **kwargs: None
mock_ttk.LabelFrame = lambda *args, **kwargs: None
mock_ttk.Entry = lambda *args, **kwargs: None
mock_ttk.Button = lambda *args, **kwargs: None
mock_ttk.Checkbutton = lambda *args, **kwargs: None
sys.modules["tkinter.ttk"] = mock_ttk
mock_scrolled = types.ModuleType("tkinter.scrolledtext")
mock_scrolled.ScrolledText = lambda *args, **kwargs: None
sys.modules["tkinter.scrolledtext"] = mock_scrolled
mock_ws = types.ModuleType("websocket")
mock_ws.WebSocketApp = lambda *args, **kwargs: None
sys.modules["websocket"] = mock_ws

import unittest
from types import SimpleNamespace

from utilities import DEFAULT_COMMANDS
from ui import AppUI


class TestHandshakeFeature(unittest.TestCase):
    def test_default_commands_include_handshake(self):
        handshake_commands = [cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake"]
        self.assertEqual(len(handshake_commands), 1)
        payload = handshake_commands[0]["payload"]
        self.assertEqual(payload["action"], "handshake")
        self.assertIn("clientId", payload)
        self.assertIn("token", payload)
        self.assertIn("capabilities", payload)

    def test_build_handshake_payload_uses_ws_url_for_client_id(self):
        dummy = SimpleNamespace(ws_url_var=SimpleNamespace(get=lambda: "ws://example.com/device"))
        payload = AppUI._build_handshake_payload(dummy)
        self.assertEqual(payload["clientId"], "example.com")
        self.assertEqual(payload["action"], "handshake")
        self.assertIn("capabilities", payload)

    def test_send_handshake_calls_send_json_and_marks_sent(self):
        sent = []
        logs = []
        dummy = SimpleNamespace(
            ws_connected=True,
            handshake_sent=False,
            handshake_completed=False,
            ws_manager=SimpleNamespace(send_json=lambda payload: sent.append(payload)),
            logger=SimpleNamespace(log=lambda message: logs.append(message)),
            ws_url_var=SimpleNamespace(get=lambda: "ws://example.com/device"),
        )
        dummy._build_handshake_payload = lambda: {
            "action": "handshake",
            "clientId": "example.com",
            "token": "replace-me",
            "capabilities": ["telemetry", "status", "commands"],
            "sessionMeta": {
                "source": "simulator",
                "websocketUrl": "ws://example.com/device",
            },
        }
        AppUI._send_handshake(dummy)
        self.assertTrue(dummy.handshake_sent)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["action"], "handshake")
        self.assertTrue(any("Sending handshake message." in msg for msg in logs))

    def test_handle_ws_status_change_triggers_handshake_on_connect(self):
        sent = []
        dummy = SimpleNamespace(
            ws_connected=False,
            handshake_sent=False,
            handshake_completed=False,
            root=SimpleNamespace(after=lambda delay, func: func()),
            ws_manager=SimpleNamespace(send_json=lambda payload: sent.append(payload)),
            logger=SimpleNamespace(log=lambda message: None),
            ws_url_var=SimpleNamespace(get=lambda: "ws://example.com/device"),
        )
        dummy._send_handshake = lambda: (sent.append({"action": "handshake"}), setattr(dummy, "handshake_sent", True))
        AppUI._handle_ws_status_change(dummy, True)
        self.assertTrue(dummy.ws_connected)
        self.assertTrue(dummy.handshake_sent)
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]["action"], "handshake")

    def test_handle_ws_status_change_resets_on_disconnect(self):
        dummy = SimpleNamespace(
            ws_connected=True,
            handshake_sent=True,
            handshake_completed=True,
            root=SimpleNamespace(after=lambda delay, func: None),
            ws_manager=SimpleNamespace(send_json=lambda payload: None),
            logger=SimpleNamespace(log=lambda message: None),
            ws_url_var=SimpleNamespace(get=lambda: "ws://example.com/device"),
        )
        AppUI._handle_ws_status_change(dummy, False)
        self.assertFalse(dummy.ws_connected)
        self.assertFalse(dummy.handshake_sent)
        self.assertFalse(dummy.handshake_completed)


if __name__ == "__main__":
    unittest.main()


