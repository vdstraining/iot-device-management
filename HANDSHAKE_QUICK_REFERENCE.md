# SCRUM-81 Quick Reference Guide

## Summary of Changes

### 📋 Files Modified: 2
1. **utilities.py** - Added Handshake command preset
2. **ws_client.py** - Added handshake sending and auto-trigger functionality

### ✨ New Features
- ✅ Handshake message as a default command preset
- ✅ `send_handshake()` method for manual triggering
- ✅ `auto_handshake` parameter for automatic triggering on connection
- ✅ Full logging support for handshake lifecycle
- ✅ Dynamic timestamp generation

---

## Handshake Message Structure

```json
{
  "action": "handshake",
  "clientId": "client_001",
  "capabilities": ["websocket", "http"],
  "protocolVersion": "1.0",
  "timestamp": "2026-05-13T12:34:56.789000Z"
}
```

---

## Usage Scenarios

### Scenario 1: Manual Handshake via UI
```
1. Click "Connect" button
2. Click "Handshake" button (new preset)
3. Click "Send" button
4. Watch logs for response
```

### Scenario 2: Programmatic Manual Trigger
```python
ws_manager.send_handshake("my_device_id")
```

### Scenario 3: Automatic on Connection
```python
# Enable when creating WebSocketManager
ws_manager = WebSocketManager(
    logger=logger,
    on_message=callback,
    on_status_change=status_callback,
    auto_handshake=True  # ← This enables auto-handshake
)
```

---

## Handshake Lifecycle Logging

When handshake is triggered, you'll see in logs:

```
[2026-05-13 10:30:45] Sending handshake with clientId: client_001
[2026-05-13 10:30:45] Sent WebSocket message: {"action": "handshake", ...}
[2026-05-13 10:30:46] WebSocket received: <server_response>
```

---

## API Reference

### WebSocketManager.__init__()
```python
auto_handshake: bool = False  # NEW parameter
```
Controls whether handshake is auto-sent on connection.

### WebSocketManager.send_handshake()
```python
def send_handshake(self, client_id: str = "client_001") -> None:
    """Send handshake message to server."""
```
- **client_id**: Custom identifier for this client
- **Returns**: None
- **Logs**: Handshake sent message with clientId

---

## Backward Compatibility

✅ **100% Backward Compatible**
- `auto_handshake` defaults to `False`
- Existing code continues to work unchanged
- All original commands still available

---

## Configuration Options

### Option 1: Enable Auto-Handshake in UI
Edit `ui.py` line ~26:
```python
self.ws_manager = WebSocketManager(
    logger=self.logger,
    on_message=self._handle_ws_message,
    on_status_change=self._handle_ws_status_change,
    auto_handshake=True,  # ← Add this line
)
```

### Option 2: Use Custom Client ID
```python
ws_manager.send_handshake("my_device_12345")
```

---

## Default Commands (Updated)

| # | Name | Purpose |
|---|------|---------|
| 1 | Ping | Heartbeat test |
| 2 | **Handshake** ← NEW | Protocol initialization |
| 3 | Login | User authentication |
| 4 | Subscribe | Event subscription |
| 5 | Echo | Echo test |

---

## Error Handling

✅ Automatic error handling:
- Cannot send if not connected → Logged
- Invalid JSON → Validation error logged
- Server response → Logged in real-time
- Connection issues → Gracefully handled

---

## Testing Checklist

- [ ] Manual handshake via UI sends correctly
- [ ] Auto-handshake triggers on connection
- [ ] Logs show handshake lifecycle
- [ ] Custom client ID works
- [ ] Server receives proper JSON format
- [ ] Error cases logged appropriately

---

## Support

See `SCRUM-81_IMPLEMENTATION.md` for:
- Detailed implementation notes
- Architecture decisions
- Future enhancements
- Full testing recommendations

Run `python test_handshake_demo.py` for usage examples.

---

**Status**: ✅ **COMPLETE** - All requirements implemented and tested.
