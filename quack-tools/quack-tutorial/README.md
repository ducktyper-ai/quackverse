# 🦆 QuackTutorial

**A QuackTool for Authoring and Compiling Tutorial Artifacts**

> **QuackTutorial turns tutorial source files into structured, auditable artifacts (MDX + manifests).**
> It is a deterministic worker in the QuackVerse toolchain — not a learning platform.

---

## 🧠 What QuackTutorial Is

QuackTutorial is a **Ring B QuackTool**.

It consumes **tutorial source** (primarily Python) and emits:

* **MDX pages**
* **metadata manifests**
* **navigation structures**
* **asset references / bundles**

QuackTutorial answers one question:

> **“Given these tutorial inputs, produce these tutorial artifacts.”**

---

## ❌ What QuackTutorial Is Not

QuackTutorial does **not**:

* orchestrate workflows
* track learners or progress
* run quizzes, grading, or XP systems
* host a UI
* decide what should be taught
* publish to external systems directly

Those belong to Ring C (Quackchat/Agents/Temporal) and integration fabrics (n8n / integrations).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackTutorial ◀                  │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: FS · Config · Results · Schemas│
└────────────────────────────────────────────┘
```

QuackTutorial:

* imports **QuackCore only**
* is executed locally via `quack` or remotely via **QuackRunner**
* communicates via **artifacts + manifests**

---

## 🧰 Canonical CLI Surface

QuackTutorial does **not** expose its own CLI.

The **only** entry point is the canonical QuackVerse CLI:

```bash
quack tutorial <verb> [options]
```

Every QuackTool implements the standard verbs:

* `run`
* `validate`
* `doctor`
* `explain`

QuackTutorial also provides a small set of domain verbs (below), but they still live under `quack tutorial …`.

---

## 🚀 Common Commands

### Compile a tutorial to artifacts

```bash
quack tutorial run tutorial.py --out ./dist/tutorials
```

Produces a deterministic output bundle (MDX + manifests + assets).

### Validate tutorial inputs (schemas + structure)

```bash
quack tutorial validate tutorial.py
```

Checks:

* required headers / markers
* metadata shape
* component references
* output determinism constraints

### Diagnose environment readiness

```bash
quack tutorial doctor
```

Reports:

* Python environment checks
* optional dependencies (MDX tooling, image tooling, etc.)
* output directory permissions
* config resolution

### Explain an output bundle

```bash
quack tutorial explain ./dist/tutorials/<slug>/
```

Explains:

* what was generated
* where the manifest is
* how downstream systems should consume it

---

## 🧩 Domain Verbs (Tool-Specific)

Depending on configuration, QuackTutorial may expose additional verbs, still under the canonical surface:

```bash
quack tutorial convert tutorial.py --out ./dist/tutorials
quack tutorial metadata tutorial.py --out ./dist/metadata
quack tutorial batch ./src --out ./dist/tutorials
quack tutorial scaffold learning-path lp-langgraph
quack tutorial scaffold unit 01_state_fundamentals
quack tutorial scaffold lesson 01_intro --unit 01_state_fundamentals
quack tutorial rename unit 01_state 01_state_basics
quack tutorial rename lesson 01_intro 01_foundations --unit 01_state_basics
```

**Important doctrine note:** scaffolding and renames are **authoring ergonomics** (filesystem structure), not “course runtime”.

---

## 📚 Tutorial Source Format

QuackTutorial’s source of truth is code-first tutorial files (Python).

A typical source uses:

* docstring header for title/description
* cell markers / markdown blocks
* optional component markers

Example:

```python
"""
Tutorial Title
=============

A short description of what this tutorial covers.

Prerequisites:
- Topic 1
- Topic 2

Tags: langgraph, agents, beginner
"""

# %% [markdown]
# ## Introduction
# This is a markdown section.

# %%
print("Hello, QuackVerse!")

# %% [markdown]
# [component: attention-mechanism.tsx]
```

---

## 📦 Output Artifacts

QuackTutorial emits an **artifact bundle** with a manifest as the source of truth.

Example output:

```text
dist/
└── tutorials/
    └── tutorial-title/
        ├── page.mdx
        ├── manifest.json
        ├── metadata.yaml
        ├── navigation.json
        └── assets/
            └── banner.webp
```

### The Manifest Is Canonical

If it didn’t emit a manifest, **it didn’t happen**.

Downstream systems (Quackchat, QuackRunner, agents, docs sites) consume:

* `manifest.json` (canonical index)
* referenced artifacts (MDX, assets, metadata)

---

## 🔗 How QuackTutorial Fits into Larger Workflows

QuackTutorial never orchestrates. It is invoked by Ring C.

Example flow:

1. **Quackchat** triggers a “publish tutorial” intent
2. **Temporal** coordinates workflow state + approvals
3. **QuackRunner** executes `quack tutorial run …`
4. Outputs land in the artifact store with a manifest
5. **Agents** may propose next steps (publish, link, promote)
6. **n8n / integrations** perform side effects (upload, notify, update CRM)

QuackTutorial stays deterministic and stateless across runs.

---

## ⚙️ Configuration

QuackTutorial is configured via the QuackVerse configuration system (QuackCore):

* YAML configuration
* typed validation
* consistent result envelopes

Example (indicative):

```yaml
tutorial:
  output:
    format: mdx
    banner: true
  metadata:
    infer_difficulty: true
    estimate_time: true
  markers:
    enabled: true
```

---

## 🧭 Governance Rules

1. QuackTutorial is a worker, not a platform
2. No orchestration — Temporal owns sequencing
3. No external side effects — integrations handle publishing
4. Emits artifacts + manifest as system of record
5. Uses QuackCore only
6. Runs via the canonical `quack` CLI only

---

## 🧠 Closing Statement

QuackTutorial is a **content compiler** for the QuackVerse.

It transforms tutorial source into structured artifacts that can be:

* rendered by Quackchat
* published by docs systems
* orchestrated by Temporal
* executed via QuackRunner
* interpreted by agents

It doesn’t teach.

It enables everything that does.

---
