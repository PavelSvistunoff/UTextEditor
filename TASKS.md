# UTextEditor — executable Codex backlog

> **Unfinished work only.** `[ ]` does not mean a feature is absent: inspect code and tests before changing it. `README.md` is the current product guide; `UNIMPLEMENTED_FEATURES.md` describes risks and optional proposals, not authorized implementation work.

## Codex run contract

For each implementation ticket, follow the [Clean Code discipline](AGENTS.md#clean-code-discipline-for-codex) and its [practical review checklist](docs/clean-code-codex.md#codex-completion-review-apply-to-each-selected-ticket). Apply it only to new/touched code; preserve acceptance and safety guarantees.

1. Inspect `git status --short`, [AGENTS.md](AGENTS.md), the newest [checkpoint](IMPLEMENTATION_PROGRESS.md), one selected parent and exact subtask IDs, then source and related tests.
2. Execute one high-risk ticket or 1–4 related subtasks **within one parent** per bounded batch. An explicitly authorized whole-backlog run can continue in additional **verified, checkpointed batches**.
3. Write success, failure, stale-state and undo/data-safety checks before coding. Verify what already exists; never implement a duplicate merely to satisfy an open checkbox.
4. Run focused tests and the full offline suite when practical. For UI changes, validate translations and packaged catalogs. Never claim a native OS or screen-reader check that was not performed.
5. Report `COMPLETE`, `CHECKPOINT` or `BLOCKED` **per ticket**, parent status separately, and exact commands/results. Prepend a short resume checkpoint. Remove a verified ticket only after preserving evidence.
6. Preserve dirty buffers, Qt undo, stable project IDs, local-first editing, AI consent/generation guards and transaction rollback. Leave unrelated files and user changes alone.

**Statuses:** `[ ]` open; `[~]` partial; `[?]` needs inspection. `.V2` is a **native verification gate**, not a request to rewrite built features. Without real Linux/macOS GUI and necessary assistive technologies, record `BLOCKED (native environment)` and leave it open. Green offscreen Qt tests alone never close native acceptance.

## Recommended execution sequence

| Priority | Ticket(s) | Runnable outcome |
| --- | --- | --- |
| 1 | TASK-032.01, .02, .04 | Audit/translate concrete dynamic UI and service errors, test contexts/placeholders |
| 2 | TASK-032.03 | Re-extract, validate and compile en/uk catalogs; prove packaged parity |
| 3 | TASK-027.03, TASK-030.03 | Measure Markdown preview native latency; complete narrow profile keyboard test |
| 4 | TASK-034 and remaining .V2 | Record real native keyboard, palette, screen-reader and Ukrainian runtime evidence |

**Dependencies:** TASK-032 source/catalog work precedes localized `.V2` acceptance, TASK-034 coordinates accessibility. The cross-process save race is a separate known limitation in [docs/save-coordination.md](docs/save-coordination.md).

## Standard verification (run only what applies)

```bash
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/check_translations.py translations/utexteditor_uk.ts
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/audit_ui_strings.py
git diff --check
```

For localization extraction/compilation, use the commands in [README.md](README.md#interface-localization). Record actual runs and skips rather than treating this example as evidence.

## Summary of parent tasks

| Parent | Scope | Documented state |
|---|---|---|
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

### TASK-012 — Implement project-wide full-text search
**Priority:** High · **Parent status:** partial

**Inspect first:** `app/project/search.py; tests/test_project_search.py`.

Evidence: [docs/project-search-verification.md](docs/project-search-verification.md).

**Parent acceptance gate (all must pass):**
- Results navigate to the correct document and match.
- Stale matches are not selected incorrectly.
- Unsaved buffers take precedence over disk content.
- Search does not modify project files.
- Large-project and cancellation tests pass.

- [ ] **TASK-012.V2** — Native test: Search unsaved Ukrainian/emoji scene and note, activate result via Down/Enter, then change source and confirm stale selection rejection.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-013 — Implement Quick Open
**Priority:** High · **Parent status:** partial

**Inspect first:** `app/ui/quick_open_dialog.py; tests/test_project_ui.py`.

Evidence: [docs/quick-open-verification.md](docs/quick-open-verification.md).

**Parent acceptance gate (all must pass):**
- Duplicate names are distinguishable.
- Deleted items fail gracefully.
- Existing unsaved tabs are preserved.
- Keyboard navigation works.

- [ ] **TASK-013.V2** — Native test: Quick Open duplicate scene and alias from keyboard without losing a dirty tab.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-015 — Implement related-item navigation
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/character_dialog.py; tests/test_project_ui.py`.

Evidence: [docs/related-navigation-verification.md](docs/related-navigation-verification.md).

**Parent acceptance gate (all must pass):**
- Existing links and associations are reused.
- Navigation does not create new metadata relationships.
- Unsaved changes are never silently discarded.

- [ ] **TASK-015.V2** — Native test: Open linked note and character-associated scene, return to profile with staged edits unchanged.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-016 — Improve tab navigation
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/tab_widget.py; tests/test_editor_widget.py`.

Evidence: [docs/tab-navigation-verification.md](docs/tab-navigation-verification.md).

- [~] **TASK-016.05** — Verify native Qt shortcuts.
  Offscreen Ctrl+Tab/Ctrl+Shift+Tab tests pass; actual native OS shortcut and
  assistive-technology verification remains outstanding.
  **Done when:** Demonstrate this named criterion in a focused regression or reviewed implementation, record failures and limits; no unrelated refactoring.

**Parent acceptance gate (all must pass):**
- No shortcut conflicts exist.
- Closing tabs uses existing unsaved-change handling.
- Tab switching works with keyboard only.

- [ ] **TASK-016.V2** — Native test: Use native next/previous tab shortcuts, Open Tabs picker, and Cancel on dirty-tab close.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-017 — Add recent standalone documents
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/settings/settings.py; tests/test_settings.py`.

Evidence: [docs/recent-files-verification.md](docs/recent-files-verification.md).

**Parent acceptance gate (all must pass):**
- Duplicate tabs are avoided.
- Missing files produce useful feedback.
- Unsaved buffers remain safe.
- Recent-file history can be cleared.

- [ ] **TASK-017.V2** — Native test: Reopen an existing tab from Recent Files, handle a missing path, and clear recents without losing edits.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-018 — Improve menu organization
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/main_window.py; tests/test_project_ui.py`.

Evidence: [docs/menu-organization-verification.md](docs/menu-organization-verification.md).

**Parent acceptance gate (all must pass):**
- All existing actions remain accessible.
- Keyboard navigation is preserved.
- No shortcut conflicts are introduced.
- Manual accessibility review is documented.

- [ ] **TASK-018.V2** — Native test: Traverse Project/AI menus by keyboard and inspect disabled-action explanations and shortcut collisions.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-019 — Implement navigation history
**Priority:** Low · **Parent status:** partial

**Inspect first:** `app/ui/navigation_history.py; tests/test_navigation_history.py`.

Verification evidence and remaining native/catalog gates are recorded in
`docs/navigation-history-verification.md`. Path-resolution failures are skipped
without changing dirty buffers. Parent remains partial for V2.

**Parent acceptance gate (all must pass):**
- Normal typing does not create history entries.
- Unsaved buffers are preserved.
- Removed targets are handled gracefully.

- [ ] **TASK-019.V2** — Native test: Back/Forward through scene, search and note, then remove/relink a destination and confirm safe skipping.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-020 — Improve Find and Replace
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/find_replace.py; tests/test_find_replace.py`.

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

- [ ] **TASK-020.V2** — Native test: Find/Replace Unicode with case/whole-word toggles in a narrow window, check focus and undo.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-021 — Implement batch spelling and grammar review
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/spellcheck_review_dialog.py; tests/test_spellcheck_service.py`.

Typed provider suggestions now receive field/range/length validation before
sorting, matching the JSON safety bounds. Verification evidence is recorded in
`docs/spelling-review-verification.md`; parent remains partial for V2.

**Parent acceptance gate (all must pass):**
- Cancel leaves text unchanged.
- Stale or overlapping suggestions are rejected.
- Model output is validated before application.
- Undo restores the original document.

- [ ] **TASK-021.V2** — Native test: Select spelling suggestions with arrows/Space, cancel/apply, undo and verify spoken labels.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-022 — Implement AI context preview and controls
**Priority:** High · **Parent status:** partial

**Inspect first:** `app/ai/completion_service.py; tests/test_ai_workflows_e2e.py`.

Captured context/provenance, cancellation, note controls and disclosure guards
are verified in `docs/completion-context-verification.md`. Parent remains
partial for native/catalog V2 checks.

**Parent acceptance gate (all must pass):**
- Preview corresponds to the captured request.
- Context changes invalidate stale responses.
- Unassociated characters are not implicitly included.
- No document content is transmitted without required disclosure.

- [ ] **TASK-022.V2** — Native test: Review captured completion context and destination, exclude notes, then cancel without sending.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-023 — Add AI translation batch review
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/project/translation.py; tests/test_project_translation.py`.

Numbered tickets are verified in `docs/translation-review-verification.md`.
Native/catalog checks and the shared independent-writer race remain open;
parent remains partial.

**Parent acceptance gate (all must pass):**
- IDs, paths, links, and line endings are preserved.
- Cancel leaves the project unchanged.
- Apply remains all-or-nothing.
- Translation failures do not partially modify project data.

- [ ] **TASK-023.V2** — Native test: Navigate side-by-side translation with duplicate titles and cancel without modifying the project.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-024 — Improve AI scene draft review
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/project/auto_writer.py; tests/test_ai_workflows_e2e.py`.

Numbered tickets verified in `docs/auto-writer-review-verification.md`.
Selected drafts commit together; later drafts are not regenerated after earlier
ones are rejected, and review warns about that dependency. Parent remains
partial for native/catalog checks and shared filesystem limitations.

**Parent acceptance gate (all must pass):**
- Rejected drafts do not modify scenes.
- Accepted changes are explicitly confirmed.
- Stale project state is detected.
- Failed batches do not leave unintended partial changes.

- [ ] **TASK-024.V2** — Native test: Toggle Auto-writer scene draft selection and verify Cancel versus explicit Apply.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-025 — Add optional streaming AI previews
**Priority:** Low · **Parent status:** partial

**Inspect first:** `app/ai/ollama_client.py; tests/test_ollama_client.py`.

Numbered tickets verified in `docs/streaming-preview-verification.md`; parent
remains partial for native/catalog V2 checks. Cancellation may wait for an
in-flight network read or timeout.

**Parent acceptance gate (all must pass):**
- Partial output never automatically enters the manuscript.
- Final application requires explicit acceptance.
- Cancellation leaves existing content unchanged.
- Non-streaming behavior remains supported.

- [ ] **TASK-025.V2** — Native test: Inspect provisional streaming text, cancel, and verify completed output inserts only on acceptance.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-026 — Improve inline completion display
**Priority:** Low · **Parent status:** partial

**Inspect first:** `app/ui/editor_widget.py; tests/test_editor_widget.py`.

Investigation retains a single-line ghost with safe rejection instead of
adding a popup; evidence/design tradeoff is in
`docs/inline-completion-verification.md`. Block-end detection now avoids a
whole-document copy. Parent remains partial for native/catalog V2 checks.

**Parent acceptance gate (all must pass):**
- Normal typing is never blocked.
- Suggestions never silently modify text.
- Cursor and selection behavior remain correct.
- Small-window and multiline cases are tested.

- [ ] **TASK-026.V2** — Native test: Test long, multiline, mid-line and narrow-window completion and normal Tab fallback.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-027 — Implement Markdown preview
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/markdown_preview.py; tests/test_markdown_preview.py`.

- [~] **TASK-027.03** — Update preview when appropriate without blocking typing.
  **Done when:** Measure capture/render/HTML installation and Qt timer gaps for small, 1M and oversized Unicode documents; exercise stale-result cancellation and native responsiveness.

Bounded-prefix/background-render/stale-result tests pass; .03 remains partial
for representative native GUI latency and bounded HTML installation timings.
`docs/markdown-preview-verification.md` records evidence and limits.

**Parent acceptance gate (all must pass):**
- Preview reflects current text.
- Preview does not modify manuscript content.
- Large documents do not freeze the UI.
- Feature works without Ollama.

- [ ] **TASK-027.V2** — Native test: Update read-only Markdown preview for unsaved Unicode and oversized content without stealing focus.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-028 — Improve manuscript export and PDF settings
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/document/book_compiler.py; tests/test_book_compiler.py`.

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

- [ ] **TASK-028.V2** — Native test: Verify text-export preview, PDF paper/heading/scene choices, overwrite Cancel and native pagination.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-030 — Improve character profile navigation
**Priority:** Low · **Parent status:** partial

**Inspect first:** `app/ui/character_dialog.py; tests/test_project_ui.py`.

- [~] **TASK-030.03** — Ensure usability in small windows.
  **Done when:** On a narrow native window, traverse every profile field, save/cancel and return from an associated scene; assert exact staged values survive.

Saving now retains exact captured values for untouched fields, avoiding
whitespace normalization and lossy reparsing of multiline/delimited values.
`docs/character-profile-verification.md` records named tests. Profile multiline
fields now use Tab for focus traversal; an offscreen narrow-window test visits
all profile fields. .03 remains
partial for all-field native keyboard/focus review in small windows; V2 open.

**Parent acceptance gate (all must pass):**
- Every field remains keyboard-accessible.
- Existing values round-trip unchanged.
- Navigating away does not discard unsaved edits.

- [ ] **TASK-030.V2** — Native test: Tab through all character fields in a narrow window and return from a scene with staged edits intact.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-032 — Complete Ukrainian interface localization
**Priority:** High · **Parent status:** partial

**Inspect first:** `app/ui/, translations/; tests/test_i18n.py, tests/test_translation_validation.py`.

- [~] **TASK-032.01** — Audit all UI strings.
  **Done when:** Inventory visible strings outside the narrow AST heuristic, including dynamically wrapped service errors; attach a reproducible path and owning widget to each finding.
- [~] **TASK-032.02** — Migrate untranslated strings into Qt translation mechanisms.
  **Done when:** Migrate inventoried UI wrappers to the owning tr() context; retain placeholders/IDs and add focused temporary or packaged Ukrainian runtime tests.
- [~] **TASK-032.03** — Complete Ukrainian Qt Linguist catalogs.
  **Done when:** Run source extraction, placeholder/plural validation and both lrelease commands; compare packaged .qm runtime output to fresh compilation and record native gaps.
- [~] **TASK-032.04** — Include dialogs, errors, confirmations, and status messages.
  **Done when:** Reproduce invalid UTF-8, binary, missing-file, save-conflict, project and AI errors; translate typed user-facing categories while retaining diagnostic details.

Source extraction, placeholder checks and release catalog compilation pass;
automated tests compare packaged translations against freshly compiled sources.
Standalone open errors for invalid UTF-8, binary content and missing files are
translated; missing-file diagnostics retain the original system detail and path.
Standalone save conflicts use a translated category for manual and automatic
saves while preserving the original diagnostics and dirty buffer. Invalid project
format/path errors during opening and project changes use shared typed UI
formatting with translated categories and original details. Profile-save failures
now use the same categories and retain staged profile edits for retry. Text/PDF
export failures also share typed project categories and existing source protection.
Character scene-search errors share these categories, with project/generation
staleness rejection covered by packaged Ukrainian tests.
AI generation/completion network failures have packaged Ukrainian runtime coverage,
including stale request/settings rejection and preservation of dirty text/details.
Automated literal candidates were reviewed; other raw service errors and native
workflows remain incomplete. Evidence and limits are in
`docs/localization-accessibility-checkpoint.md`.

**Parent acceptance gate (all must pass):**
- All supported UI workflows have Ukrainian translations.
- No unintended English fallback remains in the audited scope.
- Document content and AI prompts are not translated implicitly.

- [ ] **TASK-032.V2** — Native test: Run packaged Ukrainian UI through menus, dialogs, status and failure paths, recording fallbacks.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

### TASK-034 — Perform accessibility audit and fixes
**Priority:** Medium · **Parent status:** partial

**Inspect first:** `app/ui/; tests/test_review_accessibility.py`.

- [~] **TASK-034.01** — Audit keyboard-only workflows.
  **Done when:** Document native keyboard navigation of open/save, project search, tabs, AI review and dialogs with OS/Qt version and focus outcomes.
- [~] **TASK-034.02** — Check accessible names and descriptions.
  **Done when:** Test accessible names/descriptions and spoken labels for fields, lists, actions and status; add offscreen regressions for confirmed failures.
- [~] **TASK-034.03** — Review focus order and modal dialogs.
  **Done when:** Reproduce initial focus, Tab traversal, Enter/Esc cancellation and return focus for modal and non-modal dialogs; fix and retest failures.
- [~] **TASK-034.04** — Verify behavior under system palettes.
  **Done when:** Record native light/dark/high-contrast palette behavior, focus visibility and readable error/disabled/ghost text with screenshots.
- [ ] **TASK-034.05** — Test with screen readers on supported platforms.
  **Done when:** Test core workflows with Orca (Linux) or VoiceOver (macOS) and record actual spoken output; offscreen tests do not substitute.
- [~] **TASK-034.06** — Fix identified barriers.
  **Done when:** Fix each reproduced barrier, add automated regression and rerun native acceptance; otherwise leave native retest blocked.

Offscreen keyboard/name/focus/palette evidence and outstanding manual coverage
are recorded in `docs/localization-accessibility-checkpoint.md`. No native
screen-reader audit was performed; numbered tickets and parent remain open
or partial as indicated.

**Parent acceptance gate (all must pass):**
- Core workflows are keyboard-accessible.
- Accessible controls expose meaningful names.
- Automated tests cover testable accessibility behavior.
- Manual verification results and limitations are documented.

- [ ] **TASK-034.V2** — Native test: Perform the documented native keyboard, screen-reader and system-palette matrix.
  **Done when:** Record OS, Qt, actual keyboard/focus/screen-reader steps, packaged Ukrainian runtime result and evidence link. Without native GUI: BLOCKED, keep unchecked.

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

1. **Verify already-built UI:** the remaining navigation, AI review, preview and localization tasks have substantial documented implementation; focus on outstanding acceptance and native checks.
2. **Deferred scope:** toolbar, theme overrides, additional providers and languages remain deferred; see `UNIMPLEMENTED_FEATURES.md`.

## Completion record template

For each atomic ticket record: date, commit/diff, relevant files, test command and result, manual verification (OS/Qt), updated documentation/translations, residual risk, and parent acceptance impact.

## Source notes

- [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) points to the latest work and archived evidence.
- [README.md](README.md) records shipped behavior; [UNIMPLEMENTED_FEATURES.md](UNIMPLEMENTED_FEATURES.md) records unapproved options and risks.
- A .V2 script is a planned test, **not** proof of native execution.
