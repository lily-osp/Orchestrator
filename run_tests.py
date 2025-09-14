#!/usr/bin/env python3
"""
Test runner script for the Orchestrator Platform.
Runs all tests from the tests/ directory with proper path configuration.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Run all tests with proper Python path configuration."""
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Run pytest with the tests directory
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]
    
    print("Running Orchestrator Platform tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())