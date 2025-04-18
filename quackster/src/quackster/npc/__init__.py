# quackster/src/quackster/npc/__init__.py
"""
Quackster quackster NPC module.

This module provides a quackster NPC (Non-Player Character) named Quackster
who guides users through educational content, quests, and progress tracking.
"""

from quackster.npc.agent import run_npc_session
from quackster.npc.schema import (
    QuacksterProfile,
    TeachingNPCInput,
    TeachingNPCResponse,
)

__all__ = [
    # Schema
    "TeachingNPCInput",
    "TeachingNPCResponse",
    "QuacksterProfile",
    # Main function
    "run_npc_session",
]
