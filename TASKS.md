# UTextEditor — TASKS.md (atomic revision 2)

> Planning baseline: `TASKS.md`, `IMPLEMENTATION_PROGRESS.md`, `README.md`, `SPEC.md`, `UNIMPLEMENTED_FEATURES.md`, `AGENTS.md` (2026-10-31).
> Atomic status synchronization is in progress. Updated checkboxes are backed by code and test review; other inherited statuses still require verification. `partial` does not mean acceptance criteria are satisfied.

## Working agreement

- Execute **one atomic subtask** per Codex run unless explicitly asked otherwise.
- Before implementation inspect the current code, README, tests and working-tree diff; do not overwrite unrelated work.
- Each subtask must produce one independently reviewable change, a focused test (or documented reason), and evidence of verification.
- For UI changes update English/Ukrainian source strings; compiled catalog and native verification are separate subtasks.
- Preserve unsaved content, transactionality, backward compatibility, and offline editing without Ollama.
- Run focused tests, then `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` when practical; check `git diff --check`.
- States: `[x]` documented complete, `[~]` implemented partly / verification outstanding, `[ ]` not documented complete, `[?]` requires code-level confirmation. Never promote a task merely because UI exists.

## Summary of parent tasks

| Parent | Scope | Documented state |
|---|---|---|
| TASK-001 | Fix writing-goal history memory growth | open |
| TASK-002 | Correct AI destination labeling | complete |
| TASK-003 | Implement first-use AI context disclosure | complete |
| TASK-004 | Coalesce slow AI requests | complete |
| TASK-005 | Investigate and mitigate save race conditions | partial |
| TASK-006 | Benchmark large-document responsiveness | partial |
| TASK-007 | Implement external file conflict resolution | partial |
| TASK-008 | Improve recovery diagnosis | open |
| TASK-009 | Implement revision snapshot management | open |
| TASK-010 | Implement portable project backup | open |
| TASK-011 | Improve file encoding and large-file handling | open |
| TASK-012 | Implement project-wide full-text search | partial |
| TASK-013 | Implement Quick Open | partial |
| TASK-014 | Add Reveal in Project | complete |
| TASK-015 | Implement related-item navigation | partial |
| TASK-016 | Improve tab navigation | partial |
| TASK-017 | Add recent standalone documents | partial |
| TASK-018 | Improve menu organization | partial |
| TASK-019 | Implement navigation history | partial |
| TASK-020 | Improve Find and Replace | partial |
| TASK-021 | Implement batch spelling and grammar review | partial |
| TASK-022 | Implement AI context preview and controls | partial |
| TASK-023 | Add AI translation batch review | partial |
| TASK-024 | Improve AI scene draft review | partial |
| TASK-025 | Add optional streaming AI previews | partial |
| TASK-026 | Improve inline completion display | partial |
| TASK-027 | Implement Markdown preview | partial |
| TASK-028 | Improve manuscript export and PDF settings | partial |
| TASK-029 | Add writing-goal history viewer | open |
| TASK-030 | Improve character profile navigation | partial |
| TASK-031 | Improve automatic language detection | complete |
| TASK-032 | Complete Ukrainian interface localization | partial |
| TASK-033 | Add automated localization validation | complete |
| TASK-034 | Perform accessibility audit and fixes | partial |
| TASK-035 | Evaluate and implement selected interface extensions | complete (evaluation only; extensions deferred) |

## Atomic execution backlog

Each checkbox is a separately executable ticket. Subtasks under a partially implemented parent are **verification / remaining-work candidates**, not assertions that the listed functionality is absent. Confirm existing implementation before writing code.

### TASK-001 — Fix writing-goal history memory growth
**Priority:** High · **Parent status:** open

- [x] **TASK-001.01** — Investigate state-record growth during long editing sessions.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-001.02** — Implement bounded history metadata without breaking word counts.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-001.03** — Preserve correct behavior across undo, redo, pause, and reset.
  Saving to an unused tracking identity now retains checkpoints; same-ID rekeys
  retain matching history. Existing-destination progress and mismatched text
  now form minimum daily counts in transferred checkpoints when the destination
  is not actively tracked. Scope/enable transitions now
  preserve checkpoints, with no new-word credit for inactive edits; bounded
  history and actively tracked identity collisions remain outstanding.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-001.04** — Coordinate pruning with Qt undo history.
  Merged commands are compacted; deferred Qt availability checks now release
  unreachable checkpoints after either or both stacks are cleared without a
  text change, including disabling undo. Remaining-direction undo/redo and
  daily counts are covered by offscreen regressions. Reachable history is
  still unbounded (TASK-001.02); this ticket does not impose an undo limit.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-001.05** — Benchmark realistic long editing sessions.
  History benchmark now accepts command/undo counts and checks branching after
  undo; 100-command smoke and 10,000-command runs passed. The latter retained
  10,001 states and 3,723,574 current Python-traced bytes; no bound established.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Memory growth is measured and bounded for the supported editing history.
- Undo/redo does not produce incorrect daily counts.
- Existing writing-goal tests pass.
- New stress and regression tests pass.

### TASK-002 — Correct AI destination labeling
**Priority:** High · **Parent status:** complete

- [x] **TASK-002.01** — Identify messages that incorrectly describe remote Ollama hosts as local.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-002.02** — Update project setup and Auto-writer confirmations.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-002.03** — Display the actual configured destination.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-002.04** — Update translations and tests.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Remote destinations are never described as local.
- Users can identify where document content will be sent.
- Both local and remote configurations are tested.

### TASK-003 — Implement first-use AI context disclosure
**Priority:** High · **Parent status:** complete

- [x] **TASK-003.01** — Show disclosure before the first AI request containing document context.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-003.02** — Cover automatic completion and spellcheck.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-003.03** — Show the configured destination and categories of transmitted data.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-003.04** — Require renewed disclosure when the destination materially changes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-003.05** — Persist consent appropriately without storing document content.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- No context-bearing request is sent before required disclosure.
- Declining does not modify documents.
- Disclosure correctly handles remote Ollama hosts.
- Repeated requests do not unnecessarily interrupt writing.

### TASK-004 — Coalesce slow AI requests
**Priority:** High · **Parent status:** complete

- [x] **TASK-004.01** — Inspect `FunctionWorker` and request scheduling.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-004.02** — Keep at most one running and one latest pending spellcheck request per relevant request stream.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-004.03** — Replace superseded pending snapshots.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-004.04** — Prevent stale responses from modifying UI state.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-004.05** — Preserve cancellation and shutdown behavior.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Repeated requests do not create unbounded concurrent provider calls.
- Only current results are displayed.
- Slow and failed provider calls are covered by tests.
- UI remains responsive.

### TASK-005 — Investigate and mitigate save race conditions
**Priority:** High · **Parent status:** partial

- [x] **TASK-005.01** — Inspect `app/document/file_manager.py` and `app/project/service.py`.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-005.02** — Reproduce the check-before-replace race using separate processes.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-005.03** — Evaluate platform-appropriate coordination.
  Evaluation and platform verification boundaries: docs/save-coordination.md.
  Executable POSIX experiment confirms an advisory exclusive lock does not
  exclude an uncooperative subprocess writer; independent-writer race remains.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-005.04** — Implement a safe mitigation where practical.
  Shared reentrant in-process coordination now covers standalone, project text,
  and manifest saves (673 passed, 2 skipped); independent-process races remain.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-005.05** — Document residual risks.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Concurrent modifications are detected or safely coordinated within the supported guarantee.
- No silent overwrite occurs in tested conflict scenarios.
- Atomic replacement and recovery behavior remain correct.
- Remaining cross-process limitations are documented.

- [x] **TASK-005.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  Acceptance matrix and named regressions: docs/save-coordination.md. .01,
  .02, .03 and .05 verified; .04 and parent remain partial because the suite
  explicitly reproduces the independent-writer final-check overwrite window.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [x] **TASK-005.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  N/A for UI/catalog checks: coordination changes no GUI or strings. Native
  filesystem and multi-process guarantees remain unverified as documented;
  this does not complete the parent or TASK-007.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-006 — Benchmark large-document responsiveness
Evidence: editor_responsiveness.py covers reads, GUI open, typing, cursor,
search, word counts and completion context with new-word tracking enabled.
Sizes and repetition counts are configurable; repeated operations report
median/max. Read/open samples remain single; RSS is a cumulative process peak
where supported. Native event-loop latency and representative project workloads
remain unverified.
**Priority:** Medium · **Parent status:** partial

- [x] **TASK-006.01** — Benchmark opening, typing, cursor movement, searching, and word counts.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-006.02** — Include writing-goal tracking and AI context construction.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-006.03** — Measure GUI-thread latency and memory usage.
  The benchmark now measures ready zero-timer callback delays during idle and
  typing with new-word tracking, alongside cumulative RSS. Ten-sample
  100K/1M/5M results and limitations are in docs/gui-latency-evaluation.md.
  Native input/paint latency and representative project workloads remain open.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-006.04** — Establish representative document sizes and repeatable benchmarks.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-006.05** — Optimize confirmed bottlenecks without weakening correctness.
  Writing-goal token scanning is limited to the changed span plus boundary
  context; exhaustive small-edit equivalence regression passes.
  Goal refresh also skips buffer word scans for paused/disabled and new-word
  goals. Overall GUI latency and bounded history remain outstanding.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Baseline and post-change measurements are documented.
- Performance regressions can be detected.
- UI behavior and correctness are preserved.

- [x] **TASK-006.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  Acceptance matrix, named regressions and reproducible context baseline are
  in docs/gui-latency-evaluation.md. .01/.02 verified; .03/.04/.05 and parent
  remain partial for native/representative workloads and unresolved bounds.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [x] **TASK-006.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  UI/catalog checks N/A: internal optimizations and benchmarks introduce no
  controls or Qt strings. Native performance checks remain .03/.04; they
  are not waived by this UI-specific N/A.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-007 — Implement external file conflict resolution
Audit: version display, explicit reload/save-elsewhere/merge, cancellation and
stale-review protection are verified. Saves recheck staged disk state; the
independent-process final-check-to-replace race remains (TASK-005). Native
keyboard/screen-reader checks and release translation compilation remain open.
**Priority:** High · **Parent status:** partial

- [x] **TASK-007.01** — Detect when disk content differs from the saved base.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-007.02** — Present saved base, current disk version, and open buffer.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-007.03** — Support reload, save elsewhere, and reviewed merge.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-007.04** — Preserve unsaved content when the user cancels.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-007.05** — Recheck disk state before writing.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Conflicting content is never overwritten silently.
- Three-way merge conflicts are clearly identified.
- Cancellation preserves all versions.
- Concurrent-change tests pass.

- [x] **TASK-007.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-007.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-008 — Improve recovery diagnosis
**Priority:** High · **Parent status:** open

- [x] **TASK-008.01** — Show per-document recovery status and timestamps.
  Scan workers capture canonical-file state (unchanged, changed, missing,
  appeared, unreadable, unknown, or untitled); chooser details show it with
  each capture timestamp in English/Ukrainian. Hashing uses bounded chunks
  and rejects non-regular files. Status is advisory and restore rechecks disk.
  Domain and temporary-catalog UI regressions pass; broader diagnosis,
  release catalog and native verification remain open.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-008.02** — Identify incomplete or corrupt recovery entries.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-008.03** — Display readable diagnostic information.
  Directory-listing failures now produce per-directory diagnostics while other
  readable snapshots remain recoverable. Root enumeration failures also return
  a diagnostic. Symbolic-link snapshots are diagnosed and preserved by automatic
  cleanup. Directory-resolution errors also preserve access to other snapshots;
  comparisons now label truncation beyond 6,000 characters in English/Ukrainian;
  Empty/NUL-containing snapshot paths are diagnosed and preserved; broader
  inspection includes captured text when a canonical file is absent. Broader
  diagnosis remains incomplete.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-008.04** — Support selective recovery or export of valid content.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-008.05** — Preserve damaged recovery data until explicitly discarded.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Partial recovery sets can be inspected.
- Invalid entries do not prevent recovery of valid entries.
- Canonical files are never silently overwritten.
- Unrecoverable data is clearly identified.

### TASK-009 — Implement revision snapshot management
**Priority:** High · **Parent status:** open

- [x] **TASK-009.01** — Add snapshot preview.
  History chronology now uses timezone-aware instants; malformed/timezone-free
  capture timestamps are diagnosed without hiding valid snapshots. Directory
  enumeration failures and symbolic-link snapshots are also diagnosed. Note
  previews use captured titles plus stable IDs, with legacy ID fallback.
  The comparison dialog now also orders selected snapshots by instant rather
  than timestamp text; an offscreen regression covers differing UTC offsets.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-009.02** — Add confirmed snapshot deletion.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-009.03** — Add selective restore.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-009.04** — Extend comparison to chapter, link, and project-structure changes.
  Reference-note relative reordering is now reported without false moves from
  additions/removals; moved items expose stable IDs using existing translations.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-009.05** — Add optional scheduled snapshots and retention policies.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-009.06** — Create safety snapshots before destructive restores.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Users can inspect affected content before restoring.
- Unsaved buffers are handled explicitly.
- Restore is transactional or leaves original data intact on failure.
- Snapshot deletion requires confirmation.

### TASK-010 — Implement portable project backup
**Priority:** Medium · **Parent status:** open

- [ ] **TASK-010.01** — Allow users to select a backup destination.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-010.02** — Include project metadata and required manuscript files.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-010.03** — Explicitly define handling of revisions and unsaved buffers.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-010.04** — Add read-only backup integrity validation.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-010.05** — Support restoring a backup into a separate directory.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Backup contents are documented.
- Missing or unreadable files are reported.
- Existing destinations are not overwritten without confirmation.
- Restored projects pass integrity checks.

### TASK-011 — Improve file encoding and large-file handling
**Priority:** Medium · **Parent status:** open

- [x] **TASK-011.01** — Investigate support for non-UTF-8 encodings.
  Completed codec experiment and compatibility design in docs/encoding-support.md;
  strict failure-preservation regressions pass. Selection remains TASK-011.02.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-011.02** — Add encoding selection where appropriate.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-011.03** — Add line-ending detection and selection.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-011.04** — Improve binary-file detection.
  Shared control-character heuristic rejects NUL/non-whitespace ASCII controls
  and DEL at standalone/project reads, import/relink and conflict review.
  Unicode and text whitespace are retained; universal binary detection is not
  claimed. Focused regressions and full offline suite pass.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-011.05** — Evaluate memory and responsiveness for large files.
  Evaluated 1M/5M/10M-character sessions and byte-verified saves; results and
  implementation review in docs/large-file-evaluation.md. No enforced safe
  file-size limit exists; the parent safe-large-file gate remains unsatisfied.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Encoding failures are reported without data loss.
- Supported encodings round-trip correctly.
- Line endings are preserved unless explicitly changed.
- Unsupported large files fail safely.

### TASK-012 — Implement project-wide full-text search
**Priority:** High · **Parent status:** partial

- [x] **TASK-012.01** — Search scenes, chapters where applicable, and reference notes.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.02** — Include open unsaved document buffers.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.03** — Provide a persistent results panel.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.04** — Display document title, excerpt, and match location.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.05** — Navigate directly to selected results.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.06** — Support cancellation and bounded resource usage.
  Cooperative cancellation, per-file/result/error limits and POSIX FIFO
  rejection are verified. Open text capture is capped at 8 Mi UTF-16 units
  across tabs; omitted buffers are reported without disk fallback. Descriptor
  metadata still scales with project/tab count, and already-blocked regular-
  filesystem I/O is not interruptible. Native verification remains V2.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-012.07** — Report unreadable files.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Results navigate to the correct document and match.
- Stale matches are not selected incorrectly.
- Unsaved buffers take precedence over disk content.
- Search does not modify project files.
- Large-project and cancellation tests pass.

- [x] **TASK-012.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  Named service/UI tests and remaining resource/native limits are recorded in
  docs/project-search-verification.md. All numbered tickets are verified,
  including .06's aggregate text-capture budget. Parent remains partial
  pending V2. No existing UI was rebuilt.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-012.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-013 — Implement Quick Open
**Priority:** High · **Parent status:** partial

- [x] **TASK-013.01** — Add a keyboard-accessible Quick Open dialog.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-013.02** — Search scene, chapter, note, and character names.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-013.03** — Include character aliases.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-013.04** — Display item type and chapter context.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-013.05** — Use stable IDs when opening selected items.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Duplicate names are distinguishable.
- Deleted items fail gracefully.
- Existing unsaved tabs are preserved.
- Keyboard navigation works.

- [x] **TASK-013.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  All numbered tickets verified by code review and six focused Qt tests;
  evidence is in docs/quick-open-verification.md. Parent remains partial
  pending V2 release-catalog/native keyboard/accessibility verification.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-013.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-014 — Add Reveal in Project
**Priority:** Medium · **Parent status:** complete

- [x] **TASK-014.01** — Add a Reveal in Project action for bound scenes and notes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-014.02** — Expand the necessary tree ancestors.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-014.03** — Select and scroll to the matching project item.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-014.04** — Preserve unrelated tree expansion state.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- The correct stable ID is selected.
- Standalone and unbound tabs are handled explicitly.
- No manuscript content is modified.

### TASK-015 — Implement related-item navigation
**Priority:** Medium · **Parent status:** partial

- [x] **TASK-015.01** — Navigate between linked notes and associated scenes.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-015.02** — Navigate from character profiles to related scenes.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-015.03** — Distinguish explicit associations from text mentions.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-015.04** — Provide a convenient return path.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-015.05** — Protect unsaved profile edits.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Existing links and associations are reused.
- Navigation does not create new metadata relationships.
- Unsaved changes are never silently discarded.

- [x] **TASK-015.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  Existing link/association/profile workflows and eight focused Qt tests are
  mapped in docs/related-navigation-verification.md. All numbered tickets
  verified; parent remains partial for V2 release-catalog/native checks.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-015.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-016 — Improve tab navigation
**Priority:** Medium · **Parent status:** partial

- [x] **TASK-016.01** — Add next/previous-tab navigation.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-016.02** — Add a searchable list of open tabs.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-016.03** — Display project context and modified-state indicators.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-016.04** — Handle duplicate filenames.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-016.05** — Verify native Qt shortcuts.
  Offscreen Ctrl+Tab/Ctrl+Shift+Tab tests pass; actual native OS shortcut and
  assistive-technology verification remains outstanding.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- No shortcut conflicts exist.
- Closing tabs uses existing unsaved-change handling.
- Tab switching works with keyboard only.

- [x] **TASK-016.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  .01–.04 verified; evidence and remaining .05/V2 native checks are recorded
  in docs/tab-navigation-verification.md. Parent remains partial.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-016.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-017 — Add recent standalone documents
**Priority:** Medium · **Parent status:** partial

- [x] **TASK-017.01** — Add a recent-file list separate from recent projects.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-017.02** — Reopen files using existing document-opening logic.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-017.03** — Handle missing or moved files.
  Missing and path-resolution failures are reported without replacing dirty
  tabs, including failures while checking duplicates after a worker read.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-017.04** — Add a clear-history action.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-017.05** — Store paths only, not document content.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Duplicate tabs are avoided.
- Missing files produce useful feedback.
- Unsaved buffers remain safe.
- Recent-file history can be cleared.

- [x] **TASK-017.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  All numbered tickets verified; evidence and path-failure regressions are
  recorded in docs/recent-files-verification.md. Parent remains partial for
  V2 release-catalog/native keyboard/accessibility checks.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-017.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-018 — Improve menu organization
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-018.01** — Review Project and AI menus.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-018.02** — Group related actions logically.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-018.03** — Consider submenus or a command picker.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-018.04** — Preserve existing actions and shortcuts.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-018.05** — Explain unavailable context-dependent actions.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- All existing actions remain accessible.
- Keyboard navigation is preserved.
- No shortcut conflicts are introduced.
- Manual accessibility review is documented.

- [ ] **TASK-018.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-018.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-019 — Implement navigation history
**Priority:** Low · **Parent status:** partial

- [?] **TASK-019.01** — Add bounded Back and Forward navigation history.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-019.02** — Record explicit scene, note, and search-result jumps.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-019.03** — Restore cursor position when safe.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-019.04** — Skip deleted or stale destinations.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-019.05** — Keep history session-local.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Normal typing does not create history entries.
- Unsaved buffers are preserved.
- Removed targets are handled gracefully.

- [ ] **TASK-019.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-019.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-020 — Improve Find and Replace
**Priority:** Medium · **Parent status:** partial

- [x] **TASK-020.01** — Add optional case-insensitive matching.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-020.02** — Add optional whole-word matching.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-020.03** — Improve Find and Replace focus behavior.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-020.04** — Preserve existing default matching semantics.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-020.05** — Keep match counts, navigation, and replacement consistent.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Automated verification: tests/test_find_replace.py (21 passed) covers default
case-sensitive semantics, case/whole-word options, Unicode offsets, batched
counts, stale queries/editor switches, zero matches, small windows, focus
return and undo/redo replacement consistency. Numbered tickets are complete;
parent remains partial pending V2 native keyboard/accessibility review and
release catalog verification. Offscreen Qt tests do not replace that review.

**Parent acceptance gate (all must pass):**
- Unicode search behaves correctly.
- Zero-match and small-window cases work.
- Replacements preserve undo behavior.
- Keyboard focus returns predictably.

- [x] **TASK-020.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-020.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-021 — Implement batch spelling and grammar review
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-021.01** — Collect validated spelling and grammar findings.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-021.02** — Present them in a navigable review dialog.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-021.03** — Show explanations and proposed corrections.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-021.04** — Allow individual selection and rejection.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-021.05** — Apply accepted edits as one undoable operation.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Cancel leaves text unchanged.
- Stale or overlapping suggestions are rejected.
- Model output is validated before application.
- Undo restores the original document.

- [ ] **TASK-021.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-021.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-022 — Implement AI context preview and controls
**Priority:** High · **Parent status:** partial

- [?] **TASK-022.01** — Show the configured AI destination.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-022.02** — Summarize included document and project context.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-022.03** — Identify unsaved buffers and truncation.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-022.04** — Allow excluding reference notes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-022.05** — Allow disabling automatic project context.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-022.06** — Avoid interrupting every completion request.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Preview corresponds to the captured request.
- Context changes invalidate stale responses.
- Unassociated characters are not implicitly included.
- No document content is transmitted without required disclosure.

- [ ] **TASK-022.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-022.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-023 — Add AI translation batch review
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-023.01** — Show original and translated content side by side.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-023.02** — Include translated titles and text.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-023.03** — Allow per-item navigation.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-023.04** — Require explicit Apply or Cancel.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-023.05** — Revalidate project state before applying.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- IDs, paths, links, and line endings are preserved.
- Cancel leaves the project unchanged.
- Apply remains all-or-nothing.
- Translation failures do not partially modify project data.

- [ ] **TASK-023.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-023.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-024 — Improve AI scene draft review
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-024.01** — Add per-scene draft review for Auto-writer output.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-024.02** — Display generated text separately from committed manuscript content.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-024.03** — Support accept, reject, and review navigation.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-024.04** — Define how partial acceptance affects batch consistency.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-024.05** — Protect existing scene content.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Rejected drafts do not modify scenes.
- Accepted changes are explicitly confirmed.
- Stale project state is detected.
- Failed batches do not leave unintended partial changes.

- [ ] **TASK-024.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-024.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-025 — Add optional streaming AI previews
**Priority:** Low · **Parent status:** partial

- [?] **TASK-025.01** — Add optional Ollama streaming support.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-025.02** — Update workers to consume streamed output.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-025.03** — Display provisional tokens incrementally.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-025.04** — Bound partial-output memory.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-025.05** — Support cancellation and stale-result rejection.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Partial output never automatically enters the manuscript.
- Final application requires explicit acceptance.
- Cancellation leaves existing content unchanged.
- Non-streaming behavior remains supported.

- [ ] **TASK-025.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-025.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-026 — Improve inline completion display
**Priority:** Low · **Parent status:** partial

- [?] **TASK-026.01** — Investigate readable alternatives for long suggestions.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-026.02** — Consider multiline and mid-line completion previews.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-026.03** — Handle suggestions exceeding viewport width.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-026.04** — Preserve explicit acceptance via Tab.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-026.05** — Retain safe rejection when a suggestion cannot be represented.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Normal typing is never blocked.
- Suggestions never silently modify text.
- Cursor and selection behavior remain correct.
- Small-window and multiline cases are tested.

- [ ] **TASK-026.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-026.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-027 — Implement Markdown preview
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-027.01** — Add a Markdown preview for the active document.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-027.02** — Support unsaved buffer content.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-027.03** — Update preview when appropriate without blocking typing.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-027.04** — Keep preview read-only.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-027.05** — Avoid unsafe external-resource loading.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Preview reflects current text.
- Preview does not modify manuscript content.
- Large documents do not freeze the UI.
- Feature works without Ollama.

- [ ] **TASK-027.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-027.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-028 — Improve manuscript export and PDF settings
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-028.01** — Add export preview.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-028.02** — Add selectable page sizes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-028.03** — Add title-page metadata.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-028.04** — Add heading and scene-selection options.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-028.05** — Preserve existing Markdown/plain-text export.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-028.06** — Improve PDF layout configuration.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Export uses a captured document state.
- Unsaved content and omissions are clearly identified.
- Source documents are never modified.
- Existing files require overwrite confirmation.
- PDF output is tested for pagination and layout.

- [ ] **TASK-028.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-028.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-029 — Add writing-goal history viewer
**Priority:** Low · **Parent status:** open

- [ ] **TASK-029.01** — Display daily writing-goal history.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-029.02** — Show progress by date and scope.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-029.03** — Explain counting and local-date semantics.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-029.04** — Preserve pause/reset behavior.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-029.05** — Allow users to remove locally stored progress.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Historical values remain consistent with the tracker.
- Removing progress does not affect manuscript text.
- Approximate counts are not presented as exact analytics.

### TASK-030 — Improve character profile navigation
**Priority:** Low · **Parent status:** partial

- [?] **TASK-030.01** — Review Story and Background field organization.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-030.02** — Improve scrolling and grouping.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-030.03** — Ensure usability in small windows.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-030.04** — Add navigation to related scenes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-030.05** — Preserve directed relationships and existing profile data.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Every field remains keyboard-accessible.
- Existing values round-trip unchanged.
- Navigating away does not discard unsaved edits.

- [ ] **TASK-030.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-030.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-031 — Improve automatic language detection
**Priority:** Low · **Parent status:** complete

- [x] **TASK-031.01** — Evaluate current script and common-word detection.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-031.02** — Create a multilingual test corpus.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-031.03** — Improve handling of short and ambiguous text.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-031.04** — Preserve explicit language overrides.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-031.05** — Avoid unreliable confident classifications.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Evidence: existing NFC/script/common-word detector and 43-case multilingual
corpus verified. Offline language_detection.py reports 43/43 matches versus
29/43 for the explicit always-Auto baseline; zero unsupported confident guesses
on this curated corpus. Prompt overrides verified across all cases for both
English/Ukrainian. This is regression evidence, not real-world accuracy.
V2 native UI/catalog checks N/A: no UI or translated strings changed.

**Parent acceptance gate (all must pass):**
- Detection performance is measured against a baseline.
- Ambiguous input falls back safely.
- English and Ukrainian behavior does not regress.

- [x] **TASK-031.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [x] **TASK-031.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-032 — Complete Ukrainian interface localization
**Priority:** High · **Parent status:** partial

- [?] **TASK-032.01** — Audit all UI strings.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-032.02** — Migrate untranslated strings into Qt translation mechanisms.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-032.03** — Complete Ukrainian Qt Linguist catalogs.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-032.04** — Include dialogs, errors, confirmations, and status messages.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-032.05** — Preserve placeholders and formatting.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- All supported UI workflows have Ukrainian translations.
- No unintended English fallback remains in the audited scope.
- Document content and AI prompts are not translated implicitly.

- [ ] **TASK-032.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-032.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-033 — Add automated localization validation
**Priority:** High · **Parent status:** complete

- [x] **TASK-033.01** — Add translation completeness checks.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-033.02** — Validate placeholder parity.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-033.03** — Detect missing or malformed translations.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-033.04** — Integrate checks into the developer workflow.
  Added localization CI on pushes/PRs/manual runs: catalog validation, explicit
  extraction coverage and existing regression tests. Local commands pass; the
  first hosted run remains to be observed after an authorized push.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-033.05** — Document extraction, validation, and compilation.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Verification: 14 localization regressions pass, including CLI failures for
unfinished/invalid catalogs, placeholders, plurals and missing extracted entries.
All 897 marked UI sources are covered; temporary English/Ukrainian compilation
passes (28/903 entries). README documents extraction/validation/compilation;
CI invokes the same tools. Hosted CI execution is unobserved until push.
V2 native UI checks are N/A: this task adds validation tooling, no UI behavior;
release asset updates and native localization audit remain TASK-032/TASK-034.

**Parent acceptance gate (all must pass):**
- Invalid placeholders cause validation failure.
- Missing translations are reported clearly.
- Checks can run locally and in CI.

- [x] **TASK-033.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [x] **TASK-033.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-034 — Perform accessibility audit and fixes
**Priority:** Medium · **Parent status:** partial

- [?] **TASK-034.01** — Audit keyboard-only workflows.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-034.02** — Check accessible names and descriptions.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-034.03** — Review focus order and modal dialogs.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-034.04** — Verify behavior under system palettes.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-034.05** — Test with screen readers on supported platforms.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [?] **TASK-034.06** — Fix identified barriers.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Core workflows are keyboard-accessible.
- Accessible controls expose meaningful names.
- Automated tests cover testable accessibility behavior.
- Manual verification results and limitations are documented.

- [ ] **TASK-034.V1** — Reconcile implementation with the parent acceptance criteria and record which numbered subtasks are already satisfied.  
  **Done when:** evidence includes test names, remaining gaps, and platform-specific verification needs.
- [ ] **TASK-034.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-035 — Evaluate and implement selected interface extensions
**Priority:** Low · **Parent status:** complete (evaluation only; extensions deferred)

- [x] **TASK-035.01** — Optional toolbar for common actions.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-035.02** — User-selectable light/dark appearance override.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-035.03** — Additional interface languages.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-035.04** — Additional writing/spellcheck languages.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [x] **TASK-035.05** — Alternative AI providers.  
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Each extension has a documented scope and design decision.
- Existing local-first behavior is preserved.
- New providers are not enabled without explicit privacy and configuration decisions.
- No optional extension is implemented solely because it appears in older specifications.
- [ ] Implementation satisfies acceptance criteria.
- [ ] Relevant tests have been added or updated.
- [ ] Existing tests pass.
- [ ] No unrelated functionality has regressed.
- [ ] Existing user data remains compatible.
- [ ] UI remains responsive.
- [ ] English and Ukrainian translations are updated where applicable.
- [ ] Documentation reflects implemented behavior.
- [ ] Manual verification requirements are documented.
- [ ] Remaining limitations are recorded.

## Cross-cutting execution priorities

1. **Safety first:** TASK-005 and TASK-007 share the unresolved cross-process overwrite race; implement a defined coordination guarantee before declaring either complete.
2. **Memory/performance:** TASK-001 and TASK-006 need measured bounds and repeated GUI benchmarks; do not truncate Qt undo silently.
3. **Recovery and revision safety:** TASK-008–TASK-011 require failure-mode tests before new UI polish.
4. **Verify already-built UI:** TASK-012–TASK-028, TASK-030–TASK-034 have substantial documented implementation; avoid rebuilding features. Focus on remaining acceptance and native/localization checks.
5. **Deferred scope:** TASK-035 evaluation is complete; toolbar/theme/additional providers or languages are not authorized implementation work.

## Completion record template

For each atomic ticket record: date, commit/diff, relevant files, test command and result, manual verification (OS/Qt), updated documentation/translations, residual risk, and parent acceptance impact.

## Source notes

- `IMPLEMENTATION_PROGRESS.md` provides per-task progress and test evidence; its snapshots differ in time and should not be read as a single current test run.
- `README.md` describes shipped behavior; `UNIMPLEMENTED_FEATURES.md` records remaining limitations and optional candidates.
- `README.uk.md` contains some older status claims; prefer the current English README when they disagree.
- This is a task decomposition and reconciliation plan, not proof of the current repository state.
