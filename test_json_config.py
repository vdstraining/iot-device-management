#!/usr/bin/env python
"""Verify default_commands.json is valid"""

import json

try:
    with open('default_commands.json', 'r') as f:
        data = json.load(f)
    
    print(f"✓ Valid JSON with {len(data)} commands")
    print(f"  Commands: {[cmd['name'] for cmd in data]}")
    
    # Verify Handshake is present
    commands = [cmd['name'] for cmd in data]
    assert 'Handshake' in commands, "Handshake not found in JSON"
    print("✓ Handshake command present in JSON")
    
    # Verify Handshake structure
    handshake = next(cmd for cmd in data if cmd['name'] == 'Handshake')
    payload = handshake['payload']
    required = ['action', 'clientId', 'clientVersion', 'protocolVersion', 'timestamp']
    for field in required:
        assert field in payload, f"Missing field: {field}"
    print("✓ Handshake payload structure valid")
    
except Exception as e:
    print(f"✗ Error: {e}")
    exit(1)

print("\n✅ default_commands.json validation passed!")
