# QuackCore Tests

This directory contains comprehensive tests for the QuackCore library. 
These tests ensure that all components work correctly in isolation and together as a system.

## Running Tests

Tests can be run using the following command from the project root:

```bash
make test
```

This will execute all tests with coverage reporting. To run specific tests, you can use pytest directly:

```bash
python -m pytest tests/test_fs
```

## Test Structure

The tests are organized by module:

- `test_errors/`: Tests for error handling classes and utilities
- `test_fs/`: Tests for filesystem operations
- `test_paths/`: Tests for path resolution
- `test_config/`: Tests for configuration management
- `test_plugins/`: Tests for plugin system
- `test_integration/`: Integration tests for full pipelines

## Creating New Tests

When creating new tests, please follow these guidelines:

1. Use appropriate pytest fixtures from `conftest.py`
2. Test both success and failure cases
3. Follow the pattern of existing tests for similar components
4. Use hypothesis for property-based testing where appropriate
5. Keep tests isolated and avoid side effects

## Mocks and Fixtures

Common testing utilities are provided in `conftest.py`:

- `temp_dir`: Creates a temporary directory for tests
- `test_file`: Creates a test file with content
- `sample_config`: Creates a sample configuration
- `mock_project_structure`: Creates a mock project structure
- `mock_plugin`: Creates a mock plugin for testing

## Coverage Goals

The goal is to maintain at least 90% test coverage for all modules. 
Coverage reports are generated when running tests with `make test`.