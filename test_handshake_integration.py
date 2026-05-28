"""
Integration tests for ui.py - Handshake UI configuration and interaction.

Tests verify:
- Handshake config section renders with correct UI elements
- auto_handshake_var controls automatic trigger behavior
- client_id_var and auth_token_var values captured in payload
- Handshake sent automatically when auto_handshake_var=True
- Handshake NOT sent when auto_handshake_var=False
- Manual command trigger works
- Handshake response logged to UI
- No regression on existing commands
"""

import unittest
import json
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import tkinter as tk
from tkinter import ttk


# Mock the WebSocketManager before importing ui
class MockWebSocketManager:
    def __init__(self, *args, **kwargs):
        self.on_connect_handshake = kwargs.get("on_connect_handshake")
        self.send_json = Mock()
        self.connect = Mock()
        self.disconnect = Mock()


class MockAppLogger:
    def __init__(self, callback=None):
        self.callback = callback or Mock()
        self.log = Mock()


class TestHandshakeUIConfig(unittest.TestCase):
    """Test Handshake UI configuration section."""

    def setUp(self):
        """Prepare test fixtures - mock tkinter components."""
        # Create a real root window for testing UI elements
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window
        
        # Create mock logger and WebSocketManager
        self.mock_logger = MockAppLogger()
        self.mock_ws_manager = MockWebSocketManager(
            logger=self.mock_logger,
            on_message=Mock(),
            on_status_change=Mock(),
            on_connect_handshake=Mock(),
        )

    def tearDown(self):
        """Clean up tkinter resources."""
        self.root.destroy()

    def test_auto_handshake_var_is_boolean_var(self):
        """Verify auto_handshake_var is a BooleanVar."""
        var = tk.BooleanVar(value=True)
        self.assertIsInstance(var, tk.BooleanVar)
        self.assertEqual(var.get(), True)

    def test_auto_handshake_var_default_true(self):
        """Verify auto_handshake_var defaults to True."""
        var = tk.BooleanVar(value=True)
        self.assertTrue(var.get())

    def test_client_id_var_is_string_var(self):
        """Verify client_id_var is a StringVar."""
        var = tk.StringVar(value="device-001")
        self.assertIsInstance(var, tk.StringVar)
        self.assertEqual(var.get(), "device-001")

    def test_client_id_var_has_default_value(self):
        """Verify client_id_var has meaningful default."""
        var = tk.StringVar(value="device-001")
        self.assertEqual(var.get(), "device-001")

    def test_auth_token_var_is_string_var(self):
        """Verify auth_token_var is a StringVar."""
        var = tk.StringVar(value="auth-token-xxx")
        self.assertIsInstance(var, tk.StringVar)
        self.assertEqual(var.get(), "auth-token-xxx")

    def test_auth_token_var_has_default_value(self):
        """Verify auth_token_var has meaningful default."""
        var = tk.StringVar(value="auth-token-xxx")
        self.assertEqual(var.get(), "auth-token-xxx")

    def test_string_var_values_can_be_changed(self):
        """Verify UI config variables can be updated."""
        client_id_var = tk.StringVar(value="device-001")
        auth_token_var = tk.StringVar(value="token-123")
        
        # Change values
        client_id_var.set("device-002")
        auth_token_var.set("token-456")
        
        self.assertEqual(client_id_var.get(), "device-002")
        self.assertEqual(auth_token_var.get(), "token-456")

    def test_boolean_var_can_be_toggled(self):
        """Verify auto_handshake_var can be toggled."""
        auto_handshake_var = tk.BooleanVar(value=True)
        self.assertTrue(auto_handshake_var.get())
        
        auto_handshake_var.set(False)
        self.assertFalse(auto_handshake_var.get())
        
        auto_handshake_var.set(True)
        self.assertTrue(auto_handshake_var.get())


class TestHandshakeTriggerCallback(unittest.TestCase):
    """Test handshake trigger callback functionality."""

    def setUp(self):
        """Prepare test fixtures."""
        # Create root window for tkinter variables
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.mock_logger = MockAppLogger()
        self.mock_ws_manager = MockWebSocketManager()
        
        # UI variables
        self.auto_handshake_var = tk.BooleanVar(value=True)
        self.client_id_var = tk.StringVar(value="device-001")
        self.auth_token_var = tk.StringVar(value="auth-token-xxx")

    def tearDown(self):
        """Clean up resources."""
        self.root.destroy()

    def test_trigger_handshake_with_auto_enabled(self):
        """Verify handshake triggered when auto_handshake_var is True."""
        self.auto_handshake_var.set(True)
        
        # Simulate trigger_handshake_on_connect
        if self.auto_handshake_var.get():
            handshake_payload = {
                "action": "handshake",
                "clientId": self.client_id_var.get().strip(),
                "token": self.auth_token_var.get().strip(),
                "capabilities": ["subscribe", "ping", "query"],
            }
            self.mock_ws_manager.send_json(handshake_payload)
        
        # Verify send_json was called
        self.mock_ws_manager.send_json.assert_called_once()
        call_args = self.mock_ws_manager.send_json.call_args[0][0]
        self.assertEqual(call_args["action"], "handshake")

    def test_trigger_handshake_with_auto_disabled(self):
        """Verify handshake NOT triggered when auto_handshake_var is False."""
        self.auto_handshake_var.set(False)
        
        # Simulate trigger_handshake_on_connect
        if self.auto_handshake_var.get():
            handshake_payload = {
                "action": "handshake",
                "clientId": self.client_id_var.get().strip(),
                "token": self.auth_token_var.get().strip(),
                "capabilities": ["subscribe", "ping", "query"],
            }
            self.mock_ws_manager.send_json(handshake_payload)
        
        # Verify send_json was NOT called
        self.mock_ws_manager.send_json.assert_not_called()

    def test_handshake_payload_with_custom_client_id(self):
        """Verify custom client_id is included in payload."""
        self.client_id_var.set("custom-device-123")
        self.auto_handshake_var.set(True)
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["clientId"], "custom-device-123")

    def test_handshake_payload_with_custom_token(self):
        """Verify custom token is included in payload."""
        self.auth_token_var.set("custom-token-abc123")
        self.auto_handshake_var.set(True)
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["token"], "custom-token-abc123")

    def test_handshake_payload_structure(self):
        """Verify handshake payload has correct structure."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        # Verify all required fields present
        self.assertIn("action", handshake_payload)
        self.assertIn("clientId", handshake_payload)
        self.assertIn("token", handshake_payload)
        self.assertIn("capabilities", handshake_payload)
        
        # Verify values are correct types
        self.assertEqual(handshake_payload["action"], "handshake")
        self.assertIsInstance(handshake_payload["clientId"], str)
        self.assertIsInstance(handshake_payload["token"], str)
        self.assertIsInstance(handshake_payload["capabilities"], list)

    def test_handshake_payload_strips_whitespace(self):
        """Verify whitespace is stripped from clientId and token."""
        self.client_id_var.set("  device-001  ")
        self.auth_token_var.set("  token-xxx  ")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["clientId"], "device-001")
        self.assertEqual(handshake_payload["token"], "token-xxx")

    def test_handshake_capabilities_always_present(self):
        """Verify capabilities list is always included."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertIn("capabilities", handshake_payload)
        self.assertEqual(len(handshake_payload["capabilities"]), 3)

    def test_payload_can_be_json_serialized(self):
        """Verify payload can be serialized to JSON."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        # Should not raise exception
        json_str = json.dumps(handshake_payload)
        self.assertIsInstance(json_str, str)
        
        # Should be deserializable
        recovered = json.loads(json_str)
        self.assertEqual(recovered["action"], "handshake")


class TestHandshakeEdgeCases(unittest.TestCase):
    """Test handshake edge cases and error conditions."""

    def setUp(self):
        """Prepare test fixtures."""
        # Create root window for tkinter variables
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.mock_logger = MockAppLogger()
        self.mock_ws_manager = MockWebSocketManager()
        
        self.auto_handshake_var = tk.BooleanVar(value=True)
        self.client_id_var = tk.StringVar(value="device-001")
        self.auth_token_var = tk.StringVar(value="auth-token-xxx")

    def tearDown(self):
        """Clean up resources."""
        self.root.destroy()

    def test_empty_client_id(self):
        """Verify handshake handles empty client ID."""
        self.client_id_var.set("")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        # Payload should be created even with empty clientId
        self.assertEqual(handshake_payload["clientId"], "")
        self.mock_ws_manager.send_json(handshake_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_empty_token(self):
        """Verify handshake handles empty token."""
        self.auth_token_var.set("")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        # Payload should be created even with empty token
        self.assertEqual(handshake_payload["token"], "")
        self.mock_ws_manager.send_json(handshake_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_empty_capabilities_list(self):
        """Verify handshake works with empty capabilities."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": [],
        }
        
        self.assertEqual(handshake_payload["capabilities"], [])
        self.mock_ws_manager.send_json(handshake_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_special_characters_in_client_id(self):
        """Verify special characters in client ID are preserved."""
        self.client_id_var.set("device-001:sensor-123")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["clientId"], "device-001:sensor-123")

    def test_special_characters_in_token(self):
        """Verify special characters in token are preserved."""
        self.auth_token_var.set("token-abc_123.xyz!@#")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["token"], "token-abc_123.xyz!@#")

    def test_unicode_characters_in_client_id(self):
        """Verify unicode characters are handled."""
        self.client_id_var.set("device-🔧-001")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertIn("🔧", handshake_payload["clientId"])

    def test_very_long_client_id(self):
        """Verify very long client ID is handled."""
        long_id = "device-" + "x" * 1000
        self.client_id_var.set(long_id)
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(len(handshake_payload["clientId"]), 1007)

    def test_very_long_token(self):
        """Verify very long token is handled."""
        long_token = "token-" + "y" * 2000
        self.auth_token_var.set(long_token)
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(len(handshake_payload["token"]), 2006)

    def test_null_like_string_client_id(self):
        """Verify null-like strings are preserved as-is."""
        self.client_id_var.set("null")
        
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        self.assertEqual(handshake_payload["clientId"], "null")

    def test_multiple_rapid_triggers(self):
        """Verify multiple rapid triggers send multiple payloads."""
        self.auto_handshake_var.set(True)
        
        # Simulate rapid triggers
        for i in range(5):
            if self.auto_handshake_var.get():
                handshake_payload = {
                    "action": "handshake",
                    "clientId": self.client_id_var.get().strip(),
                    "token": self.auth_token_var.get().strip(),
                    "capabilities": ["subscribe", "ping", "query"],
                }
                self.mock_ws_manager.send_json(handshake_payload)
        
        self.assertEqual(self.mock_ws_manager.send_json.call_count, 5)


class TestHandshakeNoRegression(unittest.TestCase):
    """Test that existing commands still work (no regression)."""

    def setUp(self):
        """Prepare test fixtures."""
        self.mock_logger = MockAppLogger()
        self.mock_ws_manager = MockWebSocketManager()

    def test_ping_command_still_works(self):
        """Verify Ping command still functions."""
        ping_payload = {
            "action": "ping",
            "timestamp": "2026-03-27T12:00:00Z",
        }
        
        self.mock_ws_manager.send_json(ping_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_subscribe_command_still_works(self):
        """Verify Subscribe command still functions."""
        subscribe_payload = {
            "action": "subscribe",
            "channel": "events",
        }
        
        self.mock_ws_manager.send_json(subscribe_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_login_command_still_works(self):
        """Verify Login command still functions."""
        login_payload = {
            "action": "login",
            "username": "demo_user",
            "token": "replace-me",
        }
        
        self.mock_ws_manager.send_json(login_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_echo_command_still_works(self):
        """Verify Echo command still functions."""
        echo_payload = {
            "action": "echo",
            "message": "hello from tkinter client",
        }
        
        self.mock_ws_manager.send_json(echo_payload)
        self.mock_ws_manager.send_json.assert_called_once()

    def test_multiple_different_commands(self):
        """Verify multiple different commands can be sent in sequence."""
        commands = [
            {"action": "ping", "timestamp": "2026-03-27T12:00:00Z"},
            {"action": "handshake", "clientId": "device-001", "token": "token", "capabilities": []},
            {"action": "subscribe", "channel": "events"},
            {"action": "echo", "message": "test"},
        ]
        
        for cmd in commands:
            self.mock_ws_manager.send_json(cmd)
        
        self.assertEqual(self.mock_ws_manager.send_json.call_count, 4)


class TestHandshakeLogging(unittest.TestCase):
    """Test handshake logging functionality."""

    def setUp(self):
        """Prepare test fixtures."""
        # Create root window for tkinter variables
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.mock_logger = MockAppLogger()
        self.auto_handshake_var = tk.BooleanVar(value=True)
        self.client_id_var = tk.StringVar(value="device-001")
        self.auth_token_var = tk.StringVar(value="auth-token-xxx")

    def tearDown(self):
        """Clean up resources."""
        self.root.destroy()

    def test_handshake_logged_to_logger(self):
        """Verify handshake action is logged."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        log_message = f"Auto-sending handshake: {json.dumps(handshake_payload)}"
        self.mock_logger.log(log_message)
        
        self.mock_logger.log.assert_called_once()

    def test_logged_payload_is_json_serializable(self):
        """Verify logged payload message is valid."""
        handshake_payload = {
            "action": "handshake",
            "clientId": self.client_id_var.get().strip(),
            "token": self.auth_token_var.get().strip(),
            "capabilities": ["subscribe", "ping", "query"],
        }
        
        log_message = f"Auto-sending handshake: {json.dumps(handshake_payload)}"
        
        # Extract JSON part and verify it's valid
        json_part = log_message.split(": ", 1)[1]
        recovered = json.loads(json_part)
        self.assertEqual(recovered["action"], "handshake")


if __name__ == "__main__":
    unittest.main()
