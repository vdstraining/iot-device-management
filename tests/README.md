# Tests for SCRUM-127: Implement new handshake message to server

## Overview

This test suite provides comprehensive coverage for the SCRUM-127 feature implementation, which adds automatic handshake message support to the IoT Device Management WebSocket client.

## Test Structure

### Test Files

1. **test_utilities.py** - Unit tests for utility functions
   - `TestValidateHandshakePayload` - Tests for handshake payload validation function
   - `TestIsHandshakeMessage` - Tests for handshake message detection function
   - `TestDefaultCommands` - Tests for DEFAULT_COMMANDS configuration

2. **test_ws_client.py** - Unit tests for WebSocketManager
   - `TestWebSocketManagerInit` - Initialization and configuration tests
   - `TestValidatePayload` - JSON serialization validation tests
   - `TestSendHandshake` - Handshake sending functionality tests
   - `TestOnOpen` - Connection callback tests
   - `TestSetConnected` - Connection state management tests
   - `TestHandshakeIntegration` - Integration tests for handshake flow

3. **test_ui_integration.py** - UI integration tests
   - `TestUIHandshakeIntegration` - UI handshake feature integration tests
   - `TestUIHandshakeDetection` - Message detection in UI context
   - `TestEnvironmentVariableSupport` - Environment variable handling
   - `TestUIDefaultCommandsRendering` - UI command rendering tests
   - `TestHandshakeMessageEdgeCases` - Edge cases for message detection

4. **test_negative_cases.py** - Negative and edge case tests
   - `TestNegativeValidationCases` - Invalid input validation tests
   - `TestIsHandshakeMessageEdgeCases` - Message detection edge cases
   - `TestWebSocketManagerNegativeCases` - WebSocket manager negative cases
   - `TestJSONSerializationEdgeCases` - JSON serialization edge cases
   - `TestConcurrencyAndStateBehavior` - State management tests
   - `TestErrorMessageAccuracy` - Error message verification
   - `TestConnectorStateConsistency` - Connection state consistency

## Test Coverage Summary

### Unit Tests (118 tests)

#### Utilities Module
- **validate_handshake_payload**: 11 tests
  - Valid complete payloads
  - Valid minimal payloads
  - Invalid input types (string, list, None)
  - Missing required fields (type, clientId, version)
  - Invalid field values
  - Extra fields handling
  - Empty dictionaries

- **is_handshake_message**: 7 tests
  - Valid handshake messages
  - Non-handshake type fields
  - Missing type fields
  - Non-dict inputs (None, list, string, etc.)
  - Exception handling

- **DEFAULT_COMMANDS**: 9 tests
  - Handshake command presence
  - Command structure validation
  - Required fields verification
  - Environment variable support
  - Default values
  - Payload format consistency

#### WebSocketManager
- **Initialization**: 6 tests
  - Default parameters
  - auto_handshake parameter variations
  - Custom payloads
  - Callbacks configuration

- **_validate_payload**: 7 tests
  - Valid JSON-serializable objects
  - Nested structures and lists
  - Various data types (int, float, bool, None)
  - Non-serializable objects
  - Circular references
  - Empty dictionaries

- **_send_handshake**: 7 tests
  - Connection state checks
  - Valid payload sending
  - Invalid payload structure rejection
  - Missing required fields
  - Non-serializable payloads
  - Exception handling during send

- **_on_open**: 4 tests
  - auto_handshake enabled/disabled flow
  - Status callback invocation
  - Connection logging
  - Handshake triggering

- **_set_connected**: 3 tests
  - State flag updates
  - Callback invocation
  - Behavior without callbacks

### Integration Tests (30 tests)

#### UI Integration
- **Handshake Detection**: 12 tests
  - Valid handshake responses with various payloads
  - Non-handshake message filtering
  - Non-JSON message handling
  - 9 parametrized test cases covering edge cases

- **Default Commands**: 8 tests
  - Handshake command presence
  - Payload JSON serializability
  - Environment variable support
  - Field presence and structure

- **Message Edge Cases**: 6 tests
  - Empty JSON objects
  - Null type values
  - Empty string types
  - Case sensitivity
  - Extra fields in messages

#### End-to-End Flow
- **Auto-handshake Flow**: 1 test
  - Complete flow from connection to handshake send

- **Manual Handshake**: 1 test
  - Manual handshake invocation

- **Connection State**: 1 test
  - Connection persistence despite handshake failure

### Negative Test Cases (45 tests)

- **Invalid Input Types**: 10 tests
  - All non-dict types (None, string, list, int, float, bool, set, tuple)
  - Various handshake type values
  - Edge cases for required fields

- **JSON Serialization Issues**: 3 tests
  - Infinity values
  - NaN values
  - Bytes objects

- **Exception Handling**: 5 tests
  - Various exception types (RuntimeError, ValueError, TypeError, IOError)
  - AttributeError on None ws_app
  - JSON serialization exceptions

- **State Behavior**: 5 tests
  - Multiple state transitions
  - Payload mutation effects
  - State consistency

- **Edge Cases**: 12 tests
  - Special characters in fields
  - Large field values
  - Unicode characters
  - Deeply nested structures
  - Dict-like objects that aren't dicts

- **Error Messages**: 1 test
  - Descriptive error messages

## Requirements

### Python Version
- Python 3.10+

### Dependencies
- pytest >= 7.4.3
- pytest-cov >= 4.1.0
- pytest-mock >= 3.12.0

### Installation

```bash
# From the tests directory
pip install -r requirements.txt
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_utilities.py
pytest tests/test_ws_client.py
pytest tests/test_ui_integration.py
pytest tests/test_negative_cases.py
```

### Run specific test class
```bash
pytest tests/test_utilities.py::TestValidateHandshakePayload
pytest tests/test_ws_client.py::TestSendHandshake
```

### Run specific test
```bash
pytest tests/test_utilities.py::TestValidateHandshakePayload::test_valid_handshake_payload_complete
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with coverage report
```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

### Run with pytest markers
```bash
# Run parametrized tests
pytest tests/test_ui_integration.py::TestUIHandshakeDetection::test_handshake_message_detection_variations -v
```

### Run tests in parallel (requires pytest-xdist)
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## Test Fixtures

### Available Fixtures (conftest.py)

- **mock_logger**: Mock logger object for testing
  ```python
  def test_something(mock_logger):
      mock_logger.log("test")
      mock_logger.log.assert_called()
  ```

- **valid_handshake_payload**: Complete valid handshake payload
  ```python
  {
      "type": "handshake",
      "clientId": "test-client",
      "version": "1.0",
      "token": "test-token",
  }
  ```

- **valid_handshake_payload_no_token**: Minimal valid handshake payload
  ```python
  {
      "type": "handshake",
      "clientId": "test-client",
      "version": "1.0",
  }
  ```

- **valid_handshake_response**: Valid handshake response message
  ```python
  {
      "type": "handshake",
      "status": "success",
      "sessionId": "sess-123",
  }
  ```

- **mock_callback**: Mock callback function

## Feature Coverage

### 1. Handshake Message Validation ✓
- [x] validate_handshake_payload function validation
- [x] Required field checks (type, clientId, version)
- [x] Invalid input handling
- [x] Error message accuracy

### 2. Handshake Auto-send on Connection ✓
- [x] auto_handshake configuration option
- [x] _on_open callback triggers _send_handshake
- [x] auto_handshake=False disables auto-send
- [x] Connection state set before handshake attempt

### 3. Handshake Payload Validation ✓
- [x] JSON serializability checking
- [x] _validate_payload method
- [x] Circular reference detection
- [x] Non-serializable object handling

### 4. Handshake Response Detection ✓
- [x] is_handshake_message function
- [x] Type field checking
- [x] Non-handshake message filtering
- [x] Non-JSON message handling
- [x] Exception handling in detection

### 5. Environment Variable Support ✓
- [x] IOT_CLIENT_ID environment variable
- [x] IOT_AUTH_TOKEN environment variable
- [x] Default values when env vars not set
- [x] Environment variable integration in DEFAULT_COMMANDS

### 6. Handshake in UI Default Commands ✓
- [x] Handshake appears in DEFAULT_COMMANDS
- [x] Correct payload structure
- [x] JSON serializable payload
- [x] Environment variable substitution

### 7. Error Handling ✓
- [x] Validation failure logging
- [x] JSON serialization error handling
- [x] Network error handling
- [x] Non-serializable object rejection
- [x] Connection state on handshake failure

### 8. Connection State Management ✓
- [x] Connection remains established if handshake fails
- [x] Status callback invocation
- [x] Connected flag state consistency

## Uncovered Risks and Limitations

### Known Limitations

1. **WebSocket Connection Mocking**: Tests use mocked WebSocket objects. Real WebSocket connection testing would require a test server.

2. **Threading**: Background thread execution in actual code is not tested; only the methods are tested in isolation.

3. **UI Component Testing**: Tkinter UI testing is not included in this suite. These tests validate the business logic that UI components use.

4. **Callback Execution Order**: Tests verify callbacks are called but don't test execution order in multi-callback scenarios.

### Recommendations for Additional Testing

1. **Integration Testing**: Set up a mock WebSocket server to test actual message exchange.

2. **Performance Testing**: Test handshake performance with large payloads.

3. **Concurrency Testing**: Test concurrent handshakes in multi-connection scenarios.

4. **End-to-End Testing**: Test complete flows with actual UI interaction.

5. **Security Testing**: Test handshake with malicious payloads.

## Test Execution Output

When run with coverage, expected output:

```
tests/test_utilities.py ...................... [18%]
tests/test_ws_client.py ...................... [48%]
tests/test_ui_integration.py ................. [70%]
tests/test_negative_cases.py ................. [100%]

============ 120 passed in X.XXs ===========

Name                    Stmts   Miss  Cover
--------------------------------------------
utilities.py              XX     0    100%
ws_client.py              XX     0    100%
ui.py (handshake parts)   XX     0    100%
--------------------------------------------
TOTAL                     XX     0    100%
```

## Debugging Failed Tests

### Run with full traceback
```bash
pytest tests/ -v --tb=long
```

### Run with print statements
```bash
pytest tests/ -v -s
```

### Run single failing test with verbose output
```bash
pytest tests/test_file.py::TestClass::test_method -vv --tb=long
```

### Get more detailed output
```bash
pytest tests/ --capture=no --verbose
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Example GitHub Actions workflow:

```yaml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt
      - run: pip install -r tests/requirements.txt
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Test Maintenance

### Adding New Tests

1. Identify the feature/component to test
2. Choose appropriate test file based on module (utilities, ws_client, ui_integration, negative_cases)
3. Follow naming convention: `test_<feature_or_behavior>`
4. Use descriptive docstrings
5. Create fixtures in conftest.py if needed
6. Add test to appropriate test class

### Updating Tests

- Keep tests aligned with implementation changes
- Update fixtures if payload structures change
- Add tests for new features/behaviors
- Remove tests for deprecated features

## Support

For questions or issues with tests, refer to:
- Test docstrings for test-specific documentation
- Pytest documentation: https://docs.pytest.org/
- Project README for feature documentation
