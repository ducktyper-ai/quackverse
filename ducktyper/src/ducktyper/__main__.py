# src/tests/__main__.py
"""
Entry point for the DuckTyper CLI when run as a module.
"""

import sys
from typing import NoReturn, Optional

from ducktyper.main import app
from ducktyper.ui.branding import duck_dance, print_banner, print_error, print_info
from ducktyper.src.ducktyper.ui.mode import is_playful_mode


def display_intro() -> None:
    """Display a fancy intro when DuckTyper is launched with no arguments."""
    if is_playful_mode():
        print_banner("DuckTyper: Your Feathered Terminal Friend", mood="happy")
        print_info("Type 'tests --help' to see available commands.")
        duck_dance()
    else:
        print_info("DuckTyper CLI")
        print_info("Type 'tests --help' to see available commands.")


def main(args: Optional[list[str]] = None) -> NoReturn:
    """Main entry point for the CLI."""
    try:
        if args is None:
            args = sys.argv[1:]

        if not args:
            display_intro()
            sys.exit(0)

        app()
    except KeyboardInterrupt:
        if is_playful_mode():
            print("\n👋 Quackster waves goodbye!")
        else:
            print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if "--debug" in args:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()