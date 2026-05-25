# Test Data for SCRUM-107 Handshake Tests

This directory contains test data files and mock configurations used by the handshake test suites.

## Configuration Files

### config_valid.json
Complete and valid handshake configuration with all fields populated:
- `enabled`: true
- `auto_trigger`: true
- `clientId`: "test-handshake-device-001"
- Full capabilities list
- Complete session_metadata with test identifiers
- Authentication context with test token

**Use case**: Testing normal operation, payload building with complete config

### config_disabled.json
Configuration with handshake disabled:
- `enabled`: false
- `auto_trigger`: false
- Minimal other fields

**Use case**: Testing disabled handshake behavior, ensuring no messages are sent when disabled

### config_minimal.json
Minimal configuration with only required flags:
- `enabled`: true
- `auto_trigger`: true
- Other fields omitted (will use defaults)

**Use case**: Testing default value merging, backward compatibility

## Response Files

### response_success.json
Mock server response indicating successful handshake:
- `action`: "handshake_ack"
- `status`: "success"
- `sessionId`: "sess-test-abc123"
- Additional server features and capabilities

**Use case**: Testing successful handshake scenario, logging of positive responses

### response_error.json
Mock server response indicating handshake failure:
- `action`: "handshake_ack"
- `status`: "error"
- `error_code`: "AUTH_FAILED"
- Error message details

**Use case**: Testing error handling, failed authentication scenario

### response_invalid.txt
Invalid/malformed JSON content:
- Intentionally incomplete JSON structure

**Use case**: Testing error handling for malformed responses, graceful failure handling

## Usage in Tests

### Load Configuration
```python
import json

with open('test_data/config_valid.json', 'r') as f:
    config = json.load(f)
```

### Load Response
```python
with open('test_data/response_success.json', 'r') as f:
    response = json.load(f)
```

### Test Malformed Data
```python
with open('test_data/response_invalid.txt', 'r') as f:
    invalid_content = f.read()
    # Try to parse as JSON - should fail gracefully
```

## Test Data Naming Convention

- `config_*.json`: Configuration files for testing config loading
- `response_*.json`: Valid server response files
- `response_*.txt`: Invalid/malformed response files

## Adding New Test Data

When adding new test data files:
1. Use descriptive names
2. Add corresponding `.json` extension for valid data
3. Use `.txt` for invalid/edge-case data
4. Document the purpose in this README
5. Ensure files are valid JSON where appropriate

## Integration with Tests

Test files can reference this data:

```python
import os
import json

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'test_data')

def load_test_config(filename):
    with open(os.path.join(TEST_DATA_DIR, filename), 'r') as f:
        return json.load(f)
```
