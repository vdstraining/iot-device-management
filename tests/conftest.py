"""Pytest configuration and shared fixtures."""
import pytest
import sys
import os
from unittest.mock import Mock

# Add parent directory to path so we can import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.log = Mock()
    return logger


@pytest.fixture
def valid_handshake_payload():
    """Create a valid handshake payload."""
    return {
        "type": "handshake",
        "clientId": "test-client",
        "version": "1.0",
        "token": "test-token",
    }


@pytest.fixture
def valid_handshake_payload_no_token():
    """Create a valid handshake payload without token field (minimal)."""
    return {
        "type": "handshake",
        "clientId": "test-client",
        "version": "1.0",
    }


@pytest.fixture
def valid_handshake_response():
    """Create a valid handshake response message."""
    return {
        "type": "handshake",
        "status": "success",
        "sessionId": "sess-123",
    }


@pytest.fixture
def mock_callback():
    """Create a mock callback function."""
    return Mock()
