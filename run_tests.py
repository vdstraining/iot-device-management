#!/usr/bin/env python3
"""
Simple test runner for SCRUM-81 handshake tests.
Run this script to execute all tests and generate a report.
"""

import sys
import subprocess

# Try to run pytest
try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_handshake.py", 
         "-v", "--tb=short", "--color=yes"],
        cwd=sys.path[0],
        capture_output=False
    )
    sys.exit(result.returncode)
except Exception as e:
    print(f"Error running tests: {e}", file=sys.stderr)
    sys.exit(1)
