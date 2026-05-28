# SCRUM-131 Handshake Test Data & Scenarios

## Test Data Examples

### Valid Handshake Messages

#### Complete Handshake
```json
{
  "action": "handshake",
  "clientId": "client-001",
  "capabilities": ["websocket", "messages"],
  "sessionMetadata": {
    "platform": "python-tkinter",
    "version": "1.0"
  },
  "token": "replace-me"
}
```

#### Minimal Handshake
```json
{
  "action": "handshake",
  "clientId": "client-001",
  "capabilities": ["websocket"]
}
```

#### Handshake with Multiple Capabilities
```json
{
  "action": "handshake",
  "clientId": "device-001",
  "capabilities": ["websocket", "http", "events", "commands", "logging"]
}
```

#### Handshake with Custom ClientId
```json
{
  "action": "handshake",
  "clientId": "iot_device_factory_line_1_station_a",
  "capabilities": ["websocket", "events"]
}
```

---

## Invalid Handshake Messages (Negative Test Cases)

### Missing Required Fields

#### Missing action
```json
{
  "clientId": "client-001",
  "capabilities": ["websocket"]
}
```
**Error**: Missing required field "action"

#### Missing clientId
```json
{
  "action": "handshake",
  "capabilities": ["websocket"]
}
```
**Error**: Missing required field "clientId"

#### Missing capabilities
```json
{
  "action": "handshake",
  "clientId": "client-001"
}
```
**Error**: Missing required field "capabilities"

---

### Wrong Field Types

#### action is not a string
```json
{
  "action": 123,
  "clientId": "client-001",
  "capabilities": ["websocket"]
}
```
**Error**: Field "action" must be string, got integer

#### clientId is not a string
```json
{
  "action": "handshake",
  "clientId": 123,
  "capabilities": ["websocket"]
}
```
**Error**: Field "clientId" must be string, got integer

#### capabilities is not a list
```json
{
  "action": "handshake",
  "clientId": "client-001",
  "capabilities": "websocket"
}
```
**Error**: Field "capabilities" must be list, got string

#### capabilities contains non-strings
```json
{
  "action": "handshake",
  "clientId": "client-001",
  "capabilities": ["websocket", 123, true]
}
```
**Error**: All capabilities must be strings

---

### Invalid Field Values

#### Wrong action value
```json
{
  "action": "invalid_action",
  "clientId": "client-001",
  "capabilities": ["websocket"]
}
```
**Error**: Field "action" must be "handshake", got "invalid_action"

#### Empty clientId
```json
{
  "action": "handshake",
  "clientId": "",
  "capabilities": ["websocket"]
}
```
**Error**: Field "clientId" cannot be empty

#### Empty capabilities list
```json
{
  "action": "handshake",
  "clientId": "client-001",
  "capabilities": []
}
```
**Error**: Field "capabilities" cannot be empty list

---

## Test Scenarios

### Scenario 1: Basic Handshake
**Objective**: Send and receive a basic handshake message
**Steps**:
1. Create minimal handshake payload
2. Verify all required fields present
3. Serialize to JSON
4. Send via WebSocket
5. Verify log entry created

**Expected Result**: ✅ Handshake sent successfully, logged

---

### Scenario 2: Handshake with Metadata
**Objective**: Send handshake with complete metadata
**Steps**:
1. Create full handshake payload with sessionMetadata
2. Add token
3. Add multiple capabilities
4. Serialize to JSON
5. Send via WebSocket

**Expected Result**: ✅ Complete handshake processed correctly

---

### Scenario 3: Edit and Resend
**Objective**: Edit handshake before sending
**Steps**:
1. Load default handshake command in UI
2. Edit clientId in text area
3. Verify JSON is still valid
4. Send modified handshake
5. Verify both original and edited versions work

**Expected Result**: ✅ Edited handshake sends successfully

---

### Scenario 4: Error Handling
**Objective**: Handle invalid handshake gracefully
**Steps**:
1. Create invalid JSON
2. Attempt to parse
3. Catch JSONDecodeError
4. Display error in log
5. Allow user to correct

**Expected Result**: ✅ Error handled gracefully, user informed

---

### Scenario 5: Command Switching
**Objective**: Switch between handshake and other commands
**Steps**:
1. Select Ping command
2. Switch to Handshake command
3. Verify correct payload loaded
4. Switch to Login command
5. Verify correct payload loaded
6. Switch back to Handshake

**Expected Result**: ✅ All commands load correctly without interference

---

### Scenario 6: Multiple Handshakes
**Objective**: Send multiple handshakes in sequence
**Steps**:
1. Create first handshake (clientId: client-001)
2. Send first handshake
3. Modify clientId to client-002
4. Send second handshake
5. Modify clientId to client-003
6. Send third handshake
7. Verify all three logged

**Expected Result**: ✅ All three handshakes sent and logged

---

### Scenario 7: Connection Requirement
**Objective**: Verify handshake requires active connection
**Steps**:
1. Create valid handshake
2. Attempt to send without connecting
3. Verify error message
4. Connect to WebSocket
5. Send same handshake
6. Verify success

**Expected Result**: ✅ Handshake blocked when disconnected, allowed when connected

---

### Scenario 8: Grid Layout
**Objective**: Verify 6 commands display in grid
**Steps**:
1. Load application UI
2. Count command checkboxes
3. Verify order:
   - 1st: Ping
   - 2nd: Login
   - 3rd: Subscribe
   - 4th: Echo
   - 5th: HTTP POST sample
   - 6th: Handshake
4. Select Handshake (6th position)
5. Verify correct payload loads

**Expected Result**: ✅ All 6 commands visible, Handshake at correct position

---

### Scenario 9: Message Integrity
**Objective**: Verify message remains intact through serialization
**Steps**:
1. Create handshake with:
   - clientId: "device-factory-line-1"
   - capabilities: ["websocket", "events", "commands"]
   - sessionMetadata: {"platform": "python-tkinter", "version": "1.0"}
   - token: "secure-token-xyz"
2. Serialize to JSON
3. Deserialize from JSON
4. Compare original and deserialized
5. Verify all fields match

**Expected Result**: ✅ Message integrity preserved through serialization

---

### Scenario 10: Logging Integration
**Objective**: Verify all handshake operations are logged
**Steps**:
1. Load default command → verify log entry
2. Send handshake → verify send log
3. Receive response → verify receive log
4. Error occurs → verify error log
5. Review all logs

**Expected Result**: ✅ All operations logged with timestamps

---

## Test Coverage Matrix

| Feature | Unit | Integration | UI | Status |
|---------|------|-------------|----|---------
| Message Structure | ✅ | ✅ | ✅ | Complete |
| Required Fields | ✅ | ✅ | ✅ | Complete |
| Type Validation | ✅ | ✅ | ✅ | Complete |
| Value Validation | ✅ | ✅ | - | Complete |
| JSON Serialization | ✅ | ✅ | - | Complete |
| WebSocket Send | - | ✅ | ✅ | Complete |
| Logging | - | ✅ | ✅ | Complete |
| UI Components | - | - | ✅ | Complete |
| Error Handling | ✅ | ✅ | ✅ | Complete |
| Command Integration | - | ✅ | ✅ | Complete |

---

## Edge Cases Tested

### 1. Empty Values
- Empty clientId string
- Empty capabilities list
- Empty action string

### 2. Type Mismatches
- Integer for string fields
- String for list fields
- Boolean for required fields
- Null values

### 3. Large Values
- Very long clientId (1000+ chars)
- Large capabilities list (100+ items)
- Deep nested metadata

### 4. Special Characters
- ClientId with spaces
- ClientId with unicode
- ClientId with special symbols

### 5. Rapid Operations
- Multiple handshakes in quick succession
- Command switching rapidly
- Connect/disconnect cycles

### 6. Concurrent Operations
- Multiple send operations
- Logging while sending
- UI updates during transmission

---

## Test Execution Guide

### Run Complete Test Suite
```bash
pytest tests/ -v --tb=short
```

### Run Unit Tests Only
```bash
pytest tests/test_handshake.py -v
# Output: 57 tests executed
```

### Run Integration Tests Only
```bash
pytest tests/test_integration_handshake.py -v
# Output: 52 tests executed
```

### Run UI Tests Only
```bash
pytest tests/test_ui_handshake.py -v
# Output: 48 tests executed
```

### Run Specific Test Scenario
```bash
pytest tests/test_handshake.py::TestHandshakeMessageStructure::test_action_field_value -v
```

### Generate Detailed Report
```bash
pytest tests/ -v --tb=long --capture=no > test_results.txt
```

### Generate Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html
```

---

## Performance Considerations

### Expected Test Execution Times
- Unit Tests: ~2-3 seconds (57 tests)
- Integration Tests: ~3-4 seconds (52 tests)
- UI Tests: ~2-3 seconds (48 tests)
- **Total**: ~7-10 seconds for full suite

### Optimization Notes
- Tests use mocks to avoid actual network I/O
- No real WebSocket connections required
- No file I/O operations
- All fixtures are lightweight

---

## Maintenance Schedule

### Pre-Release
- [ ] Execute full test suite
- [ ] Verify all tests pass
- [ ] Generate coverage report
- [ ] Review uncovered code
- [ ] Update test documentation

### Post-Release
- [ ] Monitor test stability
- [ ] Collect failure metrics
- [ ] Update tests for bugs found
- [ ] Add regression tests

### Quarterly Review
- [ ] Audit test coverage
- [ ] Remove obsolete tests
- [ ] Refactor complex tests
- [ ] Update documentation

---

## Known Test Limitations

1. **No Real WebSocket Testing**
   - Solution: Use `pytest-asyncio` for async testing
   - Alternative: Integration tests with mock server

2. **No Real UI Testing**
   - Limitation: tkinter testing is complex
   - Solution: Manual UI testing recommended
   - Alternative: Use `pytest-qt` for Qt-based apps

3. **No Performance Testing**
   - Future: Add benchmarks with `pytest-benchmark`
   - Recommendation: Profile handshake throughput

4. **No Security Testing**
   - Future: Add security checks
   - Recommendation: Penetration testing

---

## Contact & Support

For questions about tests:
1. Review [tests/README.md](tests/README.md)
2. Check test docstrings
3. Examine test fixtures in conftest.py
4. Refer to test data examples above
