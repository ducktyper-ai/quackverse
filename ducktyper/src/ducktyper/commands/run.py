# ducktyper/src/ducktyper/commands/run.py
"""
Implementation of the 'run' command.

The run command executes a specified QuackTool with arguments.
"""

import sys
from difflib import get_close_matches

import typer

from ducktyper.src.ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.branding import (
    duck_dance,
    print_banner,
    print_error,
    print_info,
    print_loading,
    print_success,
    quack_say,
)
from quackcore.cli import CliContext
from quackcore.plugins.registry import execute_command, get_plugin, list_plugins

# Create Typer app for the run command
app = typer.Typer(
    name="run",
    help="Run a QuackTool with arguments.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def run_tool(
        ctx: typer.Context,
        tool_name: str = typer.Argument(..., help="Name of the tool to run"),
        args: list[str] | None = typer.Argument(
            None, help="Arguments to pass to the tool"
        ),
        dance: bool = typer.Option(
            False, "--dance", help="Do a victory dance after successful completion"
        ),
) -> None:
    """
    Run a QuackTool with the specified arguments.

    Examples:

        tests run quackmeta --help

        tests run quackviz mydata.csv --format png
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    # Parse args if None (handles Typer's behavior with empty arguments)
    if args is None:
        args = []

    try:
        # Get the plugin from registry
        plugin = get_plugin(tool_name)

        if plugin is None:
            # Tool not found, try to find similar names
            available_tools = [p.name for p in list_plugins()]
            similar_tools = get_close_matches(tool_name, available_tools, n=3,
                                              cutoff=0.6)

            if similar_tools:
                suggestions = ", ".join(similar_tools)
                print_error(
                    f"Tool '{tool_name}' not found. Did you mean: {suggestions}?")
            else:
                print_error(
                    f"Tool '{tool_name}' not found. Run 'tests list' to see available tools.")

            sys.exit(1)

        # Show running message
        tool_description = getattr(plugin, "description", "")

        if is_playful_mode():
            print_banner(f"Running QuackTool: {tool_name}", tool_description,
                         mood="wizard")
            print_loading(f"Summoning the powers of {tool_name}")
        else:
            print_info(f"Running: {tool_name}")
            if tool_description:
                print_info(f"Description: {tool_description}")

        # Debug log
        cli_env.logger.debug(f"Running tool {tool_name} with args: {args}")

        # Execute the tool's main command
        command = "main"  # Default command name

        # Check if the plugin has a different main command
        if hasattr(plugin, "default_command"):
            command = plugin.default_command

        # Execute the command
        result = execute_command(tool_name, command, args=args)

        # Success message
        if is_playful_mode():
            success_msg = f"✨ '{tool_name}' completed successfully!"
            print_success(success_msg)

            # Victory dance if requested
            if dance or cli_env.config.get_custom("tests.always_dance", False):
                quack_say("Time for a victory dance!")
                duck_dance()
        else:
            print_info(f"Tool '{tool_name}' completed successfully.")

        return result

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"Error running tool '{tool_name}': {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception(f"Error in run command for tool '{tool_name}'")
        sys.exit(1)
