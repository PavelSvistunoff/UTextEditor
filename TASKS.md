# UTextEditor — active task backlog

> This file tracks unfinished work only. Completed tasks and subtasks are removed after verification; historical evidence is in `IMPLEMENTATION_PROGRESS.md`, the linked verification documents and Git history. Parent acceptance gates remain until the parent is complete. Partial status does not mean its acceptance criteria are satisfied.

## Working agreement

By default, implement one logical batch of **1–4 closely related atomic subtasks within one parent TASK** per Codex run, following `AGENTS.md` → “Logical task batches and continuation”. For high-risk changes, use a smaller batch (often one subtask). Do not automatically implement the entire backlog or unrelated parent tasks. Mark each subtask complete only when its own acceptance criteria pass; checkpoint unfinished work.

- Execute **one bounded logical batch of 1–4 closely related atomic subtasks within one parent TASK** per Codex run unless explicitly asked otherwise. For high-risk changes, prefer one subtask. Follow `AGENTS.md` → “Logical task batches and continuation”; do not automatically move to another parent TASK.
- Before implementation inspect the current code, README, tests and working-tree diff; do not overwrite unrelated work.
- Each subtask must produce one independently reviewable change, a focused test (or documented reason), and evidence of verification.
- For UI changes update English/Ukrainian source strings; compiled catalog and native verification are separate subtasks.
- Preserve unsaved content, transactionality, backward compatibility, and offline editing without Ollama.
- Run focused tests, then `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q` when practical; check `git diff --check`.
- States: `[~]` implemented partly / verification outstanding, `[ ]` not documented complete, `[?]` requires code-level confirmation. Remove `[x]` entries after recording verified completion and its evidence. Never promote a task merely because UI exists.

## Summary of parent tasks

| Parent | Scope | Documented state |
|---|---|---|
| TASK-001 | Fix writing-goal history memory growth | open |
| TASK-012 | Implement project-wide full-text search | partial |
| TASK-013 | Implement Quick Open | partial |
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
| TASK-030 | Improve character profile navigation | partial |
| TASK-032 | Complete Ukrainian interface localization | partial |
| TASK-034 | Perform accessibility audit and fixes | partial |

## Atomic execution backlog

Each checkbox is a separately executable ticket. Subtasks under a partially implemented parent are **verification / remaining-work candidates**, not assertions that the listed functionality is absent. Confirm existing implementation before writing code.

### TASK-001 — Fix writing-goal history memory growth
**Priority:** High · **Parent status:** open

- [~] **TASK-001.02** — Implement bounded history metadata without breaking word counts.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-001.03** — Preserve correct behavior across undo, redo, pause, and reset.
  Saving to an unused tracking identity now retains checkpoints; same-ID rekeys
  retain matching history. Existing-destination progress and mismatched text
  now form minimum daily counts in transferred checkpoints when the destination
  is not actively tracked. Scope/enable transitions now
  preserve checkpoints, with no new-word credit for inactive edits; bounded
  history and actively tracked identity collisions remain outstanding.
  A direct tracker reproduction confirms rekeying into an active destination
  replaces its tracked text and checkpoints; a per-editor identity design is
  still needed to preserve both histories.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-001.05** — Benchmark realistic long editing sessions.
  History benchmark now accepts command/undo counts and checks branching after
  undo; 100-command smoke and 10,000-command runs passed. The latter retained
  10,001 states and 3,723,574 current Python-traced bytes; no bound established.
  The mixed workload additionally inserts multilingual words at the start and
  adds/removes punctuation; a 10,000-command run verified undo, redo and
  branching, retaining 10,001 states and 2,206,486 Python-traced bytes. It
  remains synthetic and does not establish a memory bound.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- Memory growth is measured and bounded for the supported editing history.
- Undo/redo does not produce incorrect daily counts.
- Existing writing-goal tests pass.
- New stress and regression tests pass.

### TASK-012 — Implement project-wide full-text search
**Priority:** High · **Parent status:** partial

Evidence: [docs/project-search-verification.md](docs/project-search-verification.md).

**Parent acceptance gate (all must pass):**
- Results navigate to the correct document and match.
- Stale matches are not selected incorrectly.
- Unsaved buffers take precedence over disk content.
- Search does not modify project files.
- Large-project and cancellation tests pass.

- [ ] **TASK-012.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-013 — Implement Quick Open
**Priority:** High · **Parent status:** partial

Evidence: [docs/quick-open-verification.md](docs/quick-open-verification.md).

**Parent acceptance gate (all must pass):**
- Duplicate names are distinguishable.
- Deleted items fail gracefully.
- Existing unsaved tabs are preserved.
- Keyboard navigation works.

- [ ] **TASK-013.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-015 — Implement related-item navigation
**Priority:** Medium · **Parent status:** partial

Evidence: [docs/related-navigation-verification.md](docs/related-navigation-verification.md).

**Parent acceptance gate (all must pass):**
- Existing links and associations are reused.
- Navigation does not create new metadata relationships.
- Unsaved changes are never silently discarded.

- [ ] **TASK-015.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-016 — Improve tab navigation
**Priority:** Medium · **Parent status:** partial

Evidence: [docs/tab-navigation-verification.md](docs/tab-navigation-verification.md).

- [~] **TASK-016.05** — Verify native Qt shortcuts.
  Offscreen Ctrl+Tab/Ctrl+Shift+Tab tests pass; actual native OS shortcut and
  assistive-technology verification remains outstanding.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

**Parent acceptance gate (all must pass):**
- No shortcut conflicts exist.
- Closing tabs uses existing unsaved-change handling.
- Tab switching works with keyboard only.

- [ ] **TASK-016.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-017 — Add recent standalone documents
**Priority:** Medium · **Parent status:** partial

Evidence: [docs/recent-files-verification.md](docs/recent-files-verification.md).

**Parent acceptance gate (all must pass):**
- Duplicate tabs are avoided.
- Missing files produce useful feedback.
- Unsaved buffers remain safe.
- Recent-file history can be cleared.

- [ ] **TASK-017.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-018 — Improve menu organization
**Priority:** Medium · **Parent status:** partial

Evidence: [docs/menu-organization-verification.md](docs/menu-organization-verification.md).

**Parent acceptance gate (all must pass):**
- All existing actions remain accessible.
- Keyboard navigation is preserved.
- No shortcut conflicts are introduced.
- Manual accessibility review is documented.

- [ ] **TASK-018.V2** — Complete outstanding translation compilation/native verification where this task changes UI.  
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-019 — Implement navigation history
**Priority:** Low · **Parent status:** partial

Verification evidence and remaining native/catalog gates are recorded in
`docs/navigation-history-verification.md`. Path-resolution failures are skipped
without changing dirty buffers. Parent remains partial for V2.

**Parent acceptance gate (all must pass):**
- Normal typing does not create history entries.
- Unsaved buffers are preserved.
- Removed targets are handled gracefully.

- [ ] **TASK-019.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-020 — Improve Find and Replace
**Priority:** Medium · **Parent status:** partial

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

- [ ] **TASK-020.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-021 — Implement batch spelling and grammar review
**Priority:** Medium · **Parent status:** partial

Typed provider suggestions now receive field/range/length validation before
sorting, matching the JSON safety bounds. Verification evidence is recorded in
`docs/spelling-review-verification.md`; parent remains partial for V2.

**Parent acceptance gate (all must pass):**
- Cancel leaves text unchanged.
- Stale or overlapping suggestions are rejected.
- Model output is validated before application.
- Undo restores the original document.

- [ ] **TASK-021.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-022 — Implement AI context preview and controls
**Priority:** High · **Parent status:** partial

Captured context/provenance, cancellation, note controls and disclosure guards
are verified in `docs/completion-context-verification.md`. Parent remains
partial for native/catalog V2 checks.

**Parent acceptance gate (all must pass):**
- Preview corresponds to the captured request.
- Context changes invalidate stale responses.
- Unassociated characters are not implicitly included.
- No document content is transmitted without required disclosure.

- [ ] **TASK-022.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-023 — Add AI translation batch review
**Priority:** Medium · **Parent status:** partial

Numbered tickets are verified in `docs/translation-review-verification.md`.
Native/catalog checks and the shared independent-writer race remain open;
parent remains partial.

**Parent acceptance gate (all must pass):**
- IDs, paths, links, and line endings are preserved.
- Cancel leaves the project unchanged.
- Apply remains all-or-nothing.
- Translation failures do not partially modify project data.

- [ ] **TASK-023.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-024 — Improve AI scene draft review
**Priority:** Medium · **Parent status:** partial

Numbered tickets verified in `docs/auto-writer-review-verification.md`.
Selected drafts commit together; later drafts are not regenerated after earlier
ones are rejected, and review warns about that dependency. Parent remains
partial for native/catalog checks and shared filesystem limitations.

**Parent acceptance gate (all must pass):**
- Rejected drafts do not modify scenes.
- Accepted changes are explicitly confirmed.
- Stale project state is detected.
- Failed batches do not leave unintended partial changes.

- [ ] **TASK-024.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-025 — Add optional streaming AI previews
**Priority:** Low · **Parent status:** partial

Numbered tickets verified in `docs/streaming-preview-verification.md`; parent
remains partial for native/catalog V2 checks. Cancellation may wait for an
in-flight network read or timeout.

**Parent acceptance gate (all must pass):**
- Partial output never automatically enters the manuscript.
- Final application requires explicit acceptance.
- Cancellation leaves existing content unchanged.
- Non-streaming behavior remains supported.

- [ ] **TASK-025.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-026 — Improve inline completion display
**Priority:** Low · **Parent status:** partial

Investigation retains a single-line ghost with safe rejection instead of
adding a popup; evidence/design tradeoff is in
`docs/inline-completion-verification.md`. Block-end detection now avoids a
whole-document copy. Parent remains partial for native/catalog V2 checks.

**Parent acceptance gate (all must pass):**
- Normal typing is never blocked.
- Suggestions never silently modify text.
- Cursor and selection behavior remain correct.
- Small-window and multiline cases are tested.

- [ ] **TASK-026.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-027 — Implement Markdown preview
**Priority:** Medium · **Parent status:** partial

- [~] **TASK-027.03** — Update preview when appropriate without blocking typing.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Bounded-prefix/background-render/stale-result tests pass; .03 remains partial
for representative native GUI latency and bounded HTML installation timings.
`docs/markdown-preview-verification.md` records evidence and limits.

**Parent acceptance gate (all must pass):**
- Preview reflects current text.
- Preview does not modify manuscript content.
- Large documents do not freeze the UI.
- Feature works without Ollama.

- [ ] **TASK-027.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-028 — Improve manuscript export and PDF settings
**Priority:** Medium · **Parent status:** partial

Markdown/plain-text export now offers an optional captured preview with explicit
Export/Cancel and bounded display. This is not a PDF page preview. Existing
PDF paper/title/heading/selection controls are verified in
`docs/export-verification.md`; native/catalog V2 remains open.

**Parent acceptance gate (all must pass):**
- Export uses a captured document state.
- Unsaved content and omissions are clearly identified.
- Source documents are never modified.
- Existing files require overwrite confirmation.
- PDF output is tested for pagination and layout.

- [ ] **TASK-028.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-030 — Improve character profile navigation
**Priority:** Low · **Parent status:** partial

- [~] **TASK-030.03** — Ensure usability in small windows.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Saving now retains exact captured values for untouched fields, avoiding
whitespace normalization and lossy reparsing of multiline/delimited values.
`docs/character-profile-verification.md` records named tests. .03 remains
partial for all-field native keyboard/focus review in small windows; V2 open.

**Parent acceptance gate (all must pass):**
- Every field remains keyboard-accessible.
- Existing values round-trip unchanged.
- Navigating away does not discard unsaved edits.

- [ ] **TASK-030.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-032 — Complete Ukrainian interface localization
**Priority:** High · **Parent status:** partial

- [~] **TASK-032.01** — Audit all UI strings.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-032.02** — Migrate untranslated strings into Qt translation mechanisms.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-032.03** — Complete Ukrainian Qt Linguist catalogs.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-032.04** — Include dialogs, errors, confirmations, and status messages.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Source extraction, placeholder checks and temporary compilation pass, including
new export-preview strings. Automated literal candidates were reviewed; raw
service errors and release/native workflows remain incomplete. Evidence and
limits are in `docs/localization-accessibility-checkpoint.md`.

**Parent acceptance gate (all must pass):**
- All supported UI workflows have Ukrainian translations.
- No unintended English fallback remains in the audited scope.
- Document content and AI prompts are not translated implicitly.

- [ ] **TASK-032.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

### TASK-034 — Perform accessibility audit and fixes
**Priority:** Medium · **Parent status:** partial

- [~] **TASK-034.01** — Audit keyboard-only workflows.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-034.02** — Check accessible names and descriptions.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-034.03** — Review focus order and modal dialogs.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-034.04** — Verify behavior under system palettes.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [ ] **TASK-034.05** — Test with screen readers on supported platforms.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.
- [~] **TASK-034.06** — Fix identified barriers.
  **Done when:** implementation or existing behavior is demonstrated by a focused test/review, with no unrelated changes.

Offscreen keyboard/name/focus/palette evidence and outstanding manual coverage
are recorded in `docs/localization-accessibility-checkpoint.md`. No native
screen-reader audit was performed; numbered tickets and parent remain open
or partial as indicated.

**Parent acceptance gate (all must pass):**
- Core workflows are keyboard-accessible.
- Accessible controls expose meaningful names.
- Automated tests cover testable accessibility behavior.
- Manual verification results and limitations are documented.

- [ ] **TASK-034.V2** — Complete outstanding translation compilation/native verification where this task changes UI.
  **Done when:** release catalog and native keyboard/accessibility checks are recorded, or marked N/A with reason.

## Completion checklist

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

1. **Memory:** TASK-001 needs measured bounds; do not truncate Qt undo silently.
2. **Verify already-built UI:** the remaining navigation, AI review, preview and localization tasks have substantial documented implementation; focus on outstanding acceptance and native checks.
3. **Deferred scope:** toolbar, theme overrides, additional providers and languages remain deferred; see `UNIMPLEMENTED_FEATURES.md`.

## Completion record template

For each atomic ticket record: date, commit/diff, relevant files, test command and result, manual verification (OS/Qt), updated documentation/translations, residual risk, and parent acceptance impact.

## Source notes

- `IMPLEMENTATION_PROGRESS.md` provides per-task progress and test evidence; its snapshots differ in time and should not be read as a single current test run.
- `README.md` describes shipped behavior; `UNIMPLEMENTED_FEATURES.md` records remaining limitations and optional candidates.
- `README.uk.md` contains some older status claims; prefer the current English README when they disagree.
- This is a task decomposition and reconciliation plan, not proof of the current repository state.
