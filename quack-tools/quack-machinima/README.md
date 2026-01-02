Below is a **doctrine-final, drop-in `README.md` for `quackverse/quack-tools/quack-machinima`**.

This positions **QuackMachinima** correctly as a **deterministic rendering worker**, keeps PixiJS in the *right place*, and cleanly separates it from Everduck IP, agents, and orchestration.

---

# 🎥 **QuackMachinima**

**Deterministic Scene & Animation Renderer for the QuackVerse**

> **QuackMachinima renders.**
> It does not write stories.
> It does not plan scenes.
> It does not decide pacing.
>
> Given a **scene manifest** and **assets**, it produces **video artifacts** — reliably and repeatably.

---

## 🧠 What QuackMachinima Is

**QuackMachinima is a QuackTool** responsible for **turning structured scene manifests into rendered video outputs**.

It is the **rendering worker** of the QuackVerse.

QuackMachinima answers one question only:

> **“Given this scene description and these assets, render the result.”**

---

## ❌ What QuackMachinima Is Not

QuackMachinima is **not**:

* a storytelling engine
* a screenplay generator
* an agent
* a workflow engine
* a video editor UI
* an asset repository
* an IP container

It **never**:

* decides what scenes exist
* chooses camera angles creatively
* modifies story structure
* talks to CRMs or docs
* coordinates pipelines

Those decisions live elsewhere by doctrine.

---

## 🧭 Position in the QuackVerse

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES                │
│  Temporal · Agents · QuackRunner           │
│  Quackchat                                │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackMachinima ◀                 │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: Contracts · IO · Schemas       │
└────────────────────────────────────────────┘
```

**QuackMachinima lives in Ring B.**

It is invoked by orchestration layers and exits after producing artifacts.

---

## 🎬 Core Responsibility

QuackMachinima performs **deterministic rendering**.

### Inputs

* **Scene Manifest**

  * scenes
  * beats
  * timings
  * camera instructions
  * animation directives
* **Asset References**

  * sprites
  * backgrounds
  * audio
  * fonts
* **Render Configuration**

  * resolution
  * frame rate
  * output format
  * runtime backend

### Outputs

* rendered video files (MP4 / WebM)
* optional intermediate frames
* render metadata
* **RenderManifest** describing all outputs

---

## 🧠 Rendering Doctrine

### Engine-Agnostic by Design

QuackMachinima does **not** hardcode a single renderer.

* **PixiJS** is the **reference runtime**
* Other runtimes may be added later (e.g. Three.js, WebGPU)

The **rendering engine is a runtime**, not a contract.

> **QuackCore defines the schema.
> QuackMachinima executes it.
> Everduck supplies the content.**

---

## 🎨 PixiJS and Everduck (Important Boundary)

* **PixiJS runtime code** lives in **QuackMachinima**
* **Everduck assets, worlds, stories** live in a **separate proprietary repo**
* QuackMachinima consumes Everduck assets **only via paths / object storage**

This enforces the doctrine:

> **Engine public. Content private.**

---

## 🧠 QuackMachinima vs Agents

| Aspect   | QuackMachinima   | Agent               |
| -------- | ---------------- | ------------------- |
| Role     | Render           | Decide              |
| Input    | Scene manifest   | Context + artifacts |
| Output   | Video + manifest | Decisions           |
| Judgment | ❌ None           | ✅ Yes               |
| State    | Stateless        | Long-lived          |

Agents decide **what** to render.
QuackMachinima renders **exactly that**.

---

## 🧠 QuackMachinima vs Video Editors

QuackMachinima is **not a creative editor**.

* no timelines
* no interactive scrubbing
* no drag & drop
* no hidden heuristics

All creativity must be **explicit in the manifest**.

This makes renders:

* reproducible
* auditable
* retryable
* agent-readable

---

## 🧠 Execution Model

QuackMachinima is **never run directly** in production.

Canonical execution:

```
Temporal → QuackRunner → QuackMachinima
```

* **Temporal** owns sequencing and retries
* **QuackRunner** executes and tracks the run
* **QuackMachinima** renders and exits

---

## 🧠 Artifacts & Manifests

Every run must emit:

### Artifacts

* final video(s)
* optional frame dumps
* logs

### RenderManifest

Includes:

* scene manifest hash
* asset references
* render settings
* runtime engine + version
* output file list
* checksums

> **If it didn’t emit a RenderManifest, it didn’t render.**

---

## 🧠 Tool Interface

### Canonical CLI

QuackMachinima registers commands with the canonical `quack` CLI:

```
quack machinima render \
  --scene-manifest scene.json \
  --assets s3://everduck-assets/ \
  --out s3://renders/episode-001/
```

---

### Required Verbs

* `render` — perform rendering
* `validate` — validate scene manifest and assets
* `doctor` — check runtime environment (GPU, codecs, fonts)
* `explain` — describe inputs, outputs, and constraints

---

## 📦 Repository Structure

```text
quack-machinima/
├── src/
│   ├── runtime/          # PixiJS renderer implementation
│   ├── loaders/          # Asset loaders
│   ├── timeline/         # Deterministic beat execution
│   ├── export/           # Video encoding
│   └── cli.py
│
├── schemas/
│   ├── scene_manifest.json
│   └── render_manifest.json
│
├── tests/
├── README.md
```

---

## 🔗 Dependencies

QuackMachinima:

* imports **QuackCore** (schemas, result envelopes)
* depends on **PixiJS** (runtime)
* depends on codecs (FFmpeg, etc.)
* has **no dependency** on:

  * agents
  * Quackchat
  * CRM
  * docs systems

---

## 🎓 Pedagogical Mandate

QuackMachinima is a **teaching tool**.

It should make explicit:

* how scene graphs map to animation
* how timing and beats work
* how rendering decisions affect output
* how deterministic rendering differs from creative editing

Hidden magic is considered a bug.

---

## 🧭 Governance Rules (Non-Negotiable)

1. No story logic
2. No planning or judgment
3. Deterministic rendering only
4. Assets passed by reference
5. Emit RenderManifest always
6. Engine-agnostic contracts
7. CLI-first interface
8. Stateless per run

---

## 🧠 Closing Statement

**QuackMachinima is the camera and projector.**

It does not write the script.
It does not direct the actors.
It does not decide the cut.

It renders — faithfully, repeatably, audibly.

That separation is what allows
AI agents to create worlds
without losing control of the machine.