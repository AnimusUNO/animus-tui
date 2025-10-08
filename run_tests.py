#!/usr/bin/env python3
"""
Test runner for Letta Chat Client
Runs all tests with coverage reporting
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run the test suite with coverage"""
    print("=" * 60)
    print("           LETTA CHAT CLIENT - TEST SUITE")
    print("=" * 60)
    print()
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not running in a virtual environment")
        print("Consider running: python -m venv venv && .\\venv\\Scripts\\activate")
        print()
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--verbose",
        "--tb=short",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    print("Running tests...")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True)
        print()
        print("=" * 60)
        print("           ALL TESTS PASSED! OK")
        print("=" * 60)
        print()
        print("Coverage report generated in htmlcov/index.html")
        return True
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 60)
        print("           TESTS FAILED! ERROR")
        print("=" * 60)
        print(f"Exit code: {e.returncode}")
        return False
    except FileNotFoundError:
        print("Error: pytest not found. Install test dependencies:")
        print("pip install -r requirements-test.txt")
        return False

def install_test_deps():
    """Install test dependencies"""
    print("Installing test dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"], check=True)
        print("Test dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install test dependencies: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        success = install_test_deps()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
