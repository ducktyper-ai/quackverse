# 🦆 QuackVerse

Welcome to **QuackVerse**, the ecosystem of modular, developer-first tools for building, learning, and teaching with AI.

Whether you're automating metadata extraction, building AI agents, exploring tokenizers, or crafting CLI-based learning experiences — QuackVerse gives you open, structured tools that feel great to use and easy to extend.

---

## 🌐 What’s Inside?

| Tool | Description |
|------|-------------|
| [`quackcore`](https://github.com/ducktyper-ai/quackverse/quackcore) | The shared foundation for all QuackTools — infrastructure, integrations, protocols |
| [`ducktyper`](https://github.com/ducktyper-ai/quackverse/ducktyper) | The unified CLI experience to run, learn from, and interact with QuackTools |
| [`quacktools/*`](https://github.com/ducktyper-ai) | Modular tools for AI workflows — metadata, prompt engineering, token inspection, and more |
| `quackdocs/` | Canonical docs, specs, and implementation guides (coming soon) |
| `quackbrand/` | Mascots, design assets, and licensing guidelines |

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
pip install tests
```

Once installed, try:

```bash
tests list
tests run quacktool-name
```

Each tool has its own README with usage examples and learning paths.

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
- Follow us at [ducktyper.ai](https://ducktyper.ai)

---

## 🐤 Brought to you by

**Rod & the DuckTyper Collective at AI Product Engineer**  
Independent creators building tools for the next generation of AI developers.

```

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