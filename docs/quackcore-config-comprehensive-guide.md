# QuackCore Configuration Guide

## Overview

The `quackcore.config` module provides a robust configuration management system for QuackCore applications and plugins. It allows you to:

- Load configuration from YAML files
- Override configuration with environment variables
- Validate configuration values using Pydantic models
- Merge configurations from different sources
- Access configuration values in a type-safe manner

This guide will help you understand how to use the configuration system effectively in your QuackTools.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Configuration Models](#configuration-models)
3. [Loading Configuration](#loading-configuration)
4. [Accessing Configuration Values](#accessing-configuration-values)
5. [Environment-specific Configuration](#environment-specific-configuration)
6. [Path Handling](#path-handling)
7. [Custom Configuration](#custom-configuration)
8. [Best Practices](#best-practices)
9. [Common Pitfalls](#common-pitfalls)
10. [API Reference](#api-reference)

## Basic Usage

The simplest way to use QuackCore's configuration system is to import the global `config` instance:

```python
from quackcore.config import config

# Access configuration values
log_level = config.logging.level
base_dir = config.paths.base_dir

# Set up logging based on configuration
config.setup_logging()
```

The global `config` instance is automatically loaded when the `quackcore.config` module is imported, searching for configuration files in standard locations.

## Configuration Models

QuackCore uses Pydantic models for configuration, providing type safety, validation, and default values. The main configuration model is `QuackConfig`, which contains nested models for different aspects of configuration:

- `GeneralConfig`: General settings like project name and environment
- `LoggingConfig`: Logging settings like level and output locations
- `PathsConfig`: File path settings
- `IntegrationsConfig`: Settings for third-party integrations
- `PluginsConfig`: Plugin settings
- `custom`: A dictionary for custom configuration values

### Example: Custom Configuration Model

If you need to extend the configuration with your own settings, you can create a Pydantic model and use it with the `custom` field:

```python
from pydantic import BaseModel, Field
from quackcore.config import config, merge_configs

class MyToolConfig(BaseModel):
    max_threads: int = Field(default=4, description="Maximum number of threads")
    cache_size: int = Field(default=1024, description="Cache size in MB")
    api_url: str = Field(default="https://api.example.com", description="API URL")

# Load your tool's configuration from a YAML file
from quackcore.config.loader import load_yaml_config
tool_config = load_yaml_config("my_tool_config.yaml")

# Merge with the global config
config = merge_configs(config, {"custom": {"my_tool": tool_config}})

# Access your tool's configuration
threads = config.get_custom("my_tool", {}).get("max_threads", 4)
# Or, with proper type checking:
tool_config_dict = config.get_custom("my_tool", {})
my_config = MyToolConfig.model_validate(tool_config_dict)
max_threads = my_config.max_threads
```

## Loading Configuration

QuackCore provides several ways to load configuration:

### Default Loading

By default, the global `config` instance is loaded from:

1. Environment variable `QUACK_CONFIG` (if set)
2. Standard locations (`./quack_config.yaml`, `./config/quack_config.yaml`, `~/.quack/config.yaml`, `/etc/quack/config.yaml`)
3. Project root (using heuristics to find `quack_config.yaml` or `config/quack_config.yaml`)

```python
from quackcore.config import config
# config is already loaded and ready to use
```

### Custom Loading

You can load configuration from a specific file:

```python
from quackcore.config import load_config

# Load from a specific file
my_config = load_config("/path/to/my/config.yaml")

# Load without environment variables
my_config = load_config("/path/to/my/config.yaml", merge_env=False)

# Load without default values
my_config = load_config("/path/to/my/config.yaml", merge_defaults=False)
```

### Environment Variables

QuackCore automatically loads configuration from environment variables with the prefix `QUACK_`. The format is:

```
QUACK_SECTION__KEY=value
```

For example:

```
QUACK_LOGGING__LEVEL=DEBUG
QUACK_PATHS__BASE_DIR=/app/data
QUACK_GENERAL__DEBUG=true
```

These will override the corresponding values in the configuration files.

## Accessing Configuration Values

There are several ways to access configuration values:

### Direct Access

```python
from quackcore.config import config

# Access values directly
log_level = config.logging.level
base_dir = config.paths.base_dir
project_name = config.general.project_name
```

### Dictionary Access

```python
# Convert to dictionary
config_dict = config.to_dict()

# Access nested values
log_level = config_dict["logging"]["level"]
```

### Path-based Access

```python
from quackcore.config.utils import get_config_value

# Access by path
log_level = get_config_value(config, "logging.level")

# With default value
api_key = get_config_value(config, "integrations.notion.api_key", "default-key")
```

### Custom Configuration

```python
# Access custom configuration
my_tool_config = config.get_custom("my_tool", {})

# With default value
cache_size = config.get_custom("my_tool.cache_size", 1024)
```

## Environment-specific Configuration

QuackCore supports environment-specific configuration through the `QUACK_ENV` environment variable and environment-specific YAML files:

```python
from quackcore.config.utils import load_env_config

# Load environment-specific configuration
# If QUACK_ENV=production, this will look for production.yaml in the config directory
config = load_env_config(config, "/path/to/config/dir")
```

Example directory structure:
```
/config
  ├── development.yaml  # Loaded when QUACK_ENV=development (default)
  ├── production.yaml   # Loaded when QUACK_ENV=production
  └── test.yaml         # Loaded when QUACK_ENV=test
```

## Path Handling

QuackCore provides utilities for working with paths in configuration:

```python
from quackcore.config.utils import normalize_paths

# Normalize all paths in the configuration (convert relative paths to absolute)
config = normalize_paths(config)

# Access normalized paths
base_dir = config.paths.base_dir
output_dir = config.paths.output_dir  # Now an absolute path based on base_dir
```

## Custom Configuration

The `custom` field in `QuackConfig` allows you to add your own configuration values:

```python
from quackcore.config import config, merge_configs

# Add custom configuration
custom_config = {
    "custom": {
        "my_tool": {
            "max_threads": 8,
            "cache_size": 2048,
            "api_url": "https://api.example.com/v2"
        }
    }
}

# Merge with existing configuration
config = merge_configs(config, custom_config)

# Access custom configuration
max_threads = config.get_custom("my_tool.max_threads", 4)
```

## Best Practices

### 1. Use Pydantic Models for Type Safety

Create Pydantic models for your tool's configuration to get type checking, validation, and default values:

```python
from pydantic import BaseModel, Field

class MyToolConfig(BaseModel):
    max_threads: int = Field(default=4, ge=1, le=16, description="Maximum number of threads")
    cache_size: int = Field(default=1024, ge=0, description="Cache size in MB")
    api_url: str = Field(default="https://api.example.com", description="API URL")
    
    @property
    def cache_size_bytes(self) -> int:
        """Convert cache size to bytes."""
        return self.cache_size * 1024 * 1024
```

### 2. Validate Required Configuration

Use `validate_required_config` to ensure all required configuration values are present:

```python
from quackcore.config.utils import validate_required_config

required_keys = [
    "integrations.notion.api_key",
    "paths.data_dir",
    "custom.my_tool.api_url"
]

missing = validate_required_config(config, required_keys)
if missing:
    raise ValueError(f"Missing required configuration: {', '.join(missing)}")
```

### 3. Use Environment Variables for Secrets

Don't store sensitive information like API keys in configuration files. Use environment variables instead:

```
QUACK_INTEGRATIONS__NOTION__API_KEY=secret-api-key
```

### 4. Provide Good Defaults

Always provide sensible default values for your configuration to make it easier for users:

```python
class MyToolConfig(BaseModel):
    # Good defaults make your tool easier to use
    max_threads: int = Field(default=min(4, os.cpu_count() or 1), description="Maximum number of threads")
    cache_size: int = Field(default=1024, description="Cache size in MB")
    timeout: float = Field(default=30.0, description="Timeout in seconds")
```

### 5. Document Your Configuration

Use the `description` field in Pydantic models to document your configuration:

```python
class MyToolConfig(BaseModel):
    max_threads: int = Field(
        default=4,
        description="Maximum number of threads. Higher values may improve performance "
                    "but will use more system resources."
    )
```

## Common Pitfalls

### 1. Modifying the Global Config

The global `config` instance is shared across your application. If you modify it, those changes will affect all parts of your application that use it:

```python
# BAD: Modifying the global config directly
from quackcore.config import config
config.logging.level = "DEBUG"  # This affects the whole application!

# GOOD: Create a local copy before modifying
from quackcore.config import config, merge_configs
my_config = merge_configs(config, {"logging": {"level": "DEBUG"}})
```

### 2. Assuming Configuration Files Exist

Don't assume that configuration files always exist:

```python
# BAD: Assumes the file exists
config_dict = load_yaml_config("my_config.yaml")

# GOOD: Handle the case where the file doesn't exist
try:
    config_dict = load_yaml_config("my_config.yaml")
except QuackConfigurationError:
    config_dict = {}  # Use default empty dictionary
```

### 3. Not Normalizing Paths

Always normalize paths to ensure they work correctly:

```python
# BAD: Using relative paths directly
data_file = f"{config.paths.data_dir}/my_data.csv"

# GOOD: Normalize paths first
from quackcore.config.utils import normalize_paths
config = normalize_paths(config)
data_file = config.paths.data_dir / "my_data.csv"  # Now a Path object that works correctly
```

### 4. Hard-coding Configuration Paths

Don't hard-code paths to configuration files:

```python
# BAD: Hard-coded path
config = load_config("/etc/quack/config.yaml")

# GOOD: Use the standard loading mechanism
from quackcore.config import config  # Uses the standard search paths

# Or if you need a specific file:
config_path = os.environ.get("MY_TOOL_CONFIG", "my_tool_config.yaml")
config = load_config(config_path)
```

### 5. Not Validating Configuration

Always validate your configuration to catch errors early:

```python
# BAD: Assuming configuration is valid
api_key = config.get_custom("my_tool.api_key")
# If api_key is None or invalid, this might cause problems later

# GOOD: Validate configuration upfront
from quackcore.config.utils import validate_required_config
missing = validate_required_config(config, ["custom.my_tool.api_key"])
if missing:
    raise ValueError(f"Missing required configuration: {', '.join(missing)}")
```

## API Reference

### Models

- `QuackConfig`: Main configuration model
  - `general`: General settings (`GeneralConfig`)
  - `paths`: Path settings (`PathsConfig`)
  - `logging`: Logging settings (`LoggingConfig`)
  - `integrations`: Integration settings (`IntegrationsConfig`)
  - `plugins`: Plugin settings (`PluginsConfig`)
  - `custom`: Custom settings (`dict`)

- `GeneralConfig`: General settings
  - `project_name`: Name of the project
  - `environment`: Environment (development, test, production)
  - `debug`: Debug mode
  - `verbose`: Verbose output

- `LoggingConfig`: Logging settings
  - `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `file`: Log file path
  - `console`: Log to console
  - `setup_logging()`: Set up logging based on configuration

- `PathsConfig`: Path settings
  - `base_dir`: Base directory
  - `output_dir`: Output directory
  - `assets_dir`: Assets directory
  - `data_dir`: Data directory
  - `temp_dir`: Temporary directory

- `IntegrationsConfig`: Integration settings
  - `google`: Google integration settings (`GoogleConfig`)
  - `notion`: Notion integration settings (`NotionConfig`)

- `GoogleConfig`: Google integration settings
  - `client_secrets_file`: Path to client secrets file
  - `credentials_file`: Path to credentials file
  - `shared_folder_id`: Google Drive shared folder ID
  - `gmail_labels`: Gmail labels to filter
  - `gmail_days_back`: Number of days back for Gmail queries

- `NotionConfig`: Notion integration settings
  - `api_key`: Notion API key
  - `database_ids`: Mapping of database names to IDs

- `PluginsConfig`: Plugin settings
  - `enabled`: List of enabled plugins
  - `disabled`: List of disabled plugins
  - `paths`: Additional plugin search paths

### Functions

- `load_config(config_path=None, merge_env=True, merge_defaults=True)`: Load configuration from a file
- `merge_configs(base, override)`: Merge a base configuration with override values
- `get_env()`: Get the current environment
- `load_env_config(config, config_dir=None)`: Load environment-specific configuration
- `get_config_value(config, path, default=None)`: Get a configuration value by path
- `validate_required_config(config, required_keys)`: Validate that the configuration contains all required keys
- `normalize_paths(config)`: Normalize all paths in the configuration

### Global Instances

- `config`: Global configuration instance, loaded automatically when the module is imported