#!/usr/bin/env python3
"""
Test Runner Script for Grammatomy.

This utility sets up the environment (PYTHONPATH) and executes the full
test suite using pytest. It is designed to be run from the project root
or the tools directory.
"""

import importlib.util
import logging
import os
import sys

import pytest


def main():
    """
    Configures the path and runs pytest on the 'tests' directory.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Determine the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    tests_path = os.path.join(project_root, "tests")
    src_path = os.path.join(project_root, "src")

    # Add project root and src to sys.path to resolve imports like 'src.api...' and 'core.grammatomy...'
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    logging.info("🚀 Starting Test Suite in: %s", tests_path)
    logging.info("=" * 60)

    # Check if pytest-cov is installed to avoid errors with pytest.ini configuration
    has_cov = importlib.util.find_spec("pytest_cov") is not None
    pytest_args = ["-v", tests_path] + sys.argv[1:]

    if not has_cov:
        logging.warning(
            "⚠️  pytest-cov not found. Disabling coverage reports defined in pytest.ini."
        )
        pytest_args.extend(["-o", "addopts=--verbose"])

    exit_code = pytest.main(pytest_args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
