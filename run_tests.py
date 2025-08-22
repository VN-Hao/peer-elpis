#!/usr/bin/env python3
"""
Test Runner for Peer Elpis

Usage:
    python run_tests.py                # Run all tests
    python run_tests.py voice         # Run voice tests only
    python run_tests.py integration   # Run integration tests only
    python run_tests.py debug         # Run debug utilities
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_voice_tests():
    """Run all voice-related tests."""
    print("=== Running Voice Tests ===")
    test_dir = Path("tests/voice")
    
    for test_file in test_dir.glob("test_*.py"):
        print(f"\nRunning {test_file.name}...")
        try:
            subprocess.run([sys.executable, str(test_file)], check=True)
            print(f"✅ {test_file.name} passed")
        except subprocess.CalledProcessError:
            print(f"❌ {test_file.name} failed")

def run_integration_tests():
    """Run integration tests."""
    print("=== Running Integration Tests ===")
    test_dir = Path("tests/integration")
    
    for test_file in test_dir.glob("test_*.py"):
        print(f"\nRunning {test_file.name}...")
        try:
            subprocess.run([sys.executable, str(test_file)], check=True)
            print(f"✅ {test_file.name} passed")
        except subprocess.CalledProcessError:
            print(f"❌ {test_file.name} failed")

def run_debug_utilities():
    """Run debug utilities."""
    print("=== Running Debug Utilities ===")
    debug_dir = Path("tests/debug")
    
    for debug_file in debug_dir.glob("debug_*.py"):
        print(f"\nRunning {debug_file.name}...")
        try:
            subprocess.run([sys.executable, str(debug_file)], check=True)
            print(f"✅ {debug_file.name} completed")
        except subprocess.CalledProcessError:
            print(f"❌ {debug_file.name} failed")

def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        # Run all tests
        run_voice_tests()
        run_integration_tests()
    else:
        test_type = sys.argv[1].lower()
        if test_type == "voice":
            run_voice_tests()
        elif test_type == "integration":
            run_integration_tests()
        elif test_type == "debug":
            run_debug_utilities()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available options: voice, integration, debug")
            sys.exit(1)

if __name__ == "__main__":
    main()
