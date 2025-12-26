# **QuackVerse Doctrine v2**

The operating doctrine for an AI-first media + education ecosystem built in the open, with a protected creative moat — now including the tool surface, cloud execution, and agent interfaces.

# **0) One sentence**

Open-source the engine, standardize the contracts and tool surface once, orchestrate externally, and keep the stories/courses proprietary.

# **1) The Three Rings Model**

QuackVerse is structured as three concentric rings:

**Ring A — Core (QuackCore)**

QuackCore is the kernel and governance layer. It defines:

- Contracts (schemas, result types)
- Capability interfaces (protocols)
- Registries (discoverability)
- Configuration, logging, IO conventions
- Teaching scaffolding (quests, XP, checks)
- Adapters (HTTP/MCP) as protocol layers, not business logic

Non-negotiables

- Core never renders pixels
- Core never contains story IP
- Core defines contracts, not pipelines

**Ring B — Tools (QuackTools)**

QuackTools are vertical workers. They:

- Implement business logic for one domain (video, images, tutorials, distro, machinima, newsletter…)
- Consume structured inputs
- Produce structured outputs (artifacts + manifests)
- Import QuackCore, not other tools
- Remain composable and pipeline-friendly

Non-negotiables

- Tools never orchestrate end-to-end workflows
- Tools don’t communicate directly with each other
- Tools communicate via artifacts and schemas

**Ring C — Experiences (Control Planes)**

Experiences orchestrate. They include:

- n8n flows (automation manager)
- DuckTyper (interactive chat/CLI control plane)
- CI jobs / cron runners
- dashboards / web UIs

Non-negotiables

- UI contains no core logic
- Orchestration lives here (human-in-loop + automation)

# **2) Communication Doctrine: Artifacts, not Imports**

Tools do not call each other as a dependency chain. Instead, communication is via:

1. Artifact Interface (default)
- Inputs/outputs are files and structured manifests (plus optional JSONL events)
- This is the primary integration surface for pipelines
1. Service Interface (shared concerns)
- Tools may use QuackCore services (config, storage, registry, schema validation)
- Tools still emit artifacts to remain portable
1. Event Interface (optional)
- Tools may emit events.jsonl for observability/auditing
- Orchestrators may consume these for dashboards and “digital worker” traces

# **3) Tool Surface Doctrine: One CLI to Rule Them All**

To eliminate duplication and inconsistency:

**The Quack CLI Rule**

There is one canonical CLI entrypoint: quack.

- Tools do not build bespoke CLIs.
- Tools register commands into the quack CLI via a plugin/registry mechanism provided by QuackCore.

Examples:

- quack video cut …
- quack image thumbnail …
- quack tutorial init …
- quack machinima render …

Optional: tool-specific shims may exist (quackvideo, quackimage) but they are thin wrappers around quack <tool> ….

**Required verbs for every tool**

Every tool MUST implement at least:

- run — execute the primary operation
- validate — validate inputs and schemas
- doctor — verify environment dependencies (ffmpeg, fonts, GPU libs, etc.)
- explain — print planned steps (dry-run narrative)

This yields consistency without killing flexibility.

# **4) Cloud Execution Doctrine: One Gateway, Not 12 Microservices**

Cloud mode is enabled via a single execution gateway.

**QuackRunner Rule (FastAPI)**

Introduce one service: QuackRunner (FastAPI), whose job is to:

- start tool runs
- track status
- expose logs
- index artifacts

It does not contain tool logic. It executes tools (via CLI or direct Python entrypoints).

Interfaces

- POST /runs (tool + args + inputs)
- GET /runs/{id} (status, logs)
- GET /runs/{id}/artifacts (artifact index / signed links)

This enables:

- remote execution
- queues/workers later
- consistent n8n integration via HTTP

**Artifact Store Rule**

In cloud mode, the artifact store is the integration backbone:

- S3-compatible object storage (or equivalent)
- Each run writes to a deterministic run directory/prefix
- The manifest is the source of truth

Tools don’t need to “talk to each other” in the cloud. They share artifacts.

# **5) Orchestration Doctrine: n8n and DuckTyper are Foremen**

**n8n Rule**

n8n orchestrates via:

- CLI nodes in local mode (quack …)
- HTTP nodes in cloud mode (QuackRunner /runs)

n8n does not call QuackCore internals. It calls the gateway or the CLI.

**DuckTyper Rule**

DuckTyper is the human control plane:

- interactive runs
- approvals
- re-runs (“redo option 2”)
- editorial choice points
- “explain what happened” views

DuckTyper calls tools via:

- CLI (local)
- HTTP (QuackRunner) and/or MCP (agent mode)

# **6) Agent Doctrine: Digital Workers are Orchestrators with Judgment**

Agents are not tools. Agents are decision-makers.

Agents live in Ring C and interact with tools through:

- quack CLI
- QuackRunner HTTP
- MCP (standard agent interface)

Agents:

- read artifacts + manifests
- decide next actions
- apply policies (editorial rules, brand rules, guardrails)
- log their reasoning/actions as events

Tools remain atomic; agents provide autonomy.

# **7) MCP Doctrine: MCP is an Adapter Surface, Not an Internal Dependency**

MCP is used to expose QuackVerse tools to LLM agents in a standardized way.

Rule

- MCP is exposed at the gateway layer (QuackRunner) or as a QuackCore adapter.
- MCP is not embedded into every tool.

So we support three stable “surfaces”:

- CLI surface (humans, local, CI)
- HTTP surface (n8n, cloud)
- MCP surface (agent tool calling)

# **8) Rendering Doctrine (PixiJS decision)**

PixiJS is a runtime adapter for machinima.

Rule

- QuackCore defines rendering contracts (capabilities)
- QuackMachinima defines beat/scene schemas and execution logic
- PixiJS lives as a runtime implementation under machinima (replaceable)

Core never renders.

# **9) IP Doctrine: Engine Public, Content Private**

**Open source (public, pedagogical, DevRel-safe)**

- QuackCore
- quack CLI framework + plugin registry
- QuackTools logic (minus proprietary assets/styles)
- QuackRunner gateway (FastAPI)
- MCP adapter layer
- templates, sample content, dummy worlds
- teaching scaffolding and sample quests

**Proprietary (moat)**

- Rod comics assets (characters, sprites, style packs)
- story registries + beat libraries
- signature branded templates and house style
- paid course content (AIPE / AI Automators Club)

Rule: The engine runs on content. The content never ships with the engine.

# **10) Operational Scenario Doctrine: Monday Morning Briefing**

A canonical workflow exists to validate the system end-to-end:

- collect AI news
- cluster and rank
- draft show agenda
- pitch a tutorial
- generate tutorial skeleton
- create promo assets
- stage/publish via approval

This workflow must be runnable:

- locally (CLI + disk artifacts)
- automated (n8n + QuackRunner + object storage)
- agent-assisted (DuckTyper + MCP)

# **11) Governance Rules (final non-negotiables)**

1. Core never renders pixels
2. Tools never orchestrate
3. UI never contains core logic
4. Tools don’t import tools
5. Capabilities are contracts
6. Runtimes are replaceable
7. Everything emits artifacts + manifests
8. One canonical CLI: quack
9. One cloud gateway: QuackRunner (FastAPI)
10. MCP lives at the gateway/adapter layer
11. Engine public, content private
12. Teaching is first-class

If you want, I can also produce the “implementation companion” to this doctrine:

- ADR-001 PixiJS as runtime adapter
- ADR-002 Single quack CLI + plugin registry
- ADR-003 QuackRunner FastAPI gateway
- ADR-004 MCP exposed via gateway
- ADR-005 Artifact manifest spec (Run Contract v1)

---

Below is a clean, final doctrine that incorporates all the decisions, clarifications, and future-facing intent we’ve discussed.

This is written as something you could realistically put in quackverse/doctrine/DOCTRINE.md and live with for many years.

# **The QuackVerse Doctrine**

An operating doctrine for AI-first edutainment, digital workers, and organizational leverage

# **0. Preamble**

QuackVerse exists to turn AI from demos into operating reality.

It is not a product, a startup, or a content brand.

It is a systemic way of building, teaching, and deploying AI-first organizations, expressed through tools, agents, media, and education.

This doctrine defines:

- what QuackVerse is
- what it is not
- how its parts interact
- where ownership, IP, and mission live
- and how it can scale from a solo creator to industry-wide adoption

# **1. The Core Belief**

AI is not a feature.

AI is not a chatbot.

AI is an operating system for modern organizations.

Those who win with AI will not be the ones with the best prompts, but the ones who:

- design systems
- standardize operations
- deploy digital workers
- and compound leverage over time

QuackVerse is built to serve that belief.

# **2. The Three Rings Model**

QuackVerse is structured into three concentric rings:

┌──────────────────────────────────────────┐
│        EXPERIENCES / ORCHESTRATION       │
│   DuckTyper · n8n · Agents · CI · Chat   │
├──────────────────────────────────────────┤
│              TOOLS (QuackTools)          │
│   Video · Image · Tutorial · Machinima   │
│   Distro · Newsletter · GTM · Research   │
├──────────────────────────────────────────┤
│              CORE (QuackCore)            │
│   Contracts · Capabilities · Registries  │
│   Config · IO · Teaching · Adapters      │
└──────────────────────────────────────────┘


**Ring A — Core (QuackCore)**

QuackCore is the kernel and governance layer.

It defines:

- contracts and schemas
- capability interfaces
- registries and discovery
- configuration, logging, IO
- teaching scaffolding
- adapter layers (HTTP, MCP)

Non-negotiables

- Core never renders pixels
- Core never contains IP or narrative
- Core defines what is possible, not what happens next

**Ring B — Tools (QuackTools)**

QuackTools are atomic, vertical workers.

Each tool:

- does one domain job well
- consumes structured inputs
- emits structured artifacts + manifests
- imports QuackCore, never other tools
- remains composable and pipeline-safe

Non-negotiables

- Tools never orchestrate workflows
- Tools never depend on other tools
- Tools communicate only via artifacts and schemas

**Ring C — Experiences (Control Planes)**

Experiences are orchestrators, not logic holders.

They include:

- DuckTyper (CLI + chat-based UX)
- n8n (visual automation)
- agents (digital workers with judgment)
- CI / cron / dashboards

Non-negotiables

- UI contains no core logic
- Orchestration and decision-making live here

# **3. Communication Doctrine**

There are only three sanctioned communication paths:

1. Artifact Interface (default)
    - Files + manifests + optional event logs
    - Deterministic, teachable, debuggable
2. 
3. Service Interface (shared concerns)
    - Tools may use QuackCore services (config, registry, storage)
    - Tools still emit artifacts
4. 
5. Adapter Interface (external)
    - HTTP (QuackRunner)
    - MCP (agent tool calling)
6. 

Tools never “talk” directly.

# **4. The Tool Surface Doctrine**

**One Canonical CLI**

There is exactly one canonical CLI surface:

quack <tool> <verb> [options]

Examples:

- quack video cut
- quack image thumbnail
- quack tutorial init
- quack machinima render

QuackCore provides the CLI framework.

QuackTools only register commands.

**Required verbs for every tool**

Every QuackTool must implement:

- run — execute
- validate — input/schema validation
- doctor — environment sanity check
- explain — dry-run narrative

This enforces consistency without killing flexibility.

# **5. Cloud Execution Doctrine**

**One Gateway: QuackRunner**

There is one cloud execution service: QuackRunner (FastAPI).

Responsibilities:

- start tool runs
- track status
- expose logs
- index artifacts

It executes tools via:

- CLI
- or direct Python entrypoints

n8n and agents talk to QuackRunner, not to tools directly.

**Artifact Store as the Backbone**

In cloud mode:

- all runs write to an object store
- manifests are the source of truth
- downstream steps read artifacts, not processes

This enables:

- scaling
- retries
- auditability
- AI “private equity” style rollouts

### QuackShowrunner Doctrine

QuackShowrunner is a Ring C experience focused on media production.

It is the “producer brain” for AI-first shows and edutainment pipelines.

Rules:

- QuackShowrunner never contains tool logic
- It orchestrates only via CLI / HTTP / MCP
- It consumes and produces artifacts
- It enforces editorial policy, not creativity

# **6. Agent Doctrine: Digital Workers**

Agents are not tools.

Agents are:

- orchestrators with judgment
- policy enforcers
- foremen for tools

They:

- read manifests and artifacts
- decide what to do next
- trigger tools via CLI / HTTP / MCP
- log decisions as events

Agents live in Ring C.

# **7. MCP Doctrine**

MCP is an adapter surface, not an internal dependency.

Rules:

- MCP is exposed at the gateway or adapter layer
- Tools do not implement MCP individually
- MCP allows LLMs to call QuackVerse tools safely

Surfaces supported:

- CLI (humans, local, CI)
- HTTP (n8n, cloud)
- MCP (agents)

# **8. Rendering Doctrine (PixiJS Decision)**

Rendering engines are replaceable runtimes.

Rules:

- QuackCore defines rendering capabilities
- QuackMachinima defines beat/scene schemas
- PixiJS is one runtime implementation
- Core never renders

# **9. Ownership & IP Doctrine**

**Organizational structure**

- Dreamhuggers → personal holding
- ducktyper-ai (GitHub org) → steward of the open ecosystem
- quackverse (monorepo) → the operating system
- f-squared.ai → faceless edutainment IP studio
- AI Automators Club → operator education
- AI Product Engineer → developer education (shared ownership)

**Engine vs IP**

Engine is public. IP is private.

- QuackVerse contains no branded narratives
- Everduck / Rod comics live exclusively under f-squared.ai
- f-squared.ai depends on QuackVerse
- QuackVerse never depends on f-squared.ai

Example private repos:

- everduck-assets
- everduck-stories
- everduck-style

This preserves:

- legal clarity
- open-source safety
- long-term optionality

# **10. Edutainment Doctrine**

QuackVerse operates in edutainment, not pure education.

Different surfaces teach differently:

- DuckTyper → systems thinking
- AIPE → developers
- AAC → operators / GTM
- Everduck → narrative intuition

Same engine.

Different pedagogical interfaces.

# **11. Strategic North Star**

QuackVerse is designed to enable:

- AI-first media houses
- AI operators installing leverage in companies
- agent engineering in enterprise contexts
- AI private equity–style rollups via standardized operations

# **12. Final Governance Rules (Non-Negotiable)**

1. Core never renders pixels
2. Tools never orchestrate
3. UI never contains core logic
4. Tools never import tools
5. Capabilities are contracts
6. Runtimes are replaceable
7. Everything emits artifacts
8. One canonical CLI (quack)
9. One cloud gateway (QuackRunner)
10. MCP lives at the adapter layer
11. Engine public, content private
12. Teaching is first-class

# **13. Closing Statement**

DuckTyper is the interface.

QuackVerse is the operating system.

f-squared.ai owns the stories.

Dreamhuggers owns the future.

This doctrine exists so that:

- projects may come and go
- brands may evolve
- collaborators may change

…but the system, mission, and leverage compound.