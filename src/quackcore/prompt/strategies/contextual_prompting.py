# src/quackcore/prompt/strategies/contextual_prompting.py
"""
Contextual Prompting strategy for the PromptBooster.

This strategy provides task-specific context or background information.
"""

from quackcore.prompt.registry import register_prompt_strategy
from quackcore.prompt.strategy_base import PromptStrategy


def render(context: str, task_description: str) -> str:
    return f"""
Context: {context}

{task_description}
""".strip()

strategy = PromptStrategy(
    id="contextual-prompting",
    label="Contextual Prompting",
    description="Supplies background context to guide the model’s response.",
    input_vars=["context", "task_description"],
    render_fn=render,
    tags=["contextual-prompt", "background"],
    origin="Prompt Engineering (Lee Boonstra, February 2025)",
)
register_prompt_strategy(strategy)
