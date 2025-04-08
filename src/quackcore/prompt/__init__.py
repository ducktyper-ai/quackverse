# src/quackcore/prompt/__init__.py
"""
QuackCore Prompt module.

This module provides tools and strategies for creating high-quality LLM prompts.
"""
from .booster import PromptBooster
from .strategy_base import PromptStrategy
from .registry import (
    register_prompt_strategy,
    get_strategy_by_id,
    find_strategies_by_tags,
    get_all_strategies,
)

# Import strategies package to register all strategies
from . import strategies

__all__ = [
    "PromptBooster",
    "PromptStrategy",
    "register_prompt_strategy",
    "get_strategy_by_id",
    "find_strategies_by_tags",
    "get_all_strategies",
]