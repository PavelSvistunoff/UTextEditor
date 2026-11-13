# UTextEditor — open tasks

Only unfinished work is listed. Inspect existing code and tests before changing it; historical results live in [docs/](docs/) and [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md). Follow [AGENTS.md](AGENTS.md) and the [Clean Code rules](docs/clean-code-codex.md).

## Partially completed subtasks
- [~] **TASK-032.01** — Inventory untranslated UI strings, including dynamic service errors; identify each owning widget and reproducible path.
- [~] **TASK-032.02** — Move inventoried visible strings to the correct Qt translation context; preserve placeholders/IDs and test Ukrainian runtime behavior.
- [~] **TASK-032.04** — Translate typed dialogs/errors/status for invalid UTF-8, binary/missing files, save conflicts, project/export and AI failures without losing diagnostic details or dirty data. [Localization evidence](docs/localization-accessibility-checkpoint.md)
- [~] **TASK-034.03** — Check dialog initial/return focus, Tab order, Enter/Esc and cancellation; fix/retest issues.
