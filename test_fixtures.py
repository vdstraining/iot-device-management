#!/usr/bin/env python3
"""
Test fixtures and mock data for SCRUM-107 handshake tests.

Provides:
- Mock configurations
- Test data files
- Common test utilities
- Fixture builders
"""

import json
import tempfile
import os
from typing import Dict, Any


# ============================================================================
# MOCK CONFIGURATIONS
# ============================================================================

MOCK_CONFIG_VALID = {
    "enabled": True,
    "auto_trigger": True,
    "clientId": "test-device-001",
    "capabilities": [
        "websocket",
        "http",
        "json-messaging",
        "command-execution",
    ],
    "session_metadata": {
        "version": "1.0",
        "application": "IoT Device Simulator",
        "platform": "Tkinter",
    },
    "authentication_context": {
        "auth_type": "bearer",
        "token": "test-token-123",
    },
}

MOCK_CONFIG_MINIMAL = {
    "enabled": True,
    "auto_trigger": True,
}

MOCK_CONFIG_DISABLED = {
    "enabled": False,
    "auto_trigger": False,
}

MOCK_CONFIG_NO_AUTO_TRIGGER = {
    "enabled": True,
    "auto_trigger": False,
}

MOCK_CONFIG_CUSTOM_CLIENT = {
    "clientId": "custom-device-999",
    "capabilities": ["websocket"],
    "enabled": True,
}


# ============================================================================
# MOCK RESPONSES
# ============================================================================

MOCK_RESPONSE_HANDSHAKE_SUCCESS = {
    "action": "handshake_ack",
    "status": "success",
    "sessionId": "sess-abc123def456",
    "message": "Handshake successful",
}

MOCK_RESPONSE_HANDSHAKE_ERROR = {
    "action": "handshake_ack",
    "status": "error",
    "error_code": "AUTH_FAILED",
    "message": "Authentication failed",
}

MOCK_RESPONSE_HANDSHAKE_TIMEOUT = None  # Simulates timeout

MOCK_RESPONSE_INVALID_JSON = "{ invalid json }"

MOCK_RESPONSE_EMPTY = ""

MOCK_RESPONSE_MALFORMED = {
    "action": "handshake_ack",
    # Missing required fields
}


# ============================================================================
# MOCK PAYLOADS
# ============================================================================

MOCK_HANDSHAKE_PAYLOAD = {
    "action": "handshake",
    "clientId": "test-device-001",
    "capabilities": [
        "websocket",
        "http",
        "json-messaging",
        "command-execution",
    ],
    "session_metadata": {
        "version": "1.0",
        "application": "IoT Device Simulator",
        "platform": "Tkinter",
    },
    "authentication_context": {
        "auth_type": "bearer",
        "token": "",
    },
}

MOCK_HANDSHAKE_PAYLOAD_WITH_TOKEN = {
    "action": "handshake",
    "clientId": "test-device-001",
    "capabilities": ["websocket", "http"],
    "session_metadata": {"version": "1.0"},
    "authentication_context": {
        "auth_type": "jwt",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    },
}

MOCK_HANDSHAKE_PAYLOAD_MINIMAL = {
    "action": "handshake",
    "clientId": "device-001",
}


# ============================================================================
# TEST CONFIGURATION FILES
# ============================================================================

class ConfigFileBuilder:
    """Builder for creating temporary config files for testing."""

    @staticmethod
    def create_config_file(data: Dict[str, Any]) -> str:
        """
        Create a temporary JSON config file.
        
        Args:
            data: Dictionary to save as JSON
            
        Returns:
            Path to the temporary file
        """
        tmpdir = tempfile.gettempdir()
        config_path = os.path.join(tmpdir, "test_handshake_config.json")
        
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return config_path

    @staticmethod
    def create_valid_config_file() -> str:
        """Create a valid handshake config file."""
        return ConfigFileBuilder.create_config_file(MOCK_CONFIG_VALID)

    @staticmethod
    def create_minimal_config_file() -> str:
        """Create a minimal handshake config file."""
        return ConfigFileBuilder.create_config_file(MOCK_CONFIG_MINIMAL)

    @staticmethod
    def create_invalid_json_file() -> str:
        """Create a file with invalid JSON."""
        tmpdir = tempfile.gettempdir()
        config_path = os.path.join(tmpdir, "test_invalid.json")
        
        with open(config_path, "w") as f:
            f.write("{ invalid json content }")
        
        return config_path

    @staticmethod
    def cleanup_file(path: str) -> None:
        """Remove temporary config file."""
        if os.path.exists(path):
            os.remove(path)


# ============================================================================
# LOG CAPTURE UTILITY
# ============================================================================

class LogCapture:
    """Utility to capture logs for testing."""

    def __init__(self):
        self.logs = []

    def callback(self, message: str) -> None:
        """Capture log message."""
        self.logs.append(message)

    def clear(self) -> None:
        """Clear captured logs."""
        self.logs.clear()

    def get_logs(self) -> list:
        """Get all captured logs."""
        return self.logs.copy()

    def get_log_text(self) -> str:
        """Get logs as single text."""
        return "".join(self.logs)

    def has_log_containing(self, text: str) -> bool:
        """Check if any log contains text."""
        return any(text.lower() in log.lower() for log in self.logs)

    def get_logs_containing(self, text: str) -> list:
        """Get logs containing specific text."""
        return [log for log in self.logs if text.lower() in log.lower()]

    def count_logs(self) -> int:
        """Get number of captured logs."""
        return len(self.logs)


# ============================================================================
# MESSAGE BUILDER UTILITIES
# ============================================================================

class MessageBuilder:
    """Utility to build test messages."""

    @staticmethod
    def build_handshake_message(
        clientId: str = "device-001",
        capabilities: list = None,
        auth_type: str = "bearer",
        token: str = "",
    ) -> dict:
        """Build a handshake message."""
        if capabilities is None:
            capabilities = ["websocket"]

        return {
            "action": "handshake",
            "clientId": clientId,
            "capabilities": capabilities,
            "session_metadata": {
                "version": "1.0",
                "application": "Test",
            },
            "authentication_context": {
                "auth_type": auth_type,
                "token": token,
            },
        }

    @staticmethod
    def build_response_message(
        action: str = "handshake_ack",
        status: str = "success",
        **kwargs
    ) -> dict:
        """Build a response message."""
        msg = {
            "action": action,
            "status": status,
        }
        msg.update(kwargs)
        return msg

    @staticmethod
    def to_json_string(payload: dict) -> str:
        """Convert payload to JSON string."""
        return json.dumps(payload)


# ============================================================================
# MOCK WEBSOCKET UTILITIES
# ============================================================================

class MockWebSocketApp:
    """Mock WebSocket app for testing."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.close_status_code = None
        self.close_message = None
        self.on_open_callback = None
        self.on_message_callback = None
        self.on_error_callback = None
        self.on_close_callback = None

    def send(self, message: str) -> None:
        """Mock send method."""
        self.sent_messages.append(message)

    def close(self) -> None:
        """Mock close method."""
        self.closed = True

    def simulate_open(self) -> None:
        """Simulate connection open."""
        if self.on_open_callback:
            self.on_open_callback(self)

    def simulate_message(self, message: str) -> None:
        """Simulate receiving a message."""
        if self.on_message_callback:
            self.on_message_callback(self, message)

    def simulate_error(self, error) -> None:
        """Simulate an error."""
        if self.on_error_callback:
            self.on_error_callback(self, error)

    def simulate_close(self, code: int = 1000, msg: str = "Normal close") -> None:
        """Simulate connection close."""
        self.close_status_code = code
        self.close_message = msg
        if self.on_close_callback:
            self.on_close_callback(self, code, msg)

    def get_sent_messages(self) -> list:
        """Get all sent messages."""
        return self.sent_messages.copy()

    def get_sent_message_count(self) -> int:
        """Get count of sent messages."""
        return len(self.sent_messages)

    def get_last_sent_message(self) -> str:
        """Get the last sent message."""
        return self.sent_messages[-1] if self.sent_messages else None


# ============================================================================
# SCENARIO BUILDERS
# ============================================================================

class ScenarioBuilder:
    """Build common test scenarios."""

    @staticmethod
    def scenario_handshake_auto_trigger():
        """Scenario: Handshake auto-triggers on connection."""
        return {
            "name": "Auto-trigger Handshake",
            "config": MOCK_CONFIG_VALID,
            "expected_auto_trigger": True,
        }

    @staticmethod
    def scenario_handshake_disabled():
        """Scenario: Handshake disabled."""
        return {
            "name": "Handshake Disabled",
            "config": MOCK_CONFIG_DISABLED,
            "expected_auto_trigger": False,
        }

    @staticmethod
    def scenario_handshake_manual():
        """Scenario: Manual handshake trigger."""
        return {
            "name": "Manual Handshake",
            "config": MOCK_CONFIG_NO_AUTO_TRIGGER,
            "expected_auto_trigger": False,
            "manual_trigger": True,
        }

    @staticmethod
    def scenario_success_response():
        """Scenario: Successful handshake response."""
        return {
            "name": "Success Response",
            "response": MOCK_RESPONSE_HANDSHAKE_SUCCESS,
            "expected_status": "success",
        }

    @staticmethod
    def scenario_error_response():
        """Scenario: Error in handshake response."""
        return {
            "name": "Error Response",
            "response": MOCK_RESPONSE_HANDSHAKE_ERROR,
            "expected_status": "error",
        }


# ============================================================================
# ASSERTION HELPERS
# ============================================================================

class HandshakeAssertions:
    """Common assertions for handshake tests."""

    @staticmethod
    def assert_valid_handshake_payload(payload: dict) -> None:
        """Assert that payload is a valid handshake message."""
        assert isinstance(payload, dict)
        assert payload.get("action") == "handshake"
        assert "clientId" in payload
        assert "capabilities" in payload
        assert isinstance(payload["capabilities"], list)

    @staticmethod
    def assert_valid_response(response: dict) -> None:
        """Assert that response is valid."""
        assert isinstance(response, dict)
        assert "action" in response
        assert "status" in response

    @staticmethod
    def assert_config_has_required_fields(config: dict) -> None:
        """Assert that config has all required fields."""
        required = [
            "enabled",
            "auto_trigger",
            "clientId",
            "capabilities",
        ]
        for field in required:
            assert field in config, f"Missing required field: {field}"

    @staticmethod
    def assert_payload_json_serializable(payload: dict) -> None:
        """Assert that payload can be serialized to JSON."""
        json_str = json.dumps(payload)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # Verify it can be deserialized
        restored = json.loads(json_str)
        assert restored.get("action") == "handshake"
