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
- **TASK-014 — implemented:** Project > Reveal Current Document in Project
  locates a bound scene or note by stable ID, expands only its ancestors and
  preserves other expansion state. Standalone and unavailable items report
  why they cannot be revealed. Offline Qt tests cover both item types,
  duplicate titles, unsaved text, and standalone documents; Ukrainian strings
  are in the catalog. The full offline suite passed: 414 passed, 2 skipped
  (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
  pytest -q`).

The initial worktree included staged `.DS_Store` files and Python bytecode.
Preserve these unrelated changes. Earlier checkpoint implementation was
committed in `c5c2330`; the subsequent character AI fix is in `82b693f`.
