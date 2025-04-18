# quackster/src/quackster/npc/schema.py
"""
Schema definitions for the Quackster quackster NPC.

This module defines the core data models for interacting with the quackster NPC,
including input, response, and profile schemas.
"""

from typing import Any

from pydantic import BaseModel, Field


class TeachingNPCInput(BaseModel):
    """
    Input data for a quackster NPC interaction.

    This defines what information the NPC receives for each interaction.
    """

    user_input: str = Field(description="The user's message to the NPC")
    github_username: str | None = Field(
        default=None, description="GitHub username of the user (if available)"
    )
    conversation_id: str | None = Field(
        default=None, description="Unique ID for the conversation thread"
    )
    conversation_context: list[dict[str, str]] | None = Field(
        default=None, description="Previous messages in the conversation"
    )


class TeachingNPCResponse(BaseModel):
    """
    Response data from a quackster NPC interaction.

    This defines what information the NPC returns after each interaction.
    """

    response_text: str = Field(description="The NPC's response message")
    actions_taken: list[str] | None = Field(
        default_factory=list,
        description="List of actions taken by the NPC during processing",
    )
    suggested_quests: list[dict[str, Any]] | None = Field(
        default=None,
        description="Suggested quests that the user might want to complete",
    )
    used_tools: list[dict[str, Any]] | None = Field(
        default=None, description="Tools that were used to generate the response"
    )
    should_verify_quests: bool = Field(
        default=False,
        description="Whether quests should be verified after this interaction",
    )


class QuacksterProfile(BaseModel):
    """
    Profile configuration for the Quackster NPC.

    This defines the personality and characteristics of Quackster.
    """

    name: str = Field(default="Quackster", description="Name of the NPC")
    tone: str = Field(default="friendly", description="Tone of voice for the NPC")
    backstory: str = Field(
        default="A magical duck who guides developers through quests",
        description="Backstory of the NPC",
    )
    expertise: list[str] = Field(
        default=["Python", "CLI tools", "GitHub", "QuackVerse"],
        description="Areas of expertise for the NPC",
    )
    teaching_style: str = Field(
        default="Socratic method with playful quips",
        description="Teaching style of the NPC",
    )
    emoji_style: str = Field(
        default="moderate",
        description="How often to use emojis (sparse, moderate, liberal)",
    )
    catchphrases: list[str] = Field(
        default=[
            "Quacktastic!",
            "Let's code some magic!",
            "Time to spread your wings!",
            "Duck, duck, code!",
        ],
        description="Catchphrases the NPC might use",
    )


class QuestionCategory(BaseModel):
    """
    Category of questions that the NPC can handle.

    This helps the NPC agent categorize user questions.
    """

    name: str = Field(description="Name of the category")
    examples: list[str] = Field(description="Example questions in this category")
    description: str = Field(description="Description of the category")


class UserMemory(BaseModel):
    """
    Memory of the user's progress and interactions.

    This is used to personalize the NPC's responses.
    """

    github_username: str | None = Field(
        default=None, description="GitHub username of the user"
    )
    xp: int = Field(default=0, description="Total XP earned by the user")
    level: int = Field(default=1, description="Current level of the user")
    completed_quests: list[str] = Field(
        default_factory=list, description="IDs of quests the user has completed"
    )
    badges: list[str] = Field(
        default_factory=list, description="IDs of badges the user has earned"
    )
    conversation_count: int = Field(
        default=0, description="Number of conversations with Quackster"
    )
    last_interaction: str | None = Field(
        default=None, description="Timestamp of the last interaction"
    )
    interests: list[str] | None = Field(
        default=None, description="Topics the user has expressed interest in"
    )
    custom_data: dict[str, Any] = Field(
        default_factory=dict, description="Additional custom data about the user"
    )
    user_tags: list[str] = Field(
        default_factory=list,
        description="Tags associated with the user, for tracking topics and interests",
    )
