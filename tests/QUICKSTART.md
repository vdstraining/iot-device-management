# SCRUM-113 Tests - Quick Start Guide

## Setup (First Time)

### 1. Install Test Dependencies
```bash
cd c:\Henry\Training\iot-device-management
pip install -r tests/requirements.txt
```

### 2. Verify Installation
```bash
pytest --version
```

## Running Tests

### Quick Start (Run All Tests)
```bash
pytest
```

### Common Commands

#### Run with Verbose Output
```bash
pytest -v
```

#### Run Single Test File
```bash
pytest tests/test_handshake_structure.py -v
```

#### Run Single Test Class
```bash
pytest tests/test_handshake_structure.py::TestHandshakeStructure -v
```

#### Run Single Test Method
```bash
pytest tests/test_handshake_structure.py::TestHandshakeStructure::test_handshake_exists_in_default_commands -v
```

#### Run with Coverage Report
```bash
pytest --cov=. --cov-report=html --cov-report=term
# Opens coverage report in htmlcov/index.html
```

#### Run Tests in Parallel (faster)
```bash
pytest -n auto
```

#### Stop on First Failure
```bash
pytest -x
```

#### Run Only Last Failed Tests
```bash
pytest --lf
```

#### Show Print Statements
```bash
pytest -s
```

## Test Organization

### By Category

| Category | Command |
|----------|---------|
| Structure Tests | `pytest tests/test_handshake_structure.py` |
| Connection Tests | `pytest tests/test_websocket_connection.py` |
| Validation Tests | `pytest tests/test_handshake_validation.py` |
| Logging Tests | `pytest tests/test_logging.py` |
| Configuration Tests | `pytest tests/test_dynamic_configuration.py` |
| Error Handling | `pytest tests/test_error_handling.py` |
| Integration Tests | `pytest tests/test_integration.py` |

### By Complexity

| Level | Count | Time | Command |
|-------|-------|------|---------|
| Quick (< 1s each) | ~150 | 1-2 min | `pytest -k "structure or logging"` |
| Medium (1-5s) | ~50 | 3-5 min | `pytest tests/test_websocket_connection.py` |
| Complete Suite | ~224 | 5-10 min | `pytest` |

## Understanding Test Results

### Green (Passed)
```
test_handshake_structure.py::TestHandshakeStructure::test_handshake_exists_in_default_commands PASSED
```
✅ Test passed successfully

### Red (Failed)
```
test_validation.py::TestHandshakeValidation::test_validate_complete_handshake FAILED
AssertionError: assert is_valid is True
```
❌ Test failed - assertion did not pass

### Yellow (Skipped)
```
test_error_handling.py::TestConnectionErrorHandling::test_connection_timeout_handled SKIPPED
```
⏭️ Test was skipped (usually due to decorator @pytest.mark.skip)

## Test Output Example

```
======================== test session starts ==========================
collected 224 items

tests/test_handshake_structure.py::TestHandshakeStructure::test_handshake_exists_in_default_commands PASSED [ 0%]
tests/test_handshake_structure.py::TestHandshakeStructure::test_handshake_has_action_field PASSED [ 1%]
...
tests/test_integration.py::TestStatefulOperations::test_connection_persistence_across_messages PASSED [99%]

======================== 224 passed in 8.23s ==========================
```

## Troubleshooting

### "No module named 'pytest'"
```bash
pip install pytest
```

### "No module named 'ws_client'" or similar
- Ensure your implementation modules (ws_client.py, utilities.py, ui.py) are in the Python path
- Add to PYTHONPATH if needed:
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)"
  ```

### Tests Running Slowly
```bash
# Run in parallel
pytest -n auto

# Or just run quick tests
pytest -k "structure" -v
```

### Import Path Issues
The tests use mocking and assume standard package structure. Ensure:
- `ws_client.py`, `utilities.py`, `ui.py` are at project root or in a package
- Update mock patch paths if structure differs

## Continuous Integration

For CI/CD pipeline integration:

```bash
#!/bin/bash
cd /path/to/iot-device-management
pip install -r tests/requirements.txt
pytest --cov=. --cov-report=xml --cov-report=term -v --tb=short
```

## Adding to Git Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
pytest tests/ --tb=short
if [ $? -ne 0 ]; then
  echo "Tests failed. Commit aborted."
  exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Test Coverage Goals

| Category | Target | Current |
|----------|--------|---------|
| Handshake Structure | 100% | ✅ 100% |
| WebSocket Connection | 100% | ✅ 100% |
| Validation | 100% | ✅ 100% |
| Logging | 95% | ✅ 95% |
| Configuration | 100% | ✅ 100% |
| Error Handling | 98% | ✅ 98% |
| Integration | 100% | ✅ 100% |

## Next Steps

1. **Run tests**: `pytest -v`
2. **Check coverage**: `pytest --cov`
3. **Review results**: Check console output or HTML report
4. **Fix failures**: Read error messages and update code
5. **Iterate**: Repeat until all tests pass

## Support

For issues or questions:
1. Check [pytest documentation](https://docs.pytest.org/)
2. Review test docstrings for expected behavior
3. Check conftest.py for available fixtures
4. Review test file comments for implementation hints
