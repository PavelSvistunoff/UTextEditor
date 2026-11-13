# Refactoring progress

## TASK-032.04 checkpoint — shared export errors

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 open.
- Text/PDF export callbacks share source-protection and typed project formatting.
- Four format/path cases failed before fix; system fallback cases passed. Eight
  final cases cover both callbacks, original details and busy-state reset.
- Focused UI/export/PDF/i18n/translation tests: 273 passed; full offscreen suite:
  975 passed, 2 skipped. `git diff --check` passed; packaged parity tested.
- No new translation strings/catalog changes. Native Ukrainian UI/accessibility,
  native pagination and live Ollama not tested.
- Clean Code review: shared presentation rule, operation-specific titles retained;
  no export persistence/undo/API changes or new dependencies. Broader audit open.
- Started at `d0787db` (profile package already committed externally); three
  pre-existing tracked pyc changes preserved and excluded from this package.
- Files: main window, UI tests, README, TASKS, refactoring plan and evidence docs.
- Next: remaining custom project/character error callbacks; branch `main`.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — profile save errors

- TASK-032.04: **CHECKPOINT**; TASK-032 parent partial; native .V2 open.
- Profile-save callback now reuses shared typed project-error presentation.
- Generic errors retain their original text; format/path failures show translated
  categories with exact details. Failed saves reopen staged edits for retry.
- Two typed regressions failed before fix; generic case passed. Focused UI/i18n/
  translation tests: 240 passed; full offscreen: 967 passed, 2 skipped.
- `git diff --check` passed; existing packaged catalog parity tests passed.
- No new UI strings; no catalog rebuild needed. Native Ukrainian UI/accessibility
  and live Ollama not tested. Branch `main`.
- Clean Code review: shared UI formatting reused, callback lifecycle and source
  profile preserved; no dependencies/API changes. Broader refactoring incomplete.
- Files: main window, UI tests, README, TASKS and localization/progress docs.
- Next: remaining custom project/character callbacks and export error handling.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — shared project error presentation

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 remains open.
- Opening/mutation warnings share typed project error formatting; format and path
  categories are translated while exact original diagnostics remain visible.
- Real traversal rejection tests failed before fix for both UI routes; prior
  malformed-manifest regression still passes after extraction.
- Focused UI/domain/i18n/translation tests: 288 passed; full offscreen suite:
  965 passed, 2 skipped. `git diff --check` passed.
- Source extraction/reference validation and en/uk compilation passed; packaged
  parity covered. Native Ukrainian UI/accessibility and live Ollama not tested.
- Clean Code review: shared UI rule, domain path checks/workers/callback guards
  retained, no dependencies or public API changes; broader audit incomplete.
- Files: main window, UI tests, Ukrainian TS/QM, README, TASKS and evidence docs.
- Next: custom character/project workflow error callbacks; branch `main`.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — AI failure audit

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 remains open.
- Generation/completion failure handlers reviewed; existing localized wrappers
  and request/settings guards retained. No production refactor warranted here.
- Six regressions use a real OllamaClient failure with mocked network, checking
  packaged Ukrainian, exact details, stale status and dirty manuscript safety.
- Focused UI/provider/i18n/translation tests: 250 passed; full offscreen suite:
  963 passed, 2 skipped. `git diff --check` passed.
- Clean Code review: deterministic failure injection, no network service needed,
  no domain/API/undo change; other AI workflows and repository audit incomplete.
- Native Ukrainian UI/accessibility and live Ollama not tested; branch `main`.
- Files: UI tests, TASKS, refactoring plan and localization/progress evidence.
- Next: remaining project/path errors and character/project AI workflow failures.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — invalid project format

- TASK-032.04: **CHECKPOINT**; TASK-032 parent partial; native .V2 remains open.
- Typed project-format open errors receive Ukrainian category with original detail.
- Regression failed before change; active project, dirty text and busy reset tested.
- Focused UI/i18n/translation tests: 230 passed; full offscreen: 957 passed, 2 skipped.
- Source extraction/reference validation and en/uk compilation passed; packaged
  parity covered by tests. `git diff --check` passed.
- Clean Code review: existing formatter reused; domain, workers and persistence
  unchanged; no dependency or public API changes. Broader refactoring incomplete.
- Native Ukrainian UI/accessibility and live Ollama not tested.
- Files: main window, UI tests, Ukrainian TS/QM, README, TASKS and evidence docs.
- Next: audit AI errors and remaining project/path error categories; branch `main`.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## 2026-11-13 — TASK-032.04 standalone save conflict

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 remains open.
- Shared typed conflict formatting in manual and autosave paths; original error,
  filename, dirty buffer and existing manual review guidance are retained.
- Actual modified and removed file regressions exercise both save routes.
- Focused UI/i18n/translation/document suite: 269 passed; final four targeted
  tests passed; full offscreen: 956 passed, 2 skipped.
- Translation source/reference validation and both compilations passed; packaged
  parity covered. Native Ukrainian UI, accessibility and live Ollama not tested.
- Clean Code review: existing formatting helper reused, no new dependency or
  domain/persistence change; stale and conflict protections remain in place.
- Next: typed project and AI errors; repository-wide refactoring incomplete.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## 2026-11-13 — TASK-032.04 missing-file category

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 remains open.
- `app/ui/main_window.py` wraps typed missing-file errors in a translated category
  and retains exact system details; other error types preserve their prior paths.
- Regression with a real missing file and `%1` in its name failed before fix;
  i18n/translation suite: 42 passed; full offscreen suite: 952 passed, 2 skipped.
- Source extraction/reference validation and both catalog compilations succeeded;
  packaged catalog parity covered by tests. Native Ukrainian UI not checked.
- Clean Code review: formatting uses existing placeholder helper, domain and UI
  boundaries preserved; no new dependencies, stale-state or persistence changes.
- Next: typed save conflict, project and AI errors; broader refactoring incomplete.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## 2026-11-13 — TASK-030.03 keyboard traversal

- TASK-030.03: **CHECKPOINT**; TASK-030 parent partial; native .V2 remains open.
- `app/ui/character_dialog.py`: multiline profile fields pass Tab to focus
  traversal; the regression failed before the change and reaches every profile
  field offscreen at 400x380 afterward. Tab no longer inserts a literal tab.
- Existing profile save/cancel and navigation tests remain applicable; source
  profile remains unchanged on Cancel. Native focus reveal is unverified.
- Focused UI suite: 183 passed; full offscreen suite: 951 passed, 2 skipped.
- Translation validation passed; UI string audit returned 9 candidates.
- Clean Code review: existing widget registry reused; no domain, persistence,
  async or undo behavior changed; no new dependencies or translation strings.
- Native GUI, screen-reader and packaged Ukrainian runtime were not tested.
- Next: native profile review; continue TASK-001.02 without dropping undo.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## 2026-11-13 — TASK-001.02 daily snapshot overhead

- TASK-001.02: **CHECKPOINT**, parent TASK-001 remains open; full repository
  refactoring and package audits remain incomplete.
- `app/document/writing_goals.py`: daily snapshots use slots, retaining all
  reachable checkpoints and existing reset/rekey and undo semantics.
- Focused writing-goal/editor/benchmark suite: 124 passed before and after.
- Full offscreen suite: 950 passed, 2 skipped; `git diff --check` passed.
- Single mixed 1,000-command samples: 251,241 traced bytes before and 236,924
  after; both retained 1,001 states and passed undo/redo/branch checks. These
  noisy measurements show no bound. The 10,000-command mixed run retained
  10,001 states and 1,943,227 traced bytes; undo/redo and branch counts passed.
  A previous recorded run reported 2,206,486 bytes; conditions may differ.
- Clean Code review: ownership and side effects unchanged; no new dependencies,
  error handling, persistence format, undo pruning or public API changes.
- Native GUI, accessibility and live Ollama not tested.
- Next: design and validate a real bound without discarding reachable Qt undo.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## 2026-11-13 — character map validation

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- `app/project/model.py`: shared existing unknown-key validation for character
  background, personality and arc maps; error ordering and wording retained.
- Added parameterized regression for unknown keys; 50 domain tests passed before
  the refactor; project domain, setup and translation tests: 98 passed after it.
- Reviewed transaction staging, installation, rollback and cleanup and existing
  failure tests; no transaction code changed. Cross-process races remain a risk.
- Clean Code review: shared rule, unchanged boundaries and diagnostics; no new
  dependencies or public API. Model and project service audits remain incomplete.
- Full offscreen suite: 950 passed, 2 skipped; `git diff --check` passed.
- Native GUI, accessibility and live Ollama were not tested.
- Next: examine remaining manifest parsing/validation and transaction edge cases.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — character manifest serialization review

- Status: **CHECKPOINT**; full repository audit and refactoring remain incomplete.
- Reviewed character mapping in `app/project/model.py` and project domain tests.
  Expanded the dense mapping and named goal/knowledge variables; field order,
  optional portrait and serialized values are unchanged.
- Focused `tests/test_project_domain.py`: 47 passed.
- Full offscreen suite before and after edit: 947 passed, 2 skipped each.
- `git diff --check` passed; Clean Code review: names and mapping clarity improved;
  serialization contract retained; no new dependencies or error paths.
- This readability change does not complete the model or project package audit.
- Native GUI, accessibility and live Ollama were not tested.
- Next: inspect remaining model validation and service transaction failure paths.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

## 2026-11-13 — Auto-writer rollback cleanup diagnostics

- Status: **CHECKPOINT**; repository-wide audit and refactoring remain incomplete.
- A failure-injection regression showed rollback silently omitted a failed
  temporary-file cleanup from the error. Original scene was restored, but the
  generated temporary file remained; the regression failed before the fix.
- Separate behavior fix reports remaining temporary names, also retaining
  rollback failure details when both operations fail. README updated.
- Focused project setup, translation and domain suite: 94 passed.
- Full offscreen suite: 946 passed, 2 skipped; a second combined-failure test
  was added afterward and the setup module passed all 41 tests. `git diff --check` passed.
- Cross-process races and failed rollback itself remain independent risks; this
  change does not claim stronger transaction guarantees.
- Next: complete project service/model and transaction failure-path inventory.
- Native GUI, accessibility and live Ollama were not tested.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`.

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
