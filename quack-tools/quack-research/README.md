# 🦆 QuackResearch

**A QuackTool for Deterministic Research Extraction, Structuring, and Signal Generation**

> **QuackResearch converts raw information streams into structured research artifacts.**
> It does not decide strategy. It does not plan calendars. It does not publish content.

---

## 🧠 What QuackResearch Is

QuackResearch is a **Ring B QuackTool**.

It consumes **authoritative information sources** (emails, feeds, documents, web pages) and produces **structured research artifacts**, such as:

* research briefs
* topic clusters
* trend snapshots
* outlines and evidence packs
* citation-backed summaries

Each run emits:

* research artifacts
* a manifest describing provenance, sources, and transformations

QuackResearch answers one question only:

> **“Given these sources and parameters, what structured research artifacts can be derived?”**

---

## ❌ What QuackResearch Is Not

QuackResearch is **not**:

* a personal research assistant
* a content strategy engine
* a planner or scheduler
* a publishing system
* a CRM or knowledge base
* an agent with judgment

It never:

* decides what topic to pursue
* prioritizes business goals
* schedules content
* publishes outputs
* calls other tools
* mutates canonical state

Those responsibilities live in **Ring C** (Agents, Temporal, Quackchat, n8n).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackResearch ◀                  │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: FS · Config · Results · IO     │
└────────────────────────────────────────────┘
```

QuackResearch:

* imports **QuackCore only**
* runs through **QuackRunner**
* emits **artifacts + manifest**
* is stateless across runs

---

## 🧰 Canonical CLI Surface

QuackResearch does **not** expose its own standalone CLI.

All execution uses the **single canonical CLI**:

```bash
quack research <verb> [options]
```

All QuackTools implement the same verbs:

* `run`
* `validate`
* `doctor`
* `explain`

---

## 🚀 Common Commands

### Run a research extraction

```bash
quack research run sources.yaml --out ./dist/research
```

Produces:

* structured research artifacts
* citations and references
* a manifest recording all derivations

---

### Validate sources and configuration

```bash
quack research validate sources.yaml
```

Checks:

* source accessibility
* schema correctness
* authentication presence
* determinism guarantees

---

### Diagnose environment readiness

```bash
quack research doctor
```

Reports:

* email / feed access readiness
* parser availability
* NLP dependencies
* configuration health

---

### Explain a research bundle

```bash
quack research explain ./dist/research/<run-id>/
```

Explains:

* what sources were consumed
* how signals were extracted
* how topics were clustered
* how downstream systems should consume outputs

---

## 🔍 Inputs

Typical inputs include:

* email archives (e.g. newsletters)
* RSS / Atom feeds
* web pages
* document collections
* metadata about audience or domain (optional)

All inputs are treated as **immutable source artifacts**.

---

## 📦 Output Artifacts

Each run produces a **research artifact bundle** with a canonical manifest.

Example:

```text
dist/
└── research/
    └── run-2025-03-21T16-12-44/
        ├── briefs/
        │   └── llm-inference-optimization.md
        ├── clusters/
        │   └── inference-techniques.json
        ├── trends/
        │   └── weekly-signals.json
        ├── outlines/
        │   └── tutorial-outline.md
        ├── references/
        │   └── citations.bib
        └── manifest.json
```

### Manifest Is the System of Record

The `manifest.json` captures:

* source identifiers and hashes
* extraction parameters
* derived artifacts
* timestamps and checksums
* traceability to inputs

If it is not in the manifest, **it did not happen**.

---

## 🔗 How QuackResearch Fits into Workflows

QuackResearch is always invoked **by orchestration**, never by other tools.

Typical flow:

1. **Quackchat** captures intent (“research this topic”)
2. **Temporal** manages workflow state and approvals
3. **QuackRunner** executes `quack research run`
4. Artifacts + manifest are written
5. **Agents** interpret findings and propose decisions
6. Downstream tools consume outputs:

   * **QuackDistro** → content derivation
   * **QuackTutorial** → educational structure
   * **QuackVideo** → scripting inputs
   * **QuackImage** → visual context

QuackResearch never crosses these boundaries.

---

## ⚙️ Configuration (Indicative)

Configuration uses **QuackCore primitives** and is injected at runtime.

```yaml
research:
  sources:
    email:
      provider: gmail
      labels: ["AI/Newsletters"]
    feeds:
      - https://arxiv.org/list/cs.AI/recent
  outputs:
    - briefs
    - clusters
    - trends
  language: en
```

Configuration is:

* typed
* validated
* auditable
* environment-agnostic

---

## 🧭 Governance Rules

1. QuackResearch is a research derivation worker
2. No strategy or prioritization
3. No publishing or scheduling
4. No SaaS side-effects
5. Emits artifacts + manifest
6. Uses QuackCore only
7. Runs via `quack` CLI

---

## 🧠 Closing Statement

QuackResearch does not “think”.

It **extracts, structures, and preserves knowledge** so thinking can happen elsewhere.

In the DuckTyper AI Operating System:

* Agents decide what matters
* Temporal decides when
* n8n executes side-effects
* **QuackResearch turns noise into evidence**

It is the research substrate for AI-first organizations —
auditable, repeatable, and replaceable.