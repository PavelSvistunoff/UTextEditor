# UTextEditor — open tasks

Only unfinished work is listed. Inspect existing code and tests before changing it; historical results live in [docs/](docs/) and [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md). Follow [AGENTS.md](AGENTS.md) and the [Clean Code rules](docs/clean-code-codex.md).

**Workflow:** Pick 1–4 related tickets from one parent; preserve dirty text, undo, project IDs, file/transaction safety and AI consent/stale guards. Run focused tests, then the full offline suite when practical (`QT_QPA_PLATFORM=offscreen python -m pytest`); for translations use [README instructions](README.md#interface-localization). Record actual results, changed files and remaining blockers in the checkpoint. `[~]` = partial; `[ ]` = open. Do not claim native verification from offscreen tests.

**Order:** Finish TASK-032 localization → TASK-027.03 and TASK-030.03 native latency/keyboard work → TASK-034 accessibility → remaining `.V2` checks. The independent-writer save race is tracked separately in [save coordination](docs/save-coordination.md), not fixed by these tickets.

## Partially completed subtasks

- [~] **TASK-016.05** — Confirm Ctrl+Tab / Ctrl+Shift+Tab work on native Linux/macOS with no conflicts, including keyboard and assistive technology; offscreen tests already pass. [Evidence](docs/tab-navigation-verification.md)
- [~] **TASK-027.03** — Measure Markdown preview capture/render/HTML installation and timer gaps on small, 1M and oversized Unicode documents; verify stale cancellation and native typing responsiveness. [Evidence](docs/markdown-preview-verification.md)
- [~] **TASK-030.03** — In a narrow native window, traverse all character fields, save/cancel and return from a linked scene; retain exact staged values. [Evidence](docs/character-profile-verification.md)
- [~] **TASK-032.01** — Inventory untranslated UI strings, including dynamic service errors; identify each owning widget and reproducible path.
- [~] **TASK-032.02** — Move inventoried visible strings to the correct Qt translation context; preserve placeholders/IDs and test Ukrainian runtime behavior.
- [~] **TASK-032.03** — Re-extract sources, validate placeholders/plurals, compile en/uk `.qm` and verify packaged catalogs match fresh builds.
- [~] **TASK-032.04** — Translate typed dialogs/errors/status for invalid UTF-8, binary/missing files, save conflicts, project/export and AI failures without losing diagnostic details or dirty data. [Localization evidence](docs/localization-accessibility-checkpoint.md)
- [~] **TASK-034.01** — Audit native keyboard-only open/save, search, tabs, AI review and dialogs; record OS/Qt and focus.
- [~] **TASK-034.02** — Check accessible names/descriptions and spoken labels; add focused regressions for defects.
- [~] **TASK-034.03** — Check dialog initial/return focus, Tab order, Enter/Esc and cancellation; fix/retest issues.
- [~] **TASK-034.04** — Verify native light/dark/high-contrast palettes, focus and readable disabled/error/ghost text; capture evidence.
- [ ] **TASK-034.05** — Test core workflows with Orca (Linux) or VoiceOver (macOS); record actual speech, not offscreen substitutes.
- [~] **TASK-034.06** — Fix reproduced barriers, add regressions and repeat native tests; keep unverifiable cases blocked. [Accessibility evidence](docs/localization-accessibility-checkpoint.md)

## Native acceptance gates

Each `.V2` requires **real** Linux/macOS GUI testing: record OS/Qt, keyboard/focus/assistive-technology observations where applicable, packaged Ukrainian behavior, and a link to evidence. Without that environment, report **BLOCKED (native)** and leave the box open. These checks verify existing features; they are **not** instructions to reimplement them.

- [ ] **TASK-012.V2** (High) — Search dirty Ukrainian/emoji scene and note, activate with Down/Enter, then edit the source; verify correct match, stale rejection and unchanged project files. [Search evidence](docs/project-search-verification.md)
- [ ] **TASK-013.V2** (High) — Quick Open duplicate titles/aliases by keyboard; preserve dirty tabs and handle vanished targets. [Quick Open](docs/quick-open-verification.md)
- [ ] **TASK-015.V2** (Medium) — Open linked note/associated scene and return to character profile; preserve staged edits and avoid creating relationships. [Related navigation](docs/related-navigation-verification.md)
- [ ] **TASK-016.V2** (Medium) — Next/previous native tab shortcuts and Open Tabs picker; Cancel closing a dirty tab without data loss or shortcut conflicts. [Tab navigation](docs/tab-navigation-verification.md)
- [ ] **TASK-017.V2** (Medium) — Reopen existing tab via Recent Files, handle missing path, clear recents; preserve unsaved buffers. [Recent files](docs/recent-files-verification.md)
- [ ] **TASK-018.V2** (Medium) — Navigate Project/AI menus by keyboard; verify action reachability, disabled explanations and no shortcut collisions. [Menus](docs/menu-organization-verification.md)
- [ ] **TASK-019.V2** (Low) — Back/Forward through scene/search/note; remove/relink a target and verify safe skipping without changing dirty buffers. [History](docs/navigation-history-verification.md)
- [ ] **TASK-020.V2** (Medium) — Find/Replace Unicode, case/whole-word and narrow-window focus; verify zero matches and replacement undo. [Find/Replace tests](tests/test_find_replace.py)
- [ ] **TASK-021.V2** (Medium) — Navigate spelling suggestions with arrows/Space; Cancel/Apply, reject stale suggestions, undo and check spoken labels. [Spellcheck](docs/spelling-review-verification.md)
- [ ] **TASK-022.V2** (High) — Inspect captured AI completion context/destination, exclude notes and Cancel before sending; verify disclosure and stale guards. [AI context](docs/completion-context-verification.md)
- [ ] **TASK-023.V2** (Medium) — Navigate duplicate-title translation review; Cancel with project unchanged, check explicit all-or-nothing Apply and stable IDs. [Translation](docs/translation-review-verification.md)
- [ ] **TASK-024.V2** (Medium) — Toggle selected Auto-writer drafts; Cancel changes nothing, Apply only confirmed non-stale batch. [Draft review](docs/auto-writer-review-verification.md)
- [ ] **TASK-025.V2** (Low) — Review provisional streaming text, Cancel safely and insert final output only after acceptance; non-streaming still works. [Streaming](docs/streaming-preview-verification.md)
- [ ] **TASK-026.V2** (Low) — Check long/multiline/mid-line/narrow inline completions and normal Tab fallback; typing and cursor remain correct. [Inline completion](docs/inline-completion-verification.md)
- [ ] **TASK-027.V2** (Medium) — Refresh read-only Markdown preview for dirty Unicode/oversized text without losing focus, editing text or freezing UI. [Preview](docs/markdown-preview-verification.md)
- [ ] **TASK-028.V2** (Medium) — Check captured text-export preview, PDF paper/heading/scene options, native pagination and overwrite Cancel; source stays unchanged. [Export](docs/export-verification.md)
- [ ] **TASK-030.V2** (Low) — Tab through all profile fields in narrow window; follow a scene and return with staged edits intact. [Profiles](docs/character-profile-verification.md)
- [ ] **TASK-032.V2** (High) — Run packaged Ukrainian UI across menus/dialogs/status/error paths; record English fallbacks, preserve manuscript/AI prompt text. [Localization](docs/localization-accessibility-checkpoint.md)
- [ ] **TASK-034.V2** (Medium) — Complete native keyboard, screen-reader and system-palette matrix; document spoken output and unresolved issues. [Accessibility](docs/localization-accessibility-checkpoint.md)
