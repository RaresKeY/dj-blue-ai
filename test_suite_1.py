"""
Pre-build script to run logic tests with a timeout.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    print("--- Running Pre-Build Logic Tests ---")
    
    # Path to venv python
    venv_python = Path(".venv/bin/python")
    if not venv_python.exists():
        # Fallback for systems where venv is elsewhere or using global
        venv_python = Path(sys.executable)

    test_file = "architects/tests/test_logic.py"
    
    try:
        # Run tests with a 30-second timeout to allow for multiple real API calls
        result = subprocess.run(
            [str(venv_python), test_file],
            timeout=30,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("✅ All logic tests passed.")
        return True
    except subprocess.TimeoutExpired:
        print("❌ Error: Logic tests timed out after 10 seconds.")
        return False
    except subprocess.CalledProcessError as e:
        print("❌ Error: Logic tests failed.")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Unexpected error running tests: {e}")
        return False

if __name__ == "__main__":
    if run_tests():
        sys.exit(0)
    else:
        sys.exit(1)
