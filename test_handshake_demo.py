#!/usr/bin/env python3
"""
Demo and test file for SCRUM-81 Handshake functionality.

This demonstrates how to use the new handshake message functionality
in the IoT device management client.
"""

import json
from datetime import datetime


def demo_handshake_payload():
    """Demonstrate the handshake message structure."""
    handshake = {
        "action": "handshake",
        "clientId": "client_001",
        "capabilities": ["websocket", "http"],
        "protocolVersion": "1.0",
        "timestamp": datetime.now().isoformat() + "Z",
    }
    
    print("=== Handshake Message Payload ===")
    print(json.dumps(handshake, indent=2))
    print()


def demo_ui_usage():
    """Demonstrate how to use handshake from the UI."""
    print("=== UI Usage Guide ===\n")
    print("1. MANUAL HANDSHAKE:")
    print("   - Start the application: python main.py")
    print("   - Click 'Connect' button to establish WebSocket connection")
    print("   - Click 'Handshake' button in Default commands section")
    print("   - Click 'Send' button to transmit the handshake")
    print("   - View response in Logs panel")
    print()
    print("2. PROGRAMMATIC USAGE:")
    print("   - Enable auto_handshake=True in WebSocketManager init")
    print("   - Handshake will auto-trigger on successful connection")
    print()


def demo_programmatic_usage():
    """Show how to use handshake programmatically."""
    print("=== Programmatic Usage ===\n")
    
    code = '''
from ws_client import WebSocketManager
from utilities import AppLogger

def log_callback(msg):
    print(msg)

logger = AppLogger(log_callback)

# Option 1: Manual handshake trigger
ws_manager = WebSocketManager(logger=logger)
# ... connect first ...
ws_manager.send_handshake("my_device_id_123")

# Option 2: Automatic handshake on connection
ws_manager_auto = WebSocketManager(
    logger=logger,
    auto_handshake=True  # Auto-send handshake on connect
)
ws_manager_auto.connect("ws://localhost:8765/ws")
# Handshake auto-triggers in _on_open() callback
    '''
    
    print(code)
    print()


def demo_custom_client_id():
    """Show how to use custom client IDs."""
    print("=== Custom Client ID ===\n")
    
    print("Default client ID: 'client_001'")
    print()
    print("To use custom client ID in code:")
    print("  ws_manager.send_handshake('my_iot_device_42')")
    print()
    print("In UI:")
    print("  1. Click 'Handshake' to load the default command")
    print("  2. Edit the 'clientId' field in the command")
    print("  3. Click 'Send' to transmit with your custom ID")
    print()


def demo_logging_output():
    """Show expected logging output."""
    print("=== Expected Logging Output ===\n")
    
    logs = [
        "[2026-05-13 10:30:45] Connecting to WebSocket: ws://localhost:8765/ws",
        "[2026-05-13 10:30:46] WebSocket connected.",
        "[2026-05-13 10:30:46] Sending handshake with clientId: client_001",
        "[2026-05-13 10:30:46] Sent WebSocket message: {...handshake_payload...}",
        "[2026-05-13 10:30:47] WebSocket received: {\"action\": \"handshake_response\", \"status\": \"accepted\"}",
    ]
    
    for log in logs:
        print(log)
    print()


def demo_default_commands():
    """Show the updated default commands list."""
    print("=== Updated DEFAULT_COMMANDS ===\n")
    
    commands = [
        "1. Ping - Simple heartbeat message",
        "2. Handshake - NEW! Protocol initialization",
        "3. Login - User authentication",
        "4. Subscribe - Event subscription",
        "5. Echo - Echo test message",
    ]
    
    for cmd in commands:
        print(f"  {cmd}")
    print()


def main():
    """Run all demos."""
    print("\n")
    print("=" * 60)
    print("SCRUM-81: Handshake Message Functionality Demo")
    print("=" * 60)
    print("\n")
    
    demo_handshake_payload()
    demo_ui_usage()
    demo_programmatic_usage()
    demo_custom_client_id()
    demo_logging_output()
    demo_default_commands()
    
    print("=" * 60)
    print("For more details, see SCRUM-81_IMPLEMENTATION.md")
    print("=" * 60)
    print("\n")


if __name__ == "__main__":
    main()
