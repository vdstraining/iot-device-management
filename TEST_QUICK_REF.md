# Quick Reference: SCRUM-53 Test Commands

## Installation
```bash
pip install -r requirements.txt
```

## Running Tests

### All Tests
```bash
python -m pytest tests/ -v
```
Expected: **72 tests PASSED**

### By Category
```bash
# Unit tests (isolated component testing)
python -m pytest tests/test_ws_client_handshake.py -v

# Integration tests (component interactions)
python -m pytest tests/test_integration_handshake.py -v

# Validation tests (edge cases and data validation)
python -m pytest tests/test_validation_handshake.py -v
```

### Coverage Report
```bash
# Generate HTML coverage report
python -m pytest tests/ --cov=. --cov-report=html

# View in browser: htmlcov/index.html
```

### Quick Commands
```bash
# Minimal output
python -m pytest tests/ -q

# Show print statements
python -m pytest tests/ -v -s

# Run failed tests only
python -m pytest tests/ --lf

# Run specific test
python -m pytest tests/test_ws_client_handshake.py::TestWebSocketHandshakeSend::test_handshake_payload_structure -v
```

## Using Test Runner Script
```bash
python run_tests.py all          # All tests
python run_tests.py unit         # Unit tests
python run_tests.py integration  # Integration tests
python run_tests.py validation   # Validation tests
python run_tests.py coverage     # With coverage report
python run_tests.py quick        # Quick run
```

## Test Files Overview

| File | Tests | Purpose |
|------|-------|---------|
| test_ws_client_handshake.py | 27 | Unit tests for _send_handshake() and _on_open() |
| test_integration_handshake.py | 38 | Integration: manager + ui + commands |
| test_validation_handshake.py | 27 | Payload validation, edge cases, exceptions |
| conftest.py | - | Pytest fixtures and configuration |

## Coverage Summary
- **Total Coverage**: 75%
- **Unit Tests**: 97% coverage
- **Integration Tests**: 97% coverage  
- **Validation Tests**: 99% coverage

## Test Results
✅ All 72 tests PASSED in 0.77s

## Key Features Tested
- ✅ Handshake method (_send_handshake)
- ✅ Automatic send on connection (_on_open)
- ✅ Client ID parameter handling
- ✅ JSON payload structure
- ✅ Error logging
- ✅ DEFAULT_COMMANDS integration
- ✅ Reconnection scenarios
- ✅ Backward compatibility
- ✅ Edge cases (unicode, special chars, long IDs)
- ✅ Exception handling

## Viewing Coverage Report
After running coverage tests:
```bash
# Open HTML report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
```

## Notes
- All tests use mocking to avoid external dependencies
- Tests are deterministic and fast (< 1 second)
- No database or server required
- Safe to run in parallel
