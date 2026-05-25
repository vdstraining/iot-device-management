#!/usr/bin/env python3
"""
Pytest configuration and fixtures for SCRUM-107 handshake tests.

This module provides:
- Pytest fixtures for common test scenarios
- Mock objects and builders
- Configuration loaders
- Custom assertions
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock
from pathlib import Path

from test_fixtures import (
    LogCapture,
    MockWebSocketApp,
    MessageBuilder,
    ConfigFileBuilder,
    MOCK_CONFIG_VALID,
    MOCK_CONFIG_DISABLED,
    MOCK_CONFIG_MINIMAL,
)
from utilities import AppLogger, load_handshake_config
from ws_client import WebSocketManager


# ============================================================================
# LOGGER FIXTURES
# ============================================================================

@pytest.fixture
def log_capture():
    """Fixture providing log capture utility."""
    return LogCapture()


@pytest.fixture
def app_logger(log_capture):
    """Fixture providing AppLogger with log capture."""
    return AppLogger(log_capture.callback)


# ============================================================================
# WEBSOCKET MANAGER FIXTURES
# ============================================================================

@pytest.fixture
def ws_manager_with_config(app_logger):
    """Fixture providing WebSocketManager with valid config."""
    return WebSocketManager(
        logger=app_logger,
        handshake_config=MOCK_CONFIG_VALID,
    )


@pytest.fixture
def ws_manager_disabled(app_logger):
    """Fixture providing WebSocketManager with disabled config."""
    return WebSocketManager(
        logger=app_logger,
        handshake_config=MOCK_CONFIG_DISABLED,
    )


@pytest.fixture
def ws_manager_minimal(app_logger):
    """Fixture providing WebSocketManager with minimal config."""
    return WebSocketManager(
        logger=app_logger,
        handshake_config=MOCK_CONFIG_MINIMAL,
    )


@pytest.fixture
def ws_manager_no_config(app_logger):
    """Fixture providing WebSocketManager without config."""
    return WebSocketManager(logger=app_logger)


# ============================================================================
# MOCK WEBSOCKET FIXTURES
# ============================================================================

@pytest.fixture
def mock_websocket():
    """Fixture providing mock WebSocket app."""
    return MockWebSocketApp()


@pytest.fixture
def connected_ws_manager(ws_manager_with_config, mock_websocket):
    """Fixture providing connected WebSocketManager."""
    ws_manager_with_config.ws_app = mock_websocket
    ws_manager_with_config.connected = True
    return ws_manager_with_config


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture
def temp_config_file():
    """Fixture providing temporary config file."""
    tmpdir = tempfile.gettempdir()
    config_path = os.path.join(tmpdir, "test_config.json")
    
    yield config_path
    
    # Cleanup
    if os.path.exists(config_path):
        os.remove(config_path)


@pytest.fixture
def config_valid():
    """Fixture providing valid config."""
    return MOCK_CONFIG_VALID.copy()


@pytest.fixture
def config_disabled():
    """Fixture providing disabled config."""
    return MOCK_CONFIG_DISABLED.copy()


@pytest.fixture
def config_minimal():
    """Fixture providing minimal config."""
    return MOCK_CONFIG_MINIMAL.copy()


# ============================================================================
# MESSAGE FIXTURES
# ============================================================================

@pytest.fixture
def handshake_message():
    """Fixture providing handshake message."""
    return MessageBuilder.build_handshake_message()


@pytest.fixture
def success_response():
    """Fixture providing success response."""
    return MessageBuilder.build_response_message(
        action="handshake_ack",
        status="success",
        sessionId="sess-test-123",
    )


@pytest.fixture
def error_response():
    """Fixture providing error response."""
    return MessageBuilder.build_response_message(
        action="handshake_ack",
        status="error",
        error_code="AUTH_FAILED",
        message="Authentication failed",
    )


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def test_data_dir():
    """Fixture providing path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def load_test_config(test_data_dir):
    """Fixture providing function to load test configs."""
    def _load(filename):
        config_path = test_data_dir / filename
        with open(config_path, 'r') as f:
            return json.load(f)
    return _load


@pytest.fixture
def load_test_response(test_data_dir):
    """Fixture providing function to load test responses."""
    def _load(filename):
        response_path = test_data_dir / filename
        try:
            with open(response_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            with open(response_path, 'r') as f:
                return f.read()  # Return raw content for invalid JSON
    return _load


# ============================================================================
# CALLBACK FIXTURES
# ============================================================================

@pytest.fixture
def message_callback():
    """Fixture providing message callback mock."""
    callback = Mock()
    callback.received_messages = []
    
    def record_message(msg):
        callback.received_messages.append(msg)
    
    callback.side_effect = record_message
    return callback


@pytest.fixture
def status_callback():
    """Fixture providing status callback mock."""
    callback = Mock()
    callback.status_changes = []
    
    def record_status(status):
        callback.status_changes.append(status)
    
    callback.side_effect = record_status
    return callback


# ============================================================================
# COMBINED FIXTURES
# ============================================================================

@pytest.fixture
def ws_manager_with_callbacks(app_logger, message_callback, status_callback):
    """Fixture providing WebSocketManager with callbacks."""
    return WebSocketManager(
        logger=app_logger,
        on_message=message_callback,
        on_status_change=status_callback,
        handshake_config=MOCK_CONFIG_VALID,
    )


# ============================================================================
# PARAMETRIZED FIXTURES
# ============================================================================

@pytest.fixture(params=[
    MOCK_CONFIG_VALID,
    MOCK_CONFIG_MINIMAL,
])
def various_configs(request):
    """Fixture providing various configurations for parametrized tests."""
    return request.param


# ============================================================================
# PYTEST HOOKS AND CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers",
        "handshake: mark test as related to handshake functionality"
    )


# ============================================================================
# CUSTOM ASSERTIONS HELPER
# ============================================================================

class HandshakeTestHelper:
    """Helper class for common test operations."""

    @staticmethod
    def create_mock_logger():
        """Create a mock logger with log capture."""
        log_capture = LogCapture()
        return AppLogger(log_capture.callback), log_capture

    @staticmethod
    def simulate_connection(ws_manager, mock_ws):
        """Simulate WebSocket connection."""
        ws_manager.ws_app = mock_ws
        ws_manager.connected = False
        ws_manager._on_open(None)

    @staticmethod
    def simulate_message_received(ws_manager, message):
        """Simulate receiving a message."""
        if isinstance(message, dict):
            message = json.dumps(message)
        ws_manager._on_message(None, message)

    @staticmethod
    def simulate_error(ws_manager, error):
        """Simulate WebSocket error."""
        ws_manager._on_error(None, error)

    @staticmethod
    def simulate_close(ws_manager, code=1000, msg="Normal close"):
        """Simulate WebSocket close."""
        ws_manager._on_close(None, code, msg)

    @staticmethod
    def assert_handshake_sent(ws_app):
        """Assert that handshake was sent."""
        assert len(ws_app.sent_messages) > 0
        last_msg = ws_app.sent_messages[-1]
        payload = json.loads(last_msg)
        assert payload.get("action") == "handshake"

    @staticmethod
    def assert_handshake_not_sent(ws_app):
        """Assert that handshake was NOT sent."""
        if len(ws_app.sent_messages) > 0:
            for msg in ws_app.sent_messages:
                payload = json.loads(msg)
                assert payload.get("action") != "handshake"


@pytest.fixture
def helper():
    """Fixture providing test helper."""
    return HandshakeTestHelper()


# ============================================================================
# ENVIRONMENT FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Auto-cleanup temporary files after tests."""
    yield
    # Cleanup happens automatically with temp directories
