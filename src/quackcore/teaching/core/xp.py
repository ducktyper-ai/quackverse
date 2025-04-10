# src/quackcore/teaching/core/xp.py
"""
XP management module for QuackCore teaching.

This module provides functions for adding XP to users
and handling level-up events.
"""

from quackcore.logging import get_logger
from quackcore.teaching import badges
from quackcore.teaching.core.models import UserProgress, XPEvent

logger = get_logger(__name__)


def add_xp(user: UserProgress, event: XPEvent) -> tuple[bool, int]:
    """
    Add XP to a user from an XP event.

    Args:
        user: The user to add XP to
        event: The XP event providing the points

    Returns:
        Tuple of (is_new_event, level_before) indicating if this was a
        new event for the user and their level before adding XP
    """
    # Check if the user has already completed this event
    is_new_event = not user.has_completed_event(event.id)

    # Only add XP if this is a new event
    if is_new_event:
        level_before = user.get_level()

        # Add the XP and record the event
        user.xp += event.points
        user.completed_event_ids.append(event.id)

        # Log the XP gain
        logger.info(f"Added {event.points} XP to user from event '{event.label}'")

        # Check for level up
        level_after = user.get_level()
        if level_after > level_before:
            logger.info(f"User leveled up from {level_before} to {level_after}!")
            _handle_level_up(user, level_before, level_after)

        # Check for badges based on new XP total
        _check_xp_badges(user)

        return True, level_before

    # Event was already completed
    logger.debug(f"User already completed event '{event.label}', no XP added")
    return False, user.get_level()


def add_xp_from_quest(user: UserProgress, quest_id: str, xp_amount: int) -> None:
    """
    Add XP to a user from completing a quest.

    Args:
        user: The user to add XP to
        quest_id: ID of the completed quest
        xp_amount: Amount of XP to award
    """
    # Create a synthetic XP event for this quest completion
    event = XPEvent(
        id=f"quest-{quest_id}", label=f"Completed Quest: {quest_id}", points=xp_amount
    )

    # Add the XP using the standard function
    add_xp(user, event)


def _handle_level_up(user: UserProgress, old_level: int, new_level: int) -> None:
    """
    Handle level-up events for a user.

    This is called internally when a user gains enough XP to level up.
    It may trigger special rewards or notifications.

    Args:
        user: The user who leveled up
        old_level: The user's previous level
        new_level: The user's new level
    """
    # Add a level-up XP event as a record
    for level in range(old_level + 1, new_level + 1):
        event = XPEvent(
            id=f"level-up-{level}",
            label=f"Reached Level {level}",
            points=0,  # No additional XP for leveling up
        )
        user.completed_event_ids.append(event.id)

    # Check for level badges
    _check_level_badges(user, new_level)


def _check_xp_badges(user: UserProgress) -> list[str]:
    """
    Check if the user has earned any XP-based badges.

    Args:
        user: The user to check badges for

    Returns:
        List of newly earned badge IDs
    """
    all_badges = badges.get_all_badges()
    new_badges = []

    for badge in all_badges:
        # Skip badges that aren't XP-based or already earned
        if badge.required_xp <= 0 or user.has_earned_badge(badge.id):
            continue

        # Award badge if user has enough XP
        if user.xp >= badge.required_xp:
            user.earned_badge_ids.append(badge.id)
            new_badges.append(badge.id)
            logger.info(f"User earned badge: {badge.name} ({badge.emoji})")

    return new_badges


def _check_level_badges(user: UserProgress, level: int) -> list[str]:
    """
    Check if the user has earned any level-based badges.

    Args:
        user: The user to check badges for
        level: The user's current level

    Returns:
        List of newly earned badge IDs
    """
    # Map levels to badge IDs (these would normally come from badges.py)
    level_badges = {5: "journeyman", 10: "expert", 20: "master", 50: "grandmaster"}

    new_badges = []

    # Check if there's a badge for this level
    if level in level_badges:
        badge_id = level_badges[level]

        # Award the badge if not already earned
        if not user.has_earned_badge(badge_id):
            user.earned_badge_ids.append(badge_id)
            new_badges.append(badge_id)

            # Get the badge details for logging
            badge = badges.get_badge(badge_id)
            if badge:
                logger.info(f"User earned level badge: {badge.name} ({badge.emoji})")

    return new_badges


def calculate_total_possible_xp() -> int:
    """
    Calculate the total possible XP a user could earn.

    This is used for displaying progress metrics.

    Returns:
        Total possible XP from all sources
    """
    # This is a placeholder implementation
    # In a real implementation, we would sum up all possible XP events and quests
    return 1000
