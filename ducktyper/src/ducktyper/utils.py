# src/tests/utils.py
"""
Utility functions for DuckTyper.

This module provides common helper functions used throughout DuckTyper.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple, Union


def find_executable(name: str) -> Optional[str]:
    """
    Find the path to an executable on the system PATH.

    Args:
        name: Name of the executable to find

    Returns:
        Path to the executable if found, None otherwise
    """
    return shutil.which(name)


def ensure_dir_exists(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_default_config_path() -> Path:
    """
    Get the default path for DuckTyper configuration.

    Returns:
        Path to the default configuration file
    """
    config_dir = Path.home() / ".quack"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.yaml"


def get_package_version() -> str:
    """
    Get the DuckTyper package version.

    Returns:
        Version string
    """
    from ducktyper import __version__
    return __version__


def get_editor_command() -> Tuple[str, list[str]]:
    """
    Get the user's preferred editor command.

    Returns:
        Tuple of (editor_command, base_arguments)
    """
    # Check environment variables for editor preference
    for env_var in ["DUCKTYPER_EDITOR", "EDITOR", "VISUAL"]:
        editor = os.environ.get(env_var)
        if editor:
            # Parse the editor command (handling cases like "code -w")
            parts = editor.split()
            return parts[0], parts[1:]

    # Default editors based on platform
    if sys.platform == "win32":
        # Try to find common editors on Windows
        for editor in ["code", "notepad++", "notepad"]:
            path = find_executable(editor)
            if path:
                return path, []
        return "notepad", []
    else:
        # Try to find common editors on Unix systems
        for editor in ["nano", "vim", "vi", "emacs"]:
            path = find_executable(editor)
            if path:
                return path, []
        return "nano", []


def run_editor(file_path: Union[str, Path]) -> bool:
    """
    Open a file in the user's preferred editor.

    Args:
        file_path: Path to the file to edit

    Returns:
        True if successful, False otherwise
    """
    editor_cmd, base_args = get_editor_command()
    cmd = [editor_cmd] + base_args + [str(file_path)]

    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def parse_key_value(arg: str) -> Tuple[str, str]:
    """
    Parse a key=value argument.

    Args:
        arg: String in the format "key=value"

    Returns:
        Tuple of (key, value)

    Raises:
        ValueError: If the argument is not in the expected format
    """
    if "=" not in arg:
        raise ValueError(f"Invalid format: {arg}. Expected 'key=value'")

    key, value = arg.split("=", 1)
    return key.strip(), value.strip()


def truncate_path(path: Union[str, Path], max_length: int = 40) -> str:
    """
    Truncate a path to a maximum length, preserving the filename.

    Args:
        path: Path to truncate
        max_length: Maximum length

    Returns:
        Truncated path string
    """
    path_str = str(path)

    if len(path_str) <= max_length:
        return path_str

    # Split into directory and filename
    dirname, filename = os.path.split(path_str)

    # Ensure the filename fits
    if len(filename) >= max_length - 5:
        # If filename is too long, truncate it
        return f"...{filename[-(max_length - 5):]}"

    # Calculate how much of the directory to keep
    dir_length = max_length - len(filename) - 5  # Account for "/.../"

    if dir_length <= 0:
        return f".../{filename}"

    return f"{dirname[:dir_length]}.../{filename}"


def get_terminal_size() -> Tuple[int, int]:
    """
    Get the terminal size.

    Returns:
        Tuple of (width, height)
    """
    return shutil.get_terminal_size((80, 24))


def safe_import(module_name: str) -> Optional[object]:
    """
    Safely import a module, returning None if it doesn't exist.

    Args:
        module_name: Name of the module to import

    Returns:
        Imported module or None if import failed
    """
    try:
        return __import__(module_name)
    except ImportError:
        return None


def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds as a human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def get_cache_dir() -> Path:
    """
    Get the DuckTyper cache directory.

    Returns:
        Path to the cache directory
    """
    cache_dir = Path.home() / ".cache" / "tests"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_session_id() -> str:
    """
    Generate a unique session ID.

    Returns:
        Session ID string
    """
    import uuid
    return str(uuid.uuid4())


def is_command_available(command: str) -> bool:
    """
    Check if a shell command is available.

    Args:
        command: Command name to check

    Returns:
        True if the command is available, False otherwise
    """
    return find_executable(command) is not None


def get_user_home_dir() -> Path:
    """
    Get the user's home directory.

    Returns:
        Path to the home directory
    """
    return Path.home()


def find_quack_project_root(start_dir: Optional[Union[str, Path]] = None) -> Optional[
    Path]:
    """
    Find the root directory of a QuackVerse project by looking for markers.

    Args:
        start_dir: Directory to start the search from (defaults to current directory)

    Returns:
        Path to the project root if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    start_path = Path(start_dir).resolve()

    # Look for these files/dirs as markers of project root
    markers = [
        "pyproject.toml",
        "quack_config.yaml",
        "quack.yaml",
        ".quack",
    ]

    current = start_path
    while current != current.parent:  # Stop at filesystem root
        # Check for any marker
        for marker in markers:
            if (current / marker).exists():
                return current

        # Move up one directory
        current = current.parent

    # No project root found
    return None


def ensure_single_instance(name: str) -> bool:
    """
    Ensure only one instance of a command is running.

    This is a simplified version that doesn't actually create a lock file
    for process monitoring. In a real implementation, you'd create a lock
    file and track the PID.

    Args:
        name: Command name

    Returns:
        True if this is the only instance, False otherwise
    """
    # This is just a placeholder for the concept
    # In a real implementation, you'd use file locks or similar
    return True


def get_platform_info() -> dict:
    """
    Get information about the platform.

    Returns:
        Dictionary with platform information
    """
    import platform

    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }