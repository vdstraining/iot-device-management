import json
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from handshake import HandshakeManager
from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS, AppLogger


class TestHandshakeManagerInitialization(unittest.TestCase):
    """Test HandshakeManager initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_init_with_default_values(self):
        """Test initialization with default values."""
        manager = HandshakeManager(self.mock_logger)
        
        self.assertEqual(manager.client_id, "client-001")
        self.assertEqual(manager.version, "1.0")
        self.assertEqual(manager.capabilities, ["ping", "subscribe", "echo"])
        self.assertIsNone(manager.token)
        self.assertEqual(manager.metadata, {"platform": "tkinter"})
        self.assertEqual(manager.logger, self.mock_logger)

    def test_init_with_custom_client_id(self):
        """Test initialization with custom client_id."""
        manager = HandshakeManager(self.mock_logger, client_id="device-123")
        
        self.assertEqual(manager.client_id, "device-123")

    def test_init_with_custom_version(self):
        """Test initialization with custom version."""
        manager = HandshakeManager(self.mock_logger, version="2.0.1")
        
        self.assertEqual(manager.version, "2.0.1")

    def test_init_with_custom_capabilities(self):
        """Test initialization with custom capabilities."""
        custom_caps = ["custom1", "custom2"]
        manager = HandshakeManager(self.mock_logger, capabilities=custom_caps)
        
        self.assertEqual(manager.capabilities, custom_caps)

    def test_init_with_all_custom_values(self):
        """Test initialization with all custom values."""
        custom_caps = ["feature1", "feature2", "feature3"]
        manager = HandshakeManager(
            self.mock_logger,
            client_id="test-client",
            version="3.0",
            capabilities=custom_caps,
        )
        
        self.assertEqual(manager.client_id, "test-client")
        self.assertEqual(manager.version, "3.0")
        self.assertEqual(manager.capabilities, custom_caps)


class TestHandshakeManagerValidation(unittest.TestCase):
    """Test HandshakeManager validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_validate_with_valid_payload(self):
        """Test validate() with valid payload."""
        manager = HandshakeManager(self.mock_logger)
        
        result = manager.validate()
        
        self.assertTrue(result)
        self.mock_logger.log.assert_not_called()

    def test_validate_with_missing_client_id(self):
        """Test validate() with missing client_id."""
        manager = HandshakeManager(self.mock_logger)
        manager.client_id = None
        
        result = manager.validate()
        
        self.assertFalse(result)
        self.mock_logger.log.assert_called_with(
            "Handshake validation failed: client_id is required."
        )

    def test_validate_with_empty_client_id(self):
        """Test validate() with empty client_id."""
        manager = HandshakeManager(self.mock_logger)
        manager.client_id = ""
        
        result = manager.validate()
        
        self.assertFalse(result)

    def test_validate_with_missing_version(self):
        """Test validate() with missing version."""
        manager = HandshakeManager(self.mock_logger)
        manager.version = None
        
        result = manager.validate()
        
        self.assertFalse(result)
        self.mock_logger.log.assert_called_with(
            "Handshake validation failed: version is required."
        )

    def test_validate_with_empty_version(self):
        """Test validate() with empty version."""
        manager = HandshakeManager(self.mock_logger)
        manager.version = ""
        
        result = manager.validate()
        
        self.assertFalse(result)

    def test_validate_with_empty_capabilities(self):
        """Test validate() with empty capabilities."""
        manager = HandshakeManager(self.mock_logger)
        manager.capabilities = []
        
        result = manager.validate()
        
        self.assertFalse(result)
        self.mock_logger.log.assert_called_with(
            "Handshake validation failed: capabilities must be a non-empty list."
        )

    def test_validate_with_non_list_capabilities(self):
        """Test validate() with non-list capabilities."""
        manager = HandshakeManager(self.mock_logger)
        manager.capabilities = "ping"  # Should be a list
        
        result = manager.validate()
        
        self.assertFalse(result)

    def test_validate_with_single_capability(self):
        """Test validate() with single capability in list."""
        manager = HandshakeManager(self.mock_logger)
        manager.capabilities = ["single-cap"]
        
        result = manager.validate()
        
        self.assertTrue(result)


class TestHandshakeManagerPayload(unittest.TestCase):
    """Test HandshakeManager payload generation."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_get_payload_returns_correct_structure(self):
        """Test get_payload() returns correct structure."""
        manager = HandshakeManager(self.mock_logger)
        
        payload = manager.get_payload()
        
        self.assertIsNotNone(payload)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "handshake")
        self.assertEqual(payload["clientId"], "client-001")
        self.assertEqual(payload["version"], "1.0")
        self.assertIn("capabilities", payload)
        self.assertIn("token", payload)
        self.assertIn("metadata", payload)

    def test_get_payload_with_custom_values(self):
        """Test get_payload() with custom values."""
        custom_caps = ["feature1", "feature2"]
        manager = HandshakeManager(
            self.mock_logger,
            client_id="device-xyz",
            version="2.5",
            capabilities=custom_caps,
        )
        manager.set_token("auth-token-123")
        manager.set_metadata({"platform": "linux", "arch": "x86_64"})
        
        payload = manager.get_payload()
        
        self.assertEqual(payload["clientId"], "device-xyz")
        self.assertEqual(payload["version"], "2.5")
        self.assertEqual(payload["capabilities"], custom_caps)
        self.assertEqual(payload["token"], "auth-token-123")
        self.assertEqual(payload["metadata"], {"platform": "linux", "arch": "x86_64"})

    def test_get_payload_returns_none_when_validation_fails(self):
        """Test get_payload() returns None when validation fails."""
        manager = HandshakeManager(self.mock_logger)
        manager.client_id = None
        
        payload = manager.get_payload()
        
        self.assertIsNone(payload)

    def test_get_payload_returns_json_serializable(self):
        """Test get_payload() returns JSON serializable object."""
        manager = HandshakeManager(self.mock_logger)
        
        payload = manager.get_payload()
        
        # Should not raise an exception
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["action"], "handshake")


class TestHandshakeManagerSetters(unittest.TestCase):
    """Test HandshakeManager setter methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.manager = HandshakeManager(self.mock_logger)

    def test_set_client_id(self):
        """Test set_client_id() method."""
        self.manager.set_client_id("new-client-id")
        
        self.assertEqual(self.manager.client_id, "new-client-id")

    def test_set_version(self):
        """Test set_version() method."""
        self.manager.set_version("3.0.0")
        
        self.assertEqual(self.manager.version, "3.0.0")

    def test_set_token(self):
        """Test set_token() method."""
        self.manager.set_token("new-token-123")
        
        self.assertEqual(self.manager.token, "new-token-123")

    def test_set_token_to_none(self):
        """Test set_token() to None."""
        self.manager.set_token("token")
        self.manager.set_token(None)
        
        self.assertIsNone(self.manager.token)

    def test_set_capabilities(self):
        """Test set_capabilities() method."""
        new_caps = ["cap1", "cap2", "cap3"]
        self.manager.set_capabilities(new_caps)
        
        self.assertEqual(self.manager.capabilities, new_caps)

    def test_set_metadata(self):
        """Test set_metadata() method."""
        new_metadata = {"os": "ubuntu", "version": "20.04"}
        self.manager.set_metadata(new_metadata)
        
        self.assertEqual(self.manager.metadata, new_metadata)

    def test_set_metadata_replaces_existing(self):
        """Test set_metadata() replaces existing metadata."""
        self.manager.set_metadata({"platform": "tkinter"})
        old_metadata = self.manager.metadata.copy()
        
        new_metadata = {"new_key": "new_value"}
        self.manager.set_metadata(new_metadata)
        
        self.assertNotEqual(self.manager.metadata, old_metadata)
        self.assertEqual(self.manager.metadata, new_metadata)


class TestHandshakeManagerStaticMethod(unittest.TestCase):
    """Test HandshakeManager static methods."""

    def test_build_payload_template(self):
        """Test build_payload_template() static method."""
        template = HandshakeManager.build_payload_template()
        
        self.assertIsNotNone(template)
        self.assertIsInstance(template, dict)
        self.assertEqual(template["action"], "handshake")
        self.assertEqual(template["clientId"], "client-001")
        self.assertEqual(template["version"], "1.0")
        self.assertEqual(template["capabilities"], ["ping", "subscribe", "echo"])
        self.assertIsNone(template["token"])
        self.assertEqual(template["metadata"], {"platform": "tkinter"})

    def test_build_payload_template_is_not_instance_dependent(self):
        """Test build_payload_template() works without instance."""
        template = HandshakeManager.build_payload_template()
        
        # Verify it returns the expected structure
        self.assertIn("action", template)
        self.assertIn("clientId", template)
        self.assertIn("version", template)


class TestWebSocketManagerInitialization(unittest.TestCase):
    """Test WebSocketManager initialization."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_init_with_auto_send_handshake_true(self):
        """Test WebSocketManager initialization with auto_send_handshake=True."""
        manager = WebSocketManager(
            self.mock_logger,
            auto_send_handshake=True,
        )
        
        self.assertTrue(manager.auto_send_handshake)

    def test_init_with_auto_send_handshake_false(self):
        """Test WebSocketManager initialization with auto_send_handshake=False."""
        manager = WebSocketManager(
            self.mock_logger,
            auto_send_handshake=False,
        )
        
        self.assertFalse(manager.auto_send_handshake)

    def test_init_default_auto_send_handshake_is_false(self):
        """Test default auto_send_handshake is False."""
        manager = WebSocketManager(self.mock_logger)
        
        self.assertFalse(manager.auto_send_handshake)

    def test_auto_trigger_flag_stored_correctly(self):
        """Test auto-trigger flag is stored correctly."""
        manager_true = WebSocketManager(self.mock_logger, auto_send_handshake=True)
        manager_false = WebSocketManager(self.mock_logger, auto_send_handshake=False)
        
        self.assertTrue(manager_true.auto_send_handshake)
        self.assertFalse(manager_false.auto_send_handshake)

    def test_handshake_manager_initialized_correctly(self):
        """Test handshake_manager is initialized correctly."""
        manager = WebSocketManager(self.mock_logger)
        
        self.assertIsNotNone(manager.handshake_manager)
        self.assertIsInstance(manager.handshake_manager, HandshakeManager)
        self.assertEqual(manager.handshake_manager.logger, self.mock_logger)


class TestWebSocketManagerHandshakeMethods(unittest.TestCase):
    """Test WebSocketManager handshake methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.manager = WebSocketManager(self.mock_logger)

    def test_send_handshake_method_exists(self):
        """Test _send_handshake() method exists."""
        self.assertTrue(hasattr(self.manager, "_send_handshake"))
        self.assertTrue(callable(getattr(self.manager, "_send_handshake")))

    def test_send_handshake_calls_ws_app_send_when_connected(self):
        """Test _send_handshake() calls ws_app.send when connected."""
        self.manager.ws_app = MagicMock()
        self.manager.connected = True
        
        self.manager._send_handshake()
        
        # Verify ws_app.send was called with JSON payload
        self.manager.ws_app.send.assert_called_once()
        call_args = self.manager.ws_app.send.call_args[0][0]
        payload = json.loads(call_args)
        self.assertEqual(payload["action"], "handshake")

    def test_send_handshake_handles_invalid_payload(self):
        """Test _send_handshake() handles invalid payload."""
        self.manager.handshake_manager.client_id = None
        self.manager.ws_app = MagicMock()
        
        self.manager._send_handshake()
        
        # ws_app.send should not be called if payload is None
        self.manager.ws_app.send.assert_not_called()

    def test_send_handshake_logs_error_on_exception(self):
        """Test _send_handshake() logs error on exception."""
        self.manager.ws_app = MagicMock()
        self.manager.ws_app.send.side_effect = Exception("Send failed")
        
        self.manager._send_handshake()
        
        # Verify error was logged
        self.mock_logger.log.assert_called()
        logged_message = str(self.mock_logger.log.call_args)
        self.assertIn("error", logged_message.lower())


class TestWebSocketManagerOnOpenWithHandshake(unittest.TestCase):
    """Test WebSocketManager _on_open with handshake."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_on_open_sends_handshake_when_auto_send_is_true(self):
        """Test _on_open sends handshake when auto_send_handshake is True."""
        manager = WebSocketManager(self.mock_logger, auto_send_handshake=True)
        manager.ws_app = MagicMock()
        
        manager._on_open(None)
        
        # Verify ws_app.send was called
        manager.ws_app.send.assert_called_once()

    def test_on_open_does_not_send_handshake_when_auto_send_is_false(self):
        """Test _on_open does not send handshake when auto_send_handshake is False."""
        manager = WebSocketManager(self.mock_logger, auto_send_handshake=False)
        manager.ws_app = MagicMock()
        
        manager._on_open(None)
        
        # Verify ws_app.send was not called
        manager.ws_app.send.assert_not_called()

    def test_on_open_sets_connected_status(self):
        """Test _on_open sets connected status."""
        manager = WebSocketManager(self.mock_logger)
        self.assertFalse(manager.connected)
        
        manager._on_open(None)
        
        self.assertTrue(manager.connected)

    def test_on_open_calls_on_status_change_callback(self):
        """Test _on_open calls on_status_change callback."""
        mock_callback = Mock()
        manager = WebSocketManager(
            self.mock_logger,
            on_status_change=mock_callback,
        )
        
        manager._on_open(None)
        
        mock_callback.assert_called_with(True)


class TestUtilitiesDefaultCommands(unittest.TestCase):
    """Test utilities DEFAULT_COMMANDS."""

    def test_default_commands_includes_handshake(self):
        """Test DEFAULT_COMMANDS includes Handshake command."""
        handshake_cmd = None
        for cmd in DEFAULT_COMMANDS:
            if cmd["name"] == "Handshake":
                handshake_cmd = cmd
                break
        
        self.assertIsNotNone(handshake_cmd, "Handshake command not found in DEFAULT_COMMANDS")

    def test_handshake_is_sixth_item(self):
        """Test Handshake command is the 6th item (index 5)."""
        self.assertEqual(len(DEFAULT_COMMANDS), 6, "DEFAULT_COMMANDS should have 6 items")
        self.assertEqual(DEFAULT_COMMANDS[5]["name"], "Handshake")

    def test_handshake_command_has_correct_name(self):
        """Test Handshake command has correct name."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        
        self.assertEqual(handshake_cmd["name"], "Handshake")

    def test_handshake_command_has_payload(self):
        """Test Handshake command has payload."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        
        self.assertIn("payload", handshake_cmd)
        self.assertIsInstance(handshake_cmd["payload"], dict)

    def test_handshake_payload_has_required_fields(self):
        """Test Handshake payload has all required fields."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        required_fields = [
            "action",
            "clientId",
            "version",
            "capabilities",
            "token",
            "metadata",
        ]
        
        for field in required_fields:
            self.assertIn(field, payload, f"Missing field: {field}")

    def test_handshake_payload_action_is_handshake(self):
        """Test Handshake payload action is 'handshake'."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        self.assertEqual(payload["action"], "handshake")

    def test_handshake_payload_has_valid_client_id(self):
        """Test Handshake payload has valid client_id."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        self.assertEqual(payload["clientId"], "client-001")

    def test_handshake_payload_has_valid_version(self):
        """Test Handshake payload has valid version."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        self.assertEqual(payload["version"], "1.0")

    def test_handshake_payload_capabilities_is_list(self):
        """Test Handshake payload capabilities is a list."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        self.assertIsInstance(payload["capabilities"], list)
        self.assertGreater(len(payload["capabilities"]), 0)

    def test_handshake_payload_metadata_is_dict(self):
        """Test Handshake payload metadata is a dict."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        self.assertIsInstance(payload["metadata"], dict)
        self.assertIn("platform", payload["metadata"])


class TestIntegrationHandshakeWithLogger(unittest.TestCase):
    """Test HandshakeManager integration with AppLogger."""

    def setUp(self):
        """Set up test fixtures."""
        self.logged_messages = []

        def log_callback(message):
            self.logged_messages.append(message)

        self.logger = AppLogger(log_callback)

    def test_handshake_manager_integrates_with_app_logger(self):
        """Test HandshakeManager integrates with AppLogger correctly."""
        manager = HandshakeManager(self.logger)
        
        # Trigger validation error
        manager.client_id = None
        manager.validate()
        
        # Verify message was logged
        self.assertTrue(any("client_id" in msg for msg in self.logged_messages))

    def test_validation_error_logged_with_timestamp(self):
        """Test validation error is logged with timestamp."""
        manager = HandshakeManager(self.logger)
        manager.client_id = None
        manager.validate()
        
        # Verify timestamp format
        self.assertTrue(any("[" in msg and "]" in msg for msg in self.logged_messages))


class TestIntegrationHandshakeInCommandsList(unittest.TestCase):
    """Test Handshake command integration in DEFAULT_COMMANDS."""

    def test_handshake_command_can_be_selected(self):
        """Test Handshake command can be selected from DEFAULT_COMMANDS."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        
        self.assertIsNotNone(handshake_cmd)
        self.assertEqual(handshake_cmd["name"], "Handshake")

    def test_handshake_payload_is_json_serializable(self):
        """Test Handshake payload from DEFAULT_COMMANDS is JSON serializable."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        payload = handshake_cmd["payload"]
        
        # Should not raise an exception
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["action"], "handshake")

    def test_default_commands_list_length(self):
        """Test DEFAULT_COMMANDS list length is 6."""
        self.assertEqual(len(DEFAULT_COMMANDS), 6)


class TestEdgeCasesAndErrorHandling(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_handshake_manager_with_none_logger(self):
        """Test HandshakeManager handles None logger gracefully."""
        # This should work even with None logger (though logging won't work)
        manager = HandshakeManager(None)
        
        self.assertIsNone(manager.logger)

    def test_handshake_with_special_characters_in_client_id(self):
        """Test handshake with special characters in client_id."""
        manager = HandshakeManager(
            self.mock_logger,
            client_id="client-@#$%^&*()",
        )
        
        payload = manager.get_payload()
        
        self.assertEqual(payload["clientId"], "client-@#$%^&*()")

    def test_handshake_with_unicode_in_metadata(self):
        """Test handshake with unicode in metadata."""
        manager = HandshakeManager(self.mock_logger)
        manager.set_metadata({"device": "设备", "platform": "Linux"})
        
        payload = manager.get_payload()
        
        # Should be JSON serializable
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)

    def test_handshake_with_very_long_client_id(self):
        """Test handshake with very long client_id."""
        long_id = "client-" + ("x" * 1000)
        manager = HandshakeManager(self.mock_logger, client_id=long_id)
        
        payload = manager.get_payload()
        
        self.assertEqual(payload["clientId"], long_id)

    def test_handshake_with_many_capabilities(self):
        """Test handshake with many capabilities."""
        many_caps = [f"capability_{i}" for i in range(100)]
        manager = HandshakeManager(self.mock_logger, capabilities=many_caps)
        
        payload = manager.get_payload()
        
        self.assertEqual(len(payload["capabilities"]), 100)

    def test_multiple_handshake_manager_instances_independent(self):
        """Test multiple HandshakeManager instances are independent."""
        manager1 = HandshakeManager(self.mock_logger, client_id="client-1")
        manager2 = HandshakeManager(self.mock_logger, client_id="client-2")
        
        manager1.set_version("1.0")
        manager2.set_version("2.0")
        
        self.assertEqual(manager1.get_payload()["version"], "1.0")
        self.assertEqual(manager2.get_payload()["version"], "2.0")

    def test_websocket_manager_handshake_independence(self):
        """Test multiple WebSocketManager instances have independent handshake managers."""
        manager1 = WebSocketManager(self.mock_logger)
        manager2 = WebSocketManager(self.mock_logger)
        
        manager1.handshake_manager.set_client_id("device-1")
        manager2.handshake_manager.set_client_id("device-2")
        
        self.assertEqual(
            manager1.handshake_manager.get_payload()["clientId"],
            "device-1",
        )
        self.assertEqual(
            manager2.handshake_manager.get_payload()["clientId"],
            "device-2",
        )


class TestPayloadStructureConsistency(unittest.TestCase):
    """Test payload structure consistency between different methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()

    def test_template_and_instance_payload_have_same_structure(self):
        """Test template and instance payload have same structure."""
        template = HandshakeManager.build_payload_template()
        manager = HandshakeManager(self.mock_logger)
        instance_payload = manager.get_payload()
        
        self.assertEqual(set(template.keys()), set(instance_payload.keys()))

    def test_default_commands_handshake_matches_manager_structure(self):
        """Test DEFAULT_COMMANDS Handshake matches HandshakeManager structure."""
        handshake_cmd = DEFAULT_COMMANDS[5]
        cmd_payload = handshake_cmd["payload"]
        
        manager = HandshakeManager(self.mock_logger)
        manager_payload = manager.get_payload()
        
        self.assertEqual(set(cmd_payload.keys()), set(manager_payload.keys()))

    def test_payload_values_are_reasonable_types(self):
        """Test payload values are reasonable types."""
        manager = HandshakeManager(self.mock_logger)
        payload = manager.get_payload()
        
        self.assertIsInstance(payload["action"], str)
        self.assertIsInstance(payload["clientId"], str)
        self.assertIsInstance(payload["version"], str)
        self.assertIsInstance(payload["capabilities"], list)
        self.assertIsInstance(payload["metadata"], dict)


if __name__ == "__main__":
    unittest.main()
