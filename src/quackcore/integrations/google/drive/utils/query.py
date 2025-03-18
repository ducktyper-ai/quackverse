# src/quackcore/integrations/google/drive/utils/query.py
"""
Query utilities for Google Drive integration.

This module provides functions for building query strings for
Google Drive API requests.
"""


def build_query(folder_id: str | None = None, pattern: str | None = None) -> str:
    """
    Build a query string for listing files in Google Drive.

    Args:
        folder_id: Optional folder ID to list files from.
        pattern: Optional filename pattern to filter results.

    Returns:
        str: The query string.
    """
    query_parts: list[str] = []

    # Filter by parent folder
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")

    # Exclude trashed files
    query_parts.append("trashed = false")

    # Filter by name pattern
    if pattern:
        if "*" in pattern:
            name_pattern = pattern.replace("*", "")
            if name_pattern:
                query_parts.append(f"name contains '{name_pattern}'")
        else:
            query_parts.append(f"name = '{pattern}'")

    return " and ".join(query_parts)


def build_file_fields(include_permissions: bool = False) -> str:
    """
    Build a fields parameter string for file requests.

    Args:
        include_permissions: Whether to include permission details.

    Returns:
        str: The fields parameter string.
    """
    fields = [
        "id",
        "name",
        "mimeType",
        "webViewLink",
        "webContentLink",
        "size",
        "createdTime",
        "modifiedTime",
        "parents",
        "shared",
        "trashed",
    ]

    if include_permissions:
        fields.append("permissions(id,type,role,emailAddress,domain)")

    return f"files({', '.join(fields)})"
