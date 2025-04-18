# quackster/src/quackster/npc/rag.py
"""
RAG (Retrieval-Augmented Generation) module for the Quackster quackster NPC.

This module provides functions for loading and retrieving content from
Markdown (and MDX) documents to ground the NPC's knowledge in factual information.
"""

import os
import re
from functools import lru_cache
from typing import Any

from quackcore.fs import service as fs
from quackcore.logging import get_logger

logger = get_logger(__name__)

# Default locations for tutorial content.
DEFAULT_DOC_PATHS = [
    "~/quackverse/tutorials",
    "./tutorials",
    "./docs/tutorials",
]

# Global caches for chunked documents and their modification times
_doc_cache: dict[str, str] = {}
_last_modified_times: dict[str, float] = {}


def get_doc_directories() -> list[str]:
    """
    Get the directories containing tutorial documents.

    This function first checks for a custom override via the QUACK_TUTORIAL_PATH environment variable.
    If not found, it attempts to detect a content context (with content_type "tutorial") using the QuackCore Paths resolver.
    Finally, it falls back to the default paths, expanding user variables via fs.expand_user_vars and verifying existence with fs.get_file_info.

    Returns:
        A list of directory paths (as strings) containing tutorial documents.
    """
    from quackcore.paths import service as paths

    # Check for an override via the environment variable.
    custom_path = os.environ.get("QUACK_TUTORIAL_PATH")
    if custom_path:
        expanded = fs.expand_user_vars(custom_path)
        return [expanded]

    # Attempt to detect a content context for tutorials.
    content_context = paths.detect_content_context(content_type="tutorial")
    if content_context and content_context.content_dir:
        info = fs.get_file_info(content_context.content_dir)
        if info.success and info.exists and info.is_dir:
            return [content_context.content_dir]

    # Fall back to default paths.
    paths: list[str] = []
    for path_str in DEFAULT_DOC_PATHS:
        expanded = fs.expand_user_vars(path_str)
        info = fs.get_file_info(expanded)
        if info.success and info.exists and info.is_dir:
            paths.append(expanded)
    return paths


def should_reload_docs(doc_dirs: list[str]) -> bool:
    """
    Check if documents should be reloaded based on modification times.

    Args:
        doc_dirs: List of document directories (as strings) to check.

    Returns:
        True if any document in these directories has been modified or is new; False otherwise.
    """
    global _last_modified_times

    for doc_dir in doc_dirs:
        files: list[str] = []
        result_md = fs.find_files(doc_dir, "*.md", recursive=True)
        if result_md.success:
            files.extend(result_md.files)
        result_mdx = fs.find_files(doc_dir, "*.mdx", recursive=True)
        if result_mdx.success:
            files.extend(result_mdx.files)

        for file_path in files:
            info = fs.get_file_info(file_path)
            if not info.success:
                continue

            # Check if file is new or modified.
            if (
                file_path not in _last_modified_times
                or info.modified_time > _last_modified_times.get(file_path, 0)
            ):
                return True

    return False


@lru_cache(maxsize=1)
def load_docs_for_rag() -> str:
    """
    Load all tutorial documents for Retrieval-Augmented Generation (RAG).

    This function gathers all Markdown (and MDX) files found in the tutorial directories,
    reads their contents using the FS service, and concatenates them into one string.
    Each file's content is preceded by a header bearing the file name.

    Returns:
        A concatenated string of all document contents, or an empty string if none are found.
    """
    global _doc_cache, _last_modified_times
    doc_dirs = get_doc_directories()

    # If we have cached docs and no files have changed, use the cache.
    if _doc_cache and not should_reload_docs(doc_dirs):
        logger.debug("Using cached documents for RAG")
        return "\n\n".join(_doc_cache.values())

    logger.info("Loading/reloading documents for RAG")
    docs: dict[str, str] = {}
    new_modified_times: dict[str, float] = {}

    if not doc_dirs:
        logger.warning("No tutorial directories found. RAG will be limited.")
        return ""

    for doc_dir in doc_dirs:
        files: list[str] = []
        result_md = fs.find_files(doc_dir, "*.md", recursive=True)
        if result_md.success:
            files.extend(result_md.files)
        result_mdx = fs.find_files(doc_dir, "*.mdx", recursive=True)
        if result_mdx.success:
            files.extend(result_mdx.files)

        for file_path in files:
            try:
                info = fs.get_file_info(file_path)
                if info.success:
                    new_modified_times[file_path] = info.modified_time

                read_result = fs.read_text(file_path)
                if read_result.success:
                    filename = os.path.basename(file_path)
                    content = f"# {filename}\n\n{read_result.content}\n\n"
                    docs[file_path] = content
                else:
                    logger.warning(f"Failed to read {file_path}: {read_result.error}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

    if not docs:
        logger.warning("No tutorial documents found.")
        return ""

    _doc_cache = docs
    _last_modified_times = new_modified_times

    return "\n\n".join(docs.values())


def retrieve_relevant_content(query: str, all_content: str, max_chunks: int = 3) -> str:
    """
    Retrieve content relevant to a query from the full document content.

    The function splits the complete document content into chunks based on Markdown headings,
    scores each chunk by counting keyword occurrences (keywords extracted from the query),
    and returns the top-scoring chunks (up to max_chunks). Each chunk's heading is integrated into the output.

    Args:
        query: The query string to search for.
        all_content: The full content (as a string) from which to retrieve relevant parts.
        max_chunks: The maximum number of chunks to return (default is 3).

    Returns:
        A concatenated string of the selected relevant content chunks.
    """
    chunks = _get_content_chunks(all_content)
    scored_chunks: list[tuple[dict[str, str], int]] = []
    keywords = _extract_keywords(query)

    for chunk in chunks:
        combined_text = (chunk["heading"] + " " if chunk["heading"] else "") + chunk[
            "content"
        ]
        score = sum(
            combined_text.lower().count(keyword.lower()) for keyword in keywords
        )
        if score > 0:
            scored_chunks.append((chunk, score))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, _ in scored_chunks[:max_chunks]]

    result_chunks = []
    for chunk in top_chunks:
        if chunk["heading"]:
            formatted = f"## {chunk['heading']}\n\n{chunk['content']}"
        else:
            formatted = chunk["content"]
        result_chunks.append(formatted)
    return "\n\n".join(result_chunks)


@lru_cache(maxsize=10)
def _get_content_chunks(content: str) -> list[dict[str, str]]:
    """
    Split content into chunks by Markdown headings using headings of level 2 or 3.

    Each chunk is a dictionary with keys:
      - "heading": the text of the heading (or None if absent)
      - "content": the body text following the heading

    Args:
        content: The Markdown content as a string.

    Returns:
        A list of dictionaries, each with "heading" and "content" keys.
    """
    heading_pattern = re.compile(r"^(#{2,3})\s+(.+)", re.MULTILINE)
    matches = list(heading_pattern.finditer(content))
    chunks: list[dict[str, str]] = []

    if not matches:
        return [{"heading": None, "content": content.strip()}]

    if matches[0].start() > 0:
        pre_content = content[: matches[0].start()].strip()
        if pre_content:
            chunks.append({"heading": None, "content": pre_content})

    for i, match in enumerate(matches):
        heading_text = match.group(2).strip()
        start_index = match.start()
        end_index = matches[i + 1].start() if i < len(matches) - 1 else len(content)
        chunk_text = content[start_index:end_index].strip()
        lines = chunk_text.splitlines()
        chunk_body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        chunks.append({"heading": heading_text, "content": chunk_body})
    return chunks


@lru_cache(maxsize=100)
def _extract_keywords(query: str) -> list[str]:
    """
    Extract keywords from the query for improved content matching.

    This function tokenizes the query, removes common stop words, and filters out tokens shorter than three characters.
    Caches results for repeated queries.

    Args:
        query: The query string.

    Returns:
        A list of keywords.
    """
    stop_words = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "about",
        "of",
        "that",
        "and",
        "or",
        "not",
        "but",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "when",
        "where",
        "why",
        "how",
        "this",
        "these",
        "those",
        "it",
        "they",
        "them",
        "their",
        "there",
        "here",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "i",
        "you",
        "he",
        "she",
        "we",
        "my",
        "your",
        "his",
        "her",
        "our",
    }
    tokens = re.findall(r"\b\w+\b", query.lower())
    keywords = [token for token in tokens if token not in stop_words and len(token) > 2]
    return keywords


@lru_cache(maxsize=32)
def get_quest_info(quest_id: str) -> dict[str, Any]:
    """
    Get detailed information about a quest from documentation.

    Args:
        quest_id: The quest ID.

    Returns:
        A dictionary with quest details.
    """
    from quackster import quests

    quest = quests.get_quest(quest_id)
    if not quest:
        return {
            "id": quest_id,
            "name": f"Unknown Quest ({quest_id})",
            "description": "Quest information not found",
            "guidance": "Unable to provide guidance for this quest.",
        }

    guidance = {
        "star-quackcore": (
            "To complete this quest, you'll need to star the QuackCore repository on GitHub.\n\n"
            "1. Go to https://github.com/quackverse/quackcore\n"
            "2. Click the 'Star' button in the top-right corner\n"
            "3. That's it! Your quest progress will be automatically updated."
        ),
        "star-quackverse": (
            "To complete this quest, you'll need to star the QuackVerse organization on GitHub.\n\n"
            "1. Go to https://github.com/quackverse\n"
            "2. Click the 'Star' button in the top-right corner\n"
            "3. That's it! Your quest progress will be automatically updated."
        ),
        "run-tests": (
            "To complete this quest, you'll need to run the DuckTyper CLI.\n\n"
            "1. Install DuckTyper:\n   pip install tests\n"
            "2. Run:\n   tests hello\n"
            "3. The quest will be marked as completed automatically."
        ),
    }

    return {
        "id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge_id": quest.badge_id,
        "guidance": guidance.get(
            quest.id, "Complete this quest to earn XP and progress in your journey!"
        ),
    }


@lru_cache(maxsize=32)
def get_badge_info(badge_id: str) -> dict[str, Any]:
    """
    Get detailed information about a badge from documentation.

    Args:
        badge_id: The badge's ID.

    Returns:
        A dictionary containing badge details.
    """
    from quackster import badges

    badge = badges.get_badge(badge_id)
    if not badge:
        return {
            "id": badge_id,
            "name": f"Unknown Badge ({badge_id})",
            "description": "Badge information not found",
            "guidance": "Unable to provide information for this badge.",
        }

    info = {
        "github-collaborator": {
            "guidance": "This badge is earned by starring the QuackCore repository on GitHub.",
            "fun_fact": "GitHub's star feature was introduced in 2012 as a way to bookmark repositories.",
        },
        "duck-contributor": {
            "guidance": "This badge is earned by opening a Pull Request to a QuackVerse repository.",
            "fun_fact": "The concept of 'pull requests' was popularized by GitHub to facilitate code reviews.",
        },
        "duck-team-player": {
            "guidance": "This badge is earned by having a PR merged into a QuackVerse project.",
            "fun_fact": "The average PR review and merge time in open source projects is about 4-5 days.",
        },
        "duck-initiate": {
            "guidance": "This badge is earned by gaining your first 10 XP in DuckTyper.",
            "fun_fact": "XP was first popularized in role-playing games in the 1970s.",
        },
    }

    badge_info = info.get(
        badge_id,
        {
            "guidance": f"This badge is earned by reaching {badge.required_xp} XP.",
            "fun_fact": "Badges were originally physical emblems worn to show achievement.",
        },
    )

    return {
        "id": badge.id,
        "name": badge.name,
        "description": badge.description,
        "required_xp": badge.required_xp,
        "emoji": badge.emoji,
        "guidance": badge_info.get("guidance", ""),
        "fun_fact": badge_info.get("fun_fact", ""),
    }


@lru_cache(maxsize=16)
def get_tutorial_topic(topic: str) -> dict[str, Any]:
    """
    Get tutorial content for a specific topic.

    Args:
        topic: The topic to search for.

    Returns:
        A dictionary with tutorial information including title, description, and content.
    """
    topics = {
        "tests": {
            "title": "Introduction to DuckTyper",
            "description": "DuckTyper is a CLI tool for the QuackVerse ecosystem.",
            "content": (
                "# DuckTyper Tutorial\n\nDuckTyper is a CLI tool for interacting with QuackVerse components.\n\n"
                "## Installation\n\nInstall DuckTyper using pip:\n\n```\npip install tests\n```\n\n"
                "## Usage\n\nRun:\n```\ntests --help\n```\n"
            ),
        },
        "quests": {
            "title": "Completing Quests with DuckTyper",
            "description": "Learn how to view and complete quests.",
            "content": (
                "# Quests in DuckTyper\n\nQuests are challenges that earn XP and badges.\n\n"
                "## Viewing Quests\n\nUse:\n```\ntests quest list\n```\n\n"
                "## Completing Quests\n\nActions may include starring repositories, opening PRs, etc."
            ),
        },
        "badges": {
            "title": "Understanding Badges",
            "description": "Learn about the badge system in QuackVerse.",
            "content": (
                "# Badges in QuackVerse\n\nBadges showcase achievements.\n\n"
                "## Types of Badges\n\n1. XP-based badges\n2. Quest-based badges\n3. Special badges\n\n"
                "## Viewing Your Badges\n\nUse:\n```\ntests badge list\n```\n"
            ),
        },
        "github": {
            "title": "GitHub Integration with QuackVerse",
            "description": "How QuackVerse connects with GitHub.",
            "content": (
                "# GitHub Integration\n\nQuackVerse integrates with GitHub for seamless collaboration.\n\n"
                "## Key Features\n\n- Starring repositories\n- Opening Pull Requests\n\n"
                "## Setup\n\nConnect your GitHub account with:\n```\ntests github connect\n```\n"
            ),
        },
    }

    lower_topic = topic.lower()
    for key, content in topics.items():
        if key.lower() in lower_topic or lower_topic in key.lower():
            return content

    best_match = None
    best_score = 0
    keywords = _extract_keywords(topic)

    for key, content in topics.items():
        topic_text = f"{key} {content['title']} {content['description']}"
        score = sum(topic_text.lower().count(keyword.lower()) for keyword in keywords)
        if score > best_score:
            best_score = score
            best_match = content

    if best_match and best_score > 0:
        return best_match

    return {
        "title": "Topic Not Found",
        "description": f"No tutorial found for '{topic}'",
        "content": f"I don't have a tutorial on '{topic}' yet. Try asking about DuckTyper, quests, badges, or GitHub integration.",
    }
