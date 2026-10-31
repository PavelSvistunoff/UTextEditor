
# Implementation progress

- **TASK-005.04 — PARTIAL (2026-10-31):** project manifest writes now use
  the shared document write lock. The lock is reentrant so bulk workflows
  can persist manifests while already holding it. Added
  `test_manifest_and_standalone_saves_coordinate_in_process`; focused document
  and project tests: 66 passed; full offline suite: 673 passed, 2 skipped.
  README updated; diff whitespace check passed. Independent-process races
  and native platform verification remain unresolved. No commits or pushes.

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
- **TASK-009.04 — PARTIAL:** revision comparisons identify changed manifest
  fields for character profiles, directed relationships and scene-character
  associations, without displaying their values or portrait data. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 162 passed; full offline suite: 666 passed, 2 skipped; Ukrainian
  source catalog validation passed. Before-and-after metadata values, broader
  structure comparisons, native accessibility review and
  release catalog compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** the revision comparison now displays both old
  and new titles and stable IDs for renamed chapters, scenes and notes. Modified
  `app/ui/revision_history_dialog.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 162 passed; full offline suite: 666 passed, 2 skipped; Ukrainian
  source catalog validation passed. Metadata field-level differences, native
  accessibility checks and release catalog compilation
  remain outstanding.
- **TASK-005.04 — PARTIAL:** standalone saves and project text writes now
  share an in-process lock over fingerprint checks and replacement, including
  project bulk text updates. Threaded regressions cover two standalone saves
  and a project save racing a standalone save. Modified
  `app/document/file_manager.py`, `app/document/write_lock.py`,
  `app/project/service.py`, `tests/test_document.py`,
  `tests/test_project_domain.py`, and `README.md`. Focused document, project
  and translation suites: 71 passed; full offline suite: 665 passed, 2 skipped.
  Independent-process coordination remains outstanding, as does coordination
  with separate project manifest writes.
- **TASK-009.04 — PARTIAL:** revision comparisons now report added, removed
  and changed scene-character associations by stable character ID, ignoring
  association-list reordering. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `tests/test_revisions.py`,
  `tests/test_project_ui.py`, `translations/utexteditor_uk.ts`, and `README.md`.
  Focused revision and UI suites: 161 passed; full offline suite: 663 passed,
  2 skipped; Ukrainian source catalog validation passed. Field-level metadata
  differences and broader structure comparisons remain,
  as do native accessibility verification and release catalog compilation.
- **TASK-009.04 — PARTIAL:** revision comparisons now flag added, removed and
  changed character profiles and directed relationships by stable ID, without
  rendering profile data or portraits. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `tests/test_revisions.py`,
  `tests/test_project_ui.py`, `translations/utexteditor_uk.ts`, and `README.md`.
  Focused revision and UI suites: 159 passed; full offline suite: 661 passed,
  2 skipped; Ukrainian source catalog validation passed. Field-level
  differences, scene-character association changes, native
  accessibility checks and release catalog compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** comparisons now report project title changes
  and scene/reference-note path changes with before/after values. Missing path
  or title metadata in legacy structures does not produce inferred changes.
  Modified `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 157 passed; full offline suite: 659 passed, 2 skipped; Ukrainian
  source catalog validation passed. Other metadata and structure comparisons,
  native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** comparisons now identify a scene's chapter change,
  including moves to or from ungrouped, even when its flattened ordering does
  not change. Stable chapter IDs distinguish duplicate titles; legacy snapshot
  structures without scene-parent data do not generate inferred moves. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 155 passed; full offline suite: 657 passed, 2 skipped; Ukrainian
  source catalog validation passed. Other structure and metadata comparisons,
  native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** revision comparisons now report chapter
  additions, removals, title changes and reordering, avoiding false moves from
  insertions or removals. The review dialog labels chapter changes. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, `UNIMPLEMENTED_FEATURES.md`,
  and `TASKS.md`. Focused revision and project UI suites: 153 passed; full
  offline suite: 655 passed, 2 skipped. Ukrainian source catalog validation
  passed. Directed link additions and
  removals are also reported by stable IDs. Scene-parent and other
  structure comparisons, native accessibility checks and release catalog
  compilation remain outstanding.
- **TASK-009.01 — DONE:** snapshot previews now provide previous/next pages
  over all captured scene and note text, retaining a 32,768-character display
  bound per page. Selecting a different snapshot resets the page. Modified
  `app/ui/revision_history_dialog.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, and `TASKS.md`. Focused
  revision and project UI suites: 150 passed; full offline suite: 652 passed,
  2 skipped. Ukrainian source catalog validation passed. Native accessibility checks and release catalog
  compilation remain outstanding.
- **TASK-009.01 — PARTIAL:** selecting one revision shows a read-only preview
  of scene and note contents, capped at 32,768 characters and labeled when
  truncated. A selection generation prevents older asynchronous comparisons
  from replacing the current preview. Modified `app/ui/revision_history_dialog.py`,
  `app/ui/main_window.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, and `TASKS.md`. Focused
  revision and project UI suites: 150 passed; full offline suite: 652 passed,
  2 skipped. Ukrainian source catalog validation passed. Full access to
  content beyond the preview limit, native
  accessibility verification, and release catalog compilation remain.
- **TASK-009.02 — DONE:** the revision history dialog now offers confirmed
  deletion of a single selected snapshot in a worker. The store revalidates
  the captured digest and rejects symlinks before deletion; project text is
  untouched. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `app/ui/main_window.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, `UNIMPLEMENTED_FEATURES.md`,
  and `TASKS.md`. Focused revision and project UI suites: 148 passed; full
  offline suite: 650 passed, 2 skipped. Ukrainian source catalog validation
  passed. A separate process could still
  replace the file between the final integrity check and unlink; native
  accessibility verification and release catalog compilation remain.
- **TASK-008.02 — DONE:** recovery scans now report unfinished atomic-write
  temporary files as well as malformed snapshots. The report says a write may
  still be in progress; automatic retention and document cleanup preserve
  these files, and confirmed discard removes them. Modified
  `app/document/recovery.py`, `app/ui/main_window.py`,
  `translations/utexteditor_uk.ts`, `tests/test_recovery.py`, `README.md`, and
  `TASKS.md`. Focused recovery and project UI suites: 155 passed; full offline
  suite: 648 passed, 2 skipped. Ukrainian source catalog validation passed.
  Incomplete files are diagnostic only;
  extracting intact content, native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-005.02 — DONE:** added
  `test_separate_process_edit_after_final_check_exposes_save_race` in
  `tests/test_document.py`. A subprocess writes between the final check and
  replacement, demonstrating that its edit is currently overwritten. This
  assertion records a known defect and must change when coordination is fixed.
  Focused document and project-domain suites: 63 passed; full offline suite:
  646 passed, 2 skipped. Independent-process coordination remains outstanding.
- **TASK-008.04 — DONE:** the recovery dialog can restore one selected
  readable snapshot, including an older version, via the existing conflict-safe
  background restore. Updated `app/ui/main_window.py`,
  `translations/utexteditor_uk.ts`, `tests/test_project_ui.py`, `README.md`,
  `TASKS.md`, and `UNIMPLEMENTED_FEATURES.md`. Focused recovery and project UI
  suites: 154 passed; full offline suite: 647 passed, 2 skipped. Ukrainian
  source catalog validation passed. Invalid snapshots remain
  diagnostic only; release catalog compilation and native accessibility
  verification remain outstanding.
- **TASK-005.01 and TASK-005.05 — DONE (audit):** inspected
  `app/document/file_manager.py` and `app/project/service.py`. Both recheck
  after staging; project text writes also use a process-local lock. Separate
  process staging tests in `tests/test_document.py` and
  `tests/test_project_domain.py` cover conflicts. README documents the final
  check-to-replace race with independent writers. TASK-005.04 remains partial:
  those checks cannot prevent a change after the last check. No native
  cross-platform coordination verification was performed.
- **TASK-008.02 — PARTIAL:** recovery scan now reports malformed or
  timezone-free capture timestamps and orders valid timestamps by instant,
  preventing a damaged timestamp from selecting the wrong latest snapshot.
  The invalid file remains available for diagnosis, but its text cannot yet
  be selectively recovered in the UI. Modified `app/document/recovery.py`,
  `tests/test_recovery.py`, `README.md`, `TASKS.md`, and this file. Focused
  recovery and project UI suites: 153 passed. Full offline suite: 645 passed,
  2 skipped. Further incomplete-set diagnosis and selective recovery remain.
- **TASK-001.01 — DONE:** reviewed `WritingGoalTracker.record_text` and the
  Qt undo integration in `MainWindow._record_writing_goal_text` against
  `test_history_keeps_one_text_copy_and_tracks_undo_branch_across_days` and
  `test_compacted_command_preserves_daily_counts_through_reset_undo_and_redo`.
  Merged commands share an endpoint and cleared undo stacks are pruned, but
  separately reachable commands still each retain metadata. TASK-001.02 and
  .04 remain partial; bounding them safely needs a design that preserves Qt
  undo and redo semantics.
- **TASK-008.05 — DONE:** automatic retention and saved-document cleanup now
  preserve unreadable, invalid, and unsupported-version recovery snapshots;
  confirmed explicit discard can still remove them. Modified
  `app/document/recovery.py`, `tests/test_recovery.py`, `README.md`, and
  `TASKS.md`. `tests/test_recovery.py`: 14 passed; full offline suite: 642
  passed, 2 skipped. Damaged snapshots can
  accumulate until explicitly discarded; recovery diagnosis and selective
  recovery remain incomplete.
- **Audit queue:** complete the remaining atomic status audit; prioritize
  TASK-005 save coordination, TASK-007 conflict protection, TASK-008 recovery
  diagnosis, and TASK-009 safe revision management before performance and UX.
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
- **TASK-005 — in progress:** standalone saves, project text saves, and
  project manifest saves recheck the disk after staging. Separate-process
  regression tests cover edits during staging. A separate-process edit injected
  immediately after the last check is still overwritten: no portable atomic
  compare-and-replace or independent-editor lock is in place. Do not mark this
  task complete until a supported coordination guarantee is implemented and
  cross-platform verification is performed. The full offline suite after this
  mitigation passed: 424 passed, 2 skipped (`QT_QPA_PLATFORM=offscreen
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`).
- **TASK-006 — in progress:** bounded completion-context construction now
  searches only the requested window, avoiding a copy of the entire prefix.
  On this machine, `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
  benchmarks/completion_context.py` measured 100 middle-of-document calls on
  five million characters: previous 0.0459 s and 2,504,082 peak Python bytes;
  current 0.0001 s and 4,041 bytes. These are microbenchmarks, not GUI latency
  or process memory measurements. An offscreen GUI baseline is now available
  via `benchmarks/editor_responsiveness.py`, with new-word tracking enabled.
  For 100,000/1,000,000 characters, before the tracker optimization, opening
  in Qt took 8.48/73.63 ms, typing 10.98/78.85 ms, cursor movement 1.91/14.83
  ms, word counting 1.40/14.33 ms, and cumulative peak RSS was 102/125 MB.
  Comparing unchanged edit spans in chunks reduced measured typing to
  8.68/67.20 ms in a subsequent run; Qt opening was 8.71/77.89 ms. These
  single-run, offscreen timings include GUI callbacks but exclude rendering
  and are not platform-independent thresholds. The one-million-character
  case remains slow; representative repeated measurements, GUI event-loop
  latency and further investigation are still needed. Do not mark complete.
- **TASK-007 — in progress:** fixed the standalone save callback to retain the
  newly written disk fingerprint, including after Save As. A Qt regression
  test exercises two saves followed by an external edit and verifies that the
  conflict preserves the buffer and disk. File > Review External Changes now
  presents saved, disk, and buffer versions alongside an editable conservative
  merge proposal for standalone and project files. Reload and merge are
  undoable, Save Elsewhere uses the existing save flow, and the disk is
  rechecked after review and on save. Tests cover cancellation, stale buffers
  and disk, unresolved markers, reload, Save Elsewhere, and project and
  standalone files. The Ukrainian source catalog has been updated; its
  compiled catalog remains to be rebuilt through the project's release
  process. The residual cross-process race means the no-silent-overwrite
  acceptance criterion is not yet fully met; do not mark this task complete.
  Full offline suite: 444 passed, 2 skipped.
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
