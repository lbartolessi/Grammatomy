#!/usr/bin/env python3
"""
Test Runner Script for Grammatomy.

This utility sets up the environment (PYTHONPATH) and executes the full
test suite using pytest. It is designed to be run from the project root
or the tools directory.
"""

import os
import sys

import pytest


def main():
    """
    Configures the path and runs pytest on the 'tests' directory.
    """
    # Determine the project root (parent of the 'tools' directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    src_path = os.path.join(project_root, "src")
    tests_path = os.path.join(project_root, "tests")

    # Inject src into sys.path to ensure local modules are resolvable
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"🔧 Added to PYTHONPATH: {src_path}")

    print(f"🚀 Starting Test Suite in: {tests_path}")
    print("=" * 60)

    # Run pytest with verbose output
    exit_code = pytest.main(["-v", tests_path] + sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
