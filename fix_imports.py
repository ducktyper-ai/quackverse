# fix_imports.py
"""
Script to fix imports in quackcore test files.
"""

import os
import sys
from pathlib import Path


def fix_imports(file_path):
    """Fix imports in a test file."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace 'from tests.quackcore.' with 'from tests.'
    content = content.replace('from ducktyper.src.ducktyper.', 'from ducktyper.')
    content = content.replace('import src.ducktyper.', 'import ducktyper.')

    # Write the fixed content back to the file
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"Fixed imports in {file_path}")


def find_and_fix_test_files(directory):
    """Find and fix imports in all Python test files in the directory."""
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    content = f.read()

                if 'from src.ducktyper.' in content or 'import src.ducktyper.' in content:
                    fix_imports(file_path)
                    count += 1

    return count


if __name__ == "__main__":
    # Get the quackcore tests directory
    quackcore_tests_dir = Path("ducktyper/src/ducktyper")

    if not quackcore_tests_dir.exists():
        print(f"Error: {quackcore_tests_dir} does not exist.")
        sys.exit(1)

    count = find_and_fix_test_files(quackcore_tests_dir)
    print(f"Fixed imports in {count} files.")