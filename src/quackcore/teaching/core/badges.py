# src/quackcore/teaching/core/badges.py
"""
Badge definitions and management for QuackCore teaching.

This module provides access to all available badges and functions
for managing user badges.
"""

from quackcore.logging import get_logger

from .models import Badge, UserProgress

logger = get_logger(__name__)

# Define all available badges
_BADGES: dict[str, Badge] = {
    # XP-based badges
    "duck-initiate": Badge(
        id="duck-initiate",
        name="Duck Initiate",
        description="Earned your first 10 XP in DuckTyper",
        required_xp=10,
        emoji="🥚",
    ),
    "duck-novice": Badge(
        id="duck-novice",
        name="Duck Novice",
        description="Reached 100 XP in DuckTyper",
        required_xp=100,
        emoji="🐣",
    ),
    "duck-apprentice": Badge(
        id="duck-apprentice",
        name="Duck Apprentice",
        description="Reached 500 XP in DuckTyper",
        required_xp=500,
        emoji="🐥",
    ),
    "duck-journeyman": Badge(
        id="duck-journeyman",
        name="Duck Journeyman",
        description="Reached 1,000 XP in DuckTyper",
        required_xp=1000,
        emoji="🦆",
    ),
    "duck-expert": Badge(
        id="duck-expert",
        name="Duck Expert",
        description="Reached 2,500 XP in DuckTyper",
        required_xp=2500,
        emoji="✨🦆",
    ),
    "duck-master": Badge(
        id="duck-master",
        name="Duck Master",
        description="Reached 5,000 XP in DuckTyper",
        required_xp=5000,
        emoji="🌟🦆",
    ),
    # Quest-based badges
    "github-collaborator": Badge(
        id="github-collaborator",
        name="GitHub Collaborator",
        description="Starred the QuackCore repository",
        required_xp=0,  # Not XP-based
        emoji="⭐",
    ),
    "duck-contributor": Badge(
        id="duck-contributor",
        name="Duck Contributor",
        description="Made your first contribution to a QuackVerse project",
        required_xp=0,  # Not XP-based
        emoji="📝🦆",
    ),
    "duck-team-player": Badge(
        id="duck-team-player",
        name="Duck Team Player",
        description="Had a PR merged into a QuackVerse project",
        required_xp=0,  # Not XP-based
        emoji="🤝🦆",
    ),
    # Special badges
    "quackster-friend": Badge(
        id="quackster-friend",
        name="Quackster's Friend",
        description="Had 10 conversations with Quackster",
        required_xp=0,  # Not XP-based
        emoji="💬🦆",
    ),
    "duck-explorer": Badge(
        id="duck-explorer",
        name="Duck Explorer",
        description="Completed all tutorial quests",
        required_xp=0,  # Not XP-based
        emoji="🧭🦆",
    ),
    "duck-graduate": Badge(
        id="duck-graduate",
        name="Duck Graduate",
        description="Earned a course certificate",
        required_xp=0,  # Not XP-based
        emoji="🎓🦆",
    ),
}


def get_all_badges() -> list[Badge]:
    """
    Get all available badges.

    Returns:
        list of all badge definitions
    """
    return list(_BADGES.values())


def get_badge(badge_id: str) -> Badge | None:
    """
    Get a specific badge by ID.

    Args:
        badge_id: ID of the badge to retrieve

    Returns:
        Badge if found, None otherwise
    """
    return _BADGES.get(badge_id)


def get_user_badges(user: UserProgress) -> list[Badge]:
    """
    Get all badges earned by a user.

    Args:
        user: User to get badges for

    Returns:
        list of badges earned by the user
    """
    return [
        _BADGES[badge_id] for badge_id in user.earned_badge_ids if badge_id in _BADGES
    ]


def award_badge(user: UserProgress, badge_id: str) -> bool:
    """
    Award a badge to a user if they don't already have it.

    Args:
        user: User to award the badge to
        badge_id: ID of the badge to award

    Returns:
        True if the badge was newly awarded, False otherwise
    """
    # Check if the badge exists
    if badge_id not in _BADGES:
        logger.warning(f"Attempted to award non-existent badge: {badge_id}")
        return False

    # Check if the user already has this badge
    if user.has_earned_badge(badge_id):
        logger.debug(f"User already has badge: {badge_id}")
        return False

    # Award the badge
    user.earned_badge_ids.append(badge_id)
    badge = _BADGES[badge_id]
    logger.info(f"Awarded badge to user: {badge.name} ({badge.emoji})")
    return True


def get_next_badges(user: UserProgress, limit: int = 3) -> list[Badge]:
    """
    Get the next badges a user could earn.

    This prioritizes badges that are closest to the user's current XP.

    Args:
        user: User to get next badges for
        limit: Maximum number of badges to return

    Returns:
        list of badges the user could earn next
    """
    # Get all badges the user hasn't earned yet
    unearned_badges = [
        badge for badge in _BADGES.values() if badge.id not in user.earned_badge_ids
    ]

    # Filter out non-XP badges (they would be earned through quests)
    xp_badges = [badge for badge in unearned_badges if badge.required_xp > 0]

    # Sort by XP required (ascending)
    xp_badges.sort(key=lambda badge: badge.required_xp)

    # Return the next badges the user could earn (up to the limit)
    return [badge for badge in xp_badges if badge.required_xp > user.xp][:limit]


def get_badge_progress(user: UserProgress, badge_id: str) -> float:
    """
    Calculate a user's progress toward a specific badge.

    Args:
        user: User to calculate progress for
        badge_id: ID of the badge to check

    Returns:
        Progress as a value between 0.0 and 1.0
    """
    # Check if the badge exists
    badge = _BADGES.get(badge_id)
    if not badge:
        return 0.0

    # If the user already has the badge, progress is 100%
    if user.has_earned_badge(badge_id):
        return 1.0

    # For XP-based badges, calculate progress based on required XP
    if badge.required_xp > 0:
        progress = min(1.0, user.xp / badge.required_xp)
        return progress

    # For non-XP badges, we can't calculate progress
    return 0.0
