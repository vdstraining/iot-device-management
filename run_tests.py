"""
Test runner script for SCRUM-53 handshake feature tests.

This script provides easy commands for running tests with various options.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results."""
    print(f"\n{'='*80}")
    print(f"{description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    """Main test runner."""
    test_dir = Path(__file__).parent
    
    commands = {
        "all": (
            f"python -m pytest {test_dir} -v",
            "Running all tests"
        ),
        "unit": (
            f"python -m pytest {test_dir}/test_ws_client_handshake.py -v",
            "Running unit tests (ws_client_handshake)"
        ),
        "integration": (
            f"python -m pytest {test_dir}/test_integration_handshake.py -v",
            "Running integration tests"
        ),
        "validation": (
            f"python -m pytest {test_dir}/test_validation_handshake.py -v",
            "Running validation tests"
        ),
        "coverage": (
            f"python -m pytest {test_dir} --cov=. --cov-report=html --cov-report=term-missing",
            "Running tests with coverage report"
        ),
        "quick": (
            f"python -m pytest {test_dir} -q",
            "Quick test run (minimal output)"
        ),
        "failed": (
            f"python -m pytest {test_dir} --lf -v",
            "Running only failed tests"
        ),
        "markers": (
            f"python -m pytest {test_dir} -v -m 'unit or integration'",
            "Running tests by markers"
        ),
    }
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type in commands:
            cmd, desc = commands[test_type]
            success = run_command(cmd, desc)
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown test type: {test_type}")
            print(f"Available options: {', '.join(commands.keys())}")
            sys.exit(1)
    else:
        print("Test Runner for SCRUM-53 Handshake Feature")
        print("="*80)
        print("\nUsage: python run_tests.py [test_type]\n")
        print("Available test types:")
        for test_type, (cmd, desc) in commands.items():
            print(f"  {test_type:15} - {desc}")
        print("\nExample: python run_tests.py all")


if __name__ == "__main__":
    main()
