"""Pytest configuration and shared fixtures for IoT Device Management tests."""

import json
from unittest.mock import MagicMock, Mock, patch
import pytest


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = MagicMock()
    logger.log = MagicMock()
    logger.callback = MagicMock()
    return logger


@pytest.fixture
def handshake_payload():
    """Provide a valid handshake payload for testing."""
    return {
        "action": "handshake",
        "clientId": "client-001",
        "capabilities": ["websocket", "messages"],
        "sessionMetadata": {
            "platform": "python-tkinter",
            "version": "1.0",
        },
        "token": "replace-me",
    }


@pytest.fixture
def minimal_handshake_payload():
    """Provide a minimal valid handshake payload with only required fields."""
    return {
        "action": "handshake",
        "clientId": "client-001",
        "capabilities": ["websocket"],
    }


@pytest.fixture
def invalid_handshake_payloads():
    """Provide various invalid handshake payloads for error testing."""
    return {
        "missing_action": {
            "clientId": "client-001",
            "capabilities": ["websocket"],
        },
        "missing_clientId": {
            "action": "handshake",
            "capabilities": ["websocket"],
        },
        "missing_capabilities": {
            "action": "handshake",
            "clientId": "client-001",
        },
        "wrong_action_type": {
            "action": 123,
            "clientId": "client-001",
            "capabilities": ["websocket"],
        },
        "wrong_clientId_type": {
            "action": "handshake",
            "clientId": 123,
            "capabilities": ["websocket"],
        },
        "wrong_capabilities_type": {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": "websocket",
        },
        "capabilities_empty_list": {
            "action": "handshake",
            "clientId": "client-001",
            "capabilities": [],
        },
        "invalid_action_value": {
            "action": "invalid_action",
            "clientId": "client-001",
            "capabilities": ["websocket"],
        },
    }


@pytest.fixture
def mock_ws_manager(mock_logger):
    """Create a mock WebSocket manager for testing."""
    from ws_client import WebSocketManager

    ws_manager = Mock(spec=WebSocketManager)
    ws_manager.logger = mock_logger
    ws_manager.connected = False
    ws_manager.send_json = MagicMock()
    ws_manager.connect = MagicMock()
    ws_manager.disconnect = MagicMock()
    return ws_manager


@pytest.fixture
def real_ws_manager_with_mocked_ws(mock_logger):
    """Create a real WebSocketManager instance with mocked WebSocket."""
    from ws_client import WebSocketManager
    
    ws_manager = WebSocketManager(logger=mock_logger)
    ws_manager.connected = True
    ws_manager.ws_app = MagicMock()
    return ws_manager


@pytest.fixture
def mock_http_client(mock_logger):
    """Create a mock HTTP client for testing."""
    from http_client import HttpClient

    http_client = Mock(spec=HttpClient)
    http_client.logger = mock_logger
    http_client.send_request = MagicMock()
    return http_client


@pytest.fixture
def default_commands_fixture():
    """Provide the DEFAULT_COMMANDS list for testing."""
    from utilities import DEFAULT_COMMANDS
    return DEFAULT_COMMANDS
