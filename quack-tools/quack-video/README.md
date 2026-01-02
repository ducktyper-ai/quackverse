# 🦆 QuackVideo

**A QuackTool for Deterministic Video Processing and Asset Generation**

> **QuackVideo turns raw video inputs into structured, auditable video artifacts.**
> It does not plan workflows. It does not publish. It does not decide what matters.

---

## 🧠 What QuackVideo Is

QuackVideo is a **Ring B QuackTool**.

It consumes **video inputs** and produces **video-derived artifacts**, such as:

* processed video files
* extracted clips
* frames and thumbnails
* captions and transcripts
* per-run manifests describing outputs

QuackVideo answers one question only:

> **“Given these video inputs and parameters, produce these video artifacts.”**

---

## ❌ What QuackVideo Is Not

QuackVideo is **not**:

* a video editor UI
* a content strategy engine
* a publishing system
* a workflow orchestrator
* a social-media automation tool
* an AI agent

It never:

* decides *what* clips to publish
* talks to SaaS platforms directly
* calls other tools
* stores canonical business state

Those responsibilities belong to **Ring C** (Temporal, Agents, Quackchat, n8n).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackVideo ◀                     │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: FS · Config · Results · IO     │
└────────────────────────────────────────────┘
```

QuackVideo:

* imports **QuackCore only**
* is executed via **QuackRunner**
* emits **artifacts + manifest**
* is orchestrated externally

---

## 🧰 Canonical CLI Surface

QuackVideo does **not** expose its own CLI.

All interaction happens via the **single canonical CLI**:

```bash
quack video <verb> [options]
```

Every QuackTool implements the standard verbs:

* `run`
* `validate`
* `doctor`
* `explain`

---

## 🚀 Common Commands

### Process a video

```bash
quack video run input.mp4 --out ./dist/video
```

Produces:

* processed video(s)
* derived assets (clips, frames, captions, etc.)
* a manifest describing all outputs

---

### Validate inputs & parameters

```bash
quack video validate input.mp4
```

Checks:

* file existence and format
* FFmpeg availability
* configuration validity
* deterministic output constraints

---

### Diagnose environment readiness

```bash
quack video doctor
```

Reports:

* FFmpeg / codec availability
* GPU / acceleration detection (if applicable)
* filesystem permissions
* optional dependency status

---

### Explain an output bundle

```bash
quack video explain ./dist/video/<run-id>/
```

Explains:

* what artifacts were generated
* where the manifest lives
* how downstream systems should consume outputs

---

## 🎥 Supported Capabilities (Indicative)

Depending on configuration, QuackVideo may produce:

* **Video preprocessing**

  * audio normalization
  * noise reduction
  * color correction
* **Clip extraction**

  * fixed-duration clips
  * timestamp-based segments
* **Frame extraction**

  * thumbnail candidates
  * still frames
* **Captions & transcripts**

  * subtitle files
  * aligned text artifacts
* **Format conversion**

  * resolution
  * aspect ratio
  * codec/container changes

All outputs are **deterministic and reproducible**.

---

## 📦 Output Artifacts

Each run produces an **artifact bundle** with a manifest.

Example:

```text
dist/
└── video/
    └── run-2024-03-21T10-32-00/
        ├── processed.mp4
        ├── clips/
        │   ├── clip_01.mp4
        │   └── clip_02.mp4
        ├── frames/
        │   └── thumbnail_01.png
        ├── captions.vtt
        ├── transcript.json
        └── manifest.json
```

### Manifest Is the System of Record

The `manifest.json` contains:

* inputs
* parameters
* produced artifacts
* checksums
* timestamps

If there is no manifest, **the run does not exist**.

---

## 🔗 How QuackVideo Fits into Larger Workflows

QuackVideo never orchestrates.

Typical flow:

1. **Quackchat** captures intent (“process episode footage”)
2. **Temporal** manages workflow state and approvals
3. **QuackRunner** executes `quack video run …`
4. Artifacts + manifest are stored
5. **Agents** interpret outputs and propose next steps
6. **n8n / integrations** perform side effects (upload, notify, publish)

QuackVideo remains a pure worker throughout.

---

## ⚙️ Configuration

QuackVideo is configured via **QuackCore configuration primitives**.

Example (indicative):

```yaml
video:
  processing:
    audio:
      normalize: true
      noise_reduction: true
    video:
      color_correction: true
  clips:
    enabled: true
    duration: 60
  captions:
    enabled: true
```

Configuration is:

* typed
* validated
* versioned
* passed in by the orchestrator

---

## 🧭 Governance Rules

1. QuackVideo is a deterministic worker
2. No workflow orchestration
3. No SaaS side effects
4. Emits artifacts + manifest
5. Uses QuackCore only
6. Runs via `quack` CLI only

---

## 🧠 Closing Statement

QuackVideo is **not a video product**.

It is a **video worker** inside the DuckTyper AI Operating System.

It transforms raw video into structured artifacts that can be:

* reasoned about by agents
* orchestrated by Temporal
* published by integrations
* audited long after execution

It does not decide.

It produces.
