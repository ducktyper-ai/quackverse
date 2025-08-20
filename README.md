# 🦆 QuackVerse

Welcome to **QuackVerse**, the ecosystem of modular, developer-first tools for building, learning, and teaching with AI.

Whether you're automating metadata extraction, building AI agents, exploring tokenizers, or crafting CLI-based learning experiences — QuackVerse gives you open, structured tools that feel great to use and easy to extend.

---

## 🌐 What's Inside?

| Tool | Description |
|------|-------------|
| [`quackcore`](https://github.com/ducktyper-ai/quackverse/tree/main/quackcore) | The shared foundation for all QuackTools — infrastructure, integrations, protocols |
| [`quacktools/*`](https://github.com/ducktyper-ai) | Modular tools for AI workflows — metadata, prompt engineering, token inspection, and more |
| `quackdata` | Data manipulation tools (coming soon) |
| `quackcloud` | Cloud infrastructure (coming soon) |
| `quackdocs/` | Canonical docs, specs, and implementation guides (coming soon) |

---

## 💡 Philosophy

QuackVerse is inspired by:
- 🧠 **Fast.ai-style teaching**: code-first, hands-on learning
- 🛠️ **Unix-style tools**: each tool does one thing well
- 🧪 **Solo-friendly engineering**: every repo is small, self-contained, and shippable
- 🧑‍🏫 **Gamified learning**: XP, quests, and teaching UX baked into the CLI

---

## 📦 Install & Use

The main entrypoint for the ecosystem is:

```bash
pip install ducktyper
```

Once installed, try:

```bash
ducktyper list
ducktyper run quacktool-name
```

Each tool has its own README with usage examples and learning paths.

### Development Setup

#### Prerequisites

- Python 3.10 or newer
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

#### Quick Start

The fastest way to get started is to use the setup script:

```bash
# Clone the repository
git clone https://github.com/ducktyper-ai/quackverse
cd quackverse

# Run the setup script (creates venv and installs dependencies)
make setup
source setup.sh
```

#### Manual Setup

If you prefer to set up manually:

```bash
# Create a virtual environment
make env
source .venv/bin/activate

# Install all packages with dependencies
make install-all

# Install development tools
make install-dev
```

---

## 🧑‍💻 Development Workflow

### Testing

Run the full test suite:

```bash
make test
```

Run tests for specific packages:

```bash
make test-quack-core
```

### Code Quality

Format your code and run linters:

```bash
make format  # Format code with Ruff and isort
make lint    # Run linters (Ruff, MyPy)
```

Before committing, run all checks:

```bash
make pre-commit
```

### Building and Publishing

To build distribution packages:

```bash
make build
```

To publish to PyPI:

```bash
make publish
```

### Project Structure

To view the current project structure:

```bash
make structure
```

---

## 🛠️ Modern Python Packaging

QuackVerse follows modern Python packaging best practices:
- **Monorepo Structure**: Multiple related packages in a single repository
- **uv for Dependency Management**: Fast, modern Python package installer
- **hatchling for Building**: Modern, extensible build backend
- **Ruff for Linting**: Fast, comprehensive Python linter
- **MyPy for Type Checking**: Static type analysis
- **pytest for Testing**: Comprehensive testing framework

---

## 🔐 Licensing Overview

| Layer | License |
|-------|---------|
| `quackcore`, `ducktyper` | [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.en.html) |
| `quacktools/*` | [BUSL-1.1](https://mariadb.com/bsl11/) (source-available, converts to Apache 2.0 in 3 years) |
| Branding & Mascot | [CC BY-NC-ND](https://creativecommons.org/licenses/by-nc-nd/4.0/) |

See [`LICENSE_POLICY.md`](./LICENSE_POLICY.md) for more details.

---

## 🛠 Contributing

We welcome contributions from educators, hackers, and AI enthusiasts.

- Open issues to request a new QuackTool or learning module
- Use pull requests for bugfixes or enhancements
- Follow us at [aiproduct.engineer](https://aiproduct.engineer)

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

---

## 🐤 Brought to you by

**Rod & the DuckTyper Collective at AI Product Engineer**  
Independent creators building tools for the next generation of AI developers.