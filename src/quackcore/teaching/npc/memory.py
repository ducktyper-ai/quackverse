# src/quackcore/teaching/npc/memory.py
"""
Memory management for the Quackster teaching NPC.

This module provides functions for loading user information into a
format that the NPC can use to personalize interactions.
"""

from datetime import datetime

from quackcore.logging import get_logger
from quackcore.teaching import badges, quests
from quackcore.teaching.models import UserProgress
from quackcore.teaching.npc.schema import UserMemory
from quackcore.teaching.utils import load_progress

logger = get_logger(__name__)


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

    # Get badge and quest data
    user_badges = badges.get_user_badges(user)
    badge_names = [badge.name for badge in user_badges]

    quest_data = quests.get_user_quests(user)
    completed_quests = [quest.name for quest in quest_data["completed"]]

    # Create memory object
    memory = UserMemory(
        github_username=user.github_username,
        xp=user.xp,
        level=user.get_level(),
        completed_quests=user.completed_quest_ids,
        badges=user.earned_badge_ids,
        # Other fields would be populated from persistent storage
        conversation_count=0,
        last_interaction=datetime.now().isoformat(),
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

    return memory


def update_user_memory(memory: UserMemory, user_input: str) -> UserMemory:
    """
    Update user memory based on the current interaction.

    Args:
        memory: Current user memory
        user_input: User's latest input

    Returns:
        Updated user memory
    """
    # Increment conversation count
    memory.conversation_count += 1

    # Update last interaction time
    memory.last_interaction = datetime.now().isoformat()

    # Track interests based on keywords in user input
    # This is a simple implementation - a real one would use NLP
    interest_keywords = {
        "python": "Python programming",
        "javascript": "JavaScript programming",
        "cli": "Command-line interfaces",
        "github": "GitHub",
        "quack": "QuackVerse ecosystem",
        "duck": "DuckTyper",
        "badge": "Achievements and badges",
        "quest": "Quests and challenges",
        "certificate": "Course certificates",
    }

    if memory.interests is None:
        memory.interests = []

    lower_input = user_input.lower()
    for keyword, interest in interest_keywords.items():
        if keyword in lower_input and interest not in memory.interests:
            memory.interests.append(interest)

    return memory


def format_memory_for_prompt(memory: UserMemory) -> str:
    """
    Format user memory into a string for inclusion in a prompt.

    Args:
        memory: User memory to format

    Returns:
        Formatted memory string
    """
    lines = []

    # Add basic user info
    github_username = memory.github_username or "Unknown User"
    lines.append(f"User: {github_username}")
    lines.append(f"XP: {memory.xp}")
    lines.append(f"Level: {memory.level}")

    # Add badges
    badge_names = memory.custom_data.get("badge_names", [])
    if badge_names:
        lines.append(f"Badges: {', '.join(badge_names)}")
    else:
        lines.append("Badges: None yet")

    # Add completed quests
    quest_names = memory.custom_data.get("completed_quest_names", [])
    if quest_names:
        lines.append(f"Completed Quests: {', '.join(quest_names)}")
    else:
        lines.append("Completed Quests: None yet")

    # Add suggested quests
    suggested = memory.custom_data.get("suggested_quests", [])
    if suggested:
        lines.append("\nSuggested Quests:")
        for quest in suggested:
            lines.append(
                f"- {quest['name']}: {quest['description']} ({quest['reward_xp']} XP)"
            )

    # Add level progression
    xp_to_next = memory.custom_data.get("xp_to_next_level", 100)
    next_level = memory.custom_data.get("next_level", memory.level + 1)
    lines.append(f"\nNeeds {xp_to_next} XP to reach Level {next_level}")

    # Add interests if available
    if memory.interests:
        lines.append(f"\nInterests: {', '.join(memory.interests)}")

    # Add conversation count
    lines.append(f"\nConversation Count: {memory.conversation_count}")

    return "\n".join(lines)


def get_conversation_history(
    user: UserProgress, limit: int = 5
) -> list[dict[str, str]]:
    """
    Get the conversation history for a user.

    This would normally load from persistent storage. This is a placeholder
    implementation that returns an empty history.

    Args:
        user: User to get conversation history for
        limit: Maximum number of messages to return

    Returns:
        list of conversation messages
    """
    # This would normally load from a database or file
    # For now, return an empty history
    return []
