# Refactoring progress

## 2026-11-13 — project translation scene capture

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- Reviewed translation capture and transaction entry points plus project tests.
  Grouped and ungrouped scenes duplicated capture; one operation now handles both.
- Added regression for scene and request order, saved versus unsaved text and
  snapshot contents. Translation tests passed before change; focused translation,
  project domain and setup suite passed after change (93 passed).
- Full offscreen suite: 945 passed, 2 skipped. `git diff --check` passed.
- Transaction rollback and stale checks were not moved. Initial service review
  found `_rollback_scene_replacements` suppresses temporary unlink failures;
  determine impact and test separately before changing failure behavior.
- Next: investigate that cleanup failure and finish project service/model audit;
  retain transaction ordering, stable IDs and manifest compatibility.
- Native GUI, accessibility and live Ollama were not tested.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — writing-goal checkpoint restoration

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- Reviewed `writing_goals.py`, its tests and editor integration. Undo and redo
  duplicated the same restore operation; they now share one lazy candidate scan.
- Added a repeated-text regression verifying the nearest reachable checkpoint;
  document/editor tests passed before and after. No Qt undo state was removed.
- Focused writing goals, editor and benchmark suite: 124 passed.
- Full offscreen suite: 944 passed, 2 skipped. `git diff --check` passed.
- Reachable checkpoint metadata still grows with Qt undo; TASK-001.02 remains open.
- Initial additional review: project paths/search, AI validation/provider/models,
  and settings; these are not yet complete package audits. Settings recent-file
  and recent-project handling differ in normalization and limits;
  do not merge without verifying compatibility.
- Next: finish revision comparison review and document package inventory, then
  investigate project service and its transaction/rollback tests.
- Native GUI, accessibility and live Ollama were not tested.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — revision FIFO behavior fix

- Status: **CHECKPOINT**; overall audit and refactoring remain incomplete.
- Confirmed revision listing blocked on a FIFO with a `.json` suffix. A bounded
  regression failed with a timeout before the fix.
- `RevisionStore.read` now opens nonblocking where supported and validates the
  opened descriptor as a regular file, following the existing recovery pattern.
  Invalid entries are diagnosed, retained and do not hide valid snapshots.
- This is a separate behavior fix; README now describes the diagnostic.
- Focused revision/recovery suite: 77 passed. FIFO regression ran on macOS;
  other platform behavior and native GUI were not independently verified.
- Full offscreen suite: 943 passed, 2 skipped. `git diff --check` passed.
- Next: finish examining revision comparison ownership and failure coverage,
  then audit `writing_goals.py` without truncating Qt undo.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — recovery identity validation

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- Reviewed `recovery.py` and recovery test inventory. The save and parse paths
  duplicated the same project-item identity rule; they now share a predicate.
- Added valid and malformed identity cases on both paths; verified invalid files
  remain available for diagnosis. Recovery tests passed before modification.
- Focused document/recovery tests: 87 passed. Existing snapshot format, errors,
  canonical conflict checks and cleanup policy are unchanged.
- Full offscreen suite: 942 passed, 2 skipped. `git diff --check` passed.
- Confirmed separately: a FIFO named `fifo.json` in the revision root makes
  `RevisionStore.list_snapshots()` block. A child process calling it timed out
  after one second with no FIFO writer. No behavior fix is included in this batch;
  assess worker callers, non-regular files, symlink races and diagnostics separately.
- Next: add a bounded FIFO regression and address this behavior in its own batch
  after reviewing revisions tests and call sites.
- Native GUI, accessibility and live Ollama were not tested.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — export scene validation

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- Reviewed `export.py`, `book_compiler.py`, `test_export.py` and
  `test_book_compiler.py` for scene validation and export persistence.
- Shared the identical scene ID and text validation; each caller retains its
  original ordering and selection behavior. PDF still validates each scene in
  sequence; text export checks all IDs and only selected scene text.
- Added three regressions for selected text and error ordering; focused tests
  passed before and after (25 passed). No output or public API change intended.
- Full offscreen suite: 934 passed, 2 skipped. `git diff --check` passed.
- Export replacement and PDF pagination/native behavior remain separate risks;
  existing tests do not constitute native GUI verification.
- Next: inspect `app/document/recovery.py` and `tests/test_recovery.py`, then
  record concrete findings before choosing the next bounded batch.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — save conflict check

- Status: **CHECKPOINT**; overall audit and refactoring remain incomplete.
- Reviewed `file_manager.py`, `document.py`, `write_lock.py`, `test_document.py`
  and callers; export and PDF compiler received an initial comparison only.
- The two save conflict checks duplicated the digest rule. Extracted it without
  moving either check or changing their diagnostics, save order or lock scope.
- Added tests for source removal before save and during staging; each checks the
  dirty buffer, original digest and temporary-file cleanup. Both passed before
  the refactor. Existing tests cover changed files and the independent-writer race.
- Focused command: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_document.py tests/test_project_domain.py tests/test_recovery.py` → 126 passed.
- Full offscreen suite: 931 passed, 2 skipped. `git diff --check` passed.
- Risk remains: the last digest check is not an atomic cross-process compare-and-swap.
- Next: compare `export.py` and `book_compiler.py` scene validation and tests,
  preserving selection behavior and validation order before any deduplication.
- Native GUI, accessibility and live Ollama were not tested.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — initial checkpoint

- Scope: repository-wide Clean Code refactoring, separate from `TASKS.md` feature tickets.
- Status: **CHECKPOINT**; overall audit and refactoring are incomplete.
- Git started clean on `main` at `e1b577e`.
- Initial inventory: 123 tracked Python files; `app/ui/main_window.py` and
  `app/project/service.py` are large investigation targets, not proven defects.
- Examined: instructions, repository inventory and selected document helpers;
  no complete package audit has yet been performed.
- `app/document/encoding.py`: replaced repeated counting/manual scanning with
  one explicit line-ending matcher. Added tie, majority, empty and adjacent
  ending cases; pre-change focused test passed (38 passed).
- Baseline: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`
  → 923 passed, 2 skipped; `python` itself is unavailable on PATH.
- After change: focused `tests/test_document.py` → 38 passed; full command
  above → 929 passed, 2 skipped. `git diff --check` passed.
- Remaining: audit every package and test against the plan; assess performance
  and safety before touching save, recovery, Qt undo or transactions.
- Native GUI, accessibility and live Ollama were not tested.
- Next: inspect `app/document/file_manager.py` and `tests/test_document.py`,
  then record concrete findings and choose the next bounded, tested batch.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`
