# 🦆 DuckTyper

**The AI Operating System for Knowledge Work**

> **Open-source the engine.  
> Standardize the contracts once.  
> Orchestrate durably.  
> Integrate externally.  
> Keep stories and courses proprietary.**
 
DuckTyper is built on **QuackVerse** — an internal architectural doctrine
that defines how AI-first organizations are structured, governed, and run.


DuckTyper enables building **AI-first organizations** that are:

- **auditable** (artifacts + manifests are the system of record)
- **durable** (workflow state is owned by Temporal)
- **sovereign** (portable infrastructure, minimal SaaS lock-in)
- **teachable** (white-box by default)

This is **not** a chatbot framework.  
DuckTyper is **organizational infrastructure**.

---

## ✨ One Sentence

**DuckTyper turns AI from demos into operating reality by separating kernel contracts, deterministic workers, 
and durable orchestration — and wiring them together safely.**

---

## 🧭 System Model (QuackVerse): Three Rings + One Runtime Layer

DuckTyper is implemented using **three strict architectural rings**, plus a **runtime wiring layer**.

```

┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents · CI  │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)             │
│  QuackVideo · QuackImage · QuackQuote · …  │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)               │
│  Contracts · Capabilities · IO · Config    │
│  Registries · Results · Adapters            │
└────────────────────────────────────────────┘

══════════════════════════════════════════════
RUNTIME / OPERATIONS (Outside the Rings)
Quackshowrunner — Infrastructure-as-Code
══════════════════════════════════════════════

````

### Key principle

- **Rings define behavior and responsibility**
- **Quackshowrunner defines what is running and how it is wired**
- Repo location ≠ architectural role

---

## 🧠 What Lives in This Monorepo

The DuckTyper monorepo contains **both the engine and its canonical runtime wiring**.

### 🟦 Ring A — Core (Kernel)

#### `quackcore/`

The **constitutional layer** of the DuckTyper.

Defines:
- schemas and contracts
- capability interfaces
- registries and discovery
- config and logging semantics
- filesystem and path primitives
- result and error envelopes
- adapter libraries (HTTP, MCP)

> **QuackCore answers:**  
> *“What shapes and rules are valid in this system?”*

It never:
- executes tools
- orchestrates workflows
- renders UI
- embeds prompts or policies

---

### 🟨 Ring B — Tools (Workers)

#### `quacktools/`

**Atomic, deterministic workers**.

Each tool:
- performs one bounded job
- consumes structured inputs
- emits artifacts + a manifest
- is stateless across runs
- imports **QuackCore only**

> **QuackTools answer:**  
> *“Given these inputs, produce these outputs.”*

Tools never:
- plan workflows
- call other tools
- talk to SaaS systems directly
- store canonical state

---

### 🟩 Ring C — Experiences (Control Planes)

#### `quackrunner/`
**The execution gateway**  
Runs tools safely, isolates execution, captures logs, indexes artifacts.

> *Executes exactly what it is told — once.*

---

#### `quackchat/`
**The human & agent cockpit**

- intent entry
- approvals / rejections
- workflow visibility
- explanations and steering

> *Where intent enters the system.*

---

#### `quackagents/`
**Judgment-bearing services**

Agents:
- read artifacts and manifests
- apply policy and heuristics
- propose decisions
- signal Temporal

They never execute tools directly.

> *Agents decide. Tools produce.*

---

### 🧩 Shared Capabilities

#### `quackintegrations/`

Reusable **native integration capabilities** that increase sovereign leverage.

Used when an integration:
- removes brittle glue
- enables repeatable, auditable workflows
- is reusable across businesses
- fits QuackCore’s config / error / result model

n8n is preferred for:
- fast-changing glue
- one-off business logic
- operational playbooks

---

## 🏗 Runtime / Operations Layer (In-Repo, Outside the Rings)

### 🎬 `quackshowrunner/`

**Infrastructure-as-Code for the DuckTyper runtime**

Quackshowrunner **lives in this monorepo**, but it is **not part of the three rings**.

It is the **deployment and operations layer**.

Quackshowrunner:

- provisions and wires:
  - Temporal
  - n8n
  - QuackRunner
  - agent services
  - shared business systems (CRM, knowledge base)
  - storage and observability
- manages:
  - networking
  - credentials injection
  - backups and recovery
  - upgrades and migrations

It never:
- contains business logic
- defines workflows
- embeds prompts
- executes tools
- renders UI

> **In short:**  
> **DuckTyper defines the system.**  
> **Quackshowrunner runs the system.**

---

## 🔌 Communication Doctrine

Only **three communication paths** are allowed:

1. **Artifact Interface (default)**  
   Files + manifests, immutable, auditable

2. **Service Interface (shared concerns)**  
   Config, registries, schema validation

3. **Adapter Interface (external)**  
   HTTP / MCP at gateways only

**Tools never talk to tools.**

If a tool didn’t emit a manifest — **it didn’t happen**.

---

## 🧰 Canonical Tool Surface

There is exactly **one** CLI:

```bash
quack <tool> <verb> [options]
````

Every tool must implement:

* `run`
* `validate`
* `doctor`
* `explain`

No exceptions.

---

## 🏃 Execution Model (Production)

```
Quackchat
   ↓ intent / approvals
Temporal
   ↓ activity
QuackRunner
   ↓ isolated execution
QuackTool
   ↓
Artifacts + Manifest
```

* **Temporal** owns workflow state, retries, history
* **QuackRunner** owns execution and logs
* **n8n** owns side-effects only
* **Agents** propose decisions
* **Quackchat** enables human steering

---

## 📦 Monorepo Layout (Indicative)

```text
quackverse/
├── quackcore/              # Ring A: kernel
├── quacktools/             # Ring B: workers
├── quackrunner/            # Ring C: execution
├── quackchat/              # Ring C: cockpit
├── quackagents/            # Ring C: judgment
├── quackintegrations/      # Shared capabilities
├── quackshowrunner/        # Runtime / IaC (outside rings)
└── README.md
```

---

## 🧪 The North Star Test

A canonical workflow must exist and run end-to-end:

* collect AI news
* cluster and rank
* draft agenda
* generate content
* produce assets
* publish with approval

It must run:

* locally
* automated
* agent-assisted

This is the **Monday Morning Briefing Test**.

---

## 🧭 Governance Rules (Non-Negotiable)

1. Core defines rules, not pipelines
2. Tools never orchestrate
3. UI never contains core logic
4. Tools never import tools
5. Capabilities are contracts
6. Runtimes are replaceable
7. Everything emits artifacts
8. One canonical CLI (`quack`)
9. One execution gateway (QuackRunner)
10. MCP lives at the adapter layer
11. Temporal owns workflow state
12. n8n owns integrations
13. Engine public, content private
14. Teaching is first-class

**Naming note:**  
QuackVerse refers to the internal architectural doctrine and vocabulary.
DuckTyper is the product and public-facing system built on it.


---

## 🧠 Closing Statement

DuckTyper is built to replace **roles**, not tasks.

* **QuackCore** is the constitution
* **QuackTools** are the hands
* **QuackRunner** is the muscle
* **Temporal** is the process OS
* **n8n** is connective tissue
* **Agents** provide judgment
* **Quackchat** is the cockpit
* **Quackshowrunner** keeps it all running

People can change.
Tools can be swapped.
Agents can evolve.

**The organization still runs.**