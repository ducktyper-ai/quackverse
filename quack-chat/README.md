Below is a **doctrine-correct, first-principles README.md for `quackchat`**.

This README positions Quackchat **cleanly as the Ring C human & agent control plane**, avoids overlap with Quackshowrunner (IaC), avoids tool creep, and makes it clear how Quackchat fits into AI rollups, Everduck, and business workflows like QuackQuote.

This is written so that:

* an infra person understands the boundary
* a frontend/TS engineer knows what they’re building
* a future contributor won’t accidentally turn it into a logic dump

---

# 🦆 Quackchat

**The Human & Agent Control Plane of the QuackVerse**

> **Quackchat is where intent enters the system.**
> It does not execute tools.
> It does not define workflows.
> It does not contain business logic.
>
> It lets humans and agents *observe, steer, approve, and explain* what the AI organization is doing.

---

## 🧠 What Quackchat Is

**Quackchat is an interactive control plane** for AI-first organizations built on the QuackVerse.

It is a **TypeScript application** (UI + CLI surfaces) that allows humans to:

* start workflows
* inspect running processes
* approve or reject steps
* ask “what happened?”
* steer agents
* review artifacts
* re-run decisions

Quackchat answers one question only:

> **“What should we do now?”**

---

## ❌ What Quackchat Is Not

Quackchat is **not**:

* a chatbot framework
* a tool runner
* a workflow engine
* a prompt repository
* a business rules engine
* a rendering engine
* a CRM
* a docs system

Those responsibilities belong elsewhere — by design.

---

## 🧭 Position in the QuackVerse

QuackVerse is structured into three rings:

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

**Quackchat lives entirely in Ring C.**

It interacts *with* the system — it never *implements* it.

---

## 🧠 Core Responsibilities

Quackchat provides **four core capabilities**.

---

### 1️⃣ Intent Entry

Quackchat is the **primary surface where intent enters the system**.

Examples:

* “Create a new Everduck episode”
* “Generate a quote for this customer”
* “Redo option B”
* “Pause this workflow”
* “Why did the agent choose this?”

Quackchat:

* validates intent
* structures it
* forwards it to **Temporal** as a workflow signal or start request

---

### 2️⃣ Workflow Visibility

Quackchat allows humans to **observe what is happening right now**.

It can:

* list active workflows
* show current step
* show decision history
* show retry/backoff state
* show approvals waiting

Quackchat **queries Temporal** — it does not track state itself.

---

### 3️⃣ Human-in-the-Loop Control

Quackchat is the **human override layer**.

It supports:

* approve / reject
* pause / resume
* re-run (“redo with different parameters”)
* escalation to human judgment

All decisions are:

* recorded by Temporal
* visible to agents
* auditable later

---

### 4️⃣ Explanation & Steering

Quackchat provides **explainability**, not raw logs.

It enables:

* “Why did the agent do this?”
* “What alternatives were considered?”
* “What artifacts were produced?”
* “What happens if I change this?”

Explanations come from:

* agent reasoning logs
* manifests
* Temporal event history

---

## 🧠 Relationship to Agents

Agents are **judgment-bearing actors**.

Quackchat:

* does **not** contain agent logic
* does **not** embed prompts
* does **not** call tools

Instead, Quackchat:

* displays agent proposals
* allows humans to accept or override them
* sends signals back to Temporal

> **Agents propose. Humans approve. Temporal records.**

---

## 🧰 Relationship to Tools (QuackTools)

Quackchat never executes tools directly.

Correct flow:

```
Quackchat → Temporal → QuackRunner → QuackTool
```

Quackchat:

* reads tool outputs as artifacts
* never depends on tool internals
* never imports tool code

---

## 🔌 Relationship to Business Systems

Systems like:

* Twenty CRM
* Docusaurus
* Email
* Billing
* Storage

are **infrastructure services**, not tools.

Quackchat:

* may display their state
* may link to records
* may show derived summaries

But **side-effects happen elsewhere**:

* via Temporal + n8n
* never from the UI directly

---

## 🧪 Example: QuackQuote Flow

**Goal:** Generate a quote for a print shop.

1. User enters request in **Quackchat**
2. Quackchat signals **Temporal** to start `quote.v1`
3. Agent proposes pricing strategy
4. Human approves in Quackchat
5. Temporal executes **QuackQuote** via QuackRunner
6. Tool emits artifacts + manifest
7. n8n updates **Twenty CRM** and **Docusaurus**
8. Quackchat displays results

Quackchat never:

* calculates pricing
* updates CRM
* writes docs
* executes code

---

## 🏗 Architecture (Conceptual)

```
[ Human ]
    ↓
[ Quackchat ]
    ↓ signals / queries
[ Temporal ]
    ↓
[ QuackRunner ]
    ↓
[ QuackTools ]
```

Artifacts flow **back up** for visibility and explanation.

---

## 📦 Project Structure (Indicative)

```text
quackchat/
├── apps/
│   ├── web/              # Web UI (React / Next / etc.)
│   └── cli/              # CLI surface (optional)
│
├── src/
│   ├── api/              # Typed clients (Temporal, QuackRunner)
│   ├── views/            # Workflow, run, artifact views
│   ├── actions/          # Intent & signal definitions
│   ├── explain/          # Explanation & reasoning renderers
│   └── types/            # Shared domain types (no logic)
│
├── public/
├── tests/
└── README.md
```

---

## 🎓 Pedagogical Mandate

Quackchat is **part of the teaching surface**.

It should make:

* workflows understandable
* agent decisions legible
* failures instructive
* retries visible
* trade-offs explicit

The UI is not decoration — it is **education**.

---

## 🧭 Governance Rules (Non-Negotiable)

1. Quackchat never executes tools
2. Quackchat never contains business logic
3. Quackchat never owns workflow state
4. Quackchat never embeds prompts or policies
5. Quackchat only signals and queries Temporal
6. Artifacts are read-only
7. Infrastructure lives elsewhere
8. UI is replaceable
9. Teaching is first-class

---

## 🧠 Closing Statement

**Quackchat is the cockpit.**
**Temporal is the flight computer.**
**Agents are the copilots.**
**QuackTools are the engines.**

Humans stay in control.
Systems stay auditable.
The organization compounds.

---

If you want next, strong follow-ups would be:

* a **Quackchat → Temporal API contract**
* a **workflow-centric UI wireframe**
* a **role-aware Quackchat UX** (Producer vs Sales vs Editor)
* or a **CLI-first Quackchat spec**

Just point the direction.
