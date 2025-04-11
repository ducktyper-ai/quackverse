"""
Tests for the individual prompt strategy implementations.
"""

import pytest

from quackcore.prompt.registry import clear_registry, get_strategy_by_id


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Clear registry at the start to prevent cross-test contamination
    clear_registry()

    # Re-import the strategies to ensure they're registered
    from quackcore.prompt.strategies import (
        multi_shot_structured,
        react_agentic,
        single_shot_structured,
        task_decomposition,
        zero_shot_cot,
    )

    yield

    # Clear registry after test
    clear_registry()


def test_zero_shot_cot_rendering():
    """Test the zero-shot COT strategy renders correctly."""
    # Get the strategy from the registry
    strategy = get_strategy_by_id("zero-shot-cot")

    # Test basic rendering
    task = "Solve this math problem: 5 + 7 * 2"
    result = strategy.render_fn(task_description=task)

    # Check the content
    assert task in result
    assert "Let's think through this step by step." in result

    # Test with final instruction
    final_instruction = "Show your work and explain each step."
    result_with_final = strategy.render_fn(
        task_description=task, final_instruction=final_instruction
    )

    # Check the content includes the final instruction
    assert task in result_with_final
    assert "Let's think through this step by step." in result_with_final
    assert final_instruction in result_with_final


def test_task_decomposition_rendering():
    """Test the task decomposition strategy renders correctly."""
    # Get the strategy from the registry
    strategy = get_strategy_by_id("task-decomposition")

    # Test basic rendering
    task = "Create a Python function that calculates the Fibonacci sequence."
    result = strategy.render_fn(task_description=task)

    # Check the content
    assert task in result
    assert "Break down this task into smaller, manageable subtasks" in result
    assert "List each subtask in the order they should be addressed" in result
    assert "Solve each subtask step by step" in result

    # Test with output format
    output_format = "Provide the code in a Python code block with comments."
    result_with_format = strategy.render_fn(
        task_description=task, output_format=output_format
    )

    # Check the content includes the output format instructions
    assert task in result_with_format
    assert (
        "format your final answer according to these instructions" in result_with_format
    )
    assert output_format in result_with_format


def test_multi_shot_structured_rendering():
    """Test the multi-shot structured strategy renders correctly."""
    # Get the strategy from the registry
    strategy = get_strategy_by_id("multi-shot-structured")

    # Test parameters
    task = "Extract company names and their founding dates from the text."
    schema = '{"companies": [{"name": "string", "founding_date": "string"}]}'
    examples = [
        'Text: "Apple Inc. was founded on April 1, 1976."\nOutput: {"companies": [{"name": "Apple Inc.", "founding_date": "April 1, 1976"}]}',
        'Text: "Microsoft Corporation was established in 1975 by Bill Gates."\nOutput: {"companies": [{"name": "Microsoft Corporation", "founding_date": "1975"}]}',
    ]

    # Test with list of examples
    result_list = strategy.render_fn(
        task_description=task, schema=schema, examples=examples
    )

    # Check content
    assert task in result_list
    assert schema in result_list
    assert examples[0] in result_list
    assert examples[1] in result_list

    # Test with string of examples
    examples_str = "\n\n".join(examples)
    result_str = strategy.render_fn(
        task_description=task, schema=schema, examples=examples_str
    )

    # Both results should be identical
    assert result_list == result_str


def test_single_shot_structured_rendering():
    """Test the single-shot structured strategy renders correctly."""
    # Get the strategy from the registry
    strategy = get_strategy_by_id("single-shot-structured")

    # Test parameters
    task = "Extract the main sentiment from the text."
    schema = '{"sentiment": "string", "confidence": "number"}'
    example = 'Text: "I really enjoyed the movie!"\nOutput: {"sentiment": "positive", "confidence": 0.95}'

    # Test with example
    result = strategy.render_fn(task_description=task, schema=schema, example=example)

    # Check content
    assert task in result
    assert schema in result
    assert example in result
    assert "Here is an example:" in result

    # Test without example
    result_no_example = strategy.render_fn(task_description=task, schema=schema)

    # Check content
    assert task in result_no_example
    assert schema in result_no_example
    assert "Here is an example:" not in result_no_example


def test_react_agentic_rendering():
    """Test the ReAct agentic strategy renders correctly."""
    # Get the strategy from the registry
    strategy = get_strategy_by_id("react-agentic")

    # Test parameters
    task = "Find information about the population of New York City."
    tools = [
        {
            "name": "search",
            "description": "Search for information on the web",
            "parameters": {"query": "The search query string"},
        },
        {
            "name": "calculate",
            "description": "Calculate a mathematical expression",
            "parameters": {"expression": "The expression to calculate"},
        },
    ]

    # Test with tools as list
    result_list = strategy.render_fn(task_description=task, tools=tools)

    # Check content
    assert task in result_list
    assert "Available tools:" in result_list
    assert "search: Search for information on the web" in result_list
    assert "calculate: Calculate a mathematical expression" in result_list
    assert "Thought: <your reasoning about what to do next>" in result_list

    # Test with tools as string
    tools_str = "You have access to:\n- search: Search for information\n- calculate: Calculate math expressions"
    result_str = strategy.render_fn(task_description=task, tools=tools_str)

    # Check content
    assert task in result_str
    assert tools_str in result_str

    # Test with examples
    examples = [
        "Example 1: [Example of the ReAct process]",
        "Example 2: [Another example]",
    ]
    result_with_examples = strategy.render_fn(
        task_description=task, tools=tools, examples=examples
    )

    # Check examples are included
    assert "Examples:" in result_with_examples
    assert "Example 1: [Example of the ReAct process]" in result_with_examples
    assert "Example 2: [Another example]" in result_with_examples


def test_system_prompt_engineer():
    """Test the system prompt engineer strategy, which may be imported separately."""
    try:
        # Import the module
        from quackcore.prompt.strategies import system_prompt_engineer

        # Get the strategy
        strategy = get_strategy_by_id("system-prompt-engineer")

        # Test rendering
        example_prompt = "Write a poem about artificial intelligence."
        result = strategy.render_fn(strategy=example_prompt)

        # Check content
        assert "You are an expert prompt engineer" in result
        assert example_prompt in result
        assert "IMPORTANT: Only output the rewritten prompt" in result

    except (ImportError, KeyError):
        # Skip test if module is not available or not registered
        pytest.skip("system-prompt-engineer strategy not available")
