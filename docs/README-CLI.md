# QuackCore CLI Bootstrapper

The QuackCore CLI Bootstrapper provides a unified framework for initializing command-line applications in the QuackVerse ecosystem. It handles configuration loading, logging setup, and environment initialization with consistent behavior across all tools.

## Overview

The CLI bootstrapper is designed to be a shared foundation that all QuackVerse CLI tools can rely on, ensuring a consistent user experience and reducing code duplication. It's built with modern Python practices and provides extensive utilities for common CLI tasks.

## Key Features

- **Unified CLI Environment**: Consistent startup behavior across all tools
- **Configuration Management**: Load config from files, environment variables, or CLI flags
- **Smart Logging**: Configurable logging with support for debug, quiet, and log levels
- **Rich CLI Utilities**: Colorized output, progress bars, interactive prompts
- **Type Safety**: Full type hints and Pydantic models for better developer experience
- **Error Handling**: Standardized error formatting and handling

## Core Components

### QuackContext

The `QuackContext` class encapsulates all the runtime information needed by CLI commands:

```python
@dataclass(frozen=True)
class QuackContext:
    config: QuackConfig                # Loaded configuration
    logger: logging.Logger             # Configured logger
    base_dir: Path                     # Base directory
    environment: str                   # Current environment
    debug: bool = False                # Debug mode flag
    verbose: bool = False              # Verbose output flag
    working_dir: Path = field(default_factory=Path.cwd)  # Working directory
    extra: dict[str, Any] = field(default_factory=dict)  # Custom data
```

### Primary Functions

- **`init_cli_env()`**: Main entry point for bootstrapping CLI applications
- **`setup_logging()`**: Configure logging based on CLI flags and configuration
- **`load_config()`**: Load configuration with proper precedence (CLI > env vars > config file)
- **`format_cli_error()`**: Format errors for CLI display
- **`from_cli_options()`**: Initialize from a parsed CliOptions object

### Utility Functions

The `utils.py` module provides helpers for:

- **Colored Output**: `colorize()`, `print_error()`, `print_success()`, etc.
- **User Interaction**: `confirm()`, `ask()`, `ask_choice()`
- **Progress Reporting**: `show_progress()`, `ProgressReporter`, `with_spinner()`
- **Text Formatting**: `table()`, `truncate_text()`, `dict_to_table()`

## Installation

The CLI bootstrapper is included with QuackCore:

```bash
pip install quack-core
```

## Basic Usage

```python
from quack_core.cli import init_cli_env, print_success

# Initialize CLI environment
ctx = init_cli_env(
    config_path="config.yaml",
    debug=True,
    verbose=True,
    app_name="myapp",
)

# Access components from the context
ctx.logger.info("Application started")
project_name = ctx.config.general.project_name
output_dir = ctx.config.paths.output_dir

# Use CLI utilities
print_success(f"Successfully loaded project: {project_name}")
```

## Framework Integration

### With Typer

```python
import typer
from typing import Annotated
from quack_core.cli import init_cli_env, print_error

app = typer.Typer()

@app.command()
def hello(
    name: str,
    debug: Annotated[bool, typer.Option("--debug", "-d")] = False,
):
    ctx = init_cli_env(debug=debug, app_name="myapp.hello")
    ctx.logger.debug(f"Hello {name}")
    print(f"Hello, {name}!")

if __name__ == "__main__":
    app()
```

### With Click

```python
import click
from quack_core.cli import init_cli_env, print_success

@click.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.argument("name")
def hello(debug, name):
    ctx = init_cli_env(debug=debug, app_name="myapp.hello")
    print_success(f"Hello, {name}!")

if __name__ == "__main__":
    hello()
```

### With ArgParse

```python
import argparse
from quack_core.cli import init_cli_env, print_success

def main():
    parser = argparse.ArgumentParser(description="My CLI App")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("name", help="Your name")
    
    args = parser.parse_args()
    
    ctx = init_cli_env(debug=args.debug, app_name="myapp")
    print_success(f"Hello, {args.name}!")

if __name__ == "__main__":
    main()
```

## Best Practices

1. **Call `init_cli_env()` at the beginning** of each command to ensure proper setup
2. **Use the logger from the context** for consistent logging behavior
3. **Access configuration through the context** to ensure it's properly loaded and normalized
4. **Handle errors with try/except** and use `print_error()` for user-friendly messages
5. **Leverage the utility functions** for consistent output formatting and user interaction
6. **Use meaningful app_name values** to create a logical logger hierarchy (e.g., "myapp.command.subcommand")
7. **Provide helpful docstrings** for CLI commands to auto-generate good help text

## Advanced Features

### Progress Reporting

```python
from quack_core.cli import show_progress
import time

# Simple progress bar
for i in show_progress(range(100), desc="Processing"):
    time.sleep(0.1)

# Custom progress reporter
from quack_core.cli import ProgressReporter

reporter = ProgressReporter(total=100, desc="Downloading")
reporter.start()

for i in range(100):
    # Do some work
    time.sleep(0.1)
    reporter.update(i+1, f"File {i+1}/100")

reporter.finish("Download complete!")
```

### Interactive Prompts

```python
from quack_core.cli import ask, confirm, ask_choice

# Simple input
name = ask("What's your name?", required=True)

# Password input
password = ask("Enter password:", hide_input=True)

# Confirmation
if confirm("Are you sure?", default=False):
    print("Confirmed!")

# Selection from choices
role = ask_choice(
    "Select your role:",
    ["Admin", "User", "Guest"],
    default=1
)
```

### Tables and Formatting

```python
from quack_core.cli import table, dict_to_table

# Simple table
headers = ["Name", "Role", "Status"]
rows = [
    ["Alice", "Admin", "Active"],
    ["Bob", "User", "Inactive"],
    ["Charlie", "Guest", "Active"]
]
print(table(headers, rows, title="User List"))

# Dict to table
user_info = {
    "name": "Alice",
    "role": "Admin",
    "status": "Active",
    "last_login": "2025-03-20"
}
print(dict_to_table(user_info, title="User Details"))
```

## Design Philosophy

The CLI bootstrapper follows these principles:

- **Separation of concerns**: Bootstrapping is separate from command logic
- **Consistent behavior**: All CLI tools behave the same way
- **Reusable components**: Avoid duplicating code across CLI tools
- **Sensible defaults**: Work out-of-the-box with minimal configuration
- **Extensibility**: Allow customization where needed
- **Type safety**: Leverage Python's type system for better developer experience
- **Modern Python practices**: Use the latest Python features appropriately

## Contributing

Contributions to the CLI bootstrapper are welcome! Please follow these guidelines:

1. Ensure all code has proper type hints
2. Add tests for new features
3. Follow the existing code style
4. Document new features in docstrings and update the README if needed

## License

QuackCore is licensed under the MIT License. See the LICENSE file for details.