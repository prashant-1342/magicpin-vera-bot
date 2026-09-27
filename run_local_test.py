#!/usr/bin/env python3
"""
Local test runner to verify Vera API with Judge Simulator scenarios.
Can test via live FastAPI server or in-memory client.
"""

import sys
import os
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_tests():
    print("=" * 70)
    print("Running Vera Bot Automated Test Suite")
    print("=" * 70)

    result = subprocess.run([sys.executable, "-m", "pytest", "-v", "tests/test_bot.py"], cwd=BASE_DIR)
    if result.returncode != 0:
        print("\n[FAIL] Tests failed!")
        sys.exit(1)
    
    print("\n[PASS] All Vera core tests passed successfully!")


if __name__ == "__main__":
    run_tests()
