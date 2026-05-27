#!/usr/bin/env python
"""Test script to verify WebSocket Manager handshake integration"""

from ws_client import WebSocketManager

class MockLogger:
    def __init__(self):
        self.messages = []
    
    def log(self, msg):
        self.messages.append(msg)
        print(f"  LOG: {msg}")

# Test 1: Verify WebSocketManager has handshake_handler
logger = MockLogger()
ws_manager = WebSocketManager(logger)
assert hasattr(ws_manager, 'handshake_handler'), "WebSocketManager missing handshake_handler"
print("✓ Test 1 PASSED: WebSocketManager has handshake_handler")

# Test 2: Verify handshake_handler is HandshakeHandler instance
from handshake import HandshakeHandler
assert isinstance(ws_manager.handshake_handler, HandshakeHandler), "handshake_handler is not HandshakeHandler instance"
print("✓ Test 2 PASSED: handshake_handler is proper instance")

# Test 3: Verify update_handshake_config method exists
assert hasattr(ws_manager, 'update_handshake_config'), "Missing update_handshake_config method"
ws_manager.update_handshake_config(token="test-token")
assert any("Handshake config updated" in msg for msg in logger.messages), "Config update not logged"
print("✓ Test 3 PASSED: update_handshake_config method works")

# Test 4: Verify _send_handshake method exists
assert hasattr(ws_manager, '_send_handshake'), "Missing _send_handshake method"
print("✓ Test 4 PASSED: _send_handshake method exists")

# Test 5: Test handshake message building and validation
handshake_msg = ws_manager.handshake_handler.build_handshake_message()
assert handshake_msg is not None, "Failed to build handshake message"
assert handshake_msg["action"] == "handshake", "Invalid action"
print("✓ Test 5 PASSED: Handshake message building works")

# Test 6: Test handshake response handling
ws_manager.handshake_handler._on_handshake_response = lambda x: None
response_json = '{"action": "handshake_ack", "status": "success"}'
ws_manager.handshake_handler.handle_handshake_response(response_json)
assert ws_manager.handshake_handler.handshake_acknowledged, "Handshake not marked as acknowledged"
assert any("Handshake acknowledged" in msg for msg in logger.messages), "Acknowledgment not logged"
print("✓ Test 6 PASSED: Handshake response handling works")

# Test 7: Verify state reset
ws_manager.handshake_handler.reset_for_new_connection()
assert not ws_manager.handshake_handler.handshake_sent, "handshake_sent not reset"
assert not ws_manager.handshake_handler.handshake_acknowledged, "handshake_acknowledged not reset"
print("✓ Test 7 PASSED: State reset works")

print("\n✅ ALL WEBSOCKET MANAGER TESTS PASSED - Handshake integration verified!")
