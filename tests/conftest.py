"""
Pytest configuration and shared fixtures for SCRUM-53 tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Add parent directory to path so we can import application modules
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture
def mock_logger():
    """Fixture that provides a mock logger."""
    return MagicMock()


@pytest.fixture
def mock_websocket_app():
    """Fixture that provides a mock WebSocket app."""
    return MagicMock()


@pytest.fixture
def mock_callbacks():
    """Fixture that provides mock callbacks."""
    return {
        "on_message": MagicMock(),
        "on_status_change": MagicMock(),
    }


@pytest.fixture
def websocket_manager(mock_logger):
    """Fixture that provides a WebSocketManager instance with mocks."""
    from ws_client import WebSocketManager
    
    manager = WebSocketManager(
        logger=mock_logger,
        client_id="test-device-001"
    )
    manager.ws_app = MagicMock()
    return manager


@pytest.fixture
def app_logger_instance(mock_logger):
    """Fixture that provides an AppLogger instance with mock callback."""
    from utilities import AppLogger
    
    def mock_callback(message):
        pass
    
    return AppLogger(mock_callback)
