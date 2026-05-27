#!/usr/bin/env python
"""Test script to verify handshake implementation"""

from utilities import DEFAULT_COMMANDS
from handshake_config import HandshakeConfig
from handshake import HandshakeHandler

# Test 1: Verify Handshake is in DEFAULT_COMMANDS
commands = [cmd["name"] for cmd in DEFAULT_COMMANDS]
assert "Handshake" in commands, "Handshake not found in DEFAULT_COMMANDS"
print(f"✓ Test 1 PASSED: Handshake found in DEFAULT_COMMANDS")
print(f"  Available commands: {commands}")

# Test 2: Verify Handshake payload structure
handshake_cmd = next(cmd for cmd in DEFAULT_COMMANDS if cmd["name"] == "Handshake")
payload = handshake_cmd["payload"]
required_fields = ["action", "clientId", "clientVersion", "protocolVersion", "timestamp"]
for field in required_fields:
    assert field in payload, f"Missing field: {field}"
print(f"✓ Test 2 PASSED: Handshake payload has all required fields")
print(f"  Payload: {payload}")

# Test 3: Verify HandshakeConfig validation
config = HandshakeConfig()
is_valid, error = config.validate()
assert is_valid, f"Config validation failed: {error}"
print(f"✓ Test 3 PASSED: HandshakeConfig validation works")

# Test 4: Verify HandshakeHandler initialization
class MockLogger:
    def log(self, msg):
        pass

logger = MockLogger()
handler = HandshakeHandler(logger)
assert handler.config is not None, "HandshakeHandler config not initialized"
assert not handler.handshake_sent, "handshake_sent should be False initially"
print(f"✓ Test 4 PASSED: HandshakeHandler initializes correctly")

# Test 5: Verify handshake payload generation
msg = handler.build_handshake_message()
assert msg is not None, "Failed to build handshake message"
assert msg["action"] == "handshake", "Invalid action in handshake message"
assert "clientId" in msg, "Missing clientId in message"
print(f"✓ Test 5 PASSED: Handshake message generation works")

print("\n✅ ALL TESTS PASSED - Handshake implementation verified!")
