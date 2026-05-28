"""Test Runner and Documentation for IoT Device Management Handshake Tests"""

# Run tests with pytest:
# cd tests/
# pytest -v --tb=short
# 
# Or from project root:
# python -m pytest tests/ -v
#
# Generate coverage report:
# pytest tests/ --cov=. --cov-report=html
#
# Run specific test file:
# pytest tests/test_handshake.py -v
#
# Run specific test class:
# pytest tests/test_handshake.py::TestHandshakeMessageStructure -v
#
# Run specific test:
# pytest tests/test_handshake.py::TestHandshakeMessageStructure::test_handshake_in_default_commands -v

import subprocess
import sys


def run_tests(test_path=None, verbose=True, coverage=False):
    """
    Run pytest tests.
    
    Args:
        test_path: Specific test file or directory to run. None runs all tests.
        verbose: If True, use verbose output.
        coverage: If True, generate coverage report.
    """
    cmd = [sys.executable, "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])
    
    cmd.append("--tb=short")
    
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run IoT Device Management tests")
    parser.add_argument("--file", help="Specific test file to run")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")
    
    args = parser.parse_args()
    
    exit_code = run_tests(
        test_path=args.file,
        verbose=not args.quiet,
        coverage=args.coverage
    )
    
    sys.exit(exit_code)
