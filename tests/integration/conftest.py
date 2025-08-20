# tests/integration/conftest.py
"""
Shared fixtures for integration tests across all packages.
"""

import sys
import os
from pathlib import Path
import pytest

# Get repository root directory
REPO_ROOT = Path(__file__).parent.parent.parent

# Add all src directories to Python path
PACKAGES = ["quack-core", "ducktyper", "quackster"]
for package in PACKAGES:
    package_src = REPO_ROOT / package / "src"
    if package_src.exists() and str(package_src.parent) not in sys.path:
        sys.path.insert(0, str(package_src.parent))

# Import fixtures from individual packages
try:
    # Import fixtures from quack-core
    from quackcore.tests.conftest import (
        temp_dir,
        test_file,
        test_binary_file,
        sample_config,
        mock_env_vars,
        mock_project_structure,
        mock_plugin,
    )
except ImportError as e:
    print(f"Warning: Unable to import quack-core fixtures: {e}")

try:
    # Import fixtures from quackster
    from quackster.tests.conftest import patch_quackster_utils
except ImportError as e:
    print(f"Warning: Unable to import quackster fixtures: {e}")

# Add package-specific integration test fixtures below