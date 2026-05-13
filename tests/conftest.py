"""
Shared pytest fixtures and configuration for handshake tests.

This module provides reusable fixtures for WebSocket, handshake payload,
and mocking common dependencies across test suite.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from datetime import datetime


@pytest.fixture
def handshake_payload():
    """Fixture providing a valid handshake payload."""
    return {
        "action": "handshake",
        "clientId": "test-device-001",
        "token": "test-token-12345",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def invalid_handshake_missing_action():
    """Fixture providing handshake with missing action field."""
    return {
        "clientId": "test-device-001",
        "token": "test-token-12345",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def invalid_handshake_missing_clientId():
    """Fixture providing handshake with missing clientId."""
    return {
        "action": "handshake",
        "token": "test-token-12345",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def invalid_handshake_missing_token():
    """Fixture providing handshake with missing token."""
    return {
        "action": "handshake",
        "clientId": "test-device-001",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def invalid_handshake_missing_timestamp():
    """Fixture providing handshake with missing timestamp."""
    return {
        "action": "handshake",
        "clientId": "test-device-001",
        "token": "test-token-12345"
    }


@pytest.fixture
def mock_websocket():
    """Fixture providing a mock WebSocket connection."""
    ws = MagicMock()
    ws.send = MagicMock()
    ws.recv = MagicMock()
    ws.close = MagicMock()
    ws.connected = True
    return ws


@pytest.fixture
def mock_websocket_manager():
    """Fixture providing a mocked WebSocketManager."""
    with patch('ws_client.WebSocketManager') as MockWSManager:
        manager = MagicMock()
        manager.connect = MagicMock(return_value=True)
        manager.disconnect = MagicMock()
        manager.send_message = MagicMock()
        manager.is_connected = MagicMock(return_value=True)
        manager.set_handshake_payload = MagicMock()
        manager.on_message_callback = None
        manager.on_error_callback = None
        manager.on_connect_callback = None
        MockWSManager.return_value = manager
        yield manager


@pytest.fixture
def mock_ui_logger():
    """Fixture providing a mock UI logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture
def default_commands():
    """Fixture providing DEFAULT_COMMANDS structure with handshake."""
    return {
        "handshake": {
            "action": {"type": "string", "value": "handshake"},
            "clientId": {"type": "string", "value": ""},
            "token": {"type": "string", "value": ""},
            "timestamp": {"type": "string", "value": ""}
        },
        "ping": {
            "action": {"type": "string", "value": "ping"}
        },
        "data_transfer": {
            "action": {"type": "string", "value": "data"},
            "payload": {"type": "string", "value": ""}
        }
    }


@pytest.fixture
def mock_logging_module():
    """Fixture providing a mock logging module."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger
