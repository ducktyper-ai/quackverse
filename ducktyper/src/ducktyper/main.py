# src/tests/main.py
"""
Main entry point for the DuckTyper CLI.
"""

import os
from typing import Optional

import typer
from quackcore.cli import init_cli_env
from quackcore.cli.options import CliOptions
from rich.console import Console

from ducktyper.commands import assistant, certify, config, explain, list_cmd, new, run
from ducktyper.ui.branding import duck_dance, print_banner, print_info, print_success
from ducktyper.src.ducktyper.ui.mode import is_playful_mode, set_mode_from_env

# Create the Typer app
app = typer.Typer(
    name="tests",
    help="The unified CLI interface for the QuackVerse ecosystem.",
    add_completion=True,
)

# Register commands
app.add_typer(list_cmd.app, name="list")
app.add_typer(run.app, name="run")
app.add_typer(config.app, name="config")
app.add_typer(explain.app, name="explain")
app.add_typer(new.app, name="new")
app.add_typer(assistant.app, name="assistant")
app.add_typer(certify.app, name="certify")

# Create console for rich output
console = Console()


@app.callback()
def callback(
        ctx: typer.Context,
        mode: str = typer.Option(
            None, "--mode", "-m", help="UI mode: 'teaching' (default) or 'production'"
        ),
        config_path: Optional[str] = typer.Option(
            None, "--config", help="Path to config file"
        ),
        debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
        verbose: bool = typer.Option(False, "--verbose", "-v",
                                     help="Enable verbose output"),
        quiet: bool = typer.Option(False, "--quiet", "-q",
                                   help="Quiet mode (errors only)"),
        log_level: Optional[str] = typer.Option(
            None, "--log-level",
            help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
        ),
        environment: Optional[str] = typer.Option(
            None, "--environment", help="Override environment"
        ),
) -> None:
    """
    DuckTyper: The unified CLI interface for the QuackVerse ecosystem.
    """
    # Set UI mode based on option or environment
    if mode:
        os.environ["DUCKTYPER_MODE"] = mode
    set_mode_from_env()

    # Initialize CLI environment for QuackCore
    cli_options = CliOptions(
        config_path=config_path,
        debug=debug,
        verbose=verbose,
        quiet=quiet,
        log_level=log_level,
        environment=environment,
    )

    ctx.obj = {
        "cli_env": init_cli_env(
            app_name="tests",
            config_path=cli_options.config_path,
            debug=cli_options.debug,
            verbose=cli_options.verbose,
            log_level=cli_options.log_level,
            environment=cli_options.environment,
        ),
        "options": cli_options,
    }


@app.command()
def version() -> None:
    """Show the DuckTyper version."""
    from ducktyper import __version__
    print_info(f"DuckTyper version: {__version__}")


@app.command()
def demo() -> None:
    """Run a demo of DuckTyper's UI capabilities."""
    if is_playful_mode():
        print_banner("Welcome to DuckTyper Demo!", mood="wizard")
        print_info("This is a showcase of DuckTyper's UI capabilities!")

        # Simulate some operations
        with console.status("[bold green]Brewing some duck magic..."):
            # Simulate work
            import time
            time.sleep(2)

        print_success("Demo completed successfully!")
        duck_dance()
    else:
        print_info("DuckTyper Demo")
        print_info("Demo completed in production mode.")