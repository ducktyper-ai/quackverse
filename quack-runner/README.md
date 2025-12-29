# 🏃 **QuackRunner**

**The Execution Gateway of the QuackVerse**

> **QuackRunner executes.**
> It does not decide *what* to run.
> It does not decide *when* to run.
> It does not plan workflows.
>
> QuackRunner is the **only place where QuackTools are executed in production**.

---

## 🧠 What QuackRunner Is

**QuackRunner is a stateless execution service** in Ring C of the QuackVerse.

It exists to provide a **single, hardened, auditable execution surface** for all QuackTools.

QuackRunner answers one question only:

> **“Run this tool with these inputs, and tell me exactly what happened.”**

---

## ❌ What QuackRunner Is Not

QuackRunner is **not**:

* a workflow engine (Temporal)
* an agent or planner
* an integration fabric (n8n)
* a UI (Quackchat)
* infrastructure-as-code (Quackshowrunner)
* a business system (CRM, docs)
* a place for prompts or policies

It never:

* selects tools
* retries business logic
* mutates CRM or docs
* stores long-lived organizational state
* embeds workflow sequencing

Those responsibilities live elsewhere by doctrine.

---

## 🧭 Position in the QuackVerse

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES                │
│  Temporal · Agents · QuackRunner           │
│  Quackchat                                │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│  QuackVideo · QuackImage · QuackMachinima │
│  QuackQuote · QuackTutorial · …            │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: Contracts · Schemas            │
│  Result Envelopes · Registries             │
└────────────────────────────────────────────┘
```

**QuackRunner lives in Ring C.**

It sits **between orchestration and execution**.

---

## 🧠 Core Responsibilities

QuackRunner is responsible for **execution only**.

### QuackRunner Does

* accept **run requests**
* resolve tools and versions
* set up isolated execution environments
* execute tools via the canonical `quack` CLI
* stream and capture logs
* collect artifacts
* validate manifest emission
* emit structured run results

### QuackRunner Does Not

* plan workflows
* apply judgment
* manage retries or backoff
* perform side effects
* call SaaS APIs
* store canonical business truth

---

## 🧠 Execution Model

Canonical execution path:

```
Temporal → QuackRunner → QuackTool → Artifacts
```

Alternate (local / dev / interactive):

```
Quackchat → QuackRunner → QuackTool
```

QuackRunner treats tools as **black boxes**.

---

## 🧠 Run Lifecycle

### 1️⃣ Receive Run Request

Via HTTP API (typically from Temporal).

A request includes:

* tool name
* tool version
* verb (`run`, `render`, etc.)
* input manifest reference
* execution parameters
* artifact destination

---

### 2️⃣ Prepare Execution

QuackRunner:

* validates the request
* resolves the tool binary / container
* injects configuration and credentials
* creates an isolated runtime (container / venv / sandbox)

---

### 3️⃣ Execute Tool

* invokes `quack <tool> <verb>`
* streams stdout/stderr
* tracks exit status
* enforces timeouts and limits

---

### 4️⃣ Collect Results

After execution:

* verifies artifact presence
* verifies manifest emission
* computes checksums
* indexes metadata

---

### 5️⃣ Emit Run Result

QuackRunner emits a **RunResult** containing:

* status (success / failure)
* duration
* artifact locations
* manifest pointer
* logs reference
* error details (if any)

This result is:

* returned to Temporal
* visible in Quackchat
* auditable later

---

## 🧠 API Surface

### Canonical Endpoints

```
POST /runs
GET  /runs/{id}
GET  /runs/{id}/artifacts
GET  /runs/{id}/logs
```

QuackRunner’s API is:

* machine-oriented
* schema-driven
* stable across tools

---

## 🧠 Relationship to QuackCore

QuackRunner **imports QuackCore**.

From QuackCore it uses:

* RunRequest / RunResult schemas
* result envelopes
* error models
* artifact conventions
* adapter libraries (HTTP, MCP)

QuackRunner **does not live in QuackCore**.

QuackCore stays pure.
QuackRunner performs side effects.

---

## 🧠 Relationship to Agents

* Agents **decide** which tool should run
* Agents **never execute tools**
* Agents signal **Temporal**
* Temporal calls **QuackRunner**

Agents may read QuackRunner results, but never control execution directly.

---

## 🧠 Relationship to Temporal

Temporal:

* owns workflow state
* owns retries and timing
* records history

QuackRunner:

* executes exactly what it is told
* once per request
* with no memory of previous runs

---

## 🧠 Relationship to n8n

n8n:

* performs external side effects
* updates CRM / docs / notifications

QuackRunner:

* never talks to SaaS APIs
* never mutates business systems

---

## 🧠 Relationship to Quackshowrunner

* **Quackshowrunner deploys QuackRunner**
* Quackshowrunner wires networking, storage, secrets
* Quackshowrunner does not contain QuackRunner logic

---

## 📦 Repository Structure

```text
quackrunner/
├── src/
│   ├── api/              # HTTP & MCP endpoints
│   ├── execution/        # Tool execution engine
│   ├── sandbox/          # Isolation & limits
│   ├── artifacts/        # Artifact collection & indexing
│   ├── logs/             # Log streaming & storage
│   └── main.py           # App entrypoint
│
├── tests/
├── README.md
└── pyproject.toml
```

---

## 🔐 Security Model (High-Level)

QuackRunner enforces:

* strict input validation
* isolated execution per run
* least-privilege credentials
* explicit artifact paths
* immutable outputs
* auditable logs

Execution is treated as a **security boundary**.

---

## 🎓 Pedagogical Mandate

QuackRunner is **teachable infrastructure**.

It should make explicit:

* how execution differs from planning
* why isolation matters
* how artifacts enable auditability
* how failures are surfaced cleanly

Opaque execution is considered broken.

---

## 🧭 Governance Rules (Non-Negotiable)

1. All tool execution flows through QuackRunner
2. QuackRunner never selects tools
3. QuackRunner never retries business logic
4. QuackRunner never mutates business systems
5. Tools are black boxes
6. Artifacts + manifests are mandatory
7. Logs are first-class outputs
8. QuackCore remains pure

---

## 🧠 Closing Statement

**QuackRunner is the muscle of the QuackVerse.**

Agents think.
Temporal remembers.
Tools work.

QuackRunner makes execution **real, safe, and auditable**.

Without it, everything leaks.
With it, the system holds.