# src/quackcore/teaching/npc/dialogue/__init__.py
"""
Dialogue system for the Quackster teaching NPC.

This module provides access to Quackster's dialogue templates and phrases,
allowing for consistent character representation across interactions.
"""

from quackcore.teaching.npc.dialogue.registry import DialogueRegistry

__all__ = ["DialogueRegistry"]