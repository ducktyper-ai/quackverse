# **The QuackVerse Doctrine (v3)**

**The AI Operating System for Knowledge Work**

---

## **0. One Sentence**

**Open-source the engine, standardize the contracts once, orchestrate durably, integrate externally, and keep stories and courses proprietary.**

---

## **1. Purpose**

QuackVerse exists to turn AI from demos into **operating reality**.

It is not:

* a chatbot framework
* a single product
* a content brand

It *is*:

* a system for building AI-first organizations
* a teaching vehicle for agent engineering
* an execution engine for AI operators
* a leverage multiplier for individual builders and small teams

This doctrine defines **what lives where**, **who owns what**, and **how the system compounds instead of collapsing**.

---

## **2. The Core Belief**

AI is not a feature.
AI is not a prompt.
AI is not a chatbot.

**AI is an operating system for modern organizations.**

Those who win with AI will be the ones who:

* design systems
* standardize operations
* deploy digital workers
* and compound leverage daily

QuackVerse exists to enable that outcome.

---

## **3. The Three Rings Model**

QuackVerse is structured as **three concentric rings**, each with strict responsibilities.

```
┌────────────────────────────────────────────┐
│        EXPERIENCES / ORCHESTRATION         │
│  Quackchat · Temporal · n8n · Agents · CI  │
├────────────────────────────────────────────┤
│               TOOLS (WORKERS)              │
│  Video · Image · Tutorial · Machinima · …  │
├────────────────────────────────────────────┤
│              CORE (KERNEL)                 │
│  Contracts · Capabilities · Registries     │
│  Config · IO · Teaching · Adapters         │
└────────────────────────────────────────────┘
```

---

## **Ring A — Core (QuackCore)**

QuackCore is the **kernel and governance layer**.

### Responsibilities

QuackCore defines:

* contracts and schemas
* capability interfaces (protocols)
* registries and discovery
* configuration and logging
* IO and artifact conventions
* teaching scaffolding (quests, XP, checks)
* adapter layers (HTTP, MCP)

### Non-Negotiables

* Core **never renders pixels**
* Core **never contains IP or narrative**
* Core **defines contracts, not pipelines**
* Core **does not orchestrate workflows**

QuackCore answers:

> *“What is possible, and in what shape?”*

---

## **Ring B — Tools (QuackTools)**

QuackTools are **atomic vertical workers**.

Each QuackTool:

* performs **one domain job**
* consumes **structured inputs**
* emits **structured artifacts + manifests**
* imports **QuackCore only**
* remains **composable and pipeline-safe**

### Examples

* quack video
* quack image
* quack machinima
* quack tutorial
* quack research
* quack distro

### Non-Negotiables

* Tools **never orchestrate workflows**
* Tools **never import other tools**
* Tools **do not communicate directly**
* Tools **only communicate via artifacts + schemas**

QuackTools answer:

> *“Given these inputs, produce these outputs.”*

---

## **Ring C — Experiences (Control Planes)**

Ring C contains **orchestrators and interfaces**.

This is where **decisions, sequencing, and judgment live**.

Ring C is composed of **four distinct roles**.

---

### **1️⃣ Temporal — Durable Workflow Engine (Authoritative State)**

Temporal is the **single source of truth for workflows**.

### Temporal Owns

* workflow state
* progression logic
* retries and backoff
* timers and waits
* human-in-the-loop pauses
* task queues
* audit history

### Temporal Does NOT

* render
* contain tool logic
* talk to SaaS APIs directly
* replace n8n

### Rules

* All **domain workflows** live in Temporal
* Temporal workflows describe **what happens next and when**
* Temporal calls tools **only via**:

  * quack CLI (local/dev)
  * QuackRunner HTTP (cloud)

Temporal answers:

> *“What is the organization doing right now?”*

---

### **2️⃣ n8n — Integration & IO Fabric**

n8n is **not a workflow brain**.

It is the **connector mesh**.

### n8n Owns

* webhooks (incoming + outgoing)
* SaaS connectors (Sheets, Airtable, Instagram, Notion, etc.)
* notifications
* CRM updates
* lightweight routing and transforms

### Rules

* n8n never owns long-term state
* n8n never retries business logic
* n8n executes **side-effects only**
* n8n flows must be **idempotent**
* n8n is triggered **by Temporal** or **triggers Temporal**

n8n answers:

> *“How do we talk to the outside world?”*

---

### **3️⃣ Quackchat — Human & Agent Cockpit**

Quackchat is the **interactive control plane**.

### Quackchat Provides

* approvals and rejections
* interactive runs
* re-runs (“redo option 2”)
* explanations (“what happened?”)
* agent-assisted steering

### Rules

* Quackchat never contains core logic
* Quackchat never runs tools directly
* Quackchat signals and queries Temporal
* Quackchat reads artifacts + manifests

Quackchat answers:

> *“What should we do now?”*

---

### **4️⃣ Agents — Digital Workers with Judgment**

Agents are **not tools**.

Agents are:

* orchestrators with judgment
* policy enforcers
* autonomous foremen

Agents:

* read artifacts and manifests
* decide next actions
* trigger tools via CLI / HTTP / MCP
* log reasoning and actions as events

Agents live entirely in **Ring C**.

---

## **4. Communication Doctrine**

There are **only three sanctioned communication paths**.

### 1️⃣ Artifact Interface (Default)

* files + manifests
* deterministic
* debuggable
* teachable
* portable

### 2️⃣ Service Interface (Shared Concerns)

* config
* storage
* registries
* schema validation

### 3️⃣ Adapter Interface (External)

* HTTP (QuackRunner)
* MCP (agent tool calling)

**Tools never talk to tools.**

---

## **5. Tool Surface Doctrine**

### **One Canonical CLI**

There is exactly **one** canonical CLI:

```
quack <tool> <verb> [options]
```

Examples:

* quack video cut
* quack image thumbnail
* quack machinima render
* quack tutorial init

Tools **register commands**; they do not define their own CLIs.

### **Required Verbs**

Every tool must implement:

* `run`
* `validate`
* `doctor`
* `explain`

---

## **6. Cloud Execution Doctrine**

### **QuackRunner — The Execution Gateway**

There is **one cloud execution service**: **QuackRunner (FastAPI)**.

### Responsibilities

* start tool runs
* track status
* expose logs
* index artifacts

### Interfaces

* `POST /runs`
* `GET /runs/{id}`
* `GET /runs/{id}/artifacts`

### Rules

* QuackRunner contains **no tool logic**
* Temporal and n8n talk to tools **only via QuackRunner**
* Artifacts are the integration backbone

---

## **7. Artifact Store Doctrine**

In cloud mode:

* all runs write to object storage
* each run has a deterministic prefix
* the manifest is the source of truth

This enables:

* retries
* auditability
* reproducibility
* agent reasoning

---

## **8. MCP Doctrine**

MCP is an **adapter surface**, not an internal dependency.

### Rules

* MCP is exposed at the gateway or adapter layer
* Tools do not embed MCP
* MCP enables safe LLM tool calling

Supported surfaces:

* CLI
* HTTP
* MCP

---

## **9. Rendering Doctrine (PixiJS Decision)**

Rendering engines are **replaceable runtimes**.

### Rules

* QuackCore defines rendering capabilities
* QuackMachinima defines beat/scene schemas
* PixiJS is one runtime implementation
* Core never renders

---

## **10. IP & Ownership Doctrine**

### Public (Open Source)

* QuackCore
* quack CLI framework
* QuackTools logic
* QuackRunner
* MCP adapters
* templates and sample worlds
* teaching scaffolding

### Proprietary (Moat)

* Everduck assets and stories
* Rod comics IP
* branded templates
* paid courses (AIPE / AAC)

**Engine runs on content. Content never ships with the engine.**

---

## **11. Operational North Star**

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

## **12. Final Governance Rules (Non-Negotiable)**

1. Core never renders pixels
2. Tools never orchestrate
3. UI never contains core logic
4. Tools never import tools
5. Capabilities are contracts
6. Runtimes are replaceable
7. Everything emits artifacts
8. One canonical CLI (`quack`)
9. One cloud gateway (QuackRunner)
10. MCP lives at the adapter layer
11. Temporal owns workflow state
12. n8n owns integrations
13. Engine public, content private
14. Teaching is first-class

---

## **13. Closing Statement**

**Temporal is the process OS.**
**QuackTools are the hands.**
**QuackRunner is the muscle.**
**n8n is the connective tissue.**
**Quackchat is the cockpit where human and agent intent enters.**
**DuckTyper is the steward of the ecosystem.**

DuckTyper is the organizational umbrella.
QuackVerse is the operating system.
Quackchat is the human interaction interface.
f-squared.ai owns the stories.

The system compounds — even when people change.


Doctrine rule: implement native integrations when they increase sovereign leverage
Build an integration in quack_core when it:
Reduces dependency on brittle glue (manual steps / SaaS UI clicking / tribal knowledge)
Enables repeatable, automatable, auditable workflows (runs the same way every time)
Improves portability across rollups (a capability that multiple businesses can reuse)
Fits your system boundaries (config, credentials, logging, error model, results, CLI UX)
And prefer n8n (or external endpoints) when:
it’s mostly ad-hoc orchestration glue with lots of one-off branching per business
it changes weekly and you don’t want it in core code
it’s better represented as an operational playbook than a reusable capability
This is about leverage + sovereignty, not pedagogy.
