# src/quackcore/teaching/npc/memory.py
"""
Memory management for the Quackster teaching NPC.

This module provides functions for loading user information into a
format that the NPC can use to personalize interactions.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from quackcore.fs import service as fs
from quackcore.logging import get_logger
from quackcore.teaching import badges, quests
from quackcore.teaching.core.utils import get_user_data_dir, load_progress
from quackcore.teaching.npc.schema import UserMemory

logger = get_logger(__name__)

# Memory persistence settings
MEMORY_FILE_NAME = "quackster_memory.json"
MEMORY_EXPIRES_DAYS = 30  # Memory expires after 30 days of inactivity


def _get_memory_file_path() -> Path:
    """
    Get the path to the user's memory file.

    Returns:
        Path to the user memory file
    """
    data_dir = get_user_data_dir()
    return data_dir / MEMORY_FILE_NAME


def _load_persistent_memory(github_username: str | None) -> dict[str, Any] | None:
    """
    Load persistent memory from file.

    Args:
        github_username: GitHub username to load memory for

    Returns:
        User memory data or None if not found/expired
    """
    file_path = _get_memory_file_path()

    # Check if memory file exists
    result = fs.get_file_info(file_path)
    if not result.success or not result.exists:
        logger.debug(f"No memory file found at {file_path}")
        return None

    try:
        # Read memory file
        read_result = fs.read_json(file_path)
        if not read_result.success:
            logger.warning(f"Failed to read memory file: {read_result.error}")
            return None

        memory_data = read_result.data

        # Check if memory is for this user
        stored_username = memory_data.get("github_username")
        if github_username and stored_username != github_username:
            logger.debug(f"Memory file is for a different user: {stored_username}")
            return None

        # Check if memory has expired
        last_interaction = memory_data.get("last_interaction")
        if last_interaction:
            try:
                last_time = datetime.fromisoformat(last_interaction)
                expiry_time = datetime.now() - timedelta(days=MEMORY_EXPIRES_DAYS)
                if last_time < expiry_time:
                    logger.debug("Memory has expired, creating fresh memory")
                    return None
            except (ValueError, TypeError):
                logger.warning("Invalid timestamp in memory file")

        return memory_data
    except Exception as e:
        logger.warning(f"Error loading memory: {str(e)}")
        return None


def _save_persistent_memory(memory: UserMemory) -> bool:
    """
    Save user memory to a persistent file.

    Args:
        memory: User memory to save

    Returns:
        True if saved successfully, False otherwise
    """
    file_path = _get_memory_file_path()

    try:
        # Convert to dict and save
        memory_dict = memory.model_dump()
        result = fs.write_json(file_path, memory_dict)
        if not result.success:
            logger.warning(f"Failed to save memory: {result.error}")
            return False

        logger.debug(f"Saved user memory for {memory.github_username}")
        return True
    except Exception as e:
        logger.warning(f"Error saving memory: {str(e)}")
        return False


def get_user_memory(github_username: str = None) -> UserMemory:
    """
    Get memory data about a user for the NPC.

    Args:
        github_username: Optional GitHub username to load
            If None, tries to load the current user's progress

    Returns:
        User memory data
    """
    # Load user progress
    user = load_progress()

    # If a specific username was provided, override the loaded username
    if github_username:
        user.github_username = github_username

    # Try loading persistent memory
    persistent_memory = _load_persistent_memory(user.github_username)

    # Get badge and quest data
    user_badges = badges.get_user_badges(user)
    badge_names = [badge.name for badge in user_badges]

    quest_data = quests.get_user_quests(user)
    completed_quests = [quest.name for quest in quest_data["completed"]]

    # Create base memory object
    memory = UserMemory(
        github_username=user.github_username,
        xp=user.xp,
        level=user.get_level(),
        completed_quests=user.completed_quest_ids,
        badges=user.earned_badge_ids,
        # Initialize with default values or values from persistent memory
        conversation_count=persistent_memory.get("conversation_count", 0)
        if persistent_memory
        else 0,
        last_interaction=datetime.now().isoformat(),
        interests=persistent_memory.get("interests", []) if persistent_memory else [],
        custom_data={},
    )

    # Add badge and quest names for easier reference
    memory.custom_data["badge_names"] = badge_names
    memory.custom_data["completed_quest_names"] = completed_quests

    # Add next level info
    memory.custom_data["xp_to_next_level"] = user.get_xp_to_next_level()
    memory.custom_data["next_level"] = user.get_level() + 1

    # Add suggested quests
    suggested = quests.get_suggested_quests(user, limit=3)
    memory.custom_data["suggested_quests"] = [
        {
            "id": q.id,
            "name": q.name,
            "description": q.description,
            "reward_xp": q.reward_xp,
        }
        for q in suggested
    ]

    # Add additional data from persistent memory if available
    if persistent_memory and isinstance(persistent_memory, dict):
        # Transfer long-term memory attributes
        if "favorite_topics" in persistent_memory:
            memory.custom_data["favorite_topics"] = persistent_memory.get(
                "favorite_topics", []
            )

        if "stuck_points" in persistent_memory:
            memory.custom_data["stuck_points"] = persistent_memory.get(
                "stuck_points", []
            )

        if "recent_quests_discussed" in persistent_memory:
            memory.custom_data["recent_quests_discussed"] = persistent_memory.get(
                "recent_quests_discussed", []
            )

        if "learning_style" in persistent_memory:
            memory.custom_data["learning_style"] = persistent_memory.get(
                "learning_style"
            )

        if "session_history" in persistent_memory:
            memory.custom_data["session_history"] = persistent_memory.get(
                "session_history", []
            )

            # Limit session history to last 10 entries
            if len(memory.custom_data["session_history"]) > 10:
                memory.custom_data["session_history"] = memory.custom_data[
                    "session_history"
                ][-10:]

    return memory
