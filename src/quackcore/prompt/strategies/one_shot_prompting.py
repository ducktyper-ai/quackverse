# src/quackcore/prompt/strategies/one_shot_prompting.py
"""
One-shot Prompting strategy for the PromptBooster.

This strategy provides a single example demonstration to guide the LLM.
"""

from quackcore.prompt.registry import register_prompt_strategy
from quackcore.prompt.strategy_base import PromptStrategy


def render(task_description: str, example: str) -> str:
    return f"""
{task_description}

Example:
{example}
""".strip()

strategy = PromptStrategy(
    id="one-shot-prompting",
    label="One-shot Prompting",
    description="Provides one example to guide the model’s response.",
    input_vars=["task_description", "example"],
    render_fn=render,
    tags=["one-shot", "few-shot"],
    origin="Prompt Engineering (Lee Boonstra, February 2025)",
)
register_prompt_strategy(strategy)
