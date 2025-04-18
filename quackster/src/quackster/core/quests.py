# quackster/src/quackster/core/quests.py
"""
Quest definitions and management for QuackCore quackster.

This module provides access to all available quests and functions
for managing user quest progress.
"""

from quackcore.logging import get_logger
from quackster.core import badges, github_api, xp
from quackster.core.models import Quest, UserProgress

logger = get_logger(__name__)


# Quest verification functions
def _verify_star_quackcore(user: UserProgress) -> bool:
    """Verify if the user has starred the QuackCore repository."""
    if not user.github_username:
        return False
    return github_api.has_starred_repo(user.github_username, "quackverse/quackcore")


def _verify_star_quackverse(user: UserProgress) -> bool:
    """Verify if the user has starred the QuackVerse organization."""
    if not user.github_username:
        return False
    return github_api.has_starred_repo(user.github_username, "quackverse/quackverse")


def _verify_first_pr(user: UserProgress) -> bool:
    """Verify if the user has opened a PR to any QuackVerse repository."""
    if not user.github_username:
        return False
    return github_api.has_opened_pr(user.github_username, "quackverse")


def _verify_merged_pr(user: UserProgress) -> bool:
    """Verify if the user has a merged PR in any QuackVerse repository."""
    if not user.github_username:
        return False
    return github_api.has_merged_pr(user.github_username, "quackverse")


def _verify_run_ducktyper(user: UserProgress) -> bool:
    """Verify if the user has run DuckTyper at least once."""
    return user.has_completed_event("run-tests")


def _verify_daily_streak(user: UserProgress) -> bool:
    """Verify if the user has a daily streak of using DuckTyper."""
    # This would normally check dates of usage events
    # For now, just check if they've run it at least 3 times
    return (
        len([e for e in user.completed_event_ids if e.startswith("run-tests-day-")])
        >= 3
    )


# Define all available quests
_QUESTS: dict[str, Quest] = {
    # GitHub quests
    "star-quackcore": Quest(
        id="star-quackcore",
        name="Star QuackCore",
        description="Star the QuackCore repository on GitHub",
        reward_xp=50,
        badge_id="github-collaborator",
        github_check={"repo": "quackverse/quackcore", "action": "star"},
    ),
    "star-quackverse": Quest(
        id="star-quackverse",
        name="Star QuackVerse",
        description="Star the QuackVerse organization on GitHub",
        reward_xp=50,
        github_check={"repo": "quackverse/quackverse", "action": "star"},
    ),
    "open-pr": Quest(
        id="open-pr",
        name="Open a PR",
        description="Open your first Pull Request to a QuackVerse repository",
        reward_xp=100,
        badge_id="duck-contributor",
        github_check={"org": "quackverse", "action": "open_pr"},
    ),
    "merged-pr": Quest(
        id="merged-pr",
        name="Merged PR",
        description="Get a Pull Request merged into a QuackVerse repository",
        reward_xp=200,
        badge_id="duck-team-player",
        github_check={"org": "quackverse", "action": "merged_pr"},
    ),
    # Tool usage quests
    "run-tests": Quest(
        id="run-tests",
        name="Run DuckTyper",
        description="Run the DuckTyper CLI for the first time",
        reward_xp=10,
        github_check=None,
    ),
    "daily-streak": Quest(
        id="daily-streak",
        name="Daily Streak",
        description="Use DuckTyper for 3 days in a row",
        reward_xp=30,
        github_check=None,
    ),
    # Tutorial quests
    "complete-tutorial": Quest(
        id="complete-tutorial",
        name="Complete Tutorial",
        description="Complete the DuckTyper tutorial",
        reward_xp=75,
        badge_id="duck-explorer",
        github_check=None,
    ),
}

# Add verification functions to quests
_QUESTS["star-quackcore"].verify_func = _verify_star_quackcore
_QUESTS["star-quackverse"].verify_func = _verify_star_quackverse
_QUESTS["open-pr"].verify_func = _verify_first_pr
_QUESTS["merged-pr"].verify_func = _verify_merged_pr
_QUESTS["run-tests"].verify_func = _verify_run_ducktyper
_QUESTS["daily-streak"].verify_func = _verify_daily_streak


# Tutorial quest validation would usually be more complex


def get_all_quests() -> list[Quest]:
    """
    Get all available quests.

    Returns:
        list of all quest definitions
    """
    return list(_QUESTS.values())


def get_quest(quest_id: str) -> Quest | None:
    """
    Get a specific quest by ID.

    Args:
        quest_id: ID of the quest to retrieve

    Returns:
        Quest if found, None otherwise
    """
    return _QUESTS.get(quest_id)


def get_user_quests(user: UserProgress) -> dict[str, list[Quest]]:
    """
    Get all quests for a user, categorized by completion status.

    Args:
        user: User to get quests for

    Returns:
        Dictionary with 'completed' and 'available' quests
    """
    completed = []
    available = []

    for quest in _QUESTS.values():
        if user.has_completed_quest(quest.id):
            completed.append(quest)
        else:
            available.append(quest)

    return {"completed": completed, "available": available}


def check_quest_completion(user: UserProgress) -> list[Quest]:
    """
    Check which quests a user has newly completed.

    Args:
        user: User to check quest completion for

    Returns:
        list of newly completed quests
    """
    newly_completed = []

    for quest in _QUESTS.values():
        # Skip quests that are already completed
        if user.has_completed_quest(quest.id):
            continue

        # Skip quests without verification function
        if quest.verify_func is None:
            continue

        # Check if the quest is now completed
        try:
            if quest.verify_func(user):
                newly_completed.append(quest)
        except Exception as e:
            logger.error(f"Error verifying quest {quest.id}: {str(e)}")

    return newly_completed


def complete_quest(user: UserProgress, quest_id: str, forced: bool = False) -> bool:
    """
    Mark a quest as completed for a user and award XP and badges.

    Args:
        user: User to complete quest for
        quest_id: ID of the quest to complete
        forced: If True, mark as completed without verification

    Returns:
        True if quest was newly completed, False otherwise
    """
    # Check if quest exists
    quest = _QUESTS.get(quest_id)
    if not quest:
        logger.warning(f"Attempted to complete non-existent quest: {quest_id}")
        return False

    # Check if already completed
    if user.has_completed_quest(quest_id):
        logger.debug(f"User already completed quest: {quest_id}")
        return False

    # Verify quest completion if not forced
    if not forced and quest.verify_func:
        try:
            if not quest.verify_func(user):
                logger.debug(f"Quest verification failed for: {quest_id}")
                return False
        except Exception as e:
            logger.error(f"Error verifying quest {quest_id}: {str(e)}")
            return False

    # Mark quest as completed
    user.completed_quest_ids.append(quest_id)
    logger.info(f"User completed quest: {quest.name}")

    # Award XP for quest
    if quest.reward_xp > 0:
        xp.add_xp_from_quest(user, quest_id, quest.reward_xp)
        logger.info(f"Awarded {quest.reward_xp} XP for quest: {quest.name}")

    # Award badge if applicable
    if quest.badge_id:
        badges.award_badge(user, quest.badge_id)

    return True


def apply_completed_quests(user: UserProgress) -> list[Quest]:
    """
    Check for newly completed quests and update user progress.

    Args:
        user: User to update

    Returns:
        list of newly completed quests
    """
    newly_completed = check_quest_completion(user)

    for quest in newly_completed:
        complete_quest(user, quest.id)

    return newly_completed


def get_suggested_quests(user: UserProgress, limit: int = 3) -> list[Quest]:
    """
    Get suggested quests for a user to complete next.

    Args:
        user: User to get suggestions for
        limit: Maximum number of suggestions to return

    Returns:
        list of suggested quests
    """
    # Get quests that aren't completed yet
    available_quests = [
        quest for quest in _QUESTS.values() if not user.has_completed_quest(quest.id)
    ]

    # Sort by XP reward (highest first)
    available_quests.sort(key=lambda quest: quest.reward_xp, reverse=True)

    # Return top suggestions up to limit
    return available_quests[:limit]
