# src/quackcore/paths/context.py
"""
Project context models for path resolution.

This module provides data models for representing project structure context,
which is used for resolving paths in a project.
"""

from pathlib import Path

from pydantic import BaseModel, Field


class ProjectDirectory(BaseModel):
    """
    Represents a project directory structure.

    This model contains information about a specific directory in a project,
    such as a source code directory or an output directory.
    """

    name: str = Field(description="Name of the directory")
    path: Path = Field(description="Absolute path to the directory")
    rel_path: Path | None = Field(
        default=None, description="Relative path from project root"
    )
    is_source: bool = Field(
        default=False, description="Whether this is a source code directory"
    )
    is_output: bool = Field(
        default=False, description="Whether this is an output directory"
    )
    is_data: bool = Field(default=False, description="Whether this is a data directory")
    is_config: bool = Field(
        default=False, description="Whether this is a configuration directory"
    )
    is_test: bool = Field(default=False, description="Whether this is a test directory")
    is_asset: bool = Field(
        default=False, description="Whether this is an asset directory"
    )
    is_temp: bool = Field(
        default=False, description="Whether this is a temporary directory"
    )

    def __str__(self) -> str:
        """String representation of the directory."""
        return str(self.path)


class ProjectContext(BaseModel):
    """
    Represents the context of a project.

    This model contains information about the project structure,
    such as the root directory, source code directories, and output directories.
    """

    root_dir: Path = Field(
        description="Root directory of the project",
    )

    directories: dict[str, ProjectDirectory] = Field(
        default_factory=dict,
        description="Dictionary of project directories by name",
    )

    config_file: Path | None = Field(
        default=None,
        description="Path to the project configuration file",
    )

    name: str | None = Field(
        default=None,
        description="Name of the project",
    )

    def __str__(self) -> str:
        """String representation of the project context."""
        return f"ProjectContext(root={self.root_dir}, dirs={len(self.directories)})"

    def get_source_dir(self) -> Path | None:
        """
        Get the primary source directory.

        Returns:
            Path to the source directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_source:
                return dir_info.path
        return None

    def get_output_dir(self) -> Path | None:
        """
        Get the primary output directory.

        Returns:
            Path to the output directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_output:
                return dir_info.path
        return None

    def get_data_dir(self) -> Path | None:
        """
        Get the primary data directory.

        Returns:
            Path to the data directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_data:
                return dir_info.path
        return None

    def get_config_dir(self) -> Path | None:
        """
        Get the primary configuration directory.

        Returns:
            Path to the configuration directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_config:
                return dir_info.path
        return None

    def get_directory(self, name: str) -> Path | None:
        """
        Get a directory by name.

        Args:
            name: Name of the directory

        Returns:
            Path to the directory or None if not found
        """
        dir_info = self.directories.get(name)
        return dir_info.path if dir_info else None

    def add_directory(
        self,
        name: str,
        path: Path,
        is_source: bool = False,
        is_output: bool = False,
        is_data: bool = False,
        is_config: bool = False,
        is_test: bool = False,
        is_asset: bool = False,
        is_temp: bool = False,
    ) -> None:
        """
        Add a directory to the project context.

        Args:
            name: Name of the directory
            path: Path to the directory
            is_source: Whether this is a source code directory
            is_output: Whether this is an output directory
            is_data: Whether this is a data directory
            is_config: Whether this is a configuration directory
            is_test: Whether this is a test directory
            is_asset: Whether this is an asset directory
            is_temp: Whether this is a temporary directory
        """
        rel_path = (
            path.relative_to(self.root_dir)
            if path.is_relative_to(self.root_dir)
            else None
        )

        self.directories[name] = ProjectDirectory(
            name=name,
            path=path,
            rel_path=rel_path,
            is_source=is_source,
            is_output=is_output,
            is_data=is_data,
            is_config=is_config,
            is_test=is_test,
            is_asset=is_asset,
            is_temp=is_temp,
        )


class ContentContext(ProjectContext):
    """
    Represents the context of a content creation project.

    Extends ProjectContext with content creation specific information.
    """

    content_type: str | None = Field(
        default=None,
        description="Type of content (e.g., 'tutorial', 'video', 'image')",
    )

    content_name: str | None = Field(
        default=None,
        description="Name of the content item",
    )

    content_dir: Path | None = Field(
        default=None,
        description="Path to the content directory",
    )

    def get_assets_dir(self) -> Path | None:
        """
        Get the assets directory.

        Returns:
            Path to the assets directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_asset:
                return dir_info.path
        return None

    def get_temp_dir(self) -> Path | None:
        """
        Get the temporary directory.

        Returns:
            Path to the temporary directory or None if not found
        """
        for dir_info in self.directories.values():
            if dir_info.is_temp:
                return dir_info.path
        return None
