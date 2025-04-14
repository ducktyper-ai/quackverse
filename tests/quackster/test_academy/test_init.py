# tests/quackster/test_academy/test_init.py
"""
Tests for module initialization and import structure.
"""

import importlib


def test_import_module():
    """Test that the module can be imported."""
    # Should not raise an exception
    import quackster.academy


def test_module_exports():
    """Test that all expected entities are exported."""
    from quackster.academy import (  # Core classes; Result classes; Service
        Annotation,
        Assignment,
        AssignmentResult,
        AssignmentStatus,
        Course,
        CourseModule,
        Feedback,
        FeedbackItem,
        FeedbackResult,
        GradeResult,
        GradingCriteria,
        ModuleItem,
        Student,
        StudentSubmission,
        SubmissionStatus,
        TeachingContext,
        TeachingResult,
        service,
    )

    # Verify these are the expected types
    assert service is not None

    # Core class checks
    from quackster.academy.assignment import Assignment as _Assignment

    assert Assignment is _Assignment

    from quackster.academy.context import TeachingContext as _TeachingContext

    assert TeachingContext is _TeachingContext

    from quackster.academy.student import Student as _Student

    assert Student is _Student

    from quackster.academy.course import Course as _Course

    assert Course is _Course


def test_service_singleton():
    """Test that the service export is a singleton."""
    from quackster.academy import service as service1
    from quackster.academy import service as service2

    assert service1 is service2

    # Also verify it's the same as directly importing
    from quackster.academy.service import service as service3

    assert service1 is service3


def test_module_reload():
    """Test that module can be reloaded and maintains integrity."""
    import quackster.academy

    # Get reference to service before reload
    from quackster.academy import service as service_before

    # Reload the module
    importlib.reload(quackster.academy)

    # Get reference to service after reload
    from quackster.academy import service as service_after

    # Service should still be the same object (singleton)
    assert service_before is service_after
