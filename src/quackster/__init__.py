# src/quackster/__init__.py
"""
QuackCore Teaching Module.

This module provides a gamified education system with XP, badges, quests,
and a quackster NPC named Quackster. It's designed for CLI-first interaction
through the DuckTyper tool.

Core Components:
- XP System: Award experience points for completing tasks and activities
- Badge System: Earn badges for reaching XP milestones and completing quests
- Quest System: Complete GitHub-based quests to earn XP and badges
- Teaching NPC: Interact with Quackster, a duck mentor with memory and tools
- Local Progress: Save user progress locally in ~/.quack

Example:
    ```python
    from quackcore.quackster import xp, utils
    from quackcore.quackster.models import XPEvent

    # Load user progress
    user = utils.load_progress()

    # Add XP for completing a task
    event = XPEvent(id="used-ducktyper", label="Used DuckTyper", points=10)
    xp.add_xp(user, event)

    # Save updated progress
    utils.save_progress(user)

    # Talk to Quackster NPC
    from quackcore.quackster.npc import agent
    from quackcore.quackster.npc.schema import TeachingNPCInput

    response = agent.run_npc_session(
        TeachingNPCInput(user_input="What's my current XP?")
    )
    print(response.response_text)
    ```
"""

from quackster.core import badges, certificates, quests, utils, xp
from quackster.core.models import Badge, Quest, UserProgress, XPEvent
from quackster.npc import agent

__all__ = [
    # Core models
    "XPEvent",
    "Badge",
    "Quest",
    "UserProgress",
    # Module references
    "xp",
    "badges",
    "quests",
    "utils",
    "certificates",
    "agent",
]
