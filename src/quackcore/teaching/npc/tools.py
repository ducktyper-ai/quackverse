# src/quackcore/teaching/npc/tools.py
"""
Tools for the Quackster teaching NPC.

This module provides tool functions that the NPC can use to answer
questions, check progress, and provide guidance.
"""

from typing import Any

from quackcore.logging import get_logger
from quackcore.teaching import badges, quests, utils
from quackcore.teaching.npc import rag
from quackcore.teaching.npc.schema import UserMemory

logger = get_logger(__name__)


def list_xp_and_level(user_memory: UserMemory) -> dict[str, Any]:
    """
    Get information about a user's XP and level.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with XP and level information
    """
    level = user_memory.level
    xp = user_memory.xp
    xp_to_next = user_memory.custom_data.get("xp_to_next_level", 100)
    next_level = level + 1

    # Calculate percentage progress to next level
    progress_pct = int(100 - (xp_to_next / (next_level * 100) * 100))

    # Create progress bar
    progress_bar = "█" * (progress_pct // 5) + "░" * ((100 - progress_pct) // 5)

    return {
        "level": level,
        "xp": xp,
        "next_level": next_level,
        "xp_needed": xp_to_next,
        "progress_pct": progress_pct,
        "progress_bar": progress_bar,
        "formatted_text": f"Level {level} ({xp} XP)\n{progress_bar} {progress_pct}%\n{xp_to_next} XP needed for Level {next_level}",
    }


def list_badges(user_memory: UserMemory) -> dict[str, Any]:
    """
    Get information about a user's badges.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with badge information
    """
    # Load full badge data
    user = utils.load_progress()
    user_badges = badges.get_user_badges(user)

    # Format badge list with emojis
    badge_list = [f"{badge.emoji} {badge.name}" for badge in user_badges]

    # Get next badges user could earn
    next_badges = badges.get_next_badges(user, limit=3)
    next_badge_list = []

    for badge in next_badges:
        progress = badges.get_badge_progress(user, badge.id) * 100
        progress_str = f"({progress:.0f}% complete)"
        next_badge_list.append(
            {
                "id": badge.id,
                "name": badge.name,
                "emoji": badge.emoji,
                "description": badge.description,
                "required_xp": badge.required_xp,
                "progress": progress,
                "formatted": f"{badge.emoji} {badge.name} - {badge.description} {progress_str}",
            }
        )

    return {
        "earned_badges": user_badges,
        "earned_count": len(user_badges),
        "earned_formatted": badge_list if badge_list else ["No badges earned yet"],
        "next_badges": next_badges,
        "next_badges_formatted": [b["formatted"] for b in next_badge_list]
        if next_badge_list
        else ["Keep earning XP to unlock badges!"],
        "formatted_text": f"You have earned {len(user_badges)} badges.\n\nEarned Badges:\n"
        + "\n".join(badge_list or ["No badges earned yet"])
        + "\n\nNext Badges:\n"
        + "\n".join(
            [b["formatted"] for b in next_badge_list]
            if next_badge_list
            else ["Keep earning XP to unlock badges!"]
        ),
    }


def list_quests(user_memory: UserMemory) -> dict[str, Any]:
    """
    Get information about a user's quests.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with quest information
    """
    # Load full quest data
    user = utils.load_progress()
    quest_data = quests.get_user_quests(user)

    completed = quest_data["completed"]
    available = quest_data["available"]

    # Format completion status
    completed_list = [f"✅ {quest.name} (+{quest.reward_xp} XP)" for quest in completed]

    # Sort available quests by XP reward (highest first)
    available.sort(key=lambda q: q.reward_xp, reverse=True)
    available_list = [
        f"⏳ {quest.name} (+{quest.reward_xp} XP) - {quest.description}"
        for quest in available[:5]
    ]

    # Get suggested quests
    suggested = quests.get_suggested_quests(user, limit=3)
    suggested_list = []

    for quest in suggested:
        badge_text = (
            f" (Earns {badges.get_badge(quest.badge_id).emoji} badge)"
            if quest.badge_id
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

    return {
        "completed": completed,
        "completed_count": len(completed),
        "completed_formatted": completed_list
        if completed_list
        else ["No quests completed yet"],
        "available": available,
        "available_count": len(available),
        "available_formatted": available_list
        if available_list
        else ["No more quests available!"],
        "suggested": suggested,
        "suggested_formatted": [q["formatted"] for q in suggested_list]
        if suggested_list
        else ["No suggested quests available."],
        "formatted_text": f"You have completed {len(completed)} quests and have {len(available)} available.\n\nCompleted Quests:\n"
        + "\n".join(completed_list or ["No quests completed yet"])
        + "\n\nSuggested Quests:\n"
        + "\n".join(
            [q["formatted"] for q in suggested_list]
            if suggested_list
            else ["No suggested quests available."]
        ),
    }


def get_quest_details(quest_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific quest.

    Args:
        quest_id: ID of the quest to get details for

    Returns:
        Dictionary with quest details
    """
    # Get quest info from documentation
    info = rag.get_quest_info(quest_id)

    # Check if user has completed this quest
    user = utils.load_progress()
    is_completed = user.has_completed_quest(quest_id)

    quest = quests.get_quest(quest_id)
    if not quest:
        return {
            "id": quest_id,
            "name": info.get("name", f"Unknown Quest ({quest_id})"),
            "description": info.get("description", "Quest information not found"),
            "is_completed": is_completed,
            "formatted_text": f"Quest '{info.get('name', quest_id)}' not found.",
        }

    # If quest has a badge, get badge info
    badge_info = None
    if quest.badge_id:
        badge = badges.get_badge(quest.badge_id)
        if badge:
            badge_info = f"{badge.emoji} {badge.name} badge"

    return {
        "id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge": badge_info,
        "is_completed": is_completed,
        "status": "Completed" if is_completed else "Not completed",
        "guidance": info.get(
            "guidance", "No specific guidance available for this quest."
        ),
        "formatted_text": (
            f"{'✅' if is_completed else '⏳'} {quest.name}\n\n"
            f"Description: {quest.description}\n"
            f"Reward: {quest.reward_xp} XP"
            f"{f' + {badge_info}' if badge_info else ''}\n"
            f"Status: {is_completed}\n\n"
            f"Guidance:\n{info.get('guidance', 'No specific guidance available.')}"
        ),
    }


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
            return {
                "has_suggestion": False,
                "formatted_text": "No quest suggestions available at this time.",
            }

        # Use the first suggested quest
        quest = quest_objects[0]
        quest_info = rag.get_quest_info(quest.id)
    else:
        # Use the first suggestion from memory
        quest_info = suggested[0]
        quest = quests.get_quest(quest_info["id"])
        if not quest:
            return {
                "has_suggestion": False,
                "formatted_text": "No quest suggestions available at this time.",
            }

    # If quest has a badge, get badge info
    badge_info = None
    if quest.badge_id:
        badge = badges.get_badge(quest.badge_id)
        if badge:
            badge_info = f"{badge.emoji} {badge.name} badge"

    return {
        "has_suggestion": True,
        "quest": quest,
        "quest_id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge": badge_info,
        "guidance": quest_info.get("guidance", "No specific guidance available."),
        "formatted_text": (
            f"I suggest you try the '{quest.name}' quest!\n\n"
            f"Description: {quest.description}\n"
            f"Reward: {quest.reward_xp} XP"
            f"{f' + {badge_info}' if badge_info else ''}\n\n"
            f"Guidance:\n{quest_info.get('guidance', 'No specific guidance available.')}"
        ),
    }


def get_badge_details(badge_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific badge.

    Args:
        badge_id: ID of the badge to get details for

    Returns:
        Dictionary with badge details
    """
    # Get badge info from documentation
    info = rag.get_badge_info(badge_id)

    # Check if user has this badge
    user = utils.load_progress()
    is_earned = user.has_earned_badge(badge_id)

    badge = badges.get_badge(badge_id)
    if not badge:
        return {
            "id": badge_id,
            "name": info.get("name", f"Unknown Badge ({badge_id})"),
            "description": info.get("description", "Badge information not found"),
            "is_earned": is_earned,
            "formatted_text": f"Badge '{info.get('name', badge_id)}' not found.",
        }

    # Get progress toward earning this badge
    progress = badges.get_badge_progress(user, badge_id) * 100
    progress_bar = "█" * (int(progress) // 5) + "░" * ((100 - int(progress)) // 5)

    return {
        "id": badge.id,
        "name": badge.name,
        "emoji": badge.emoji,
        "description": badge.description,
        "required_xp": badge.required_xp,
        "is_earned": is_earned,
        "progress": progress,
        "progress_bar": progress_bar,
        "guidance": info.get("guidance", "No specific guidance available."),
        "fun_fact": info.get("fun_fact", ""),
        "formatted_text": (
            f"{badge.emoji} {badge.name}\n\n"
            f"Description: {badge.description}\n"
            f"Status: {'Earned' if is_earned else 'Not yet earned'}\n"
            f"{f'Required XP: {badge.required_xp}' if badge.required_xp > 0 else ''}\n"
            f"{f'Progress: {progress:.0f}%\n{progress_bar}' if not is_earned and badge.required_xp > 0 else ''}\n\n"
            f"How to earn: {info.get('guidance', 'No specific guidance available.')}\n\n"
            f"Fun fact: {info.get('fun_fact', '')}"
        ),
    }


def verify_quest_completion(user_memory: UserMemory) -> dict[str, Any]:
    """
    Check for newly completed quests.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with quest verification results
    """
    # Load progress and check for completed quests
    user = utils.load_progress()
    newly_completed = quests.check_quest_completion(user)

    if not newly_completed:
        return {
            "quests_completed": False,
            "completed_quests": [],
            "formatted_text": "No newly completed quests found.",
        }

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

        completed_details.append(
            {
                "id": quest.id,
                "name": quest.name,
                "reward_xp": quest.reward_xp,
                "badge": badge_info,
                "formatted": f"✅ {quest.name} (+{quest.reward_xp} XP)"
                + (f" → Earned {badge_info}!" if badge_info else ""),
            }
        )

    # Save the updated progress
    utils.save_progress(user)

    return {
        "quests_completed": True,
        "completed_quests": newly_completed,
        "completed_details": completed_details,
        "formatted_text": "🎉 You've completed "
        + (
            "a new quest!"
            if len(newly_completed) == 1
            else f"{len(newly_completed)} new quests!"
        )
        + "\n\n"
        + "\n".join([details["formatted"] for details in completed_details]),
    }


def get_tutorial(topic: str) -> dict[str, Any]:
    """
    Get tutorial information for a specific topic.

    Args:
        topic: Topic to get tutorial for

    Returns:
        Dictionary with tutorial information
    """
    # Get tutorial from RAG
    tutorial = rag.get_tutorial_topic(topic)

    return {
        "topic": topic,
        "title": tutorial.get("title", f"Tutorial on {topic}"),
        "description": tutorial.get("description", ""),
        "content": tutorial.get(
            "content", "No tutorial content available for this topic."
        ),
        "formatted_text": f"# {tutorial.get('title', f'Tutorial on {topic}')}\n\n"
        + f"{tutorial.get('description', '')}\n\n"
        + f"{tutorial.get('content', 'No tutorial content available for this topic.')}",
    }


def get_certificate_info(user_memory: UserMemory) -> dict[str, Any]:
    """
    Get information about certificates that the user can earn.

    Args:
        user_memory: User memory data

    Returns:
        Dictionary with certificate information
    """
    from quackcore.teaching import certificates

    # Load user progress
    user = utils.load_progress()

    # Check available certificates
    available_certificates = [
        {
            "id": "quackverse-basics",
            "name": "QuackVerse Basics",
            "description": "Completed the introductory QuackVerse curriculum",
            "earned": certificates.has_earned_certificate(user, "quackverse-basics"),
            "requirements": [
                "Complete the 'star-quackcore' quest",
                "Complete the 'run-ducktyper' quest",
                "Complete the 'complete-tutorial' quest",
                "Earn at least 100 XP",
            ],
        },
        {
            "id": "github-contributor",
            "name": "GitHub Contributor",
            "description": "Contributed to the QuackVerse ecosystem on GitHub",
            "earned": certificates.has_earned_certificate(user, "github-contributor"),
            "requirements": [
                "Complete the 'open-pr' quest",
                "Complete the 'merged-pr' quest",
                "Earn the 'duck-team-player' badge",
                "Earn at least 300 XP",
            ],
        },
    ]

    # Format certificate list
    cert_list = []
    for cert in available_certificates:
        status = "✅ Earned" if cert["earned"] else "⏳ Not yet earned"
        cert_list.append(
            {
                "id": cert["id"],
                "name": cert["name"],
                "description": cert["description"],
                "earned": cert["earned"],
                "requirements": cert["requirements"],
                "formatted": f"{cert['name']} - {cert['description']}\n  Status: {status}",
            }
        )

    # If any certificate is earned, mention how to generate it
    earned_any = any(cert["earned"] for cert in available_certificates)
    generation_info = (
        """
To generate your certificate, use the following command:
```
ducktyper cert --course=certificate_id
```
Replace 'certificate_id' with the ID of the certificate you've earned.
"""
        if earned_any
        else ""
    )

    return {
        "certificates": available_certificates,
        "earned_any": earned_any,
        "formatted_text": f"# Available Certificates\n\n"
        + "\n\n".join([cert["formatted"] for cert in cert_list])
        + generation_info,
    }
