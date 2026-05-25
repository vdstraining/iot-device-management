# SCRUM-107: Quick Reference Guide

## What Was Implemented?

A complete handshake message mechanism that automatically establishes communication between client and server after WebSocket connection, with manual trigger capability and full configuration support.

---

## Key Features at a Glance

| Feature | Status | How to Use |
|---------|--------|-----------|
| **Auto-trigger** | ✓ Enabled | Connect to WebSocket, handshake sends automatically |
| **Manual trigger** | ✓ Ready | Click "Send Handshake" button in UI |
| **Logging** | ✓ Enabled | All events logged to UI log panel |
| **Configuration** | ✓ Ready | Edit `handshake_config.json` to customize |
| **Default command** | ✓ First | Handshake is first checkbox in UI |

---

## Acceptance Criteria Checklist

- [x] **AC1** - Handshake sent automatically after WebSocket connection
- [x] **AC2** - JSON-formatted, validated handshake message
- [x] **AC3** - Handshake logged in UI (both request and response)
- [x] **AC4** - Manual trigger option available
- [x] **AC5** - Server response captured and logged
- [x] **AC6** - Configuration support for dynamic fields
- [x] **AC7** - Treated as default command (like Subscribe, Ping)
- [x] **AC8** - No breaking changes to existing APIs

---

## Modified Files

### 1. **utilities.py**
- Added: `load_handshake_config()` function
- Added: Handshake to DEFAULT_COMMANDS (position 0)
- Added: Handshake payload structure with clientId, capabilities, metadata, auth context

### 2. **ws_client.py**
- Added: `handshake_config` parameter to `__init__()`
- Added: `_build_handshake_payload()` method
- Added: `send_handshake()` method
- Enhanced: `_on_open()` to auto-trigger handshake

### 3. **ui.py**
- Added: Import of `load_handshake_config`
- Added: Load and pass `handshake_config` to WebSocketManager
- Added: "Send Handshake" button
- Added: `send_handshake()` method

### 4. **default_commands.json**
- Added: Handshake command as first entry

### 5. **NEW: handshake_config.json**
- Configuration file for handshake settings
- Supports customization without code changes

---

## Usage Scenarios

### Scenario 1: Default Behavior (Auto-trigger)
```
1. User opens application
2. User clicks "Connect" button
3. WebSocket connects
4. Handshake automatically sent
5. Server receives handshake
6. Response appears in log panel
```

### Scenario 2: Manual Trigger
```
1. User is already connected
2. User clicks "Send Handshake" button
3. Handshake sent on-demand
4. Response logged
```

### Scenario 3: Disable Auto-trigger
Edit `handshake_config.json`:
```json
{
  "auto_trigger": false
}
```
Then use manual trigger via button.

### Scenario 4: Customize Client Info
Edit `handshake_config.json`:
```json
{
  "clientId": "my-custom-device-001",
  "capabilities": ["websocket", "http", "custom-feature"]
}
```
Changes take effect on next application start.

---

## Testing

Run validation tests:
```bash
python test_handshake.py
```

Expected output:
```
✓ Test 1 - Load handshake config: PASS
✓ Test 2 - Handshake in DEFAULT_COMMANDS: PASS
✓ Test 3 - handshake_config.json file: PASS
✓ Test 4 - WebSocketManager initialization: PASS
✓ All validation tests passed!
```

---

## Configuration Options

**File:** `handshake_config.json`

```json
{
  "enabled": true,              // Enable handshake feature
  "auto_trigger": true,         // Auto-send after connection
  "clientId": "device-001",     // Unique client ID
  "capabilities": [             // Client capabilities
    "websocket",
    "http",
    "json-messaging"
  ],
  "session_metadata": {         // Session info
    "version": "1.0",
    "application": "IoT Device Simulator",
    "platform": "Tkinter"
  },
  "authentication_context": {   // Auth details
    "auth_type": "bearer",
    "token": ""
  }
}
```

---

## Code Examples

### Using Handshake in Code

```python
from utilities import load_handshake_config
from ws_client import WebSocketManager

# Load configuration
config = load_handshake_config()

# Create manager with handshake
ws_manager = WebSocketManager(
    logger=my_logger,
    handshake_config=config
)

# Connect (handshake sends automatically)
ws_manager.connect("ws://server:8765/ws")

# Or manually trigger later
ws_manager.send_handshake()
```

---

## Log Panel Output Examples

### Connection Sequence
```
[2026-05-25 14:30:15] Connecting to WebSocket: ws://localhost:8765/ws
[2026-05-25 14:30:16] WebSocket connected.
[2026-05-25 14:30:16] Sent handshake message: {"action": "handshake", ...}
[2026-05-25 14:30:16] WebSocket received: {"status": "ok", "version": "1.0"}
```

### Manual Trigger
```
[2026-05-25 14:30:45] Sent handshake message: {"action": "handshake", ...}
[2026-05-25 14:30:45] WebSocket received: {"status": "ok"}
```

---

## Troubleshooting

### Handshake Not Sending Automatically
**Check:**
1. Is `handshake_config.json` in the project root?
2. Is `"enabled": true` in the config?
3. Is `"auto_trigger": true` in the config?

### Configuration Changes Not Applied
**Solution:**
Restart the application. Configuration is loaded at startup.

### Manual Trigger Button Does Nothing
**Check:**
1. Are you connected to WebSocket? (connection status should show)
2. Check log panel for error messages
3. Verify `handshake_config.json` exists and is valid JSON

---

## Performance Notes

- Handshake payload: ~300-500 bytes
- No significant performance impact
- Runs in WebSocket thread (non-blocking UI)
- Logging is async to UI thread

---

## Security Considerations

- Token field in authentication_context is empty by default
- Populate token in config file or environment
- Never commit real tokens to version control
- Use environment variables for sensitive data

---

## Backward Compatibility

✓ All changes are backward compatible:
- Old code without handshake_config still works
- WebSocketManager gracefully handles missing config
- No existing APIs modified
- All existing commands preserved

---

## Next Steps for Integration

1. Test with actual WebSocket server
2. Monitor handshake exchange in server logs
3. Verify server capabilities in response
4. Customize client capabilities in `handshake_config.json`
5. Add token to authentication_context if server requires it
