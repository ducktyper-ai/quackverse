# 🐣 DuckTyper

**DuckTyper** is the official CLI interface for the [QuackVerse](https://github.com/ducktyper-ai) ecosystem — a growing collection of intelligent, open-source tools for learning, building, and working with AI.

> ✨ Think: `fast.ai` meets `aider.chat`, but fully terminal-native.

---

## 🚀 What is DuckTyper?

DuckTyper is a **modular CLI assistant** that:
- Helps you **learn AI** hands-on via gamified tutorials, quests, and challenges.
- Gives you access to **QuackTools** — composable microtools for real-world GenAI, ML, and data workflows.
- Powers solo devs, indie researchers, and AI learners with an elegant command-line experience.

---

## 🧰 Features

- 🧩 **Plugin-based**: Dynamically discover and run any QuackTool.
- 🎓 **Teaching Mode**: Interactive challenges, XP, badges, and CLI-first tutorials.
- 📦 **MCP Compliant**: Speak the [Model Context Protocol](https://docs.anthropic.com/mcp) to interoperate with cutting-edge agents and runtimes.
- 📚 **Offline-first learning**: No browser needed — learn AI fully in your terminal.
- 🔌 **Integrates with QuackCore**: All logic handled in the powerful core engine.

---

## 🐤 Install

```bash
pip install ducktyper
```

> Requires Python 3.10+

---

## 🏁 Quickstart

```bash
ducktyper list          # See available tools
ducktyper run quackprompt --help     # Run a specific QuackTool
ducktyper teach quackprompt          # Start a tutorial with badges + XP
```

Or try your first tutorial:

```bash
ducktyper learn langgraph
```

---

## 📦 QuackTools

DuckTyper works by orchestrating **QuackTools** — modular tools that do one thing really well.

| Tool | Description |
|------|-------------|
| `quackprompt` | Boost and refactor your prompts using templates + LLMs |
| `quackmetadata` | Extract metadata from Google Docs with LLMs |
| `quacktokenscope` | Compare tokenization across different libraries |
| `quacktutorial` | Author AI tutorials in `.py` format |
| `quackresearch` | Digest newsletters and trends |
| `quackvideo` | Automate video postproduction using subtitles + AI |

More at [github.com/quackverse](https://github.com/quackverse)

---

## 🧠 Teaching Mode

Every tool can be run in `--teach` mode:

```bash
ducktyper run quackprompt --teach
```

This enables:
- 🧩 Step-by-step walkthroughs
- ✅ Concept checks and quizzes
- 💯 XP and badge tracking
- 🦆 Progress stored locally in `.duckprogress.json`

---

## 🏗️ Developer Guide

Want to build your own QuackTool?

```bash
ducktyper dev init mycooltool
cd mycooltool
ducktyper dev test
```

Tools follow the [QuackTool Manifesto](https://github.com/ducktyper-ai/.github/blob/main/MANIFESTO.md): small, composable, and educational.

---

## 🧪 Experimental

DuckTyper is under active development.

Want to contribute, test edge tools, or help shape the CLI experience?

Join us at [AI Product Engineer](https://aiproduct.engineer)

---

## 🦆 About the QuackVerse

QuackVerse is an open ecosystem for building and teaching with AI. It includes:

- `quackcore` — Core infrastructure (open-source)
- `ducktyper` — CLI UX for learners and devs
- `quacktools` — Plugin tools for GenAI, agents, LLMs, etc.
- `AI Product Engineer` — A visual learning platform built on top of this stack

---

## 🐣 Ready to learn?

```bash
ducktyper learn intro
```

---

> 🧙‍♂️ Powered by `quackcore`. Guided by `Quackster` the Ducktyper, the duck AI mage.  
> For serious learners with a playful heart.
```

---

---

# 🦆 QuackVerse Licensing Overview

QuackVerse is a modular ecosystem with mixed licensing to balance community contribution and project protection.

### 🔓 Open Source (with strong copyleft)
- **Repositories**: `quackcore`, `ducktyper`
- **License**: [GNU Affero General Public License v3.0 (AGPL-3.0)](https://www.gnu.org/licenses/agpl-3.0.en.html)
- **Why?** This license ensures that any public use of these tools — including SaaS or hosted services — must release the source code and improvements back to the community.

### 🔐 Source-Available (with delayed open-source)
- **Repositories**: All `quacktools/*`
- **License**: [Business Source License 1.1 (BUSL-1.1)](https://mariadb.com/bsl11/)
- **What does this mean?**
  - You can **view, fork, and modify** the code.
  - **Production or commercial use is not allowed** unless you obtain a commercial license from us.
  - The license **automatically converts to Apache 2.0 after 3 years**, ensuring long-term openness.
- A short human summary is provided in each tool's README.

### 🎨 Brand and Creative Assets
- **Assets**: Logos, Mascot (Quackster), design elements
- **License**: [Creative Commons Attribution-NonCommercial-NoDerivs 4.0 (CC BY-NC-ND 4.0)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
- **You may not** redistribute, remix, or use our branding for commercial purposes.

---

### 🧠 Why this setup?

We love open-source and education. However, to continue building high-quality learning tools, we need to protect our work from being commercialized or rebranded by others without contributing back. Our structure enables:
- A healthy developer community.
- Opportunities for contributors to shape the future.
- Commercial protection for sustainability.

We welcome pull requests, issues, and feedback. If you're interested in **commercial use**, please reach out via [rod@aip.engineer](mailto:rod@aip.engineer).


---

## 💬 Questions?

Tweet at [@aipengineer](https://twitter.com/aipengineer) or file an issue on GitHub!