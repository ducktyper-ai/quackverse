# 🦆 QuackBrandPack

**A QuackTool for Deterministic Brand Constraint Application and Safe Content Reuse**

> **QuackBrandPack applies brand-specific rules to neutral content artifacts.**
> It does not invent messaging.
> It does not choose audiences.
> It does not decide strategy.

---

## 🧠 What QuackBrandPack Is

QuackBrandPack is a **Ring B QuackTool**.

It consumes **neutral, already-derived artifacts** (text, captions, images, clips, metadata) and produces **brand-specific variants** by applying explicit constraints such as:

* tone and voice rules
* CTA policies
* disclosure requirements
* employer or sponsor restrictions
* safety and compliance constraints

Each run emits:

* per-brand artifact bundles
* a manifest describing exactly which constraints were applied

QuackBrandPack answers one question only:

> **“Given this neutral artifact and these brand rules, produce compliant brand-specific variants.”**

---

## ❌ What QuackBrandPack Is Not

QuackBrandPack is **not**:

* a brand strategy engine
* a creative writing tool
* a social media planner
* a legal advisor
* a publishing system
* a workflow orchestrator
* an agent with judgment

It never:

* decides *what* content should exist
* invents tone beyond configured rules
* chooses platforms or timing
* publishes content
* negotiates employer boundaries
* stores canonical state

All judgment, selection, and approval live in **Ring C**
(Agents, Temporal, Quackchat).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackBrandPack ◀                 │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: Schemas · Config · Results    │
└────────────────────────────────────────────┘
```

QuackBrandPack:

* imports **QuackCore only**
* is executed via **QuackRunner**
* emits **artifacts + manifest**
* remains stateless across runs

---

## 🧰 Canonical CLI Surface

QuackBrandPack does **not** expose its own CLI.

All execution happens via the **single canonical CLI**:

```bash
quack brandpack <verb> [options]
```

Every QuackTool implements the standard verbs:

* `run`
* `validate`
* `doctor`
* `explain`

---

## 🚀 Common Commands

### Apply brand constraints to artifacts

```bash
quack brandpack run neutral_bundle/ --brands brands.yaml --out ./dist/brandpack
```

Produces:

* one artifact bundle per brand
* rewritten / modified assets as required
* a manifest recording all applied rules

---

### Validate inputs and brand rules

```bash
quack brandpack validate neutral_bundle/ --brands brands.yaml
```

Checks:

* brand configuration schemas
* rule completeness
* forbidden-content coverage
* determinism guarantees

---

### Diagnose environment readiness

```bash
quack brandpack doctor
```

Reports:

* configuration resolution
* rule engine availability
* filesystem permissions

---

### Explain a brandpack output

```bash
quack brandpack explain ./dist/brandpack/<run-id>/
```

Explains:

* which brands were generated
* which rules were applied per brand
* what changed relative to the neutral input
* how downstream systems should consume outputs

---

## 🏷️ Supported Brand Targets (Indicative)

QuackBrandPack is designed to support **multiple concurrent properties** safely, including:

* **Prof Rod**
* **Rasa**
* **AI Automators Club (AIAC)**
* **AI Product Engineer (AIPE)**
* **Agent Engineering Community**
* **billion.robots**

Each brand is treated as a **rule set**, not a personality.

---

## 🔐 What Brand Rules Can Express

Brand rules are **explicit and declarative**, for example:

* allowed / forbidden claims
* mandatory disclaimers
* CTA formats and placement
* hashtag policies
* emoji usage rules
* tone constraints (formal, neutral, playful)
* employer separation requirements

> **Important:**
> QuackBrandPack enforces rules.
> It does not invent them.

---

## 📦 Output Artifacts

Each run produces a **brand-segmented artifact bundle**.

Example:

```text
dist/
└── brandpack/
    └── run-2025-03-22T11-03-51/
        ├── prof-rod/
        │   ├── post.txt
        │   ├── caption.txt
        │   └── manifest.json
        ├── rasa/
        │   ├── post.txt
        │   ├── disclaimer.txt
        │   └── manifest.json
        ├── aiac/
        │   └── post.txt
        └── manifest.json
```

---

### Manifest Is the System of Record

Each `manifest.json` captures:

* source artifact references and hashes
* brand rule identifiers and versions
* applied transformations
* rejected or modified elements
* timestamps and checksums

If a rule was applied, **it is recorded**.
If it is not recorded, **it did not happen**.

---

## 🔗 How QuackBrandPack Fits into Workflows

QuackBrandPack never orchestrates.

Typical flow:

1. **Upstream tools** produce neutral artifacts
   (QuackDistro, QuackQuote, QuackClip, QuackImage)
2. **Quackchat** captures intent (“apply brand rules”)
3. **Temporal** manages sequencing and approvals
4. **QuackRunner** executes `quack brandpack run`
5. Brand-specific artifacts + manifests are written
6. **Agents** decide what to publish
7. **n8n / integrations** perform side-effects

QuackBrandPack exits immediately after producing artifacts.

---

## ⚙️ Configuration (Indicative)

Configuration is provided via **QuackCore config primitives**.

```yaml
brands:
  prof_rod:
    tone: playful
    cta: "Follow Prof Rod for more"
    disclaimers: []
  rasa:
    tone: professional
    disclaimers:
      - "Views are personal and do not represent Rasa"
    forbidden_topics:
      - competitors
      - roadmap speculation
  billion_robots:
    tone: minimal
    emojis: false
```

Configuration is:

* typed
* validated
* auditable
* environment-agnostic

---

## 🧭 Governance Rules

1. QuackBrandPack applies constraints, not strategy
2. No creative decision-making
3. No publishing or scheduling
4. No SaaS side-effects
5. Emits artifacts + manifest
6. Uses QuackCore only
7. Runs via the canonical `quack` CLI

---

## 🧠 Closing Statement

QuackBrandPack is **not branding**.

It is a **safety and reuse mechanism** inside the DuckTyper AI Operating System.

It exists so that:

* one idea can safely serve many properties
* employer boundaries are enforced mechanically
* compliance is provable
* reuse does not require manual policing

In DuckTyper:

* Agents decide *what* to say
* Humans decide *why*
* **QuackBrandPack ensures it is safe to say it — everywhere**

It does not judge.

It enforces.
