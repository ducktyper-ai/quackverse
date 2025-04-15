# src/quackster/core/utils.py
"""
Utility functions for the QuackCore quackster module.

This module provides functions for loading and saving user progress,
getting usernames, and other utility _operations.
"""

import getpass
import os

from quackcore.fs import expand_user_vars
from quackcore.fs.service.standalone import join_path, get_file_info, read_json, write_json, delete, copy, create_directory
from quackcore.logging import get_logger
from quackster.core.models import UserProgress

logger = get_logger(__name__)

# Default location for user progress file
DEFAULT_DATA_DIR = "~/.quack"
DEFAULT_PROGRESS_FILE = "ducktyper_user.json"


def get_user_data_dir() -> str:
    """
    Get the directory for user data.

    Returns:
        Absolute path to the user data directory as a string.
    """
    # Use fs.expand_user_vars to process shell shortcuts (e.g., '~').
    data_dir = os.environ.get("QUACK_DATA_DIR", DEFAULT_DATA_DIR)
    # Expand the user variables.
    expanded = expand_user_vars(data_dir)
    # Create the directory if it does not exist.
    create_directory(expanded, exist_ok=True)
    return expanded


def get_progress_file_path() -> str:
    """
    Get the path to the user progress file.

    Returns:
        Absolute path to the user progress file as a string.
    """
    data_dir = get_user_data_dir()
    file_name = os.environ.get("QUACK_PROGRESS_FILE", DEFAULT_PROGRESS_FILE)
    return join_path(data_dir, file_name)


def get_github_username() -> str:
    """
    Get the user's GitHub username.

    Checks in the following order:
      1. The GITHUB_USERNAME environment variable.
      2. The Git configuration.
      3. Prompts the user.
      4. Falls back to the system username.

    Returns:
        GitHub username as a string.
    """
    username = os.environ.get("GITHUB_USERNAME")
    if username:
        return username

    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    try:
        username = input("Enter your GitHub username: ")
        if username:
            return username
    except Exception:
        pass

    return getpass.getuser()


def load_progress() -> UserProgress:
    """
    Load user progress from the progress file.

    If the file doesn't exist or can't be loaded, returns a new UserProgress.

    Returns:
        A UserProgress instance.
    """
    file_path = get_progress_file_path()

    result = get_file_info(file_path)
    if not result.success or not result.exists:
        logger.debug(f"Progress file not found at {file_path}, creating new progress")
        return create_new_progress()

    try:
        result = read_json(file_path)
        if not result.success:
            logger.warning(f"Failed to read progress file: {result.error}")
            return create_new_progress()

        data = result.data
        progress = UserProgress.model_validate(data)
        logger.debug(
            f"Loaded user progress: {progress.xp} XP, {len(progress.completed_quest_ids)} quests"
        )
        return progress

    except Exception as e:
        logger.warning(f"Error loading progress file: {str(e)}")
        return create_new_progress()


def save_progress(progress: UserProgress) -> bool:
    """
    Save user progress to the progress file.

    Args:
        progress: The UserProgress instance to save.

    Returns:
        True if saved successfully; False otherwise.
    """
    file_path = get_progress_file_path()
    data = progress.model_dump()

    try:
        result = write_json(file_path, data)
        if not result.success:
            logger.error(f"Failed to save progress file: {result.error}")
            return False

        logger.debug(
            f"Saved user progress: {progress.xp} XP, {len(progress.completed_quest_ids)} quests"
        )
        return True
    except Exception as e:
        logger.error(f"Error saving progress file: {str(e)}")
        return False


def create_new_progress() -> UserProgress:
    """
    Create new user progress.

    Returns:
        A new UserProgress instance.
    """
    github_username = get_github_username()
    progress = UserProgress(github_username=github_username)
    save_progress(progress)
    return progress


def reset_progress() -> bool:
    """
    Reset user progress by deleting the progress file.

    Returns:
        True if reset successfully; False otherwise.
    """
    file_path = get_progress_file_path()
    result = get_file_info(file_path)
    if not result.success or not result.exists:
        logger.debug(f"No progress file to reset at {file_path}")
        return True

    result = delete(file_path)
    if not result.success:
        logger.error(f"Failed to delete progress file: {result.error}")
        return False

    logger.info(f"Reset user progress by deleting {file_path}")
    return True


def backup_progress(backup_name: str = None) -> bool:
    """
    Create a backup of the user progress file.

    Args:
        backup_name: Optional name for the backup file. If not provided, a timestamp is used.

    Returns:
        True if backup was created successfully; False otherwise.
    """
    import datetime

    file_path = get_progress_file_path()
    result = get_file_info(file_path)
    if not result.success or not result.exists:
        logger.debug(f"No progress file to backup at {file_path}")
        return False

    if not backup_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"ducktyper_user_{timestamp}.json"

    data_dir = get_user_data_dir()
    backup_path = join_path(data_dir, backup_name)
    result = copy(file_path, backup_path)
    if not result.success:
        logger.error(f"Failed to create backup: {result.error}")
        return False

    logger.info(f"Created backup of user progress at {backup_path}")
    return True
