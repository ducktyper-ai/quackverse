# quackster/tests/conftest.py
"""
Shared fixtures for QuackSter tests.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch

# Add the src directories to the Python path if they're not already there
QUACKSTER_ROOT = Path(__file__).parent.parent
QUACKCORE_ROOT = QUACKSTER_ROOT.parent / "quackcore"

QUACKSTER_SRC = QUACKSTER_ROOT / "src"
QUACKCORE_SRC = QUACKCORE_ROOT / "src"

if QUACKSTER_SRC.exists() and str(QUACKSTER_SRC.parent) not in sys.path:
    sys.path.insert(0, str(QUACKSTER_SRC.parent))

if QUACKCORE_SRC.exists() and str(QUACKCORE_SRC.parent) not in sys.path:
    sys.path.insert(0, str(QUACKCORE_SRC.parent))

# Now the imports should work
from quackster.core.models import UserProgress


@pytest.fixture(autouse=True)
def patch_quackster_utils():
    """
    Patch quackster utilities for tests.
    """
    # Patch functions in quackster.core.utils
    with patch(
            "quackster.core.utils.get_user_data_dir", return_value="/mock/.quackverse"
    ):
        with patch(
                "quackster.core.utils.get_progress_file_path",
                return_value="/mock/.quackverse/progress.json",
        ):
            with patch(
                    "quackster.core.utils.load_progress",
                    return_value=UserProgress(github_username="testuser"),
            ):
                yield

# Import shared fixtures from quackcore
# You can add specific quackster fixtures below as needed