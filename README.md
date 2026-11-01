# UTextEditor

UTextEditor is a native desktop text editor for people who want a simple place to write and edit plain text, with optional Ollama AI assistance. It is inspired by GEdit and built with Python and Qt. The editor remains usable when AI is disabled or Ollama is unavailable.

The project aims to keep writing fast and predictable: documents stay under the user's control, AI suggestions are visible before use, and normal editing does not depend on a network service. AI requests use an Ollama server on localhost by default. The host is configurable and may be remote, so document text sent to it may leave the device. No separate cloud AI provider is configured.

## Project goals

- Provide a dependable, lightweight writing tool, with a long-term focus on helping novelists manage and write manuscripts.
- Keep multiple documents and their modified state separate in tabs.
- Make common editing, search, and file operations easy to reach.
- Offer optional Ollama completion and spelling assistance without freezing the interface.
- Keep AI integration replaceable and separate from the UI.
- Prefer explicit user control over generated or corrected text.
- Keep manuscript content portable and under the author's control.

## Current status

The editor supports standalone text files and a local project workspace. Implemented features include:

- Native PySide6 desktop window with File, Edit, Search, View, Project, Writing, AI, and Settings menus. Project and AI actions are grouped by workflow; recovery is available in File.
- New, open, save, and Save As for UTF-8 text files; unsaved-change prompts on close.
- File > Open Recent File lists up to ten recently opened or saved standalone files. It stores paths only, reuses open tabs, reports missing or unverifiable paths, and can clear the list independently of recent projects. A path-verification failure during opening leaves existing tabs and unsaved text intact.
- File reads and writes run in background workers; saves replace files atomically where supported.
- File > Review External Changes compares the saved base, disk version, and open buffer. It offers an editable merge proposal, reload, or Save Elsewhere. Staging a merge does not itself save it; the disk is checked again before staging and on the next save.
- Multiple document tabs with per-document text, dirty state, and modified-tab markers.
- Qt's next/previous-tab shortcuts switch open documents; View > Open Tabs provides a searchable list with modified indicators and file or project context.
- Project creation/opening in a navigation dock, with an Open Recent Project menu and a persisted list of the ten most recently opened projects. Projects use stable-ID chapters, scenes, and separate reference notes stored as ordinary UTF-8 files. The project tree preserves its expansion and selection during refresh and provides context-menu shortcuts for creating characters, chapters, scenes, and notes, and for common open, rename, move, duplicate, link, analyze, and remove actions.
- The Project menu groups movement, links, revisions, export, and project AI into submenus; action descriptions explain when a project or selection is required.
- Project > Reveal Current Document in Project locates the open scene or reference note in the project tree, expanding its ancestors while preserving other branches. Standalone documents report that they are not bound to the project.
- Open Linked Item is available for both scenes and reference notes, allowing navigation along existing links without changing them; open tabs retain unsaved text, and the link is checked again after selection. A character's project-tree menu and profile can open explicitly associated scenes separately from the name-and-alias mention search. Returning to the profile preserves staged edits; saving detects changes to that profile or its relationships, and a failed save keeps the edits available.
- Project scene import, title rename, duplication/removal, ordering and chapter moves, note types and links, and live scene/chapter/project word counts.
- Structured character profiles in the project tree, with identity, background, personality, motivations, prioritized goals, knowledge/secret categories, and arc notes. Use Project > New Character and the tree filter, which works in both interface languages; activating a profile or choosing Open in its context menu opens the editor. The Relationships tab adds, edits, and removes directed relationships; its changes are saved together with the profile or discarded on Cancel. The context menu also supports directed relationship management, duplicate/remove, name-and-alias scene search, and YAML profile import/export. Imports receive a new stable ID and do not import source-project relationships or scene associations. Scene associations record presence, development notes, and structured state changes with evidence; profiles show the ordered history and a current-state projection, and scene AI context includes only the associated character's scene-linked changes. Profile IDs and scene references remain stable across renames; removing a profile also removes its relationships and scene associations after confirmation. Opening older projects does not rewrite them.
- In a character profile, **Fill Empty Fields with AI** sends the current profile fields to the configured Ollama destination after confirmation, allowing up to five minutes for the response. Review the proposed values before filling empty fields; save the profile to keep them. Existing fields and relationships are not replaced. Requests and responses appear in AI diagnostics.
- A character profile can also suggest scene development from an open scene explicitly associated with that character. After confirmation, the configured AI receives the profile and a bounded scene excerpt. Each proposed arc field includes an exact scene quotation; select individual suggestions to stage them in the profile form, then save the profile to keep them. Rejecting or cancelling leaves it unchanged, and results are discarded if the captured context changes.
- The Story and Background and personality sections of a character profile scroll independently so their fields remain reachable in smaller windows. Saving preserves untouched profile values exactly, including whitespace and structured entries that contain line breaks or delimiters; editing another field does not normalize them.
- View > Navigation Back and Navigation Forward revisit explicit project-document and search jumps during the current session. Positions are restored only while the original tab remains open and unchanged; stale, removed, relinked, or unverifiable paths are skipped.
- The character profile's Portrait tab can add, preview, replace, or remove a PNG or JPEG portrait. Images are limited to 256 KB and 2048 pixels per side. The portrait is saved with the profile and embedded in the project and character YAML export; Cancel discards staged changes. Older application versions that do not understand portraits may reject projects containing them.
- Optional AI project setup starts from an editable story-planning template. Suggest proposes clearly marked ideas for gaps; the author reviews and edits them before requesting an outline. Outline planning receives bounded motivations, goals, conflicts, and directed relationships for relevant profiles. The optional autonomous Auto-pilot can append a bounded new plan, draft its scenes, and create character reference notes after explicit confirmation; it never overwrites existing files and applies no batch if generation fails or is cancelled.
- Whole-project Auto-writer can draft empty scenes or refine every scene using the project outline, reference notes, characters explicitly associated with each target scene, optional writing instructions, and the configured Ollama model. It confirms context use and the destination, snapshots the complete project before generation, shows each completed draft immediately in a live progress window, and allows up to five minutes per model request. Progress from an older request is ignored. After generation, review and select drafts to apply together; later drafts may depend on earlier drafts, including rejected ones. The selected changes use a single transaction.
- Project scene and note saves compare against the last-read disk contents. An already-open file is bound to a project only if its captured disk version matches the project read; otherwise it remains a standalone tab with conflict protection. Autosave is configurable (two-second idle interval by default); failures leave documents dirty and report non-blocking feedback.
- Optional daily writing goals support active-document words, project manuscript words, or newly inserted words. New-word progress is local-date based and undo/redo aware; edits made while paused add no words, and pausing or resetting preserves tracked undo checkpoints without changing manuscript text. Undo tracking keeps one current text copy per open document and fingerprints for earlier states, combining consecutive edits that Qt groups into one undo command. Invalid saved goal data produces a warning and falls back to defaults without overwriting the data at startup.
- Local recovery snapshots every 30 seconds while documents are dirty and at orderly shutdown. Startup offers restoring the latest snapshots or a selected readable snapshot, inspect/compare, locate a moved project, discard recovery data, or defer. Snapshots with invalid or timezone-free capture timestamps are reported for diagnosis rather than automatically restored; valid snapshots are ordered by capture time. Project snapshots identify their scene or note, including after relocation; older snapshots use their original project-relative path. If an item cannot be identified or its file changed, recovered text opens separately without overwriting the original.
- Explicit Markdown/plain-text manuscript export uses current scene buffers, selectable scene subsets, configurable headings and separators, UTF-8 encoding, and LF line endings. It confirms inclusion of unsaved edits in selected scenes; reference notes and unselected scenes are excluded. The optional Preview before exporting review shows the captured Markdown/plain-text output before an explicit Export or Cancel. It displays at most 65,536 characters with a notice when truncated; Export writes the entire captured version. Changing the project or an open scene discards the pending preview. Replacing a destination requires confirmation. Export and PDF compilation reject project manuscript, reference-note, and manifest files as destinations.
- View > Markdown Preview shows a read-only rendering of the active buffer, including unsaved edits, without loading external resources or opening links. For documents larger than 65,536 Qt text units, it labels and renders only the beginning.
- Project > Export > Compile Book as PDF creates a book on A5, A4, or Letter paper, with an editable title and optional author on the title page, contents, ordered chapters and scenes, indented left-aligned prose paragraphs, page numbers, and black text on a white page regardless of the system theme. Choose which scenes to include and whether to show chapter and scene headings in the contents and manuscript. It uses open scene buffers (including unsaved edits after confirmation), excludes reference notes, and never changes project files.
- Named local revision snapshots capture current project structure and in-memory scene/note text without clearing dirty state. Project > Revisions > Review Revision Snapshots lists valid local snapshots, reports unreadable ones, previews a selected snapshot in pages, allows deletion of a selected snapshot after confirmation, and compares two snapshots for project titles; chapter additions, removals, ordering and titles; scene additions, removals, ordering, chapter, title, path and text; reference-note additions, removals, title, type, path and text; and directed link additions and removals. Renames show both titles and the item's stable ID.
- Opt-in scene summaries and continuity checks send only explicitly selected scenes/notes and, for continuity, the scene's explicitly associated characters after displaying their names and the configured Ollama destination; bounded requests run in workers and stale results are dropped. Continuity findings include confidence, scene and associated-character IDs, a source quotation, and a suggested review question. The app rejects malformed results and quotations outside the captured source excerpts; findings appear in a separate review panel without editing files. An empty findings list does not prove consistency. Outline planning receives compact character motivations and goals.
- Project > Project AI > Translate Project to Ukrainian/English translates the project title, chapter/scene/reference-note titles, and all scene and note text using the configured Ollama model. It confirms the destination, snapshots the original project, and offers a side-by-side review with stable IDs to distinguish duplicate titles before applying the complete translation. It supports cancellation, preserves IDs/paths/order/links and line endings, and commits the result only if all translations succeed and the project has not changed. Each run is limited to 500 translatable fields of up to 32,000 characters each; exceeding a limit aborts without applying partial translations.
- Distraction-free mode from View or `Ctrl+Shift+F`; `Esc` exits after first dismissing any inline completion, and an accessible status-bar action is always available while the mode is active.
- Standard editing through Qt, including undo, redo, clipboard actions, and select all. Edit > Text Formatting provides case conversion, line indent/outdent, trailing-whitespace cleanup, and “Like in the book,” which indents the first line of each paragraph while preserving blank lines and line endings. Transformations apply to selected text/lines or the whole document and are undoable. “Format Whole Document…” lets the author choose one operation to apply explicitly across the entire document.
- Find, previous/next navigation with live match counts, replace-current, and undoable replace-all. Literal case-sensitive matching is the default; case-insensitive and whole-word options are available. Counts with many matches update in batches so the interface can respond while counting. A search with no matches preserves the cursor and selection.
- Search > Search Project Text searches scenes and reference notes, including open unsaved buffers, and lists matching locations in a persistent panel. From the search field, Down moves focus to the results; arrow keys select a result and Enter opens it. Results open only if their captured text still matches; unreadable, likely binary and non-regular files and documents over the 4 MiB search limit are reported in a scrollable status area, with a count when more than 100 file errors occur. Searches can be cancelled and do not change project content. Per-file reads, captured open-buffer text, results and diagnostics are bounded. Buffers omitted because the total capture limit is reached are reported and never searched from stale disk content instead.
- Search > Quick Open (`Ctrl+P`/`Cmd+P`) filters project scenes, chapters, reference notes, characters, and character aliases. It shows item type, chapter context, and stable IDs; selecting a chapter reveals it in the project tree.
- Status display for UTF-8, detected line-ending style (LF, CRLF, or CR), cursor line and column, and AI connection state.
- Ollama connection using `http://localhost:11434` and `gemma4:12b` by default; host and model can be changed in Settings > AI Settings, including to a remote host.
- Before sending document or project context to a destination for the first time, the app shows a non-modal disclosure of the host and data categories and asks for consent. Consent is saved for that host only, without document content; a different host requires a new decision. Declining suppresses repeated automatic prompts for that host during the session, and an explicit AI action can ask again. If an explicit action was waiting for consent, invoke it again after allowing; automatic completion and spellcheck retry with the current editor state.
- Inline completions shown as non-destructive ghost text. `Tab` accepts a suggestion and `Esc` dismisses it. Suggestions are discarded when the relevant text, cursor, selection, or active document changes, or when resizing leaves insufficient room to display them; they are shown only at the end of a text block. This visibility check uses the Qt cursor without copying the whole document.
- Debounced completion requests with bounded context, background workers, and stale-result checks. When completing a project scene, requests also include its explicitly associated characters and up to 10,000 characters of project reference notes (using open unsaved note buffers when available). Closed notes are checked for changes before sending and after generation. AI Settings can exclude project context from automatic completions; manually requested completions still include it. AI > Completion Reference Notes can exclude individual notes for the current project session. AI > Review Completion Context captures and displays the context and destination before an explicit request, including a notice when character details are limited; Cancel sends nothing. This material is sent to the configured Ollama destination and appears in AI diagnostics.
- Automatic writing-language selection identifies clear English and Ukrainian signals, including canonically decomposed text; short, mixed-script, or otherwise uncertain text falls back to Auto. Digits and repeated words alone do not establish a language. Cyrillic text without Ukrainian-specific letters remains Auto because shared words alone are ambiguous. Explicit language choices are preserved.
- AI Settings optionally enables a bounded streaming preview for prompt-based text generation. The preview is provisional; a completed draft still requires explicit insertion. Cancelling or changing the captured editor state discards it. Cancellation of a network read may wait for data or the connection timeout.
- AI-assisted spelling and grammar suggestions with underlines, context-menu replace/ignore actions, response validation, and undo support for edits. AI > Review Spelling and Grammar lets you select current findings and apply them as one undoable edit. Both typed provider results and JSON results reject malformed ranges and fields; reviews retain at most 200 non-overlapping findings, with replacements limited to 2,000 characters and explanations to 1,000. A slow spellcheck runs at most one provider call at a time; repeated requests retain only the latest unchanged pending document state.
- In spelling and Auto-writer reviews, arrow keys navigate the lists and Space includes or excludes an item; the lists expose these instructions to accessibility tools.
- Prompt-based text generation runs in the background, can be cancelled, and appears in a review dialog; generated text is inserted at the captured cursor or over the captured selection only after explicit acceptance. Results for a changed document or another active tab are discarded, and the cancel action follows the current request when requests overlap.
- Settings are grouped into Connection, Writing, AI assistance, and Advanced prompts tabs, with a reset-to-defaults option; the Connection tab can test the configured Ollama host/model and suggests how to install a missing model.
- The interface language can be set from Settings > Application Language or from AI Settings, choosing System default, English, or Українська. The menu shows the saved choice; selecting a language stores its stable code, reports save errors, and explains that the change takes effect after restarting. System locale matching recognizes regional language tags and falls back to English. The selection is stored separately from the writing/spellcheck language. Qt Linguist catalogs currently cover the main menus, project navigation and creation prompts, settings, find/replace, recovery comparison labels, and common character, analysis, generation, writing-goal, and Auto-writer dialogs; untranslated interface text falls back to English.
- Editor background, text, and selection colors follow the system palette.
- Application preferences are saved as YAML in the user's configuration directory (`settings.yaml`); existing `settings.json` preferences are loaded for compatibility.
- An in-memory Ollama diagnostics window for the current session. It retains at most 100 recent events, truncates oversized events, and can be cleared; diagnostics may contain manuscript text.
- The status bar's AI activity control opens a non-modal task panel with separate states and elapsed times for AI requests. It shows real batch progress where available, offers cancellation and safe retries where supported, and links to Auto-writer and translation progress. In-flight network requests finish before cancellation is complete. The session-only activity history stores task metadata rather than prompts or model output.
- Unit tests using fake providers and mocks; tests do not require a running Ollama server.

### Known gaps and behavior to be aware of

- Automatic spellcheck now only presents validated underlines. Corrections require an explicit context-menu action and are undoable.
- `Auto` uses local script and common-word signals, and ambiguous or short text remains `Auto` for the model to infer.
- The [large-file evaluation](docs/large-file-evaluation.md) records measured costs and the absence of an enforced safe size limit. Files are currently read into memory as a whole; very large files may still use substantial memory even though reads and writes run off the GUI thread.
- Writing-goal undo metadata can still grow with the number of separate undo commands in a long editing session; it is not yet bounded.
- Changing writing-goal scope or disabling/re-enabling a goal preserves its undo checkpoints; intervening edits add no new-word credit. Undo or redo to an unknown checkpoint does not count restored text as new writing, but cannot reconstruct its earlier contribution to the daily count.
- The app currently supports UTF-8 files only. Standalone and project text reads reject NUL, non-whitespace ASCII controls and DEL as likely binary input. Tabs, line breaks, vertical tabs, form feeds and Unicode prose remain accepted. This heuristic does not detect every binary format.
- The status bar reports encoding and line ending, but these are not currently user-selectable. The [encoding-support investigation](docs/encoding-support.md) records the proposed standalone-file approach and compatibility requirements; it does not add legacy encoding support.
- The UI is minimal and has no toolbar. Recent standalone files and projects are listed separately.
- Recovery handles the supported snapshot cases without overwriting changed canonical files, but full repair and diagnosis workflows for partial or corrupt recovery data remain incomplete.
- Scheduled revision snapshots and revision-history restore controls are not yet available. Revision comparisons report reference-note reordering among shared notes without treating additions or removals as moves. Revision comparisons also flag added, removed or changed character profiles, directed relationships and scene-character associations by stable ID. Character, relationship and scene-association comparisons show affected manifest field names and read-only JSON diffs of captured values, including added and removed records; not all project-structure changes are covered.
- Localization is an initial rollout, not yet a complete translation of every dialog and error/status path. Untranslated strings remain usable in English; the current catalogs cover common workflows listed above.

### Project format and local data

A project uses a version-1 UTF-8 YAML manifest named `utexteditor.yaml`. It stores `format_version`, a stable `project_id`, the title, ordered chapters and scenes, ungrouped scenes, reference-note IDs/types/titles, project-relative paths, note links, and optional structured character profiles, directed relationships, and scene associations. Character metadata is inline YAML; scene and reference-note contents remain separate files under `manuscript/` and `notes/`. Empty character/relationship collections and empty scene-association lists are omitted when serialized. Opening a legacy project does not itself rewrite its manifest. Project metadata writes are atomic and reject a manifest whose contents changed externally since the project was opened. Unknown fields and unsupported versions are rejected rather than rewritten.

Word counts treat a word as a run of Unicode letters or digits, with internal apostrophes or dash variants allowed when surrounded by word characters. Missing or unreadable scene files produce an explicitly incomplete count. Reference notes are excluded from manuscript totals and exports.

Recovery data is stored locally in the operating system's UTextEditor application-data directory (on macOS, `~/Library/Application Support/UTextEditor/recovery`). It does not replace canonical files. Snapshot writes and cleanup run in order in the background, and orderly shutdown waits for queued recovery work. The scan reports unfinished snapshot writes, which may still be in progress, and directory-listing or directory-resolution failures without hiding readable snapshots in other directories. Recovery inspection includes captured text for untitled documents and missing canonical files. Recovery comparisons label diffs that exceed the 6,000-character display limit. If the recovery root cannot be listed, the scan reports that failure for diagnosis. Symbolic-link snapshot files and snapshots with empty or NUL-containing file paths are reported as invalid. Automatic cleanup preserves unreadable or damaged snapshots and unfinished writes for diagnosis; an explicit discard can remove them. Recovery is best-effort: edits since the latest snapshot and failures outside the captured snapshot interval may not be recoverable, and it is not a substitute for backups. Revision previews label reference notes with their captured titles and stable IDs, falling back to IDs for legacy metadata. Revision history reports directory-listing failures and symbolic-link snapshots as diagnostics. Revision history orders valid timezone-aware capture timestamps by instant and reports malformed timestamps as invalid entries. Named revision snapshots are stored in `.utexteditor/revisions` inside the project and should be included in the author's own backup when they need to retain them; snapshot retention management is not yet exposed in the UI.

The recovery chooser's details show each readable snapshot's capture timestamp and the canonical file's status at inspection: unchanged from the saved disk version, changed, missing, newly appeared, unreadable, or unknown. Untitled snapshots are identified separately. Diagnosis runs in the scan worker and hashes regular files in chunks; an unreadable canonical file does not prevent recovering its snapshot. These statuses are advisory; restoring checks the disk again.

Revision history and the before/after comparison both order snapshots by their capture instant, including timestamps with different timezone offsets.

Save conflict checks run both before and after staging standalone files, project text, and project manifests. Standalone, project text, and project manifest writes are serialized with one another within the application process. This does not lock out independent processes: an edit between the final check and atomic replacement can still be overwritten. The [save-coordination evaluation](docs/save-coordination.md) records why advisory locking alone does not close that race.

Exports use UTF-8 without a byte-order mark and normalize line endings to LF. Export and snapshot creation do not save source documents or clear their dirty state.

Saving to a new writing-goal document identity preserves undo/redo checkpoints when that identity is not actively tracked; existing destination progress provides a minimum daily count across those checkpoints. Writing-goal configuration and per-document daily progress are stored locally in `writing-goals.json` beside the application settings. The local system date defines the daily boundary; changing the timezone does not delete progress recorded under other dates.

## Install and run

Requires Python 3.12 or newer. Install the project and its test extra in a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e '.[test]'
```

Run the editor with:

```bash
utexteditor
# or
python -m app.main
```

To use AI, install and start [Ollama](https://ollama.com/) separately, then make sure the configured model is available. The default model is `gemma4:12b`. The editor can still be used as a text editor without Ollama.

Run the test suite with:

```bash
pytest
```

The normal suite is offline. To run the separate live AI smoke test against the
Ollama host and model saved in your application settings, start Ollama and run:

```bash
QT_QPA_PLATFORM=offscreen UTEXTEDITOR_LIVE_AI=1 python -m pytest -v tests/test_live_ollama_e2e.py
```

The tests send short synthetic prompts to that configured destination, exercise
generation and the review dialog through the desktop worker, and check that
accepted insertions and selected-text replacements can be undone. They use a temporary copy of settings and do
not open or modify your documents. It can take several minutes while the model
loads; an unavailable server or model causes the explicitly enabled test to fail.

## Technology and design

- Python 3.12+
- PySide6 / Qt 6
- Ollama for AI requests, using a configurable host that defaults to localhost
- pytest

The application separates document state and file handling (`app/document/`), AI services and the `AIProvider` abstraction (`app/ai/`), persistent settings (`app/settings/`), and Qt UI (`app/ui/`). The Ollama HTTP client is isolated in `app/ai/ollama_client.py`. GUI widgets do not make direct Ollama calls; the UI dispatches AI work to background workers and receives results on the GUI thread.

AI completions are suggestions and do not enter the document until accepted. Model responses are untrusted: spellcheck output is parsed and checked against the captured document snapshot before it is used. No separate cloud AI provider is configured; a remote Ollama host can nevertheless receive document text.

## Interface localization

The interface uses Qt Linguist source catalogs in `translations/` and compiled Qt `.qm` catalogs packaged under `app/resources/translations/`. `system`, `en`, and `uk` are the persisted interface-language values. System mode uses Qt's preferred UI locales, matches regional variants by language, and falls back to English. The daily writing goal selector and revision comparison statuses and change labels support Ukrainian. Language selection does not change manuscript language, writing instructions, project content, filenames, or AI prompts. Interface changes take effect after restart.

When adding or changing translatable UI text, use `self.tr("English source text")` in the owning widget. Extract and compile catalogs with the PySide6 Qt Linguist tools:

```bash
pyside6-lupdate app/ui/*.py -ts translations/utexteditor_uk.ts
pyside6-lrelease translations/utexteditor_en.ts -qm app/resources/translations/utexteditor_en.qm
pyside6-lrelease translations/utexteditor_uk.ts -qm app/resources/translations/utexteditor_uk.qm
```

Validate existing catalog entries with `python tools/check_translations.py translations/utexteditor_uk.ts`. To audit marked source strings, extract them to a temporary TS file with `pyside6-lupdate app/ui/*.py -ts /tmp/utexteditor-extracted.ts`, then pass `--reference /tmp/utexteditor-extracted.ts` to the checker. It exits nonzero for missing, duplicate, malformed or unfinished translations and placeholder or plural-form errors, including plural flags that disagree with the extracted source, so the same commands can run in CI. `python tools/audit_ui_strings.py` separately reports likely unmarked literals in selected Qt calls; these are candidates for human review and do not cover every UI string. Add `--fail-on-findings` to make candidates fail the command. For messages belonging to another widget, use its class's `tr` method so extraction and runtime use the same context. The English catalog intentionally contains only selected strings and numerus forms.

The Localization validation GitHub Actions workflow runs on pushes and pull requests. It validates the Ukrainian source catalog, extracts UI strings to check coverage, and runs the localization regression tests on Python 3.12 with offscreen Qt. The same checker and pytest commands can be run locally.

The small English catalog supplies Qt numerus forms; ordinary English text remains the source fallback. Ukrainian uses Qt numerus forms, including the three common plural categories. Keep placeholders such as `%1`, `%2`, and `%n` aligned between source and all translation forms. Contexts use stable widget class names. Proper names, shortcuts, filenames, project data, and AI prompt instructions are not translated.

Recurring glossary: project — проєкт; chapter — розділ; scene — сцена; character — персонаж; reference note — довідкова нотатка; revision snapshot — знімок редакції; recovery — відновлення; inline completion — продовження тексту; continuity check — перевірка узгодженості; Auto-writer — автоматичне написання; writing goal — ціль письма.

Writing-goal status refresh counts buffer words only for the active goal scope and skips those scans for paused or disabled goals. Writing-goal insertion counting scans tokens within the changed text span plus boundary context; unchanged text is compared in chunks to locate that span. Clearing either Qt undo/redo stack also releases the corresponding unreachable goal checkpoints, even when the text does not change; checkpoints in the other direction remain available.

For an offline language-detection evaluation, run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/language_detection.py`. It compares the curated regression corpus with an always-Auto baseline and reports unsupported confident guesses; these results are not real-world accuracy estimates.

For performance investigation, run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/completion_context.py` for the completion-context microbenchmark, `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/editor_responsiveness.py` for editor operation median/maximum timings, ready Qt callback delays and peak process memory (where supported; `--sizes 100000 1000000 --repetitions 10` controls the workload; reads, opens and saves remain single samples; saves verify buffer bytes), or `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/writing_goal_history.py` for a synthetic editing, undo/redo and branch session. Pass `--commands 10000 --undo 1000` to increase the history length; allocation tracing can make long runs slow. These measurements are diagnostic, not portable pass/fail thresholds. The [Qt callback latency measurements](docs/gui-latency-evaluation.md) describe the event-loop probe and its limits.

## Product direction

The project-workspace, character reference, Ollama AI planning and review, manuscript export, and named revision-snapshot foundations are implemented. The next useful increments are the remaining gaps listed in `UNIMPLEMENTED_FEATURES.md`: broader revision management, recovery diagnosis, richer project search, and complete interface translation. These are candidates, not promises or descriptions of current behavior. Any future AI or project features must preserve privacy, portability, and the author's control; avoid proprietary project formats or a separate cloud AI provider without a separate product decision.

## Development expectations

- Keep the application a native desktop app.
- Keep UI, document management, and AI integration separated.
- Keep network and AI work off the Qt GUI thread; discard stale results.
- Never require a live Ollama instance for unit tests; use fakes or mocks.
- Update tests and this README when behavior changes.
- Avoid unrelated changes and unnecessary dependencies.

## REFERENCES
specification: [SPEC.md](SPEC.md)
unimplemented features: [UNIMPLEMENTED_FEATURES.md](UNIMPLEMENTED_FEATURES.md)
agents and architecture: [AGENTS.md](AGENTS.md)
