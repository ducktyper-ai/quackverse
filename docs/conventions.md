# QuackCore v2 Conventions & Standards

**Status:** Draft v1
**Scope:** All Capability Development

## 1. Capability Status Semantics
We use three statuses. Do not invent new ones.

| Status | Meaning | Action for n8n | Example |
| :--- | :--- | :--- | :--- |
| **`success`** | The specific task completed successfully. | Continue flow | `video_sliced.mp4` created. |
| **`skipped`** | The task ran but decided *not* to act based on valid logic. **This is NOT an error.** | Branch to "Log/Ignore" | Video was already short enough; no slicing needed. |
| **`error`** | The task failed due to an exception, invalid state, or infrastructure failure. | Branch to "Retry/Alert" | FFmpeg binary missing; S3 upload timeout. |

## 2. Error Code Format (`machine_message`)
Error codes are strings used by n8n to route logic (e.g., "If `QC_AUTH_*`, alert admin").
Format: `QC_{CATEGORY}_{SPECIFIC_ERROR}`

* **`QC_SYS_*`**: System/Python level errors (e.g., `QC_SYS_IMPORT_ERROR`, `QC_SYS_TIMEOUT`)
* **`QC_VAL_*`**: Input validation errors (e.g., `QC_VAL_FILE_MISSING`, `QC_VAL_INVALID_DURATION`)
* **`QC_EXT_*`**: External service errors (e.g., `QC_EXT_OPENAI_RATE_LIMIT`, `QC_EXT_DRIVE_AUTH_FAIL`)
* **`QC_POL_*`**: Policy violations that force a hard stop (e.g., `QC_POL_CONTENT_FILTERED`)

## 3. Configuration & Defaults
* **Precedence:** Runtime Input > Preset > Policy File > Code Defaults.
* **The "None" Rule:** `None` in an input argument means **"Unset / Use Default."**
* **Disabling:** If you want to turn a feature off, use an explicit boolean flag (e.g., `enable_transcription=False`), never `transcription_model=None`.

## 4. Architectural Boundaries
When building a new capability, check this table:

| Question | If YES → Put logic in... | If NO → Put logic in... |
| :--- | :--- | :--- |
| Does this decide "what happens next?" | **n8n** | QuackCore |
| Is this logic reusable across tools? | **QuackCore** | n8n |
| Is this about safety, formats, or retries? | **QuackCore** | n8n |
| Is this a generic API call (e.g. OpenAI)? | **lib/integrations/** | capabilities/ |