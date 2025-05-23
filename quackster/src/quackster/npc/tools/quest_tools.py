# quackster/src/quackster/npc/tools/quest_tools.py
"""
Tools for quest-related information and management.

This module provides functions for retrieving quest information,
listing available quests, suggesting next quests, and verifying quest completion.
"""

from quackcore.logging import get_logger
from quackster import badges, quests, utils
from quackster.npc import rag
from quackster.npc.dialogue import DialogueRegistry
from quackster.npc.schema import UserMemory
from quackster.npc.tools.common import standardize_tool_output
from quackster.npc.tools.schema import (
    QuestCompletionDetail,
    QuestCompletionOutput,
    QuestDetailOutput,
    QuestInfo,
    QuestListOutput,
)

logger = get_logger(__name__)


def list_quests(user_memory: UserMemory) -> QuestListOutput:
    """
    Get information about a user's quests.

    Args:
        user_memory: User memory data containing quest completion info

    Returns:
        QuestListOutput with quest information
    """
    # Load full quest data
    user = utils.load_progress()  # Still needed for some _operations
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
        "Suggested Quests:\n"
        + "\n".join(
            [q["formatted"] for q in suggested_list]
            if suggested_list
            else ["No suggested quests available."]
        )
    )

    # Convert quests to QuestInfo objects for the Pydantic model
    quest_info_completed = [
        QuestInfo(
            id=quest.id,
            name=quest.name,
            description=quest.description,
            reward_xp=quest.reward_xp,
            badge_id=quest.badge_id,
            is_completed=True,
        )
        for quest in completed
    ]

    quest_info_available = [
        QuestInfo(
            id=quest.id,
            name=quest.name,
            description=quest.description,
            reward_xp=quest.reward_xp,
            badge_id=quest.badge_id,
            is_completed=False,
        )
        for quest in available
    ]

    quest_info_suggested = [
        QuestInfo(
            id=quest.id,
            name=quest.name,
            description=quest.description,
            reward_xp=quest.reward_xp,
            badge_id=quest.badge_id,
            is_completed=False,
        )
        for quest in suggested
    ]

    return standardize_tool_output(
        "list_quests",
        {
            "completed": quest_info_completed,
            "completed_count": completed_count,
            "completed_formatted": completed_list
            if completed_list
            else ["No quests completed yet"],
            "available": quest_info_available,
            "available_count": available_count,
            "available_formatted": available_list
            if available_list
            else ["No more quests available!"],
            "suggested": quest_info_suggested,
            "suggested_formatted": [q["formatted"] for q in suggested_list]
            if suggested_list
            else ["No suggested quests available."],
            "formatted_text": formatted_text,
        },
        return_type=QuestListOutput,
    )


def get_quest_details(quest_id: str) -> QuestDetailOutput:
    """
    Get detailed information about a specific quest.

    Args:
        quest_id: ID of the quest to get details for

    Returns:
        QuestDetailOutput with quest details
    """
    # Get custom quest dialogue
    quest_guidance = DialogueRegistry.get_quest_dialogue(quest_id, "guidance")
    quest_hint = DialogueRegistry.get_quest_dialogue(quest_id, "hint")

    # Default to RAG if no custom dialogue found
    info = rag.get_quest_info(quest_id)
    if not quest_guidance and info:
        quest_guidance = info.get(
            "guidance", "No specific guidance available for this quest."
        )

    # Check if user has completed this quest
    user = utils.load_progress()
    is_completed = user.has_completed_quest(quest_id)

    quest = quests.get_quest(quest_id)
    if not quest:
        # Create a QuestInfo object for non-existent quest
        return standardize_tool_output(
            "get_quest_details",
            {
                "id": quest_id,
                "name": info.get("name", f"Unknown Quest ({quest_id})"),
                "description": info.get("description", "Quest information not found"),
                "is_completed": is_completed,
                "formatted_text": f"Quest '{info.get('name', quest_id)}' not found.",
            },
            return_type=QuestDetailOutput,
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
    return standardize_tool_output(
        "get_quest_details", quest_data, return_type=QuestDetailOutput
    )


def suggest_next_quest(user_memory: UserMemory) -> QuestDetailOutput:
    """
    Suggest the next quest for a user to complete.

    Args:
        user_memory: User memory data

    Returns:
        QuestDetailOutput with quest suggestion
    """
    # Get suggested quests
    suggested = user_memory.custom_data.get("suggested_quests", [])

    if not suggested:
        # If no suggestions in memory, get them from quests module
        user = utils.load_progress()
        quest_objects = quests.get_suggested_quests(user, limit=1)
        if not quest_objects:
            # Create an empty QuestInfo for when there's no suggestion
            return standardize_tool_output(
                "suggest_next_quest",
                {
                    "id": "",
                    "name": "No suggestion available",
                    "description": "No quests to suggest at this time.",
                    "reward_xp": 0,
                    "has_suggestion": False,
                    "formatted_text": "No quest suggestions available at this time.",
                },
                return_type=QuestDetailOutput,
            )

        # Use the first suggested quest
        quest = quest_objects[0]
        quest_info = rag.get_quest_info(quest.id)
    else:
        # Use the first suggestion from memory
        quest_info = suggested[0]
        quest = quests.get_quest(quest_info["id"])
        if not quest:
            # Create an empty QuestInfo for when there's no suggestion
            return standardize_tool_output(
                "suggest_next_quest",
                {
                    "id": "",
                    "name": "No suggestion available",
                    "description": "No quests to suggest at this time.",
                    "reward_xp": 0,
                    "has_suggestion": False,
                    "formatted_text": "No quest suggestions available at this time.",
                },
                return_type=QuestDetailOutput,
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
        "has_suggestion": True,
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

    quest_data["formatted_text"] = formatted_text
    return standardize_tool_output(
        "suggest_next_quest", quest_data, return_type=QuestDetailOutput
    )


def verify_quest_completion(user_memory: UserMemory) -> QuestCompletionOutput:
    """
    Check for newly completed quests.

    Args:
        user_memory: User memory data with current quest status

    Returns:
        QuestCompletionOutput with quest verification results following the standardized schema
    """
    # Load progress and check for completed quests
    user = utils.load_progress()

    # Use the completed_quests from user_memory to check for new completions
    already_completed = set(user_memory.completed_quests)
    newly_completed = quests.check_quest_completion(user)

    # Filter out quests that were already in user_memory as completed
    newly_completed = [
        quest for quest in newly_completed if quest.id not in already_completed
    ]

    # Initialize XP gained
    total_xp_gained = 0
    badge_awarded = False

    if not newly_completed:
        # Check session history to personalize the message
        session_history = user_memory.custom_data.get("session_history", [])
        completion_attempts = sum(
            1
            for session in session_history
            if "complete" in session.get("content_snippet", "").lower()
        )

        message = "No newly completed quests found."
        if completion_attempts > 2:
            message = "I don't see any newly completed quests. Are you having trouble with a particular quest? I'd be happy to help!"

        # Create and return a properly typed QuestCompletionOutput using return_type parameter
        return standardize_tool_output(
            "verify_quest_completion",
            {
                "quests_completed": False,
                "completed_quests": [],
                "completed_details": [],
                "total_completed_count": 0,
                "formatted_text": message,
                "badge_awarded": False,
                "xp_gained": 0,
                "level_up": False,
            },
            return_type=QuestCompletionOutput,
        )

    # Apply completions and get quest details
    completed_details = []
    old_level = user_memory.level

    for quest in newly_completed:
        quests.complete_quest(user, quest.id)

        # Track XP gained
        total_xp_gained += quest.reward_xp

        # Get badge info if one is awarded
        badge_info = None
        if quest.badge_id:
            badge = badges.get_badge(quest.badge_id)
            if badge:
                badge_info = f"{badge.emoji} {badge.name}"
                badge_awarded = True

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

    # Check if the user leveled up due to the XP gain
    new_xp = user_memory.xp + total_xp_gained
    xp_per_level = 100  # Assuming 100 XP per level as a baseline
    new_level = 1 + (new_xp // xp_per_level)  # Simple level calculation
    level_up = new_level > old_level

    # Convert the newly_completed quests to QuestInfo objects for the Pydantic model
    quest_info_list = [
        QuestInfo(
            id=quest.id,
            name=quest.name,
            description=quest.description,
            reward_xp=quest.reward_xp,
            badge_id=quest.badge_id,
            is_completed=True,
        )
        for quest in newly_completed
    ]

    if level_up:
        header = f"🎉 LEVEL UP! You're now level {new_level}! 🎉"
    elif user_memory.level >= 5:
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

    details_text = "\n\n".join(
        [
            f"{details['formatted']}\n{details['completion_message']}"
            for details in completed_details
        ]
    )

    # Add level up information to the formatted text if applicable
    if level_up:
        level_up_text = (
            f"\n\n✨ You leveled up from level {old_level} to level {new_level}! ✨"
        )
        formatted_text = f"{header}\n\n{details_text}{milestone_text}{level_up_text}"
    else:
        formatted_text = f"{header}\n\n{details_text}{milestone_text}"

    # Convert completed_details to proper QuestCompletionDetail objects
    completion_details = [
        QuestCompletionDetail(
            id=detail["id"],
            name=detail["name"],
            reward_xp=detail["reward_xp"],
            badge=detail.get("badge"),
            completion_message=detail["completion_message"],
            formatted=detail["formatted"],
        )
        for detail in completed_details
    ]

    # Return a properly typed QuestCompletionOutput using the return_type parameter
    return standardize_tool_output(
        "verify_quest_completion",
        {
            "quests_completed": True,
            "completed_quests": quest_info_list,
            "completed_details": completion_details,
            "total_completed_count": total_completed,
            "formatted_text": formatted_text,
            "badge_awarded": badge_awarded,
            "xp_gained": total_xp_gained,
            "level_up": level_up,
            "old_level": old_level,
            "new_level": new_level,
        },
        return_type=QuestCompletionOutput,
    )
