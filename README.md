# 🦆 QuackCore

## Python Infrastructure for Media Production Automation

QuackCore is a foundational library that provides shared infrastructure for the Quack ecosystem of media production tools. It centralizes common functionality like path resolution, configuration management, and plugin architecture to enable seamless integration between specialized tools.

## 🌟 Features

- **Unified Path Management**: Robust system for resolving and managing paths across different operating environments
- **Configuration Framework**: Flexible configuration with environment-specific overrides
- **Plugin Architecture**: Extensible system for registering commands and workflows
- **Workflow Engine**: Chain operations together into repeatable workflows
- **Command Registry**: Central registry for commands from all Quack modules
- **Utilities**: Common utilities for file operations, logging, error handling, and more
- **Testing Framework**: Shared testing infrastructure for all Quack modules
- **Integrations**: Integrate with the ecosystem such as Google Drive, Google Mail and Notion for upload and download

## 🧩 Core Modules

- **paths**: Path resolution and manipulation utilities
- **config**: Configuration management
- **plugins**: Plugin discovery and registration
- **commands**: Command registry and execution
- **workflows**: Workflow definition and execution
- **logging**: Structured logging framework
- **utils**: Shared utility functions

## ⚙️ Integration

QuackCore serves as the foundation for all Quack ecosystem tools:

- **QuackImage**: Social media image generation
- **QuackDistro**: Text generation for social media from transcripts
- **QuackVideo**: Social media video production
- **QuackTutorial**: Educational programming tutorial generation
- **QuackBuddy**: Interactive CLI assistant that ties everything together

## 🚀 Getting Started

```bash
pip install quackcore
```

```python
from quackcore.paths import PathResolver
from quackcore.config import ConfigManager

# Initialize with project configuration
config = ConfigManager("my_project")
resolver = PathResolver(config.get_config())

# Resolve project paths
media_path = resolver.get_media_path("my_project", "episode_5", "video")
```

## 📚 Example: Adding Commands

```python
from quackcore.commands import CommandRegistry

@CommandRegistry.register(
    "generate_thumbnails",
    help_text="Generate thumbnails from video",
    category="Media"
)
def generate_thumbnails(video_path, output_dir, count=3):
    """Generate thumbnail candidates from video."""
    # Implementation
    pass
```

## 📦 Project Structure

```
├── LICENSE
├── Makefile
├── README.md
├── pyproject.toml
└── src
    └── quackcore
        ├── __init__.py
        ├── config
        │   ├── __init__.py
        │   ├── loader.py
        │   ├── models.py
        │   ├── plugin.py
        │   └── utils.py
        ├── errors
        │   ├── __init__.py
        │   ├── base.py
        │   └── handlers.py
        ├── fs
        │   ├── __init__.py
        │   ├── operations.py
        │   ├── plugin.py
        │   ├── results.py
        │   ├── service.py
        │   └── utils.py
        ├── paths
        │   ├── __init__.py
        │   ├── context.py
        │   ├── plugin.py
        │   ├── resolver.py
        │   └── utils.py
        └── plugins
            ├── __init__.py
            ├── discovery.py
            ├── protocols.py
            └── registry.py

```

## 💻 Requirements

- Python 3.13+
- Pydantic
- Click
- Rich

## 🔧 Development

```bash
# Clone the repository
git clone https://github.com/rodmtech/quackcore.git
cd quackcore

# Install development dependencies
python -m pip install -e ".[dev]"

# Run tests
pytest
```

## 📄 License

GNU Alfero
