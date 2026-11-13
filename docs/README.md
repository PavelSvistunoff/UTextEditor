# Technical evidence and verification index

> These notes capture the state and test evidence **at their recorded dates**. They are not implementation instructions and their test totals are not automatically current. Start with [TASKS.md](../TASKS.md), [AGENTS.md](../AGENTS.md), and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md).

## Development practices

- [Clean Code guidelines for Codex](clean-code-codex.md) — naming, focused functions, clear boundaries, error handling, tests and scoped refactoring for Python/PySide6.

- [Repository refactoring acceptance](refactoring-audit.md) — per-module dispositions, changes, tests and retained risks.
- [Refactoring plan](refactoring-plan.md) and [progress](refactoring-progress.md) — completed batches and verification history.

## Data integrity and performance

- [Save coordination](save-coordination.md) — in-process lock guarantee, cross-process overwrite race and platform trade-offs.
- [Large-file evaluation](large-file-evaluation.md) — input sizes, Qt/memory measurements and workload limits.
- [GUI latency](gui-latency-evaluation.md) — offscreen event-loop callback delays.
- [Encoding investigation](encoding-support.md) — UTF-8/legacy-codec experiments and no-loss boundaries.

## Navigation, editing and projects

- [Project search](project-search-verification.md), [Quick Open](quick-open-verification.md), [Open Tabs](tab-navigation-verification.md), [Recent Files](recent-files-verification.md).
- [Related-item navigation](related-navigation-verification.md), [navigation history](navigation-history-verification.md), [menu organization](menu-organization-verification.md).
- [Character profiles](character-profile-verification.md) and [inline completions](inline-completion-verification.md).

## AI and writing workflows

- [Completion context](completion-context-verification.md), [spelling review](spelling-review-verification.md), [streaming preview](streaming-preview-verification.md).
- [Translation review](translation-review-verification.md) and [Auto-writer review](auto-writer-review-verification.md).
- [Markdown preview](markdown-preview-verification.md), [manuscript export/PDF](export-verification.md).

## Localization and historical records

- [Localization and accessibility](localization-accessibility-checkpoint.md) — automation coverage versus native/screen-reader acceptance.
- [Documentation/static audit (2026-11-13)](repository-audit-2026-11-13.md) — scope, findings and limits.
- [Archived implementation checkpoints](archive/implementation-progress-2026-11-13.md) — full older log; use the short root checkpoint for current work.
