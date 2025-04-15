# tests/quackster/test_academy/test_course.py
"""
Tests for the Course module.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackster.academy.course import (
    Course,
    CourseManager,
    CourseModule,
    ItemType,
    ModuleItem,
)


class TestModuleItem:
    """Tests for the ModuleItem class."""

    def test_create(self):
        """Test creating a module item."""
        # Basic create
        item = ModuleItem.create(
            title="Test Item", type=ItemType.LECTURE, description="Test description"
        )
        assert item.title == "Test Item"
        assert item.type == ItemType.LECTURE
        assert item.description == "Test description"
        assert item.id is not None
        assert item.published is True

        # Create with optional fields
        due_date_str = "2023-01-01T12:00:00"
        item = ModuleItem.create(
            title="Test Assignment",
            type=ItemType.ASSIGNMENT,
            description="Test assignment",
            url="https://example.com",
            file_path="/path/to/file",
            assignment_id="assignment-1",
            due_date=due_date_str,
            points=100.0,
            published=False,
        )
        assert item.title == "Test Assignment"
        assert item.type == ItemType.ASSIGNMENT
        assert item.description == "Test assignment"
        assert item.url == "https://example.com"
        assert item.file_path == "/path/to/file"
        assert item.assignment_id == "assignment-1"
        assert item.due_date == datetime.fromisoformat(due_date_str)
        assert item.points == 100.0
        assert item.published is False

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        item = ModuleItem(title="Test Item", type=ItemType.LECTURE)
        assert item.id is not None

        # Create with provided ID
        item = ModuleItem(id="custom-id", title="Test Item", type=ItemType.LECTURE)
        assert item.id == "custom-id"


class TestCourseModule:
    """Tests for the CourseModule class."""

    def test_create(self):
        """Test creating a course module."""
        # Basic create
        module = CourseModule.create(
            title="Test Module", description="Test description"
        )
        assert module.title == "Test Module"
        assert module.description == "Test description"
        assert module.id is not None
        assert module.position == 0
        assert module.published is True
        assert module.items == []
        assert module.prerequisites == []
        assert module.start_date is None
        assert module.end_date is None

        # Create with optional fields
        start_date_str = "2023-01-01T00:00:00"
        end_date_str = "2023-01-31T23:59:59"
        items = [ModuleItem.create(title="Test Item", type=ItemType.LECTURE)]
        prerequisites = ["module-1"]

        module = CourseModule.create(
            title="Advanced Module",
            description="Advanced topics",
            position=1,
            published=False,
            items=items,
            prerequisites=prerequisites,
            start_date=start_date_str,
            end_date=end_date_str,
        )
        assert module.title == "Advanced Module"
        assert module.description == "Advanced topics"
        assert module.id is not None
        assert module.position == 1
        assert module.published is False
        assert len(module.items) == 1
        assert module.items[0].title == "Test Item"
        assert module.prerequisites == ["module-1"]
        assert module.start_date == datetime.fromisoformat(start_date_str)
        assert module.end_date == datetime.fromisoformat(end_date_str)

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        module = CourseModule(title="Test Module")
        assert module.id is not None

        # Create with provided ID
        module = CourseModule(id="custom-id", title="Test Module")
        assert module.id == "custom-id"

    def test_add_item(self):
        """Test adding an item to a module."""
        module = CourseModule.create(title="Test Module")
        item = ModuleItem.create(title="Test Item", type=ItemType.LECTURE)

        module.add_item(item)

        assert len(module.items) == 1
        assert module.items[0] == item

    def test_remove_item(self):
        """Test removing an item from a module."""
        module = CourseModule.create(title="Test Module")
        item1 = ModuleItem.create(title="Item 1", type=ItemType.LECTURE)
        item2 = ModuleItem.create(title="Item 2", type=ItemType.LECTURE)

        module.add_item(item1)
        module.add_item(item2)

        # Remove existing item
        result = module.remove_item(item1.id)
        assert result is True
        assert len(module.items) == 1
        assert module.items[0] == item2

        # Remove non-existent item
        result = module.remove_item("non-existent")
        assert result is False
        assert len(module.items) == 1

    def test_get_item(self):
        """Test getting an item by ID."""
        module = CourseModule.create(title="Test Module")
        item1 = ModuleItem.create(title="Item 1", type=ItemType.LECTURE)
        item2 = ModuleItem.create(title="Item 2", type=ItemType.LECTURE)

        module.add_item(item1)
        module.add_item(item2)

        # Get existing item
        result = module.get_item(item1.id)
        assert result == item1

        # Get non-existent item
        result = module.get_item("non-existent")
        assert result is None

    def test_get_published_items(self):
        """Test getting published items."""
        module = CourseModule.create(title="Test Module")
        item1 = ModuleItem.create(title="Item 1", type=ItemType.LECTURE, published=True)
        item2 = ModuleItem.create(
            title="Item 2", type=ItemType.LECTURE, published=False
        )

        module.add_item(item1)
        module.add_item(item2)

        published = module.get_published_items()
        assert len(published) == 1
        assert published[0] == item1

    def test_is_active(self):
        """Test checking if a module is active."""
        now = datetime.now()

        # Published, no dates
        module = CourseModule.create(title="Test Module", published=True)
        assert module.is_active() is True

        # Not published
        module = CourseModule.create(title="Test Module", published=False)
        assert module.is_active() is False

        # Published, with start date in the past
        module = CourseModule.create(
            title="Test Module", published=True, start_date=now - timedelta(days=1)
        )
        assert module.is_active() is True

        # Published, with start date in the future
        module = CourseModule.create(
            title="Test Module", published=True, start_date=now + timedelta(days=1)
        )
        assert module.is_active() is False

        # Published, with end date in the future
        module = CourseModule.create(
            title="Test Module", published=True, end_date=now + timedelta(days=1)
        )
        assert module.is_active() is True

        # Published, with end date in the past
        module = CourseModule.create(
            title="Test Module", published=True, end_date=now - timedelta(days=1)
        )
        assert module.is_active() is False

        # Published, with start date in the past and end date in the future
        module = CourseModule.create(
            title="Test Module",
            published=True,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
        )
        assert module.is_active() is True

        # Published, with start date in the future and end date in the future
        module = CourseModule.create(
            title="Test Module",
            published=True,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=2),
        )
        assert module.is_active() is False

        # Published, with start date in the past and end date in the past
        module = CourseModule.create(
            title="Test Module",
            published=True,
            start_date=now - timedelta(days=2),
            end_date=now - timedelta(days=1),
        )
        assert module.is_active() is False


class TestCourse:
    """Tests for the Course class."""

    def test_create(self):
        """Test creating a course."""
        # Basic create
        course = Course.create(
            name="Test Course", code="TEST101", description="A test course"
        )
        assert course.name == "Test Course"
        assert course.code == "TEST101"
        assert course.description == "A test course"
        assert course.id is not None
        assert course.start_date is None
        assert course.end_date is None
        assert course.modules == []
        assert course.instructors == []
        assert course.syllabus_url is None
        assert course.homepage_content is None

        # Create with optional fields
        start_date_str = "2023-01-01T00:00:00"
        end_date_str = "2023-05-31T23:59:59"
        instructors = ["instructor1", "instructor2"]

        course = Course.create(
            name="Advanced Course",
            code="ADV202",
            description="An advanced course",
            start_date=start_date_str,
            end_date=end_date_str,
            instructors=instructors,
            syllabus_url="https://example.com/syllabus",
            homepage_content="# Welcome to the course",
        )
        assert course.name == "Advanced Course"
        assert course.code == "ADV202"
        assert course.description == "An advanced course"
        assert course.id is not None
        assert course.start_date == datetime.fromisoformat(start_date_str)
        assert course.end_date == datetime.fromisoformat(end_date_str)
        assert course.modules == []
        assert course.instructors == instructors
        assert course.syllabus_url == "https://example.com/syllabus"
        assert course.homepage_content == "# Welcome to the course"

    def test_ensure_id(self):
        """Test that ID is generated if not provided."""
        # Create with no ID
        course = Course(name="Test Course")
        assert course.id is not None

        # Create with provided ID
        course = Course(id="custom-id", name="Test Course")
        assert course.id == "custom-id"

    def test_add_module(self):
        """Test adding a module to a course."""
        course = Course.create(name="Test Course")
        module = CourseModule.create(title="Test Module")

        course.add_module(module)

        assert len(course.modules) == 1
        assert course.modules[0] == module
        assert module.position == 0

    def test_add_multiple_modules(self):
        """Test adding multiple modules to a course and checking position."""
        course = Course.create(name="Test Course")
        module1 = CourseModule.create(title="Module 1")
        module2 = CourseModule.create(title="Module 2")
        module3 = CourseModule.create(title="Module 3")

        course.add_module(module1)
        course.add_module(module2)
        course.add_module(module3)

        assert len(course.modules) == 3
        assert course.modules[0] == module1
        assert course.modules[1] == module2
        assert course.modules[2] == module3
        assert module1.position == 0
        assert module2.position == 1
        assert module3.position == 2

    def test_remove_module(self):
        """Test removing a module from a course."""
        course = Course.create(name="Test Course")
        module1 = CourseModule.create(title="Module 1")
        module2 = CourseModule.create(title="Module 2")

        course.add_module(module1)
        course.add_module(module2)

        # Remove existing module
        result = course.remove_module(module1.id)
        assert result is True
        assert len(course.modules) == 1
        assert course.modules[0] == module2
        assert module2.position == 0  # Position should be updated

        # Remove non-existent module
        result = course.remove_module("non-existent")
        assert result is False
        assert len(course.modules) == 1

    def test_get_module(self):
        """Test getting a module by ID."""
        course = Course.create(name="Test Course")
        module1 = CourseModule.create(title="Module 1")
        module2 = CourseModule.create(title="Module 2")

        course.add_module(module1)
        course.add_module(module2)

        # Get existing module
        result = course.get_module(module1.id)
        assert result == module1

        # Get non-existent module
        result = course.get_module("non-existent")
        assert result is None

    def test_get_published_modules(self):
        """Test getting published modules."""
        course = Course.create(name="Test Course")
        module1 = CourseModule.create(title="Module 1", published=True)
        module2 = CourseModule.create(title="Module 2", published=False)
        module3 = CourseModule.create(title="Module 3", published=True)

        course.add_module(module1)
        course.add_module(module2)
        course.add_module(module3)

        published = course.get_published_modules()
        assert len(published) == 2
        assert published[0] == module1
        assert published[1] == module3

    def test_get_active_modules(self):
        """Test getting active modules."""
        now = datetime.now()
        course = Course.create(name="Test Course")

        # Active module (published, no dates)
        module1 = CourseModule.create(title="Module 1", published=True)

        # Inactive module (not published)
        module2 = CourseModule.create(title="Module 2", published=False)

        # Inactive module (published, future start date)
        module3 = CourseModule.create(
            title="Module 3", published=True, start_date=now + timedelta(days=1)
        )

        # Active module (published, past start date, future end date)
        module4 = CourseModule.create(
            title="Module 4",
            published=True,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
        )

        course.add_module(module1)
        course.add_module(module2)
        course.add_module(module3)
        course.add_module(module4)

        active = course.get_active_modules()
        assert len(active) == 2
        assert active[0] == module1
        assert active[1] == module4

    def test_reorder_modules(self):
        """Test reordering modules."""
        course = Course.create(name="Test Course")
        module1 = CourseModule.create(title="Module 1")
        module2 = CourseModule.create(title="Module 2")
        module3 = CourseModule.create(title="Module 3")

        course.add_module(module1)
        course.add_module(module2)
        course.add_module(module3)

        # Reorder by removing and adding back
        course.modules = [module2, module3, module1]
        course._reorder_modules()

        assert module2.position == 0
        assert module3.position == 1
        assert module1.position == 2


class TestCourseManager:
    """Tests for the CourseManager class."""

    def test_init(self):
        """Test initialization of CourseManager."""
        manager = CourseManager()
        assert manager.courses == {}

    def test_add_course(self):
        """Test adding a course."""
        manager = CourseManager()
        course = Course.create(name="Test Course")

        manager.add_course(course)

        assert len(manager.courses) == 1
        assert manager.courses[course.id] == course

    def test_get_course(self):
        """Test getting a course by ID."""
        manager = CourseManager()
        course = Course.create(name="Test Course")

        manager.add_course(course)

        # Get existing course
        result = manager.get_course(course.id)
        assert result == course

        # Get non-existent course
        result = manager.get_course("non-existent")
        assert result is None

    def test_add_courses(self):
        """Test adding multiple courses."""
        manager = CourseManager()
        course1 = Course.create(name="Course 1")
        course2 = Course.create(name="Course 2")

        manager.add_courses([course1, course2])

        assert len(manager.courses) == 2
        assert manager.courses[course1.id] == course1
        assert manager.courses[course2.id] == course2

    def test_remove_course(self):
        """Test removing a course."""
        manager = CourseManager()
        course1 = Course.create(name="Course 1")
        course2 = Course.create(name="Course 2")

        manager.add_course(course1)
        manager.add_course(course2)

        # Remove existing course
        result = manager.remove_course(course1.id)
        assert result is True
        assert len(manager.courses) == 1
        assert course1.id not in manager.courses
        assert course2.id in manager.courses

        # Remove non-existent course
        result = manager.remove_course("non-existent")
        assert result is False
        assert len(manager.courses) == 1

    def test_get_active_courses(self):
        """Test getting active courses."""
        manager = CourseManager()
        now = datetime.now()

        # Active course (no dates)
        course1 = Course.create(name="Course 1")

        # Active course (past start date, no end date)
        course2 = Course.create(name="Course 2", start_date=now - timedelta(days=10))

        # Active course (past start date, future end date)
        course3 = Course.create(
            name="Course 3",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
        )

        # Inactive course (future start date)
        course4 = Course.create(name="Course 4", start_date=now + timedelta(days=10))

        # Inactive course (past end date)
        course5 = Course.create(name="Course 5", end_date=now - timedelta(days=10))

        manager.add_courses([course1, course2, course3, course4, course5])

        active = manager.get_active_courses()
        assert len(active) == 3
        assert course1 in active
        assert course2 in active
        assert course3 in active
        assert course4 not in active
        assert course5 not in active

    def test_resolve_file_path_absolute(self):
        """Test _resolve_file_path with absolute path."""
        path = "/absolute/path"
        resolved = CourseManager._resolve_file_path(path)
        assert resolved == Path(path)

    def test_resolve_file_path_relative(self, mock_resolver):
        """Test _resolve_file_path with relative path."""
        mock_resolver.get_project_root.return_value = Path("/project/root")

        path = "relative/path"
        resolved = CourseManager._resolve_file_path(path)
        assert resolved == Path("/project/root/relative/path")

    def test_resolve_file_path_relative_no_project_root(self, mock_resolver):
        """Test _resolve_file_path with relative path when project root fails."""
        mock_resolver.get_project_root.side_effect = Exception("Project root not found")

        with patch("pathlib.Path.resolve") as mock_resolve:
            mock_resolve.return_value = Path("/resolved/path")

            path = "relative/path"
            resolved = CourseManager._resolve_file_path(path)
            assert str(resolved).startswith("/resolved/")

    def test_load_from_file(self, mock_fs):
        """Test loading courses from a file."""
        file_path = "/path/to/courses.yaml"

        # Mock read_yaml to return success with courses data
        courses_data = {
            "courses": [
                {
                    "id": "course-1",
                    "name": "Course 1",
                    "code": "C1",
                    "description": "Description 1",
                    "modules": [
                        {
                            "id": "module-1",
                            "title": "Module 1",
                            "description": "Module description",
                            "items": [
                                {"id": "item-1", "title": "Item 1", "type": "LECTURE"}
                            ],
                        }
                    ],
                },
                {"id": "course-2", "name": "Course 2", "code": "C2"},
            ]
        }
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=courses_data)

        # Load from file
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            manager = CourseManager.load_from_file(file_path)

            # Verify courses were loaded
            assert len(manager.courses) == 2
            assert "course-1" in manager.courses
            assert "course-2" in manager.courses

            # Verify course details
            course1 = manager.courses["course-1"]
            assert course1.name == "Course 1"
            assert course1.code == "C1"
            assert len(course1.modules) == 1

            # Verify module details
            module1 = course1.modules[0]
            assert module1.id == "module-1"
            assert module1.title == "Module 1"
            assert len(module1.items) == 1

            # Verify item details
            item1 = module1.items[0]
            assert item1.id == "item-1"
            assert item1.title == "Item 1"
            assert item1.type == ItemType.LECTURE

    def test_load_from_file_file_not_found(self, mock_fs):
        """Test loading courses when file is not found."""
        file_path = "/path/to/courses.yaml"

        # Mock read_yaml to return failure
        mock_fs._read_yaml.return_value = MagicMock(
            success=False, error="File not found"
        )

        # Load from file should raise FileNotFoundError
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            with pytest.raises(FileNotFoundError):
                CourseManager.load_from_file(file_path)

    def test_load_from_file_invalid_format(self, mock_fs):
        """Test loading courses with invalid file format."""
        file_path = "/path/to/courses.yaml"

        # Mock read_yaml to return success with invalid data
        invalid_data = {"not_courses": []}
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=invalid_data)

        # Load from file should raise ValueError
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            with pytest.raises(ValueError):
                CourseManager.load_from_file(file_path)

    def test_load_from_file_course_error(self, mock_fs, mock_logger):
        """Test loading courses with error in course data."""
        file_path = "/path/to/courses.yaml"

        # Mock read_yaml to return success with invalid course data
        courses_data = {
            "courses": [
                {"id": "course-1", "name": "Course 1"},
                {
                    # Missing required name field
                    "id": "course-2"
                },
            ]
        }
        mock_fs._read_yaml.return_value = MagicMock(success=True, data=courses_data)

        # Load from file should still work, but log a warning and skip the invalid course
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            manager = CourseManager.load_from_file(file_path)

            # Verify only valid course was loaded
            assert len(manager.courses) == 1
            assert "course-1" in manager.courses
            assert "course-2" not in manager.courses

            # Verify warning was logged
            mock_logger.warning.assert_called_once()

    def test_save_to_file(self, mock_fs):
        """Test saving courses to a file."""
        file_path = "/path/to/courses.yaml"

        # Create manager with courses
        manager = CourseManager()
        course1 = Course.create(name="Course 1")
        course2 = Course.create(name="Course 2")
        manager.add_courses([course1, course2])

        # Mock write_yaml to return success
        mock_fs._write_yaml.return_value = MagicMock(success=True)

        # Save to file
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            result = manager.save_to_file(file_path)

            # Verify result
            assert result is True

            # Verify write_yaml was called with correct data
            expected_data = {"courses": [course1.model_dump(), course2.model_dump()]}
            mock_fs._write_yaml.assert_called_once_with(file_path, expected_data)

    def test_save_to_file_error(self, mock_fs, mock_logger):
        """Test saving courses when write fails."""
        file_path = "/path/to/courses.yaml"

        # Create manager with courses
        manager = CourseManager()
        course = Course.create(name="Test Course")
        manager.add_course(course)

        # Mock write_yaml to return failure
        mock_fs._write_yaml.return_value = MagicMock(success=False, error="Write error")

        # Save to file
        with patch.object(CourseManager, "_resolve_file_path") as mock_resolve:
            mock_resolve.return_value = Path(file_path)
            result = manager.save_to_file(file_path)

            # Verify result
            assert result is False

            # Verify error was logged
            mock_logger.error.assert_called_once()
