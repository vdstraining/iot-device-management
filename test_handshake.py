#!/usr/bin/env python3
"""Test script to validate the handshake mechanism implementation."""

from utilities import load_handshake_config, DEFAULT_COMMANDS
import json

def test_handshake_config():
    """Test 1: Load handshake config"""
    config = load_handshake_config()
    print('Test 1 - Load handshake config:')
    print(f'  Enabled: {config.get("enabled")}')
    print(f'  Auto-trigger: {config.get("auto_trigger")}')
    print(f'  ClientId: {config.get("clientId")}')
    print(f'  Capabilities: {len(config.get("capabilities", []))} items')
    assert config.get("enabled") == True, "Handshake should be enabled"
    assert config.get("auto_trigger") == True, "Auto-trigger should be enabled"
    print('  ✓ PASS')
    print()

def test_default_commands():
    """Test 2: Check Handshake in DEFAULT_COMMANDS"""
    print('Test 2 - Handshake in DEFAULT_COMMANDS:')
    handshake_cmd = DEFAULT_COMMANDS[0]
    print(f'  Command name: {handshake_cmd["name"]}')
    print(f'  Payload action: {handshake_cmd["payload"].get("action")}')
    print(f'  Has clientId: {"clientId" in handshake_cmd["payload"]}')
    print(f'  Has capabilities: {"capabilities" in handshake_cmd["payload"]}')
    print(f'  Has authentication_context: {"authentication_context" in handshake_cmd["payload"]}')
    assert handshake_cmd["name"] == "Handshake", "First command should be Handshake"
    assert handshake_cmd["payload"].get("action") == "handshake", "Action should be handshake"
    assert "clientId" in handshake_cmd["payload"], "Should have clientId"
    assert "capabilities" in handshake_cmd["payload"], "Should have capabilities"
    assert "authentication_context" in handshake_cmd["payload"], "Should have authentication_context"
    print('  ✓ PASS')
    print()

def test_config_file():
    """Test 3: Verify handshake config JSON file"""
    with open('handshake_config.json', 'r') as f:
        file_config = json.load(f)
    print('Test 3 - handshake_config.json file:')
    print(f'  File loaded successfully')
    print(f'  Enabled: {file_config.get("enabled")}')
    print(f'  Auto-trigger: {file_config.get("auto_trigger")}')
    assert file_config.get("enabled") == True, "File config should be enabled"
    assert file_config.get("auto_trigger") == True, "File config auto-trigger should be enabled"
    print('  ✓ PASS')
    print()

def test_websocket_manager():
    """Test 4: Verify WebSocketManager accepts handshake_config"""
    from utilities import AppLogger
    from ws_client import WebSocketManager
    
    print('Test 4 - WebSocketManager initialization:')
    
    # Mock logger
    logs = []
    def mock_log(msg):
        logs.append(msg)
    
    logger = AppLogger(mock_log)
    config = load_handshake_config()
    
    # Initialize WebSocketManager with handshake_config
    ws_manager = WebSocketManager(
        logger=logger,
        handshake_config=config
    )
    
    print(f'  WebSocketManager created')
    print(f'  Has handshake_config: {bool(ws_manager.handshake_config)}')
    print(f'  Can build handshake payload: {ws_manager._build_handshake_payload() is not None}')
    
    payload = ws_manager._build_handshake_payload()
    assert payload is not None, "Should build handshake payload"
    assert payload["action"] == "handshake", "Payload action should be handshake"
    assert "clientId" in payload, "Payload should have clientId"
    print('  ✓ PASS')
    print()

if __name__ == "__main__":
    try:
        test_handshake_config()
        test_default_commands()
        test_config_file()
        test_websocket_manager()
        print('✓ All validation tests passed!')
    except AssertionError as e:
        print(f'✗ Test failed: {e}')
        exit(1)
    except Exception as e:
        print(f'✗ Unexpected error: {e}')
        import traceback
        traceback.print_exc()
        exit(1)
