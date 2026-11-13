# Implementation progress — current resume pointer

> This short file records the **latest actionable checkpoint**. Earlier execution history is recorded in [docs/archive/implementation-progress-2026-11-13.md](docs/archive/implementation-progress-2026-11-13.md). Do not confuse historical test totals with tests performed today. For a new run, prepend a concise checkpoint following [AGENTS.md](AGENTS.md#logical-task-batches-and-continuation).


## TASK-032.01/.02/.03 checkpoint — analysis context heading

- TASK-032.01, TASK-032.02, TASK-032.03: **CHECKPOINT** each; parent TASK-032
  partial; native .V2 remains open. Broader repository refactoring incomplete.
- Inventoried unmarked MainWindow analysis-source heading; summary/continuity
  workflows now use one translated template with captured timestamp/source data.
- Two packaged Ukrainian regressions failed before fix; source placeholders and
  model output remain verbatim. No manuscript/AI prompt or stale-guard changes.
- Focused workflow/i18n/translation suite: 102 passed; full offscreen suite:
  1006 passed, 2 skipped. `git diff --check` passed.
- Source extraction/reference validation passed; Ukrainian package rebuilt and
  en/uk compilation/parity tested. No native Ukrainian UI/accessibility check.
- Clean Code review: simple template replaces concatenation; existing formatter
  reused, owning tr context correct, no dependencies/API/persistence changes.
- Files: main window, workflow tests, Ukrainian TS/QM, README and evidence docs.
- Existing pyc changes preserved; branch `main`.
- Next: inventory remaining dynamic labels/service errors beyond AST heuristic.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — stale character-development failure

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 open.
- Separate behavior fix: development failure callback uses existing captured
  context guard before warning; button reset still permits retry.
- Four regressions reproduced warnings after scene/profile/settings/project
  changes; current failure retains packaged Ukrainian title and exact detail.
- Five new worker scenarios preserve scene file and unstaged character arc.
- Focused AI workflow/development/i18n/translation tests: 105 passed; full
  offscreen suite: 1004 passed, 2 skipped. `git diff --check` passed.
- Clean Code review: reused context predicate, no duplicate state rule, dependency,
  provider protocol or persistence change. No new translation strings.
- Native Ukrainian UI/accessibility and live Ollama not tested; pyc preserved.
- Concurrent concise TASKS rewrite preserved; detailed evidence in localization doc.
- Files: main window, workflow tests, README, localization/refactoring checkpoints.
- Next: remaining project/character failure categories and package audit.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## Refactoring / TASK-032.04 checkpoint — background character export

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; repository refactor incomplete.
- Extracted portable YAML export to `app/project/character_export.py`; public
  Project export keeps destination-before-profile validation and file semantics.
- UI writes a deep-copied profile through FunctionWorker with queued feedback;
  changed project/generation or closing state suppresses stale success/errors.
- Existing overwrite/localization tests adapted to await worker feedback; six
  delayed-worker cases verify background thread, captured name and stale feedback.
- fsync failure tests retain existing destination and remove staged files.
- Focused UI/domain/i18n/translation suite: 321 passed. Final full offscreen:
  998 passed, 2 skipped; added API-order regression afterward passed in a focused
  17-case export run. `git diff --check` passed; packaged parity tested.
- Clean Code review: domain serialization/persistence separated from Qt; no new
  dependency, YAML/API format, undo or manuscript changes. No arbitrary-writer claim.
- Native GUI/accessibility and live Ollama not tested; existing pyc changes preserved.
- Files: new export module, service, main window, tests, README/TASKS/evidence docs.
- Next: remaining custom AI/project errors and package audit; branch `main`.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — character profile export errors

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 open.
- Character export reuses shared typed project-error presentation; generic
  details, overwrite confirmation and existing target behavior are retained.
- Two typed confirmed cases failed before fix; six final injected UI cases cover
  format/path/system errors, confirmation/cancellation and unchanged destination.
- Focused UI/domain/i18n/translation tests: 313 passed; full offscreen suite:
  990 passed, 2 skipped. `git diff --check` passed; packaged parity tested.
- No new strings/catalog rebuild; native Ukrainian UI/accessibility and live
  Ollama not tested. Three pre-existing pyc changes preserved; branch `main`.
- Clean Code review: shared formatting reused; no domain/API/dependency changes.
  Failure injection does not prove arbitrary-writer or partial-write rollback safety.
- Found synchronous character export filesystem work; separate worker migration
  needs a captured profile and tests for project changes and failed writes.
- Files: main window, UI tests, README, TASKS, refactoring/localization docs.
- Next: worker migration for profile export, then remaining custom AI callbacks.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.04 checkpoint — character scene-search errors

- TASK-032.04: **CHECKPOINT**; parent TASK-032 partial; native .V2 remains open.
- Scene-search callback uses shared typed project presentation; stale checks use
  an explicit early return. Format/path categories localized, diagnostics retained.
- Nine injected callback cases cover three error types across current/project/
  generation changes. Two typed current cases failed before the change.
- Focused UI/domain/i18n/translation tests: 307 passed; full offscreen suite:
  984 passed, 2 skipped. `git diff --check` passed; packaged parity tested.
- No new UI strings or catalog rebuild. Native Ukrainian UI/accessibility and
  live Ollama not tested. Existing three pyc changes preserved; branch `main`.
- Clean Code review: shared formatting and clear guard, domain and workers
  unchanged; no dependency/API changes. Repository-wide refactoring incomplete.
- Files: main window, UI tests, README, TASKS, refactoring/localization evidence.
- Next: character export and remaining custom AI/project failure callbacks.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


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


## TASK-032.04 checkpoint — standalone save conflict

- TASK-032.04: **CHECKPOINT**; TASK-032 parent partial; .V2 native gate open.
- Shared manual/autosave error formatting adds Ukrainian conflict category for
  `ExternalChangeError`, retaining original details, filename and review advice.
- Real changed/removed file regressions cover both paths, callback failure,
  dirty buffer and unchanged disk; original two cases failed before the fix.
- Focused UI/i18n/translation/document suite: 269 passed; four final targeted
  cases passed; full offscreen suite: 956 passed, 2 skipped.
- Extracted reference and placeholder validation plus both lrelease runs passed;
  packaged catalog parity covered by tests. `git diff --check` passed.
- Native Ukrainian UI/accessibility and live Ollama were not tested.
- Files: main window, UI tests, Ukrainian TS/QM, README, TASKS and evidence docs;
  branch `main`. Next: audit typed project and AI error categories.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## TASK-032.04 checkpoint — missing file localization

- TASK-032.04: **CHECKPOINT**; TASK-032 parent remains partial; .V2 native gate open.
- Real missing standalone file receives translated category with original error
  and filename retained, including placeholder-like text. Other errors unchanged.
- Regression failed before change; i18n/translation focused tests: 42 passed.
- Full offscreen suite: 952 passed, 2 skipped; catalog extraction/reference check
  and English/Ukrainian lrelease succeeded; packaged parity tested.
- Existing recent-file tests verify unsaved text survives missing-file failure.
- Native Ukrainian UI/accessibility and live Ollama were not tested.
- Files: `app/ui/main_window.py`, `tests/test_i18n.py`, Ukrainian TS/QM,
  README, TASKS and localization/refactoring evidence; branch `main`.
- Next: audit remaining typed save-conflict, project and AI error categories.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

## TASK-030.03 checkpoint — profile keyboard traversal

- TASK-030.03: **CHECKPOINT**; parent TASK-030 remains partial; .V2 native gate open.
- Offscreen regression failed before fix: Tab inserted text and Ctrl+Tab changed
  tabs before all profile fields could be reached.
- Multiline profile fields now move focus on Tab; this changes literal Tab entry.
- 400x380 offscreen traversal visits all profile fields; Cancel preserves source.
- `tests/test_project_ui.py`: 183 passed; full offscreen suite: 951 passed, 2 skipped.
- Translation validation passed; UI string audit reported 9 candidates for review.
- Native keyboard/focus, screen-reader and Ukrainian packaged runtime not tested.
- Files: `app/ui/character_dialog.py`, `tests/test_project_ui.py`, README,
  TASKS and profile/refactoring evidence docs; branch `main`.
- Next: native TASK-030.03/.V2 review.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.

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
- No history truncation; reachable undo metadata remains unbounded.
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
- **Most recent recorded offline suite:** `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` → **923 passed, 2 skipped** (from the archived checkpoint, **not newly run here**).

## Resume

1. Inspect current branch and `git status --short`; use [TASKS.md](TASKS.md) to select exact active subtask IDs.
2. Continue `TASK-032.04` by finding untranslated typed and untyped service errors: `rg -n 'str\\(error\\)|str\\(exc\\)' app/ui/main_window.py`. Translate user-facing wrappers, not manuscript text.
3. Add the **next** actual code/test checkpoint above this section. Include IDs, results, files, exact commands, unrun native checks, residual risk and the next resume command.

## Durable evidence

- [Full historical checkpoint log](docs/archive/implementation-progress-2026-11-13.md)
- [Localization and accessibility verification](docs/localization-accessibility-checkpoint.md)
- [Save coordination limitation](docs/save-coordination.md)
- [2026-11-13 documentation/static audit](docs/repository-audit-2026-11-13.md)
