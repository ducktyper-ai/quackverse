# 🦆 QuackAudio

**A QuackTool for Deterministic Audio Processing, Voice Rendering, and Audio Asset Production**

> **QuackAudio produces reproducible audio artifacts from structured inputs.**
> It does not compose stories.
> It does not direct performances.
> It does not decide creative intent.

---

## 🧠 What QuackAudio Is

QuackAudio is a **Ring B QuackTool**.

It consumes **audio inputs and audio specifications** and produces **audio artifacts**, such as:

* mastered podcast episodes
* stitched intro / outro audio
* deterministic character voice tracks
* narration and voice-over assets
* normalized audio stems for video and animation

Each execution emits:

* audio files
* a manifest describing how they were produced

QuackAudio answers one question only:

> **“Given these audio inputs and parameters, produce these audio artifacts.”**

---

## ❌ What QuackAudio Is Not

QuackAudio is **not**:

* a DAW or audio editor UI
* a storytelling or script-writing engine
* a casting or creative direction system
* a publishing or distribution tool
* a workflow orchestrator
* an autonomous agent

It never:

* decides what should be said
* writes dialogue or scripts
* chooses emotional tone
* publishes audio to platforms
* triggers other tools
* stores canonical business state

Those responsibilities live in **Ring C**
(Agents, Temporal, Quackchat, n8n).

---

## 🧭 Position in the DuckTyper / QuackVerse Doctrine

```
┌────────────────────────────────────────────┐
│        RING C — EXPERIENCES / CONTROL      │
│  Quackchat · Temporal · n8n · Agents       │
├────────────────────────────────────────────┤
│        RING B — TOOLS (WORKERS)            │
│        ▶ QuackAudio ◀                     │
├────────────────────────────────────────────┤
│        RING A — CORE (KERNEL)              │
│  QuackCore: FS · Config · Results · IO     │
└────────────────────────────────────────────┘
```

QuackAudio:

* imports **QuackCore only**
* is executed via **QuackRunner**
* emits **artifacts + manifest**
* remains stateless across runs

---

## 🧰 Canonical CLI Surface

QuackAudio does **not** expose a standalone CLI.

All execution happens via the **single canonical CLI**:

```bash
quack audio <verb> [options]
```

Every QuackTool implements the required verbs:

* `run`
* `validate`
* `doctor`
* `explain`

---

## 🚀 Common Commands

### Produce audio artifacts

```bash
quack audio run audio_spec.yaml --out ./dist/audio
```

Produces:

* mastered audio files
* stitched segments (if configured)
* voice tracks (if configured)
* a manifest describing all outputs

---

### Validate inputs and configuration

```bash
quack audio validate audio_spec.yaml
```

Checks:

* input file availability
* script / voice references
* backend configuration
* deterministic constraints
* output schema compatibility

---

### Diagnose environment readiness

```bash
quack audio doctor
```

Reports:

* audio backend availability (FFmpeg, SoX, etc.)
* TTS runtime availability (if enabled)
* codec support
* filesystem permissions

---

### Explain an audio bundle

```bash
quack audio explain ./dist/audio/<run-id>/
```

Explains:

* what audio was produced
* which inputs were used
* which voices and settings were applied
* how downstream systems should consume outputs

---

## 🔊 Supported Capabilities (Indicative)

Depending on configuration, QuackAudio can produce:

### 🎙 Podcast & Long-Form Audio

* loudness normalization
* noise reduction
* compression and EQ
* stitching intros / outros
* deterministic mastering profiles

---

### 🗣 Character & Narration Voices

* deterministic TTS voice tracks
* character-specific voice mappings (e.g. Quackster, Mator)
* multi-language narration
* timing-aligned speech assets for animation

> **Important:**
> Voice selection and dialogue content are **inputs**, not decisions.

---

### 🎬 Audio Assets for Video & Machinima

* narration stems
* dialogue tracks
* ambient layers
* timing-aligned audio for QuackMachinima

QuackAudio produces **audio only**.
Synchronization happens downstream.

---

## 📦 Output Artifacts

Each run produces an **audio artifact bundle** with a canonical manifest.

Example:

```text
dist/
└── audio/
    └── run-2025-03-22T09-18-04/
        ├── podcast_master.wav
        ├── intro.wav
        ├── outro.wav
        ├── voices/
        │   ├── quackster.wav
        │   └── mator.wav
        └── manifest.json
```

---

### Manifest Is the System of Record

The `manifest.json` captures:

* input references and hashes
* audio processing parameters
* voice mappings and backend versions
* produced artifacts
* checksums and timestamps

If it is not in the manifest, **the audio does not exist**.

---

## 🔗 How QuackAudio Fits into Larger Workflows

QuackAudio never orchestrates.

Typical flow:

1. **Quackchat** captures intent (“produce podcast audio”)
2. **Temporal** coordinates workflow state
3. **QuackRunner** executes `quack audio run`
4. Audio artifacts + manifest are written
5. **Agents** reason over outputs
6. **Downstream tools** consume audio:

   * **QuackVideo** → video assembly
   * **QuackMachinima** → lip-sync and animation
   * **n8n / integrations** → publishing

QuackAudio exits immediately after producing artifacts.

---

## ⚙️ Configuration (Indicative)

Configuration uses **QuackCore primitives** and is injected at runtime.

```yaml
audio:
  mastering:
    normalize_lufs: -16
    noise_reduction: true
  stitching:
    intro: assets/audio/intro.wav
    outro: assets/audio/outro.wav
  voices:
    quackster:
      provider: tts
      voice_id: quackster_v1
    mator:
      provider: tts
      voice_id: mator_v1
```

Configuration is:

* typed
* validated
* auditable
* environment-agnostic

---

## 🧭 Governance Rules

1. QuackAudio is a deterministic worker
2. No creative decision-making
3. No orchestration or sequencing
4. No SaaS side-effects
5. Emits artifacts + manifest
6. Uses QuackCore only
7. Runs via the canonical `quack` CLI

---

## 🧠 Closing Statement

QuackAudio is **not a sound studio**.

It is an **audio worker** inside the DuckTyper AI Operating System.

It produces:

* reliable podcast audio
* reproducible character voices
* animation-ready sound assets

So that:

* agents can reason
* Temporal can orchestrate
* QuackMachinima can animate
* humans can focus on story and taste

It does not perform.

It produces sound — **exactly as specified**.
