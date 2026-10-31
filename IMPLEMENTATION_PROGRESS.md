
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
  responsiveness and compiled localization remain outstanding.
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
  mark complete. Full offline suite: 535 passed, 2 skipped.
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
  counting and replace-all can still process large texts on the GUI thread;
  broader performance work remains. Do not mark complete until verified. Full
  offline suite: 594 passed, 2 skipped.
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
  outstanding. Full offline suite: 489 passed, 2 skipped.
- **TASK-024 — in progress:** after generation, Auto-writer presents a
  navigable, read-only per-scene review with individual selection. It warns
  that later drafts can depend on rejected drafts, rechecks open project
  buffers and applies selected scenes through the existing transaction.
  Tests cover selection, cancellation, stale edits and preview navigation.
  Compiled Ukrainian strings and native accessibility review remain
  outstanding. Full offline suite: 492 passed, 2 skipped.
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
  evaluation is still needed. Full offline suite: 567 passed, 2 skipped.
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
- **TASK-033 audit extension:** `tools/audit_ui_strings.py` reports likely
  unmarked literals and f-strings in selected Qt UI calls, with an optional
  nonzero exit for findings and explicit parse-error handling. A current scan
  reports 148 candidates requiring human review; this heuristic neither
  covers every API nor proves each candidate is user-visible. Catalog
  compilation and the broader audit remain outstanding. Full offline suite:
  596 passed, 2 skipped.
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
  disclosure. Further AI workflows still need auditing. Full offline suite:
  610 passed, 2 skipped.
- **TASK-034 — in progress:** the spelling and Auto-writer review lists now
  expose keyboard-selection instructions through their accessibility
  descriptions. Offscreen tests inspect the Qt accessible interface and use
  arrow and Space keys to select and reject items. Native keyboard, screen
  reader and system-palette audits across core workflows, as well as compiled
  translations, remain outstanding. Do not mark complete. Full offline suite:
  541 passed, 2 skipped.
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
