# src/quackster/npc/tools/badge_tools.py
"""
Tools for badge-related information and management.

This module provides functions for retrieving badge information,
listing earned badges, and checking badge progress.
"""

from quackcore.logging import get_logger
from quackster import badges, utils
from quackster.npc import rag
from quackster.npc.dialogue import DialogueRegistry
from quackster.npc.schema import UserMemory
from quackster.npc.tools.common import standardize_tool_output
from quackster.npc.tools.schema import BadgeDetailOutput, BadgeInfo, BadgeListOutput

logger = get_logger(__name__)


def list_badges(user_memory: UserMemory) -> BadgeListOutput:
    """
    Get information about a user's badges.

    Args:
        user_memory: User memory data containing badge information

    Returns:
        BadgeListOutput with badge information
    """
    # Use the user data from memory instead of loading it again
    user = utils.load_progress()  # Still needed for some badge _operations

    # Use badge IDs from user_memory
    badge_ids = user_memory.badges
    user_badges = [
        badges.get_badge(badge_id)
        for badge_id in badge_ids
        if badges.get_badge(badge_id)
    ]

    # Format badge list with emojis
    badge_list = [f"{badge.emoji} {badge.name}" for badge in user_badges]

    # Get next badges user could earn
    next_badges = badges.get_next_badges(user, limit=3)
    next_badge_list = []

    # Convert badges to BadgeInfo objects
    earned_badges = []
    for badge in user_badges:
        earned_badges.append(
            BadgeInfo(
                id=badge.id,
                name=badge.name,
                emoji=badge.emoji,
                description=badge.description,
                required_xp=badge.required_xp,
                is_earned=True,
                progress=100.0,
            )
        )

    for badge in next_badges:
        # Calculate progress - use user_memory.xp for XP-based badges
        if badge.required_xp > 0:
            progress = (
                (user_memory.xp / badge.required_xp * 100)
                if badge.required_xp > 0
                else 0
            )
        else:
            progress = badges.get_badge_progress(user, badge.id) * 100

        progress_str = f"({progress:.0f}% complete)"

        # Create BadgeInfo object
        badge_info = BadgeInfo(
            id=badge.id,
            name=badge.name,
            emoji=badge.emoji,
            description=badge.description,
            required_xp=badge.required_xp,
            is_earned=False,
            progress=progress,
        )

        next_badge_list.append(
            {
                "id": badge.id,
                "name": badge.name,
                "emoji": badge.emoji,
                "description": badge.description,
                "required_xp": badge.required_xp,
                "progress": progress,
                "formatted": f"{badge.emoji} {badge.name} - {badge.description} {progress_str}",
                "badge_info": badge_info,
            }
        )

    # Create badge summary with Quackster's enthusiasm
    badge_count = len(user_badges)

    # Use interests from user_memory to personalize the message
    interests = user_memory.interests or []
    badge_interest = (
        "badges" in " ".join(interests).lower()
        or "achievements" in " ".join(interests).lower()
    )

    if badge_count == 0:
        if badge_interest:
            intro = "You haven't earned any badges yet! I know you're interested in badges, so let's help you earn some!"
        else:
            intro = "You haven't earned any badges yet! Let's change that!"
    elif badge_count == 1:
        intro = f"You've earned your first badge! A great start to your collection!"
    else:
        if badge_interest:
            intro = f"You have earned {badge_count} badges - your collection is growing nicely! I know you enjoy collecting these!"
        else:
            intro = f"You have earned {badge_count} badges. Keep up the great work!"

    formatted_text = (
        f"{intro}\n\n"
        f"Earned Badges:\n" + "\n".join(badge_list or ["No badges earned yet"]) + "\n\n"
        f"Next Badges:\n"
        + "\n".join(
            [b["formatted"] for b in next_badge_list]
            if next_badge_list
            else ["Keep earning XP to unlock badges!"]
        )
    )

    # Extract badge info objects from next_badge_list
    next_badge_info = [item["badge_info"] for item in next_badge_list]

    return standardize_tool_output(
        "list_badges",
        {
            "earned_badges": earned_badges,
            "earned_count": badge_count,
            "earned_formatted": badge_list if badge_list else ["No badges earned yet"],
            "next_badges": next_badge_info,
            "next_badges_formatted": [b["formatted"] for b in next_badge_list]
            if next_badge_list
            else ["Keep earning XP to unlock badges!"],
            "formatted_text": formatted_text,
        },
        return_type=BadgeListOutput,
    )


def get_badge_details(badge_id: str) -> BadgeDetailOutput:
    """
    Get detailed information about a specific badge.

    Args:
        badge_id: ID of the badge to get details for

    Returns:
        BadgeDetailOutput with badge details
    """
    # Get custom badge dialogue
    badge_description = DialogueRegistry.get_badge_dialogue(badge_id, "description")
    badge_guidance = DialogueRegistry.get_badge_dialogue(badge_id, "guidance")
    badge_fun_fact = DialogueRegistry.get_badge_dialogue(badge_id, "fun_fact")
    badge_flavor = DialogueRegistry.get_badge_dialogue(badge_id, "flavor")

    # Fall back to RAG if custom dialogue not found
    info = rag.get_badge_info(badge_id)
    if not badge_description and info:
        badge_description = info.get("description", "Badge information not found")
    if not badge_guidance and info:
        badge_guidance = info.get("guidance", "No specific guidance available.")
    if not badge_fun_fact and info:
        badge_fun_fact = info.get("fun_fact", "")

    # Check if user has this badge
    user = utils.load_progress()
    is_earned = user.has_earned_badge(badge_id)

    badge = badges.get_badge(badge_id)
    if not badge:
        # Return a BadgeInfo with placeholder data for non-existent badges
        return standardize_tool_output(
            "get_badge_details",
            {
                "id": badge_id,
                "name": info.get("name", f"Unknown Badge ({badge_id})"),
                "emoji": "❓",
                "description": badge_description or "Badge information not found",
                "required_xp": 0,
                "is_earned": is_earned,
                "progress": 0.0,
                "progress_bar": "",
                "guidance": "Badge not found in system.",
                "fun_fact": "",
                "flavor": "",
                "formatted_text": f"Badge '{info.get('name', badge_id)}' not found.",
            },
            return_type=BadgeDetailOutput,
        )

    # Get progress toward earning this badge
    progress = badges.get_badge_progress(user, badge_id) * 100
    progress_bar = "█" * (int(progress) // 5) + "░" * ((100 - int(progress)) // 5)

    # Prepare badge data for template
    badge_data = {
        "id": badge.id,
        "name": badge.name,
        "emoji": badge.emoji,
        "description": badge_description or badge.description,
        "required_xp": badge.required_xp,
        "is_earned": is_earned,
        "progress": progress,
        "progress_bar": progress_bar,
        "guidance": badge_guidance
        or "Complete related quests or earn XP to unlock this badge.",
        "fun_fact": badge_fun_fact or "",
        "flavor": badge_flavor or "",
    }

    # Use template to generate formatted text
    try:
        formatted_text = DialogueRegistry.render_badge_status(badge_data)
    except Exception as e:
        logger.error(f"Error rendering badge template: {e}")
        # Fallback formatted text
        formatted_text = (
            f"{badge.emoji} {badge.name}\n\n"
            f"Description: {badge_description or badge.description}\n"
            f"Status: {'Earned' if is_earned else 'Not yet earned'}\n"
            f"{f'Required XP: {badge.required_xp}' if badge.required_xp > 0 else ''}\n"
            f"{f'Progress: {progress:.0f}%\n{progress_bar}' if not is_earned and badge.required_xp > 0 else ''}\n\n"
            f"How to earn: {badge_guidance or 'No specific guidance available.'}\n\n"
            f"Fun fact: {badge_fun_fact or ''}"
        )

    badge_data["formatted_text"] = formatted_text
    return standardize_tool_output(
        "get_badge_details", badge_data, return_type=BadgeDetailOutput
    )
