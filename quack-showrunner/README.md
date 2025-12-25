# 🎬 Quackshowrunner

**The Sovereign Operating System for the AI-First Media Company.**

> *"The future of media is not bigger teams. It is better systems."* — [The AI-First Media Operating Doctrine (v1)](../docs/doctrine.md)

## 🧠 The Vision

**Quackshowrunner** is not just a collection of Docker containers. It is the physical manifestation of **Pillar B (Automation & Orchestration)** of our operating doctrine.

It is a production-grade, self-hosted infrastructure stack designed to replace the "collection of SaaS tools" with a cohesive **Media Operating System**. It creates a "Sovereign Cloud" where AI agents perform organizational functions traditionally done by humans (Research, Editing, Production Management).

### Core Philosophy

1. **AI Replaces Roles, Not Tasks:** The infrastructure handles the "drudgery" so humans provide the taste.
2. **Visible Control Plane:** n8n is the brain. If a process cannot be visualized in a flow, it does not exist.
3. **Pedagogical Mandate:** Our infrastructure is our curriculum. This codebase itself is educational content.

---

## 🏗 Architecture (v2 Roadmap)

We are currently refactoring the stack to align with the **v2 Vision**. This architecture is designed for "Compound Leverage"—where every input results in multiple, high-quality outputs.

### 1. The Brain (Orchestration)

* **Service:** **n8n** (Production Grade, Postgres-backed)
* **Role:** The visible control plane. Orchestrates the flow of data between ingestion, processing, and publishing.
* **The Killer Feature:** **MCP Gateway**. A dedicated service exposing the *Model Context Protocol* via SSE. This allows n8n to "hire" AI Agents to perform complex reasoning, SQL querying, and research tasks autonomously.

### 2. The Memory (Context & Relations)

* **Service:** **Twenty CRM** (Replacing EspoCRM)
* **Role:** The canonical source of truth for relationships, deals, and guests.
* **Why:** Twenty is API-first and open-source, allowing AI agents to navigate relationship graphs easier than legacy CRMs.

### 3. The Curriculum (Knowledge Base)

* **Service:** **Docusaurus** (Replacing Wiki.js)
* **Role:** The "Pedagogical Mandate." Documentation is treated as code.
* **Why:** By using a Git-backed, static-site generator, our internal SOPs are technically identical to our public educational content. An agent can write a tutorial, open a PR, and deploy it as a lesson for the **AI Automators Club**.

### 4. The Nervous System (Telemetry)

* **Services:** **Telegraf + TimescaleDB + Superset**
* **Role:** Observability.
* **The Shift:** Moving from monitoring "CPU Usage" to monitoring **"Content Throughput"** and **"Agent Token ROI."**

### 5. The Gatekeeper (Zero Trust)

* **Services:** **Nginx + OAuth2 Proxy + Dex**
* **Role:** Security.
* **Why:** The entire stack is shielded behind a single authentication layer (Google OAuth/OIDC). Even if a service has no auth, the Gatekeeper protects it.

---

## 🚧 Current Status & Roadmap

We are currently transitioning from **v1 (POC)** to **v2 (The Vision)**.

* [ ] **Infrastructure Hardening:**
* [x] Docker Compose modular architecture.
* [x] Automated Borgmatic backups (to Hetzner Storage Box).
* [x] "Nuclear Recovery" scripts (Idempotent restoration).


* [ ] **The "Brain" Upgrade:**
* [x] Deploy MCP Gateway (Supergateway).
* [ ] Integrate AI Agents via SSE.


* [ ] **The "Memory" Refactor:**
* [ ] Migrate from EspoCRM to **Twenty CRM**.
* [ ] Add **MinIO (S3)** for "Pillar A" (Long-form video storage).
* [ ] Enable `pgvector` for Agent long-term memory.


* [ ] **The "Curriculum" Pivot:**
* [ ] Migrate from Wiki.js to **Docusaurus**.
* [ ] Setup Git-based publishing pipelines.



---

## 📂 Directory Structure (Vision)

```text
quack-showrunner/
├── apps/
│   ├── n8n/              # The Brain
│   ├── mcp-gateway/      # The Agent Interface (Supergateway)
│   ├── twenty/           # The CRM (Relations)
│   ├── docusaurus/       # The Docs (SOPs & Content)
│   └── superset/         # The Dashboard
├── conf/                 # Infrastructure as Code
│   ├── nginx/            # Reverse Proxy & Security Headers
│   ├── postgres/         # DB Initialization & Migrations
│   └── timescale/        # Telemetry Schemas
├── scripts/              # The "Sovereign" Toolset
│   ├── nuclear-recovery.sh  # Disaster Recovery
│   └── deploy.sh            # CI/CD
└── docker-compose.yml    # The Orchestration File

```

---

## 🔌 Integrations

Quackshowrunner is designed to be the "Backend" of the operation. It integrates with:

* **Ducktyper:** Our writing and interface layer. Quackshowrunner receives signals from Ducktyper via secured webhooks.
* **QuackCore:** The shared logic library.
* **?:** An AI Agent framework powering the MCP Gateway.

---

## 🤝 Contributing

This repository follows the **Pedagogical Mandate**. If code cannot be understood by a junior developer, it is refactored.

1. **Documentation First:** No PR is merged without updating the Docusaurus docs.
2. **Idempotency:** Setup scripts must run safely multiple times without breaking the state.
3. **Manifesto Alignment:** Does your change help AI replace a role?

---

*“If it cannot be shown in a flow, it cannot be trusted.”*