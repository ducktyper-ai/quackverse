# src/quackcore/prompt/strategy_base.py
"""
Base strategy module for the PromptBooster.

This module defines the PromptStrategy class that serves as the foundation
for all prompt enhancement strategies in the QuackCore ecosystem.
"""

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PromptStrategy(BaseModel):
    """
    A reusable prompt strategy that encodes information about
    how to transform a basic prompt into an enhanced one.

    Attributes:
        id: Unique identifier for the strategy
        label: Human-readable name for the strategy
        description: Detailed explanation of what the strategy does
        input_vars: List of input variables required by the strategy
        render_fn: Function that renders the prompt given the input variables
        tags: List of tags for categorizing and searching strategies
        origin: Optional source of the strategy (paper, blog, etc.)
    """

    id: str = Field(..., description="Unique identifier for the strategy")
    label: str = Field(..., description="Human-readable name for the strategy")
    description: str = Field(
        ..., description="Detailed explanation of what the strategy does"
    )
    input_vars: list[str] = Field(
        ..., description="List of input variables required by the strategy"
    )
    render_fn: Callable[..., str] = Field(
        ..., description="Function that renders the prompt"
    )
    tags: list[str] = Field(
        default_factory=list, description="Tags for categorizing strategies"
    )
    origin: str | None = Field(
        None, description="Source of the strategy (paper, blog, etc.)"
    )

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True
