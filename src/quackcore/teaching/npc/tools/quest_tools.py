# src/quackcore/teaching/npc/tools/quest_tools.py
"""
Tools for quest-related information and management.

This module provides functions for retrieving quest information,
listing available quests, suggesting next quests, and verifying quest completion.
"""

from typing import Any

from quackcore.logging import get_logger
from quackcore.teaching import badges, quests, utils
from quackcore.teaching.npc import rag
from quackcore.teaching.npc.dialogue import DialogueRegistry
from quackcore.teaching.npc.schema import UserMemory
from quackcore.teaching.npc.tools.common import standardize_tool_output

logger = get_logger(__name__)


def list_quests(user_memory: UserMemory) -> dict[str, Any]:
    """
    Get information about a user's quests.

    Args:
        user_memory: User memory data containing quest completion info

    Returns:
        Dictionary with quest information
    """
    # Load full quest data
    user = utils.load_progress()  # Still needed for some operations
    quest_data = quests.get_user_quests(user)

    # Use completed_quests from user_memory to identify completed quests
    completed_quest_ids = user_memory.completed_quests
    completed = [q for q in quest_data["completed"] if q.id in completed_quest_ids]
    available = quest_data["available"]

    # Format completion status
    completed_list = [f"✅ {quest.name} (+{quest.reward_xp} XP)" for quest in completed]

    # Sort available quests by XP reward (highest first)
    available.sort(key=lambda q: q.reward_xp, reverse=True)
    available_list = [
        f"⏳ {quest.name} (+{quest.reward_xp} XP) - {quest.description}"
        for quest in available[:5]
    ]

    # Get suggested quests - try from user_memory first
    suggested_quests = user_memory.custom_data.get("suggested_quests", [])
    if suggested_quests:
        # Convert dict objects from memory to Quest objects
        suggested = []
        for sq in suggested_quests:
            quest = quests.get_quest(sq["id"])
            if quest:
                suggested.append(quest)

        # If no quests found from memory, use the regular method
        if not suggested:
            suggested = quests.get_suggested_quests(user, limit=3)
    else:
        suggested = quests.get_suggested_quests(user, limit=3)

    suggested_list = []

    for quest in suggested:
        badge_text = (
            f" (Earns {badges.get_badge(quest.badge_id).emoji} badge)"
            if quest.badge_id and badges.get_badge(quest.badge_id)
            else ""
        )
        suggested_list.append(
            {
                "id": quest.id,
                "name": quest.name,
                "description": quest.description,
                "reward_xp": quest.reward_xp,
                "badge_id": quest.badge_id,
                "formatted": f"⭐ {quest.name} (+{quest.reward_xp} XP){badge_text} - {quest.description}",
            }
        )

    # Create quest summary with Quackster flavor
    completed_count = len(completed)
    available_count = len(available)

    # Use recently discussed quests for personalization
    recent_quests = user_memory.custom_data.get("recent_quests_discussed", [])
    learning_style = user_memory.custom_data.get("learning_style", "")

    if completed_count == 0:
        if "challenge" in learning_style:
            intro = "Ready for a challenge? Here are some quests to test your skills:"
        else:
            intro = "Time to start your quest journey! Here are some quests to get you started:"
    elif completed_count < 3:
        if recent_quests:
            mentioned_quest = recent_quests[0]
            intro = f"You've completed {completed_count} quests so far. I see you were asking about '{mentioned_quest}' - that's a great one to try next!"
        else:
            intro = f"You've completed {completed_count} quests so far. Great start! Here are some more adventures:"
    else:
        if user_memory.xp > 500:
            intro = f"Impressive work! You've completed {completed_count} quests and reached level {user_memory.level}. You're becoming a QuackVerse expert!"
        else:
            intro = f"Impressive! You've completed {completed_count} quests and have {available_count} more to explore."

    formatted_text = (
            f"{intro}\n\n"
            f"Completed Quests:\n"
            + "\n".join(completed_list or ["No quests completed yet"])
            + "\n\n"
              f"Suggested Quests:\n"
            + "\n".join(
        [q["formatted"] for q in suggested_list]
        if suggested_list
        else ["No suggested quests available."]
    )
    )

    return standardize_tool_output(
        "list_quests",
        {
            "completed": completed,
            "completed_count": completed_count,
            "completed_formatted": completed_list
            if completed_list
            else ["No quests completed yet"],
            "available": available,
            "available_count": available_count,
            "available_formatted": available_list
            if available_list
            else ["No more quests available!"],
            "suggested": suggested,
            "suggested_formatted": [q["formatted"] for q in suggested_list]
            if suggested_list
            else ["No suggested quests available."],
            "formatted_text": formatted_text,
        }
    )


def get_quest_details(quest_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific quest.

    Args:
        quest_id: ID of the quest to get details for

    Returns:
        Dictionary with quest details
    """
    # Get custom quest dialogue
    quest_guidance = DialogueRegistry.get_quest_dialogue(quest_id, "guidance")
    quest_hint = DialogueRegistry.get_quest_dialogue(quest_id, "hint")

    # Default to RAG if no custom dialogue found
    info = rag.get_quest_info(quest_id)
    if not quest_guidance and info:
        quest_guidance = info.get("guidance",
                                  "No specific guidance available for this quest.")

    # Check if user has completed this quest
    user = utils.load_progress()
    is_completed = user.has_completed_quest(quest_id)

    quest = quests.get_quest(quest_id)
    if not quest:
        return standardize_tool_output(
            "get_quest_details",
            {
                "id": quest_id,
                "name": info.get("name", f"Unknown Quest ({quest_id})"),
                "description": info.get("description", "Quest information not found"),
                "is_completed": is_completed,
                "formatted_text": f"Quest '{info.get('name', quest_id)}' not found.",
            }
        )

    # If quest has a badge, get badge info
    badge_info = None
    if quest.badge_id:
        badge = badges.get_badge(quest.badge_id)
        if badge:
            badge_info = f"{badge.emoji} {badge.name} badge"

    # Prepare quest data for template
    quest_data = {
        "id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge": badge_info,
        "is_completed": is_completed,
        "guidance": quest_guidance,
        "hint": quest_hint,
    }

    # Use template to generate formatted text
    try:
        formatted_text = DialogueRegistry.render_quest_intro(quest_data)
    except Exception as e:
        logger.error(f"Error rendering quest template: {e}")
        # Fallback formatted text
        formatted_text = (
            f"{'✅' if is_completed else '⏳'} {quest.name}\n\n"
            f"Description: {quest.description}\n"
            f"Reward: {quest.reward_xp} XP"
            f"{f' + {badge_info}' if badge_info else ''}\n"
            f"Status: {'Completed' if is_completed else 'Not completed'}\n\n"
            f"Guidance:\n{quest_guidance}"
        )

    quest_data["formatted_text"] = formatted_text
    return standardize_tool_output("get_quest_details", quest_data)


def suggest_next_quest(user_memory: UserMemory) -> dict[str, Any]:
    """
    Suggest the next quest for a user to complete.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with quest suggestion
    """
    # Get suggested quests
    suggested = user_memory.custom_data.get("suggested_quests", [])

    if not suggested:
        # If no suggestions in memory, get them from quests module
        user = utils.load_progress()
        quest_objects = quests.get_suggested_quests(user, limit=1)
        if not quest_objects:
            return standardize_tool_output(
                "suggest_next_quest",
                {
                    "has_suggestion": False,
                    "formatted_text": "No quest suggestions available at this time.",
                }
            )

        # Use the first suggested quest
        quest = quest_objects[0]
        quest_info = rag.get_quest_info(quest.id)
    else:
        # Use the first suggestion from memory
        quest_info = suggested[0]
        quest = quests.get_quest(quest_info["id"])
        if not quest:
            return standardize_tool_output(
                "suggest_next_quest",
                {
                    "has_suggestion": False,
                    "formatted_text": "No quest suggestions available at this time.",
                }
            )

    # Get custom quest guidance or use RAG
    quest_guidance = DialogueRegistry.get_quest_dialogue(quest.id, "guidance")
    if not quest_guidance:
        quest_guidance = quest_info.get("guidance", "No specific guidance available.")

    # If quest has a badge, get badge info
    badge_info = None
    if quest.badge_id:
        badge = badges.get_badge(quest.badge_id)
        if badge:
            badge_info = f"{badge.emoji} {badge.name} badge"

    # Prepare quest data for template
    quest_data = {
        "id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge": badge_info,
        "guidance": quest_guidance,
        "hint": DialogueRegistry.get_quest_dialogue(quest.id, "hint"),
    }

    # Use template to generate formatted text
    try:
        formatted_text = DialogueRegistry.render_quest_intro(quest_data)
    except Exception as e:
        logger.error(f"Error rendering quest template: {e}")
        # Fallback formatted text
        formatted_text = (
            f"I suggest you try the '{quest.name}' quest!\n\n"
            f"Description: {quest.description}\n"
            f"Reward: {quest.reward_xp} XP"
            f"{f' + {badge_info}' if badge_info else ''}\n\n"
            f"Guidance:\n{quest_guidance}"
        )

    return standardize_tool_output(
        "suggest_next_quest",
        {
            "has_suggestion": True,
            "quest": quest,
            "quest_id": quest.id,
            "name": quest.name,
            "description": quest.description,
            "reward_xp": quest.reward_xp,
            "badge": badge_info,
            "guidance": quest_guidance,
            "formatted_text": formatted_text,
        }
    )


def verify_quest_completion(user_memory: UserMemory) -> dict[str, Any]:
    """
    Check for newly completed quests.

    Args:
        user_memory: User memory data with current quest status

    Returns:
        Dictionary with quest verification results
    """
    # Load progress and check for completed quests
    user = utils.load_progress()

    # Use the completed_quests from user_memory to check for new completions
    already_completed = set(user_memory.completed_quests)
    newly_completed = quests.check_quest_completion(user)

    # Filter out quests that were already in user_memory as completed
    newly_completed = [quest for quest in newly_completed if
                       quest.id not in already_completed]

    if not newly_completed:
        # Check session history to personalize the message
        session_history = user_memory.custom_data.get("session_history", [])
        completion_attempts = sum(1 for session in session_history if
                                  "complete" in session.get("content_snippet",
                                                            "").lower())

        message = "No newly completed quests found."
        if completion_attempts > 2:
            message = "I don't see any newly completed quests. Are you having trouble with a particular quest? I'd be happy to help!"

        return standardize_tool_output(
            "verify_quest_completion",
            {
                "quests_completed": False,
                "completed_quests": [],
                "formatted_text": message,
            }
        )

    # Apply completions and get quest details
    completed_details = []
    for quest in newly_completed:
        quests.complete_quest(user, quest.id)

        # Get badge info if one is awarded
        badge_info = None
        if quest.badge_id:
            badge = badges.get_badge(quest.badge_id)
            if badge:
                badge_info = f"{badge.emoji} {badge.name}"

        # Get custom completion message
        completion_msg = DialogueRegistry.get_quest_dialogue(quest.id, "completion")
        if not completion_msg:
            completion_msg = f"You've completed the {quest.name} quest!"

        completed_details.append(
            {
                "id": quest.id,
                "name": quest.name,
                "reward_xp": quest.reward_xp,
                "badge": badge_info,
                "completion_message": completion_msg,
                "formatted": f"✅ {quest.name} (+{quest.reward_xp} XP)"
                             + (f" → Earned {badge_info}!" if badge_info else ""),
            }
        )

    # Save the updated progress
    utils.save_progress(user)

    # Create an enthusiastic completion message
    quest_count = len(newly_completed)

    # Use user_memory to personalize celebration based on level and completed quests
    total_completed = len(user_memory.completed_quests) + quest_count

    if user_memory.level >= 5:
        header = "🎉 QUEST MASTERY ACHIEVED! 🎉"
    elif quest_count == 1:
        header = "🎉 QUEST COMPLETED! 🎉"
    else:
        header = f"🎉 {quest_count} QUESTS COMPLETED! 🎉"

    # Add personalized milestone recognition
    milestone_text = ""
    if total_completed == 5:
        milestone_text = "\n\n🌟 Milestone: You've completed 5 quests! You're becoming a true QuackVerse adventurer! 🌟"
    elif total_completed == 10:
        milestone_text = "\n\n🌟 Milestone: 10 quests completed! You're now a QuackVerse Quest Champion! 🌟"

    details_text = "\n\n".join([
        f"{details['formatted']}\n{details['completion_message']}"
        for details in completed_details
    ])

    formatted_text = f"{header}\n\n{details_text}{milestone_text}"

    return standardize_tool_output(
        "verify_quest_completion",
        {
            "quests_completed": True,
            "completed_quests": newly_completed,
            "completed_details": completed_details,
            "total_completed_count": total_completed,
            "formatted_text": formatted_text,
        }
    )