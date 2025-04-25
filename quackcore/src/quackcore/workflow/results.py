# quackcore/src/quackcore/workflow/results.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class InputResult(BaseModel):
    """Result returned after resolving the input source."""
    success: bool = True
    path: Path
    metadata: dict[str, Any] = Field(default_factory=dict)

class OutputResult(BaseModel):
    """Result returned after processing the input content."""
    success: bool = True
    content: Any
    raw_text: str | None = None

class FinalResult(BaseModel):
    """Final result returned after completing the workflow."""
    success: bool = True
    result_path: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
