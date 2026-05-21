"""Quick reference for running SCRUM-127 tests."""

# QUICK START - Running Tests for SCRUM-127 Handshake Feature

## 1. Install test dependencies
pip install -r tests/requirements.txt

## 2. Run all tests
pytest tests/ -v

## 3. Run tests with coverage report
pytest tests/ --cov=. --cov-report=html

## 4. Run specific test module

### Utilities validation tests
pytest tests/test_utilities.py -v

### WebSocket client tests
pytest tests/test_ws_client.py -v

### UI integration tests
pytest tests/test_ui_integration.py -v

### Negative/edge case tests
pytest tests/test_negative_cases.py -v

## 5. Run specific test class
pytest tests/test_utilities.py::TestValidateHandshakePayload -v
pytest tests/test_ws_client.py::TestSendHandshake -v

## 6. Run specific test
pytest tests/test_utilities.py::TestValidateHandshakePayload::test_valid_handshake_payload_complete -v

## 7. Run with detailed output
pytest tests/ -vv --tb=short

## 8. Run tests and show print statements
pytest tests/ -v -s

## Expected Results

All 136 tests should pass:
- 61 unit tests (utilities, WebSocketManager)
- 30 integration tests (UI handshake handling)
- 45 negative/edge case tests

Expected output:
============ 136 passed in X.XXs ===========

## Test Files

1. test_utilities.py (27 tests)
   - TestValidateHandshakePayload (11 tests)
   - TestIsHandshakeMessage (7 tests)
   - TestDefaultCommands (9 tests)

2. test_ws_client.py (34 tests)
   - TestWebSocketManagerInit (6 tests)
   - TestValidatePayload (7 tests)
   - TestSendHandshake (7 tests)
   - TestOnOpen (4 tests)
   - TestSetConnected (3 tests)
   - TestHandshakeIntegration (7 tests)

3. test_ui_integration.py (30 tests)
   - TestUIHandshakeIntegration (5 tests)
   - TestUIHandshakeDetection (12 tests parametrized)
   - TestEnvironmentVariableSupport (2 tests)
   - TestUIDefaultCommandsRendering (3 tests)
   - TestHandshakeMessageEdgeCases (6 tests)

4. test_negative_cases.py (45 tests)
   - TestNegativeValidationCases (10 tests)
   - TestIsHandshakeMessageEdgeCases (2 tests)
   - TestWebSocketManagerNegativeCases (3 tests)
   - TestJSONSerializationEdgeCases (3 tests)
   - TestConcurrencyAndStateBehavior (2 tests)
   - TestErrorMessageAccuracy (1 test)
   - TestConnectorStateConsistency (2 tests)

## Coverage Analysis

After running with coverage, check:
1. utilities.py - 100% coverage
2. ws_client.py - 100% coverage for new handshake methods
3. ui.py - 100% coverage for _handle_ws_message changes

## Debugging Tips

If tests fail:
1. Check error message for specific assertion that failed
2. Run failing test in isolation: pytest <test_path> -vv
3. Add -s flag to see print statements
4. Check mock_logger calls to see what was logged

## Continuous Integration

To run in CI/CD:
```
pytest tests/ --cov=. --cov-report=xml --junitxml=test-results.xml
```

This generates:
- coverage.xml - For codecov
- test-results.xml - For test reporting
"""
