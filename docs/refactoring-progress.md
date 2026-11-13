# Refactoring progress

## Repository completion run — R2/R3 domain ownership batch

- Project/AI worker extraction and UI orchestration refactor: COMPLETE.
- Planning/analysis, project summaries, recovery resolution, bound saves,
  captured text/PDF exports and project snapshots now have domain owners.
- Existing MainWindow static call APIs retained; Qt signals and stale guards stay in UI.
- Shared selected-scene capture preserves buffers, order and destination-before-read validation.
- Profile goal/knowledge parsers now name their records and diagnostic paths.
- Activity terminal callbacks use named functions and short-circuit stale results.
- Pure project worker tests moved from UI tests: 6 passed without QApplication;
  extracted services import without loading PySide6. New activity cases: 9 passed.
- UI/E2E/settings/i18n pre/post extraction: 413 passed each; expanded final: 492 passed.
- Full control: 1114 passed, 2 skipped; final targeted domain/worker/activity: 68 passed.
- Direct Cocoa focus/activity: 36 passed; VoiceOver/OS palette not claimed.
- Standalone editor smoke exposed an existing goal-tab initialization race despite exit 0;
  this will be fixed separately, with a failing regression, before final reconciliation.
- No unrelated staged pyc or DS_Store files included; no new dependencies.
- Next: separate initialization fix, then close the reviewed refactoring inventory.

## Repository completion run — R2 AI boundary batch

- AI shared parsing/protocol refactor: COMPLETE; final repository reconciliation pending.
- One complete JSON-fence rule serves character profile, development, continuity
  and spellcheck; strict schemas and spellcheck's tolerant extraction stay distinct.
- Added 12 strict-boundary cases before extraction (plain/fenced/prefixed responses).
- Ollama completion, generation and streaming share their chat payload builder;
  timeout, observer events, raw whitespace and cancellation behavior are retained.
- Focused AI/activity corpus: 228 passed; final provider/project-worker/E2E/activity
  corpus: 89 passed. Project/AI earlier focused corpus: 320 passed.
- All network tests use fake HTTP/provider responses; no live Ollama gate claimed.
- Clean Code review: one protocol owner; no schema, context, consent or worker change.
- Full offscreen control run is in progress; staged bytecode remains excluded.
- Next: commit verified UI-to-domain extraction and complete per-module audit report.
- Resume: `git status --short && cat docs/refactoring-plan.md`.

## Repository completion run — R1 document batch

- R1: COMPLETE; repository audit/extraction batches R2–R4 remain in progress.
- Baseline full offscreen: 1093 passed, 2 skipped (118.43s).
- Revision comparison now delegates project/chapter/scene/note/link/profile rules;
  common-item position calculation shares the same insertion/removal semantics.
- Recovery/revision snapshot staging shares durable byte writing behind old methods.
- Unicode word tokens share one owner; project count_words import API retained.
- Added pre-extraction cross-category order and fsync/replace failure regressions.
- Focused document/export/compiler/project/goals corpus: 268 passed; final
  revised comparison/recovery/goals/project subset: 183 passed.
- No save-conflict, YAML, Undo/Redo, retention or transaction policy changes.
- Clean Code review: intent/ownership/errors/safety/tests/diff/report checked.
- Native GUI not rerun for this domain-only batch; staged pyc/DS_Store preserved.
- Next: finish project/AI extraction and UI worker-boundary verification.
- Resume: `git status --short && cat docs/refactoring-plan.md`.

## Current backlog — completed localization acceptance

- TASK-032.01/.02/.04: **COMPLETE**; TASK-034.03 already **COMPLETE**.
- TASK-032 remaining inventory, migration and error gates are closed; current TASKS.md is empty.
- Source audit covers all 35 UI modules and helper/worker diagnostic paths.
- Dispositions and exclusions: docs/ui-localization-inventory.md.
- Native Qt translators replace Python virtual translation callbacks; English and missing-resource resets tested.
- Full offscreen: 1093 passed, 2 skipped; final focused fallback checks: 47 passed.
- Native Cocoa: expanded corpus 392 passed; all-dialog matrix 27 passed; final subset 44 passed.
- Extraction 970 strings; Ukrainian 980 finished entries; both catalogs compile.
- Clean Code checklist and criterion-by-criterion outcomes: docs/all-remaining-tasks-checkpoint.md.
- TASK-034 VoiceOver/system-appearance gates were removed externally, not verified complete.
- Changed scope: i18n lifecycle/tests, acceptance inventory, README and progress/backlog documents.
- Unrelated staged bytecode and DS_Store changes preserved; no new dependency.
- Repository-wide refactoring remains separate and is not declared complete.
- Resume command for that work: `git status --short && cat docs/refactoring-plan.md`.

## TASK-034.03 — completed native dialog focus matrix

- TASK-034.03: **COMPLETE**, removed from the current backlog.
- Inventory and tests cover all 24 standalone QDialog subclasses: initial focus,
  forward/back Tab, unchanged text, Enter/Cancel or Esc and native owner focus return.
- AI consent initial focus/default explicitly selects Not now; explicit Allow
  via Enter/Space remains supported. Native missing focus reproduced before fix.
- Final matrix: 27 passed offscreen, 27 Cocoa; additional native/localization
  subset: 44 passed; broader earlier native UI corpus: 392 passed.
- Full offscreen control run: 1093 passed, 2 skipped. Final focused fallback suite:
  47 passed after English/missing-resource Qt-base reset validation.
- Clean Code review: existing Qt controls/signals, no data/undo/dependency change.
- VoiceOver/actual OS appearance gates were retired externally, not completed;
  global macOS menu visibility is outside this dialog acceptance.
- Existing staged pyc and DS_Store changes remain untouched.
- Next: record completed localization inventory/migration acceptance.


## All-remaining-task execution — final checkpoint

- Reviewed all eight starting tickets in one session; overall objective incomplete.
- COMPLETE/removed: TASK-030.03 (native all-field profile lifecycle), TASK-034.06
  (reproduced native width/clipping barriers fixed and native retested).
- TASK-032.01/.02/.04: CHECKPOINT; dynamic inventory broadened, goal/autosave/
  recovery labels localized, binary/UTF-8 original diagnostics retained.
- TASK-034.03: CHECKPOINT, comprehensive focus inventory remains; .034.02/.04:
  BLOCKED for speech and actual OS matrix. AXIsProcessTrusted() returned False.
- Final native expanded UI corpus: 392 passed; final Ukrainian subset: 10 passed.
- Focused recovery/UI/i18n suite: 368 passed; final full offscreen: 1059 passed,
  2 skipped; source/reference and en/uk compilation/parity passed; diff check passed.
- Recovery label capture leaves legacy defaults/data flow intact; a failing
  regression demonstrated lost binary diagnostics before the separate behavior fix.
- Clean Code review: UI-owned messages captured before worker work, explicit
  templates, no dependencies/undo/YAML changes; existing three pyc changes preserved.
- Evidence and remaining criteria: docs/all-remaining-tasks-checkpoint.md.
- Next: complete dynamic/service inventory; grant/observe native accessibility,
  VoiceOver and actual system appearance tests before closing remaining gates.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-034.03/.04/.06 — direct native retest

- TASK-034.06: **COMPLETE** for reproduced barriers; removed from open backlog.
- TASK-034.03: **CHECKPOINT**; .04: **BLOCKED** for actual OS palette matrix.
  .02 spoken labels also BLOCKED: VoiceOver output not observable with these tools.
- Fixed native Find/Replace width 429->420 and clipped status using dedicated rows;
  regression checks wrapped status geometry. Native focused run: 25 passed.
- Expanded final Cocoa UI/editor/settings run: 392 passed, macOS 27.0.1/Qt 6.11.2.
- Embedded-menu test precondition made explicit; macOS global-menu behavior unverified.
- System/dark-test/contrast-test native widget grabs visually inspected at 420px;
  synthetic palette overrides do not establish real OS appearance transitions.
- Full offscreen suite: 1056 passed, 2 skipped; `git diff --check` passed.
- Clean Code review: layout-only UI fix, keyboard/undo/domain semantics preserved;
  no strings or dependencies. Sources and task evidence updated; pyc preserved.
- Next: remaining localization/recovery inventory and native gaps.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.01/.02/.04 — expanded dynamic-string audit

- Each selected ticket: **CHECKPOINT**; parent TASK-032 partial.
- Audit now detects conditional/concatenated/formatted wrappers and show_error/
  AnalysisWindow source text. Ten residual candidates reviewed as translated data
  compositions, application name, paths/filters and language autonyms.
- Fixed newly found daily-goal progress/completion/incomplete/pause and autosave
  success/failure labels; use owning MainWindow templates with original counts.
- Audit/status/profile focus: 11 passed after adding incomplete-count regression;
  full earlier batch: 1055 passed, 2 skipped; final new branch tested separately.
- Source reference/placeholder validation and en/uk compilation passed; Ukrainian
  package rebuilt. No native or heuristic claim of complete runtime inventory.
- Broader recovery/service-error inventory remains outstanding; native speech and
  system palette requirements are recorded as blocked, not complete.
- Clean Code: existing formatter, clearer branch templates, no data-format/undo
  changes or dependencies; no raw manuscript/AI content translated.
- Next: native Find/Replace width defect and remaining inventory; pyc preserved.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-030.03 — direct native completion

- TASK-030.03: **COMPLETE**, removed from TASKS.md; broader parent/native audit
  remains separate. Cocoa Qt screen available on macOS 27.0.1 arm64 / Qt 6.11.2.
- Native all-field keyboard/structured-profile run: 5 passed; earlier native
  profile/review run: 31 passed. Inputs used QTest on native Qt widgets.
- New 400x380 case preserves every staged field through associated-scene return,
  saves/reopens exact character model, then verifies Cancel preserves persisted data.
- Full offscreen batch: 1055 passed, 2 skipped; `git diff --check` passed.
- No VoiceOver spoken-label or system-palette acceptance claimed.
- Files: TASKS, profile evidence, UI regression and checkpoints; pyc preserved.
- Next: TASK-032 dynamic strings and native Find/Replace width defect (.034.06).
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.01/.02/.04 checkpoint — revision creation feedback

- TASK-032.01, .02, .04: **CHECKPOINT** each; parent TASK-032 partial.
- Revision failure uses shared typed project formatting; success/failure share
  completion cleanup and captured project/generation/closing checks.
- Separate behavior fix rejects stale feedback and changed/cancelled name prompts;
  busy operations cannot start another revision creation through this entry point.
- Five baseline cases failed; 12 final cases cover worker feedback and prompt state.
- Focused UI/revisions/i18n/translation tests: 341 passed; full offscreen suite:
  1048 passed, 2 skipped. `git diff --check` passed; packaged parity tested.
- No new strings/catalog rebuild; native UI/accessibility and live Ollama untested.
- Clean Code review: shared completion rule, explicit guards, original diagnostics;
  no revision-store/file-write/undo/YAML/API change or new dependency.
- Files: main window, UI tests, README, localization/refactoring evidence docs.
- Existing three pyc changes preserved; broader audit/refactoring incomplete.
- Next: remaining recovery error presentation and dynamic UI inventory.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.01/.02/.04 checkpoint — project document-open failures

- TASK-032.01, .02, .04: **CHECKPOINT** each; parent TASK-032 partial.
- Warning and binding-verification status share typed project error formatting.
- Separate behavior fix: failure callbacks capture generation and reject changed
  projects/generations or closing windows, while releasing pending-open keys.
- Eight callback tests preserve dirty text and diagnostic placeholders; four
  worker tests cover new-open/existing-tab routes and captured generation.
- Focused UI/domain/i18n/translation tests: 352 passed; full offscreen suite:
  1036 passed, 2 skipped. `git diff --check` passed; packaged parity tested.
- No new strings/catalog rebuild. Native UI/accessibility and live Ollama untested.
- Clean Code review: existing presentation reused; explicit stale guard; no
  file-read/save/undo/domain/API change or dependency. Broader audit incomplete.
- Files: main window, UI tests, README, refactoring/localization evidence docs.
- Existing three pyc changes preserved; branch `main`.
- Next: revision-creation and recovery typed errors, then remaining UI inventory.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.01/.02/.04 checkpoint — project-search completion

- TASK-032.01, .02, .04: **CHECKPOINT** each; parent TASK-032 partial.
- Inventoried raw search failure status; translated wrapper retains exact details.
- Refactor: success/failure share completion and captured-context validation.
- Separate behavior fix: obsolete failure reports project change; closing and
  superseded callbacks do not overwrite current feedback or newer search state.
- Ten worker cases cover success/failure across current/project/generation/
  closing/superseded states. Three baseline failure cases reproduced defects.
- Focused UI/search/i18n/translation tests: 307 passed; full offscreen suite:
  1024 passed, 2 skipped. `git diff --check` passed.
- Source extraction/reference validation and en/uk compilation passed; Ukrainian
  package rebuilt and parity tested. Native UI/accessibility and live Ollama untested.
- Clean Code review: shared state rule, explicit guards, original diagnostics;
  no domain search, persistence, undo, dependency or public API changes.
- Files: main window, UI tests, Ukrainian TS/QM, README and evidence/checkpoints.
- Existing TASKS.md and three pyc changes preserved; branch `main`.
- Next: remaining revision/recovery typed errors and full UI inventory.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


## TASK-032.01/.02/.03/.04 checkpoint — revision error messages

- TASK-032.01, .02, .03, .04: **CHECKPOINT** each; parent TASK-032 partial;
  native .V2 open. Repository-wide refactor/audit remains incomplete.
- Inventoried unmarked revision load/compare error wrappers; translated templates
  retain exact details and explicit project/visibility/selection guards.
- Eight injected UI cases; three untranslated cases failed before change, stale
  cases already passed. Diagnostic placeholders remain literal data.
- Focused UI/revisions/i18n/translation tests: 307 passed; full offscreen:
  1014 passed, 2 skipped. `git diff --check` passed.
- Source extraction/reference validation passed; en/uk compiled; Ukrainian package
  rebuilt and packaged parity tested. Native Ukrainian UI/accessibility untested.
- Clean Code review: explicit guards and existing formatter; no domain, storage,
  undo, public API or dependency changes. Live Ollama not tested.
- Files: main window, UI tests, Ukrainian TS/QM, README and evidence/checkpoints.
- Existing TASKS.md and three pyc changes preserved outside this package.
- Next: remaining revision/project search error paths and UI inventory.
- Resume: `git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`.


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
- Next: native profile review.
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
- Reachable checkpoint metadata still grows with Qt undo; Reachable history remains unbounded.
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
