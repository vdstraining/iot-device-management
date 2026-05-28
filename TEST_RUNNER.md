# Quick Start - Running SCRUM-142 Handshake Tests

## Installation

```bash
pip install -r requirements.txt
```

## Run All Tests

```bash
python -m unittest discover -s . -p "test_handshake*.py" -v
```

**Expected Result**: ✅ Ran 74 tests in ~2 seconds - OK

## Run Individual Test Modules

```bash
# Unit tests for utilities.py (19 tests)
python -m unittest test_handshake_utilities -v

# Unit tests for ws_client.py (22 tests)
python -m unittest test_handshake_ws_client -v

# Integration tests for ui.py (33 tests)
python -m unittest test_handshake_integration -v
```

## Test Files

- **test_handshake_utilities.py** - Validates DEFAULT_COMMANDS Handshake structure
- **test_handshake_ws_client.py** - Validates WebSocketManager callback mechanism
- **test_handshake_integration.py** - Validates UI configuration and payload generation

## Coverage Summary

| Module | Tests | Status |
|--------|-------|--------|
| utilities.py | 19 | ✅ All Pass |
| ws_client.py | 22 | ✅ All Pass |
| ui.py | 33 | ✅ All Pass |
| **Total** | **74** | **✅ All Pass** |

## Quick Validation

```bash
# Quick check - all tests pass?
python -m unittest discover -s . -p "test_handshake*.py" 2>&1 | findstr "OK"
```

If you see `OK`, all tests passed! ✅
