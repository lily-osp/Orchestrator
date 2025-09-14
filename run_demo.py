#!/usr/bin/env python3
"""
Demo runner script for the Orchestrator Platform.
Provides easy access to run demo and validation scripts.
"""

import sys
import os
import subprocess
from pathlib import Path

def list_demos():
    """List available demo scripts."""
    demos_dir = Path("demos")
    if not demos_dir.exists():
        print("No demos directory found")
        return []
    
    demo_files = list(demos_dir.glob("*.py"))
    return sorted([f.name for f in demo_files])

def run_demo(demo_name):
    """Run a specific demo script."""
    demo_path = Path("demos") / demo_name
    if not demo_path.exists():
        print(f"Demo '{demo_name}' not found")
        return 1
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    cmd = [sys.executable, str(demo_path)]
    
    print(f"Running demo: {demo_name}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print(f"\nDemo '{demo_name}' interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running demo '{demo_name}': {e}")
        return 1

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_demo.py <demo_name>")
        print("\nAvailable demos:")
        demos = list_demos()
        for demo in demos:
            print(f"  - {demo}")
        return 1
    
    demo_name = sys.argv[1]
    if not demo_name.endswith('.py'):
        demo_name += '.py'
    
    return run_demo(demo_name)

if __name__ == "__main__":
    sys.exit(main())