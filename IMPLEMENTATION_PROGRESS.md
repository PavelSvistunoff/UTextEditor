# Implementation progress — current resume pointer

> This short file records the **latest actionable checkpoint**. The original full execution history is preserved verbatim in [docs/archive/implementation-progress-2026-11-13.md](docs/archive/implementation-progress-2026-11-13.md). Do not confuse historical test totals with tests performed today. For a new run, prepend a concise checkpoint following [AGENTS.md](AGENTS.md#logical-task-batches-and-continuation).


## Refactoring checkpoint — character map validation

- Repository-wide refactoring: **CHECKPOINT**; backlog statuses unchanged.
- Branch `main`; character background, personality and arc maps share key validation.
- Sorted unknown-key diagnostics tested before and after; YAML contract unchanged.
- Files: `app/project/model.py`, `tests/test_project_domain.py`, refactoring docs.
- Focused project tests: 98 passed; full offscreen suite: 950 passed, 2 skipped.
- `git diff --check` passed; native GUI, accessibility and live Ollama not tested.
- Transaction staging and rollback inspected; concurrent-writer risk remains.
- Project model/service and remaining package audits are incomplete.
- Next: examine remaining manifest parsing and transaction edge cases.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — Auto-writer cleanup diagnostics

- Repository-wide refactoring: **CHECKPOINT**; backlog statuses unchanged.
- Separate behavior fix reports temporary files remaining after failed rollback cleanup.
- Failure-injection regression failed before fix; original scene remains restored.
- Focused setup/translation/domain suite: 94 passed; README updated.
- Full offscreen suite: 946 passed, 2 skipped; subsequently added combined-failure
  regression passed in the setup module (41 passed); `git diff --check` passed.
- Cross-process races and actual rollback failures remain separate risks.
- No native GUI, accessibility or live Ollama checks performed.
- Next: finish project service/model and transaction failure-path inventory.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — translation scene capture

- Repository-wide refactoring: **CHECKPOINT**; backlog statuses unchanged.
- Shared grouped/ungrouped scene capture; no transaction or conflict checks moved.
- Regression checks order, unsaved buffer, disk snapshot and snapshot content; passed before change.
- Focused translation/project domain/setup suite: 93 passed after change.
- Full offscreen suite: 945 passed, 2 skipped; `git diff --check` passed.
- Auto-writer rollback suppresses temporary cleanup failures; investigate separately.
- No native GUI, accessibility or live Ollama checks performed.
- Next: investigate cleanup failures and finish project service/model audit.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — writing-goal undo/redo

- Repository-wide refactoring: **CHECKPOINT**; backlog statuses unchanged.
- Shared undo/redo checkpoint restoration in `app/document/writing_goals.py`.
- Added nearest repeated-text checkpoint regression; focused pre-change tests passed.
- Writing goals/editor/benchmark suite: 124 passed after change.
- Full offscreen suite: 944 passed, 2 skipped; `git diff --check` passed.
- No history truncation; TASK-001.02 reachable undo metadata remains unbounded.
- No native GUI, accessibility or live Ollama checks performed.
- Next: finish revision and document inventory, then review project transaction/rollback.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — revision FIFO fix

- Repository-wide refactoring: **CHECKPOINT**; backlog task statuses unchanged.
- Separate behavior fix: revision scan reports non-regular snapshot files instead of blocking on a FIFO.
- Bounded regression failed by timeout before the fix; revision/recovery suite now has 77 passing tests.
- Full offscreen suite: 943 passed, 2 skipped; `git diff --check` passed.
- README updated; corrupt entries remain on disk and valid snapshots remain visible.
- FIFO regression ran on macOS; no native GUI, accessibility or live Ollama checks.
- Next: finish revision comparison review, then inspect writing-goal history without truncating undo.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — recovery identity

- Repository-wide refactoring: **CHECKPOINT**; backlog task statuses unchanged.
- Shared project-item identity validation between recovery save and snapshot parsing.
- Valid and malformed cases checked on both paths; invalid snapshots remain on disk.
- Focused document/recovery suite: 87 passed; recovery tests passed before the refactor.
- Full offscreen suite: 942 passed, 2 skipped; `git diff --check` passed.
- Revision scan blocked on a FIFO named `.json` in a one-second subprocess test;
  treat a fix as a separate behavior change with a bounded regression.
- Native GUI, accessibility and live Ollama were not tested.
- Next: investigate revision FIFO reads and inspect revision tests and callers.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — export validation

- Repository-wide refactoring: **CHECKPOINT**; backlog task statuses unchanged.
- Shared scene ID and text checks between document export and PDF compilation.
- Preserved text-export selection and the different validation orders; three regressions added.
- Focused `tests/test_export.py tests/test_book_compiler.py`: 25 passed before and after.
- Full offscreen suite: 934 passed, 2 skipped; `git diff --check` passed.
- No native GUI, accessibility or live Ollama checks performed.
- Full inventory and all remaining packages are still outstanding.
- Next: inspect `app/document/recovery.py` and `tests/test_recovery.py`.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — save conflicts

- Repository-wide refactoring: **CHECKPOINT**; no backlog subtask selected or closed.
- `app/document/file_manager.py`: shared digest-check rule, retaining both checks and diagnostics.
- `tests/test_document.py`: source removal before save and during staging; dirty state and cleanup preserved.
- Focused document/project/recovery suite: 126 passed; tests also passed before the change.
- Full offscreen suite: 931 passed, 2 skipped; `git diff --check` passed.
- Independent writers can still race after the final check; no stronger guarantee is claimed.
- No native GUI, accessibility or live Ollama checks performed.
- See `docs/refactoring-progress.md` and `docs/refactoring-plan.md` for scope and remaining work.
- Next: compare scene validation in `app/document/export.py` and `book_compiler.py` with their tests.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Refactoring checkpoint — 2026-11-13

- User-authorized repository-wide refactoring; no `TASKS.md` subtask selected or closed.
- Overall audit and refactoring: **CHECKPOINT**, incomplete; backlog parent statuses unchanged.
- Branch `main`; started clean at `e1b577e`.
- Initial inventory and priorities: `docs/refactoring-plan.md`; detailed status: `docs/refactoring-progress.md`.
- Document batch: `app/document/encoding.py`, `tests/test_document.py`.
- Preserve most-frequent line ending, first-occurrence ties and LF default; focused tests passed before and after.
- Baseline full suite: 923 passed, 2 skipped; after change: 929 passed, 2 skipped.
- Focused `tests/test_document.py`: 38 passed; `git diff --check` passed.
- Native GUI and live Ollama not run.
- File saving, Qt undo, asynchronous work, YAML and transactions were not changed.
- Remaining: review all modules/tests; document findings and resolve or justify them.
- Next: inspect `app/document/file_manager.py` and its tests for a bounded safe batch.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## Latest recorded work — 2026-11-13 (not rerun during documentation cleanup)

- **TASK-032.04 — CHECKPOINT (parent TASK-032 partial):** standalone invalid UTF-8 and likely-binary file-open errors now use translated UI messages. Other service error strings, a complete UI audit and native localization review remain open.
- **TASK-032.03 — CHECKPOINT (parent TASK-032 partial):** packaged English/Ukrainian `.qm` catalogs were rebuilt and runtime parity-tested. This does **not** establish native screen-reader or comprehensive UI string coverage.
- **TASK-001.02 — CHECKPOINT (parent TASK-001 open):** sharing prior-day snapshot data reduced some Python metadata retention, but reachable Qt undo states still grow without a demonstrated bound. Do not clear Qt undo to satisfy the metric.
- **Most recent recorded offline suite:** `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` → **923 passed, 2 skipped** (from the archived checkpoint, **not newly run here**).

## Resume

1. Inspect current branch and `git status --short`; use [TASKS.md](TASKS.md) to select exact active subtask IDs.
2. First investigate `TASK-001.02` in `app/document/writing_goals.py` with `benchmarks/writing_goal_history.py`, retaining exact undo and daily-count behavior.
3. Then continue `TASK-032.04` by finding untranslated typed and untyped service errors: `rg -n 'str\\(error\\)|str\\(exc\\)' app/ui/main_window.py`. Translate user-facing wrappers, not manuscript text.
4. Add the **next** actual code/test checkpoint above this section. Include IDs, results, files, exact commands, unrun native checks, residual risk and the next resume command.

## Durable evidence

- [Full historical checkpoint log](docs/archive/implementation-progress-2026-11-13.md)
- [Localization and accessibility verification](docs/localization-accessibility-checkpoint.md)
- [Save coordination limitation](docs/save-coordination.md)
- [2026-11-13 documentation/static audit](docs/repository-audit-2026-11-13.md)
