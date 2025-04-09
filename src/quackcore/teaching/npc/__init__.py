# src/quackcore/teaching/npc/__init__.py
"""
Quackster teaching NPC module.

This module provides a teaching NPC (Non-Player Character) named Quackster
who guides users through educational content, quests, and progress tracking.
"""

from quackcore.teaching.npc.agent import run_npc_session
from quackcore.teaching.npc.schema import (
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
