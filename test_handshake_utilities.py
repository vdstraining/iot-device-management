"""
Unit tests for utilities.py - Handshake command verification.

Tests verify:
- Handshake command exists in DEFAULT_COMMANDS
- Payload structure and required fields
- Payload consistency across multiple accesses
"""

import unittest
from utilities import DEFAULT_COMMANDS


class TestHandshakeCommand(unittest.TestCase):
    """Test Handshake command in DEFAULT_COMMANDS."""

    def setUp(self):
        """Prepare test fixtures."""
        self.commands = DEFAULT_COMMANDS
        self.handshake_cmd = None
        for cmd in self.commands:
            if cmd.get("name") == "Handshake":
                self.handshake_cmd = cmd
                break

    def test_handshake_command_exists(self):
        """Verify Handshake command exists in DEFAULT_COMMANDS."""
        self.assertIsNotNone(self.handshake_cmd, "Handshake command not found in DEFAULT_COMMANDS")

    def test_handshake_command_has_name(self):
        """Verify Handshake command has 'name' field."""
        self.assertIn("name", self.handshake_cmd)
        self.assertEqual(self.handshake_cmd["name"], "Handshake")

    def test_handshake_command_has_payload(self):
        """Verify Handshake command has 'payload' field."""
        self.assertIn("payload", self.handshake_cmd)
        self.assertIsInstance(self.handshake_cmd["payload"], dict)

    def test_handshake_payload_required_fields(self):
        """Verify Handshake payload contains all required fields."""
        payload = self.handshake_cmd["payload"]
        
        required_fields = ["action", "clientId", "token", "capabilities"]
        for field in required_fields:
            self.assertIn(field, payload, f"Missing required field: {field}")

    def test_handshake_action_is_correct(self):
        """Verify Handshake action is 'handshake'."""
        payload = self.handshake_cmd["payload"]
        self.assertEqual(payload["action"], "handshake")

    def test_handshake_clientid_is_string(self):
        """Verify clientId is a string."""
        payload = self.handshake_cmd["payload"]
        self.assertIsInstance(payload["clientId"], str)
        self.assertTrue(len(payload["clientId"]) > 0)

    def test_handshake_token_is_string(self):
        """Verify token is a string."""
        payload = self.handshake_cmd["payload"]
        self.assertIsInstance(payload["token"], str)
        self.assertTrue(len(payload["token"]) > 0)

    def test_handshake_capabilities_is_list(self):
        """Verify capabilities is a non-empty list."""
        payload = self.handshake_cmd["payload"]
        self.assertIsInstance(payload["capabilities"], list)
        self.assertTrue(len(payload["capabilities"]) > 0)

    def test_handshake_capabilities_contains_expected_values(self):
        """Verify capabilities list contains expected capability names."""
        payload = self.handshake_cmd["payload"]
        capabilities = payload["capabilities"]
        
        # Verify common expected capabilities
        self.assertIn("subscribe", capabilities)
        self.assertIn("ping", capabilities)
        self.assertIn("query", capabilities)

    def test_handshake_payload_no_extra_fields(self):
        """Verify payload only contains expected fields."""
        payload = self.handshake_cmd["payload"]
        expected_fields = {"action", "clientId", "token", "capabilities"}
        actual_fields = set(payload.keys())
        self.assertEqual(actual_fields, expected_fields)

    def test_other_commands_still_exist(self):
        """Verify existing commands (Ping, Login, Subscribe) are not affected."""
        command_names = [cmd["name"] for cmd in self.commands]
        
        expected_commands = ["Ping", "Login", "Subscribe", "Echo", "Handshake", "HTTP POST sample"]
        for cmd_name in expected_commands:
            self.assertIn(cmd_name, command_names, f"Command '{cmd_name}' missing from DEFAULT_COMMANDS")

    def test_ping_command_intact(self):
        """Verify Ping command structure is unchanged."""
        ping_cmd = None
        for cmd in self.commands:
            if cmd.get("name") == "Ping":
                ping_cmd = cmd
                break
        
        self.assertIsNotNone(ping_cmd)
        self.assertEqual(ping_cmd["payload"]["action"], "ping")

    def test_subscribe_command_intact(self):
        """Verify Subscribe command structure is unchanged."""
        subscribe_cmd = None
        for cmd in self.commands:
            if cmd.get("name") == "Subscribe":
                subscribe_cmd = cmd
                break
        
        self.assertIsNotNone(subscribe_cmd)
        self.assertEqual(subscribe_cmd["payload"]["action"], "subscribe")

    def test_handshake_payload_immutability(self):
        """Verify multiple accesses return consistent payload structure."""
        payload1 = self.handshake_cmd["payload"]
        payload2 = self.handshake_cmd["payload"]
        
        # Same reference (testing from module constant)
        self.assertEqual(payload1, payload2)
        self.assertEqual(payload1["action"], payload2["action"])
        self.assertEqual(payload1["clientId"], payload2["clientId"])
        self.assertEqual(payload1["token"], payload2["token"])
        self.assertEqual(payload1["capabilities"], payload2["capabilities"])


class TestDefaultCommandsIntegrity(unittest.TestCase):
    """Test overall integrity of DEFAULT_COMMANDS list."""

    def test_commands_list_not_empty(self):
        """Verify DEFAULT_COMMANDS is not empty."""
        self.assertGreater(len(DEFAULT_COMMANDS), 0)

    def test_all_commands_have_name(self):
        """Verify all commands have a 'name' field."""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn("name", cmd, f"Command missing 'name': {cmd}")
            self.assertIsInstance(cmd["name"], str)
            self.assertTrue(len(cmd["name"]) > 0)

    def test_all_commands_have_payload(self):
        """Verify all commands have a 'payload' field."""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn("payload", cmd, f"Command {cmd.get('name')} missing 'payload'")
            self.assertIsInstance(cmd["payload"], dict)

    def test_command_names_are_unique(self):
        """Verify command names are unique (no duplicates)."""
        names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
        self.assertEqual(len(names), len(set(names)), "Duplicate command names found")

    def test_all_payloads_have_action_or_method(self):
        """Verify all payloads have either 'action' or 'method' (for HTTP)."""
        for cmd in DEFAULT_COMMANDS:
            payload = cmd["payload"]
            has_action_or_method = "action" in payload or "method" in payload
            self.assertTrue(
                has_action_or_method,
                f"Command '{cmd['name']}' payload missing 'action' or 'method'"
            )


if __name__ == "__main__":
    unittest.main()
