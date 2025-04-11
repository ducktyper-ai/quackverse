# tests/test_teaching/test_academy/test_init.py
"""
Tests for module initialization and import structure.
"""
import importlib


def test_import_module():
    """Test that the module can be imported."""
    # Should not raise an exception
    import quackcore.teaching.academy


def test_module_exports():
    """Test that all expected entities are exported."""
    from quackcore.teaching.academy import (
        # Core classes
        Assignment, AssignmentStatus, TeachingContext, Student, StudentSubmission,
        SubmissionStatus, Course, CourseModule, ModuleItem, Feedback, FeedbackItem,
        Annotation, GradingCriteria, GradeResult,
        # Result classes
        TeachingResult, AssignmentResult, FeedbackResult,
        # Service
        service
    )

    # Verify these are the expected types
    assert service is not None

    # Core class checks
    from quackcore.teaching.academy.assignment import Assignment as _Assignment
    assert Assignment is _Assignment

    from quackcore.teaching.academy.context import TeachingContext as _TeachingContext
    assert TeachingContext is _TeachingContext

    from quackcore.teaching.academy.student import Student as _Student
    assert Student is _Student

    from quackcore.teaching.academy.course import Course as _Course
    assert Course is _Course


def test_service_singleton():
    """Test that the service export is a singleton."""
    from quackcore.teaching.academy import service as service1
    from quackcore.teaching.academy import service as service2

    assert service1 is service2

    # Also verify it's the same as directly importing
    from quackcore.teaching.academy.service import service as service3
    assert service1 is service3


def test_module_reload():
    """Test that module can be reloaded and maintains integrity."""
    import quackcore.teaching.academy

    # Get reference to service before reload
    from quackcore.teaching.academy import service as service_before

    # Reload the module
    importlib.reload(quackcore.teaching.academy)

    # Get reference to service after reload
    from quackcore.teaching.academy import service as service_after

    # Service should still be the same object (singleton)
    assert service_before is service_after