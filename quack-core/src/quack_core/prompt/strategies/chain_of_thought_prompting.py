# quack-core/src/quack-core/prompt/strategies/chain_of_thought_prompting.py
"""
Chain of Thought Prompting strategy for the PromptBooster.

This strategy elicits step-by-step reasoning before arriving at a final answer.
"""

from quack_core.prompt.registry import register_prompt_strategy
from quack_core.prompt.strategy_base import PromptStrategy


def render(task_description: str, final_instruction: str | None = None) -> str:
    final_instr = f"\n{final_instruction}" if final_instruction else ""
    return f"""
{task_description}

Let's think through this step by step.{final_instr}
""".strip()

strategy = PromptStrategy(
    id="chain-of-thought-prompting",
    label="Chain of Thought Prompting",
    description="Encourages the model to break down reasoning into intermediate steps.",
    input_vars=["task_description", "final_instruction"],
    render_fn=render,
    tags=["chain-of-thought", "reasoning"],
    origin="Prompt Engineering (Lee Boonstra, February 2025)",
)
register_prompt_strategy(strategy)
