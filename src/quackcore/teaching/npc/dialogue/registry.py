# src/quackcore/teaching/npc/dialogue/registry.py
"""
Central registry for Quackster NPC dialogue.

This module provides access to template-based dialogue for the Quackster NPC,
allowing for consistent and easily customizable character responses.
"""

import random
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from quackcore.logging import get_logger
from quackcore.teaching.npc.schema import QuacksterProfile, UserMemory

logger = get_logger(__name__)

# Initialize Jinja2 environment for templates
TEMPLATE_DIR = Path(__file__).parent
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


class DialogueCategory(BaseModel):
    """A category of dialogue entries for the NPC."""

    category: str
    entries: list[str]


def load_yaml(name: str) -> dict[str, Any]:
    """
    Load a YAML file from the dialogue directory.

    Args:
        name: Name of the YAML file (without extension)

    Returns:
        Parsed YAML content as a dictionary
    """
    path = Path(__file__).parent / f"{name}.yaml"
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Dialogue file not found: {path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {path}: {e}")
        return {}


def _render_template(template_name: str, context: dict[str, Any]) -> str:
    """
    Render a Jinja2 template with the provided context.

    Args:
        template_name: Name of the template file
        context: Variables to use in the template

    Returns:
        Rendered template as a string
    """
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {e}")
        return f"[Template Error: {template_name}]"


class DialogueRegistry:
    """
    Registry for NPC dialogue templates and snippets.

    This class provides access to all NPC dialogue, including greetings,
    farewells, catchphrases, and templated content for various interactions.
    """

    # Load dialogue data once on module import
    _greetings = load_yaml("greetings")
    _farewells = load_yaml("farewells")
    _catchphrases = load_yaml("catchphrases")
    _badge_dialogue = load_yaml("badges")
    _quest_dialogue = load_yaml("quests")

    @classmethod
    def get_greeting(cls, memory: UserMemory) -> str:
        """
        Get an appropriate greeting based on user memory.

        Args:
            memory: User memory data

        Returns:
            A greeting string
        """
        greetings = cls._greetings

        # First time greeting
        if memory.conversation_count == 0 and "first_time" in greetings:
            return random.choice(greetings["first_time"])

        # Returning user greetings
        options = []

        # Add general returning greetings
        if "returning" in greetings and "general" in greetings["returning"]:
            options.extend(greetings["returning"]["general"])

        # Add level-specific greetings
        if "returning" in greetings and "level" in greetings["returning"]:
            level_greetings = greetings["returning"]["level"]
            for greeting in level_greetings:
                options.append(greeting.replace("{{ level }}", str(memory.level)))

        # Add badge-specific greetings
        if len(memory.badges) > 0 and "returning" in greetings and "badges" in \
                greetings["returning"]:
            badge_greetings = greetings["returning"]["badges"]
            for greeting in badge_greetings:
                options.append(
                    greeting.replace("{{ badge_count }}", str(len(memory.badges))))

        # Add quest-specific greetings
        if len(memory.completed_quests) > 0 and "returning" in greetings and "quests" in \
                greetings["returning"]:
            quest_greetings = greetings["returning"]["quests"]
            for greeting in quest_greetings:
                options.append(greeting.replace("{{ quest_count }}",
                                                str(len(memory.completed_quests))))

        # If we have options, choose one randomly
        if options:
            return random.choice(options)

        # Fallback to default greeting
        return "Quack! How can I help you today? 🦆"

    @classmethod
    def get_farewell(cls, memory: UserMemory) -> str:
        """
        Get an appropriate farewell based on user memory.

        Args:
            memory: User memory data

        Returns:
            A farewell string
        """
        farewells = cls._farewells

        options = []

        # Add general farewells
        if "general" in farewells:
            options.extend(farewells["general"])

        # Add beginner farewells
        if memory.xp < 100 and "beginner" in farewells:
            options.extend(farewells["beginner"])
        # Add intermediate farewells
        elif memory.xp < 500 and "intermediate" in farewells:
            options.extend(farewells["intermediate"])
        # Add advanced farewells
        elif "advanced" in farewells:
            options.extend(farewells["advanced"])

        # If we have options, choose one randomly
        if options:
            return random.choice(options)

        # Fallback to default farewell
        return "Quack for now! Come back soon! 🦆"

    @classmethod
    def get_catchphrase(cls) -> str:
        """
        Get a random catchphrase.

        Returns:
            A catchphrase string
        """
        if "catchphrases" in cls._catchphrases:
            return random.choice(cls._catchphrases["catchphrases"])
        return "Quacktastic!"

    @classmethod
    def get_badge_dialogue(cls, badge_id: str, key: str = "description") -> str | None:
        """
        Get dialogue for a specific badge.

        Args:
            badge_id: ID of the badge
            key: Type of dialogue to retrieve (description, guidance, fun_fact)

        Returns:
            Badge dialogue string or None if not found
        """
        if badge_id in cls._badge_dialogue and key in cls._badge_dialogue[badge_id]:
            return cls._badge_dialogue[badge_id][key]
        return None

    @classmethod
    def get_quest_dialogue(cls, quest_id: str, key: str = "guidance") -> str | None:
        """
        Get dialogue for a specific quest.

        Args:
            quest_id: ID of the quest
            key: Type of dialogue to retrieve (guidance, hint, completion)

        Returns:
            Quest dialogue string or None if not found
        """
        if quest_id in cls._quest_dialogue and key in cls._quest_dialogue[quest_id]:
            return cls._quest_dialogue[quest_id][key]
        return None

    @classmethod
    def render_system_prompt(cls, profile: QuacksterProfile, memory: UserMemory) -> str:
        """
        Render the system prompt template using profile and memory.

        Args:
            profile: NPC personality profile
            memory: User memory data

        Returns:
            Rendered system prompt
        """
        context = {
            "profile": profile.model_dump(),
            "memory": memory.model_dump(),
        }
        return cls.render_template("system_prompt.md.j2", context)

    @classmethod
    def render_badge_status(cls, badge_data: dict[str, Any]) -> str:
        """
        Render a badge status template.

        Args:
            badge_data: Badge information

        Returns:
            Rendered badge status
        """
        return cls.render_template("badge_status.md.j2", badge_data)

    @classmethod
    def render_quest_intro(cls, quest_data: dict[str, Any]) -> str:
        """
        Render a quest introduction template.

        Args:
            quest_data: Quest information

        Returns:
            Rendered quest introduction
        """
        return cls.render_template("quest_intro.md.j2", quest_data)

    @classmethod
    def render_template(cls, template_name: str, context: dict[str, Any]) -> str:
        """
        Render a Jinja2 template with the provided context.

        Args:
            template_name: Name of the template file
            context: Variables to use in the template

        Returns:
            Rendered template as a string
        """
        return _render_template(template_name, context)

    @classmethod
    def flavor_text(cls, category: str, text: str) -> str:
        """
        Add Quackster flavor to plain text.

        Args:
            category: Category of text (badge, quest, tutorial, etc.)
            text: Plain text to add flavor to

        Returns:
            Text with added Quackster flavor
        """
        # Define category-specific flavor additions
        category_flavors = {
            "badge": [
                "What a shiny achievement! ",
                "Badge collectors unite! ",
                "Your collection grows! ",
                "Display this with pride! "
            ],
            "quest": [
                "Adventure awaits! ",
                "Your quest journey continues! ",
                "A challenge approaches! ",
                "Ready for this mission? "
            ],
            "tutorial": [
                "Learning time! ",
                "Knowledge is power! ",
                "Let me guide you! ",
                "Time to learn something new! "
            ],
            "xp": [
                "Level up progress! ",
                "XP tracker activated! ",
                "Growth metrics incoming! ",
                "Your coding journey stats! "
            ],
            "certificate": [
                "Achievement unlocked! ",
                "Official recognition! ",
                "Your coding credentials! ",
                "Proof of mastery! "
            ]
        }

        # Get category-specific flavors or use generic ones
        if category.lower() in category_flavors:
            if random.random() < 0.5:  # 50% chance to add category flavor
                category_flavor = random.choice(category_flavors[category.lower()])
                text = f"{category_flavor}{text}"

        # Add a quack catchphrase occasionally (20% chance)
        if random.random() < 0.2:
            text = f"{cls.get_catchphrase()} {text}"

        # Add appropriate emoji based on category if no duck emoji
        category_emojis = {
            "badge": "🏆 🦆",
            "quest": "🗺️ 🦆",
            "tutorial": "📚 🦆",
            "xp": "📈 🦆",
            "certificate": "🎓 🦆",
            "completion": "🎉 🦆",
            "error": "❓ 🦆",
        }

        # Add duck emoji if missing, using category-specific styling if available
        if "🦆" not in text:
            emoji_suffix = category_emojis.get(category.lower(), "🦆")
            text = f"{text} {emoji_suffix}"

        return text