# ducktyper/src/ducktyper/ui/branding.py
"""
DuckTyper branding and UI components.

This module implements the UI components for DuckTyper, including the retro
RPG-inspired styling, ASCII art, and interactive elements.
"""

import time
from enum import Enum
from typing import TypeVar

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from ducktyper.ui.mode import is_playful_mode

# Create console for rich output
console = Console()

# Type variable for generic functions
T = TypeVar("T")

# === 🎨 Color Palette (16-bit Inspired) === #
COLOR_PALETTE = {
    "primary": "medium_purple3",  # Main brand color
    "accent": "cyan",  # Secondary color
    "highlight": "bright_yellow",  # For important elements
    "success": "spring_green2",  # Success messages
    "error": "red",  # Error messages
    "warning": "orange1",  # Warning messages
    "info": "sky_blue2",  # Info messages
    "gray": "gray70",  # Subtle text
    "border": "white",  # Borders
    "title": "bold medium_purple3",  # Titles
    "rose": "#ff87ff",  # Rose Quartz
    "gold": "#ffd700",  # Pixel Gold
    "mana": "#00afff",  # Mana Blue
    "obsidian": "#000000",  # Obsidian
}


class Mood(str, Enum):
    """Moods for Quackster."""

    HAPPY = "happy"
    WIZARD = "wizard"
    MAD = "mad"
    SLEEPY = "sleepy"
    SURPRISED = "surprised"
    DUCKROLL = "duckroll"


class AlertLevel(str, Enum):
    """Alert levels for quack_alert."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# === 🖼️ UI Components === #

def print_banner(title: str, subtitle: str | None = None,
                 mood: str = "happy") -> None:
    """
    Print a stylized banner with title and optional subtitle.

    Args:
        title: The main title text
        subtitle: Optional subtitle text
        mood: The mood emoji to display (happy, wizard, mad, sleepy, surprised)
    """
    if not is_playful_mode():
        console.print(f"[bold]{title}[/bold]")
        if subtitle:
            console.print(f"{subtitle}")
        return

    mood_emoji = {
        "happy": "🦆",
        "wizard": "🧙‍♂️",
        "mad": "😠",
        "sleepy": "😴",
        "surprised": "😲",
        "duckroll": "🎲",
    }.get(mood, "🦆")

    header = f"{mood_emoji} QUACKSTER "
    if mood == "wizard":
        header += "THE WISE 🦆 says..."
    elif mood == "mad":
        header += "THE CRANKY 🦆 grumbles..."
    elif mood == "sleepy":
        header += "THE TIRED 🦆 yawns..."
    elif mood == "surprised":
        header += "THE SHOCKED 🦆 gasps..."
    elif mood == "duckroll":
        header += "THE PLAYFUL 🦆 dances..."
    else:
        header += "THE FRIENDLY 🦆 says..."

    console.print(f"\n{header}\n", style=f"bold {COLOR_PALETTE['primary']}")

    title_lines = [title]
    if subtitle:
        title_lines.append(f"[italic]{subtitle}[/italic]")

    title_text = "\n".join(title_lines)
    width = min(len(title) + 20, console.width - 4)

    # Create a box around the title
    console.print("╔" + "═" * width + "╗", style=COLOR_PALETTE["primary"])

    # Print the title centered in the box
    padding = (width - len(title.strip())) // 2
    console.print(
        "║" + " " * padding + f"[bold]{title.strip()}[/bold]" + " " * (
                    width - padding - len(title.strip())) + "║",
        style=COLOR_PALETTE["primary"]
    )

    # Print subtitle if provided
    if subtitle:
        padding_sub = (width - len(subtitle.strip())) // 2
        console.print(
            "║" + " " * padding_sub + f"{subtitle.strip()}" + " " * (
                        width - padding_sub - len(subtitle.strip())) + "║",
            style=COLOR_PALETTE["primary"]
        )

    console.print("╚" + "═" * width + "╝", style=COLOR_PALETTE["primary"])
    console.print()


def quack_say(message: str, mood: str = "happy") -> None:
    """
    Print a message from Quackster.

    Args:
        message: The message to display
        mood: The mood emoji to use
    """
    if not is_playful_mode():
        console.print(message)
        return

    emojis = {
        "happy": "🦆",
        "wizard": "🧙‍♂️",
        "think": "🤔",
        "joy": "😄",
        "error": "💥",
        "warn": "⚠️",
    }
    icon = emojis.get(mood, "🦆")

    text = Text(f"{icon}💬 Quackster says: ", style=COLOR_PALETTE["info"])
    text.append(message, style="default")
    console.print(text)


def retro_box(title: str, content: str, icon: str = "🎮") -> None:
    """
    Print content in a stylized retro box.

    Args:
        title: Box title
        content: Box content
        icon: Optional icon to display in title
    """
    if not is_playful_mode():
        console.print(f"[bold]{title}[/bold]")
        console.print(content)
        return

    header = f"[bold {COLOR_PALETTE['primary']}]{icon} {title}[/bold {COLOR_PALETTE['primary']}]"
    box = Panel(
        content,
        title=header,
        title_align="left",
        border_style=COLOR_PALETTE["primary"],
    )
    console.print(box)


def quack_alert(message: str, level: str = "info") -> None:
    """
    Display an alert banner.

    Args:
        message: The alert message
        level: Alert level (info, success, warning, error)
    """
    styles = {
        "info": (COLOR_PALETTE["info"], "ℹ️"),
        "success": (COLOR_PALETTE["success"], "✅"),
        "warning": (COLOR_PALETTE["warning"], "⚠️"),
        "error": (COLOR_PALETTE["error"], "❌"),
    }

    style, icon = styles.get(level, styles["info"])

    if not is_playful_mode():
        console.print(f"[bold {style}]{icon} {message}[/bold {style}]")
        return

    width = min(len(message) + 4, console.width - 4)
    padding = (width - len(message) - 2) // 2

    console.print("╔" + "═" * width + "╗", style=style)
    console.print(
        "║" + " " * padding + f"{icon} {message}" + " " * (
                    width - padding - len(message) - 2) + "║",
        style=style
    )
    console.print("╚" + "═" * width + "╝", style=style)


def retro_choice(prompt: str, options: list[str]) -> str:
    """
    Present a RPG-style multiple-choice menu.

    Args:
        prompt: The prompt to display
        options: List of options to choose from

    Returns:
        The selected option
    """
    if not is_playful_mode():
        return Prompt.ask(
            prompt,
            choices=options,
            default=options[0] if options else "",
        )

    # Add emoji prefixes if not already present
    formatted_options = []
    emojis = ["🦆", "📽️", "🤖", "✨", "🧩", "🎲", "🎮", "📊", "🧠", "🔍"]

    for i, option in enumerate(options):
        # If option already starts with emoji, use as is
        if any(option.startswith(emoji) for emoji in emojis):
            formatted_options.append(option)
        else:
            # Otherwise, add an emoji prefix
            emoji = emojis[i % len(emojis)]
            formatted_options.append(f"{emoji} {option}")

    console.print(f"\n[bold]{prompt}[/bold]")

    # Display options
    selected = 0
    key_pressed = None

    # Function to print the menu
    def print_menu() -> None:
        for i, option in enumerate(formatted_options):
            if i == selected:
                console.print(
                    f"  [bold][bright_yellow]▶[/bright_yellow] {option}[/bold]")
            else:
                console.print(f"    {option}")

    # Interactive selection loop
    with Live("", refresh_per_second=10, console=console) as live:
        while key_pressed != "enter":
            live.update("")  # Clear the Live display
            print_menu()

            # Wait for a key press
            key_pressed = typer.prompt("\nUse arrow keys and Enter to select",
                                       default="", show_default=False)

            # Handle arrow keys (in a simple way for demo)
            if key_pressed.lower() in ("up", "k"):
                selected = (selected - 1) % len(formatted_options)
            elif key_pressed.lower() in ("down", "j"):
                selected = (selected + 1) % len(formatted_options)
            elif key_pressed.lower() in ("enter", "\n", ""):
                break

    # Extract the selected option (remove emoji prefix if added)
    selected_option = formatted_options[selected]
    for emoji in emojis:
        if selected_option.startswith(f"{emoji} "):
            selected_option = selected_option[len(emoji) + 1:]
            break

    # Find the original option that matches
    original_option = next(
        (opt for opt in options if opt == selected_option or opt in selected_option),
        options[0])
    return original_option


def get_retro_progress(
        total: int, description: str = "Processing", unit: str = "items"
) -> Progress:
    """
    Create a retro-styled progress bar.

    Args:
        total: Total number of items
        description: Description of the task
        unit: Unit label for the items

    Returns:
        A Progress object that can be used in a context manager
    """
    if not is_playful_mode():
        # Simple progress bar for production mode
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )

    # Fancy progress bar for teaching mode
    return Progress(
        SpinnerColumn("dots", style=COLOR_PALETTE["primary"]),
        TextColumn(
            f"[bold {COLOR_PALETTE['primary']}]{{task.description}}[/bold {COLOR_PALETTE['primary']}]",
            justify="right",
        ),
        BarColumn(
            bar_width=None,
            style=COLOR_PALETTE["primary"],
            complete_style=COLOR_PALETTE["highlight"],
        ),
        TextColumn(f"[{COLOR_PALETTE['highlight']}]{{task.percentage:>3.0f}}%"),
        TextColumn(f"{{task.completed}} of {{task.total}} {unit}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )


def retro_table(headers: list[str], rows: list[list[str]],
                title: str | None = None) -> None:
    """
    Display data in a retro-styled table.

    Args:
        headers: Table headers
        rows: Table rows
        title: Optional table title
    """
    if not is_playful_mode():
        # Simple table for production mode
        table = Table(title=title)
        for header in headers:
            table.add_column(header)
        for row in rows:
            table.add_row(*row)
        console.print(table)
        return

    # Create a fancy retro table
    table = Table(
        title=f"🧾 {title}" if title else None,
        title_style=COLOR_PALETTE["title"],
        border_style=COLOR_PALETTE["border"],
    )

    # Add columns with styling
    for header in headers:
        table.add_column(
            header, style=COLOR_PALETTE["accent"],
            header_style=f"bold {COLOR_PALETTE['primary']}"
        )

    # Add rows
    for row in rows:
        table.add_row(*row)

    console.print(table)


def duck_dance() -> None:
    """Display a fun duck dance animation."""
    if not is_playful_mode():
        return

    # ASCII art frames for duck dance
    frames = [
        """
        (•_•)
        <)   )╯  QUACK
        /    \\
        """,
        """
        (•_•)
        (   (>   QUACK
        /    \\
        """,
        """
        (•_•)>
        \\   )    QUACK
        /    \\
        """,
    ]

    # Dance!
    console.print("\n[bold]Quackster performs a mighty retro duck dance![/bold]")
    for _ in range(3):  # Do the dance 3 times
        for frame in frames:
            console.clear()
            console.print(frame, style=COLOR_PALETTE["highlight"])
            time.sleep(0.3)

    # Final frame
    console.print(
        """
        (•_•)
        <)   )>  QUACK QUACK!
        /    \\
        """,
        style=COLOR_PALETTE["highlight"],
    )
    time.sleep(0.5)
    console.print("\n🎉 Done! Press any key to flap away 🦆✨")

    # Wait for any key press (simplified)
    typer.prompt("", default="", show_default=False)


# === 📊 Helper Functions for Commands === #

def print_success(message: str) -> None:
    """
    Print a success message.

    Args:
        message: The message to display
    """
    if is_playful_mode():
        console.print(
            f"[bold {COLOR_PALETTE['success']}]✅ {message}[/bold {COLOR_PALETTE['success']}]")
    else:
        console.print(f"SUCCESS: {message}")


def print_error(message: str) -> None:
    """
    Print an error message.

    Args:
        message: The message to display
    """
    if is_playful_mode():
        console.print(
            f"[bold {COLOR_PALETTE['error']}]❌ {message}[/bold {COLOR_PALETTE['error']}]")
    else:
        console.print(f"ERROR: {message}")


def print_warning(message: str) -> None:
    """
    Print a warning message.

    Args:
        message: The message to display
    """
    if is_playful_mode():
        console.print(
            f"[bold {COLOR_PALETTE['warning']}]⚠️ {message}[/bold {COLOR_PALETTE['warning']}]")
    else:
        console.print(f"WARNING: {message}")


def print_info(message: str) -> None:
    """
    Print an info message.

    Args:
        message: The message to display
    """
    if is_playful_mode():
        console.print(
            f"[bold {COLOR_PALETTE['info']}]ℹ️ {message}[/bold {COLOR_PALETTE['info']}]")
    else:
        console.print(message)


def print_loading(message: str) -> None:
    """
    Print a loading message.

    Args:
        message: The message to display
    """
    if is_playful_mode():
        console.print(
            f"[bold {COLOR_PALETTE['highlight']}]🕹️ {message}...[/bold {COLOR_PALETTE['highlight']}]")
    else:
        console.print(f"Loading: {message}...")
