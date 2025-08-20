# tests/conftest.py
"""
Root level test configuration for QuackVerse monorepo.
This sets up the Python path for tests across the entire monorepo.
"""

import sys
from pathlib import Path

# Add all src directories to Python path
REPO_ROOT = Path(__file__).parent
for package_dir in ["quack-core", "ducktyper", "quackster"]:
    src_dir = REPO_ROOT / package_dir / "src"
    if src_dir.exists() and src_dir not in sys.path:
        sys.path.insert(0, str(src_dir.parent))

# Print current path setup for debugging
print(f"Python path: {sys.path}")