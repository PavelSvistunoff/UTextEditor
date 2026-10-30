# Remaining features and known limitations

This inventory compares the repository's Markdown documents with the current
implementation. `README.md` is the source of truth for current product scope;
`SPEC.md` and the later sections of `README.uk.md` also describe older
requirements and future ideas. Items below distinguish incomplete current
requirements from optional future work. They are not promises to implement
every candidate. Completed workflows are described in `README.md`.

The review also covered `AGENTS.md` (development instructions) and
`codex_run.md` (command examples); neither defines a separate product feature.

## Code-review findings

The following are unfixed findings from a code and offline-test review. Severity
is an estimate of impact, not proof of how often the issue occurs. The existing
315-test suite passed in the review environment; the reproductions below use
temporary projects or in-memory objects and do not modify the user's documents.

### Confirmed defects

1. **Medium — writing-goal history metadata grows during long sessions.**
   The tracker keeps one current document copy and a fingerprint per reachable
   state. Consecutive edits merged by Qt into one undo command now share one
   endpoint, and a cleared Qt undo stack releases unreachable states. For a
   synthetic 3,000-character typing session starting with 2,400 characters,
   Python's `tracemalloc` measured about 510 KB retained before compaction and
   6 KB after (3,001 versus 2 states; 0.88 versus 0.69 seconds). This measures
   Python allocations in the tracker, not Qt memory or process RSS. Separate
   Qt undo commands still each require a state, so metadata remains unbounded.
   Qt offers no per-command pruning for its native text undo stack; a complete
   solution must preserve counts without silently discarding supported undo.

### Risks requiring further verification

- **Save conflict check versus replacement:** standalone saves, project text,
  and project manifests recheck disk contents after staging. Separate-process
  tests detect edits made during staging. A separate-process edit injected
  immediately after the final check was nevertheless overwritten by atomic
  replacement, confirming a residual race. Investigate platform-appropriate
  coordination; a check alone is not a cross-process lock. See
  `app/document/file_manager.py` and `app/project/service.py`.
- **Large-document UI latency:** goal tracking, match counts, and some cursor
  conversions inspect or copy document text on the GUI thread. The user-visible
  latency threshold has not been measured. Profile representative documents
  before selecting an incremental implementation.

### Review coverage and verification limits

The review traced document save/recovery, project paths and mutations,
translation and Auto-writer, character context and profiles, AI requests and
validation, settings, search, writing goals, localization, and the UI worker
pattern. The test baseline was
`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`
(315 passed). The original reproductions were run with `.venv/bin/python` in
temporary or in-memory state. No
live Ollama, real multi-process race, screen-reader, or platform-specific GUI
session was exercised, and this review does not prove other paths defect-free.

## Current behavior that falls short of documented requirements


## Project and revision workflows

- **Recovery diagnosis:** recovery supports restore, inspection/comparison,
  project relocation, discard, and defer. Repair and diagnosis for partial or
  corrupt recovery sets remain limited.
- **Revision management:** scheduled snapshots, deletion, and restore with a
  preview are not available. Comparisons cover scenes and reference notes,
  but not all chapter, link, and project-structure changes.
- **Large documents and encodings:** files are read into memory as a whole;
  the editor supports UTF-8 only, and encoding and line-ending choices are not
  selectable in the status bar. Detection of binary files beyond embedded NULs
  is also not implemented.

## Writing and language tools

- **Batch spellcheck review:** spelling and grammar suggestions are presented
  per finding; there is no dedicated batch review workflow.
- **Language detection:** automatic language choice uses local script and
  common-word signals, leaving ambiguous or short text to the model.
- **Project-wide search:** literal, case-sensitive scene and note text search
  is available with bounded results and per-document size limits. Broader
  matching options and larger-file support remain future work.
- **Markdown preview:** Markdown export is available, but the Markdown preview
  suggested in `SPEC.md` §22 and `README.uk.md` §32 is not implemented.
- **Additional languages:** writing/spellcheck language choices are Auto,
  English, and Ukrainian. More languages are a future candidate, not a current
  requirement (`SPEC.md` §15).
- **Inline completion limitations:** mid-line and multiline suggestions and suggestions too
  wide for the available viewport are rejected rather than displayed. The
  specification permits this safe fallback; a readable alternative is a
  possible future improvement (`SPEC.md` §12).
- **Per-scene AI draft review:** prompt generation has an explicit review
  dialog, and Auto-writer shows live drafts after prior confirmation. It does
  not provide a separate accept/reject decision for each generated scene before
  its successful batch is applied. More granular proposed-edit review is a
  future candidate (`SPEC.md` §22 and `README.uk.md` §32).

## Interface localization

- **Complete UI translation:** English source text and Ukrainian Qt Linguist
  catalogs are available for the main menus, project navigation, settings,
  find/replace, and selected character, analysis, generation, writing-goal,
  and Auto-writer dialogs. Many MainWindow prompts, error paths, and less-used
  dialogs still fall back to English and need migration and translation.
- **Catalog audit tooling:** extraction and compilation are documented, but a
  dedicated automated check for missing translations and placeholder parity
  across all UI catalogs is not yet part of the developer workflow.

## Navigation assessment and suggestions

The app already has a project tree with context actions, a character filter,
tabbed documents, active-document Find, character-name scene search, linked
notes, and recent projects. The following ideas extend those workflows; they
are proposals except where explicitly identified as a confirmed defect. Priorities
and effort are relative estimates.

### Make destinations easier to find

4. **Extend project text search** — medium priority. The persistent search
   panel searches scenes and notes including unsaved buffers and reports files
   it cannot read. Searches are literal and case-sensitive, limited to 1,000
   matches and 4 MiB per document. Additional matching options and larger-file
   support remain future work.
7. **Navigate between related items** — medium priority, medium effort. Build
   on existing note links, scene associations, and character scene search with
   accessible lists that open a linked item or associated scene directly, and
   provide a way back. Clearly distinguish an explicit scene association from
   a text mention; do not infer new relationships or change project metadata.
   Keep unsaved character-profile edits safe when navigating away.

### Reduce navigation friction

8. **Verify open-tab navigation on native platforms** — small effort. Qt's
   next/previous-tab shortcuts and the searchable open-tab list are available;
   manual native-platform shortcut verification remains outstanding.
10. **Improve menu discoverability** — medium priority, medium effort. Review
    the long Project and AI menus with real usage scenarios; consider grouped
    submenus or a searchable command picker while retaining existing actions
    and shortcuts. Show why context-dependent actions are unavailable and
    avoid adding conflicting shortcuts. Validate the grouping with keyboard and
    screen-reader users instead of moving actions solely for cosmetic reasons.
11. **Add navigation history and return-to-writing** — lower priority, medium
    effort. Record a bounded, session-only back/forward history of explicit
    scene, note, and search-result jumps, including cursor position where safe.
    Skip removed or stale targets with clear feedback and preserve unsaved
    buffers. Do not treat ordinary typing or every cursor move as a history
    entry.
12. **Improve find controls and focus** — lower priority, small/medium effort.
    Consider distinct Find and Replace focus targets, optional matching modes,
    and predictable focus return on close. Retain current literal,
    case-sensitive defaults, match counts, and undo behavior; test keyboard
    navigation, Unicode, zero matches, and small windows.

All navigation changes should work without Ollama, be translated into the
supported interface languages, preserve the editor's current text and selection
unless navigation explicitly requires a change, and have offscreen Qt tests plus
manual keyboard and accessibility checks. The proposals are not claims that every workflow
has been manually usability-tested.

## Prioritized upgrade proposals

These are recommendations derived from the product goals and current workflows,
not confirmed defects or commitments. Effort and priority are relative estimates;
they need design and validation before scheduling. The existing gaps above remain
the authoritative description of what is missing today.

### Optional streaming previews

Ollama requests are currently non-streaming. A token-by-token preview would
require separate provider and worker changes. Partial output must remain
provisional, bounded in memory, and outside the manuscript until explicitly
accepted; cancellation and stale-result checks would still apply.

### High priority

1. **Review AI context before it is sent** (medium effort). Project-scene
   completion already uses bounded associated characters and reference notes,
   while Auto-writer and analysis have confirmation flows. Offer an accessible
   summary of the destination, included material, and truncation, with an
   option to exclude reference notes or disable automatic project context.
   Acceptance: the preview matches the captured request, unsaved buffers are
   identified, and changing the selection invalidates stale results. Preserve
   scene association boundaries and do not expose other characters implicitly.
   This complements the first-use disclosure gap above; it adds UI complexity
   and must avoid interrupting every keystroke.
2. **Complete external file conflict protection** (medium/high effort).
   The review flow shows the saved base, current disk version, and open buffer,
   with reload, save elsewhere, or a reviewed merge. The disk is checked again
   after review and before replacement, but an independent process can still
   change it between the final check and replacement. A supported coordination
   guarantee and cross-platform verification remain necessary before claiming
   that conflicts cannot be overwritten silently.
3. **Make revision snapshots actionable** (high effort). Build on existing
   snapshots and comparisons with previewed, selective restore and confirmed
   deletion, followed by optional scheduling and retention settings. Acceptance:
   show affected files and dirty buffers before restore, create a safety
   snapshot, recheck disk and project state, and either apply transactionally or
   leave the original intact. This depends on the revision-management gap
   above and requires especially careful failure and rollback tests.
4. **Improve recovery triage** (medium/high effort). Extend the existing scan,
   comparison, relocation, and restore choices with per-document status,
   timestamps, readable corruption details, and selective recovery/export of
   valid content. Acceptance: damaged entries remain available for diagnosis;
   no repair or discard occurs without explicit action, and canonical files
   changed on disk are never overwritten silently. Partial or corrupt snapshots
   may not contain enough data to recover; the UI must say so.

### Medium priority

5. **Extend project-wide search** (medium/high effort). Add matching options
   and investigate larger-file support. Project-wide replacement would need a
   separate preview and transactional design.
6. **Review translations before applying a batch** (high effort). Translation
   already snapshots and applies only after all fields succeed. Add a review of
   original and translated titles and text, with per-item navigation and an
   explicit final apply or cancel. Acceptance: preserve IDs, paths, links, and
   line endings, recheck the captured project state, and retain all-or-nothing
   behavior. Selective application and translation of character metadata would
   require separate decisions about consistency and scope.
7. **Batch spelling review** (medium effort). Build on validated individual
   suggestions with a navigable list, explanations, and explicit selection of
   corrections. Acceptance: reject stale or overlapping ranges, group accepted
   edits into an undoable operation, and leave text untouched on cancel. Model
   output remains untrusted; this is not automatic correction.
8. **Portable project backup and validation** (medium/high effort). Project
   files are already portable YAML and UTF-8, and snapshots live inside the
   project. Offer a user-selected backup destination and a read-only integrity
   report for missing files, invalid paths, and unreadable snapshots. Acceptance:
   explain whether open unsaved buffers and revisions are included, never
   overwrite without confirmation, and test restoring a backup in a separate
   directory. This must not imply that recovery snapshots are a complete backup.
9. **Improve manuscript export and PDF options** (medium effort). Existing
   Markdown/plain-text export supports scene subsets; PDF currently uses a
   fixed A5 layout. Consider a preview and choices for page size, title-page
   metadata, headings, and scene selection. Acceptance: use a captured buffer
   state, show omissions and unsaved content, preserve source files, and retain
   explicit replacement confirmation. Page-numbered contents and stable
   pagination need dedicated PDF testing across platforms.
10. **Accessibility and localization audit** (medium effort). Extend the
    current keyboard-accessible menus and partial Ukrainian catalogs by testing
    complete workflows with keyboard navigation, accessible names, screen
    readers, and system palettes. Include translation completeness and
    placeholder checks in automated tooling. Acceptance: report unresolved
    strings and barriers without translating manuscript data or AI prompts.
    Screen-reader and platform behavior also needs manual verification.

### Lower priority and exploratory

11. **Find controls and navigation** (small/medium effort). Active-document
    find currently uses literal, case-sensitive matching. Add optional
    case-insensitive or whole-word matching while keeping existing defaults.
    Acceptance: counts, navigation, replacement,
    Unicode handling, and undo agree under each chosen mode. Regular expressions
    would need separate safeguards and clear error reporting.
12. **Writing-goal history** (medium effort). Daily progress is stored locally
    and already accounts for undo/redo. A local history view could show past
    days and scope without changing manuscript text. Acceptance: explain the
    local-date and counting semantics, honor pause/reset, and provide a clear
    way to remove local progress. Avoid presenting approximate inserted-word
    counts as exact writing analytics.
13. **Measure large-project responsiveness** (medium effort). Establish
    repeatable benchmarks for opening, editing, search, word counts, snapshots,
    and AI context construction before optimizing. Then address measured
    bottlenecks with bounded memory and cancellable background work. Acceptance:
    record representative input sizes and compare results without weakening
    conflict detection or correctness. Very large-file editing may require a
    broader design change rather than a simple optimization.
14. **Optional interface and provider extensions** (design decision). The
    older Ukrainian document suggests a toolbar, a dark-mode choice, and other
    AI providers. A toolbar could expose common actions; an appearance override
    would extend the current system-palette behavior. Other providers require
    explicit privacy, configuration, and compatibility decisions. None is
    necessary for the current local-first scope; cloud services are outside it.
15. **Make character profiles easier to navigate** (small/medium effort).
    The profile dialog groups many editable fields into Story and Background
    tabs. Consider scrollable sections, clearer field grouping, and navigation
    from a character's scene history to the related scene. Acceptance: all
    fields remain reachable at small window sizes and by keyboard, existing
    values and directed relationships round-trip unchanged, and opening a
    scene never discards unsaved profile edits. Verify with manual accessibility
    testing before treating layout concerns as confirmed defects.

These gaps are independent of basic standalone editing, which remains usable
without a project or a running Ollama server.
