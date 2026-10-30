
# Implementation progress

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
  2 skipped.
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
  suite: 460 passed, 2 skipped.
- **TASK-016 — in progress:** Qt's existing Ctrl+Tab and Ctrl+Shift+Tab
  behavior was verified with offscreen keyboard tests, and View > Open Tabs
  provides a searchable picker with modified markers, file/project context,
  and distinct labels for duplicate untitled tabs. Closing remains handled by
  the existing unsaved-change flow. Compiled Ukrainian strings and manual
  native-platform shortcut verification remain outstanding; do not mark
  complete until verified. Full offline suite: 462 passed, 2 skipped.

The initial worktree included staged `.DS_Store` files and Python bytecode.
Preserve these unrelated changes. Earlier checkpoint implementation was
committed in `c5c2330`; the subsequent character AI fix is in `82b693f`.
The performance checkpoint is `b85cc21`; `780e44c` subsequently removed
several task definitions from `TASKS.md`. The save fingerprint checkpoint is
`437302c`.
