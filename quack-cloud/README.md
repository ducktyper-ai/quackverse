# 🌩️ QuackCloud

**QuackCloud** is the official QuackVerse module for working with cloud-based services like Google Calendar, Google Drive, and Notion. It provides developer-friendly functions and plugin-registered integrations designed to automate cloud workflows and enable smart data exchange between local tools and third-party platforms.

---

## 🚀 What It Does

This module exposes high-level, opinionated functions that abstract away the underlying API logic from tools and CLI scripts. All low-level adapters live under `/integrations` and are reused here to create:

- 📅 Calendar automation (e.g., read/write events from Google Calendar)
- 📂 Drive automation (e.g., upload/download files, sync folders)
- 🧠 Notion automation (e.g., create databases, update pages)

---

## 📦 Folder Structure

```
src/quackcloud/
├── __init__.py
├── drive.py            # High-level file/folder logic for Google Drive
├── calendar.py         # High-level event and schedule logic
├── notion.py           # Abstractions for Notion workspace automation
└── plugins.py          # Registers quackcore-compatible plugins
```

---

## 🔌 Plugin Registration

QuackCloud integrates with the `quack_core.integrations.core` plugin system:

```python
from quack_core.integrations.core import register_plugin

@register_plugin("google_drive")
def register_drive():
    return GoogleDriveIntegration()
```

This makes the integration auto-discoverable by DuckTyper and other QuackTools.

---

## 🧰 Usage Example

```python
from quackcloud.drive import upload_file

upload_file(
    local_path=\"/tmp/report.pdf\",
    remote_folder_id=\"1AbCDeFgHiJKLm\"
)
```

---

## 📚 When to Use QuackCloud

Use this module if you're building a tool that:
- Syncs content from/to Google services
- Logs or extracts data from Notion
- Automates personal cloud workflows for indie devs

Avoid using raw clients from `integrations/` unless you're contributing or building internal logic.

---

## 🧪 Tests

Unit tests should live under `tests/quackcloud/` and use `mock_integration()` for credentials.

---

## ✨ Goals

QuackCloud should feel like a **developer superpower** for solo hackers who want to automate cloud workflows using Python. It is designed to be:
- Friendly
- Forkable
- Teachable via DuckTyper