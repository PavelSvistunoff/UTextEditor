# UTextEditor — open tasks

Only unfinished work is listed. Inspect existing code and tests before changing it; historical results live in [docs/](docs/) and [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md). Follow [AGENTS.md](AGENTS.md) and the [Clean Code rules](docs/clean-code-codex.md).

**Workflow:** Pick 1–4 related tickets from one parent; preserve dirty text, undo, project IDs, file/transaction safety and AI consent/stale guards. Run focused tests, then the full offline suite when practical (`QT_QPA_PLATFORM=offscreen python -m pytest`); for translations use [README instructions](README.md#interface-localization). Record actual results, changed files and remaining blockers in the checkpoint. `[~]` = partial; `[ ]` = open. Do not claim native verification from offscreen tests.

**Order:** Finish TASK-032 localization → TASK-027.03 and TASK-030.03 native latency/keyboard work → TASK-034 accessibility → remaining `.V2` checks. The independent-writer save race is tracked separately in [save coordination](docs/save-coordination.md), not fixed by these tickets.

## Partially completed subtasks

- [~] **TASK-016.05** — Confirm Ctrl+Tab / Ctrl+Shift+Tab work on native Linux/macOS with no conflicts, including keyboard and assistive technology; offscreen tests already pass. [Evidence](docs/tab-navigation-verification.md)
- [~] **TASK-027.03** — Measure Markdown preview capture/render/HTML installation and timer gaps on small, 1M and oversized Unicode documents; verify stale cancellation and native typing responsiveness. [Evidence](docs/markdown-preview-verification.md)
- [~] **TASK-030.03** — In a narrow native window, traverse all character fields, save/cancel and return from a linked scene; retain exact staged values. [Evidence](docs/character-profile-verification.md)
- [~] **TASK-032.01** — Inventory untranslated UI strings, including dynamic service errors; identify each owning widget and reproducible path.
- [~] **TASK-032.02** — Move inventoried visible strings to the correct Qt translation context; preserve placeholders/IDs and test Ukrainian runtime behavior.
- [~] **TASK-032.03** — Re-extract sources, validate placeholders/plurals, compile en/uk `.qm` and verify packaged catalogs match fresh builds.
- [~] **TASK-032.04** — Translate typed dialogs/errors/status for invalid UTF-8, binary/missing files, save conflicts, project/export and AI failures without losing diagnostic details or dirty data. [Localization evidence](docs/localization-accessibility-checkpoint.md)
- [~] **TASK-034.01** — Audit native keyboard-only open/save, search, tabs, AI review and dialogs; record OS/Qt and focus.
- [~] **TASK-034.02** — Check accessible names/descriptions and spoken labels; add focused regressions for defects.
- [~] **TASK-034.03** — Check dialog initial/return focus, Tab order, Enter/Esc and cancellation; fix/retest issues.
- [~] **TASK-034.04** — Verify native light/dark/high-contrast palettes, focus and readable disabled/error/ghost text; capture evidence.
- [~] **TASK-034.06** — Fix reproduced barriers, add regressions and repeat native tests; keep unverifiable cases blocked. [Accessibility evidence](docs/localization-accessibility-checkpoint.md)