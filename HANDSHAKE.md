# WebSocket Handshake Implementation

## Overview

This document describes the WebSocket handshake mechanism implemented for SCRUM-139. The handshake is an automatic initial communication protocol that establishes client identity and capabilities when a WebSocket connection is established.

## Architecture

### Components

1. **handshake_config.py** - Configuration management for handshake fields
   - `HandshakeConfig`: Class managing client identification, token, version info
   - Validation logic to ensure required fields are present and valid
   - Factory for creating handshake payloads

2. **handshake.py** - Handshake message handling
   - `HandshakeHandler`: Manages building, sending, and responding to handshake
   - Automatic state tracking (sent, acknowledged)
   - Response callback mechanism for custom handling

3. **ws_client.py** - WebSocket connection integration
   - Modified `_on_open()` to trigger handshake automatically
   - Modified `_on_message()` to intercept handshake responses
   - New `update_handshake_config()` method for runtime configuration

4. **utilities.py** - Updated default commands
   - Added "Handshake" to DEFAULT_COMMANDS list
   - Handshake appears as a selectable preset in the UI

## Message Format

### Handshake Request
```json
{
  "action": "handshake",
  "clientId": "550e8400-e29b-41d4-a716-446655440000",
  "token": "auth-token-or-session-id",
  "clientVersion": "1.0.0",
  "protocolVersion": "1.0",
  "timestamp": "2026-03-27T12:00:00.000000Z"
}
```

### Handshake Response (expected from server)
```json
{
  "action": "handshake_ack" | "handshake_response",
  "status": "success" | "error",
  "message": "Handshake acknowledged",
  "serverVersion": "2.0.0"
}
```

## Behavior

### Automatic Trigger
- Handshake is automatically sent **2 seconds after** WebSocket connection is established
- This delay allows the connection to stabilize
- Handshake is only sent once per connection

### Validation
- All configuration fields are validated before sending
- Invalid configurations are rejected with error logging
- Required fields: `clientId`, `clientVersion`, `protocolVersion`
- Optional fields: `token` (defaults to empty string)

### Response Handling
- Server responses with action `handshake_ack` or `handshake_response` are captured
- Responses are logged with timestamp and content
- Internal state (`handshake_acknowledged`) is updated
- Optional callback can be registered for custom response handling

### State Reset
- On disconnect and reconnect, handshake state is reset
- Allows handshake to be sent again on new connections

## Configuration

### Runtime Configuration Update
```python
ws_manager.update_handshake_config(
    client_id="custom-client-id",
    token="auth-token",
    client_version="2.0.0"
)
```

### Default Configuration
If not specified:
- `client_id`: Auto-generated UUID
- `token`: Empty string
- `client_version`: "1.0.0"
- `protocol_version`: "1.0"

## Integration Points

### In UI (ui.py)
- Handshake appears in "Default commands" section as a selectable checkbox
- Users can load the handshake template and customize fields
- Handshake messages are logged like all other WebSocket messages

### In WebSocket Manager (ws_client.py)
- Automatically triggered on connection
- Response handling integrated into main message handler
- Configuration can be updated before/after connection

### Logging
All handshake events are logged with timestamps:
- Handshake message validation
- Handshake send success/failure
- Server acknowledgments
- Configuration updates

## Backwards Compatibility

✅ **No breaking changes**
- Existing command formats unchanged
- WebSocket API signatures unchanged
- Optional feature - can be disabled by not connecting
- Default commands list extended (not modified)

## Future Enhancements

1. Make handshake trigger delay configurable
2. Add retry logic if handshake is not acknowledged within timeout
3. Add custom validation callbacks
4. Support for server-initiated handshake
5. Handshake timeout and reconnection strategies

## Testing Notes

Test the implementation with:
1. Manual UI testing - select Handshake command and verify it appears correctly
2. Connection flow - connect and verify handshake is sent automatically after 2 seconds
3. Response handling - send mock handshake_ack from server and verify logging
4. Configuration update - use `update_handshake_config()` to change token/clientId
