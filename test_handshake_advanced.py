"""
Advanced Integration Tests for SCRUM-64 Handshake Implementation

Tests advanced scenarios and integration with UI and HTTP modules
"""

import unittest
import json
import threading
import time
from unittest.mock import Mock, patch, MagicMock, call, ANY
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ws_client import WebSocketManager
from utilities import DEFAULT_COMMANDS, AppLogger


class TestHandshakeWithUIIntegration(unittest.TestCase):
    """Integration tests with UI module"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_ui_loads_handshake_command(self):
        """Test UI can load Handshake from DEFAULT_COMMANDS"""
        # Find Handshake command in DEFAULT_COMMANDS
        handshake_cmd = None
        for cmd in DEFAULT_COMMANDS:
            if cmd.get('name') == 'Handshake':
                handshake_cmd = cmd
                break
        
        self.assertIsNotNone(handshake_cmd)
        self.assertIn('payload', handshake_cmd)
        payload = handshake_cmd['payload']
        
        # Verify payload can be JSON serialized for display in UI
        json_str = json.dumps(payload, indent=2)
        self.assertIsInstance(json_str, str)

    def test_handshake_payload_in_ui_request_text(self):
        """Test handshake payload can be displayed in UI request text"""
        for cmd in DEFAULT_COMMANDS:
            if cmd.get('name') == 'Handshake':
                payload = cmd['payload']
                # Simulate UI request_text.insert
                ui_text = json.dumps(payload, indent=2)
                self.assertIn('handshake', ui_text)
                self.assertIn('clientId', ui_text)

    def test_websocket_manager_initialized_with_ui_parameters(self):
        """Test WebSocketManager can be initialized with UI parameters"""
        # Simulate UI initialization
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
            auto_handshake=False,  # UI default
            handshake_payload=None
        )
        
        self.assertIsNotNone(manager)
        self.assertEqual(manager.auto_handshake, False)

    def test_websocket_manager_with_ui_enabled_handshake(self):
        """Test WebSocketManager with UI enabling handshake"""
        # Simulate user enabling handshake in UI
        handshake_payload = None
        for cmd in DEFAULT_COMMANDS:
            if cmd.get('name') == 'Handshake':
                handshake_payload = cmd['payload']
                break
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=self.mock_on_message,
            on_status_change=self.mock_on_status_change,
            auto_handshake=True,
            handshake_payload=handshake_payload
        )
        
        self.assertTrue(manager.auto_handshake)
        self.assertEqual(manager.handshake_payload, handshake_payload)


class TestHandshakeWithCustomPayloads(unittest.TestCase):
    """Tests for custom handshake payloads"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)

    def test_handshake_with_modified_clientId(self):
        """Test handshake with modified clientId"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'custom-device-123',
            'token': 'default-token',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True,
            handshake_payload=custom_payload
        )
        
        self.assertEqual(manager.handshake_payload['clientId'], 'custom-device-123')

    def test_handshake_with_modified_token(self):
        """Test handshake with modified token"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'iot-device-001',
            'token': 'custom-secret-token-xyz',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            handshake_payload=custom_payload
        )
        
        self.assertEqual(manager.handshake_payload['token'], 'custom-secret-token-xyz')

    def test_handshake_with_modified_version(self):
        """Test handshake with modified version"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'iot-device-001',
            'token': 'default-token',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '2.0.0'
        }
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            handshake_payload=custom_payload
        )
        
        self.assertEqual(manager.handshake_payload['version'], '2.0.0')

    def test_handshake_with_all_custom_fields(self):
        """Test handshake with all fields customized"""
        custom_payload = {
            'action': 'handshake',
            'clientId': 'prod-device-001',
            'token': 'prod-token-secure',
            'timestamp': '2026-05-08T10:30:00Z',
            'version': '3.0.0'
        }
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            handshake_payload=custom_payload
        )
        
        self.assertEqual(manager.handshake_payload, custom_payload)


class TestHandshakeMessageFlow(unittest.TestCase):
    """Tests for handshake message flow in WebSocket lifecycle"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)
        self.mock_on_message = Mock()
        self.mock_on_status_change = Mock()

    def test_handshake_only_on_open(self):
        """Test handshake is only sent in _on_open"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        with patch.object(manager, 'send_json') as mock_send:
            # Simulate _on_open
            manager._on_open(None)
            self.assertEqual(mock_send.call_count, 1)
            
            # _on_message should not send handshake
            mock_send.reset_mock()
            manager._on_message(None, '{"test":"message"}')
            self.assertEqual(mock_send.call_count, 0)

    def test_handshake_not_sent_on_close(self):
        """Test handshake is not sent on close"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        manager.connected = True
        with patch.object(manager, 'send_json') as mock_send:
            # Simulate _on_close
            manager._on_close(None, 1000, "Normal close")
            self.assertEqual(mock_send.call_count, 0)
            self.assertFalse(manager.connected)

    def test_handshake_not_sent_on_error(self):
        """Test handshake is not sent on error"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        with patch.object(manager, 'send_json') as mock_send:
            # Simulate _on_error
            manager._on_error(None, "Connection error")
            self.assertEqual(mock_send.call_count, 0)

    def test_connection_status_callback_before_handshake(self):
        """Test on_status_change is called before handshake send"""
        call_order = []
        
        def track_status_change(status):
            call_order.append(('status_change', status))
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=track_status_change,
            auto_handshake=True
        )
        
        with patch.object(manager, 'send_json') as mock_send:
            def track_send(payload):
                call_order.append(('send_json', payload.get('action')))
            
            mock_send.side_effect = track_send
            manager._on_open(None)
            
            # Status change should be called first
            self.assertTrue(len(call_order) > 0)
            self.assertEqual(call_order[0][0], 'status_change')


class TestHandshakeConcurrency(unittest.TestCase):
    """Tests for handshake with concurrent operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)

    def test_handshake_payload_not_modified_by_send(self):
        """Test handshake payload is not modified during send"""
        original_payload = {
            'action': 'handshake',
            'clientId': 'device-001',
            'token': 'token-xyz',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        payload_copy = original_payload.copy()
        
        manager = WebSocketManager(
            logger=self.mock_logger,
            handshake_payload=original_payload
        )
        
        # Simulate sending
        manager.connected = True
        manager.ws_app = Mock()
        manager.send_json(manager.handshake_payload)
        
        # Verify original payload unchanged
        self.assertEqual(original_payload, payload_copy)

    def test_multiple_handshake_instances_independent(self):
        """Test multiple WebSocketManager instances don't share state"""
        manager1 = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=True
        )
        
        manager2 = WebSocketManager(
            logger=self.mock_logger,
            auto_handshake=False
        )
        
        self.assertTrue(manager1.auto_handshake)
        self.assertFalse(manager2.auto_handshake)
        
        # Modifying one shouldn't affect the other
        manager1.auto_handshake = False
        self.assertFalse(manager1.auto_handshake)
        self.assertFalse(manager2.auto_handshake)


class TestHandshakeErrorRecovery(unittest.TestCase):
    """Tests for error handling and recovery in handshake"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_logger = Mock(spec=AppLogger)

    def test_send_json_with_invalid_payload(self):
        """Test send_json handles invalid JSON gracefully"""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = True
        manager.ws_app = Mock()
        
        # Create non-serializable object
        class NonSerializable:
            pass
        
        payload = {
            'action': 'handshake',
            'data': NonSerializable()  # This will fail JSON serialization
        }
        
        # Should handle error gracefully
        manager.send_json(payload)
        self.mock_logger.log.assert_called()

    def test_websocket_app_none_handling(self):
        """Test send_json when ws_app is None"""
        manager = WebSocketManager(logger=self.mock_logger)
        manager.connected = True
        manager.ws_app = None
        
        payload = {
            'action': 'handshake',
            'clientId': 'device-001'
        }
        
        # Should not raise exception
        manager.send_json(payload)
        self.mock_logger.log.assert_called()

    def test_on_message_without_callback(self):
        """Test _on_message when no callback provided"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_message=None  # No callback
        )
        
        message = '{"action":"response"}'
        # Should not raise exception
        manager._on_message(None, message)
        self.mock_logger.log.assert_called()

    def test_on_status_change_without_callback(self):
        """Test _set_connected when no callback provided"""
        manager = WebSocketManager(
            logger=self.mock_logger,
            on_status_change=None  # No callback
        )
        
        # Should not raise exception
        manager._set_connected(True)
        self.assertTrue(manager.connected)


class TestHandshakeValidation(unittest.TestCase):
    """Tests for handshake payload validation"""

    def test_payload_all_fields_present(self):
        """Test complete handshake payload has all required fields"""
        payload = {
            'action': 'handshake',
            'clientId': 'iot-device-001',
            'token': 'default-token',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        required_fields = ['action', 'clientId', 'token', 'timestamp', 'version']
        for field in required_fields:
            self.assertIn(field, payload)

    def test_payload_action_is_lowercase(self):
        """Test action field is lowercase 'handshake'"""
        payload = {
            'action': 'handshake',
            'clientId': 'iot-device-001',
            'token': 'default-token',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        self.assertEqual(payload['action'], 'handshake')
        self.assertNotEqual(payload['action'], 'Handshake')

    def test_payload_fields_not_empty(self):
        """Test payload fields have content"""
        payload = {
            'action': 'handshake',
            'clientId': 'iot-device-001',
            'token': 'default-token',
            'timestamp': '2026-05-07T00:00:00Z',
            'version': '1.0'
        }
        
        for key, value in payload.items():
            if key != 'action':  # action is checked separately
                self.assertTrue(len(str(value)) > 0, f"{key} is empty")


class TestHandshakeDefaultValues(unittest.TestCase):
    """Tests for default handshake values"""

    def test_default_handshake_payload_structure(self):
        """Test default handshake payload has correct structure"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        # Verify default payload structure
        self.assertIn('action', manager.handshake_payload)
        self.assertIn('clientId', manager.handshake_payload)
        self.assertIn('token', manager.handshake_payload)
        self.assertIn('timestamp', manager.handshake_payload)
        self.assertIn('version', manager.handshake_payload)

    def test_default_action_value(self):
        """Test default action is 'handshake'"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        self.assertEqual(manager.handshake_payload['action'], 'handshake')

    def test_default_clientId_not_empty(self):
        """Test default clientId is not empty"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        self.assertGreater(len(manager.handshake_payload['clientId']), 0)

    def test_default_token_not_empty(self):
        """Test default token is not empty"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        self.assertGreater(len(manager.handshake_payload['token']), 0)

    def test_default_timestamp_not_empty(self):
        """Test default timestamp is not empty"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        self.assertGreater(len(manager.handshake_payload['timestamp']), 0)

    def test_default_version_not_empty(self):
        """Test default version is not empty"""
        mock_logger = Mock(spec=AppLogger)
        manager = WebSocketManager(logger=mock_logger)
        
        self.assertGreater(len(manager.handshake_payload['version']), 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
