# 🎬 **Quackshowrunner**

**Infrastructure-as-Code for the QuackVerse Runtime**

Quackshowrunner wires systems together.

It does **not** think, decide, render, or create content.

It provisions, connects, and operates the runtime in which AI-first organizations execute work.

---

## 🧠 **What Quackshowrunner Is**

Quackshowrunner is the **infrastructure layer of the QuackVerse**.

It is a **self-hosted, declarative runtime** that provisions and connects the **long-lived systems** an AI-first organization depends on:

* durable workflow engines
* execution gateways
* integration fabrics
* **external agent services**
* **shared business systems (CRM, knowledge base)**
* storage and observability

Quackshowrunner answers one question only:

> **“What services are running, how are they connected, and how do we recover when something breaks?”**

---

## ❌ **What Quackshowrunner Is Not**

Quackshowrunner does **not** contain:

* business logic
* agent reasoning
* prompts or policies
* UI code
* rendering engines
* domain workflows
* proprietary IP

Those belong elsewhere by doctrine.

---

## 🧭 **Position in the QuackVerse**

QuackVerse is structured as three rings:

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES                │
│  Temporal · n8n · QuackRunner · Agents     │
│  Quackchat · CI                            │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│  QuackVideo · QuackImage · QuackMachinima │
│  QuackTutorial · QuackResearch · …         │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: Contracts · Capabilities       │
│  Config · IO · Registries · Teaching       │
└────────────────────────────────────────────┘
```

**Quackshowrunner lives outside the rings.**

It is the **deployment and operations layer** that makes **Ring C services and shared business systems** run.

---

## 🏗 **Responsibilities**

Quackshowrunner is responsible for:

---

### **1️⃣ Provisioning Runtime Services**

#### Orchestration & Execution

* **Temporal** — durable workflows and authoritative state
* **n8n** — integration & external IO fabric
* **QuackRunner** — tool execution gateway

#### External Agent Services (Deployed, Not Defined)

* deployment of **role-bound agent services**
* configuration and credential injection
* networking, health checks, restarts

> **Important:**
> Agent logic lives in `quackverse/agents/*`.
> Quackshowrunner deploys agent services but contains **no agent source code**.

#### Business Systems (Shared Infrastructure)

* **Twenty CRM** — relational system of record for business state
* **Docusaurus** — canonical knowledge base / SOP surface

#### Data & Observability

* Datastores (Postgres, pgvector, MinIO)
* Observability (metrics, logs, dashboards)

---

### **2️⃣ Wiring & Topology**

* service discovery
* network boundaries
* credentials injection
* environment configuration
* volume mounts
* port exposure
* zero-trust gateways

---

### **3️⃣ Operational Safety**

* idempotent setup
* backup and restore
* disaster recovery (“nuclear recovery”)
* upgrades and migrations
* health checks

---

## 🚫 **Explicit Non-Responsibilities**

By non-negotiable doctrine, Quackshowrunner **never**:

* defines workflows (Temporal does)
* decides sequencing (Temporal does)
* selects tools (Agents do)
* runs tools (QuackRunner does)
* renders pixels (Tools do)
* contains UI logic (Quackchat does)
* embeds prompts or policies (Agents do)
* encodes business rules for CRM or docs

---

## 🧠 **Runtime Components (What Gets Deployed)**

---

### **Temporal — Process OS**

* authoritative workflow state
* retries, timers, approvals
* audit history

**Temporal owns what happens next.**

---

### **n8n — Integration Fabric**

* webhooks
* SaaS connectors
* notifications
* side-effects only

**n8n owns external IO, not logic.**

This includes:

* updating Twenty CRM records
* writing content into Docusaurus
* triggering documentation builds or notifications

---

### **QuackRunner — Execution Gateway**

* starts QuackTool runs
* tracks execution status
* indexes artifacts
* exposes logs

**All tool execution flows through QuackRunner.**

---

### **Agent Services — Judgment Actors (External)**

Agents are **first-class Ring C codebases** living in:

```
quackverse/agents/*
```

Quackshowrunner’s responsibility is limited to:

* deploying agent services
* injecting configuration and credentials
* wiring them to Temporal, QuackRunner, and storage
* monitoring health

Agents themselves:

* read artifacts and manifests
* propose decisions and plans
* signal Temporal

**Agents decide.
Infrastructure does not.**

---

### **Business Systems**

#### **Twenty CRM — Business State**

* deals, jobs, customers, orders
* long-lived organizational truth
* updated via Temporal → n8n workflows

Twenty is:

* shared across workflows and tools
* queried by agents
* never embedded inside tools

---

#### **Docusaurus — Knowledge Surface**

* SOPs
* job descriptions
* runbooks
* agent-readable documentation

Docusaurus is:

* written to via workflows
* read by humans and agents
* never treated as a QuackTool

---

### **Storage & Memory**

* **Object storage** (MinIO / S3): artifacts
* **Relational storage** (Postgres): state
* **Vector storage** (pgvector): semantic memory

**Artifacts are the system of record.**

---

## 📦 **Directory Structure**

```text
quackshowrunner/
├── compose/                # Docker Compose definitions
│   ├── temporal.yml
│   ├── n8n.yml
│   ├── quackrunner.yml
│   ├── agents.deploy.yml  # Deploys external agent services
│   ├── twenty.yml         # Twenty CRM deployment
│   ├── docusaurus.yml     # Knowledge base deployment
│   ├── storage.yml
│   └── observability.yml
│
├── conf/                   # Service configuration
│   ├── temporal/
│   ├── postgres/
│   ├── n8n/
│   ├── twenty/
│   ├── docusaurus/
│   └── nginx/
│
├── scripts/                # Operational tooling
│   ├── deploy.sh
│   ├── backups.sh
│   ├── restore.sh
│   └── nuclear-recovery.sh
│
├── env/                    # Environment templates (no secrets)
│   └── .env.example
│
└── README.md
```

---

## 🔗 **Relationship to Other Repos**

| Component       | Lives Where                  |
| --------------- | ---------------------------- |
| QuackCore       | `quackverse/quack-core`      |
| QuackTools      | `quackverse/quacktools/*`    |
| QuackRunner     | `quackverse/quackrunner`     |
| Agents          | `quackverse/agents/*`        |
| Quackchat       | `quackverse/quackchat`       |
| Quackshowrunner | `quackverse/quackshowrunner` |
| Everduck (IP)   | separate proprietary repo    |

Quackshowrunner **deploys** these components.
It does **not** own their source code.

---

## 🎓 **Pedagogical Mandate**

Quackshowrunner is **teachable infrastructure**.

It exists so builders can learn:

* how durable workflows are deployed
* how agent systems are operated safely
* how artifacts enable auditability
* how shared business systems integrate cleanly
* how AI systems recover from failure

Infrastructure is curriculum — **logic lives elsewhere**.

---

## 🧭 **Governance Rules (Non-Negotiable)**

1. Quackshowrunner is infrastructure only
2. No business logic in IaC
3. No prompts in infrastructure
4. No rendering engines here
5. Temporal owns workflow state
6. QuackRunner owns execution
7. n8n owns integrations only
8. Agents own judgment
9. Business systems are shared infrastructure
10. Artifacts are the source of truth
11. Engine public, content private

---

## 🧠 **Closing Statement**

**Quackshowrunner is the wiring harness.**
**Temporal is the brain stem.**
**Agents provide judgment.**
**QuackTools do the work.**
**Quackchat is the cockpit.**
**Twenty and Docusaurus hold organizational truth.**
**Everduck is content — not infrastructure.**

When people change,
when agents evolve,
when tools are replaced —

**the system keeps running.**