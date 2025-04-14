# src/quackster/npc/dialogue/__init__.py
"""
Dialogue system for the Quackster quackster NPC.

This module provides access to Quackster's dialogue templates and phrases,
allowing for consistent character representation across interactions.
"""

from quackster.npc.dialogue.registry import DialogueRegistry

__all__ = ["DialogueRegistry"]
