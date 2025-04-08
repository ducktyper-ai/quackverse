# src/quackcore/prompt/strategies/__init__.py
"""
Prompt strategies package for the PromptBooster.

This package contains various prompt enhancement strategies.
"""
# Import all strategies to register them
from . import multi_shot_structured
from . import single_shot_structured
from . import react_agentic
from . import zero_shot_cot
from . import task_decomposition

__all__ = [
    "multi_shot_structured",
    "single_shot_structured",
    "react_agentic",
    "zero_shot_cot",
    "task_decomposition",
]