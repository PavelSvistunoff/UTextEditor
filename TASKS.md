# UTextEditor — Codex Implementation Tasks

## General instructions for Codex

For each task:

1. Inspect the existing implementation, `README.md`, `SPEC.md`, and relevant tests.
2. Reuse existing architecture and components wherever possible.
3. Implement the task completely without unrelated refactoring.
4. Preserve backward compatibility and existing user data.
5. Keep all core editing functionality available without Ollama.
6. Add or update automated tests, including offscreen Qt tests for UI changes.
7. Run the relevant tests and the full test suite when practical.
8. Fix regressions introduced by the implementation.
9. Update documentation and English/Ukrainian UI translations.
10. Mark the task complete only when its acceptance criteria pass.

Do not automatically implement all tasks in one execution. Work on one task at a time unless explicitly instructed otherwise.

Use the existing test command:

```bash
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
```

A task requiring manual or platform-specific verification must remain partially complete until that verification is performed.

---

# Phase 3 — Search, navigation, and usability

## TASK-012 — Implement project-wide full-text search
**Priority:** High  
**Effort:** Medium/High  
**Status:** [ ]

- Search scenes, chapters where applicable, and reference notes.
- Include open unsaved document buffers.
- Provide a persistent results panel.
- Display document title, excerpt, and match location.
- Navigate directly to selected results.
- Support cancellation and bounded resource usage.
- Report unreadable files.

**Acceptance criteria:**
- Results navigate to the correct document and match.
- Stale matches are not selected incorrectly.
- Unsaved buffers take precedence over disk content.
- Search does not modify project files.
- Large-project and cancellation tests pass.

## TASK-013 — Implement Quick Open
**Priority:** High  
**Effort:** Medium  
**Status:** [ ]

- Add a keyboard-accessible Quick Open dialog.
- Search scene, chapter, note, and character names.
- Include character aliases.
- Display item type and chapter context.
- Use stable IDs when opening selected items.

**Acceptance criteria:**
- Duplicate names are distinguishable.
- Deleted items fail gracefully.
- Existing unsaved tabs are preserved.
- Keyboard navigation works.

## TASK-014 — Add Reveal in Project
**Priority:** Medium  
**Effort:** Small  
**Status:** [x]

- Add a Reveal in Project action for bound scenes and notes.
- Expand the necessary tree ancestors.
- Select and scroll to the matching project item.
- Preserve unrelated tree expansion state.

**Acceptance criteria:**
- The correct stable ID is selected.
- Standalone and unbound tabs are handled explicitly.
- No manuscript content is modified.

## TASK-015 — Implement related-item navigation
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Navigate between linked notes and associated scenes.
- Navigate from character profiles to related scenes.
- Distinguish explicit associations from text mentions.
- Provide a convenient return path.
- Protect unsaved profile edits.

**Acceptance criteria:**
- Existing links and associations are reused.
- Navigation does not create new metadata relationships.
- Unsaved changes are never silently discarded.

## TASK-016 — Improve tab navigation
**Priority:** Medium  
**Effort:** Small/Medium  
**Status:** [ ]

- Add next/previous-tab navigation.
- Add a searchable list of open tabs.
- Display project context and modified-state indicators.
- Handle duplicate filenames.
- Verify native Qt shortcuts.

**Acceptance criteria:**
- No shortcut conflicts exist.
- Closing tabs uses existing unsaved-change handling.
- Tab switching works with keyboard only.

## TASK-017 — Add recent standalone documents
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Add a recent-file list separate from recent projects.
- Reopen files using existing document-opening logic.
- Handle missing or moved files.
- Add a clear-history action.
- Store paths only, not document content.

**Acceptance criteria:**
- Duplicate tabs are avoided.
- Missing files produce useful feedback.
- Unsaved buffers remain safe.
- Recent-file history can be cleared.

## TASK-018 — Improve menu organization
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Review Project and AI menus.
- Group related actions logically.
- Consider submenus or a command picker.
- Preserve existing actions and shortcuts.
- Explain unavailable context-dependent actions.

**Acceptance criteria:**
- All existing actions remain accessible.
- Keyboard navigation is preserved.
- No shortcut conflicts are introduced.
- Manual accessibility review is documented.

## TASK-019 — Implement navigation history
**Priority:** Low  
**Effort:** Medium  
**Status:** [ ]

- Add bounded Back and Forward navigation history.
- Record explicit scene, note, and search-result jumps.
- Restore cursor position when safe.
- Skip deleted or stale destinations.
- Keep history session-local.

**Acceptance criteria:**
- Normal typing does not create history entries.
- Unsaved buffers are preserved.
- Removed targets are handled gracefully.

## TASK-020 — Improve Find and Replace
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Add optional case-insensitive matching.
- Add optional whole-word matching.
- Improve Find and Replace focus behavior.
- Preserve existing default matching semantics.
- Keep match counts, navigation, and replacement consistent.

**Acceptance criteria:**
- Unicode search behaves correctly.
- Zero-match and small-window cases work.
- Replacements preserve undo behavior.
- Keyboard focus returns predictably.

---

# Phase 4 — Writing assistance and AI workflows

## TASK-021 — Implement batch spelling and grammar review
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Collect validated spelling and grammar findings.
- Present them in a navigable review dialog.
- Show explanations and proposed corrections.
- Allow individual selection and rejection.
- Apply accepted edits as one undoable operation.

**Acceptance criteria:**
- Cancel leaves text unchanged.
- Stale or overlapping suggestions are rejected.
- Model output is validated before application.
- Undo restores the original document.

## TASK-022 — Implement AI context preview and controls
**Priority:** High  
**Effort:** Medium  
**Status:** [ ]

- Show the configured AI destination.
- Summarize included document and project context.
- Identify unsaved buffers and truncation.
- Allow excluding reference notes.
- Allow disabling automatic project context.
- Avoid interrupting every completion request.

**Acceptance criteria:**
- Preview corresponds to the captured request.
- Context changes invalidate stale responses.
- Unassociated characters are not implicitly included.
- No document content is transmitted without required disclosure.

**Dependency:** TASK-003.

## TASK-023 — Add AI translation batch review
**Priority:** Medium  
**Effort:** High  
**Status:** [ ]

- Show original and translated content side by side.
- Include translated titles and text.
- Allow per-item navigation.
- Require explicit Apply or Cancel.
- Revalidate project state before applying.

**Acceptance criteria:**
- IDs, paths, links, and line endings are preserved.
- Cancel leaves the project unchanged.
- Apply remains all-or-nothing.
- Translation failures do not partially modify project data.

## TASK-024 — Improve AI scene draft review
**Priority:** Medium  
**Effort:** High  
**Status:** [ ]

- Add per-scene draft review for Auto-writer output.
- Display generated text separately from committed manuscript content.
- Support accept, reject, and review navigation.
- Define how partial acceptance affects batch consistency.
- Protect existing scene content.

**Acceptance criteria:**
- Rejected drafts do not modify scenes.
- Accepted changes are explicitly confirmed.
- Stale project state is detected.
- Failed batches do not leave unintended partial changes.

## TASK-025 — Add optional streaming AI previews
**Priority:** Low  
**Effort:** High  
**Status:** [ ]

- Add optional Ollama streaming support.
- Update workers to consume streamed output.
- Display provisional tokens incrementally.
- Bound partial-output memory.
- Support cancellation and stale-result rejection.

**Acceptance criteria:**
- Partial output never automatically enters the manuscript.
- Final application requires explicit acceptance.
- Cancellation leaves existing content unchanged.
- Non-streaming behavior remains supported.

## TASK-026 — Improve inline completion display
**Priority:** Low  
**Effort:** Medium  
**Status:** [ ]

- Investigate readable alternatives for long suggestions.
- Consider multiline and mid-line completion previews.
- Handle suggestions exceeding viewport width.
- Preserve explicit acceptance via Tab.
- Retain safe rejection when a suggestion cannot be represented.

**Acceptance criteria:**
- Normal typing is never blocked.
- Suggestions never silently modify text.
- Cursor and selection behavior remain correct.
- Small-window and multiline cases are tested.

---

# Phase 5 — Writing tools, export, and productivity

## TASK-027 — Implement Markdown preview
**Priority:** Medium  
**Effort:** Medium  
**Status:** [ ]

- Add a Markdown preview for the active document.
- Support unsaved buffer content.
- Update preview when appropriate without blocking typing.
- Keep preview read-only.
- Avoid unsafe external-resource loading.

**Acceptance criteria:**
- Preview reflects current text.
- Preview does not modify manuscript content.
- Large documents do not freeze the UI.
- Feature works without Ollama.

## TASK-028 — Improve manuscript export and PDF settings
**Priority:** Medium  
**Effort:** Medium/High  
**Status:** [ ]

- Add export preview.
- Add selectable page sizes.
- Add title-page metadata.
- Add heading and scene-selection options.
- Preserve existing Markdown/plain-text export.
- Improve PDF layout configuration.

**Acceptance criteria:**
- Export uses a captured document state.
- Unsaved content and omissions are clearly identified.
- Source documents are never modified.
- Existing files require overwrite confirmation.
- PDF output is tested for pagination and layout.

## TASK-029 — Add writing-goal history viewer
**Priority:** Low  
**Effort:** Medium  
**Status:** [ ]

- Display daily writing-goal history.
- Show progress by date and scope.
- Explain counting and local-date semantics.
- Preserve pause/reset behavior.
- Allow users to remove locally stored progress.

**Acceptance criteria:**
- Historical values remain consistent with the tracker.
- Removing progress does not affect manuscript text.
- Approximate counts are not presented as exact analytics.

**Dependency:** TASK-001.

## TASK-030 — Improve character profile navigation
**Priority:** Low  
**Effort:** Small/Medium  
**Status:** [ ]

- Review Story and Background field organization.
- Improve scrolling and grouping.
- Ensure usability in small windows.
- Add navigation to related scenes.
- Preserve directed relationships and existing profile data.

**Acceptance criteria:**
- Every field remains keyboard-accessible.
- Existing values round-trip unchanged.
- Navigating away does not discard unsaved edits.

**Dependency:** Coordinate with TASK-015.

## TASK-031 — Improve automatic language detection
**Priority:** Low  
**Effort:** Medium  
**Status:** [ ]

- Evaluate current script and common-word detection.
- Create a multilingual test corpus.
- Improve handling of short and ambiguous text.
- Preserve explicit language overrides.
- Avoid unreliable confident classifications.

**Acceptance criteria:**
- Detection performance is measured against a baseline.
- Ambiguous input falls back safely.
- English and Ukrainian behavior does not regress.

---

# Phase 6 — Localization and accessibility

## TASK-032 — Complete Ukrainian interface localization
**Priority:** High  
**Effort:** Medium/High  
**Status:** [ ]

- Audit all UI strings.
- Migrate untranslated strings into Qt translation mechanisms.
- Complete Ukrainian Qt Linguist catalogs.
- Include dialogs, errors, confirmations, and status messages.
- Preserve placeholders and formatting.

**Acceptance criteria:**
- All supported UI workflows have Ukrainian translations.
- No unintended English fallback remains in the audited scope.
- Document content and AI prompts are not translated implicitly.

## TASK-033 — Add automated localization validation
**Priority:** High  
**Effort:** Medium  
**Status:** [ ]

- Add translation completeness checks.
- Validate placeholder parity.
- Detect missing or malformed translations.
- Integrate checks into the developer workflow.
- Document extraction, validation, and compilation.

**Acceptance criteria:**
- Invalid placeholders cause validation failure.
- Missing translations are reported clearly.
- Checks can run locally and in CI.

## TASK-034 — Perform accessibility audit and fixes
**Priority:** Medium  
**Effort:** Medium/High  
**Status:** [ ]

- Audit keyboard-only workflows.
- Check accessible names and descriptions.
- Review focus order and modal dialogs.
- Verify behavior under system palettes.
- Test with screen readers on supported platforms.
- Fix identified barriers.

**Acceptance criteria:**
- Core workflows are keyboard-accessible.
- Accessible controls expose meaningful names.
- Automated tests cover testable accessibility behavior.
- Manual verification results and limitations are documented.

---

# Phase 7 — Optional extensions

## TASK-035 — Evaluate and implement selected interface extensions
**Priority:** Low  
**Effort:** Design dependent  
**Status:** [x]

Evaluate the following independently before implementation:

- Optional toolbar for common actions.
- User-selectable light/dark appearance override.
- Additional interface languages.
- Additional writing/spellcheck languages.
- Alternative AI providers.

**Acceptance criteria:**
- Each extension has a documented scope and design decision.
- Existing local-first behavior is preserved.
- New providers are not enabled without explicit privacy and configuration decisions.
- No optional extension is implemented solely because it appears in older specifications.

---

# Recommended execution order

Complete tasks in the following order, subject to dependencies and new findings.

**Stage A — Stability and correctness**

TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006

**Stage B — Data integrity**

TASK-007 → TASK-008 → TASK-009 → TASK-010 → TASK-011

**Stage C — Core usability**

TASK-012 → TASK-013 → TASK-014 → TASK-015 → TASK-016 → TASK-017 → TASK-018 → TASK-020

**Stage D — AI and writing tools**

TASK-022 → TASK-021 → TASK-023 → TASK-024 → TASK-025 → TASK-026

**Stage E — Productivity**

TASK-027 → TASK-028 → TASK-029 → TASK-030 → TASK-031 → TASK-019

**Stage F — Localization and accessibility**

TASK-033 → TASK-032 → TASK-034

**Stage G — Optional extensions**

TASK-035

Tasks from different stages may run independently when they do not touch overlapping components.

---

# Completion checklist

Before marking any task complete:

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

A task is complete only when its implementation and required verification are finished. Do not mark partially implemented or unverified work as complete.
