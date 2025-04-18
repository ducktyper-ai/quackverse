# ducktyper/tests/conftest.py
"""
Shared fixtures for DuckTyper tests.
"""

import sys
from pathlib import Path

# Add the src directories to the Python path if they're not already there
DUCKTYPER_ROOT = Path(__file__).parent.parent
QUACKCORE_ROOT = DUCKTYPER_ROOT.parent / "quackcore"

DUCKTYPER_SRC = DUCKTYPER_ROOT / "src"
QUACKCORE_SRC = QUACKCORE_ROOT / "src"

if DUCKTYPER_SRC.exists() and str(DUCKTYPER_SRC.parent) not in sys.path:
    sys.path.insert(0, str(DUCKTYPER_SRC.parent))

if QUACKCORE_SRC.exists() and str(QUACKCORE_SRC.parent) not in sys.path:
    sys.path.insert(0, str(QUACKCORE_SRC.parent))

# Import shared fixtures from quackcore as needed
# You can add ducktyper-specific fixtures below
