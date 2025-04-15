# QuackCore FS Module Documentation

## Introduction

The `quackcore.fs` module provides a robust and developer-friendly filesystem abstraction with standardized result objects, proper error handling, and comprehensive file operation capabilities. It is designed to be a complete replacement for Python's built-in `pathlib.Path`, `os`, and `shutil` modules when building QuackTools within the QuackVerse ecosystem.

This documentation will guide you through the features, usage patterns, and best practices for effectively leveraging the power of `quackcore.fs` in your QuackTools.

## Table of Contents

- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
  - [Result Objects](#result-objects)
  - [Error Handling](#error-handling)
- [Basic File Operations](#basic-file-operations)
  - [Reading Files](#reading-files)
  - [Writing Files](#writing-files)
  - [Deleting Files](#deleting-files)
- [Path Management](#path-management)
  - [Path Manipulation](#path-manipulation)
  - [Path Validation](#path-validation)
  - [Path Comparison](#path-comparison)
- [Directory Operations](#directory-operations)
  - [Creating Directories](#creating-directories)
  - [Listing Directory Contents](#listing-directory-contents)
  - [Finding Files](#finding-files)
- [Advanced File Operations](#advanced-file-operations)
  - [Structured Data (YAML, JSON)](#structured-data-yaml-json)
  - [File Copying and Moving](#file-copying-and-moving)
  - [Atomic Operations](#atomic-operations)
  - [File Information](#file-information)
  - [Checksums](#checksums)
  - [Temporary Files and Directories](#temporary-files-and-directories)
- [Integration with QuackCore](#integration-with-quackcore)
- [Comparison with Standard Library](#comparison-with-standard-library)
  - [pathlib.Path vs quackcore.fs](#pathlibpath-vs-quackcoref)
  - [What quackcore.fs Can Do That pathlib.Path Can't](#what-quackcoref-can-do-that-pathlibpath-cant)
- [Best Practices](#best-practices)
- [Common Pitfalls](#common-pitfalls)
- [API Reference](#api-reference)

## Getting Started

### Installation

QuackCore FS is part of the QuackCore package. If you've installed QuackCore, you already have access to the FS module.

### Basic Usage

The quickest way to start using the `quackcore.fs` module is through the global service instance:

```python
from quackcore.fs import service as fs

# Read a text file
result = fs.read_text("config.txt")
if result.success:
    print(result.content)
else:
    print(f"Error: {result.error}")

# Write a text file
fs.write_text("output.txt", "Hello, QuackVerse!")

# Create a directory
fs.create_directory("data", exist_ok=True)
```

## Core Concepts

### Result Objects

One of the key features of the `quackcore.fs` module is its consistent use of result objects for all operations. Unlike standard library functions that might raise exceptions or return different types of results, every `quackcore.fs` function returns a standardized result object that makes error handling straightforward and consistent.

All result objects inherit from the base `OperationResult` class and include:

- `success`: A boolean indicating whether the operation succeeded
- `path`: The path that was operated on
- `message`: Additional information about the operation (when successful)
- `error`: Error message (when unsuccessful)

Specific operation types have their own result classes with additional attributes:

- `ReadResult`: For file reading operations, includes `content` and possibly `encoding`
- `WriteResult`: For file writing operations, includes `bytes_written` and possibly `checksum`
- `FileInfoResult`: For file information operations, includes details like `exists`, `is_file`, `size`, etc.
- `DirectoryInfoResult`: For directory listing operations, includes `files`, `directories`, etc.
- `FindResult`: For file finding operations, includes `files`, `directories`, and `total_matches`
- `DataResult`: For structured data operations, includes parsed `data` and `format`

Example of working with a result object:

```python
result = fs.read_text("config.txt")
if result.success:
    # Access result attributes
    content = result.content
    print(f"Successfully read {len(content)} characters from {result.path}")
else:
    # Handle the error
    print(f"Failed to read file: {result.error}")
```

### Error Handling

The `quackcore.fs` module provides two layers of error handling:

1. **Result Objects**: All operations return result objects with `success` and `error` attributes for expected errors
2. **Exceptions**: For unexpected errors, the module may still raise exceptions

This dual approach allows you to handle common file operation errors (like file not found or permission denied) through the result objects, while still being able to catch unexpected errors with traditional exception handling.

```python
try:
    result = fs.read_text("config.txt")
    if not result.success:
        # Handle expected error through result object
        print(f"Could not read file: {result.error}")
    else:
        # Process the content
        process_content(result.content)
except Exception as e:
    # Handle unexpected errors
    print(f"Unexpected error: {str(e)}")
```

The module defines several custom exception types for different error scenarios:

- `QuackIOError`: Base class for IO-related errors
- `QuackFileNotFoundError`: When a file doesn't exist
- `QuackFileExistsError`: When a file already exists and that's a problem
- `QuackPermissionError`: When permission is denied for an operation
- `QuackFormatError`: When there's an issue with file format (e.g., invalid JSON)
- `QuackValidationError`: When data validation fails

## Basic File Operations

### Reading Files

The `quackcore.fs` module provides several methods for reading files:

**Reading Text Files**:

```python
# Read a text file
result = fs.read_text("document.txt")
if result.success:
    content = result.content
    print(content)

# Read with specific encoding
result = fs.read_text("international.txt", encoding="utf-16")
if result.success:
    content = result.content
    print(content)

# Read lines from a file
result = fs.read_lines("data.csv")
if result.success:
    lines = result.content  # List of lines
    for line in lines:
        process_line(line)
```

**Reading Binary Files**:

```python
# Read binary data
result = fs.read_binary("image.png")
if result.success:
    binary_data = result.content  # bytes object
    process_binary(binary_data)
```

**Getting Text from Binary Result**:

```python
result = fs.read_binary("potentially_text.bin")
if result.success:
    try:
        # Try to get content as text (will raise exception if not possible)
        text = result.text
        print(f"File is text: {text}")
    except UnicodeDecodeError:
        print("File is binary, not text")
```

### Writing Files

Writing files is just as straightforward:

**Writing Text Files**:

```python
# Write a text file
result = fs.write_text("output.txt", "Hello, QuackVerse!")
if result.success:
    print(f"Successfully wrote {result.bytes_written} bytes")

# Write with specific encoding
result = fs.write_text("international.txt", "こんにちは世界", encoding="utf-8")

# Write lines to a file
lines = ["Header", "Data1,Value1", "Data2,Value2"]
result = fs.write_lines("data.csv", lines)
if result.success:
    print(f"Successfully wrote {len(lines)} lines")

# Write lines with custom line ending
result = fs.write_lines("windows.txt", lines, line_ending="\r\n")
```

**Writing Binary Files**:

```python
# Write binary data
with open("original.png", "rb") as f:
    binary_data = f.read()
result = fs.write_binary("copy.png", binary_data)
if result.success:
    print(f"Successfully wrote {result.bytes_written} bytes")
```

**Atomic Writing**:

The `write_text` and `write_binary` methods support atomic writing to prevent data corruption:

```python
# Atomic write (default for most operations)
result = fs.write_text("important.txt", "Critical data", atomic=True)
```

### Deleting Files

Deleting files and directories is handled by the `delete` method:

```python
# Delete a file
result = fs.delete("temp.txt")
if result.success:
    print(f"Successfully deleted {result.path}")

# Delete only if exists (default behavior)
result = fs.delete("may_not_exist.txt", missing_ok=True)

# Require file to exist (will report error if missing)
result = fs.delete("must_exist.txt", missing_ok=False)
if not result.success:
    print(f"Error: {result.error}")

# Delete a directory and all its contents
result = fs.delete("temp_dir")
if result.success:
    print(f"Successfully deleted directory {result.path}")
```

## Path Management

### Path Manipulation

The `quackcore.fs` module provides utilities for manipulating paths that work consistently across platforms:

**Joining Paths**:

```python
# Join path components
path = fs._join_path("data", "users", "profiles")
print(path)  # data/users/profiles (or data\users\profiles on Windows)

# Join with Path objects
from pathlib import Path

base_dir = Path("project")
config_path = fs._join_path(base_dir, "config", "settings.yaml")
```

**Splitting Paths**:

```python
# Split a path into components
components = fs._split_path("/home/user/projects/quacktool")
print(components)  # ['/', 'home', 'user', 'projects', 'quacktool']
```

**Normalizing Paths**:

```python
# Normalize a path (resolve .. and . components)
path = fs._normalize_path("projects/../data/./files")
print(path)  # /path/to/current/directory/data/files
```

**Expanding User and Environment Variables**:

```python
# Expand ~ to home directory
home_config = fs._expand_user_vars("~/config")
print(home_config)  # /home/user/config

# Expand environment variables
env_path = fs._expand_user_vars("$HOME/projects")
print(env_path)  # /home/user/projects
```

**Getting File Extensions**:

```python
# Get file extension
ext = fs._get_extension("document.txt")
print(ext)  # txt

# For dotfiles
ext = fs._get_extension(".gitignore")
print(ext)  # gitignore
```

### Path Validation

The module provides utilities for validating paths:

```python
# Check if a path has valid syntax
is_valid = fs.is_valid_path("/valid/path")
print(is_valid)  # True

is_valid = fs.is_valid_path("invalid\\:path")
print(is_valid)  # False on most platforms

# Get detailed path information
path_info = fs.get_path_info("~/projects")
if path_info.success:
    print(f"Path: {path_info.path}")
    print(f"Is absolute: {path_info.is_absolute}")
    print(f"Is valid: {path_info.is_valid}")
    print(f"Exists: {path_info.exists}")
```

### Path Comparison

The module provides methods for comparing paths:

```python
# Check if two paths refer to the same file
same_file = fs._is_same_file("document.txt", "./document.txt")
print(same_file)  # True

# Check if a path is a subdirectory of another
is_subdir = fs._is_subdirectory("projects/quacktool", "projects")
print(is_subdir)  # True

is_subdir = fs._is_subdirectory("projects", "projects")
print(is_subdir)  # False (a directory is not a subdirectory of itself)
```

## Directory Operations

### Creating Directories

The module provides utilities for creating directories:

```python
# Create a directory
result = fs.create_directory("data")
if result.success:
    print(f"Created directory: {result.path}")

# Create if it doesn't exist, ignore if it does
result = fs.create_directory("logs", exist_ok=True)

# Create parent directories automatically
result = fs.create_directory("projects/quacktool/data/cache", exist_ok=True)
```

The `ensure_directory` function is a lower-level utility that works similarly:

```python
# Ensure a directory exists
path = fs._ensure_directory("backups")
print(f"Ensured directory exists: {path}")
```

### Listing Directory Contents

The module provides a powerful directory listing function:

```python
# List directory contents
result = fs.list_directory("data")
if result.success:
    print(f"Files: {len(result.files)}")
    for file in result.files:
        print(f"  {file.name}")
    
    print(f"Directories: {len(result.directories)}")
    for directory in result.directories:
        print(f"  {directory.name}")
    
    print(f"Total size: {result.total_size} bytes")

# List only matching files
result = fs.list_directory("logs", pattern="*.log")
if result.success:
    for log_file in result.files:
        process_log_file(log_file)

# Include hidden files
result = fs.list_directory("config", include_hidden=True)
if result.success:
    for file in result.files:
        if file.name.startswith('.'):
            print(f"Hidden file: {file}")
```

### Finding Files

The module provides utilities for finding files:

```python
# Find files matching a pattern
result = fs.find_files("src", "*.py")
if result.success:
    print(f"Found {result.total_matches} Python files:")
    for file in result.files:
        print(f"  {file}")

# Find files recursively
result = fs.find_files("project", "*.json", recursive=True)
if result.success:
    print(f"Found {len(result.files)} JSON files")

# Find files and include hidden ones
result = fs.find_files(".", ".*rc", include_hidden=True)
if result.success:
    print(f"Found {len(result.files)} rc files:")
    for file in result.files:
        print(f"  {file}")
```

For even more advanced searching, you can search by content:

```python
# Find files containing specific text
files = fs._find_files_by_content("src", "TODO:", recursive=True)
print(f"Found {len(files)} files with TODOs:")
for file in files:
  print(f"  {file}")
```

## Advanced File Operations

### Structured Data (YAML, JSON)

The module provides specialized methods for working with structured data formats:

**YAML Operations**:

```python
# Read and parse YAML
result = fs.read_yaml("config.yaml")
if result.success:
    config = result.data  # Already parsed as Python dict
    print(f"App name: {config.get('app_name')}")
    print(f"Version: {config.get('version')}")

# Write YAML
data = {
    "app_name": "QuackTool",
    "version": "1.0.0",
    "settings": {
        "debug": True,
        "log_level": "INFO"
    }
}
result = fs.write_yaml("config.yaml", data)
if result.success:
    print(f"Successfully wrote YAML to {result.path}")
```

**JSON Operations**:

```python
# Read and parse JSON
result = fs.read_json("data.json")
if result.success:
    json_data = result.data  # Already parsed as Python dict
    print(f"User: {json_data.get('user')}")
    print(f"ID: {json_data.get('id')}")

# Write JSON
data = {
    "user": "quacker",
    "id": 12345,
    "roles": ["admin", "developer"]
}
result = fs.write_json("user.json", data, indent=4)
if result.success:
    print(f"Successfully wrote JSON to {result.path}")
```

### File Copying and Moving

The module provides safe methods for copying and moving files:

```python
# Copy a file
result = fs.copy("original.txt", "backup.txt")
if result.success:
    print(f"Copied {result.original_path} to {result.path}")

# Copy and overwrite if destination exists
result = fs.copy("config.yaml", "config.yaml.backup", overwrite=True)

# Copy a directory and all its contents
result = fs.copy("templates", "templates.backup")
if result.success:
    print(f"Copied directory {result.original_path} to {result.path}")

# Move a file
result = fs.move("old_location.txt", "new_location.txt")
if result.success:
    print(f"Moved {result.original_path} to {result.path}")

# Move a directory
result = fs.move("old_dir", "new_dir", overwrite=True)
if result.success:
    print(f"Moved directory {result.original_path} to {result.path}")
```

### Atomic Operations

The module supports atomic operations for several methods, ensuring that files are written safely even if the process is interrupted:

```python
# Atomic write (write to temp file then rename)
result = fs.write_text("important.txt", "Critical data", atomic=True)

# Atomic write for YAML
result = fs.write_yaml("config.yaml", config_data, atomic=True)

# Atomic write for JSON
result = fs.write_json("data.json", json_data, atomic=True)

# Direct atomic write utility
path = fs._atomic_write("output.txt", "Content to write safely")
print(f"Wrote data atomically to {path}")
```

### File Information

The module provides methods for getting detailed information about files:

```python
# Get file information
result = fs.get_file_info("document.txt")
if result.success:
    print(f"Exists: {result.exists}")
    if result.exists:
        print(f"Is file: {result.is_file}")
        print(f"Is directory: {result.is_dir}")
        print(f"Size: {result.size} bytes")
        print(f"Modified: {result.modified}")
        print(f"Created: {result.created}")
        print(f"MIME type: {result.mime_type}")
```

Additional file information utilities:

```python
# Get human-readable file size
size_str = fs._get_file_size_str(1048576)
print(size_str)  # 1.00 MB

# Get file type
file_type = fs._get_file_type("document.txt")
print(file_type)  # text

file_type = fs._get_file_type("image.png")
print(file_type)  # binary

# Get MIME type
mime_type = fs._get_mime_type("document.pdf")
print(mime_type)  # application/pdf

# Get file timestamp
timestamp = fs._get_file_timestamp("document.txt")
print(timestamp)  # 1618047521.0

# Check if a file is locked
is_locked = fs._is_file_locked("database.sqlite")
print(is_locked)  # True/False

# Check if a path is writeable
is_writeable = fs._is_path_writeable("data")
print(is_writeable)  # True/False
```

### Checksums

The module provides utilities for computing file checksums:

```python
# Compute file checksum (SHA-256 by default)
checksum = fs._compute_checksum("important.dat")
print(f"SHA-256: {checksum}")

# Use a different algorithm
md5_checksum = fs._compute_checksum("document.txt", algorithm="md5")
print(f"MD5: {md5_checksum}")

# Compute checksum during write operation
result = fs.write_text("document.txt", "Content", calculate_checksum=True)
if result.success:
  print(f"Checksum: {result.checksum}")
```

### Temporary Files and Directories

The module provides utilities for working with temporary files and directories:

```python
# Create a temporary file
temp_file = fs._create_temp_file()
print(f"Created temp file: {temp_file}")

# Create a temporary file with specific prefix and suffix
temp_log = fs._create_temp_file(prefix="debug_", suffix=".log")
print(f"Created temp log: {temp_log}")

# Create a temporary file in a specific directory
temp_config = fs._create_temp_file(directory="config", suffix=".yaml")
print(f"Created temp config: {temp_config}")

# Create a temporary directory
temp_dir = fs._create_temp_directory()
print(f"Created temp directory: {temp_dir}")

# Create a temporary directory with specific prefix
temp_cache = fs._create_temp_directory(prefix="cache_")
print(f"Created temp cache directory: {temp_cache}")
```

### Disk Usage

The module provides utilities for checking disk usage:

```python
# Get disk usage information
usage = fs._get_disk_usage(".")
print(f"Total space: {fs._get_file_size_str(usage['total'])}")
print(f"Used space: {fs._get_file_size_str(usage['used'])}")
print(f"Free space: {fs._get_file_size_str(usage['free'])}")
```

## Integration with QuackCore

The `quackcore.fs` module is designed to integrate seamlessly with the broader QuackCore ecosystem:

### Using the FileSystemService

The `service` instance used throughout these examples is actually an instance of `FileSystemService`, which you can create custom instances of if needed:

```python
from quackcore.fs import FileSystemService

# Create a service with a specific base directory
fs_service = FileSystemService(base_dir="/specific/path")

# Use the service instance
result = fs_service.read_text("relative/path.txt")  # /specific/path/relative/path.txt
```

### Using as a Plugin

The `quackcore.fs` module can be used as a plugin in the QuackCore ecosystem:

```python
from quackcore.fs.plugin import create_plugin

# Create a filesystem plugin instance
fs_plugin = create_plugin()

# Use the plugin
result = fs_plugin.read_text("config.txt")
if result.success:
    print(result.content)
```

## Comparison with Standard Library

### pathlib.Path vs quackcore.fs

Here's how common `pathlib.Path` operations compare to their `quackcore.fs` equivalents:

| Operation | pathlib.Path | quackcore.fs |
|-----------|--------------|--------------|
| Reading a text file | `content = Path("file.txt").read_text()` | `result = fs.read_text("file.txt")` <br> `content = result.content if result.success else None` |
| Writing a text file | `Path("file.txt").write_text("content")` | `result = fs.write_text("file.txt", "content")` |
| Check if a file exists | `Path("file.txt").exists()` | `result = fs.get_file_info("file.txt")` <br> `exists = result.exists if result.success else False` |
| Create a directory | `Path("dir").mkdir(parents=True, exist_ok=True)` | `fs.create_directory("dir", exist_ok=True)` |
| Get file size | `size = Path("file.txt").stat().st_size` | `result = fs.get_file_info("file.txt")` <br> `size = result.size if result.success else None` |
| Join paths | `path = Path("dir") / "subdir" / "file.txt"` | `path = fs.join_path("dir", "subdir", "file.txt")` |
| List directory | `files = list(Path("dir").glob("*.txt"))` | `result = fs.list_directory("dir", pattern="*.txt")` <br> `files = result.files if result.success else []` |
| Rename/move a file | `Path("old.txt").rename("new.txt")` | `result = fs.move("old.txt", "new.txt")` |
| Copy a file | *Not built-in, requires shutil* | `result = fs.copy("src.txt", "dst.txt")` |
| Delete a file | `Path("file.txt").unlink(missing_ok=True)` | `result = fs.delete("file.txt", missing_ok=True)` |
| Resolve path | `path = Path("../dir").resolve()` | `path = fs.normalize_path("../dir")` |

### What quackcore.fs Can Do That pathlib.Path Can't

The `quackcore.fs` module provides many features that aren't available in `pathlib.Path`:

1. **Consistent Result Objects**: Every operation returns a standardized result object with success/error information
2. **Structured Data Handling**: Built-in support for reading and writing YAML and JSON
3. **Advanced Directory Operations**: More powerful directory listing and file finding
4. **Atomic Operations**: Built-in support for atomic file writes
5. **File Safety**: Methods like `is_file_locked` and `is_path_writeable`
6. **Checksum Computation**: Easy computation of file checksums
7. **File Type Detection**: Utilities for determining file types and MIME types
8. **Proper Error Handling**: Detailed error messages and exception handling
9. **Human-Readable File Sizes**: Conversion of byte counts to human-readable strings
10. **Disk Usage Information**: Easy access to disk space information
11. **Safe Operations**: Methods like `safe_copy`, `safe_move`, and `safe_delete` with better error handling
12. **Content Searching**: Finding files by their content
13. **Validation**: Path validation and information gathering

## Best Practices

### 1. Always Check Result Objects

```python
# Good - checks for success before using the content
result = fs.read_text("config.yaml")
if result.success:
    config_data = result.content
    # Do something with config_data
else:
    logger.error(f"Failed to read config file: {result.error}")
```

### 2. Use Type-Specific Operations

```python
# Good - uses type-specific method
yaml_result = fs.read_yaml("config.yaml")
if yaml_result.success:
    config = yaml_result.data  # Already parsed as a dictionary
```

### 3. Handle Paths Consistently

```python
# Good - works with both string and Path objects
from pathlib import Path
config_dir = Path("config")
fs.create_directory(config_dir)
```

### 4. Ensure Parent Directories Exist

```python
# Good - ensures directory exists first
fs.create_directory("logs/2023/01/01", exist_ok=True)
fs.write_text("logs/2023/01/01/app.log", log_content)
```

### 5. Use Atomic Operations for Critical Data

```python
# Good - uses atomic write for safety
fs.write_text("important_data.txt", data, atomic=True)
```

### 6. Leverage Result Objects for Error Handling

```python
# Good - uses result objects for expected errors
result = fs.read_text("config.yaml")
if not result.success:
    if "not found" in result.error:
        # Handle file not found
        create_default_config()
    elif "permission denied" in result.error:
        # Handle permission error
        request_permission_elevation()
    else:
        # Handle other errors
        log_unexpected_error(result.error)
```

## Common Pitfalls

### 1. Ignoring Result Objects

```python
# Bad - assumes success and ignores error handling
content = fs.read_text("config.yaml").content  # Might raise AttributeError if not successful

# Good - checks the result
result = fs.read_text("config.yaml")
if result.success:
    content = result.content
else:
    # Handle the error
    log_error(result.error)
```

### 2. Bypassing the Module

```python
# Bad - bypasses the fs module
import os
if not os.path.exists("data"):
    os.makedirs("data")

# Good - uses the fs module
fs.create_directory("data", exist_ok=True)
```

### 3. Mixing Path Styles

```python
# Bad - mixes different path styles
base_dir = "/projects/myapp"
config_file = base_dir + "/config.yaml"  # String concatenation

# Good - consistent path handling
config_file = fs._join_path(base_dir, "config.yaml")
```

### 4. Not Creating Parent Directories

```python
# Bad - assumes directory exists
fs.write_text("logs/2023/01/01/app.log", log_content)  # Might fail if directory doesn't exist

# Good - ensures directory exists first
fs.create_directory("logs/2023/01/01", exist_ok=True)
fs.write_text("logs/2023/01/01/app.log", log_content)
```

## API Reference

For a complete list of available functions and classes, refer to the module's `__all__` list:

```python
__all__ = [
    # Main classes
    "FileSystemService",
    "create_service",
    "service",
    # Standalone functions
    "create_directory",
    "get_file_info",
    "read_yaml",
    "read_text",
    "write_text",
    "read_binary",
    "write_binary",
    "write_yaml",
    "read_json",
    "write_json",
    "read_lines",
    "write_lines",
    "list_directory",
    "find_files",
    "copy",
    "move",
    "delete",
    "normalize_path",
    "normalize_path_with_info",
    "get_path_info",
    "is_valid_path",
    # Utility functions
    "is_same_file",
    "is_subdirectory",
    "get_file_size_str",
    "get_unique_filename",
    "create_temp_directory",
    "create_temp_file",
    "get_file_timestamp",
    "is_path_writeable",
    "get_mime_type",
    "get_disk_usage",
    "is_file_locked",
    "get_file_type",
    "find_files_by_content",
    "split_path",
    "join_path",
    "expand_user_vars",
    "get_extension",
    "ensure_directory",
    "compute_checksum",
    "atomic_write",
    # Result classes for type hints
    "OperationResult",
    "ReadResult",
    "WriteResult",
    "FileInfoResult",
    "DirectoryInfoResult",
    "FindResult",
    "DataResult",
    "PathInfo",
    # Type variables
    "T",
]
```

## Real-World Examples

Let's look at some real-world examples of how `quackcore.fs` can be used in QuackTools development.

### Example 1: Config File Management

A common task in applications is managing configuration files. Here's how you might implement that with `quackcore.fs`:

```python
from quackcore.fs import service as fs
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
  def __init__(self, config_dir="config"):
    # Ensure the config directory exists
    result = fs.create_directory(config_dir, exist_ok=True)
    if not result.success:
      logger.error(f"Failed to create config directory: {result.error}")
      raise RuntimeError(f"Failed to initialize config directory: {result.error}")

    self.config_dir = result.path
    self.configs = {}

  def load_config(self, name):
    """Load a configuration file by name."""
    config_path = fs._join_path(self.config_dir, f"{name}.yaml")

    # Check if the config file exists
    file_info = fs.get_file_info(config_path)
    if not file_info.exists:
      logger.warning(f"Config file {name}.yaml not found, creating default")
      return self._create_default_config(name)

    # Read the config
    result = fs.read_yaml(config_path)
    if not result.success:
      logger.error(f"Failed to read config {name}: {result.error}")
      return None

    logger.info(f"Successfully loaded config {name}")
    self.configs[name] = result.data
    return result.data

  def save_config(self, name, config_data):
    """Save a configuration file."""
    config_path = fs._join_path(self.config_dir, f"{name}.yaml")

    # Write the config atomically
    result = fs.write_yaml(config_path, config_data, atomic=True)
    if not result.success:
      logger.error(f"Failed to save config {name}: {result.error}")
      return False

    logger.info(f"Successfully saved config {name}")
    return True

  def _create_default_config(self, name):
    """Create a default configuration file."""
    default_config = {
      "app_name": "QuackTool",
      "version": "1.0.0",
      "created_at": "2023-01-01",
      "settings": {
        "debug": False,
        "log_level": "INFO"
      }
    }

    if self.save_config(name, default_config):
      self.configs[name] = default_config
      return default_config
    return None
```

### Example 2: Log Rotation Tool

Here's an example of a log rotation tool that uses `quackcore.fs` to manage log files:

```python
from quackcore.fs import service as fs
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LogRotator:
  def __init__(self, log_dir="logs", max_size_mb=10, max_logs=5):
    # Create log directory if it doesn't exist
    result = fs.create_directory(log_dir, exist_ok=True)
    if not result.success:
      raise RuntimeError(f"Failed to create log directory: {result.error}")

    self.log_dir = result.path
    self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
    self.max_logs = max_logs
    self.current_log = None
    self._initialize()

  def _initialize(self):
    """Find or create the current log file."""
    # List log files
    result = fs.list_directory(self.log_dir, pattern="*.log")
    if not result.success:
      logger.error(f"Failed to list log directory: {result.error}")
      # Create a new log file
      self._create_new_log()
      return

    if not result.files:
      # No existing logs, create a new one
      self._create_new_log()
      return

    # Find the most recent log
    latest_log = max(result.files, key=lambda p: fs._get_file_timestamp(p))

    # Check if it's too large
    info_result = fs.get_file_info(latest_log)
    if info_result.success and info_result.size < self.max_size:
      self.current_log = latest_log
      logger.info(f"Using existing log file: {self.current_log}")
    else:
      # Too large, create a new log
      self._create_new_log()

  def _create_new_log(self):
    """Create a new log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_log_path = fs._join_path(self.log_dir, f"app_{timestamp}.log")

    # Create an empty log file
    result = fs.write_text(new_log_path, "")
    if not result.success:
      logger.error(f"Failed to create new log file: {result.error}")
      raise RuntimeError(f"Failed to create new log file: {result.error}")

    self.current_log = new_log_path
    logger.info(f"Created new log file: {self.current_log}")

    # Clean up old logs if needed
    self._cleanup_old_logs()

  def _cleanup_old_logs(self):
    """Remove old log files if we have too many."""
    result = fs.list_directory(self.log_dir, pattern="*.log")
    if not result.success or len(result.files) <= self.max_logs:
      return

    # Sort logs by modification time (oldest first)
    sorted_logs = sorted(result.files, key=lambda p: fs._get_file_timestamp(p))

    # Delete oldest logs to stay under the limit
    logs_to_delete = sorted_logs[:len(sorted_logs) - self.max_logs]
    for log_file in logs_to_delete:
      delete_result = fs.delete(log_file)
      if delete_result.success:
        logger.info(f"Deleted old log file: {log_file}")
      else:
        logger.warning(f"Failed to delete old log file {log_file}: {delete_result.error}")

  def write(self, message):
    """Write a message to the current log file."""
    if not self.current_log:
      self._initialize()

    # Add timestamp to message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"

    # Append to the current log
    content = log_entry
    info_result = fs.get_file_info(self.current_log)
    if info_result.success and info_result.exists:
      read_result = fs.read_text(self.current_log)
      if read_result.success:
        content = read_result.content + log_entry

    # Write the updated content
    result = fs.write_text(self.current_log, content)
    if not result.success:
      logger.error(f"Failed to write to log: {result.error}")
      return False

    # Check if we need to rotate
    if info_result.success and info_result.size + len(log_entry.encode()) > self.max_size:
      logger.info(f"Log file {self.current_log} reached max size, rotating")
      self._create_new_log()

    return True
```

### Example 3: File Backup Tool

Here's a simple file backup tool that demonstrates several `quackcore.fs` features:

```python
from quackcore.fs import service as fs
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BackupTool:
  def __init__(self, source_dir, backup_dir, patterns=None):
    self.source_dir = source_dir
    self.backup_dir = backup_dir
    self.patterns = patterns or ["*"]  # Default to all files

    # Ensure the backup directory exists
    result = fs.create_directory(backup_dir, exist_ok=True)
    if not result.success:
      raise RuntimeError(f"Failed to create backup directory: {result.error}")

  def create_backup(self, include_checksum=True):
    """Create a new backup of the source directory."""
    # Create a timestamped backup directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = fs._join_path(self.backup_dir, backup_name)

    dir_result = fs.create_directory(backup_path)
    if not dir_result.success:
      logger.error(f"Failed to create backup directory: {dir_result.error}")
      return None

    # Create manifest file
    manifest = {
      "backup_date": timestamp,
      "source_directory": str(self.source_dir),
      "files": []
    }

    # Find files to backup
    files_backed_up = 0
    total_size = 0

    for pattern in self.patterns:
      find_result = fs.find_files(self.source_dir, pattern, recursive=True)
      if not find_result.success:
        logger.error(f"Failed to find files with pattern {pattern}: {find_result.error}")
        continue

      # Copy each file to the backup location
      for source_file in find_result.files:
        # Get relative path from source directory
        rel_path_str = str(source_file).replace(str(self.source_dir), "").lstrip("/").lstrip("\\")

        # Create parent directories in backup
        parent_dir = fs._join_path(backup_path, fs._split_path(rel_path_str)[:-1])
        fs.create_directory(parent_dir, exist_ok=True)

        # Destination path in backup
        dest_file = fs._join_path(backup_path, rel_path_str)

        # Copy the file
        copy_result = fs.copy(source_file, dest_file)
        if not copy_result.success:
          logger.error(f"Failed to copy {source_file}: {copy_result.error}")
          continue

        # Add to manifest
        file_info = fs.get_file_info(source_file)
        file_entry = {
          "path": rel_path_str,
          "size": file_info.size if file_info.success else 0,
          "modified": file_info.modified if file_info.success else 0
        }

        # Add checksum if requested
        if include_checksum:
          try:
            file_entry["checksum"] = fs._compute_checksum(source_file)
          except Exception as e:
            logger.warning(f"Failed to compute checksum for {source_file}: {str(e)}")

        manifest["files"].append(file_entry)
        files_backed_up += 1
        total_size += file_info.size if file_info.success else 0

    # Add summary information to manifest
    manifest["total_files"] = files_backed_up
    manifest["total_size"] = total_size
    manifest["total_size_human"] = fs._get_file_size_str(total_size)

    # Write manifest
    manifest_path = fs._join_path(backup_path, "manifest.json")
    manifest_result = fs.write_json(manifest_path, manifest, indent=2)
    if not manifest_result.success:
      logger.error(f"Failed to write manifest: {manifest_result.error}")

    logger.info(f"Backup complete: {files_backed_up} files, {fs._get_file_size_str(total_size)}")
    return backup_path

  def verify_backup(self, backup_path):
    """Verify the integrity of a backup using checksums."""
    # Read the manifest
    manifest_path = fs._join_path(backup_path, "manifest.json")
    manifest_result = fs.read_json(manifest_path)
    if not manifest_result.success:
      logger.error(f"Failed to read manifest: {manifest_result.error}")
      return False

    manifest = manifest_result.data

    # Check each file
    files_checked = 0
    files_ok = 0

    for file_entry in manifest.get("files", []):
      file_path = file_entry.get("path")
      if not file_path:
        continue

      # Get the backup copy path
      backup_file = fs._join_path(backup_path, file_path)

      # Verify the file exists
      file_info = fs.get_file_info(backup_file)
      if not file_info.success or not file_info.exists:
        logger.warning(f"Backup file missing: {file_path}")
        continue

      # Verify the checksum if available
      original_checksum = file_entry.get("checksum")
      if original_checksum:
        try:
          current_checksum = fs._compute_checksum(backup_file)
          if current_checksum != original_checksum:
            logger.warning(f"Checksum mismatch for {file_path}")
            continue
        except Exception as e:
          logger.warning(f"Failed to compute checksum for {backup_file}: {str(e)}")
          continue

      files_ok += 1
      files_checked += 1

    integrity = files_ok / files_checked if files_checked > 0 else 0
    logger.info(f"Backup integrity: {integrity:.1%} ({files_ok}/{files_checked} files verified)")
    return integrity >= 0.99  # 99% integrity required
```

## Advanced Techniques

### Working with Binary Files

The `quackcore.fs` module offers powerful features for working with binary files:

```python
from quackcore.fs import service as fs


# Reading binary file as chunks
def process_large_binary_file(file_path, chunk_size=1024 * 1024):
  """Process a large binary file in chunks."""
  info_result = fs.get_file_info(file_path)
  if not info_result.success or not info_result.exists:
    raise FileNotFoundError(f"File not found: {file_path}")

  total_size = info_result.size
  processed = 0

  with open(file_path, 'rb') as f:
    while processed < total_size:
      chunk = f.read(chunk_size)
      if not chunk:
        break

      # Process chunk here
      process_binary_chunk(chunk)

      processed += len(chunk)
      progress = (processed / total_size) * 100
      print(f"Progress: {progress:.1f}% ({fs._get_file_size_str(processed)} of {fs._get_file_size_str(total_size)})")


# Detecting file type
def is_image_file(file_path):
  """Check if a file is an image based on content and MIME type."""
  mime_result = fs._get_mime_type(file_path)
  if mime_result and mime_result.startswith('image/'):
    return True

  # Check magic numbers as fallback
  binary_result = fs.read_binary(file_path)
  if not binary_result.success:
    return False

  # Get first few bytes to check signatures
  header = binary_result.content[:12]

  # Check common image signatures
  if header.startswith(b'\xff\xd8\xff'):  # JPEG
    return True
  if header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
    return True
  if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF
    return True
  if header.startswith(b'BM'):  # BMP
    return True

  return False
```

### Handling Special Characters in Paths

Working with international filenames or paths with special characters:

```python
from quackcore.fs import service as fs

def safe_filename(filename):
    """Convert a string to a safe filename."""
    # Replace problematic characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Ensure reasonable length
    if len(filename) > 255:
        # Keep extension if present
        parts = filename.rsplit('.', 1)
        if len(parts) > 1:
            filename = parts[0][:250] + '.' + parts[1]
        else:
            filename = filename[:255]
    
    return filename

# Working with international filenames
def save_international_file(content, filename):
    """Save content to a file with an international filename."""
    # Make filename safe
    safe_name = safe_filename(filename)
    
    # Ensure we use UTF-8 encoding
    result = fs.write_text(safe_name, content, encoding="utf-8")
    if not result.success:
        print(f"Failed to save file: {result.error}")
        return False
    
    return True

# Example with Japanese filename
japanese_filename = "日本語のファイル名.txt"
save_international_file("This is content in a file with Japanese name", japanese_filename)
```

### Multi-platform Path Handling

Working with paths across different operating systems:

```python
from quackcore.fs import service as fs
import os


def create_platform_independent_path(parts):
  """Create a path that works across platforms."""
  return fs._join_path(*parts)


# Windows path
windows_path = create_platform_independent_path(["C:", "Users", "username", "Documents"])
print(f"Windows path: {windows_path}")

# Unix path
unix_path = create_platform_independent_path(["/", "home", "username", "documents"])
print(f"Unix path: {unix_path}")


# Detect the current platform
def get_data_directory():
  """Get the appropriate data directory for the current platform."""
  if os.name == 'nt':  # Windows
    base_dir = os.environ.get('APPDATA', fs._join_path('C:', 'Users', os.getlogin(), 'AppData', 'Roaming'))
    return fs._join_path(base_dir, 'QuackTool', 'data')
  else:  # Unix-like
    base_dir = os.environ.get('XDG_DATA_HOME', fs._join_path(fs._expand_user_vars('~'), '.local', 'share'))
    return fs._join_path(base_dir, 'quacktool', 'data')
```

## Performance Considerations

### Caching File Information

For performance-sensitive applications, you might want to cache file information:

```python
from quackcore.fs import service as fs
import time

class FileInfoCache:
    def __init__(self, max_age=60):  # Cache entries for 60 seconds by default
        self.cache = {}
        self.max_age = max_age
    
    def get_file_info(self, path):
        """Get file info, using cache if available and not expired."""
        now = time.time()
        
        # Check if we have a cached entry
        if path in self.cache:
            entry = self.cache[path]
            age = now - entry['timestamp']
            
            # If the entry is still valid, return it
            if age < self.max_age:
                return entry['info']
            
            # Otherwise, remove the stale entry
            del self.cache[path]
        
        # Get fresh info
        info = fs.get_file_info(path)
        
        # Cache the result if successful
        if info.success:
            self.cache[path] = {
                'info': info,
                'timestamp': now
            }
        
        return info
```

### Batch Operations

For operations on multiple files, consider using batch patterns:

```python
from quackcore.fs import service as fs
import concurrent.futures

def batch_process_files(directory, pattern, processor_func, max_workers=4):
    """Process multiple files in parallel."""
    # Find the files
    result = fs.find_files(directory, pattern, recursive=True)
    if not result.success:
        print(f"Failed to find files: {result.error}")
        return []
    
    processed_results = []
    
    # Process in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Start the operations and mark each future with its file
        future_to_file = {
            executor.submit(processor_func, file): file 
            for file in result.files
        }
        
        # Process as they complete
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                data = future.result()
                processed_results.append((file, data, None))
            except Exception as exc:
                print(f"{file} generated an exception: {exc}")
                processed_results.append((file, None, str(exc)))
    
    return processed_results
```

## Creating a Reusable Path Utility Class

Here's an example of creating a reusable path utility class that integrates with `quackcore.fs`:

```python
from quackcore.fs import service as fs
from pathlib import Path


class QuackPath:
  """A utility class for working with paths in QuackTools."""

  def __init__(self, path):
    """Initialize with a path."""
    self.path = path if isinstance(path, Path) else Path(path)

  @property
  def exists(self):
    """Check if the path exists."""
    result = fs.get_file_info(self.path)
    return result.success and result.exists

  @property
  def is_file(self):
    """Check if the path is a file."""
    result = fs.get_file_info(self.path)
    return result.success and result.is_file

  @property
  def is_dir(self):
    """Check if the path is a directory."""
    result = fs.get_file_info(self.path)
    return result.success and result.is_dir

  @property
  def size(self):
    """Get the file size."""
    result = fs.get_file_info(self.path)
    return result.size if result.success else None

  @property
  def size_str(self):
    """Get the file size as a human-readable string."""
    size = self.size
    return fs._get_file_size_str(size) if size is not None else "Unknown"

  @property
  def modified(self):
    """Get the last modified timestamp."""
    result = fs.get_file_info(self.path)
    return result.modified if result.success else None

  @property
  def parent(self):
    """Get the parent directory."""
    return QuackPath(self.path.parent)

  @property
  def name(self):
    """Get the filename."""
    return self.path.name

  @property
  def stem(self):
    """Get the filename without extension."""
    return self.path.stem

  @property
  def extension(self):
    """Get the file extension."""
    return fs._get_extension(self.path)

  def read_text(self, encoding="utf-8"):
    """Read text content from the file."""
    result = fs.read_text(self.path, encoding)
    if not result.success:
      raise IOError(f"Failed to read file: {result.error}")
    return result.content

  def write_text(self, content, encoding="utf-8", atomic=True):
    """Write text content to the file."""
    result = fs.write_text(self.path, content, encoding, atomic)
    if not result.success:
      raise IOError(f"Failed to write file: {result.error}")
    return True

  def read_yaml(self):
    """Read and parse YAML content."""
    result = fs.read_yaml(self.path)
    if not result.success:
      raise IOError(f"Failed to read YAML: {result.error}")
    return result.data

  def write_yaml(self, data, atomic=True):
    """Write data as YAML."""
    result = fs.write_yaml(self.path, data, atomic)
    if not result.success:
      raise IOError(f"Failed to write YAML: {result.error}")
    return True

  def read_json(self):
    """Read and parse JSON content."""
    result = fs.read_json(self.path)
    if not result.success:
      raise IOError(f"Failed to read JSON: {result.error}")
    return result.data

  def write_json(self, data, atomic=True, indent=2):
    """Write data as JSON."""
    result = fs.write_json(self.path, data, atomic, indent)
    if not result.success:
      raise IOError(f"Failed to write JSON: {result.error}")
    return True

  def delete(self, missing_ok=True):
    """Delete the file or directory."""
    result = fs.delete(self.path, missing_ok)
    if not result.success:
      raise IOError(f"Failed to delete: {result.error}")
    return True

  def ensure_dir(self):
    """Ensure this path exists as a directory."""
    if self.is_file:
      raise IOError(f"Path exists as a file, not a directory: {self.path}")

    result = fs.create_directory(self.path, exist_ok=True)
    if not result.success:
      raise IOError(f"Failed to create directory: {result.error}")
    return self

  def list_dir(self, pattern=None, include_hidden=False):
    """List contents of the directory."""
    result = fs.list_directory(self.path, pattern, include_hidden)
    if not result.success:
      raise IOError(f"Failed to list directory: {result.error}")

    # Convert to QuackPath objects
    return {
      'files': [QuackPath(f) for f in result.files],
      'directories': [QuackPath(d) for d in result.directories]
    }

  def find_files(self, pattern, recursive=True, include_hidden=False):
    """Find files matching a pattern."""
    result = fs.find_files(self.path, pattern, recursive, include_hidden)
    if not result.success:
      raise IOError(f"Failed to find files: {result.error}")

    # Convert to QuackPath objects
    return {
      'files': [QuackPath(f) for f in result.files],
      'directories': [QuackPath(d) for d in result.directories]
    }

  def join(self, *parts):
    """Join this path with additional parts."""
    return QuackPath(fs._join_path(self.path, *parts))

  def copy_to(self, dst, overwrite=False):
    """Copy this file or directory to destination."""
    result = fs.copy(self.path, dst, overwrite)
    if not result.success:
      raise IOError(f"Failed to copy: {result.error}")
    return QuackPath(result.path)

  def move_to(self, dst, overwrite=False):
    """Move this file or directory to destination."""
    result = fs.move(self.path, dst, overwrite)
    if not result.success:
      raise IOError(f"Failed to move: {result.error}")
    return QuackPath(result.path)

  def __str__(self):
    return str(self.path)

  def __repr__(self):
    return f"QuackPath('{self.path}')"
```

## Integration with Other QuackCore Components

The `quackcore.fs` module is designed to integrate seamlessly with other components of the QuackCore ecosystem:

### Integration with QuackCore Logging

The fs module works well with QuackCore's logging system:

```python
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

def initialize_app_directories(app_name):
    """Initialize standard directories for a QuackTool application."""
    # Create standard directories
    directories = {
        'config': f"{app_name}/config",
        'data': f"{app_name}/data",
        'logs': f"{app_name}/logs",
        'cache': f"{app_name}/cache",
        'temp': f"{app_name}/temp"
    }
    
    created_dirs = {}
    
    for name, path in directories.items():
        result = fs.create_directory(path, exist_ok=True)
        if result.success:
            logger.info(f"Initialized {name} directory at {result.path}")
            created_dirs[name] = result.path
        else:
            logger.error(f"Failed to create {name} directory: {result.error}")
    
    return created_dirs
```

### Integration with QuackCore Error System

The fs module integrates with QuackCore's error handling system:

```python
from quackcore.fs import service as fs
from quackcore.errors import QuackError, QuackIOError

def safe_read_config(config_path):
    """Safely read a config file with QuackCore error handling."""
    try:
        result = fs.read_yaml(config_path)
        if not result.success:
            # Convert fs error to QuackError
            raise QuackIOError(f"Failed to read config: {result.error}", config_path)
        return result.data
    except QuackError as e:
        # QuackErrors can be handled by QuackCore error system
        raise
    except Exception as e:
        # Convert other exceptions to QuackError
        raise QuackIOError(f"Unexpected error reading config: {str(e)}", config_path) from e
```

### Using as a Plugin

You can use the `quackcore.fs` as a plugin for other QuackCore components:

```python
from quackcore.fs.plugin import create_plugin
from quackcore.plugin_manager import PluginManager

# Create the file system plugin
fs_plugin = create_plugin()

# Register with the plugin manager
plugin_manager = PluginManager()
plugin_manager.register_plugin(fs_plugin)

# Now the fs plugin can be accessed by other components
# through the plugin manager
```

### Creating a File-based Configuration System

Here's how to create a configuration system that integrates with QuackCore:

```python
from quackcore.fs import service as fs
from quackcore.logging import get_logger
from quackcore.errors import QuackValidationError

logger = get_logger(__name__)


class QuackConfig:
  """Configuration system for QuackTools."""

  def __init__(self, config_dir="config"):
    """Initialize the configuration system."""
    self.config_dir = config_dir
    self.settings = {}
    self.ensure_config_dir()

  def ensure_config_dir(self):
    """Ensure the config directory exists."""
    result = fs.create_directory(self.config_dir, exist_ok=True)
    if not result.success:
      logger.error(f"Failed to create config directory: {result.error}")
      raise QuackIOError(f"Failed to create config directory: {result.error}", self.config_dir)

  def load_setting(self, name):
    """Load a setting file by name."""
    path = fs._join_path(self.config_dir, f"{name}.yaml")
    result = fs.read_yaml(path)
    if not result.success:
      logger.warning(f"Failed to load setting {name}: {result.error}")
      return None

    self.settings[name] = result.data
    return result.data

  def save_setting(self, name, data):
    """Save a setting file."""
    path = fs._join_path(self.config_dir, f"{name}.yaml")
    result = fs.write_yaml(path, data, atomic=True)
    if not result.success:
      logger.error(f"Failed to save setting {name}: {result.error}")
      raise QuackIOError(f"Failed to save setting: {result.error}", path)

    self.settings[name] = data
    return True

  def get(self, name, default=None):
    """Get a setting, loading it if necessary."""
    if name not in self.settings:
      setting = self.load_setting(name)
      if setting is None:
        return default
    return self.settings[name]

  def set(self, name, value):
    """Set and save a setting."""
    self.save_setting(name, value)
```

### Working with QuackCore Events

Integrating file monitoring with QuackCore's event system:

```python
import time
from threading import Thread
from quackcore.fs import service as fs
from quackcore.events import EventEmitter

class FileWatcher(EventEmitter):
    """Watch files for changes and emit events."""
    
    def __init__(self, paths_to_watch, check_interval=5):
        """Initialize the file watcher."""
        super().__init__()
        self.paths = paths_to_watch
        self.check_interval = check_interval
        self.last_modified = self._get_initial_timestamps()
        self.running = False
        self.watch_thread = None
    
    def _get_initial_timestamps(self):
        """Get initial timestamps for all watched paths."""
        timestamps = {}
        for path in self.paths:
            try:
                info_result = fs.get_file_info(path)
                if info_result.success and info_result.exists:
                    timestamps[path] = info_result.modified
                else:
                    timestamps[path] = 0  # File doesn't exist yet
            except Exception as e:
                timestamps[path] = 0
        return timestamps
    
    def start(self):
        """Start watching for file changes."""
        if self.running:
            return
        
        self.running = True
        self.watch_thread = Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
    
    def stop(self):
        """Stop watching for file changes."""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join(timeout=self.check_interval + 1)
    
    def _watch_loop(self):
        """Main watching loop."""
        while self.running:
            self._check_for_changes()
            time.sleep(self.check_interval)
    
    def _check_for_changes(self):
        """Check all watched paths for changes."""
        for path in self.paths:
            try:
                info_result = fs.get_file_info(path)
                if not info_result.success:
                    continue
                
                # Check if file was created
                if path in self.last_modified and self.last_modified[path] == 0 and info_result.exists:
                    self.emit('file_created', path)
                    self.last_modified[path] = info_result.modified
                
                # Check if file was modified
                elif info_result.exists and path in self.last_modified and info_result.modified > self.last_modified[path]:
                    self.emit('file_modified', path, info_result.modified - self.last_modified[path])
                    self.last_modified[path] = info_result.modified
                
                # Check if file was deleted
                elif path in self.last_modified and self.last_modified[path] > 0 and not info_result.exists:
                    self.emit('file_deleted', path)
                    self.last_modified[path] = 0
            
            except Exception as e:
                self.emit('error', path, str(e))
```

## Transitioning from pathlib to quackcore.fs

If you're already familiar with Python's `pathlib` module, transitioning to `quackcore.fs` is straightforward. This section provides side-by-side comparisons to help you make the switch.

### Basic Path Operations

| Task | pathlib Example | quackcore.fs Example |
|------|----------------|---------------------|
| Create a path | `path = Path('dir/file.txt')` | `path = fs.join_path('dir', 'file.txt')` |
| Check if exists | `exists = path.exists()` | `info = fs.get_file_info(path)` <br> `exists = info.exists` |
| Get parent directory | `parent = path.parent` | `parent = fs.join_path(*fs.split_path(path)[:-1])` |
| Get file name | `name = path.name` | `name = fs.split_path(path)[-1]` |
| Get stem | `stem = path.stem` | `parts = fs.split_path(path)[-1].split('.')` <br> `stem = parts[0]` |
| Get suffix | `suffix = path.suffix` | `suffix = fs.get_extension(path)` |
| Absolute path | `abs_path = path.absolute()` | `abs_path = fs.normalize_path(path)` |
| Join paths | `new_path = path / 'subdir' / 'file.txt'` | `new_path = fs.join_path(path, 'subdir', 'file.txt')` |

### File Operations 

| Task | pathlib Example | quackcore.fs Example |
|------|----------------|---------------------|
| Read text | `content = path.read_text()` | `result = fs.read_text(path)` <br> `content = result.content` |
| Write text | `path.write_text('content')` | `fs.write_text(path, 'content')` |
| Read binary | `data = path.read_bytes()` | `result = fs.read_binary(path)` <br> `data = result.content` |
| Write binary | `path.write_bytes(data)` | `fs.write_binary(path, data)` |
| File size | `size = path.stat().st_size` | `info = fs.get_file_info(path)` <br> `size = info.size` |
| Modified time | `mtime = path.stat().st_mtime` | `info = fs.get_file_info(path)` <br> `mtime = info.modified` |
| Touch file | `path.touch()` | `fs.write_text(path, '')` |
| File permissions | `mode = path.stat().st_mode` | `info = fs.get_file_info(path)` <br> `mode = info.permissions` |

### Directory Operations

| Task | pathlib Example | quackcore.fs Example |
|------|----------------|---------------------|
| Create directory | `path.mkdir()` | `fs.create_directory(path)` |
| Create with parents | `path.mkdir(parents=True)` | `fs.create_directory(path)` |
| List directory | `items = list(path.iterdir())` | `result = fs.list_directory(path)` <br> `items = result.files + result.directories` |
| Find by pattern | `py_files = list(path.glob('*.py'))` | `result = fs.find_files(path, '*.py')` <br> `py_files = result.files` |
| Recursive find | `all_py = list(path.rglob('*.py'))` | `result = fs.find_files(path, '*.py', recursive=True)` <br> `all_py = result.files` |
| Is directory | `is_dir = path.is_dir()` | `info = fs.get_file_info(path)` <br> `is_dir = info.is_dir` |
| Is file | `is_file = path.is_file()` | `info = fs.get_file_info(path)` <br> `is_file = info.is_file` |

### Migration Examples

Here are some examples of migrating more complex pathlib-based code to quackcore.fs:

**Finding and processing files with pathlib:**

```python
from pathlib import Path
import json

def process_json_files(directory):
    # Find all JSON files
    json_files = list(Path(directory).glob('**/*.json'))
    
    results = []
    for file_path in json_files:
        try:
            # Read and parse JSON
            data = json.loads(file_path.read_text())
            
            # Process data
            results.append({
                'path': str(file_path),
                'name': file_path.name,
                'data': data
            })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return results
```

**The same function with quackcore.fs:**

```python
from quackcore.fs import service as fs


def process_json_files(directory):
  # Find all JSON files
  find_result = fs.find_files(directory, '*.json', recursive=True)
  if not find_result.success:
    print(f"Error finding files: {find_result.error}")
    return []

  results = []
  for file_path in find_result.files:
    # Read and parse JSON directly
    json_result = fs.read_json(file_path)
    if not json_result.success:
      print(f"Error processing {file_path}: {json_result.error}")
      continue

    # Process data
    results.append({
      'path': str(file_path),
      'name': fs._split_path(file_path)[-1],
      'data': json_result.data
    })

  return results
```

**Creating a directory structure with pathlib:**

```python
from pathlib import Path
import shutil

def setup_project(project_name):
    # Create base directory
    project_dir = Path(project_name)
    if project_dir.exists():
        print(f"Project {project_name} already exists")
        return False
    
    try:
        # Create directories
        for subdir in ['src', 'docs', 'tests', 'data']:
            (project_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Create basic files
        (project_dir / 'README.md').write_text(f"# {project_name}\n\nA new project.")
        (project_dir / 'src' / '__init__.py').touch()
        (project_dir / 'tests' / '__init__.py').touch()
        
        print(f"Created project structure for {project_name}")
        return True
    except Exception as e:
        # Clean up on failure
        if project_dir.exists():
            shutil.rmtree(project_dir)
        print(f"Error creating project: {e}")
        return False
```

**The same function with quackcore.fs:**

```python
from quackcore.fs import service as fs


def setup_project(project_name):
  # Check if project exists
  project_dir = project_name
  info_result = fs.get_file_info(project_dir)
  if info_result.success and info_result.exists:
    print(f"Project {project_name} already exists")
    return False

  try:
    # Create directories
    for subdir in ['src', 'docs', 'tests', 'data']:
      subdir_path = fs._join_path(project_dir, subdir)
      dir_result = fs.create_directory(subdir_path, exist_ok=True)
      if not dir_result.success:
        raise Exception(f"Failed to create directory {subdir}: {dir_result.error}")

    # Create basic files
    readme_path = fs._join_path(project_dir, 'README.md')
    fs.write_text(readme_path, f"# {project_name}\n\nA new project.")

    init_src = fs._join_path(project_dir, 'src', '__init__.py')
    fs.write_text(init_src, '')

    init_tests = fs._join_path(project_dir, 'tests', '__init__.py')
    fs.write_text(init_tests, '')

    print(f"Created project structure for {project_name}")
    return True
  except Exception as e:
    # Clean up on failure
    delete_result = fs.delete(project_dir)
    print(f"Error creating project: {e}")
    return False
```

## Design Patterns with quackcore.fs

This section presents common design patterns that work well with `quackcore.fs`.

### Repository Pattern

The Repository pattern provides a clean separation between data storage logic and business logic:

```python
from quackcore.fs import service as fs
from typing import Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')  # Type of the entity we're storing


class FileSystemRepository(Generic[T]):
  """Repository implementation using quackcore.fs for storage."""

  def __init__(self, base_dir: str, serializer, deserializer):
    """
    Initialize the repository.
    
    Args:
        base_dir: Base directory for storing entities
        serializer: Function to convert entity to dict
        deserializer: Function to convert dict to entity
    """
    self.base_dir = base_dir
    self.serializer = serializer
    self.deserializer = deserializer

    # Ensure the directory exists
    fs.create_directory(base_dir, exist_ok=True)

  def _get_path(self, id: str) -> str:
    """Get the file path for an entity."""
    return fs._join_path(self.base_dir, f"{id}.json")

  def save(self, id: str, entity: T) -> bool:
    """Save an entity."""
    path = self._get_path(id)
    data = self.serializer(entity)
    result = fs.write_json(path, data, atomic=True)
    return result.success

  def get(self, id: str) -> Optional[T]:
    """Get an entity by ID."""
    path = self._get_path(id)
    result = fs.read_json(path)
    if not result.success:
      return None
    return self.deserializer(result.data)

  def delete(self, id: str) -> bool:
    """Delete an entity."""
    path = self._get_path(id)
    result = fs.delete(path)
    return result.success

  def list_all(self) -> List[T]:
    """List all entities."""
    result = fs.list_directory(self.base_dir, pattern="*.json")
    if not result.success:
      return []

    entities = []
    for file_path in result.files:
      read_result = fs.read_json(file_path)
      if read_result.success:
        entity = self.deserializer(read_result.data)
        entities.append(entity)

    return entities


# Example usage:
class User:
  def __init__(self, name: str, email: str, role: str = "user"):
    self.name = name
    self.email = email
    self.role = role


# Serializers
def serialize_user(user: User) -> Dict:
  return {
    "name": user.name,
    "email": user.email,
    "role": user.role
  }


def deserialize_user(data: Dict) -> User:
  return User(
    name=data["name"],
    email=data["email"],
    role=data.get("role", "user")
  )


# Create a user repository
user_repo = FileSystemRepository[User](
  base_dir="data/users",
  serializer=serialize_user,
  deserializer=deserialize_user
)

# Use the repository
user = User("Alice", "alice@example.com", "admin")
user_repo.save("alice", user)

# Retrieve the user
alice = user_repo.get("alice")
```

### Factory Pattern

The Factory pattern can be used to create different types of file operations:

```python
from quackcore.fs import service as fs
from typing import Callable, TypeVar, Generic, Dict, Any

T = TypeVar('T')


class FileHandlerFactory:
  """Factory for creating file handlers based on file extension."""

  def __init__(self):
    self.handlers = {}

  def register_handler(self, extension: str, reader: Callable, writer: Callable):
    """Register a handler for an extension."""
    self.handlers[extension.lower()] = {
      'reader': reader,
      'writer': writer
    }

  def get_reader(self, path: str) -> Callable:
    """Get a reader function for a path."""
    ext = fs._get_extension(path).lower()
    handler = self.handlers.get(ext)
    if not handler:
      raise ValueError(f"No handler registered for extension: {ext}")
    return handler['reader']

  def get_writer(self, path: str) -> Callable:
    """Get a writer function for a path."""
    ext = fs._get_extension(path).lower()
    handler = self.handlers.get(ext)
    if not handler:
      raise ValueError(f"No handler registered for extension: {ext}")
    return handler['writer']

  def read(self, path: str) -> Any:
    """Read data from a file using the appropriate handler."""
    reader = self.get_reader(path)
    return reader(path)

  def write(self, path: str, data: Any) -> bool:
    """Write data to a file using the appropriate handler."""
    writer = self.get_writer(path)
    return writer(path, data)


# Example usage:
file_factory = FileHandlerFactory()

# Register handlers for different file types
file_factory.register_handler('json',
                              reader=lambda path: fs.read_json(path).data if fs.read_json(path).success else None,
                              writer=lambda path, data: fs.write_json(path, data).success
                              )

file_factory.register_handler('yaml',
                              reader=lambda path: fs.read_yaml(path).data if fs.read_yaml(path).success else None,
                              writer=lambda path, data: fs.write_yaml(path, data).success
                              )

file_factory.register_handler('txt',
                              reader=lambda path: fs.read_text(path).content if fs.read_text(path).success else "",
                              writer=lambda path, data: fs.write_text(path, data).success
                              )

# Use the factory
config = file_factory.read('config.yaml')
file_factory.write('output.json', {'result': 'success'})
```

### Observer Pattern

The Observer pattern can be used to monitor file changes:

```python
from quackcore.fs import service as fs
import time
from typing import Dict, List, Callable, Any
from threading import Thread

class FileObserver:
    """Monitor files for changes."""
    
    def __init__(self, check_interval: int = 5):
        self.files: Dict[str, Dict] = {}  # Path -> metadata
        self.observers: Dict[str, List[Callable]] = {}  # Path -> callbacks
        self.check_interval = check_interval
        self.running = False
        self.thread = None
    
    def watch(self, path: str, callback: Callable[[str, Dict], None]) -> bool:
        """
        Watch a file for changes.
        
        Args:
            path: Path to watch
            callback: Function to call when file changes
                      Signature: callback(path, metadata)
        """
        # Get initial file info
        info = fs.get_file_info(path)
        if not info.success:
            return False
        
        # Store file metadata
        metadata = {
            'exists': info.exists,
            'size': info.size if info.exists else 0,
            'modified': info.modified if info.exists else 0
        }
        
        # Register the file and callback
        self.files[path] = metadata
        
        if path not in self.observers:
            self.observers[path] = []
        self.observers[path].append(callback)
        
        # Start the watcher if not already running
        if not self.running:
            self.start()
        
        return True
    
    def unwatch(self, path: str, callback: Callable = None) -> None:
        """
        Stop watching a file.
        
        Args:
            path: Path to stop watching
            callback: Specific callback to remove (or all if None)
        """
        if path not in self.observers:
            return
        
        if callback is None:
            # Remove all callbacks
            del self.observers[path]
        else:
            # Remove specific callback
            self.observers[path] = [cb for cb in self.observers[path] if cb != callback]
        
        if not self.observers[path]:
            del self.observers[path]
        
        # If no files are being watched, stop the watcher
        if not self.observers:
            self.stop()
    
    def start(self) -> None:
        """Start the file watcher."""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the file watcher."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.check_interval * 2)
    
    def _watch_loop(self) -> None:
        """Main watching loop."""
        while self.running and self.observers:
            self._check_all_files()
            time.sleep(self.check_interval)
    
    def _check_all_files(self) -> None:
        """Check all watched files for changes."""
        for path, metadata in list(self.files.items()):
            if path not in self.observers:
                continue
            
            info = fs.get_file_info(path)
            if not info.success:
                continue
            
            new_metadata = {
                'exists': info.exists,
                'size': info.size if info.exists else 0,
                'modified': info.modified if info.exists else 0
            }
            
            # Check for changes
            if self._has_changed(metadata, new_metadata):
                # Update stored metadata
                self.files[path] = new_metadata
                
                # Notify observers
                for callback in self.observers[path]:
                    try:
                        callback(path, new_metadata)
                    except Exception as e:
                        print(f"Error in observer callback for {path}: {e}")
    
    def _has_changed(self, old_metadata: Dict, new_metadata: Dict) -> bool:
        """Determine if a file has changed."""
        # Check existence
        if old_metadata['exists'] != new_metadata['exists']:
            return True
        
        # If file doesn't exist, no other changes matter
        if not new_metadata['exists']:
            return False
        
        # Check size and modification time
        return (old_metadata['size'] != new_metadata['size'] or 
                old_metadata['modified'] != new_metadata['modified'])

# Example usage:
observer = FileObserver(check_interval=2)

def on_file_change(path, metadata):
    print(f"File changed: {path}")
    print(f"New metadata: {metadata}")
    
    # Read the updated file
    if metadata['exists']:
        result = fs.read_text(path)
        if result.success:
            print(f"New content: {result.content}")

# Watch a file
observer.watch("config.txt", on_file_change)

# Later, to stop watching
# observer.unwatch("config.txt")
```
## Testing with quackcore.fs

Testing code that uses the filesystem can be challenging, but `quackcore.fs` makes it easier by providing a consistent API that can be mocked effectively. This section covers strategies for testing code that relies on `quackcore.fs`.

### Mocking the FileSystemService

When unit testing, you'll often want to mock the filesystem to avoid actually reading or writing files. Here's how to do that with `pytest` and `unittest.mock`:

```python
import pytest
from unittest.mock import MagicMock, patch
from quackcore.fs import service as fs
from quackcore.fs.results import ReadResult, FileInfoResult

def test_config_reader():
    # Function we want to test
    def read_config(config_path):
        result = fs.read_yaml(config_path)
        if not result.success:
            return {}
        return result.data
    
    # Mock the fs.read_yaml method
    with patch('quackcore.fs.service.read_yaml') as mock_read_yaml:
        # Setup the mock to return a successful result
        mock_result = MagicMock(spec=ReadResult)
        mock_result.success = True
        mock_result.data = {"app_name": "TestApp", "version": "1.0.0"}
        mock_read_yaml.return_value = mock_result
        
        # Call the function under test
        config = read_config("config.yaml")
        
        # Verify the result
        assert config["app_name"] == "TestApp"
        assert config["version"] == "1.0.0"
        
        # Verify fs.read_yaml was called with the correct path
        mock_read_yaml.assert_called_once_with("config.yaml")
    
    # Test error handling
    with patch('quackcore.fs.service.read_yaml') as mock_read_yaml:
        # Setup the mock to return a failed result
        mock_result = MagicMock(spec=ReadResult)
        mock_result.success = False
        mock_result.error = "File not found"
        mock_read_yaml.return_value = mock_result
        
        # Call the function under test
        config = read_config("missing.yaml")
        
        # Verify the result
        assert config == {}
```

### Using a Fake FileSystemService

For more complex tests, you might want to create a fake implementation of the `FileSystemService`:

```python
from quackcore.fs.results import ReadResult, WriteResult, FileInfoResult
from pathlib import Path

class FakeFileSystemService:
    """A fake FileSystemService for testing."""
    
    def __init__(self):
        # In-memory filesystem
        self.files = {}
    
    def read_text(self, path, encoding="utf-8"):
        """Simulate reading a text file."""
        path_str = str(path)
        if path_str in self.files:
            return ReadResult(
                success=True,
                path=Path(path_str),
                content=self.files[path_str],
                encoding=encoding
            )
        return ReadResult(
            success=False,
            path=Path(path_str),
            content="",
            error="File not found"
        )
    
    def write_text(self, path, content, encoding="utf-8", atomic=False):
        """Simulate writing a text file."""
        path_str = str(path)
        self.files[path_str] = content
        return WriteResult(
            success=True,
            path=Path(path_str),
            bytes_written=len(content.encode(encoding))
        )
    
    def get_file_info(self, path):
        """Simulate getting file info."""
        path_str = str(path)
        exists = path_str in self.files
        return FileInfoResult(
            success=True,
            path=Path(path_str),
            exists=exists,
            is_file=exists,
            is_dir=False,
            size=len(self.files.get(path_str, "").encode("utf-8")) if exists else 0
        )
    
    # Add more methods as needed for your tests

# Use the fake in tests
def test_with_fake_fs():
    # Create a fake fs
    fake_fs = FakeFileSystemService()
    
    # Write a test file
    fake_fs.write_text("test.txt", "Hello, World!")
    
    # Function to test that uses the fake
    def read_first_line(fs, path):
        result = fs.read_text(path)
        if not result.success:
            return None
        return result.content.split("\n")[0]
    
    # Test the function with our fake
    first_line = read_first_line(fake_fs, "test.txt")
    assert first_line == "Hello, World!"
    
    # Test with a missing file
    first_line = read_first_line(fake_fs, "missing.txt")
    assert first_line is None
```

### Creating a Test Fixture

For integration tests where you actually want to interact with the real filesystem, you can create a pytest fixture that sets up a temporary directory:

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from quackcore.fs import service as fs


@pytest.fixture
def temp_dir():
  """Create a temporary directory for tests."""
  # Create a temporary directory
  temp_path = tempfile.mkdtemp()
  yield temp_path

  # Clean up after the test
  shutil.rmtree(temp_path)


def test_file_operations(temp_dir):
  # Create a test file
  test_file = fs._join_path(temp_dir, "test.txt")
  fs.write_text(test_file, "Test content")

  # Verify the file exists
  info = fs.get_file_info(test_file)
  assert info.success
  assert info.exists
  assert info.is_file

  # Read the file
  result = fs.read_text(test_file)
  assert result.success
  assert result.content == "Test content"

  # Delete the file
  delete_result = fs.delete(test_file)
  assert delete_result.success

  # Verify the file no longer exists
  info = fs.get_file_info(test_file)
  assert info.success
  assert not info.exists
```

## Error Handling Patterns

Proper error handling is crucial when working with filesystem operations. Here are some patterns for handling errors with `quackcore.fs`:

### Basic Error Handling

The simplest pattern is to check the `success` attribute of result objects:

```python
result = fs.read_text("config.txt")
if result.success:
    # Process the content
    process_content(result.content)
else:
    # Handle the error
    print(f"Error reading config: {result.error}")
```

### Centralized Error Handler

For more complex applications, you might want to create a centralized error handler:

```python
class FSErrorHandler:
    """Centralized handler for filesystem errors."""
    
    def __init__(self, logger):
        self.logger = logger
    
    def handle_error(self, result, operation, path):
        """Handle a filesystem operation error."""
        if "not found" in result.error.lower():
            self.logger.warning(f"{path} not found when performing {operation}")
            return "NOT_FOUND"
        
        if "permission denied" in result.error.lower():
            self.logger.error(f"Permission denied for {path} when performing {operation}")
            return "PERMISSION_DENIED"
        
        if "exists" in result.error.lower():
            self.logger.warning(f"{path} already exists when performing {operation}")
            return "ALREADY_EXISTS"
        
        # Generic error
        self.logger.error(f"Error {operation} {path}: {result.error}")
        return "ERROR"
    
    def handle_read_error(self, result, path):
        """Handle a read operation error."""
        return self.handle_error(result, "reading", path)
    
    def handle_write_error(self, result, path):
        """Handle a write operation error."""
        return self.handle_error(result, "writing", path)
    
    def handle_delete_error(self, result, path):
        """Handle a delete operation error."""
        return self.handle_error(result, "deleting", path)

# Example usage:
from quackcore.logging import get_logger
logger = get_logger(__name__)
error_handler = FSErrorHandler(logger)

def safe_read_config(config_path):
    """Safely read a configuration file."""
    result = fs.read_yaml(config_path)
    if not result.success:
        error_code = error_handler.handle_read_error(result, config_path)
        if error_code == "NOT_FOUND":
            # Create default config
            return create_default_config()
        # For other errors, return empty dict
        return {}
    return result.data
```

### Using Try/Except with Result Objects

You can combine traditional exception handling with result object checking:

```python
def process_config_file(config_path):
    """Process a configuration file with robust error handling."""
    try:
        # Check if the file exists
        info_result = fs.get_file_info(config_path)
        if not info_result.success:
            raise RuntimeError(f"Error checking config file: {info_result.error}")
        
        if not info_result.exists:
            # File doesn't exist - create default
            return create_default_config(config_path)
        
        # Read the config file
        read_result = fs.read_yaml(config_path)
        if not read_result.success:
            raise RuntimeError(f"Error reading config file: {read_result.error}")
        
        # Process the config
        config = read_result.data
        # ... process config ...
        return config
    
    except RuntimeError as e:
        # Handle expected errors
        logger.error(str(e))
        return None
    except Exception as e:
        # Handle unexpected errors
        logger.exception(f"Unexpected error processing config file: {str(e)}")
        return None
```

### Creating Custom Exception Handlers

You can create custom exception handlers for specific types of filesystem operations:

```python
from functools import wraps

def handle_fs_errors(default_return=None):
    """
    Decorator to handle filesystem errors.
    
    Args:
        default_return: Value to return in case of error
    
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if hasattr(result, 'success') and not result.success:
                    logger.error(f"Error in {func.__name__}: {result.error}")
                    return default_return
                return result
            except Exception as e:
                logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
                return default_return
        return wrapper
    return decorator

# Example usage:
@handle_fs_errors(default_return={})
def load_config(config_path):
    """Load configuration safely."""
    result = fs.read_yaml(config_path)
    if not result.success:
        return {}
    return result.data
```

## Advanced Topics

### Working with Large Files

When working with large files, it's important to process them efficiently. Here are patterns for working with large files using `quackcore.fs`:

```python
def process_large_file(file_path, chunk_size=1024*1024):
    """
    Process a large file in chunks.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of each chunk in bytes
    """
    # Check if the file exists and get its size
    info_result = fs.get_file_info(file_path)
    if not info_result.success or not info_result.exists:
        print(f"File not found: {file_path}")
        return
    
    total_size = info_result.size
    processed = 0
    
    # Open the file directly for reading in binary mode
    # For very large files, we don't want to read the whole file at once
    with open(file_path, 'rb') as f:
        while processed < total_size:
            # Read a chunk
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            # Process the chunk
            process_chunk(chunk)
            
            # Update progress
            processed += len(chunk)
            progress = (processed / total_size) * 100
            print(f"Progress: {progress:.1f}% ({processed}/{total_size} bytes)")
```

### Creating a Custom FileSystemService

If you need specialized behavior, you can create your own custom `FileSystemService`:

```python
from quackcore.fs import FileSystemService
from quackcore.logging import get_logger
from quackcore.fs.results import ReadResult, WriteResult
import time

class LoggingFileSystemService(FileSystemService):
    """A FileSystemService that logs all operations."""
    
    def __init__(self, base_dir=None):
        super().__init__(base_dir)
        self.logger = get_logger(__name__)
        self.operation_count = 0
        self.start_time = time.time()
    
    def read_text(self, path, encoding="utf-8"):
        """Read text with logging."""
        self.operation_count += 1
        self.logger.info(f"Reading text from {path} (operation #{self.operation_count})")
        
        start = time.time()
        result = super().read_text(path, encoding)
        duration = time.time() - start
        
        if result.success:
            self.logger.info(f"Successfully read {len(result.content)} characters in {duration:.3f}s")
        else:
            self.logger.error(f"Failed to read {path}: {result.error}")
        
        return result
    
    def write_text(self, path, content, encoding="utf-8", atomic=True):
        """Write text with logging."""
        self.operation_count += 1
        self.logger.info(f"Writing text to {path} (operation #{self.operation_count})")
        
        start = time.time()
        result = super().write_text(path, content, encoding, atomic)
        duration = time.time() - start
        
        if result.success:
            self.logger.info(f"Successfully wrote {result.bytes_written} bytes in {duration:.3f}s")
        else:
            self.logger.error(f"Failed to write {path}: {result.error}")
        
        return result
    
    def get_stats(self):
        """Get operation statistics."""
        return {
            "operation_count": self.operation_count,
            "uptime": time.time() - self.start_time
        }

# Example usage:
logging_fs = LoggingFileSystemService()
logging_fs.write_text("example.txt", "Hello, World!")
result = logging_fs.read_text("example.txt")
print(result.content)
print(logging_fs.get_stats())
```

### Thread Safety and Concurrency

When using `quackcore.fs` in multi-threaded applications, be aware of potential concurrency issues:

```python
import threading
from quackcore.fs import service as fs
import time
import random
from concurrent.futures import ThreadPoolExecutor


class ThreadSafeCounter:
  """Thread-safe counter for filesystem operations."""

  def __init__(self):
    self.lock = threading.Lock()
    self.count = 0

  def increment(self):
    """Increment the counter safely."""
    with self.lock:
      self.count += 1
      return self.count


def worker(counter, thread_id, dir_path):
  """Worker function for a thread."""
  # Create a thread-specific file
  file_path = fs._join_path(dir_path, f"thread_{thread_id}.txt")

  for i in range(5):
    # Read, modify, and write
    info = fs.get_file_info(file_path)

    if not info.exists:
      # Create the file if it doesn't exist
      content = f"Thread {thread_id} iteration {i}\n"
    else:
      # Append to the file if it exists
      result = fs.read_text(file_path)
      if result.success:
        content = result.content + f"Thread {thread_id} iteration {i}\n"
      else:
        content = f"Thread {thread_id} iteration {i}\n"

    # Write the updated content
    write_result = fs.write_text(file_path, content, atomic=True)
    if write_result.success:
      counter.increment()

    # Sleep for a random time to simulate work
    time.sleep(random.uniform(0.01, 0.1))


def run_concurrent_fs_operations(num_threads=10):
  """Run concurrent filesystem operations."""
  # Create a temporary directory
  temp_dir = fs._create_temp_directory()
  counter = ThreadSafeCounter()

  print(f"Created temporary directory: {temp_dir}")

  # Run operations in multiple threads
  with ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = []
    for i in range(num_threads):
      futures.append(executor.submit(worker, counter, i, temp_dir))

  # Check the results
  print(f"Completed {counter.count} file operations")

  # List the created files
  result = fs.list_directory(temp_dir)
  if result.success:
    print(f"Created {len(result.files)} files:")
    for file in result.files:
      print(f"  {file.name}")

  return temp_dir
```

## Extending quackcore.fs

You can extend the functionality of `quackcore.fs` to add new capabilities:

### Creating Custom Result Classes

If you need specialized result objects for new types of operations:

```python
from quackcore.fs.results import OperationResult
from pydantic import Field

class ImageInfoResult(OperationResult):
    """Result of an image information operation."""
    
    width: int = Field(default=0, description="Image width in pixels")
    height: int = Field(default=0, description="Image height in pixels")
    format: str = Field(default="", description="Image format (e.g., PNG, JPEG)")
    color_mode: str = Field(default="", description="Color mode (e.g., RGB, CMYK)")
    dpi: tuple = Field(default=(0, 0), description="Resolution in DPI (x, y)")

# Function that uses the custom result
def get_image_info(path):
    """Get information about an image file."""
    from PIL import Image
    
    # Check if the file exists
    info_result = fs.get_file_info(path)
    if not info_result.success or not info_result.exists:
        return ImageInfoResult(
            success=False,
            path=path,
            error="File not found"
        )
    
    try:
        # Open the image
        with Image.open(path) as img:
            return ImageInfoResult(
                success=True,
                path=path,
                width=img.width,
                height=img.height,
                format=img.format,
                color_mode=img.mode,
                dpi=img.info.get('dpi', (0, 0))
            )
    except Exception as e:
        return ImageInfoResult(
            success=False,
            path=path,
            error=f"Error reading image: {str(e)}"
        )
```

### Creating Custom Utilities

You can create custom utilities that build on `quackcore.fs`:

```python
from quackcore.fs import service as fs
import hashlib
from typing import List, Dict, Any
import json


class FileIndexer:
  """Index files by content and metadata."""

  def __init__(self, base_dir, index_file="file_index.json"):
    self.base_dir = base_dir
    self.index_file = fs._join_path(base_dir, index_file)
    self.index = self._load_index()

  def _load_index(self):
    """Load the existing index or create a new one."""
    result = fs.read_json(self.index_file)
    if result.success:
      return result.data
    return {"files": {}, "tags": {}}

  def _save_index(self):
    """Save the index to disk."""
    result = fs.write_json(self.index_file, self.index, atomic=True)
    return result.success

  def _compute_file_hash(self, file_path):
    """Compute a hash of the file content."""
    result = fs.read_binary(file_path)
    if not result.success:
      return None

    hash_obj = hashlib.sha256()
    hash_obj.update(result.content)
    return hash_obj.hexdigest()

  def index_file(self, file_path, tags=None):
    """
    Index a file with optional tags.
    
    Args:
        file_path: Path to the file
        tags: List of tags to associate with the file
    
    Returns:
        True if successful, False otherwise
    """
    # Get file info
    info_result = fs.get_file_info(file_path)
    if not info_result.success or not info_result.exists:
      return False

    # Compute a hash of the file
    file_hash = self._compute_file_hash(file_path)
    if not file_hash:
      return False

    # Create the file entry
    rel_path = str(file_path).replace(str(self.base_dir), "").lstrip("/\\")

    file_entry = {
      "path": rel_path,
      "hash": file_hash,
      "size": info_result.size,
      "modified": info_result.modified,
      "tags": tags or []
    }

    # Add to the index
    self.index["files"][rel_path] = file_entry

    # Update tag index
    if tags:
      for tag in tags:
        if tag not in self.index["tags"]:
          self.index["tags"][tag] = []
        if rel_path not in self.index["tags"][tag]:
          self.index["tags"][tag].append(rel_path)

    # Save the updated index
    return self._save_index()

  def find_by_tag(self, tag):
    """Find files by tag."""
    if tag not in self.index["tags"]:
      return []

    files = []
    for rel_path in self.index["tags"][tag]:
      if rel_path in self.index["files"]:
        file_entry = self.index["files"][rel_path]
        abs_path = fs._join_path(self.base_dir, rel_path)
        files.append((abs_path, file_entry))

    return files

  def find_duplicate_files(self):
    """Find duplicate files by hash."""
    hashes = {}
    duplicates = {}

    for rel_path, file_entry in self.index["files"].items():
      file_hash = file_entry["hash"]
      if file_hash in hashes:
        if file_hash not in duplicates:
          duplicates[file_hash] = [hashes[file_hash]]
        duplicates[file_hash].append(rel_path)
      else:
        hashes[file_hash] = rel_path

    return duplicates
```

## Troubleshooting

### Common Issues and Solutions

Here are some common issues you might encounter when using `quackcore.fs` and how to solve them:

#### 1. File not found errors when working with relative paths

**Problem:** You get "File not found" errors even though you're sure the file exists.

**Solution:** Make sure you understand how relative paths are resolved in `quackcore.fs`:

```python
# Bad - uses a relative path that might be relative to the wrong directory
result = fs.read_text("data/config.txt")

# Good - use absolute paths or join with the correct base directory
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
config_path = fs._join_path(base_dir, "data", "config.txt")
result = fs.read_text(config_path)
```

#### 2. Unexpected encoding issues with text files

**Problem:** Text files with non-ASCII characters are not being read or written correctly.

**Solution:** Always specify the encoding explicitly:

```python
# Bad - uses default encoding which might not be UTF-8
result = fs.read_text("international.txt")

# Good - explicitly specify UTF-8 encoding
result = fs.read_text("international.txt", encoding="utf-8")
```

#### 3. Cannot create a directory because the parent directory doesn't exist

**Problem:** Trying to create a directory fails because its parent doesn't exist.

**Solution:** `create_directory` automatically creates parent directories, but explicit is better:

```python
# Ensure all parent directories exist
fs.create_directory("path/to/nested/directory", exist_ok=True)

# Now create a file in this directory
fs.write_text("path/to/nested/directory/file.txt", "content")
```

#### 4. Not checking for success/error in results

**Problem:** Operations fail silently because you're not checking result objects.

**Solution:** Always check the `success` attribute before using the result:

```python
# Bad - assumes success
content = fs.read_text("config.txt").content  # May raise AttributeError if read fails

# Good - checks for success
result = fs.read_text("config.txt")
if result.success:
    content = result.content
else:
    print(f"Error: {result.error}")
    content = None
```

### Debugging Tips

Here are some tips for debugging `quackcore.fs` issues:

1. **Enable verbose logging:**

```python
from quackcore.logging import get_logger, LogLevel

# Set logger to DEBUG level
logger = get_logger(__name__)
logger.setLevel(LogLevel.DEBUG)
```

2. **Use a custom FileSystemService with debugging:**

```python
from quackcore.fs import FileSystemService, service as fs
from quackcore.logging import LOG_LEVELS, LogLevel

# Create a service with debug logging
debug_fs = FileSystemService(log_level=LOG_LEVELS[LogLevel.DEBUG])

# Use this service for debugging
result = debug_fs.read_text("problem_file.txt")
```

3. **Inspect full result objects:**

```python
# Print the entire result object
result = fs.read_text("config.txt")
print(f"Result: {result}")
print(f"Success: {result.success}")
print(f"Path: {result.path}")
print(f"Error: {result.error}")
print(f"Content length: {len(result.content) if result.success else 0}")
```

4. **Test path resolution:**

```python
# Debug path resolution issues
path = "relative/path/to/file.txt"
resolved = fs._normalize_path(path)
print(f"Original: {path}")
print(f"Resolved: {resolved}")
print(f"Absolute: {resolved.is_absolute()}")
print(f"Exists: {resolved.exists()}")
```

## Community Examples and Extensions

Here are some community-contributed examples and extensions for `quackcore.fs`:

### File Watch Service

A service that watches for file changes and runs actions when files change:

```python
import time
import threading
from quackcore.fs import service as fs
from typing import Dict, Callable, Any

class FileWatchService:
    """Service that watches files and runs actions when they change."""
    
    def __init__(self, poll_interval=1.0):
        """
        Initialize the file watch service.
        
        Args:
            poll_interval: How often to check for changes (in seconds)
        """
        self.poll_interval = poll_interval
        self.watched_files = {}  # path -> (timestamp, callback)
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
    
    def start(self):
        """Start watching files."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop watching files."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=self.poll_interval * 2)
    
    def watch(self, path: str, callback: Callable[[str], Any]) -> bool:
        """
        Add a file to watch.
        
        Args:
            path: Path to watch
            callback: Function to call when the file changes
                     The function will be called with the file path
        
        Returns:
            True if the file was added, False otherwise
        """
        info = fs.get_file_info(path)
        if not info.success:
            return False
        
        with self.lock:
            self.watched_files[str(path)] = {
                'timestamp': info.modified if info.exists else 0,
                'callback': callback
            }
        
        if not self.running:
            self.start()
        
        return True
    
    def unwatch(self, path: str) -> bool:
        """
        Remove a file from watching.
        
        Args:
            path: Path to stop watching
        
        Returns:
            True if the file was removed, False if it wasn't watched
        """
        with self.lock:
            if str(path) in self.watched_files:
                del self.watched_files[str(path)]
                return True
        return False
    
    def _watch_loop(self):
        """Main loop for watching files."""
        while self.running:
            self._check_files()
            time.sleep(self.poll_interval)
    
    def _check_files(self):
        """Check all watched files for changes."""
        with self.lock:
            # Make a copy of the watched files to avoid modification during iteration
            files_to_check = self.watched_files.copy()
        
        for path, info in files_to_check.items():
            file_info = fs.get_file_info(path)
            if not file_info.success:
                continue
            
            last_timestamp = info['timestamp']
            current_timestamp = file_info.modified if file_info.exists else 0
            
            # Check if the file has changed
            if current_timestamp > last_timestamp:
                # Update the timestamp
                with self.lock:
                    if path in self.watched_files:  # Check again, it might have been unwatched
                        self.watched_files[path]['timestamp'] = current_timestamp
                
                # Call the callback
                try:
                    info['callback'](path)
                except Exception as e:
                    print(f"Error in file change callback for {path}: {e}")
```

### CSV File Utilities

Utilities for working with CSV files:

```python
from quackcore.fs import service as fs
import csv
from io import StringIO
from typing import List, Dict, Any, Union

def read_csv(
    path: str,
    delimiter: str = ',',
    has_header: bool = True
) -> Union[List[Dict[str, str]], List[List[str]]]:
    """
    Read a CSV file and return its contents.
    
    Args:
        path: Path to the CSV file
        delimiter: Field delimiter
        has_header: Whether the CSV has a header row
    
    Returns:
        If has_header is True, returns a list of dictionaries (one per row)
        If has_header is False, returns a list of lists (one per row)
    """
    result = fs.read_text(path)
    if not result.success:
        raise IOError(f"Failed to read CSV file: {result.error}")
    
    # Parse the CSV
    csv_content = result.content
    csv_file = StringIO(csv_content)
    
    if has_header:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        return list(reader)
    else:
        reader = csv.reader(csv_file, delimiter=delimiter)
        return list(reader)

def write_csv(
    path: str,
    data: Union[List[Dict[str, Any]], List[List[Any]]],
    fieldnames: List[str] = None,
    delimiter: str = ',',
    quoting: int = csv.QUOTE_MINIMAL
) -> bool:
    """
    Write data to a CSV file.
    
    Args:
        path: Path to the CSV file
        data: Data to write (list of dicts or list of lists)
        fieldnames: Column names (required for list of dicts)
        delimiter: Field delimiter
        quoting: CSV quoting style
    
    Returns:
        True if successful, False otherwise
    """
    csv_file = StringIO()
    
    if data and isinstance(data[0], dict):
        # List of dictionaries
        if not fieldnames:
            # If fieldnames not provided, use keys from first dict
            fieldnames = list(data[0].keys())
        
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter=delimiter,
            quoting=quoting
        )
        writer.writeheader()
        writer.writerows(data)
    else:
        # List of lists
        writer = csv.writer(
            csv_file,
            delimiter=delimiter,
            quoting=quoting
        )
        writer.writerows(data)
    
    # Get the CSV content
    csv_content = csv_file.getvalue()
    
    # Write the file
    result = fs.write_text(path, csv_content)
    return result.success

def csv_to_json(csv_path: str, json_path: str, delimiter: str = ',') -> bool:
    """
    Convert a CSV file to JSON.
    
    Args:
        csv_path: Path to the CSV file
        json_path: Path to write the JSON file
        delimiter: CSV field delimiter
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the CSV
        data = read_csv(csv_path, delimiter=delimiter, has_header=True)
        
        # Write as JSON
        result = fs.write_json(json_path, data, indent=2)
        return result.success
    except Exception as e:
        print(f"Error converting CSV to JSON: {e}")
        return False
```

### Directory Synchronization

A utility for synchronizing directories:

```python
from quackcore.fs import service as fs
from typing import List, Dict, Set, Tuple


class DirectorySynchronizer:
  """Utility for synchronizing directories."""

  def __init__(self, source_dir: str, target_dir: str):
    """
    Initialize the synchronizer.
    
    Args:
        source_dir: Source directory
        target_dir: Target directory
    """
    self.source_dir = source_dir
    self.target_dir = target_dir

  def analyze(self) -> Dict[str, List[str]]:
    """
    Analyze the differences between source and target.
    
    Returns:
        Dictionary with lists of files to create, update, and delete
    """
    # Get source files
    source_result = fs.find_files(self.source_dir, "*", recursive=True)
    if not source_result.success:
      raise IOError(f"Failed to list source directory: {source_result.error}")

    # Get target files
    target_result = fs.find_files(self.target_dir, "*", recursive=True)
    if not target_result.success:
      raise IOError(f"Failed to list target directory: {target_result.error}")

    # Convert to relative paths
    source_files = self._get_relative_paths(source_result.files, self.source_dir)
    target_files = self._get_relative_paths(target_result.files, self.target_dir)

    # Find files to create, update, and delete
    to_create = source_files - target_files
    to_delete = target_files - source_files
    to_update = set()

    # Check for updated files
    for rel_path in source_files & target_files:
      source_path = fs._join_path(self.source_dir, rel_path)
      target_path = fs._join_path(self.target_dir, rel_path)

      source_info = fs.get_file_info(source_path)
      target_info = fs.get_file_info(target_path)

      if (source_info.success and target_info.success and
              source_info.modified > target_info.modified):
        to_update.add(rel_path)

    return {
      "create": sorted(list(to_create)),
      "update": sorted(list(to_update)),
      "delete": sorted(list(to_delete))
    }

  def synchronize(self, delete: bool = False) -> Dict[str, int]:
    """
    Synchronize the target directory with the source.
    
    Args:
        delete: Whether to delete files in target that don't exist in source
    
    Returns:
        Statistics about the synchronization
    """
    differences = self.analyze()
    stats = {"created": 0, "updated": 0, "deleted": 0, "errors": 0}

    # Create new files
    for rel_path in differences["create"]:
      source_path = fs._join_path(self.source_dir, rel_path)
      target_path = fs._join_path(self.target_dir, rel_path)

      # Ensure parent directory exists
      parent_dir = fs._join_path(*fs._split_path(target_path)[:-1])
      fs.create_directory(parent_dir, exist_ok=True)

      # Copy the file
      result = fs.copy(source_path, target_path)
      if result.success:
        stats["created"] += 1
      else:
        stats["errors"] += 1

    # Update existing files
    for rel_path in differences["update"]:
      source_path = fs._join_path(self.source_dir, rel_path)
      target_path = fs._join_path(self.target_dir, rel_path)

      # Copy and overwrite
      result = fs.copy(source_path, target_path, overwrite=True)
      if result.success:
        stats["updated"] += 1
      else:
        stats["errors"] += 1

    # Delete files if requested
    if delete:
      for rel_path in differences["delete"]:
        target_path = fs._join_path(self.target_dir, rel_path)

        result = fs.delete(target_path)
        if result.success:
          stats["deleted"] += 1
        else:
          stats["errors"] += 1

    return stats

  def _get_relative_paths(self, paths: List[str], base_dir: str) -> Set[str]:
    """Convert absolute paths to paths relative to base_dir."""
    relative_paths = set()
    base_dir_str = str(base_dir)

    for path in paths:
      path_str = str(path)
      # Remove base directory and any leading slashes
      rel_path = path_str.replace(base_dir_str, "").lstrip("/\\")
      relative_paths.add(rel_path)

    return relative_paths
```

### File Locking Utility

A utility for file locking to coordinate access between processes:

```python
from quackcore.fs import service as fs
import time
import os
import random
from datetime import datetime, timedelta

class FileLock:
    """
    File-based locking utility.
    
    This implements a simple advisory locking system using a lock file.
    It's safe to use across multiple processes but is not thread-safe 
    within the same process (use threading.Lock for that).
    """
    
    def __init__(self, path, timeout=60, retry_delay=0.1):
        """
        Initialize the file lock.
        
        Args:
            path: Path to the file to lock. The lock file will be path + ".lock"
            timeout: Maximum time to wait for the lock (in seconds)
            retry_delay: Time to wait between lock attempts (in seconds)
        """
        self.file_path = path
        self.lock_path = str(path) + ".lock"
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.locked = False
        self.owner = f"{os.getpid()}-{random.randint(1000, 9999)}"
    
    def acquire(self):
        """
        Acquire the lock.
        
        Returns:
            True if the lock was acquired, False otherwise
        
        Raises:
            TimeoutError: If the lock could not be acquired within the timeout
        """
        if self.locked:
            return True
        
        start_time = time.time()
        
        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > self.timeout:
                raise TimeoutError(f"Could not acquire lock for {self.file_path} within {self.timeout} seconds")
            
            # Try to create the lock file
            lock_info = self._read_lock_info()
            
            if lock_info:
                # Lock exists, check if it's stale
                if self._is_lock_stale(lock_info):
                    # Lock is stale, try to break it
                    self._break_lock()
                else:
                    # Lock is valid, wait and retry
                    time.sleep(self.retry_delay)
                    continue
            
            # Try to create the lock
            if self._create_lock():
                self.locked = True
                return True
            
            # If we get here, someone else created the lock just before us
            time.sleep(self.retry_delay)
    
    def release(self):
        """Release the lock."""
        if not self.locked:
            return
        
        # Only delete the lock file if we own it
        lock_info = self._read_lock_info()
        if lock_info and lock_info.get("owner") == self.owner:
            fs.delete(self.lock_path)
        
        self.locked = False
    
    def _create_lock(self):
        """Try to create the lock file."""
        lock_data = {
            "owner": self.owner,
            "created": datetime.now().isoformat(),
            "pid": os.getpid()
        }
        
        # Write the lock file
        result = fs.write_json(self.lock_path, lock_data, atomic=True)
        return result.success
    
    def _read_lock_info(self):
        """Read information from the lock file."""
        result = fs.read_json(self.lock_path)
        if result.success:
            return result.data
        return None
    
    def _is_lock_stale(self, lock_info):
        """Check if a lock is stale (older than timeout)."""
        if not lock_info or "created" not in lock_info:
            return True
        
        try:
            created = datetime.fromisoformat(lock_info["created"])
            now = datetime.now()
            
            # Lock is stale if it's older than the timeout
            return (now - created) > timedelta(seconds=self.timeout)
        except Exception:
            # If we can't parse the date, consider the lock stale
            return True
    
    def _break_lock(self):
        """Break a stale lock."""
        fs.delete(self.lock_path)
    
    def __enter__(self):
        """Context manager protocol: acquire the lock."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager protocol: release the lock."""
        self.release()

# Example usage:
def update_shared_file(path, data):
    """Update a file that might be accessed by multiple processes."""
    with FileLock(path):
        # Read the current content
        result = fs.read_text(path)
        if result.success:
            content = result.content
        else:
            content = ""
        
        # Update the content
        new_content = content + data
        
        # Write back
        fs.write_text(path, new_content)
        
        return True
```

## Conclusion

The `quackcore.fs` module provides a robust, easy-to-use interface for filesystem operations in the QuackVerse ecosystem. By using standardized result objects, proper error handling, and consistent APIs, it offers a significant improvement over the standard library's filesystem modules.

For QuackTool developers, using `quackcore.fs` instead of `pathlib.Path` and other standard library modules leads to more maintainable, safer code with better error handling and a more consistent API. The module's powerful features for structured data, checksums, atomic operations, and detailed file information make it an essential tool in your QuackVerse development toolkit.

By following the patterns and examples in this documentation, you'll be able to build reliable, robust filesystem operations into your QuackTools while avoiding common pitfalls and bugs associated with direct filesystem access.

Happy coding in the QuackVerse!