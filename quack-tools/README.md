# 🛠️ **QuackTools**

**Deterministic Workers of the QuackVerse**

> **Tools do the work.**
> They do not decide *what* to do.
> They do not decide *when* to do it.
> They do not talk to each other.
>
> QuackTools exist to **turn structured inputs into structured outputs — reliably and repeatably**.

---

## 🧠 What QuackTools Are

**QuackTools are atomic, domain-focused workers** in the QuackVerse.

Each QuackTool:

* performs **one well-defined job**
* consumes **structured inputs**
* produces **artifacts + manifests**
* is **deterministic** given the same inputs
* is **stateless across runs**
* imports **QuackCore only**

QuackTools answer one question:

> **“Given these inputs, produce these outputs.”**

---

## ❌ What QuackTools Are Not

QuackTools are **not**:

* agents
* planners
* workflow engines
* orchestrators
* integration hubs
* CRMs
* documentation systems
* UIs
* long-running services

They **never**:

* decide which tool to run
* sequence steps
* retry or backoff
* call other tools
* update business systems
* store canonical state
* talk to SaaS APIs directly (except where explicitly allowed by contract)

Those responsibilities live elsewhere by doctrine.

---

## 🧭 Position in the QuackVerse

QuackVerse is structured as three rings:

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES                │
│  Temporal · n8n · QuackRunner · Agents     │
│  Quackchat                                │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│  QuackVideo · QuackImage · QuackQuote     │
│  QuackMachinima · QuackTutorial · …        │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: Contracts · Capabilities       │
│  Config · IO · Registries · Teaching       │
└────────────────────────────────────────────┘
```

**QuackTools live entirely in Ring B.**

They are called *by* orchestration layers — never the other way around.

---

## 🧠 Core Responsibilities

QuackTools are responsible for **execution only**.

### Tools Do

* validate inputs
* perform a bounded transformation
* generate artifacts (files, media, data)
* emit a manifest describing outputs
* report structured results and errors
* be safe to retry

### Tools Do Not

* plan workflows
* apply judgment
* manage retries
* pause for approval
* mutate CRM or docs
* call external systems ad-hoc
* remember past runs

---

## 🧠 Tools vs Agents (Critical Distinction)

| Aspect  | Tool                  | Agent                 |
| ------- | --------------------- | --------------------- |
| Purpose | Execute               | Decide                |
| State   | Stateless             | Long-lived            |
| Logic   | Deterministic         | Heuristics & policy   |
| Inputs  | Structured            | Contextual            |
| Outputs | Artifacts + manifests | Decisions + rationale |
| Calls   | ❌ Never calls tools   | ❌ Never runs tools    |

> **Agents choose. Tools produce.**

---

## 🧠 Tools vs Infrastructure

| Concern        | Tool                        | Infrastructure     |
| -------------- | --------------------------- | ------------------ |
| Deployment     | Ephemeral                   | Long-lived         |
| State          | Per run only                | Persistent         |
| Responsibility | One job                     | System wiring      |
| Examples       | Video cut, quote generation | CRM, docs, storage |

If multiple workflows depend on it → **it’s infrastructure, not a tool**.

---

## 🧠 Execution Model

QuackTools are **never run directly** in production.

Canonical execution path:

```
Temporal → QuackRunner → QuackTool
```

* **Temporal** owns sequencing and retries
* **QuackRunner** owns execution, logs, and artifacts
* **QuackTool** performs the job and exits

Tools do **not** know:

* who called them
* why they were called
* what happens next

---

## 🧠 Artifacts & Manifests

Every QuackTool **must emit artifacts and a manifest**.

### Artifacts

* files (video, images, PDFs, JSON, etc.)
* written to object storage
* immutable per run

### Manifests

* describe what was produced
* include metadata (params, versions, hashes)
* are the system of record for integration
* are readable by agents and humans

> **If a tool didn’t emit a manifest, it didn’t happen.**

---

## 🧠 Tool Interface Doctrine

### One Canonical CLI

All tools expose functionality through the **canonical `quack` CLI**:

```
quack <tool> <verb> [options]
```

Examples:

* `quack video cut`
* `quack image thumbnail`
* `quack quote generate`
* `quack machinima render`

Tools **register commands** — they do not define their own CLIs.

---

### Required Verbs

Every QuackTool must implement:

* `run` — execute the job
* `validate` — validate inputs
* `doctor` — check environment & dependencies
* `explain` — describe what the tool does and produces

This is **non-negotiable**.

---

## 📦 Repository Structure

```text
quack-tools/
├── quack-video/
│   ├── src/
│   ├── schemas/
│   ├── tests/
│   └── README.md
│
├── quack-image/
├── quack-quote/
├── quack-machinima/
├── quack-tutorial/
│
└── README.md
```

Each tool:

* is a standalone package
* imports **QuackCore**
* exposes a CLI entry
* has no dependency on other tools
* can be versioned independently

---

## 🔗 Relationship to Other QuackVerse Components

| Component           | Role                             |
| ------------------- | -------------------------------- |
| **QuackCore**       | Schemas, contracts, result types |
| **QuackRunner**     | Execution & artifact indexing    |
| **Temporal**        | Workflow sequencing              |
| **Agents**          | Decision making                  |
| **n8n**             | Side effects                     |
| **Quackchat**       | Human steering                   |
| **Quackshowrunner** | Deployment & ops                 |

QuackTools depend on **QuackCore only**.

---

## 🎓 Pedagogical Mandate

QuackTools are **teaching primitives**.

They should make clear:

* what problem is being solved
* what inputs are required
* what outputs are produced
* what assumptions exist
* how failure is handled

A tool that hides complexity instead of exposing it is considered broken.

---

## 🧭 Governance Rules (Non-Negotiable)

1. Tools never orchestrate
2. Tools never call tools
3. Tools never contain judgment
4. Tools never mutate business systems
5. Tools are stateless across runs
6. Tools emit artifacts + manifests
7. Tools are CLI-first
8. One job per tool
9. Determinism over cleverness

---

## 🧠 Closing Statement

**QuackTools are the hands of the organization.**

They swing the hammer,
cut the video,
generate the quote,
render the scene.

They do not plan the job.
They do not decide the order.
They do not keep the books.

That separation is what makes the QuackVerse
**scalable, auditable, teachable — and sovereign**.