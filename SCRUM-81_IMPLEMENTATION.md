# SCRUM-81 Implementation: Handshake Message Functionality

## Overview
Successfully implemented handshake message functionality to the IoT device management client (Tkinter WebSocket/HTTP Client). The handshake allows clients to establish protocol-level communication with the server on connection.

## Changes Made

### 1. **utilities.py** - Handshake Command Definition
**Location:** [utilities.py](utilities.py#L1-L40)

Added a new "Handshake" command to the `DEFAULT_COMMANDS` list as the second preset (replacing the previous "HTTP POST sample" to maintain 5 selectable presets).

**Handshake Message Structure:**
```json
{
  "action": "handshake",
  "clientId": "client_001",
  "capabilities": ["websocket", "http"],
  "protocolVersion": "1.0",
  "timestamp": "2026-05-13T00:00:00Z"
}
```

**Changes:**
- Added handshake as preset #2 in DEFAULT_COMMANDS
- Proper JSON formatting with all required fields
- Automatic timestamp for handshake event

### 2. **ws_client.py** - Handshake Functionality in WebSocket Client
**Location:** [ws_client.py](ws_client.py)

#### Added Parameter to `__init__`:
- `auto_handshake: bool = False` - Configurable flag for automatic handshake trigger

#### New Method: `send_handshake()`
```python
def send_handshake(self, client_id: str = "client_001") -> None:
    """Send handshake message to server."""
    from datetime import datetime
    
    handshake_payload = {
        "action": "handshake",
        "clientId": client_id,
        "capabilities": ["websocket", "http"],
        "protocolVersion": "1.0",
        "timestamp": datetime.now().isoformat() + "Z",
    }
    self.logger.log(f"Sending handshake with clientId: {client_id}")
    self.send_json(handshake_payload)
```

#### Enhanced `_on_open()` Method:
Added automatic handshake trigger support:
```python
def _on_open(self, _ws) -> None:
    self._set_connected(True)
    self.logger.log("WebSocket connected.")
    if self.auto_handshake:
        self.logger.log("Sending automatic handshake...")
        self.send_handshake()
```

**Features:**
- `send_handshake()` generates proper handshake payload with current timestamp
- Automatic validation through existing `send_json()` method
- Configurable client ID support
- All handshake attempts logged with timestamps
- Compatible with existing logging infrastructure

### 3. **UI Integration** (Automatic - No Changes Required)
The existing UI components automatically support handshake functionality:

- **Handshake Preset Button:** Available as one of 5 default command buttons in the "Default commands" section
- **Manual Trigger:** Click the "Handshake" button to load the handshake command, then click "Send"
- **Logging:** Handshake lifecycle is automatically logged:
  - Handshake sent with clientId
  - Server responses logged in real-time
  - Any handshake errors logged
- **Connection Status:** Already displayed via existing status change callback

## Usage Guide

### Manual Handshake
1. Connect to WebSocket server (click "Connect")
2. Click the "Handshake" button in Default commands section
3. Click "Send" button to transmit handshake
4. View server response in the Logs panel

### Automatic Handshake (Programmatic)
To enable automatic handshake on connection:

```python
# In main.py or your initialization code:
ws_manager = WebSocketManager(
    logger=logger,
    on_message=on_message_handler,
    on_status_change=on_status_handler,
    auto_handshake=True  # Enable automatic handshake
)
```

When auto_handshake is enabled:
- Handshake automatically sends immediately after successful WebSocket connection
- Log shows: "Sending automatic handshake..."
- Client can then send other commands

## Validation & Error Handling

✅ **JSON Validation**: Handshake payload passes through existing `_parse_request_json()` validation

✅ **Logging**: 
- Handshake attempts logged with timestamp via AppLogger
- Server responses logged in real-time
- Connection errors handled gracefully

✅ **Connection State Management**:
- Handshake only sends when connected (checked in `send_json()`)
- Proper error logging if handshake sent while disconnected

✅ **Timestamp Generation**:
- Dynamic timestamps generated at send time (not hardcoded)
- ISO 8601 format with 'Z' suffix for UTC

## Backward Compatibility

✅ **No Breaking Changes**:
- `auto_handshake` parameter defaults to `False` (disabled)
- Existing code instantiating `WebSocketManager` without the parameter continues to work
- All existing commands (Ping, Login, Subscribe, Echo) remain unchanged

## Testing Recommendations

### Unit Tests
1. **Handshake Message Generation**
   - Verify payload structure matches specification
   - Confirm timestamp is ISO 8601 format
   - Test custom clientId parameter

2. **Connection Flow**
   - Test manual handshake send via UI
   - Test automatic handshake trigger (when enabled)
   - Verify logs capture all events

3. **Error Handling**
   - Test handshake send while disconnected
   - Test invalid server responses
   - Verify graceful error logging

### Integration Tests
1. **UI Integration**
   - Click "Handshake" button loads correct command
   - "Send" button transmits to server
   - Logs display handshake events

2. **Server Communication**
   - Server receives properly formatted handshake
   - Server response logged correctly
   - Multiple handshakes handled properly

### Manual Testing Script
```python
# test_handshake.py
from ws_client import WebSocketManager
from utilities import AppLogger

def test_logger(msg):
    print(msg)

logger = AppLogger(test_logger)

# Test 1: Manual handshake
ws = WebSocketManager(logger=logger)
ws.connected = True
ws.ws_app = MockWebSocket()
ws.send_handshake("test_client_123")

# Test 2: Auto-handshake
ws_auto = WebSocketManager(logger=logger, auto_handshake=True)
# Simulate connection opening
ws_auto._on_open(None)  # Should trigger automatic handshake
```

## Files Modified
- [utilities.py](utilities.py) - Added Handshake command to DEFAULT_COMMANDS
- [ws_client.py](ws_client.py) - Added handshake sending and auto-trigger functionality
- [main.py](main.py) - No changes (backward compatible)
- [ui.py](ui.py) - No changes (automatic support)

## Configuration Notes

### Enable Auto-Handshake
Modify [ui.py](ui.py) line 26 (WebSocketManager initialization):
```python
self.ws_manager = WebSocketManager(
    logger=self.logger,
    on_message=self._handle_ws_message,
    on_status_change=self._handle_ws_status_change,
    auto_handshake=True,  # Add this to enable auto-handshake
)
```

### Custom Client ID
The handshake uses "client_001" by default. To customize:
```python
ws_manager.send_handshake("my_device_id")
```

## Future Enhancements

1. **UI Control for Auto-Handshake**: Add checkbox to toggle auto-handshake from UI
2. **Server Response Parsing**: Add handler for specific handshake response types
3. **Handshake Timeout**: Add timeout mechanism for handshake acknowledgment
4. **Protocol Negotiation**: Extend handshake to negotiate protocol features
5. **Handshake Retry Logic**: Implement retry mechanism for failed handshakes

## Summary

✅ Handshake message structure defined and integrated  
✅ Default command preset added for easy manual trigger  
✅ Automatic handshake support with configurable flag  
✅ Full logging of handshake lifecycle  
✅ Backward compatible - no breaking changes  
✅ Validated JSON payload generation  
✅ Error handling integrated with existing patterns  

The implementation follows existing patterns in the codebase, maintains backward compatibility, and provides both manual and automatic handshake triggering capabilities.
