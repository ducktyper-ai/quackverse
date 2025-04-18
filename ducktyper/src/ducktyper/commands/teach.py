# src/tests/commands/teach.py
"""
Implementation of the 'teach' command.

The teach command launches an interactive tutorial for a QuackTool.
"""

import sys
from typing import Optional

import typer
from quackcore.cli import CliContext

# Assume Quackster is properly installed and imported
from quackster import TutorialManager
from quackster.models import TutorialOptions

from ducktyper.ui.branding import (
    print_banner,
    print_error,
    print_info,
    quack_say,
)
from ducktyper.src.ducktyper.ui.mode import is_playful_mode

# Create Typer app for the teach command
app = typer.Typer(
    name="teach",
    help="Start an interactive tutorial for a QuackTool.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def teach_tool(
        ctx: typer.Context,
        tool_name: str = typer.Argument(..., help="Name of the tool to learn"),
        level: str = typer.Option(
            "beginner", "--level", "-l",
            help="Tutorial level (beginner, intermediate, advanced)"
        ),
        track: Optional[str] = typer.Option(
            None, "--track", "-t",
            help="Learning track (e.g., 'data-science', 'prompt-engineering')"
        ),
) -> None:
    """
    Start an interactive tutorial for a QuackTool.

    This will guide you through learning a QuackTool with step-by-step
    instructions, challenges, and quizzes.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        if is_playful_mode():
            print_banner(f"Learning {tool_name}",
                         f"Interactive Tutorial ({level.capitalize()})",
                         mood="wizard")
            quack_say(f"Let's learn how to use the {tool_name} tool!")
        else:
            print_info(f"Starting tutorial for {tool_name} ({level.capitalize()})")

        # Initialize the tutorial manager
        tutorial_manager = TutorialManager()

        # Configure tutorial options
        options = TutorialOptions(
            tool_name=tool_name,
            level=level,
            track=track,
            interactive=True,
            playful_mode=is_playful_mode(),
        )

        # Start the tutorial
        result = tutorial_manager.start_tutorial(options)

        if not result.success:
            print_error(f"Failed to start tutorial: {result.error}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Error in tutorial: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception(f"Error in teach command for tool '{tool_name}'")
        sys.exit(1)