# Testing in the QuackVerse Monorepo

This guide explains how testing is structured in the QuackVerse monorepo and how to effectively run and write tests.

## Directory Structure

In the QuackVerse monorepo, each package has its own test directory:

```
quackverse/
├── quackcore/
│   ├── tests/
│   │   ├── conftest.py            # QuackCore test fixtures
│   │   └── test_*.py              # QuackCore tests
├── ducktyper/
│   ├── tests/
│   │   ├── conftest.py            # DuckTyper test fixtures
│   │   └── test_*.py              # DuckTyper tests
├── quackster/
│   ├── tests/
│   │   ├── conftest.py            # QuackSter test fixtures
│   │   └── test_*.py              # QuackSter tests
└── tests/
    └── integration/
        ├── conftest.py            # Cross-package integration test fixtures
        └── test_*.py              # Integration tests
```

## Test Configuration

Test configuration is specified in the root `pyproject.toml` file:

```toml
[tool.pytest.ini_options]
testpaths = ["quackcore/tests", "ducktyper/tests", "quackster/tests"]
python_files = ["test_*.py"]
filterwarnings = ["error"]
```

## Running Tests

### Running All Tests

```bash
make test
```

This will run all tests in all packages with coverage reporting.

### Running Tests for a Specific Package

```bash
make test-quack-core
make test-ducktyper
make test-quackster
```

### Running Integration Tests

```bash
make test-integration
```

## Test Fixtures

### Shared Fixtures

Core fixtures are defined in `quackcore/tests/conftest.py` and include:

- `temp_dir`: Creates a temporary directory
- `test_file`: Creates a test file with content
- `test_binary_file`: Creates a binary test file
- `sample_config`: Creates a sample configuration
- `mock_env_vars`: Sets up environment variables
- `mock_project_structure`: Creates a mock project directory structure
- `mock_plugin`: Creates a mock plugin

### Package-Specific Fixtures

Each package has its own fixtures defined in its respective `conftest.py`:

- `quackster/tests/conftest.py`: Contains QuackSter-specific fixtures like `patch_quackster_utils`
- `ducktyper/tests/conftest.py`: Contains DuckTyper-specific fixtures

### Integration Test Fixtures

For cross-package integration tests, fixtures are imported and re-exported in `tests/integration/conftest.py`.

## Writing Tests

### Unit Tests

Write unit tests in the appropriate package's tests directory:

```python
# quack-core/tests/test_example.py
def test_example_functionality():
    # Test code here
    assert True
```

### Integration Tests

Write integration tests that span multiple packages in the root-level integration tests:

```python
# tests/integration/test_ducktyper_quack_core.py
def test_ducktyper_uses_quackcore():
    # Test code that uses both packages
    assert True
```

## Best Practices

1. **Package Isolation**: Package-specific tests should only rely on that package's code, using mocks for other packages
2. **Fixture Import**: Import fixtures from other packages only when necessary for integration tests
3. **Coverage Targets**: Aim for high coverage in each package
4. **Test Organization**: Organize tests to mirror the source code structure

## Troubleshooting

If you encounter import errors:
- Ensure all packages are installed in development mode (`make install-all`)
- Verify that `pytest` is finding the right conftest.py files
- Check if you're importing a fixture that doesn't exist in the specified conftest.py

Remember that the monorepo structure requires explicit package imports, so use full import paths.