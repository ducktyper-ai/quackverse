# 🦆 QuackImage

**A QuackTool for Deterministic Image Generation and Visual Asset Production**

> **QuackImage transforms structured inputs into reproducible image artifacts.**
> It does not design campaigns. It does not publish content. It does not decide aesthetics.

---

## 🧠 What QuackImage Is

QuackImage is a **Ring B QuackTool**.

It consumes **image specifications** and produces **image artifacts**, such as:

* banners and thumbnails
* social-media-ready images
* backgrounds and overlays
* derived image assets with safe areas

Every run produces:

* image files
* a manifest describing how they were generated

QuackImage answers one question only:

> **“Given these image inputs and parameters, produce these image artifacts.”**

---

## ❌ What QuackImage Is Not

QuackImage is **not**:

* a design tool or editor UI
* a brand strategy engine
* a publishing or distribution system
* a workflow orchestrator
* a creative agent

It never:

* decides what image to generate
* chooses copy or messaging
* talks to SaaS platforms
* calls other tools
* stores canonical state

Those responsibilities belong to **Ring C** (Agents, Temporal, Quackchat, n8n).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackImage ◀                     │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: FS · Config · Results · IO     │
└────────────────────────────────────────────┘
```

QuackImage:

* imports **QuackCore only**
* runs via **QuackRunner**
* emits **artifacts + manifest**
* is orchestrated externally

---

## 🧰 Canonical CLI Surface

QuackImage does **not** expose its own CLI.

All usage goes through the **single canonical CLI**:

```bash
quack image <verb> [options]
```

Every QuackTool implements the standard verbs:

* `run`
* `validate`
* `doctor`
* `explain`

---

## 🚀 Common Commands

### Generate image artifacts

```bash
quack image run spec.yaml --out ./dist/images
```

Produces:

* generated images
* derived variants (sizes, formats)
* a manifest describing all outputs

---

### Validate inputs and configuration

```bash
quack image validate spec.yaml
```

Checks:

* configuration schema
* asset availability (fonts, overlays)
* deterministic output constraints
* filesystem permissions

---

### Diagnose environment readiness

```bash
quack image doctor
```

Reports:

* image backend availability (e.g. Cairo)
* font loading status
* screenshot dependencies (if enabled)
* platform-specific constraints

---

### Explain an output bundle

```bash
quack image explain ./dist/images/<run-id>/
```

Explains:

* which images were produced
* how they were derived
* where the manifest lives
* how downstream systems should consume them

---

## 🖼️ Supported Capabilities (Indicative)

Depending on configuration, QuackImage can produce:

* **Background generation**

  * gradients
  * geometric / generative patterns
* **Overlays**

  * local images
  * screenshots
  * shapes and frames
* **Text rendering**

  * titles and captions
  * font selection
  * safe-area constraints
* **Image variants**

  * multiple resolutions
  * aspect ratios
  * platform-specific formats

All outputs are **deterministic and reproducible**.

---

## 📦 Output Artifacts

Each run produces an **artifact bundle** with a manifest as the system of record.

Example:

```text
dist/
└── images/
    └── run-2025-03-21T14-02-11/
        ├── banner.webp
        ├── banner_16x9.webp
        ├── banner_9x16.webp
        ├── thumbnail.png
        ├── overlays/
        │   └── screenshot.png
        └── manifest.json
```

### Manifest Is Canonical

The `manifest.json` records:

* input specification
* parameters
* generated assets
* checksums
* timestamps

If there is no manifest, **the image does not exist**.

---

## 🔗 How QuackImage Fits into Larger Workflows

QuackImage never orchestrates.

Typical flow:

1. **Quackchat** captures intent (“generate thumbnail”)
2. **Temporal** manages workflow state and approvals
3. **QuackRunner** executes `quack image run …`
4. Artifacts + manifest are written
5. **Agents** interpret outputs and propose next steps
6. **n8n / integrations** perform side-effects (upload, publish, notify)

QuackImage remains a pure worker throughout.

---

## ⚙️ Configuration

QuackImage is configured via **QuackCore configuration primitives**.

Example (indicative):

```yaml
image:
  canvas:
    width: 1792
    height: 1024
  background:
    type: gradient
    colors: ["#FF6B6B", "#4ECDC4"]
  text:
    enabled: true
    font: "NotoSans"
    safe_area: true
  overlay:
    enabled: true
    position: center
```

Configuration is:

* typed
* validated
* versioned
* injected by the orchestrator

---

## 🧭 Governance Rules

1. QuackImage is a deterministic worker
2. No workflow orchestration
3. No SaaS side effects
4. Emits artifacts + manifest
5. Uses QuackCore only
6. Runs via the canonical `quack` CLI

---

## 🧠 Closing Statement

QuackImage is **not a design product**.

It is an **image worker** inside the DuckTyper AI Operating System.

It produces reproducible visual assets that can be:

* reasoned about by agents
* orchestrated by Temporal
* rendered by Quackchat
* published by integrations
* audited long after execution

It does not decide aesthetics.

It produces images.