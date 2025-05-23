# quackcore/tests/test_helper.py
"""
Helper module to set up the Python path for quackcore tests.
This should be imported at the beginning of conftest.py.
"""

import os
import sys
from pathlib import Path


def setup_python_path():
    """
    Adds the necessary directories to the Python path.
    """
    # Get the absolute path to the quackcore directory
    quackcore_dir = Path(__file__).parent.parent.absolute()
    src_dir = quackcore_dir / "src"

    # Add src directory to Python path
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    # Print current working directory and Python path for debugging
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

    # Verify that the quackcore module can be found
    try:
        import quackcore
        print(f"quackcore found at: {quackcore.__file__}")
    except ImportError as e:
        print(f"Error importing quackcore: {e}")
        # Try a different approach
        try:
            quackcore_path = os.path.join(str(src_dir), "quackcore")
            if os.path.exists(quackcore_path):
                sys.path.insert(0, quackcore_path)
                print(f"Added quackcore directory to path: {quackcore_path}")
        except Exception as e:
            print(f"Failed to add quackcore to path: {e}")


setup_python_path()
