# quackster/src/quackster/academy/course.py
"""
Course management module.

This module provides classes for managing course structure, modules,
and content items.
"""

import os
import uuid
from collections.abc import Sequence
from datetime import datetime
from enum import Enum, auto

from pydantic import BaseModel, Field, model_validator

# Use QuackCore FS for file _operations.
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Use QuackCore Paths for project root discovery.
from quackcore.paths import service as paths

logger = get_logger(__name__)


class ItemType(Enum):
    """Type of course item."""

    LECTURE = auto()
    ASSIGNMENT = auto()
    QUIZ = auto()
    RESOURCE = auto()
    DISCUSSION = auto()
    LINK = auto()
    FILE = auto()
    OTHER = auto()


class ModuleItem(BaseModel):
    """An individual item within a course module."""

    id: str = Field(description="Unique identifier for the item")
    title: str = Field(description="Title of the item")
    type: ItemType = Field(description="Type of item")
    description: str | None = Field(default=None, description="Description of the item")
    url: str | None = Field(default=None, description="URL of the item (if external)")
    file_path: str | None = Field(
        default=None, description="Path to the file (if local)"
    )
    assignment_id: str | None = Field(
        default=None, description="ID of the associated assignment (if applicable)"
    )
    due_date: datetime | None = Field(
        default=None, description="Due date (if applicable)"
    )
    points: float | None = Field(
        default=None, description="Points possible (if applicable)"
    )
    published: bool = Field(default=True, description="Whether the item is published")
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the item"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "ModuleItem":
        """Ensure the item ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        title: str,
        type: ItemType,
        description: str | None = None,
        url: str | None = None,
        file_path: str | None = None,
        assignment_id: str | None = None,
        due_date: datetime | str | None = None,
        points: float | None = None,
        published: bool = True,
    ) -> "ModuleItem":
        """
        Create a new module item.

        Args:
            title: Title of the item.
            type: Type of item.
            description: Optional description.
            url: Optional URL for external items.
            file_path: Optional file path for local items.
            assignment_id: Optional ID of the associated assignment.
            due_date: Optional due date (datetime or ISO format string).
            points: Optional points possible.
            published: Whether the item is published.

        Returns:
            New module item instance.
        """
        parsed_due_date = None
        if due_date is not None:
            parsed_due_date = (
                datetime.fromisoformat(due_date)
                if isinstance(due_date, str)
                else due_date
            )

        return cls(
            id=str(uuid.uuid4()),
            title=title,
            type=type,
            description=description,
            url=url,
            file_path=file_path,
            assignment_id=assignment_id,
            due_date=parsed_due_date,
            points=points,
            published=published,
        )


class CourseModule(BaseModel):
    """A module within a course."""

    id: str = Field(description="Unique identifier for the module")
    title: str = Field(description="Title of the module")
    description: str | None = Field(
        default=None, description="Description of the module"
    )
    position: int = Field(default=0, description="Position of the module in the course")
    published: bool = Field(default=True, description="Whether the module is published")
    items: list[ModuleItem] = Field(
        default_factory=list, description="Items within the module"
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="IDs of modules that are prerequisites"
    )
    start_date: datetime | None = Field(
        default=None, description="Date when the module becomes available"
    )
    end_date: datetime | None = Field(
        default=None, description="Date when the module is no longer available"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "CourseModule":
        """Ensure the module ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        title: str,
        description: str | None = None,
        position: int = 0,
        published: bool = True,
        items: list[ModuleItem] | None = None,
        prerequisites: list[str] | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
    ) -> "CourseModule":
        """
        Create a new course module.

        Args:
            title: Title of the module.
            description: Optional description.
            position: Position of the module in the course.
            published: Whether the module is published.
            items: Optional list of module items.
            prerequisites: Optional list of prerequisite module IDs.
            start_date: Optional start date (datetime or ISO format string).
            end_date: Optional end date (datetime or ISO format string).

        Returns:
            New course module instance.
        """
        parsed_start_date = (
            datetime.fromisoformat(start_date)
            if isinstance(start_date, str)
            else start_date
        )
        parsed_end_date = (
            datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        )

        return cls(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            position=position,
            published=published,
            items=items or [],
            prerequisites=prerequisites or [],
            start_date=parsed_start_date,
            end_date=parsed_end_date,
        )

    def add_item(self, item: ModuleItem) -> None:
        """
        Add an item to the module.

        Args:
            item: Item to add.
        """
        self.items.append(item)

    def remove_item(self, item_id: str) -> bool:
        """
        Remove an item from the module.

        Args:
            item_id: ID of the item to remove.

        Returns:
            True if the item was removed, False if not found.
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                self.items.pop(i)
                return True
        return False

    def get_item(self, item_id: str) -> ModuleItem | None:
        """
        Get an item by ID.

        Args:
            item_id: ID of the item to get.

        Returns:
            Item if found, None otherwise.
        """
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def get_published_items(self) -> list[ModuleItem]:
        """
        Get all published items in the module.

        Returns:
            List of published items.
        """
        return [item for item in self.items if item.published]

    def is_active(self) -> bool:
        """
        Check if the module is currently active.

        A module is active if it's published and within its start and end dates.

        Returns:
            True if the module is active, False otherwise.
        """
        if not self.published:
            return False

        now = datetime.now()
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class Course(BaseModel):
    """A course with modules and other metadata."""

    id: str = Field(description="Unique identifier for the course")
    name: str = Field(description="Name of the course")
    code: str | None = Field(default=None, description="Course code (e.g., CS101)")
    description: str | None = Field(
        default=None, description="Description of the course"
    )
    start_date: datetime | None = Field(
        default=None, description="Start date of the course"
    )
    end_date: datetime | None = Field(
        default=None, description="End date of the course"
    )
    modules: list[CourseModule] = Field(
        default_factory=list, description="Modules in the course"
    )
    instructors: list[str] = Field(
        default_factory=list, description="IDs or names of course instructors"
    )
    syllabus_url: str | None = Field(
        default=None, description="URL to the course syllabus"
    )
    homepage_content: str | None = Field(
        default=None, description="Content for the course homepage"
    )
    metadata: dict = Field(
        default_factory=dict, description="Additional metadata about the course"
    )

    @model_validator(mode="after")
    def ensure_id(self) -> "Course":
        """Ensure the course ID is set, generating one if needed."""
        if not self.id:
            self.id = str(uuid.uuid4())
        return self

    @classmethod
    def create(
        cls,
        name: str,
        code: str | None = None,
        description: str | None = None,
        start_date: datetime | str | None = None,
        end_date: datetime | str | None = None,
        instructors: list[str] | None = None,
        syllabus_url: str | None = None,
        homepage_content: str | None = None,
    ) -> "Course":
        """
        Create a new course.

        Args:
            name: Name of the course.
            code: Optional course code.
            description: Optional description.
            start_date: Optional start date (datetime or ISO format string).
            end_date: Optional end date (datetime or ISO format string).
            instructors: Optional list of instructor IDs or names.
            syllabus_url: Optional URL to the course syllabus.
            homepage_content: Optional content for the course homepage.

        Returns:
            New course instance.
        """
        parsed_start_date = (
            datetime.fromisoformat(start_date)
            if isinstance(start_date, str)
            else start_date
        )
        parsed_end_date = (
            datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        )

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            code=code,
            description=description,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            instructors=instructors or [],
            syllabus_url=syllabus_url,
            homepage_content=homepage_content,
        )

    def add_module(self, module: CourseModule) -> None:
        """
        Add a module to the course.

        Args:
            module: Module to add.
        """
        self.modules.append(module)
        self._reorder_modules()

    def remove_module(self, module_id: str) -> bool:
        """
        Remove a module from the course.

        Args:
            module_id: ID of the module to remove.

        Returns:
            True if the module was removed, False if not found.
        """
        for i, module in enumerate(self.modules):
            if module.id == module_id:
                self.modules.pop(i)
                self._reorder_modules()
                return True
        return False

    def get_module(self, module_id: str) -> CourseModule | None:
        """
        Get a module by ID.

        Args:
            module_id: ID of the module to get.

        Returns:
            Module if found, None otherwise.
        """
        for module in self.modules:
            if module.id == module_id:
                return module
        return None

    def get_published_modules(self) -> list[CourseModule]:
        """
        Get all published modules in the course.

        Returns:
            List of published modules.
        """
        return [module for module in self.modules if module.published]

    def get_active_modules(self) -> list[CourseModule]:
        """
        Get all active modules in the course.

        Returns:
            List of active modules.
        """
        return [module for module in self.modules if module.is_active()]

    def _reorder_modules(self) -> None:
        """Update module positions based on their order in the list."""
        for i, module in enumerate(self.modules):
            module.position = i


class CourseManager:
    """
    Manage a collection of courses.

    This class provides functionality for loading, saving, and managing
    courses.
    """

    def __init__(self) -> None:
        """Initialize an empty course manager."""
        self.courses: dict[str, Course] = {}

    def add_course(self, course: Course) -> None:
        """
        Add a course to the manager.

        Args:
            course: Course to add.
        """
        self.courses[course.id] = course

    def get_course(self, course_id: str) -> Course | None:
        """
        Get a course by ID.

        Args:
            course_id: ID of the course to get.

        Returns:
            Course if found, None otherwise.
        """
        return self.courses.get(course_id)

    def add_courses(self, courses: Sequence[Course]) -> None:
        """
        Add multiple courses to the manager.

        Args:
            courses: Sequence of courses to add.
        """
        for course in courses:
            self.add_course(course)

    def remove_course(self, course_id: str) -> bool:
        """
        Remove a course from the manager.

        Args:
            course_id: ID of the course to remove.

        Returns:
            True if the course was removed, False if not found.
        """
        if course_id in self.courses:
            del self.courses[course_id]
            return True
        return False

    def get_active_courses(self) -> list[Course]:
        """
        Get all active courses.

        A course is considered active if the current date is between its start and end dates.

        Returns:
            List of active courses.
        """
        now = datetime.now()
        active_courses = []
        for course in self.courses.values():
            if (course.start_date is None or now >= course.start_date) and (
                course.end_date is None or now <= course.end_date
            ):
                active_courses.append(course)
        return active_courses

    @staticmethod
    def _resolve_file_path(file_path: str) -> str:
        """
        Resolve a file path to an absolute path.

        If the given file_path is relative, attempt to resolve it relative to the project root
        using the QuackCore Paths resolver; if that fails, resolve relative to the current working directory.

        Args:
            file_path: The path to resolve.

        Returns:
            An absolute path as a string.
        """
        if os.path.isabs(file_path):
            return file_path
        try:
            project_root = paths.set_project_root()
            return fs.join_path(project_root, file_path)
        except FileNotFoundError as err:
            logger.warning(
                f"Project root not found: {err}. Falling back to current working directory."
            )
            return os.path.abspath(file_path)

    @classmethod
    def load_from_file(cls, file_path: str) -> "CourseManager":
        """
        Load courses from a file.

        Args:
            file_path: Path to the file to load from.

        Returns:
            Loaded CourseManager instance.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is invalid.
        """
        resolved_path = cls._resolve_file_path(file_path)
        result = fs.read_yaml(resolved_path)
        if not result.success:
            raise FileNotFoundError(
                f"Could not read courses from {resolved_path}: {result.error}"
            )

        data = result.data
        if not isinstance(data, dict) or "courses" not in data:
            raise ValueError(f"Invalid courses format in {resolved_path}")

        manager = cls()
        for course_data in data["courses"]:
            try:
                modules = []
                for module_data in course_data.pop("modules", []):
                    items = []
                    for item_data in module_data.pop("items", []):
                        item = ModuleItem.model_validate(item_data)
                        items.append(item)
                    module = CourseModule.model_validate(
                        {**module_data, "items": items}
                    )
                    modules.append(module)
                course = Course.model_validate({**course_data, "modules": modules})
                manager.add_course(course)
            except Exception as e:
                logger.warning(f"Error loading course: {e}")

        logger.info(f"Loaded {len(manager.courses)} courses from {resolved_path}")
        return manager

    def save_to_file(self, file_path: str) -> bool:
        """
        Save courses to a file.

        Args:
            file_path: Path to save to.

        Returns:
            True if saved successfully, False otherwise.
        """
        resolved_path = self._resolve_file_path(file_path)
        data = {"courses": [course.model_dump() for course in self.courses.values()]}
        result = fs.write_yaml(resolved_path, data)
        if not result.success:
            logger.error(f"Error saving courses to {resolved_path}: {result.error}")
            return False

        logger.info(f"Saved {len(self.courses)} courses to {resolved_path}")
        return True
