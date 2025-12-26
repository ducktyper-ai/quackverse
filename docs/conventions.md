# QuackCore v2 Conventions & Standards

**Status:** Approved v2
**Scope:** All Capability Development

## 1. Capability Status Semantics
We use three statuses.

| Status | Meaning | Action for n8n | Example |
| :--- | :--- | :--- | :--- |
| **`success`** | The task completed successfully. | Continue flow | `video_sliced.mp4` created. |
| **`skipped`** | The task decided *not* to act based on valid logic. **Not an error.** | Branch to "Log/Ignore" | Video < 5s; no slicing needed. |
| **`error`** | The task failed (exception, invalid state, infra failure). | Branch to "Retry/Alert" | FFmpeg missing; API timeout. |

## 2. Error Codes (`machine_message`)
The `machine_message` field **MUST** be a `QC_*` code. Never free text.
Free text explanations belong in `human_message`.

* **`QC_SYS_*`**: System/Python level errors (e.g., `QC_SYS_IMPORT_ERROR`)
* **`QC_VAL_*`**: Input validation errors (e.g., `QC_VAL_FILE_MISSING`)
* **`QC_EXT_*`**: External service errors (e.g., `QC_EXT_OPENAI_RATE_LIMIT`)
* **`QC_POL_*`**: Policy violations (e.g., `QC_POL_CONTENT_FILTERED`)
* **`QC_CFG_*`**: Config/Preset resolution errors (e.g., `QC_CFG_PRESET_NOT_FOUND`)

## 3. Configuration Rules
1. **No Defaults in Code:** Capability functions never have default arguments like `model="gpt-4"`.
2. **Precedence:** Request > Preset > Policy File > Model Defaults.
3. **Deep Merge:** Configs are merged recursively. Setting one field in a preset does not wipe its siblings.
4. **Explicit Disable:** Use flags (e.g., `enable_feature=False`), never `None` implies disable.

## 4. Architectural Boundaries
When building a new capability, check this table:

| Question | If YES → Put logic in... | If NO → Put logic in... |
| :--- | :--- | :--- |
| Does this decide "what happens next?" | **n8n** | QuackCore |
| Is this logic reusable across tools? | **QuackCore** | n8n |
| Is this about safety, formats, or retries? | **QuackCore** | n8n |
| Is this a generic API call (e.g. OpenAI)? | **lib/integrations/** | capabilities/ |