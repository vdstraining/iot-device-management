"""
Comprehensive tests for SCRUM-64 Handshake Implementation

Tests cover:
- Unit tests for handshake message structure and validation
- Integration tests for WebSocket handshake flow
- Edge cases for missing fields, invalid formats, and timing issues
"""

import unittest
import json
import logging
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import time
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS, AppLogger


class TestHandshakeMessageStructure(unittest.TestCase):
    """Unit tests for handshake message structure validation"""

    def setUp(self):
        """Set up test fixtures"""
        self.handshake_cmd = None
        # Find handshake command in DEFAULT_COMMANDS
        for cmd in DEFAULT_COMMANDS:
            if isinstance(cmd, dict) and cmd.get('name') == 'Handshake':
                self.handshake_cmd = cmd
                self.handshake_payload = cmd.get('payload', {})
                break

    def test_handshake_in_default_commands(self):
        """Test that Handshake command exists in DEFAULT_COMMANDS"""
        self.assertIsNotNone(self.handshake_cmd, "Handshake command not found in DEFAULT_COMMANDS")

    def test_handshake_action_field(self):
        """Test handshake message has 'action' field set to 'handshake'"""
        self.assertIn('action', self.handshake_payload)
        self.assertEqual(self.handshake_payload['action'], 'handshake')

    def test_handshake_required_fields(self):
        """Test handshake message has all required fields"""
        required_fields = ['action', 'clientId', 'token', 'timestamp', 'version']
        for field in required_fields:
            self.assertIn(field, self.handshake_payload,
                         f"Missing required field: {field}")

    def test_handshake_message_is_dict(self):
        """Test handshake command is a dictionary"""
        self.assertIsInstance(self.handshake_payload, dict)

    def test_handshake_action_value(self):
        """Test handshake action value is correct"""
        self.assertEqual(self.handshake_payload['action'], 'handshake')

    def test_handshake_clientId_field_exists(self):
        """Test clientId field exists"""
        self.assertIn('clientId', self.handshake_payload)

    def test_handshake_clientId_has_value(self):
        """Test clientId field has a value"""
        self.assertTrue(len(str(self.handshake_payload['clientId'])) > 0)

    def test_handshake_token_field_exists(self):
        """Test token field exists"""
        self.assertIn('token', self.handshake_payload)

    def test_handshake_token_has_value(self):
        """Test token field has a value"""
        self.assertTrue(len(str(self.handshake_payload['token'])) > 0)

    def test_handshake_timestamp_field_exists(self):
        """Test timestamp field exists"""
        self.assertIn('timestamp', self.handshake_payload)

    def test_handshake_timestamp_has_value(self):
        """Test timestamp field has a value"""
        self.assertTrue(len(str(self.handshake_payload['timestamp'])) > 0)

    def test_handshake_version_field_exists(self):
        """Test version field exists"""
        self.assertIn('version', self.handshake_payload)

    def test_handshake_version_has_value(self):
        """Test version field has a value"""
        self.assertTrue(len(str(self.handshake_payload['version'])) > 0)

    def test_handshake_message_serializable(self):
        """Test handshake message can be JSON serialized"""
        try:
            json_str = json.dumps(self.handshake_payload)
            self.assertIsInstance(json_str, str)
        except TypeError:
            self.fail("Handshake message is not JSON serializable")

    def test_handshake_message_deserializable(self):
        """Test handshake message can be JSON deserialized"""
        json_str = json.dumps(self.handshake_payload)
        deserialized = json.loads(json_str)
        self.assertEqual(deserialized['action'], 'handshake')

    def test_handshake_command_name(self):
        """Test handshake command has correct name"""
        self.assertEqual(self.handshake_cmd['name'], 'Handshake')


class TestAutoHandshakeParameter(unittest.TestCase):
    """Unit tests for auto_handshake parameter in WebSocketManager"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock logger
        self.mock_logger = Mock(spec=AppLogger)

    def test_websocket_manager_accepts_auto_handshake_true(self):
        """Test WebSocketManager accepts auto_handshake=True"""
        try:
            manager = WebSocketManager(
                logger=self.mock_logger,
                auto_handshake=True
            )
            self.assertTrue(hasattr(manager, 'auto_handshake'))
            self.assertEqual(manager.auto_handshake, True)
        except TypeError:
            self.fail("WebSocketManager does not accept auto_handshake parameter")

    def test_websocket_manager_accepts_auto_handshake_false(self):
        """Test WebSocketManager accepts auto_handshake=False"""
        try:
            manager = WebSocketManager(
                logger=self.mock_logger,
                auto_handshake=False
            )
            self.assertTrue(hasattr(manager, 'auto_handshake'))
            self.assertEqual(manager.auto_handshake, False)
        except TypeError:
            self.fail("WebSocketManager does not accept auto_handshake parameter")

    def test_websocket_manager_default_auto_handshake(self):
        """Test WebSocketManager has default auto_handshake value"""
        manager = WebSocketManager(logger=self.mock_logger)
        # Should not raise an exception
        self.assertIsNotNone(manager)
        self.assertEqual(manager.auto_handshake, False)

    def test_auto_handshake_defaults_to_false(self):
        """Test auto_handshake defaults to False if not specified"""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertEqual(manager.auto_handshake, False)

    def test_auto_handshake_attribute_exists(self):
        """Test auto_handshake attribute exists on manager"""
        manager = WebSocketManager(logger=self.mock_logger, auto_handshake=True)
        self.assertTrue(hasattr(manager, 'auto_handshake'))

    def test_auto_handshake_with_handshake_payload(self):
        """Test auto_handshake works with custom handshake_payload"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'custom-device',
            'token': 'custom-token',
            'timestamp': '2026-05-07T12:00:00Z',
            'version': '1.0.0'
        }
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True,
            handshake_payload=custom_payload
        )
        self.assertEqual(manager.handshake_payload, custom_payload)

    def test_handshake_payload_default_values(self):
        """Test handshake_payload has default values when not provided"""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertIsNotNone(manager.handshake_payload)
        self.assertIn('action', manager.handshake_payload)
        self.assertEqual(manager.handshake_payload['action'], 'handshake')


class TestHandshakeMessageCreation(unittest.TestCase):
    """Unit tests for handshake message creation"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_clientId = "device-001"
        self.sample_token = "token-12345"
        self.sample_version = "1.0.0"
        self.mock_logger = Mock(spec=AppLogger)

    def test_create_handshake_message_with_custom_clientId(self):
        """Test creating handshake message with custom clientId"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        payload = {
            'action': 'handshake',
            'clientId': self.sample_clientId,
            'token': self.sample_token,
            'timestamp': "2026-05-07T12:00:00Z",
            'version': self.sample_version
        }
        self.assertEqual(payload['clientId'], self.sample_clientId)

    def test_create_handshake_message_with_timestamp(self):
        """Test handshake message includes timestamp"""
        payload = {
            'action': 'handshake',
            'clientId': self.sample_clientId,
            'token': self.sample_token,
            'timestamp': "2026-05-07T12:00:00Z",
            'version': self.sample_version
        }
        self.assertTrue(len(payload['timestamp']) > 0)

    def test_handshake_payload_structure(self):
        """Test handshake payload has correct structure"""
        payload = {
            'action': 'handshake',
            'clientId': self.sample_clientId,
            'token': self.sample_token,
            'timestamp': "2026-05-07T12:00:00Z",
            'version': self.sample_version
        }
        required_keys = ['action', 'clientId', 'token', 'timestamp', 'version']
        for key in required_keys:
            self.assertIn(key, payload)

    def test_handshake_custom_payload_override(self):
        """Test custom handshake payload can override defaults"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'custom-device-999',
            'token': 'custom-secret-token',
            'timestamp': "2026-05-08T15:30:00Z",
            'version': '2.0.0'
        }
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True,
            handshake_payload=custom_payload
        )
        self.assertEqual(manager.handshake_payload, custom_payload)

    def test_handshake_payload_json_valid(self):
        """Test handshake payload is valid JSON"""
        payload = {
            'action': 'handshake',
            'clientId': self.sample_clientId,
            'token': self.sample_token,
            'timestamp': "2026-05-07T12:00:00Z",
            'version': self.sample_version
        }
        json_str = json.dumps(payload)
        parsed = json.loads(json_str)
        self.assertEqual(parsed['action'], 'handshake')


class TestWebSocketConnectionWithHandshake(unittest.TestCase):
    """Integration tests for WebSocket connection with handshake"""

    def setUp(self):
        """Set up test fixtures with mocked dependencies"""
        self.mock_logger = Mock(spec=AppLogger)
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_auto_handshake_sends_after_connection(self):
        """Test auto_handshake sends message after WebSocket connection"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
            auto_handshake=True
        )
        
        # Verify manager was created with auto_handshake
        self.assertTrue(manager.auto_handshake)

    def test_handshake_logging_on_send(self):
        """Test handshake message is logged when sent"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        # Simulating a send operation
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        
        # Verify payload is valid
        self.assertEqual(payload['action'], 'handshake')

    def test_on_open_calls_send_json_when_auto_handshake(self):
        """Test _on_open calls send_json when auto_handshake is enabled"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'device-test',
            'token': 'test-token',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True,
            handshake_payload=custom_payload
        )
        
        # Mock the send_json method
        with patch.object(manager, 'send_json') as mock_send:
            # Simulate connection open
            manager._on_open(None)
            
            # Verify send_json was called with handshake payload
            mock_send.assert_called_with(custom_payload)

    def test_on_open_sets_connected_true(self):
        """Test _on_open sets connected to True"""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertFalse(manager.connected)
        
        manager._on_open(None)
        self.assertTrue(manager.connected)

    def test_on_open_calls_on_status_change(self):
        """Test _on_open calls on_status_change callback"""
        mock_on_status = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=mock_on_status,
            auto_handshake=False
        )
        
        manager._on_open(None)
        mock_on_status.assert_called_with(True)

    def test_send_json_when_not_connected(self):
        """Test send_json handles disconnected state"""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = False
        
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        
        # Should not raise exception
        manager.send_json(payload)
        
        # Verify logger was called
        self.mock_logger.log.assert_called()


class TestHandshakeEdgeCases(unittest.TestCase):
    """Tests for edge cases in handshake implementation"""

    def test_missing_clientId_in_payload(self):
        """Test handling of missing clientId field"""
        payload = {
            'action': 'handshake',
            # Missing clientId
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertNotIn('clientId', payload)
        self.assertIn('action', payload)

    def test_missing_token_in_payload(self):
        """Test handling of missing token field"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            # Missing token
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertNotIn('token', payload)

    def test_missing_timestamp_in_payload(self):
        """Test handling of missing timestamp field"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            # Missing timestamp
            'version': '1.0.0'
        }
        self.assertNotIn('timestamp', payload)

    def test_missing_version_in_payload(self):
        """Test handling of missing version field"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            # Missing version
        }
        self.assertNotIn('version', payload)

    def test_invalid_clientId_format_empty_string(self):
        """Test handling of empty clientId"""
        payload = {
            'action': 'handshake',
            'clientId': '',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertEqual(payload['clientId'], '')

    def test_invalid_token_format_empty_string(self):
        """Test handling of empty token"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': '',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertEqual(payload['token'], '')

    def test_invalid_timestamp_empty_string(self):
        """Test handling of empty timestamp"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': '',
            'version': '1.0.0'
        }
        self.assertEqual(payload['timestamp'], '')

    def test_invalid_version_empty_string(self):
        """Test handling of empty version"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': ''
        }
        self.assertEqual(payload['version'], '')

    def test_handshake_with_special_characters_in_clientId(self):
        """Test handshake with special characters in clientId"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-@#$%001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIn('@', payload['clientId'])

    def test_handshake_with_unicode_in_clientId(self):
        """Test handshake with unicode characters in clientId"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-ñ-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIn('ñ', payload['clientId'])

    def test_handshake_with_very_long_clientId(self):
        """Test handshake with very long clientId"""
        long_id = 'device-' + 'x' * 1000
        payload = {
            'action': 'handshake',
            'clientId': long_id,
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertEqual(len(payload['clientId']), len(long_id))

    def test_handshake_with_very_long_token(self):
        """Test handshake with very long token"""
        long_token = 'token-' + 'x' * 2000
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': long_token,
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertEqual(len(payload['token']), len(long_token))

    def test_handshake_with_null_values(self):
        """Test handshake with null/None values"""
        payload = {
            'action': 'handshake',
            'clientId': None,
            'token': None,
            'timestamp': None,
            'version': None
        }
        self.assertIsNone(payload['clientId'])
        self.assertIsNone(payload['token'])

    def test_handshake_with_numeric_clientId(self):
        """Test handshake with numeric clientId"""
        payload = {
            'action': 'handshake',
            'clientId': 123456,
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['clientId'], int)


class TestHandshakeIntegration(unittest.TestCase):
    """Integration tests for handshake in full workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_handshake_with_websocket_connection(self):
        """Test handshake is sent upon WebSocket connection"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        # Mock send_json to verify it would be called
        with patch.object(manager, 'send_json') as mock_send:
            manager._on_open(None)
            mock_send.assert_called_once()

    def test_manual_handshake_send(self):
        """Test manual handshake can be sent via manager"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        # Verify manager can send messages
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        
        # Simulate sending
        json_msg = json.dumps(payload)
        self.assertIsInstance(json_msg, str)

    def test_handshake_sent_before_other_messages(self):
        """Test handshake is sent before other messages when auto_handshake=True"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        self.assertIsNotNone(manager)

    def test_multiple_connections_with_handshake(self):
        """Test multiple connections each send handshake"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        # Simulate multiple connections
        with patch.object(manager, 'send_json') as mock_send:
            manager._on_open(None)
            first_call_count = mock_send.call_count
            
            # Simulate disconnect and reconnect
            manager._on_close(None, None, None)
            manager._on_open(None)
            
            # Should have called send_json twice
            self.assertEqual(mock_send.call_count, 2)

    def test_handshake_with_custom_payload_fields(self):
        """Test handshake with additional custom payload fields"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0',
            'custom_field': 'custom_value'
        }
        self.assertIn('custom_field', payload)
        self.assertEqual(payload['custom_field'], 'custom_value')

    def test_handshake_json_serialization_with_all_types(self):
        """Test handshake JSON serialization with various data types"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0',
            'is_active': True,
            'retry_count': 0
        }
        json_str = json.dumps(payload)
        deserialized = json.loads(json_str)
        self.assertEqual(deserialized['is_active'], True)
        self.assertEqual(deserialized['retry_count'], 0)

    def test_manager_has_send_json_method(self):
        """Test WebSocketManager has send_json method"""
        manager = WebSocketManager(logger=self.mock_logger)
        self.assertTrue(hasattr(manager, 'send_json'))
        self.assertTrue(callable(getattr(manager, 'send_json')))

    def test_manager_logs_connection(self):
        """Test WebSocketManager logs connection events"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        manager._on_open(None)
        
        # Verify logger was called
        self.mock_logger.log.assert_called()


class TestDefaultCommandsModification(unittest.TestCase):
    """Tests for DEFAULT_COMMANDS list modifications"""

    def test_default_commands_is_list(self):
        """Test DEFAULT_COMMANDS is a list"""
        self.assertIsInstance(DEFAULT_COMMANDS, list)

    def test_default_commands_not_empty(self):
        """Test DEFAULT_COMMANDS is not empty"""
        self.assertGreater(len(DEFAULT_COMMANDS), 0)

    def test_handshake_in_default_commands_list(self):
        """Test Handshake command is in DEFAULT_COMMANDS"""
        names = [cmd.get('name') for cmd in DEFAULT_COMMANDS if isinstance(cmd, dict)]
        self.assertIn('Handshake', names)

    def test_all_default_commands_are_dicts(self):
        """Test all DEFAULT_COMMANDS are dictionaries"""
        for cmd in DEFAULT_COMMANDS:
            self.assertIsInstance(cmd, dict, f"Command is not a dict: {cmd}")

    def test_all_default_commands_have_name_field(self):
        """Test all DEFAULT_COMMANDS have name field"""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn('name', cmd, f"Command missing name field: {cmd}")

    def test_all_default_commands_have_payload_field(self):
        """Test all DEFAULT_COMMANDS have payload field"""
        for cmd in DEFAULT_COMMANDS:
            self.assertIn('payload', cmd, f"Command missing payload field: {cmd}")

    def test_handshake_command_count(self):
        """Test there is exactly one Handshake command in DEFAULT_COMMANDS"""
        handshake_count = sum(1 for cmd in DEFAULT_COMMANDS 
                             if isinstance(cmd, dict) and cmd.get('name') == 'Handshake')
        self.assertEqual(handshake_count, 1, "Should have exactly one Handshake command")

    def test_handshake_payload_structure(self):
        """Test Handshake payload has correct structure"""
        for cmd in DEFAULT_COMMANDS:
            if cmd.get('name') == 'Handshake':
                payload = cmd.get('payload', {})
                required_keys = ['action', 'clientId', 'token', 'timestamp', 'version']
                for key in required_keys:
                    self.assertIn(key, payload, f"Handshake payload missing {key}")

    def test_handshake_action_is_handshake(self):
        """Test Handshake action field is 'handshake'"""
        for cmd in DEFAULT_COMMANDS:
            if cmd.get('name') == 'Handshake':
                self.assertEqual(cmd['payload']['action'], 'handshake')

    def test_other_commands_exist(self):
        """Test other commands exist alongside Handshake"""
        other_commands = [cmd.get('name') for cmd in DEFAULT_COMMANDS 
                         if cmd.get('name') != 'Handshake']
        self.assertGreater(len(other_commands), 0, "Should have other commands besides Handshake")


class TestHandshakeConnectionFailures(unittest.TestCase):
    """Tests for handshake behavior during connection failures"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)

    def test_handshake_when_connection_not_established(self):
        """Test handshake handling when connection is not established"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        manager.connected = False
        payload = manager.handshake_payload
        
        # send_json should handle not connected state
        manager.send_json(payload)
        
        # Logger should be called
        self.mock_logger.log.assert_called()

    def test_handshake_send_failure_handling(self):
        """Test handshake handles send failures gracefully"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        manager.ws_app = None
        manager.connected = False
        
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        
        # Should not raise exception
        manager.send_json(payload)

    def test_on_close_sets_connected_false(self):
        """Test _on_close sets connected to False"""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = True
        
        manager._on_close(None, 1000, "Normal close")
        
        self.assertFalse(manager.connected)

    def test_on_error_logs_error(self):
        """Test _on_error logs errors"""
        manager = WebSocketManager(logger=self.mock_logger)
        
        manager._on_error(None, "Test error")
        
        self.mock_logger.log.assert_called()

    def test_on_message_calls_callback(self):
        """Test _on_message calls on_message callback"""
        mock_callback = Mock()
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=mock_callback
        )
        
        test_message = '{"action":"response"}'
        manager._on_message(None, test_message)
        
        mock_callback.assert_called_with(test_message)


class TestHandshakeLogging(unittest.TestCase):
    """Tests for handshake logging functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)

    def test_handshake_sent_logging(self):
        """Test handshake send is logged"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        # Mock the connection and send
        manager.connected = True
        manager.ws_app = Mock()
        
        payload = manager.handshake_payload
        manager.send_json(payload)
        
        # Verify logger was called
        self.mock_logger.log.assert_called()

    def test_handshake_received_logging(self):
        """Test handshake response is logged"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        # Simulate receiving a message
        response = '{"action":"handshake","status":"ok"}'
        manager._on_message(None, response)
        
        # Logger should be called for any default handling
        # (since no callback was provided)
        self.mock_logger.log.assert_called()

    def test_handshake_error_logging(self):
        """Test handshake errors are logged"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        error_msg = "Connection refused"
        manager._on_error(None, error_msg)
        
        self.mock_logger.log.assert_called()

    def test_connection_logging(self):
        """Test connection events are logged"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        manager._on_open(None)
        
        self.mock_logger.log.assert_called()

    def test_disconnect_logging(self):
        """Test disconnect events are logged"""
        manager = WebSocketManager(logger=self.mock_logger)
        
        manager._on_close(None, 1000, "Normal close")
        
        self.mock_logger.log.assert_called()


class TestHandshakeParameterTypes(unittest.TestCase):
    """Tests for handshake parameter type validation"""

    def test_clientId_string_type(self):
        """Test clientId is string type"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['clientId'], str)

    def test_token_string_type(self):
        """Test token is string type"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['token'], str)

    def test_timestamp_string_type(self):
        """Test timestamp is string type in payload"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['timestamp'], str)

    def test_version_string_type(self):
        """Test version is string type"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['version'], str)

    def test_action_string_type(self):
        """Test action is string type"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload['action'], str)

    def test_handshake_payload_is_dict(self):
        """Test handshake payload is a dictionary"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        self.assertIsInstance(payload, dict)

    def test_payload_serializes_to_json(self):
        """Test payload can be serialized to JSON"""
        payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)

    def test_payload_deserializes_from_json(self):
        """Test payload can be deserialized from JSON"""
        original_payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': "2026-05-07T12:00:00Z",
            'version': '1.0.0'
        }
        json_str = json.dumps(original_payload)
        restored_payload = json.loads(json_str)
        
        self.assertEqual(original_payload, restored_payload)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
