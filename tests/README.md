# SCRUM-81: Handshake Message Implementation - Test Suite

## Overview

This test suite provides comprehensive coverage for the handshake message functionality implemented in SCRUM-81. The tests are organized into four main categories:

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test components working together
3. **Edge Case Tests** - Test boundary conditions and error scenarios
4. **Logging Tests** - Verify logging behavior

## Test File Location

```
tests/test_handshake.py
```

## Test Statistics

- **Total Test Classes**: 8
- **Total Test Functions**: 70+
- **Test Coverage Areas**:
  - Handshake payload validation (7 tests)
  - send_handshake() method (7 tests)
  - auto_handshake parameter (6 tests)
  - DEFAULT_COMMANDS integration (7 tests)
  - Logging integration (5 tests)
  - Connection flow (5 tests)
  - Message transmission (3 tests)
  - Edge cases (10+ tests)

## Installation & Setup

### Prerequisites

1. Python 3.10 or later
2. pytest framework
3. Project dependencies

### Install Test Dependencies

```bash
# Install pytest
pip install pytest pytest-cov

# Install project dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
python -m pytest --version
```

## Running the Tests

### Run All Tests

```bash
# Standard verbose output
python -m pytest tests/test_handshake.py -v

# With detailed output
python -m pytest tests/test_handshake.py -vv

# With short traceback format
python -m pytest tests/test_handshake.py -v --tb=short
```

### Run Specific Test Classes

```bash
# Unit tests only
python -m pytest tests/test_handshake.py::TestHandshakePayloadValidation -v
python -m pytest tests/test_handshake.py::TestSendHandshakeMethod -v
python -m pytest tests/test_handshake.py::TestAutoHandshakeParameter -v
python -m pytest tests/test_handshake.py::TestDefaultCommandsIntegration -v
python -m pytest tests/test_handshake.py::TestLoggingIntegration -v

# Integration tests
python -m pytest tests/test_handshake.py::TestConnectionFlow -v
python -m pytest tests/test_handshake.py::TestMessageTransmission -v

# Edge case tests
python -m pytest tests/test_handshake.py::TestEdgeCases -v
```

### Run Specific Test Functions

```bash
# Run a single test
python -m pytest tests/test_handshake.py::TestHandshakePayloadValidation::test_handshake_payload_has_all_required_fields -v

# Run tests matching a pattern
python -m pytest tests/test_handshake.py -k "timestamp" -v
python -m pytest tests/test_handshake.py -k "auto_handshake" -v
```

### Generate Coverage Report

```bash
# HTML coverage report
python -m pytest tests/test_handshake.py --cov=ws_client --cov=utilities --cov-report=html

# Terminal coverage report
python -m pytest tests/test_handshake.py --cov=ws_client --cov=utilities --cov-report=term-missing
```

### Run with Markers

```bash
# Run only unit tests
python -m pytest tests/test_handshake.py -m unit -v

# Run only integration tests
python -m pytest tests/test_handshake.py -m integration -v

# Run only edge case tests
python -m pytest tests/test_handshake.py -m edge_case -v
```

## Test Categories Explained

### 1. Handshake Payload Validation Tests

**Location**: `TestHandshakePayloadValidation` class

**Purpose**: Verify the structure and content of handshake messages

**Tests**:
- ✓ All required fields present (action, clientId, capabilities, protocolVersion, timestamp)
- ✓ Correct action value ("handshake")
- ✓ Default clientId ("client_001")
- ✓ Capabilities list contains "websocket" and "http"
- ✓ Protocol version is "1.0"
- ✓ Timestamp format is ISO 8601 with Z suffix
- ✓ Payload is valid JSON

**Example**:
```python
# Verify handshake has all required fields
def test_handshake_payload_has_all_required_fields(mock_logger):
    # ... test code ...
    assert "action" in payload
    assert "clientId" in payload
    assert "capabilities" in payload
    assert "protocolVersion" in payload
    assert "timestamp" in payload
```

### 2. send_handshake() Method Tests

**Location**: `TestSendHandshakeMethod` class

**Purpose**: Verify the send_handshake() method works correctly

**Tests**:
- ✓ Method exists and is callable
- ✓ Can be called with default parameters
- ✓ Accepts custom client_id parameter
- ✓ Works with various clientId values
- ✓ Produces log messages
- ✓ Calls send_json() internally

**Example**:
```python
def test_send_handshake_method_exists(ws_manager):
    assert hasattr(ws_manager, "send_handshake")
    assert callable(ws_manager.send_handshake)
```

### 3. auto_handshake Parameter Tests

**Location**: `TestAutoHandshakeParameter` class

**Purpose**: Verify auto_handshake functionality

**Tests**:
- ✓ Default value is False
- ✓ Parameter is accepted by WebSocketManager
- ✓ Can be set to True
- ✓ Triggers handshake on connection when True
- ✓ Does NOT trigger when False
- ✓ Doesn't prevent manual send_handshake() calls

**Example**:
```python
def test_auto_handshake_trigger_on_connection(mock_logger):
    manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
    manager.send_handshake = Mock()
    
    mock_ws = Mock()
    manager._on_open(mock_ws)
    
    assert manager.send_handshake.called
```

### 4. DEFAULT_COMMANDS Integration Tests

**Location**: `TestDefaultCommandsIntegration` class

**Purpose**: Verify handshake is properly integrated in DEFAULT_COMMANDS

**Tests**:
- ✓ Handshake preset exists in DEFAULT_COMMANDS
- ✓ Handshake command has correct structure
- ✓ Payload has all required fields
- ✓ Command is valid JSON
- ✓ DEFAULT_COMMANDS has exactly 5 presets
- ✓ All commands have name and payload fields
- ✓ Handshake appears as second command (index 1)

**Example**:
```python
def test_handshake_in_default_commands():
    command_names = [cmd["name"] for cmd in DEFAULT_COMMANDS]
    assert "Handshake" in command_names
```

### 5. Logging Integration Tests

**Location**: `TestLoggingIntegration` class

**Purpose**: Verify handshake operations are properly logged

**Tests**:
- ✓ send_handshake() produces log messages
- ✓ Log includes clientId
- ✓ Auto-handshake logs when connection established
- ✓ JSON sends are logged
- ✓ Errors are logged appropriately

**Example**:
```python
def test_send_handshake_logs_message(mock_logger):
    manager.send_handshake()
    assert mock_logger.log.called
```

### 6. Connection Flow Integration Tests

**Location**: `TestConnectionFlow` class

**Purpose**: Verify handshake works in the connection lifecycle

**Tests**:
- ✓ Handshake triggers on successful connection (with auto_handshake=True)
- ✓ No auto-handshake when disabled
- ✓ Manual handshake works anytime when connected
- ✓ Connection status is set on open
- ✓ Connection status is cleared on close

**Example**:
```python
def test_handshake_triggers_on_successful_connection_with_auto_handshake(mock_logger):
    manager = WebSocketManager(logger=mock_logger, auto_handshake=True)
    manager.send_handshake = Mock()
    
    mock_ws = Mock()
    manager._on_open(mock_ws)
    
    assert manager.send_handshake.called
```

### 7. Message Transmission Tests

**Location**: `TestMessageTransmission` class

**Purpose**: Verify handshake messages are transmitted correctly

**Tests**:
- ✓ Handshake message is properly formatted JSON
- ✓ Sent through WebSocket (ws_app.send called)
- ✓ Multiple handshakes can be sent independently

**Example**:
```python
def test_handshake_message_properly_formatted(mock_logger):
    # ... setup ...
    manager.send_handshake()
    
    msg_json = json.loads(captured_messages[0])
    assert msg_json["action"] == "handshake"
```

### 8. Edge Cases Tests

**Location**: `TestEdgeCases` class

**Purpose**: Test boundary conditions and error scenarios

**Tests**:
- ✓ Empty clientId
- ✓ Special characters in clientId (-, _, ., /, @)
- ✓ Very long clientId (1000+ characters)
- ✓ Multiple handshakes in rapid succession (10+ in sequence)
- ✓ Handshake before connection established
- ✓ Handshake after disconnection
- ✓ Unicode characters in clientId
- ✓ Payload immutability

**Example**:
```python
def test_special_characters_in_client_id(mock_logger):
    special_ids = ["client-001", "device.sensor.01", "iot/device/01"]
    
    for special_id in special_ids:
        manager.send_handshake(client_id=special_id)
        assert sent_payloads[0]["clientId"] == special_id
        json.dumps(sent_payloads[0])  # Valid JSON
```

## Test Fixtures

All tests use fixtures to manage dependencies:

### Available Fixtures

1. **mock_logger**
   - A Mock object implementing AppLogger interface
   - Tracks all log() calls

2. **captured_logs**
   - A list that captures all log messages
   - Useful for verifying what was logged

3. **ws_manager**
   - A WebSocketManager instance with mock logger
   - auto_handshake defaults to False

4. **ws_manager_with_auto_handshake**
   - A WebSocketManager with auto_handshake=True

5. **ws_manager_with_callbacks**
   - A WebSocketManager with message and status callbacks
   - Returns (manager, on_message_mock, on_status_mock)

## Example Test Runs

### Run all tests with summary
```bash
python -m pytest tests/test_handshake.py -v --tb=short
```

**Output Example**:
```
tests/test_handshake.py::TestHandshakePayloadValidation::test_handshake_payload_has_all_required_fields PASSED
tests/test_handshake.py::TestHandshakePayloadValidation::test_handshake_action_is_handshake PASSED
tests/test_handshake.py::TestHandshakePayloadValidation::test_handshake_default_clientid PASSED
...
tests/test_handshake.py::TestEdgeCases::test_unicode_in_client_id PASSED

====================== 70 passed in 0.42s ======================
```

### Run with coverage report
```bash
python -m pytest tests/test_handshake.py \
  --cov=ws_client \
  --cov=utilities \
  --cov-report=term-missing
```

**Output Example**:
```
Name          Stmts   Miss  Cover   Missing
--------------------------------------------
ws_client.py     85      0   100%
utilities.py     35      0   100%
--------------------------------------------
TOTAL           120      0   100%
```

## Continuous Integration

### GitHub Actions Example

Add this to `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          python -m pytest tests/test_handshake.py -v --cov=ws_client --cov=utilities
```

## Test Coverage Goals

The test suite is designed to achieve:

- **✓ 100% code coverage** for new/modified code in ws_client.py and utilities.py
- **✓ All critical paths** tested
- **✓ Error handling** verified
- **✓ Edge cases** covered
- **✓ Integration scenarios** validated

## Debugging Failed Tests

### Run with verbose output
```bash
python -m pytest tests/test_handshake.py -vv --tb=long
```

### Run specific test with print statements
```bash
python -m pytest tests/test_handshake.py::TestHandshakePayloadValidation::test_handshake_payload_has_all_required_fields -vv -s
```

### See captured stdout
```bash
python -m pytest tests/test_handshake.py -vv -s
```

### Run with pdb debugger
```bash
python -m pytest tests/test_handshake.py --pdb
```

## Test Dependencies

**Pytest Plugins** (optional):
- `pytest-cov` - Coverage reporting
- `pytest-html` - HTML reports
- `pytest-xdist` - Parallel execution
- `pytest-timeout` - Timeout handling

Install all:
```bash
pip install pytest pytest-cov pytest-html pytest-xdist pytest-timeout
```

## Troubleshooting

### ImportError: No module named 'pytest'

**Solution**:
```bash
pip install pytest
```

### ImportError: No module named 'ws_client'

**Solution**: Run tests from project root directory:
```bash
cd /path/to/iot-device-management
python -m pytest tests/test_handshake.py
```

### ModuleNotFoundError: No module named 'websocket'

**Solution**:
```bash
pip install -r requirements.txt
```

## Performance Notes

- Total test execution time: ~0.5 seconds
- No external network calls (all mocked)
- No file I/O operations
- Tests are thread-safe and can be run in parallel:
  ```bash
  pip install pytest-xdist
  python -m pytest tests/test_handshake.py -n auto
  ```

## Maintenance

### Adding New Tests

1. Add test to appropriate class in `tests/test_handshake.py`
2. Follow naming convention: `test_<feature>_<scenario>`
3. Use appropriate fixture
4. Add docstring explaining what is tested
5. Run full test suite to verify

### Updating Existing Tests

If implementation changes:

1. Update test assertions to match new behavior
2. Add tests for new features
3. Remove tests for removed features
4. Run full test suite
5. Verify coverage remains at 100%

## Test Report Generation

Generate an HTML coverage report:

```bash
python -m pytest tests/test_handshake.py \
  --cov=ws_client \
  --cov=utilities \
  --cov-report=html

# Then open htmlcov/index.html in a browser
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `pytest tests/test_handshake.py` | Run all tests |
| `pytest tests/test_handshake.py -v` | Verbose output |
| `pytest tests/test_handshake.py -k handshake` | Run tests matching pattern |
| `pytest tests/test_handshake.py --cov` | With coverage |
| `pytest tests/test_handshake.py -m unit` | Only unit tests |
| `pytest tests/test_handshake.py -m integration` | Only integration tests |
| `pytest tests/test_handshake.py --collect-only` | List all tests |

## Notes

- All tests use mocks to avoid external dependencies
- Tests are deterministic and repeatable
- No global state or side effects
- Each test is independent
- Fixtures are automatically managed by pytest
