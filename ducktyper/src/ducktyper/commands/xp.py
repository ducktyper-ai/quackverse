# ducktyper/src/ducktyper/commands/xp.py
"""
Implementation of the 'xp' command.

The XP command visualizes user experience points and achievements
within the QuackVerse ecosystem.
"""

import json
import random
import sys
from datetime import datetime

import typer
from rich.console import Console

from ducktyper.ui.branding import (
    duck_dance,
    get_retro_progress,
    print_banner,
    print_error,
    print_info,
    print_success,
    quack_alert,
    quack_say,
    retro_box,
    retro_table,
)
from ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.styling import render_progress_bar
from ducktyper.utils import get_cache_dir
from quackcore.cli import CliContext

# Create Typer app for the xp command
app = typer.Typer(
    name="xp",
    help="View your experience points and achievements.",
    add_completion=False,
)

# Create console for rich output
console = Console()


def load_xp_data() -> dict:
    """
    Load XP data from the cache.

    Returns:
        XP data dictionary
    """
    # In a real implementation, this would come from QuackCore or a sync server
    # For now, we'll use a local cache file
    xp_file = get_cache_dir() / "xp.json"

    if not xp_file.exists():
        # Create a demo XP file if none exists
        demo_data = {
            "xp": 750,
            "level": 3,
            "next_level_xp": 1000,
            "tools_used": [
                {"name": "quackmeta", "times_used": 5,
                 "last_used": datetime.now().isoformat()},
                {"name": "quackviz", "times_used": 3,
                 "last_used": datetime.now().isoformat()},
                {"name": "quackgpt", "times_used": 8,
                 "last_used": datetime.now().isoformat()},
            ],
            "achievements": [
                {"name": "First Tool",
                 "description": "Used a QuackTool for the first time", "unlocked": True,
                 "xp": 100},
                {"name": "Tool Master", "description": "Used 3 different QuackTools",
                 "unlocked": True, "xp": 250},
                {"name": "Contributor", "description": "Submitted a Pull Request",
                 "unlocked": False, "xp": 300},
                {"name": "Star Power",
                 "description": "Starred a QuackVerse repo on GitHub", "unlocked": True,
                 "xp": 100},
            ],
            "history": [
                {"action": "Used QuackMeta", "date": (
                    datetime.now().replace(day=datetime.now().day - 5)).isoformat(),
                 "xp": 50},
                {"action": "Unlocked achievement: First Tool", "date": (
                    datetime.now().replace(day=datetime.now().day - 5)).isoformat(),
                 "xp": 100},
                {"action": "Used QuackViz", "date": (
                    datetime.now().replace(day=datetime.now().day - 3)).isoformat(),
                 "xp": 50},
                {"action": "Used QuackGPT", "date": (
                    datetime.now().replace(day=datetime.now().day - 2)).isoformat(),
                 "xp": 50},
                {"action": "Unlocked achievement: Tool Master", "date": (
                    datetime.now().replace(day=datetime.now().day - 2)).isoformat(),
                 "xp": 250},
                {"action": "Starred repo on GitHub", "date": (
                    datetime.now().replace(day=datetime.now().day - 1)).isoformat(),
                 "xp": 100},
                {"action": "Unlocked achievement: Star Power", "date": (
                    datetime.now().replace(day=datetime.now().day - 1)).isoformat(),
                 "xp": 100},
                {"action": "Used QuackGPT", "date": datetime.now().isoformat(),
                 "xp": 50},
            ],
        }

        # Save demo data
        with open(xp_file, "w") as f:
            json.dump(demo_data, f, indent=2)

        return demo_data

    # Load existing data
    try:
        with open(xp_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        print_error(f"Failed to load XP data from {xp_file}")
        return {"xp": 0, "level": 1, "next_level_xp": 100, "tools_used": [],
                "achievements": [], "history": []}


@app.callback(invoke_without_command=True)
def show_xp(
        ctx: typer.Context,
        history: bool = typer.Option(
            False, "--history", "-h", help="Show XP history"
        ),
        achievements: bool = typer.Option(
            False, "--achievements", "-a", help="Show achievements"
        ),
        tools: bool = typer.Option(
            False, "--tools", "-t", help="Show tool usage statistics"
        ),
        all: bool = typer.Option(
            False, "--all", help="Show all XP information"
        ),
) -> None:
    """
    View your experience points and achievements.

    This command displays your progress in the QuackVerse ecosystem,
    including XP earned, level, achievements, and tool usage statistics.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Load XP data
        xp_data = load_xp_data()

        # Calculate total and percentage to next level
        current_xp = xp_data.get("xp", 0)
        current_level = xp_data.get("level", 1)
        next_level_xp = xp_data.get("next_level_xp", 100)
        percentage = min(100, (current_xp / next_level_xp) * 100)

        # Show XP overview
        if is_playful_mode():
            print_banner(f"QuackVerse XP: Level {current_level}", mood="wizard")

            retro_box("Your Progress", f"""
XP: {current_xp} / {next_level_xp} ({percentage:.1f}% to Level {current_level + 1})

{render_progress_bar(current_xp, next_level_xp, width=50)}
""")
        else:
            print_info(f"QuackVerse XP: Level {current_level}")
            print_info(
                f"XP: {current_xp} / {next_level_xp} ({percentage:.1f}% to Level {current_level + 1})")
            print_info(render_progress_bar(current_xp, next_level_xp, width=50))

        # Show tools used
        if tools or all:
            tools_used = xp_data.get("tools_used", [])

            if tools_used:
                if is_playful_mode():
                    retro_box("🧰 Tools Used", "Your magical tool usage stats:")
                else:
                    print_info("\nTools Used:")

                # Prepare table
                headers = ["Tool", "Times Used", "Last Used"]
                rows = []

                for tool in tools_used:
                    # Format date
                    last_used = tool.get("last_used", "")
                    try:
                        if last_used:
                            dt = datetime.fromisoformat(last_used)
                            last_used = dt.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        last_used = "Unknown"

                    rows.append([
                        tool.get("name", "Unknown"),
                        str(tool.get("times_used", 0)),
                        last_used,
                    ])

                # Sort by times used (descending)
                rows.sort(key=lambda x: int(x[1]), reverse=True)

                # Display table
                retro_table(headers, rows)
            else:
                print_info("No tools used yet.")

        # Show achievements
        if achievements or all:
            achievement_list = xp_data.get("achievements", [])

            if achievement_list:
                if is_playful_mode():
                    retro_box("🏆 Achievements", "Your magical accomplishments:")
                else:
                    print_info("\nAchievements:")

                # Prepare table
                headers = ["Achievement", "Description", "Status", "XP"]
                rows = []

                for achievement in achievement_list:
                    # Format status
                    status = "✅ Unlocked" if achievement.get("unlocked",
                                                             False) else "🔒 Locked"

                    rows.append([
                        achievement.get("name", "Unknown"),
                        achievement.get("description", ""),
                        status,
                        str(achievement.get("xp", 0)),
                    ])

                # Display table
                retro_table(headers, rows)
            else:
                print_info("No achievements yet.")

        # Show history
        if history or all:
            history_list = xp_data.get("history", [])

            if history_list:
                if is_playful_mode():
                    retro_box("📜 XP History", "Your magical journey:")
                else:
                    print_info("\nXP History:")

                # Prepare table
                headers = ["Date", "Action", "XP"]
                rows = []

                for entry in history_list:
                    # Format date
                    date = entry.get("date", "")
                    try:
                        if date:
                            dt = datetime.fromisoformat(date)
                            date = dt.strftime("%Y-%m-%d")
                    except (ValueError, TypeError):
                        date = "Unknown"

                    rows.append([
                        date,
                        entry.get("action", "Unknown"),
                        str(entry.get("xp", 0)),
                    ])

                # Sort by date (descending)
                rows.sort(key=lambda x: x[0], reverse=True)

                # Display table
                retro_table(headers, rows)
            else:
                print_info("No XP history yet.")

        # Easter egg dance if user has a lot of XP
        if is_playful_mode() and current_xp >= 500 and random.random() < 0.2:
            quack_say("Wow, you've earned a lot of XP! Time for a victory dance!")
            duck_dance()

    except KeyboardInterrupt:
        print("\nXP view cancelled.")
    except Exception as e:
        print_error(f"Error showing XP: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in xp command")
        sys.exit(1)


@app.command("simulate-gain")
def simulate_xp_gain(
        ctx: typer.Context,
        amount: int = typer.Argument(..., help="Amount of XP to simulate gaining"),
        action: str = typer.Option(
            "Simulated XP gain", "--action", "-a", help="Action description"
        ),
) -> None:
    """
    Simulate gaining XP (for demo purposes only).

    This command simulates gaining XP with a fancy progress animation.
    In a real implementation, XP would be tracked by QuackCore.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Load XP data
        xp_data = load_xp_data()
        current_xp = xp_data.get("xp", 0)

        if is_playful_mode():
            quack_say(f"Gaining {amount} XP for: {action}")

            # Fancy XP gain animation
            with get_retro_progress(amount, "Gaining XP", "XP") as progress:
                task = progress.add_task("Gaining XP", total=amount)

                for i in range(1, amount + 1):
                    # Simulate work
                    import time
                    time.sleep(0.01)

                    # Update progress
                    progress.update(task, advance=1)

            quack_alert(f"+{amount} XP gained!", level="success")
        else:
            print_info(f"Simulating gaining {amount} XP for: {action}")
            print_success(f"+{amount} XP gained!")

        # Update XP data
        xp_data["xp"] = current_xp + amount

        # Check for level up
        next_level_xp = xp_data.get("next_level_xp", 100)
        if xp_data["xp"] >= next_level_xp:
            xp_data["level"] += 1
            xp_data["next_level_xp"] = next_level_xp * 2  # Simple progression

            if is_playful_mode():
                quack_alert(f"🎉 LEVEL UP! You are now Level {xp_data['level']}!",
                            level="success")
                duck_dance()
            else:
                print_success(f"LEVEL UP! You are now Level {xp_data['level']}!")

        # Add to history
        xp_data["history"].append({
            "action": action,
            "date": datetime.now().isoformat(),
            "xp": amount,
        })

        # Save updated XP data
        xp_file = get_cache_dir() / "xp.json"
        with open(xp_file, "w") as f:
            json.dump(xp_data, f, indent=2)

    except KeyboardInterrupt:
        print("\nXP simulation cancelled.")
    except Exception as e:
        print_error(f"Error simulating XP gain: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in xp simulate-gain command")
        sys.exit(1)
