<!--
================================================================================
DuckTyper — The Terminal-Native AI CLI
================================================================================
-->

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.en.html)  
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)  
[![PyPI](https://img.shields.io/pypi/v/ducktyper.svg)](https://pypi.org/project/ducktyper/)  
[![Documentation](https://img.shields.io/badge/Docs-QuackVerse-brightgreen.svg)](https://github.com/ducktyper-ai)  

---

# 🐣 DuckTyper

**Terminal-native AI tooling for learners, developers, and researchers.**  
*A fast.ai–style learning experience meets an aide.chat–style assistant, all without leaving your shell.*

DuckTyper is the official CLI for the [QuackVerse](https://github.com/ducktyper-ai) ecosystem:  
a modular, plugin‑based suite of microtools, gamified tutorials, and teaching modes for hands‑on AI education.

---

## 🚀 Key Highlights

- **Plugin‑based Architecture**  
  Dynamically discover and invoke any installed QuackTool.
- **Teaching Mode**  
  Gamified, CLI‑first tutorials with step‑by‑step guidance, XP, badges, and quizzes.
- **MCP‑Compliant**  
  Speak the [Model Context Protocol (MCP)](https://docs.anthropic.com/mcp) for seamless agent integration.
- **Offline‑First Learning**  
  Master AI and ML concepts entirely in your terminal, no browser required.
- **QuackCore Integration**  
  Leverage QuackCore to power all the heavy lifting behind the scenes.

---

## 📦 Installation

Requires **Python 3.10+** and pip:

```bash
pip install tests
```

---

## 🏁 Quickstart

```bash
# List all available QuackTools
tests list

# Get help for a specific tool
tests run quackprompt --help

# Start an interactive teaching tutorial
tests teach quackprompt

# Begin your first learning quest
tests learn intro
```

---

## 🔧 Core Commands

| Command                             | Description                                         |
|-------------------------------------|-----------------------------------------------------|
| `ducktyper list`                    | Show installed QuackTools                           |
| `ducktyper run <tool> [--help]`     | Run a specific QuackTool                           |
| `ducktyper teach <tool>`            | Launch Teaching Mode for a tool                    |
| `ducktyper learn <topic>`           | Start a guided tutorial or quest                    |
| `ducktyper assistant`               | Enter AI Assistant mode in your terminal            |
| `ducktyper config edit`             | Open DuckTyper configuration                        |
| `ducktyper certify [options]`       | Generate completion certificates (ASCII, Markdown, SVG) |
| `ducktyper xp [--history|--achievements|--all]` | View XP, badges, and progress stats      |

---

## 🧰 QuackTools

QuackTools are lightweight, purpose‑built plugins. Install additional tools via pip or clone from [QuackVerse](https://github.com/ducktyper-ai/quacktools). Examples:

| Tool               | Description                                               |
|--------------------|-----------------------------------------------------------|
| **quackprompt**    | Boost, refactor, and test your prompts with templates and LLMs |
| **quackmetadata**  | Extract structured metadata from Google Docs via AI       |
| **quacktokenscope**| Compare tokenization across different libraries           |
| **quacktutorial**  | Author interactive AI tutorials in Python                |
| **quackresearch**  | Summarize newsletters, articles, and AI trends           |
| **quackvideo**     | Automate video post‑production using subtitles and AI     |

_For the full list, run `ducktyper list`._

---

## 🎓 Teaching Mode

Every tool supports a **–‑teach** flag for an immersive learning experience:

```bash
tests run quackprompt --teach
```

- **Step‑by‑Step Walkthroughs**  
- **Concept Checks & Quizzes**  
- **XP & Badge Tracking**  
- **Local Progress Saved** in `.duckprogress.json`

Earn XP by completing challenges, leveling up like a CLI‑based RPG!

---

## 🏗️ Developer Guide

Build your own QuackTool in minutes:

```bash
# Scaffold a new tool
tests dev init mycooltool

# Enter your tool’s directory
cd mycooltool

# Run tests
tests dev test
```

Tools follow the **QuackTool Manifesto**:  
> *Small, composable, educational.*

See [the manifesto](https://github.com/ducktyper-ai/.github/blob/main/MANIFESTO.md) for guidelines.

---

## 🎮 Production Mode

For CI/CD and automation:

```bash
# One-off command
tests --mode=production list

# Or set globally
export DUCKTYPER_MODE=production
```

- **Minimal, Clean Output**  
- **No Animations or Decorations**  
- **Ideal for Scripts and Pipelines**

---

## 📜 Licensing

DuckTyper and QuackCore are **AGPL‑3.0** licensed to ensure community contributions remain open:

> **GNU Affero General Public License v3.0**  
> Any public or network use must release source code and improvements.

**QuackTools** (under `ducktyper-ai/quacktools/*`) are **Business Source License 1.1 (BSL‑1.1)**:  
- View, fork, modify code  
- Production/commercial use requires a commercial license  
- Reverts to Apache 2.0 after 3 years

**Brand & Creative Assets** (logos, mascots) are **CC BY‑NC‑ND 4.0**:  
> Attribution‑NonCommercial‑NoDerivs. No commercial redistribution or remixing.

---

## 🤝 Contributing & Support

We welcome your feedback, issues, and pull requests!  
- File issues and PRs on [GitHub](https://github.com/ducktyper-ai/ducktyper)  
- Chat with us on the repo discussions  
- Tweet at [@aipengineer](https://twitter.com/aipengineer)

For commercial licensing inquiries, contact:  
rod@aip.engineer

---

## 📌 Quick Reference

```bash
# List QuackTools
tests list

# Run a tool
tests run quackmetadata

# Learn about a tool
tests explain quackmetadata

# Open interactive assistant
tests assistant

# Configure settings
tests config edit

# Generate certificates
tests certify --name "Your Name" --github "yourusername" --course "QuackVerse Advanced"

# View XP & achievements
tests xp --all
```

---

> 🦆 **DuckTyper** — lightweight, gamified, and terminal‑native AI tooling for serious learners with a playful heart!  
> *Powered by QuackCore. Guided by Quackster the AI mage.*
