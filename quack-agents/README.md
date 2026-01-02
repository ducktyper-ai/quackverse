# 🧠 **Quack Agents**

**Judgment-Bearing Services in the QuackVerse**

> **Agents decide.**
> They do not execute tools.
> They do not own workflows.
> They do not provision infrastructure.
>
> Agents exist to **apply judgment, policy, and planning** inside AI-first organizations.

---

## 🧭 What Quack Agents Are

**Quack Agents are first-class Ring C services** in the QuackVerse.

They are long-running services that:

* reason over artifacts and manifests
* apply policies and heuristics
* propose plans and decisions
* select which tools *should* be used
* explain *why* a decision was made
* signal workflow engines with structured decisions

Quack Agents answer one question:

> **“Given what we know, what should happen next?”**

---

## ❌ What Quack Agents Are Not

Quack Agents are **not**:

* tools
* workflow engines
* infrastructure
* UI components
* cron jobs
* chatbots for end users
* stateless functions

They **do not**:

* execute QuackTools directly
* mutate business systems
* retry or sequence workflows
* render output
* manage storage

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

**Quack Agents live in Ring C.**

They sit **above tools** and **alongside Temporal and Quackchat**.

---

## 🧠 Core Responsibilities

Quack Agents are responsible for **judgment**, not execution.

### Agents Do

* read **artifacts** and **manifests**
* interpret workflow context
* apply domain rules and policies
* evaluate alternatives
* select tools and parameters
* propose next actions
* explain decisions in human-readable form
* signal **Temporal** with structured decisions

### Agents Do Not

* run tools (QuackRunner does)
* sequence workflows (Temporal does)
* perform side effects (n8n does)
* own business state (CRM does)
* store canonical truth (artifacts do)

---

## 🧠 Agents vs Tools (Critical Distinction)

| Aspect      | Agent                        | Tool                         |
| ----------- | ---------------------------- | ---------------------------- |
| Purpose     | Decide                       | Execute                      |
| State       | Long-lived                   | Stateless per run            |
| Logic       | Heuristics, policy, planning | Deterministic transformation |
| Calls       | Signals workflows            | Runs jobs                    |
| Outputs     | Decisions, explanations      | Artifacts, manifests         |
| Retry logic | ❌ No                         | ❌ No                         |

> **Agents choose. Tools produce.**

---

## 🧠 Agents vs Workflows

* **Temporal workflows** describe *what must happen and when*
* **Agents** decide *how and why a choice is made*

Agents:

* do not own workflow state
* do not handle retries
* do not manage timers
* do not persist execution history

All durability belongs to Temporal.

---

## 🧠 Agents vs Quackchat

* **Quackchat** is the human control plane
* **Agents** are autonomous decision services

Quackchat:

* displays agent proposals
* allows humans to approve / reject
* sends signals back to Temporal

Agents:

* never interact directly with humans
* never render UI
* never execute commands

---

## 🧠 Types of Agents

Agents are **role-based**, not project-specific.

Examples:

* **ProducerAgent** — plans workflows and milestones
* **EditorAgent** — critiques and improves content
* **SalesOpsAgent** — pricing, quotes, deal structure
* **QAAgent** — validation, consistency checks
* **ComplianceAgent** — policy and regulatory review
* **RenderSupervisorAgent** — validates render manifests

You do **not** create:

* “EverduckEpisode17Agent”
* “Quote123Agent”

Instead, you create **generic role agents** configured with:

* domain context
* policy packs
* style guides
* constraints

---

## 🧠 Configuration, Not Specialization

Agents remain generic.

Specialization happens through:

* manifests
* domain packs
* policy definitions
* system prompts
* configuration

Example:

* The same `ProducerAgent` can:

  * plan an Everduck episode
  * plan a print-shop quote
  * plan a blog production pipeline

Only the **inputs differ**.

---

## 🔌 Communication Model

Agents communicate through **strictly defined channels**.

### 1️⃣ Read

* artifacts
* manifests
* workflow context
* historical decisions

### 2️⃣ Decide

* evaluate alternatives
* produce a decision payload
* include rationale

### 3️⃣ Signal

* send structured decisions to **Temporal**
* never call tools directly
* never mutate external systems

---

## 🧠 Decision Payloads

Agents emit **structured decisions**, not free-form text.

A decision includes:

* recommended next step
* selected tool (by name)
* parameters
* confidence or risk flags
* explanation

These payloads are:

* recorded by Temporal
* visible in Quackchat
* auditable later

---

## 📦 Repository Structure

```text
quack-agents/
├── agent-producer/
│   ├── src/
│   ├── policies/
│   ├── prompts/
│   ├── tests/
│   └── README.md
│
├── agent-editor/
├── agent-salesops/
├── agent-qa/
│
└── README.md
```

Each agent:

* is a standalone service
* imports **QuackCore**
* exposes a minimal API (HTTP / gRPC / queue)
* is deployable independently

---

## 🔗 Relationship to Other Repos

| Component           | Responsibility                             |
| ------------------- | ------------------------------------------ |
| **QuackCore**       | Contracts, schemas, capability definitions |
| **QuackTools**      | Deterministic work                         |
| **Temporal**        | Workflow state and durability              |
| **QuackRunner**     | Tool execution                             |
| **n8n**             | External side effects                      |
| **Quackchat**       | Human interaction                          |
| **Quackshowrunner** | Deployment & operations                    |

Agents depend on **QuackCore**, not on tools or infrastructure.

---

## 🎓 Pedagogical Mandate

Quack Agents are **teaching artifacts**.

They should make explicit:

* why decisions were made
* what alternatives existed
* which trade-offs were chosen
* how judgment differs from execution

Opaque agents are considered broken.

---

## 🧭 Governance Rules (Non-Negotiable)

1. Agents never execute tools
2. Agents never own workflow state
3. Agents never perform side effects
4. Agents never embed infrastructure logic
5. Agents emit structured decisions
6. Agents explain themselves
7. Tools remain deterministic
8. Workflows remain durable
9. Infrastructure remains boring

---

## 🧠 Closing Statement

**Agents are the mind of the organization.**
They plan, critique, and decide.

They do not swing the hammer.
They do not keep the books.
They do not run the machines.

That separation is what allows the system to scale,
teach, and survive change.