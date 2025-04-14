# src/quackster/core/xp.py
"""
XP management module for QuackCore quackster.

This module provides functions for adding XP to users
and handling level-up events.
"""

from quackcore.errors import QuackError
from quackcore.logging import get_logger

from . import badges  # Use relative import from the same package
from .models import UserProgress, XPEvent

logger = get_logger(__name__)


def add_xp(user: UserProgress, event: XPEvent) -> tuple[bool, int]:
    """
    Add XP to a user from an XP event.

    Args:
        user: The user to add XP to.
        event: The XP event providing the points.

    Returns:
        Tuple of (is_new_event, level_before) indicating if this was a
        new event for the user and their level before adding XP.

    Raises:
        QuackError: If there is an error during XP badge checking.
    """
    is_new_event = not user.has_completed_event(event.id)

    if is_new_event:
        level_before = user.get_level()
        user.xp += event.points
        user.completed_event_ids.append(event.id)

        logger.info(f"Added {event.points} XP to user from event '{event.label}'")

        level_after = user.get_level()
        if level_after > level_before:
            logger.info(f"User leveled up from {level_before} to {level_after}!")
            _handle_level_up(user, level_before, level_after)

        # Award any new XP-based badges. Exceptions are caught and re-thrown as QuackError.
        try:
            check_xp_badges(user)
        except Exception as e:
            logger.error(f"Error during XP badge checking: {str(e)}")
            raise QuackError("Failed to check XP badges", original_error=e)

        return True, level_before

    logger.debug(f"User already completed event '{event.label}', no XP added")
    return False, user.get_level()


def add_xp_from_quest(user: UserProgress, quest_id: str, xp_amount: int) -> None:
    """
    Add XP to a user from completing a quest.

    Args:
        user: The user to add XP to.
        quest_id: ID of the completed quest.
        xp_amount: Amount of XP to award.
    """
    event = XPEvent(
        id=f"quest-{quest_id}",
        label=f"Completed Quest: {quest_id}",
        points=xp_amount,
    )
    add_xp(user, event)


def _handle_level_up(user: UserProgress, old_level: int, new_level: int) -> None:
    """
    Handle level-up events for a user.

    Args:
        user: The user who leveled up.
        old_level: The user's previous level.
        new_level: The user's new level.
    """
    for level in range(old_level + 1, new_level + 1):
        event = XPEvent(
            id=f"level-up-{level}",
            label=f"Reached Level {level}",
            points=0,  # No additional XP for leveling up
        )
        user.completed_event_ids.append(event.id)

    _check_level_badges(user, new_level)


def check_xp_badges(user: UserProgress) -> list[str]:
    """
    Check if the user has earned any XP-based badges.

    Args:
        user: The user to check badges for.

    Returns:
        List of newly earned badge IDs.

    Raises:
        QuackError: If an error occurs during badge checking.
    """
    try:
        all_badges = badges.get_all_badges()
        new_badges = []
        for badge in all_badges:
            # Skip if not XP-based or already earned.
            if badge.required_xp <= 0 or user.has_earned_badge(badge.id):
                continue
            if user.xp >= badge.required_xp:
                user.earned_badge_ids.append(badge.id)
                new_badges.append(badge.id)
                logger.info(f"User earned badge: {badge.name} ({badge.emoji})")
        return new_badges
    except Exception as e:
        logger.error(f"Error in check_xp_badges: {str(e)}")
        raise QuackError("Error checking XP badges", original_error=e)


def _check_level_badges(user: UserProgress, level: int) -> list[str]:
    """
    Check if the user has earned any level-based badges.

    Args:
        user: The user to check badges for.
        level: The user's current level.

    Returns:
        List of newly earned badge IDs.
    """
    level_badges = {5: "journeyman", 10: "expert", 20: "master", 50: "grandmaster"}
    new_badges = []

    if level in level_badges:
        badge_id = level_badges[level]
        if not user.has_earned_badge(badge_id):
            user.earned_badge_ids.append(badge_id)
            new_badges.append(badge_id)
            badge = badges.get_badge(badge_id)
            if badge:
                logger.info(f"User earned level badge: {badge.name} ({badge.emoji})")
    return new_badges


def calculate_total_possible_xp() -> int:
    """
    Calculate the total possible XP a user could earn.

    Returns:
        Total possible XP from all sources.
    """
    # Placeholder implementation.
    return 1000
