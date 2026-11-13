# Implementation progress

## Current resume pointer (documentation routing; 2026-11-13)

- **Branch:** `codex/task-continuation`. **Parent:** TASK-001 open. **Next batch:** TASK-001.02 and TASK-001.03 (high-risk: split into one subtask if needed), then TASK-001.05 benchmark. This pointer summarizes the latest recorded checkpoint below; it is not a new test run or a completion claim.
- **Verified in latest recorded implementation checkpoint:** active-identity collisions preserve independent histories and persisted aliases; focused writing-goal/editor suite 118 passed, full offscreen suite 917 passed / 2 skipped. These are historical run results, not freshly executed here.
- **Unverified:** bounded memory across reachable Qt undo states; parent stress/acceptance gate; native platform checks. Preserve undo/redo and daily-count semantics; do not truncate history silently.
- **Next action:** inspect `TASKS.md` TASK-001 gates, then `app/document/writing_goals.py`, `app/ui/main_window.py` and related tests. Resume investigation with `rg -n '_histories|discard_unreachable_history' app/document/writing_goals.py app/ui/main_window.py`.
- **After each implementation batch:** replace this pointer with the newly verified state and add a concise dated checkpoint below it. Preserve older records as historical evidence; do not treat superseded checkpoints as current blockers.

## TASK-001.03 collision continuation (2026-11-13)

- **.03: CHECKPOINT; parent TASK-001: open.** Active-identity rekey collisions
  no longer replace another editor's history. Independent history keys retain
  undo/redo and their persisted aliases contribute to the same logical scene;
  reset, pause, alias rekey and reload have regression coverage. Bounded
  reachable history remains outstanding (.02/.03), so the parent memory gate
  and long-session stress gate are not yet satisfied.
- Changed `app/document/writing_goals.py`, `app/ui/main_window.py`, their
  tests, `README.md`, `TASKS.md` and this checkpoint on
  `codex/task-continuation`. Existing staged generated artifacts are unrelated.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py`:
  118 passed. Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  917 passed, 2 skipped. Native checks not run.
- Next: resume .03/.02; design bounded storage for every reachable Qt undo
  state without discarding undo or silently changing daily counts; measure it
  with the .05 workload. Resume: `rg -n '_histories|discard_unreachable_history' app/document/writing_goals.py app/ui/main_window.py`.

## TASK-001.03 continuation review (2026-11-13)

- **.03: CHECKPOINT; parent TASK-001: open.** Batch: .03 alone, because
  tracker identity and undo history affect stored progress. Existing pause,
  reset, rekey and rejected Save As cases pass; active identity collisions
  and correct aggregation across independent live editors remain unresolved.
- Parent gate: existing focused goal tests pass; bounded memory, stress gate
  and complete undo/redo correctness remain unverified. No code changed.
- `_record_writing_goal_text` derives the persistent identity again rather
  than using an independent editor key; project aggregation enumerates stable
  scene identities. A solution must update both paths and preserve persisted
  progress, reset/clear, closing tabs and the already-completed save path.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py -k 'rekey or save_as_open_file_preserves_both_writing_goal_histories or paused_edits or reset'`:
  13 passed, 97 deselected. Full suite and native checks not run in this review.
- Branch `codex/task-continuation`, HEAD `71396cf`; existing uncommitted
  changes and staged generated files preserved. `git diff --check` passed.
- Next: resume .03; design separate editor history keys and stable persisted
  identities, then cover collisions, project aggregation, reset and undo/redo.
  Resume: `rg -n '_goal_document_id|_attach_writing_goal_document|rekey_document' app tests`.

## TASK-001.03 continuation checkpoint (2026-11-13)

- **.03: CHECKPOINT; parent TASK-001: open.** Existing Save As guard and
  unused-destination rekey tests pass; active tracker identity collisions and
  bounded reachable history remain unresolved. No implementation changed.
- `_attach_writing_goal_document` also runs after a successful save and when
  binding an open file to a project. Raising on collision there without a UI
  recovery design can interrupt a completed save or project binding. Separate
  live-editor history identities from persisted progress before changing it.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py -k 'rekey or save_as_open_file_preserves_both_writing_goal_histories'`: 7 passed, 103 deselected. Full suite and native checks not run in this continuation.
- Prior uncommitted changes and staged generated files preserved. Branch
  `codex/task-continuation`; HEAD `71396cf`. Git metadata is read-only in this
  environment; local commits cannot be created here.
- Next: resume .03 with a per-editor history/persistent identity design and
  tests for collision, project aggregation, reset and undo/redo. Resume command:
  `rg -n 'rekey_document|_goal_document_id|_attach_writing_goal_document' app tests`.

## TASK-001.03 checkpoint (2026-11-13)

- **.03: CHECKPOINT; parent TASK-001: open.** Save As to an already-open file
  is rejected without modifying disk, and both tabs retain correct progress
  through undo and redo, verified by a new UI regression test. Direct tracker
  rekeying into an active destination can still destroy its history; bounded
  undo metadata and the parent memory gate remain outstanding.
- Changed `tests/test_editor_widget.py`, `TASKS.md` and this checkpoint on
  `codex/task-continuation`; unrelated staged generated files are untouched.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_editor_widget.py -k 'save_as_open_file_preserves_both_writing_goal_histories'`:
  1 passed, 72 deselected. Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  909 passed, 2 skipped. Native checks not run.
- `git diff --check` passed. Commit attempt `git commit --only -m 'Test writing goal history on rejected Save As' -- TASKS.md IMPLEMENTATION_PROGRESS.md tests/test_editor_widget.py` failed: sandbox denies creation of `.git/index.lock`. Changes remain uncommitted; unrelated staged files remain untouched.
- Next: design separate live editor histories and persistent document identity
  aggregation, including collision, reset and project progress tests; resume
  TASK-001.03. Resume command: `rg -n 'rekey_document|_goal_document_id' app tests`.

## TASK-001.03 / .05 checkpoint (2026-11-13)

- **.03: CHECKPOINT; .05: CHECKPOINT; parent TASK-001: open.** A direct
  tracker reproduction confirms rekeying to an active identity replaces the
  destination's tracked text and checkpoints. No collision fix is claimed;
  independent editor identities and project-wide progress need a safe design.
- Added mixed history workload: multilingual insertions at document start,
  punctuation insertion/deletion, undo, redo and branching. At 10,000 commands:
  10,001 states, 2,206,486 current traced Python bytes; counts 3334 → 3000 →
  3334, branch 3001. Timing overlapped the full test run near the end and is
  not a clean baseline. Synthetic operations do not establish a memory bound.
- Changed `benchmarks/writing_goal_history.py`, `tests/test_writing_goal_benchmark.py`,
  `README.md`, `TASKS.md` and this checkpoint on `codex/task-continuation`.
  Unrelated staged generated files remain untouched. Native checks not run.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goal_benchmark.py tests/test_writing_goals.py`: 39 passed.
  Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`: 908 passed, 2 skipped.
  Benchmark: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/writing_goal_history.py --commands 10000 --undo 1000 --workload mixed` passed.
- Blocker: none. Next: design and test separate live editor identities without
  losing historical progress, then address bounded undo metadata; resume .03.

## Active backlog cleanup (2026-11-13)

- Removed eight previously completed parent tasks and 132 completed subtasks
  from `TASKS.md`; their historical evidence remains in this file, verification
  documents and Git history. At that checkpoint, open/partial subtasks and
  parent acceptance gates were preserved. Stable task IDs are retained.
- Updated `README.uk.md` where its current-state claims conflicted with
  `README.md`, including the save-race limitation and implemented AI review,
  disclosure and navigation features.
- Documentation-only change: tests not run. Checked backlog preservation, local
  evidence links and `git diff --check`. Native checks not performed.
- Resume another open backlog task.

## TASK-029.05 and parent complete (2026-11-13)

- **TASK-029.05: COMPLETE; parent TASK-029: COMPLETE.** Explicit confirmation
  clears locally stored new-word and scope history and all tracker undo/redo
  contributions, while preserving manuscript text, goal configuration and
  pause state. Subsequent edits/observations can create new progress. The
  history displays approximate totals and last complete scope observations.
- Changed `app/document/writing_goals.py`, `app/ui/main_window.py`, writing-goal
  and editor tests, `README.md`, `UNIMPLEMENTED_FEATURES.md`, Ukrainian source
  catalog, `TASKS.md`, and this file on `codex/task-continuation`. Unrelated
  pre-existing staged generated artifacts remain untouched.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py -k 'writing_goal or goal_history or scope_history or clear_progress'`:
  51 passed, 58 deselected. Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  898 passed, 2 skipped. Source translations validated and temporary catalog
  compiled. Native UI/accessibility and release catalog checks not performed.
- Blocker: none for independent backlog work. Next: select another unfinished
  parent, preserving safety and the separate TASK-001 history-memory limitation.

## TASK-029.02 completed (2026-11-13)

- **TASK-029.02: COMPLETE; parent TASK-029 open.** The history stores the last
  complete observed count per local day and document/project identity while the
  corresponding goal is enabled and unpaused. Missing/incomplete project
  counts are excluded; no past values are fabricated. Older settings load with
  empty scope history, and malformed new data is rejected without startup writes.
- Changed `app/document/writing_goals.py`, both writing-goal UI files, goal
  tests, `README.md`, `UNIMPLEMENTED_FEATURES.md`, Ukrainian source catalog,
  `TASKS.md`, and this file on `codex/task-continuation`; original staged
  generated files remain unrelated. Native UI and release catalog not checked.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py -k 'writing_goal or goal_history or scope_history'`:
  49 passed, 58 deselected. Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  896 passed, 2 skipped. Translation source validation and temporary catalog
  compilation passed. Next: TASK-029.05, confirmed removal including all
  undo/redo checkpoints; do not change manuscript text.

## TASK-029.01–.04 checkpoint (2026-11-13)

- **.01 COMPLETE, .02 CHECKPOINT, .03 COMPLETE, .04 COMPLETE; parent TASK-029
  open.** Read-only history shows approximate stored new-word totals by local
  date and explains pause, Undo/Redo and unavailable historical scopes. It
  preserves tracker state and manuscript text. Historical active-document and
  project counts are not recorded, so .02 remains partial; .05 remains open.
- Changed `app/ui/writing_goal_history_dialog.py`, `app/ui/main_window.py`,
  `tests/test_editor_widget.py`, `translations/utexteditor_uk.ts`, `README.md`,
  `UNIMPLEMENTED_FEATURES.md`, `TASKS.md` and this file on
  `codex/task-continuation`. Pre-existing staged generated files are unrelated.
- Focused: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_writing_goals.py tests/test_editor_widget.py -k 'writing_goal or goal_history'`:
  42 passed, 58 deselected. Full: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  889 passed, 2 skipped. Ukrainian source validation and temporary compilation
  passed. Native accessibility and release catalog verification not run.
- Blocker: none. Next: design recording historical scope values without
  inventing past data; implement confirmed removal of local progress while
  clearing undo/redo checkpoints. Resume .02 before selecting further work.

## Codex batch checkpoint format (newest checkpoint first)

For each logical batch, record parent TASK, 1–4 selected subtask IDs, per-subtask `COMPLETE`/`BLOCKED`/`CHECKPOINT`, parent status, acceptance evidence, files changed, exact tests run/not run, blockers, and the next safe step with resume command. Keep the latest checkpoint concise (about 10–20 lines where practical). Resume unfinished selected subtasks on the next run for the same assignment. Completing the batch does not imply the parent task or backlog is complete.

- **Continuation checkpoint (2026-11-01):** latest implementation commit is
  `61750de`; full offline suite 879 passed, 2 skipped; diff/whitespace checks
  pass. This run verified starting `d6f7d86`, then committed revision metadata
  values `2c2a9c5`, navigation guards `5ccc181`, typed spellcheck validation
  `1272d00`, context provenance `511d967`, translation audit `42d3048`,
  Auto-writer audit `a8116d6`, streaming audit `58fedca`, inline-copy removal
  `cea8691`, Markdown capture verification `569ba0d`, captured export preview
  `ae3f1c6` and exact untouched-profile preservation `61750de`. Original staged
  .DS_Store/bytecode are preserved; no push attempted. No global completion is
  claimed. Next implementation gaps remain TASK-001 reachable-history bounds
  and active identity collisions;
  TASK-029 history viewer. TASK-027.03 and TASK-030.03 retain native latency/
  all-field focus requirements. Native/accessibility/release catalog checks in
  UI V2 remain open. Do not redo completed audits or silently truncate Qt undo.

- **TASK-032/034.V1 — evidence reconciled (2026-11-01):** nine AST string
  candidates reviewed as data/autonyms/translated compositions within the
  tool's narrow scope; Ukrainian source has 956 records and source validation,
  extraction, temporary compilation and placeholder checks pass. Raw service
  error details and release/native workflows remain incomplete. Existing Qt
  keyboard/name/focus/palette tests and a read-only profile name probe are
  recorded in docs/localization-accessibility-checkpoint.md. No native screen-
  reader work claimed. .032.05 verified; other numbered localization/accessibility
  tickets remain partial/open and both parents/V2 remain partial. No runtime,
  translation or redundant test change for this reconciliation; README accurate.
  Last full suite on unchanged implementation: 879 passed, 2 skipped. Diff
  reviewed and whitespace check passed. Original staged artifacts preserved.

- **TASK-030.01/.02/.04/.05/V1 — verified; untouched-profile preservation
  (2026-11-01):** Save no longer silently normalizes untouched profile text or
  reparses unchanged structured values that contain line breaks/delimiters.
  Initial widget text and captured values identify actual edits; untouched
  dictionary keys/empty values and structured records round-trip exactly.
  Three regressions validate serializable profiles with no edits, a motivation
  edit and a single background edit; source profiles stay unchanged. Focused
  character/profile domain/UI tests: 55 passed; full offline suite: 879 passed,
  2 skipped. README/TASKS/docs/character-profile-verification.md updated; diff
  reviewed and whitespace check passed. No controls/strings changed. .03 and
  parent/V2 remain partial for all-field native small-window keyboard/focus,
  screen-reader and release-catalog review. Existing offscreen profile fields
  all exposed nonempty Qt accessibility names in a read-only probe; this does
  not establish native assistive-technology behavior. Export preview committed
  as `ae3f1c6`; original staged artifacts retained. No push attempted.

- **TASK-028.01–.06/V1 — preview implemented / existing options verified
  (2026-11-01):** optional Markdown/plain-text preview renders in a worker,
  displays a read-only bounded prefix with an explicit truncation notice, and
  writes the complete captured version only after Export. Cancel/stale open
  scene/project checks preserve the destination; write-stage alias validation
  protects source files. Shared atomic UTF-8/LF persistence now accepts rendered
  text without rereading sources. Seven regressions cover captured output,
  cancellation, changed buffers/project, post-preview source hard link, Unicode
  display bounds and complete tail output. Focused export/PDF/catalog suites:
  52 passed; full offline suite: 876 passed, 2 skipped. Ukrainian source validator,
  extraction/temporary compilation and whitespace checks pass; final diff
  reviewed. README/TASKS/UNIMPLEMENTED_FEATURES and docs/export-verification.md
  updated. No generated release catalogs changed. Native/catalog V2 and
  cross-platform PDF review remain; no PDF page preview or overall memory bound
  is claimed. Markdown checkpoint committed as `569ba0d`; original staged
  artifacts preserved. No push attempted.

- **TASK-027.01/.02/.04/.05/V1 — verified (2026-11-01):** reviewed active
  unsaved-buffer preview, 64 Ki UTF-16 prefix, one render worker, stale-result
  guards, read-only output and disabled external/local resources. Strengthened
  the existing large-prefix regression to fail on a whole-buffer copy during
  capture. Four focused tests passed; full offline suite: 869 passed, 2 skipped.
  TASKS/docs/markdown-preview-verification.md updated; README already accurate.
  Diff reviewed and whitespace check passed. No runtime/string changes. .03
  remains partial for native/pathological-markup capture and HTML-installation
  latency; parent and V2 native/catalog gates remain partial. Inline-copy fix
  committed as `cea8691`; original staged artifacts retained. No push attempted.

- **TASK-026.01–.05/V1 — verified; bounded visibility check (2026-11-01):**
  ghost placement now asks QTextCursor.atBlockEnd instead of copying the entire
  document and its suffix. A many-paragraph Unicode regression fails if display
  checks call toPlainText and verifies accepted/rejected placement preserves
  text/revision. Focused completion tests: 11 passed; full offline suite:
  869 passed, 2 skipped. docs/inline-completion-verification.md records why the
  complete single-line ghost/safe-rejection policy is retained instead of adding
  a popup or hiding accepted text by elision. README/TASKS updated; diff reviewed
  and whitespace check passed. No new controls/strings; native/catalog V2 still
  pending, parent partial. Streaming audit
  committed as `58fedca`; original staged artifacts retained. No push attempted.

- **TASK-025.01–.05/V1 — verified (2026-11-01):** inspected optional provider
  streaming, worker chunk queue/timer, provisional/final separate reviews,
  cumulative output bounds and cancellation/stale guards. Evidence in
  docs/streaming-preview-verification.md; nine focused tests passed, last full
  suite on unchanged runtime 868 passed, 2 skipped. No redundant tests or
  behavior/string changes; README accurate. TASKS updated; diff reviewed,
  whitespace check passed. Native/catalog V2 pending; blocked network reads may
  finish before cancellation, and live server compatibility is not inferred.
  Auto-writer audit committed as `a8116d6`; original staged artifacts retained.
  No push attempted.

- **TASK-024.01–.05/V1 — verified (2026-11-01):** reviewed staged per-scene
  previews, stable-ID checkbox selection, explicit Apply/Cancel, dependency
  warning after partial rejection, captured-state guards and snapshot-protected
  selected transaction. docs/auto-writer-review-verification.md maps named
  regressions for selection/stale/cancel, line endings, late rollback and
  generation failure. Focused Auto-writer/review tests: 15 passed; last full
  suite on unchanged code: 868 passed, 2 skipped. No runtime/string changes or
  redundant tests; README accurate. TASKS updated; diff reviewed, whitespace
  check passed. Native/catalog V2 and shared filesystem race remain open;
  parent stays partial. Translation audit committed as `42d3048`; original
  staged artifacts preserved. No push attempted.

- **TASK-023.01–.05/V1 — verified (2026-11-01):** reviewed side-by-side
  captured originals/translations, title/text rows with stable IDs, explicit
  all-batch Apply/Cancel, generation/editor guards and transaction revalidation.
  docs/translation-review-verification.md maps acceptance to named tests.
  Focused translation tests: 12 passed; last full suite on unchanged runtime
  code: 868 passed, 2 skipped. Existing tests cover cancellation, invalid output,
  conflict rejection, CRLF/IDs/paths/links and byte-exact late-failure rollback.
  No runtime/string change or redundant tests; existing README accurate.
  TASKS updated; diff reviewed and whitespace check passed. Parent remains
  partial for V2 native/catalog checks and the independent-writer
  race; crash/rollback-failure atomicity is not claimed. Context-provenance
  checkpoint committed as `511d967`. Original staged artifacts preserved;
  no push attempted.

- **TASK-022.01–.06/V1 — verified (2026-11-01):** traced captured destination,
  exact context/provenance, optional preview, note exclusions, automatic-context
  setting and first-use disclosure. Added one combined real-capture regression
  for dirty scene/note buffers, note truncation and omission, read-only preview,
  no-send cancellation and unchanged canonical files. Focused context/disclosure
  tests: 20 passed; full offline suite: 868 passed, 2 skipped. TASKS and
  docs/completion-context-verification.md updated; existing README accurate.
  Diff reviewed and whitespace check passed. No runtime/translation changes;
  numbered tickets/V1 verified, parent/V2 native/catalog checks remain partial.
  Spelling validation committed as `1272d00`; original staged artifacts retained.
  No push attempted.

- **TASK-021.01–.05/V1 — verified; typed response validation (2026-11-01):**
  typed Suggestion objects now receive range/type/length checks before sorting
  or editor use, matching JSON replacement/explanation bounds. Malformed typed
  responses previously could bypass those checks or raise on sorting. Fourteen
  malformed-field regressions and a count/order/length/overlap boundary test
  retain valid companion findings. Existing review tests cover explicit
  selection, cancellation, stale/overlapping rejection, emoji and one-step undo.
  Focused service/AI/workflow/accessibility/editor suites: 149 passed; full
  offline suite: 867 passed, 2 skipped. README/TASKS and
  docs/spelling-review-verification.md updated; diff reviewed, whitespace check
  passed. No new controls or Qt strings. Native keyboard/screen-reader and
  release-catalog V2 remain open; parent stays partial. Navigation history fix
  committed as `5ccc181`; original staged artifacts preserved. No push attempted.

- **TASK-019.01–.05/V1 — verified; path failure fix (2026-11-01):**
  Back/Forward now skips OSError/RuntimeError while verifying a project path.
  Two path-failure regressions and four stale-target cases cover edited,
  closed, removed and relinked destinations, unchanged history during typing,
  retained dirty buffers and unchanged source files. Focused history tests:
  8 passed; full offline suite: 852 passed, 2 skipped. README/TASKS and
  docs/navigation-history-verification.md updated. Diff reviewed and whitespace
  check passed. Existing translated feedback reused; no new controls/strings.
  Parent remains partial for native shortcut/accessibility and release-catalog
  V2 checks. Revision-value comparison committed as `2c2a9c5`. Original staged
  artifacts preserved; no push attempted.


- **TASK-018.01–.05/V1 — VERIFIED (2026-11-01):** reviewed Project/AI
  grouping, retained handler/shortcut table, disabled-action explanations and
  existing shared navigation. docs/menu-organization-verification.md records
  evidence and the decision to retain submenus without adding a command picker.
  Focused menu tests: 4 passed, 220 deselected; full offline suite on unchanged
  code: 845 passed, 2 skipped. README already accurate; no product/translation
  changes or redundant tests. Diff reviewed; whitespace check passed. All
  numbered tickets/V1 verified; parent remains partial for required manual
  accessibility/native shortcut review and release-catalog V2 checks.
  Recent-file fix/audit committed as `a6729b6`. No push attempted.

- **Latest continuation checkpoint (2026-11-01):** implementation is tested
  with 845 passed / 2 skipped; original staged `.DS_Store` and bytecode are
  preserved and excluded from every scoped commit. Subsequent navigation
  audits after the earlier checkpoint: Quick Open `5f8f797`, related-item
  navigation `e8776d8`, tab navigation `ab51d1f`, and recent files `a6729b6`.
  TASK-012, TASK-013, TASK-015, TASK-017 and TASK-018 numbered tickets are
  verified, but their parents retain V2 native/catalog requirements. TASK-016
  .05 is still partial. No native accessibility or cross-platform filesystem
  verification has been claimed. No generated release catalogs were changed.
  The overall backlog is still incomplete: earliest open work remains
  TASK-001's reachable-history bound/active-identity collision/stress gate;
  TASK-019 and later
  inherited UI tickets still need acceptance reconciliation or implementation
  as appropriate. Continue from these gaps, preserving completed evidence;
  do not truncate Qt undo, weaken conflict checks or promote native gates on
  offscreen tests. No requested implementation has been declared globally
  complete, and no push has been attempted.

- **TASK-017.01–.05/V1 — VERIFIED; path failure fix (2026-11-01):**
  reviewed separate ten-path settings list, common open worker/reuse, missing
  feedback, clear persistence and paths-only records. Initial/completed open
  handlers now catch path-resolution errors while checking duplicates instead
  of allowing exceptions to escape Qt callbacks. Four regressions cover
  OSError/RuntimeError for requested/existing paths at both stages, preserving
  dirty tabs and both source files. Focused recent-file/settings tests:
  7 passed, 169 deselected; full offline suite: 845 passed, 2 skipped.
  README/TASKS and docs/recent-files-verification.md updated; existing Open
  failed translations reused. Diff reviewed; whitespace check passed. All
  numbered tickets/V1 complete; parent remains partial for V2 release catalog
  and native checks. Tab audit committed as `ab51d1f`. No push attempted;
  unrelated staged artifacts preserved.

- **TASK-016.01–.04/V1 — VERIFIED (2026-11-01):** reviewed QTabWidget
  built-in navigation, shared searchable picker, modified/path/project labels,
  editor identity selection and delegated closing. Evidence is in
  docs/tab-navigation-verification.md. Focused Qt tests: 3 passed,
  217 deselected; preceding shared Quick Open tests: 6 passed; last full suite
  on unchanged code: 841 passed, 2 skipped. No behavior/strings changed;
  README already accurate. Diff reviewed; whitespace check passed. No redundant
  tests added. .05/V2 and parent remain partial: offscreen Ctrl+Tab tests are
  not native OS/accessibility verification. Related-navigation audit committed
  as `e8776d8`. No push attempted; staged artifacts preserved.

- **TASK-015.01–.05/V1 — VERIFIED (2026-11-01):** traced directed links,
  explicit scene associations, separate mention search, profile hide/return,
  and staged-save guards for character/relationship changes and write failures.
  docs/related-navigation-verification.md maps acceptance to named tests.
  Focused Qt tests: 8 passed, 147 deselected; full suite on unchanged code:
  841 passed, 2 skipped. No behavior/strings changed; existing README remains
  accurate. Documentation diff reviewed; whitespace check passed. No redundant
  tests added. Numbered tickets/V1 complete; parent remains partial for V2
  release-catalog/native checks. Quick Open audit committed as `5f8f797`.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-013.01–.05/V1 — VERIFIED (2026-11-01):** inspected Ctrl+P action,
  immutable item capture, casefold filtering, type/chapter/ID labels, aliases,
  stale project guard and shared document-opening path. Added named acceptance
  evidence to docs/quick-open-verification.md. Focused Quick Open Qt tests:
  6 passed, 149 deselected; full suite on unchanged implementation: 841 passed,
  2 skipped. No new behavior/strings; existing README is accurate. Diff reviewed
  and whitespace check passed; no redundant tests added for this audit.
  Numbered tickets/V1 complete; parent remains partial for V2 release catalog
  and native keyboard/screen-reader verification. Performance audit/checkpoint
  committed as `3332f66`. No push attempted; staged artifacts preserved.


- **Resume checkpoint (2026-11-01):** this run verified starting commit
  `39ae121`, then committed Qt-history pruning (`9ce6082`), callback-latency
  tooling (`9337b37`), save audit (`5dca14c`), recovery statuses (`1501132`),
  revision comparison chronology (`62a2553`), search safety/audit (`e8031f9`)
  and aggregate search capture bounds (`f805da5`). Current implementation has
  841 passing offline tests, 2 skipped live tests; Ukrainian source validation
  and temporary-catalog runtime/extraction checks pass. No push requested or
  attempted. Initial staged `.DS_Store` and bytecode changes remain untouched.
  The entire TASKS.md backlog is NOT complete. Earliest remaining work is
  TASK-001.02/.03/.05 (bound reachable metadata without truncating Qt undo,
  preserve actively tracked identity collisions, then stress validation).
  The independent-writer final-check overwrite race remains; no broader
  guarantee may be claimed. Further work includes the UI verification queue.
  Native screen-reader,
  filesystem and release-catalog checks remain explicitly open. TASK-012's
  numbered tickets are verified; its parent still awaits V2. Do not redo the
  completed investigations/benchmarks merely because their parents are partial.

- **TASK-012.06 — DONE within documented bounds (2026-11-01):** capped
  total open-buffer copies at 8 Mi UTF-16 units using Qt counts before copying.
  Omitted buffers carry a translated reason and never fall back to stale disk
  text. The service also rejects certainly oversized text before encoding it.
  Five new regressions cover descriptor/buffer allocation rejection, omission,
  exact budget boundaries for ASCII/emoji, preserved source files and unsaved
  buffers, and continuing other matches. Focused search/project UI/localization
  suites: 199 passed; full offline suite: 841 passed, 2 skipped. Ukrainian
  source validation passed; diff reviewed and whitespace check passed.
  README/TASKS/search verification updated. All numbered TASK-012 tickets
  verified; parent remains partial pending release-catalog/native V2 checks.
  Captured text is bounded, not total process memory: descriptor metadata scales
  with tabs/project size, capture remains synchronous and blocked regular-file
  reads are not interruptible. Earlier tabs can consume the allowance first;
  omissions are explicit. Prior search checkpoint committed as `e8031f9`.
  Ready for scoped budget commit.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-012.01–.05/.07/V1 — VERIFIED; file-read fixes (2026-11-01):**
  traced service, dock, captured unsaved buffers and generation/digest-checked
  navigation. docs/project-search-verification.md maps acceptance to named
  service/UI tests. Search now shares binary-control detection with ordinary
  project reads and uses nonblocking opens plus regular-file verification to
  reject POSIX FIFOs rather than wait for a writer. Seven new regressions
  preserve good companion matches and source contents. Focused search/project
  UI suites: 170 passed; full offline suite: 836 passed, 2 skipped. Diff
  reviewed; whitespace check passed. README/TASKS updated. No controls or Qt
  source strings changed; dynamic errors retain existing localization limits.
  .06 remains partial: total captured open-buffer text is not budgeted and
  regular-filesystem reads are not interruptible. V2 release-catalog/native
  keyboard/screen-reader verification remains open. Revision chronology
  checkpoint committed as `62a2553`; ready for scoped search commit.
  No push attempted; unrelated staged artifacts preserved.





- **TASK-001.04 — DONE (2026-11-01):** verified last checkpoint
  `39ae121` with 32 document tests. Existing staged `.DS_Store` and bytecode
  changes are unrelated and preserved. Qt availability signals now schedule a
  coalesced, deferred pruning check; clearing either or both stacks or disabling
  undo releases only unreachable goal checkpoints even without a text change.
  Closed tabs are ignored. Six offscreen regressions cover both directions,
  preserved text/counts, subsequent edits, undo and redo. Focused goal/editor
  suites: 96 passed; full offline suite: 817 passed, 2 skipped. Diff reviewed;
  whitespace check passed. README/TASKS updated. No new UI strings or native
  UI changes; localization/native checks N/A for this internal lifecycle fix.
  Reachable history remains unbounded (TASK-001.02); identity collisions and
  long-session acceptance remain open. Ready for scoped commit.





- **TASK-020.05 — DONE; .01–.04/V1 — verified (2026-10-31):** audited
  shared Qt matching flags, batched/stale-safe counting, current-match checks,
  replace-all edit blocks, focus shortcuts and MainWindow refresh connections.
  Added four Unicode case-insensitive replace-all regressions covering whole
  words/substrings, deletion/emoji replacement, counts and undo/redo. Existing
  tests cover navigation, default semantics, zero matches, focus and small
  windows. Focused suite: 21 passed; full offline suite: 798 passed, 2 skipped;
  diff reviewed and whitespace check passed. README already describes verified
  behavior; no product change or new strings. All numbered TASK-020 tickets
  complete. Parent deliberately remains partial: V2 native keyboard/screen-
  reader review and release-catalog verification remain outstanding and cannot
  be established by offscreen tests. No commits or pushes.

- **TASK-031 — COMPLETE (2026-10-31):** reviewed existing NFC normalization,
  script/common-word evidence, minimum alphabetic signal, distinct-word and
  ambiguous-language fallbacks. Existing tests/language_corpus.py has 43 cases:
  6 English, 8 Ukrainian, 29 intentionally Auto, including other languages,
  short/mixed text, decomposed Unicode and repeated/digit-heavy input. Added
  benchmarks/language_detection.py: current 43/43, always-Auto baseline 29/43,
  zero unsupported confident guesses. No algorithm change warranted by these
  cases; this is curated regression behavior, not population accuracy or an
  estimate against a historical detector. Added 86 explicit-override cases
  across both prompt types. Prompt suite: 135 passed; full offline suite:
  794 passed, 2 skipped; diff reviewed and whitespace check passed. README
  documents evaluation; all TASK-031 subtasks and acceptance checks reconciled.
  Native/catalog checks N/A: no UI behavior or strings changed. Uncommitted;
  no push attempted.

- **TASK-033 — COMPLETE (2026-10-31):** acceptance audit verified checker
  completeness, Qt/named/indexed placeholder parity, malformed/duplicate/empty
  and plural errors, extracted source coverage, CLI nonzero exit/reporting,
  compiled runtime lookup, README instructions and CI integration. Added three
  CLI regressions for unfinished translations, invalid root and missing context.
  Localization suite: 14 passed. Extracted coverage: 897 strings, passed.
  Temporary catalog compilation: English 28 and Ukrainian 903 finished entries,
  none unfinished; generated repository assets untouched. Full offline suite:
  708 passed, 2 skipped. Diff reviewed and whitespace check passed. All
  TASK-033 numbered tickets and V1/V2 reconciled; native UI checks N/A because
  this task changes tooling only. First hosted CI run remains unobserved;
  complete interface translation/native review remain TASK-032/TASK-034.
  Changes uncommitted; no push attempted.

- **TASK-033.04 — DONE (2026-10-31):** added
  .github/workflows/localization.yml for push, pull request and manual runs
  with read-only repository permissions, Python 3.12 and offscreen Qt. It
  installs project test tools and Linux Qt runtime libraries, validates the
  Ukrainian catalog, explicitly extracts/checks all marked UI sources, and
  runs existing localization regressions. Local extraction: 897 marked strings,
  coverage validation passed; localization suite: 11 passed; full offline
  suite: 705 passed, 2 skipped; diff reviewed and whitespace check passed.
  README/TASKS updated. Existing tests exercise malformed/missing translations,
  placeholders, plurals, compiled lookup and source coverage; no redundant
  workflow-mirroring unit test added. First hosted Ubuntu/Python 3.12 run
  remains unobserved until commit/push; no commits or pushes made. This
  completes workflow integration, not all localization/native acceptance.








- **TASK-001.05 — PARTIAL (2026-10-31 checkpoint):** configurable
  --commands/--undo history benchmark now checks a branch edit after undo
  as well as redo. Smoke run (100 commands/10 undo) passed: 101 states,
  58,624 current Python-traced bytes; counts 100 → 90 → 100, branch 91
  words/92 states. Focused goal/editor tests: 86 passed; full suite:
  693 passed, 2 skipped; diff check passed. README/TASKS updated.
  Long run completed: 1,001/5,001/10,001 states and
  422,181/1,898,691/3,723,574 current Python-traced bytes at
  1,000/5,000/10,000 commands (3.465/45.127/156.520 seconds).
  Counts 10,000 → 9,000 → 10,000; branch 9,001 words/9,002 states.
  This is synthetic and excludes native Qt allocations; no fixed bound
  is established. Prior accounting fix committed as 7663cc4; benchmark work
  remains uncommitted.

- **TASK-001.03 — PARTIAL (2026-10-31):** Save As to an identity with
  persisted progress now preserves source checkpoints when that destination
  is not actively tracked. Each checkpoint retains the larger daily count
  from source/destination, matching existing rekey semantics without allowing
  undo to erase prior destination contributions. Shared count snapshots remain
  shared during transfer. Added regression for undo/redo above and below the
  destination floor; updated existing larger-destination test. Goal tests:
  30 passed; full offline suite: 693 passed, 2 skipped; diff check passed.
  README/TASKS updated. Active destination collisions and bounded metadata
  remain open. Previous checkpoint committed as 59eebb6; new work uncommitted.

- **TASK-001.03 — PARTIAL (2026-10-31 resumed checkpoint):** verified the
  uncommitted identity-transfer change and continued with goal scope/enable
  transitions. Configuration no longer reattaches histories; inactive edits
  retain checkpoints but receive no new-word credit. Added three Qt regressions
  for disabling, active-scene scope and project scope, with edits and undo/redo
  across reconfiguration. Focused goal/editor suites: 85 passed; full offline
  suite: 692 passed, 2 skipped. README/TASKS updated and diff reviewed;
  whitespace check passed. Transient metadata is still unbounded, including
  inactive edits retained for undo correctness. Existing-destination identity
  collisions still reattach. No commits or pushes; unrelated generated-file
  worktree changes preserved. Next: address bounded metadata design and
  existing-destination accounting before marking TASK-001 complete.

- **TASK-001.03 — PARTIAL (2026-10-31):** rekeying a writing-goal document
  to an unused identity now transfers undo/redo checkpoints when text matches;
  rekeying to the same identity also preserves matching history. Regression
  tests cover daily counts over two dates through undo/redo, existing destination
  progress, and mismatched text. Existing destinations retain conservative
  reattachment rather than importing incompatible checkpoints. Writing-goal
  suite: 29 passed; full offline suite: 689 passed, 2 skipped; diff check passed.
  README/TASKS updated. Scope/enable transitions and bounded history remain
  outstanding. Changes are uncommitted; no push attempted.










## Atomic-plan audit and recovery preservation (2026-10-31)

- **TASK-001.03 — PARTIAL:** changing the target of an active new-words goal
  no longer reattaches the tracker or discards undo checkpoints. Modified
  `app/ui/main_window.py`, `tests/test_editor_widget.py`, and `README.md`.
  Focused tests: 78 passed; full offline suite: 672 passed, 2 skipped.
  Scope changes and disabling/re-enabling tracking still reattach and can lose
  earlier checkpoints; bounded undo metadata remains outstanding.
- **TASK-001.03 — PARTIAL:** pausing no longer drops tracker checkpoints;
  paused edits add no new words, while undo/redo follows retained checkpoints.
  Reset removes today's counts from retained checkpoints instead of replacing
  the history. Modified `app/document/writing_goals.py`, `app/ui/main_window.py`,
  `tests/test_writing_goals.py`, `tests/test_editor_widget.py`, and `README.md`.
  Focused tests: 77 passed; full offline suite: 671 passed, 2 skipped.
  Reconfiguration can still discard checkpoints;
  complete cross-scope accounting and a bounded history remain outstanding.
- **TASK-001.03 — PARTIAL:** undo/redo to a checkpoint no longer retained by
  the tracker no longer credits restored text as newly written. Modified
  `app/document/writing_goals.py`, `tests/test_writing_goals.py`,
  `tests/test_editor_widget.py`, `README.md`, and `TASKS.md`. Focused tests:
  75 passed; full offline suite: 669 passed, 2 skipped. Earlier daily
  contributions cannot be reconstructed after history reattachment; complete
  pause/reset/undo accounting remains outstanding.
- **TASK-001.05 — PARTIAL:** added `benchmarks/writing_goal_history.py`, an
  offline Qt session with 1,000 separate synthetic word-insertion commands and
  100 undo/redo operations. On this machine it recorded 101/501/1,001 tracker
  states and 56,701/222,675/416,017 current Python-traced bytes after
  100/500/1,000 commands; counts were 1,000 → 900 → 1,000 across undo/redo.
  Modified the benchmark, `README.md`, and `TASKS.md`. Writing-goal tests:
  22 passed; full offline suite: 666 passed, 2 skipped. The measurement includes
  Python allocations beyond the tracker, excludes Qt native allocations, and
  is a single synthetic append-heavy run. Mixed edits, longer sessions and
  native memory measurements remain outstanding; this does not establish a
  bound or solve TASK-001.02.
- **TASK-001.01 — DONE:** reviewed `WritingGoalTracker.record_text` and the
  Qt undo integration in `MainWindow._record_writing_goal_text` against
  `test_history_keeps_one_text_copy_and_tracks_undo_branch_across_days` and
  `test_compacted_command_preserves_daily_counts_through_reset_undo_and_redo`.
  Merged commands share an endpoint and cleared undo stacks are pruned, but
  separately reachable commands still each retain metadata. TASK-001.02 and
  .04 remain partial; bounding them safely needs a design that preserves Qt
  undo and redo semantics.
- **Audit queue:** complete the remaining atomic status audit; prioritize
  remaining performance and UX work.
  Other inherited statuses remain unverified. Native screen-reader and
  platform checks require a suitable GUI environment.

This file was created because no earlier progress checkpoint was present in
the repository. The task statuses in `TASKS.md` remain authoritative.

- **TASK-001 — incomplete:** merged Qt undo commands are compacted, but
  metadata for separate undo commands remains unbounded. The documented
  benchmark covers tracker allocations, not a fixed bound. See
  `UNIMPLEMENTED_FEATURES.md` for details. Do not clear the author's undo
  stack merely to meet a memory bound.
- **TASK-002 — complete:** destination labeling was updated and local and
  remote hosts were covered by tests. The work remains in the existing
  uncommitted worktree.
- **TASK-003 — complete:** a non-modal English/Ukrainian disclosure gates
  completion, spellcheck, prompt generation, character assistance, project
  setup, Auto-pilot, Auto-writer, translation, and project analysis. Consent
  persists for the approved destination without document content; a changed
  host requires renewed consent. Automatic requests retry with fresh state
  after consent; explicit actions prompt the user to retry. Declined automatic
  requests do not repeatedly reopen the dialog. Workers retain the provider
  captured before settings changes. Tests cover all workflow gates, local and
  remote hosts, decline, destination changes, persistence failure, and a
  disclosure opened from a modal workflow. Full offline suite: 421 passed,
  2 skipped (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  .venv/bin/python -m pytest -q`).
- **TASK-004 — implemented:** spellcheck now waits for the active provider
  call to finish and retains only the latest pending request. A changed editor,
  settings change, cancellation, or shutdown discards pending work. Offline
  Qt tests exercise slow and failing calls, stale edits, cancellation, and UI
  event-loop responsiveness. The full offline suite passed: 409 passed,
  2 skipped (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  .venv/bin/python -m pytest -q`).
- **TASK-012 — in progress:** added a bounded, cancellable literal search
  service for captured scene and note descriptors. Open buffer snapshots take
  precedence over disk, unreadable, binary, or oversized files are reported,
  and results carry stable IDs, locations, excerpts, and text fingerprints.
  Search > Search Project Text now opens a persistent results panel. Navigation
  checks captured project identity and document fingerprints before selecting
  a match, including newly opened items. Qt tests cover unsaved Unicode text,
  stale buffers and files, opening results, and cancellation. Ukrainian source
  strings are present but the compiled catalog remains to be rebuilt. Large
  projects still need GUI responsiveness measurements and more stress tests;
  path resolution now runs in the search worker. Do not mark complete until
  those issues and localization are verified. Full offline suite: 454 passed,
  2 skipped. A further 5,000-document regression verifies cancellation while
  reporting unreadable files and confirms that remaining files are not visited.
  Full offline suite: 542 passed, 2 skipped. GUI responsiveness measurements
  and compiled localization remain outstanding. Error reporting now retains
  at most 100 bounded details and counts additional unreadable files, avoiding
  an unbounded results label. Focused service and panel tests and Ukrainian
  catalog validation passed; full offline suite: 544 passed, 2 skipped. The
  new `benchmarks/project_search_responsiveness.py` measures a synthetic
  2,000-file project through the offscreen window. One run measured 0.7 ms
  startup, 100.8 ms total and a 5.7 ms maximum timer gap for no matches; a
  result-limited search measured 0.7 ms startup, 20.5 ms total and a 20.5 ms
  maximum timer gap for 1,000 matches. These are single-run measurements on
  this machine, not native rendering or portable guarantees. Broader native
  responsiveness and compiled localization remain outstanding. Project-open
  callbacks now discard a read if its item was removed or relinked while the
  read was pending, including opens initiated by search. Project UI regression
  tests cover both cases; full offline suite: 546 passed, 2 skipped. Capture
  now avoids copying open buffers whose Qt length proves they exceed the search
  size limit, and reports them without falling back to stale disk text. Result
  excerpts are also bounded for long search queries. Focused service and Qt
  tests and the full offline suite passed: 574 passed, 2 skipped. Native
  responsiveness and compiled localization remain outstanding. The search
  status and unreadable-file details now scroll within a bounded-height area,
  leaving room for results; an offscreen test covers 100 errors and the
  omitted-error count. Full offline suite: 636 passed, 2 skipped.
- **TASK-013 — in progress:** Search > Quick Open provides a keyboard-driven
  picker for scene, chapter, note and character names and character aliases,
  showing type, chapter context and stable IDs. It opens existing documents
  without closing unsaved tabs; chapters are revealed in the tree. Offline Qt
  tests cover filtering, duplicates, keyboard activation, unsaved tabs, deleted
  items, chapter reveal, and shortcut uniqueness. The Ukrainian source catalog
  needs compilation and the shortcut needs native-platform verification.
  Do not mark complete until those checks are performed. Full offline suite:
  459 passed, 2 skipped.
- **TASK-014 — implemented:** Project > Reveal Current Document in Project
  locates a bound scene or note by stable ID, expands only its ancestors and
  preserves other expansion state. Standalone and unavailable items report
  why they cannot be revealed. Offline Qt tests cover both item types,
  duplicate titles, unsaved text, and standalone documents; Ukrainian strings
  are in the catalog. The full offline suite passed: 414 passed, 2 skipped
  (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
  pytest -q`).
- **TASK-015 — in progress:** existing linked-note navigation also works from
  a selected scene, and the scene context menu exposes the action. A Qt test
  verifies linked-note navigation preserves unsaved scene text and does not
  change links. Character-to-scene navigation, a return path that preserves
  staged character-profile edits, broader navigation tests, and compiled
  Ukrainian strings remain outstanding. Do not mark complete. Full offline
  suite: 460 passed, 2 skipped. The character tree menu now offers a separate
  picker for explicitly associated scenes, distinguished from mention search.
  It checks that the character and association still exist after the picker
  closes; a regression covers stale associations and duplicate scene titles.
  Profiles now open explicitly associated scenes and provide a status-bar
  return control while retaining staged fields and relationships. Closing the
  window returns to the profile, and stale profiles, changed relationships,
  stale associations and failed saves are handled without silently losing
  edits. Native keyboard/accessibility review and release catalog compilation
  remain outstanding; do not mark complete until verified. Full offline suite:
  592 passed, 2 skipped. Linked-item navigation also rechecks the project and
  link after selection, uses stable IDs even when titles contain brackets, and
  translates its picker and stale-link messages. Full offline suite after this
  follow-up: 597 passed, 2 skipped.
- **TASK-016 — in progress:** Qt's existing Ctrl+Tab and Ctrl+Shift+Tab
  behavior was verified with offscreen keyboard tests, and View > Open Tabs
  provides a searchable picker with modified markers, file/project context,
  and distinct labels for duplicate untitled tabs. Closing remains handled by
  the existing unsaved-change flow. Compiled Ukrainian strings and manual
  native-platform shortcut verification remain outstanding; do not mark
  complete until verified. Full offline suite: 462 passed, 2 skipped.
- **TASK-017 — in progress:** File > Open Recent File stores up to ten paths
  independently of recent projects, reuses existing tabs, handles missing
  files through the normal open-error path, and provides Clear Recent Files.
  Settings validation and Qt tests cover persistence, duplicates, unsaved
  buffers, missing files and clearing. Ukrainian source strings need compiling;
  settings persistence currently follows the existing synchronous recent-
  project pattern and needs a non-blocking, serialized persistence design.
  Do not mark complete until these issues are resolved. Full offline suite:
  464 passed, 2 skipped.
- **TASK-018 — in progress:** grouped Project movement, links, revisions,
  export and AI actions into submenus while retaining their existing action
  objects, and added project/selection requirement descriptions. AI menu
  separators and existing keyboard shortcuts remain in place. Automated tests
  cover grouping and action availability; native keyboard and accessibility
  review and compilation of Ukrainian source strings remain outstanding.
  Do not mark complete until manual review is performed. Full offline suite:
  464 passed, 2 skipped.
- **TASK-019 — in progress:** session-local Back and Forward actions now
  record explicit scene, note and project-search jumps in a bounded history.
  They restore positions in still-open, unchanged tabs and skip stale or
  removed destinations; tests cover branching, limits and unsaved buffers.
  Reopening closed destinations, broader search/navigation coverage, compiled
  translations and native keyboard verification remain outstanding. Do not
  mark complete. A further offscreen regression covers Back and Forward across
  two Unicode search-result selections in an unsaved scene and verifies that
  neither the buffer nor the disk is changed. Reopening closed destinations
  and native verification remain outstanding. History now also skips a tab
  when its scene or note has been relinked to a different path; an offscreen
  regression covers a relinked scene. Full offline suite: 618 passed, 2 skipped.
- **TASK-020 — in progress:** Find and Replace now offer case and whole-word
  controls while retaining case-sensitive literal defaults. Navigation,
  counts and replacement use the same Qt matching rules, replace-all remains a
  single undoable edit, and Find/Replace focus and close behavior are distinct.
  Tests cover Ukrainian case, Unicode positions, whole-word selections,
  no-op and no-match behavior, undo, focus and an offscreen small-width layout.
  Compiled Ukrainian strings and native small-window/keyboard verification
  remain outstanding. Case-insensitive and whole-word match counts now run in
  bounded event-loop batches; changing the query or active editor discards an
  unfinished count. Tests cover yielding and stale counts. Default literal
  counting now also uses Qt's batched matching path without copying the full
  buffer. An offscreen regression checks yielding, Unicode and no full-text
  copy. A single Qt search can still scan a large unmatched span on the GUI
  thread, and replace-all remains synchronous; broader performance and native
  verification remain outstanding. Full offline suite: 629 passed, 2 skipped.
- **TASK-021 — in progress:** AI > Review Spelling and Grammar presents
  current validated findings with explanations and selection controls. It
  rejects changed or overlapping selections, and applies selected corrections
  as one undoable edit. Tests cover cancellation, selection, Unicode, stale
  edits, overlapping ranges and undo. Compiled Ukrainian translations and
  native accessibility verification remain outstanding. Full offline suite:
  486 passed, 2 skipped.
- **TASK-022 — in progress:** AI Settings now offers a persisted option to
  exclude project characters and reference notes from automatic completions;
  explicit completions retain existing project context. Offline worker tests
  cover both modes and settings validation. Further preview validation and
  compiled Ukrainian translation remain outstanding. Do not mark complete.
  Full offline suite:
  472 passed, 2 skipped. Context construction now also returns an immutable
  capture with note provenance and truncation metadata for the future preview;
  the existing request path uses the same captured text. Full offline suite
  after this refactor: 473 passed, 2 skipped. AI > Completion Reference Notes
  now excludes selected notes for the project session and invalidates pending
  completions when the selection changes. A worker regression test covers
  selection and stale results. Full offline suite: 474 passed, 2 skipped. A
  read-only captured-context review dialog is available through an explicit
  AI action. It captures reference material in a worker, displays the exact
  context, destination, unsaved buffers and note truncation, and checks editor,
  project, settings and open-note state before sending and applying results.
  Tests cover exact context, cancellation and edits during review. Closed
  notes are now checked in the worker before sending and after generation;
  stale results are discarded. As with other filesystem checks, a change can
  still race the final check. The preview flags omitted
  document prefixes and character text cut by the length limit. It also flags
  character goals, traits, knowledge, scene goals, development notes and state
  changes omitted by per-field limits. Focused service and offscreen review
  tests cover these limits; compiled Ukrainian translations remain outstanding.
  Full offline suite: 557 passed, 2 skipped.
- **TASK-023 — in progress:** project translation now retains captured source
  contents and presents titles and texts side by side before explicit Apply or
  Cancel. It rechecks project, settings and all open project editors after
  review, then uses the existing transactional commit. Tests cover navigation,
  unsaved source, cancellation, changed buffers and the full apply path.
  Ukrainian catalog compilation and native accessibility review remain
  outstanding. Review labels now include stable chapter, scene and note IDs
  so duplicate titles are distinguishable. Tests cover duplicate scenes,
  unsaved source and cancellation or edits during review. Full offline suite:
  635 passed, 2 skipped.
- **TASK-024 — in progress:** after generation, Auto-writer presents a
  navigable, read-only per-scene review with individual selection. It warns
  that later drafts can depend on rejected drafts, rechecks open project
  buffers and applies selected scenes through the existing transaction.
  Tests cover selection, cancellation, stale edits and preview navigation.
  Compiled Ukrainian strings and native accessibility review remain
  outstanding. Auto-writer progress signals now carry the request generation,
  preventing delayed messages from an older request updating a newer progress
  window; a queued-signal regression covers both stale and current messages.
  Full offline suite: 640 passed, 2 skipped.
- **TASK-025 — in progress:** the provider protocol and Ollama client now
  support bounded NDJSON streaming with chunk callbacks, cooperative
  cancellation and explicit malformed/oversized response errors. Tests cover
  chunks, cancellation including the final chunk, malformed responses and the
  byte limit. An opt-in setting now enables a non-modal provisional preview
  for prompt generation, with bounded worker buffering, cancellation and stale
  editor checks; the final draft still requires explicit insertion. Offline
  tests cover incremental updates, cancellation, stale edits, undo and the
  output limit. Blocking reads remain subject to the configured network
  timeout; native accessibility review and compiled Ukrainian strings remain
  outstanding. Do not mark complete until those checks are performed. Full
  offline suite: 500 passed, 2 skipped; the additional final-review rejection
  case passed in the focused streaming tests.
- **TASK-026 — in progress:** inline completion rendering now shows any
  separating space that acceptance would insert, and discards a suggestion
  when resizing makes it too wide to display. An offscreen regression test
  covers resizing without modifying the document. Long, multiline and mid-line
  suggestions still need a safe, readable review affordance; native window
  and accessibility verification are also outstanding. Do not mark complete.
  Full offline suite: 502 passed, 2 skipped; focused completion tests also
  passed after the final rendering adjustment.
- **TASK-027 — in progress:** View > Markdown Preview renders the active
  unsaved buffer in a read-only dock, debounces changes, checks captured
  revisions, blocks resource loading, and renders in a worker. Input and
  rendered output are bounded; the initial version explicitly declined
  documents over 65,536 Qt text units. Tests cover stale renders, unsaved text, resource
  blocking and the input limit. Large-document preview and responsiveness,
  compiled translations, and native accessibility review remain outstanding;
  do not mark complete. Full offline suite: 506 passed, 2 skipped. Large
  documents now render a clearly labeled prefix captured without copying the
  entire buffer; the 65,536 Qt-unit input bound remains. A regression covers
  a Unicode cutoff and preservation of the source buffer. Full offline suite:
  568 passed, 2 skipped. Full-document preview, broader responsiveness and
  native accessibility verification remain outstanding.
- **TASK-028 — in progress:** PDF compilation now offers A5, A4 and Letter
  paper, an editable book title and an optional title-page author. Tests check
  actual page dimensions, author text, invalid sizes, and unsaved scene
  inclusion. An export preview, PDF scene/heading choices, broader pagination
  and layout checks, compiled translations and native review remain; do not
  mark complete. Full offline suite: 511 passed, 2 skipped. Markdown/text and
  PDF workers now use the captured scene list instead of enumerating the live
  manifest again. A regression covers later-added unreadable scenes and unsaved
  buffers. Closed scene contents are still read in the worker and a complete
  captured-content review remains outstanding. Full offline suite: 569 passed,
  2 skipped. PDF options now allow scene headings to be omitted from both the
  contents and manuscript, retaining them by default. PDF extraction and Qt
  workflow tests cover grouped and ungrouped scenes and unsaved text. Scene
  selection, chapter heading choices, preview, captured closed-scene contents,
  compiled translations and native PDF review remain outstanding. Full offline
  suite: 571 passed, 2 skipped. Both export workers now reject scene, note and
  manifest destinations, including symbolic and hard links. Text export retains
  the overwrite decision made at confirmation, so a destination created later
  is not replaced without approval. Tests cover both safeguards; filesystem
  changes can still race the source-path check. Full offline suite: 576 passed,
  2 skipped. PDF options now list scenes with chapter context and stable IDs;
  unchecked scenes are omitted without being read, and only selected unsaved
  buffers are included. A stale project generation cancels the selection.
  Tests cover duplicate labels, omitted unreadable scenes and stale options.
  PDF chapter headings can now also be omitted from the contents and body;
  section page breaks remain. Preview, captured closed-scene contents, compiled
  translations and native review remain outstanding. Do not mark complete.
  Full offline suite: 579 passed, 2 skipped; focused PDF tests also cover
  showing scene headings while chapter headings are hidden. Markdown/text
  export now also abandons a selection when the project generation changes
  during its destination, overwrite, options or unsaved-content dialogs; Qt
  regressions cover each dialog. Text export now captures and warns about only
  selected scene buffers, excluding unsaved notes and omitted scenes; an
  offscreen regression checks the resulting output. Full offline suite:
  585 passed, 2 skipped.
- **TASK-030 — in progress:** the long Story and Background and personality
  forms now scroll in smaller profile windows; an offscreen test covers access
  to their last fields and unchanged staged-save behavior. Character-to-scene
  navigation and a safe return path are now available as described under
  TASK-015. Native keyboard/accessibility verification and release catalog
  compilation remain outstanding. Do not mark complete. Full offline suite:
  592 passed, 2 skipped.
- **TASK-031 — in progress:** added a 20-case multilingual corpus and made
  short, unsupported-script and Russian-specific text fall back to Auto,
  requiring stronger common-word evidence for English or Ukrainian. The old
  detector matched 16/20 corpus expectations; the updated detector matched
  20/20, with explicit overrides covered. This is a small regression corpus,
  not a representative accuracy estimate; broader multilingual evaluation
  remains. Do not mark complete on that basis alone. Full offline suite: 533
  passed, 2 skipped. Shared Cyrillic words alone no longer classify text as
  Ukrainian: two Russian examples and an ambiguous Ukrainian example now fall
  back to Auto. The corpus contains 23 cases; broader evaluation remains.
  Full offline suite: 550 passed, 2 skipped. Detection now normalizes Unicode
  before inspecting scripts and treats remaining combining marks as ambiguous.
  An expanded 33-case corpus includes decomposed Ukrainian and accented or
  unsupported text: the previous detector matched 30 cases and the updated
  detector matched 33. This remains a small, nonrepresentative corpus; broader
  evaluation is still needed. The detector now requires at least eight letters
  and two distinct signal words, so digits and repeated words cannot turn a
  short fragment into a confident classification. On the expanded 43-case
  regression corpus the previous detector matched 35 expectations and the
  revised detector matched 43. This corpus remains nonrepresentative; broader
  multilingual evaluation is outstanding. Full offline suite: 628 passed,
  2 skipped.
- **TASK-033 — in progress:** added a command-line TS validator for missing,
  unfinished and malformed entries, Qt and named-format placeholder parity,
  and English/Ukrainian plural forms. It can compare against an independently
  extracted source catalog, exits nonzero on errors, and has offline tests.
  An earlier comparison against a fresh Qt extraction reported 57 gaps,
  including false contexts produced for calls such as `dialog.tr`.
  Extraction, validation and compilation are documented.
  Calls through character-dialog and AI-activity instances now use their widget
  classes for translation, so a fresh extraction uses the runtime contexts.
  The extracted marked strings match the Ukrainian source catalog, and an
  automated extraction comparison guards against regressions. This does not
  detect hardcoded, unmarked strings; the broader UI audit and compiled
  catalogs remain outstanding. Do not mark complete on extraction alone.
  Full offline suite: 547 passed, 2 skipped. Duplicate context/source/comment
  entries now fail validation instead of masking an earlier entry; one
  identical duplicate was removed from the Ukrainian source catalog. Focused
  validator tests and the full offline suite passed: 570 passed, 2 skipped.
  The validator now also checks plural flags against extracted source entries
  and rejects plural forms in non-plural messages; focused tests cover both
  mismatch directions. Python format-field detection now includes attribute
  and index lookups, with regression tests for changed fields and conversions.
  Full offline suite: 639 passed, 2 skipped.
- **TASK-033 audit extension:** `tools/audit_ui_strings.py` reports likely
  unmarked literals and f-strings in selected Qt UI calls, with an optional
  nonzero exit for findings and explicit parse-error handling. A current scan
  reports 148 candidates requiring human review; this heuristic neither
  covers every API nor proves each candidate is user-visible. Catalog
  compilation and the broader audit remain outstanding. Full offline suite:
  596 passed, 2 skipped. After reviewing that initial set, three candidates
  remain: the product name and two labels built from project or path data.
  The audit now also checks status messages, dialog buttons and file-dialog
  labels; the expanded scan reports 45 candidates for review. The scan now
  also covers tab, item, progress and dialog-detail labels. It found two
  untranslated project translation progress messages, now added to the
  Ukrainian catalog; other new candidates are language names. Runtime and
  audit tests pass. The heuristic still does not cover every UI API. Full
  offline suite: 631 passed, 2 skipped.
- **TASK-032 — in progress:** the Ukrainian source catalog now covers the
  previously missing character portrait and scene-development workflow labels,
  prompts and errors, plus the main-window open-error title. A full UI audit,
  extraction-context cleanup and compiled catalog remain outstanding. Do not
  mark complete. Temporary-catalog runtime translation tests passed; full
  offline suite: 539 passed, 2 skipped. Character profile state and scene
  history headings are now translated in the dialog's runtime context; a
  compiled temporary catalog test checks all three headings. The wider audit
  and release catalog compilation remain outstanding. Project-document opening
  and verification status/error messages now use translated strings with
  preserved dynamic details. Translation extraction and temporary-catalog
  tests pass; the full offline suite passed: 557 passed, 2 skipped. The editor's
  spelling context-menu Replace and Ignore actions now use translated labels,
  retaining the original and proposed words as placeholders. Standalone file
  open/save dialogs, status and error headings, and recovery-cleanup and
  autosave failure messages have also been marked and translated. PDF export
  dialogs, overwrite and unsaved-content prompts, and status/error headings
  now use Ukrainian catalog entries with tested path placeholders. The wider
  audit, including PDF document labels, and release catalog compilation
  remain outstanding. Markdown/plain-text export dialogs, options, prompts and
  status messages are now translated as well; a Qt regression verifies that a
  translated plain-text filter still selects plain-text output. The broader
  audit and release catalog compilation remain outstanding. The recovery
  chooser, inspection and discard messages now use Ukrainian catalog entries;
  temporary-catalog tests check dynamic recovery details. Further recovery
  flows and the wider audit remain outstanding. Recovery restore failure,
  comparison and attention headings, successful restore feedback, and the
  duplicate-open warning now also use Ukrainian catalog strings. Recovery
  comparison labels, status and read-error wrappers are now translated without
  translating document text. Underlying restore errors and the wider audit
  still need localization; release catalog compilation remains outstanding.
  Closing a tab and quitting now share translated unsaved-document prompts,
  including the untitled-document name; an offscreen test checks cancellation
  with a temporarily compiled Ukrainian catalog. Project creation, character
  filtering, project errors and chapter, scene, note and character creation
  prompts now use translated labels. Note-type choices retain their stable
  manifest values in both languages; offscreen tests cover all five types.
  Project-item removal choices and destructive confirmations are now translated,
  with cancellation and path placeholders covered by tests. Move, import,
  rename, duplicate and link-management prompts now use Ukrainian strings;
  an offscreen test checks that translated link choices retain their IDs.
  Scene-character association prompts are translated as well; tests verify
  that both localized presence choices preserve their stored values and that
  existing development details round-trip. Directed-relationship management
  and character-profile import/export messages are also translated; a Qt test
  checks the localized remove action targets the correct relationship. The
  AI project setup, Auto-writer and project translation confirmation messages
  now disclose their content and destination in Ukrainian; a cancellation test
  checks the translated destination and language labels. Template-suggestion
  and autonomous Auto-pilot disclosures now also show the destination and the
  automatic-application behavior in Ukrainian; a cancellation test checks that
  disclosure. Project-analysis confirmations now translate the selected scene,
  reference-note and associated-character labels, context limit and destination
  without changing the model prompt. Writing-goal feedback and accessibility
  names, character mention search, revision snapshots, settings validation and
  the AI diagnostics privacy warning are also translated. Whole-document
  formatting choices, outline validation, project navigation accessibility,
  AI setup and analysis errors, and connection-test feedback now use catalog
  strings. A Qt test checks that a translated formatting choice still performs
  the intended undoable operation. Recent-file and project persistence errors,
  writing-goal, recovery and shutdown status messages now use Ukrainian
  strings, with dynamic error details retained. The project-open dialog title
  and additional AI setup, generation and analysis status messages are now
  translated; an offscreen test checks the dialog title using a temporary
  compiled catalog. Further workflows still need auditing and release catalog
  compilation remains outstanding. Line and column labels, AI error details,
  and spellcheck feedback now use translated templates, including Ukrainian
  plural forms. AI connection states are also translated at display time while
  retaining their internal values. Runtime tests cover connection status,
  error details and plural selection. Project translation success, failure,
  cancellation and stale-state messages now use Ukrainian templates while
  preserving paths and error details; runtime catalog tests cover feedback.
  Translation progress now localizes its status and field labels in the UI
  while preserving source titles and IDs and the service's progress API.
  Auto-writer progress, cancellation, stale-state, completion and failure
  feedback now also uses Ukrainian templates, preserving scene titles, error
  details and snapshot paths. Runtime tests cover progress and failure and
  cancellation messages. Full offline suite: 641 passed, 2 skipped.
- **TASK-034 — in progress:** the spelling and Auto-writer review lists now
  expose keyboard-selection instructions through their accessibility
  descriptions. Offscreen tests inspect the Qt accessible interface and use
  arrow and Space keys to select and reject items. Project search now moves
  focus from its query to the results with Down, exposes result navigation
  instructions, and opens a selected result with Enter. Quick Open's Down
  shortcut is limited to its query so arrow keys can navigate its results.
  Offscreen keyboard tests cover both workflows. Native keyboard, screen
  reader and system-palette audits across core workflows, as well as compiled
  translations, remain outstanding. Do not mark complete. Full offline suite:
  635 passed, 2 skipped.
- **TASK-035 — complete:** documented independent scope and decisions for
  toolbar, appearance override, interface languages, writing languages and
  alternative providers in `UNIMPLEMENTED_FEATURES.md`. All are deferred for
  the stated usability, verification, maintenance or privacy reasons; no new
  extension is selected. Existing local-first behavior is unchanged. This is
  a documentation-only decision and needs no platform-specific verification.

The initial worktree included staged `.DS_Store` files and Python bytecode.
Preserve these unrelated changes. Earlier checkpoint implementation was
committed in `c5c2330`; the subsequent character AI fix is in `82b693f`.
The performance checkpoint is `b85cc21`; `780e44c` subsequently removed
several task definitions from `TASKS.md`. The save fingerprint checkpoint is
`437302c`.
