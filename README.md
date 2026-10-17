# UTextEditor

UTextEditor is a native desktop text editor for people who want a simple place to write and edit plain text, with optional local AI assistance. It is inspired by GEdit and built with Python and Qt. The editor remains usable when AI is disabled or Ollama is unavailable.

The project aims to keep writing fast and predictable: documents stay under the user's control, AI suggestions are visible before use, and normal editing does not depend on a network service. AI requests use a local Ollama server by default; document text is not sent to a cloud AI provider.

## Project goals

- Provide a dependable, lightweight writing tool, with a long-term focus on helping novelists manage and write manuscripts.
- Keep multiple documents and their modified state separate in tabs.
- Make common editing, search, and file operations easy to reach.
- Offer optional local completion and spelling assistance without freezing the interface.
- Keep AI integration replaceable and separate from the UI.
- Prefer explicit user control over generated or corrected text.
- Keep manuscript content portable and under the author's control.

## Current status

The editor supports standalone text files and a local project workspace. Implemented features include:

- Native PySide6 desktop window with File, Edit, Search, and AI menus.
- New, open, save, and Save As for UTF-8 text files; unsaved-change prompts on close.
- File reads and writes run in background workers; saves replace files atomically where supported.
- Multiple document tabs with per-document text, dirty state, and modified-tab markers.
- Project creation/opening in a navigation dock, with stable-ID chapters, scenes, and separate reference notes stored as ordinary UTF-8 files. The project tree provides context-menu shortcuts for common create, open, rename, move, duplicate, link, analyze, and remove actions.
- Project scene import, title rename, duplication/removal, ordering and chapter moves, note types and links, and live scene/chapter/project word counts.
- Optional local AI project setup starts from an editable story-planning template. Suggest proposes clearly marked ideas for gaps; the author reviews and edits them before requesting an outline. The optional autonomous Auto-pilot can append a bounded new plan, draft its scenes, and create character reference notes after explicit confirmation; it never overwrites existing files and applies no batch if generation fails or is cancelled.
- Whole-project Auto-writer can draft empty scenes or refine every scene using the project outline, reference notes, optional writing instructions, and configured local model settings. It confirms local context use, snapshots the complete project before generation, shows each completed draft immediately in a live progress window, and allows up to five minutes per local model request; it applies all generated scene updates together only after success, so existing files are never partially overwritten.
- Project scene and note saves compare against the last-read disk contents. Autosave is configurable (two-second idle interval by default); failures leave documents dirty and report non-blocking feedback.
- Optional daily writing goals support active-document words, project manuscript words, or newly inserted words. New-word progress is local-date based and undo/redo aware; pausing/resetting tracking never changes manuscript text.
- Local recovery snapshots every 30 seconds while documents are dirty and at orderly shutdown. Startup offers restore, inspect/compare, locate a moved project, discard recovery data, or defer.
- Explicit Markdown/plain-text manuscript export uses current editor buffers, selectable scene subsets, configurable headings and separators, UTF-8 encoding, and LF line endings. Replacing a destination requires confirmation.
- Project > Compile Book as PDF creates an A5 book with a title page, contents, ordered chapters and scenes, and page numbers. It uses open scene buffers (including unsaved edits after confirmation), excludes reference notes, and never changes project files.
- Named local revision snapshots capture current project structure and in-memory scene/note text without clearing dirty state. Project > Review Revision Snapshots lists valid local snapshots, reports unreadable ones, and compares two snapshots for scene additions, removals, ordering, title, and text changes.
- Opt-in local scene summaries and continuity checks send only explicitly selected scenes/notes after displaying their names and the configured Ollama destination; bounded requests run in workers, stale results are dropped, and output appears in a separate review panel without editing files.
- Project > Translate Project to Ukrainian/English translates the project title, chapter/scene/reference-note titles, and all scene and note text using the configured Ollama model. It confirms the destination, snapshots the original project, supports cancellation, preserves IDs/paths/order/links and line endings, and commits the result only if all translations succeed and the project has not changed. Each run is limited to 500 translatable fields of up to 32,000 characters each; exceeding a limit aborts without applying partial translations.
- Distraction-free mode from View or `Ctrl+Shift+F`; `Esc` exits after first dismissing any inline completion, and an accessible status-bar action is always available while the mode is active.
- Standard editing through Qt, including undo, redo, clipboard actions, and select all. Edit > Text Formatting provides case conversion, line indent/outdent, trailing-whitespace cleanup, and “Like in the book,” which indents the first line of each paragraph while preserving blank lines and line endings. Transformations apply to selected text/lines or the whole document and are undoable. “Format Whole Document…” lets the author choose one operation to apply explicitly across the entire document.
- Find, previous/next navigation with live match counts, replace-current, and undoable replace-all.
- Status display for UTF-8, detected line-ending style (LF, CRLF, or CR), cursor line and column, and AI connection state.
- Local Ollama connection using `http://localhost:11434` and `gemma4:12b` by default; host and model can be changed in AI Settings.
- Inline completions shown as non-destructive ghost text. `Tab` accepts a suggestion and `Esc` dismisses it. Suggestions are discarded when the relevant text, cursor, selection, or active document changes.
- Debounced completion requests with bounded context, background workers, and stale-result checks.
- AI-assisted spelling and grammar suggestions with underlines, context-menu replace/ignore actions, response validation, and undo support for edits.
- Prompt-based text generation runs in the background, can be cancelled, and appears in a review dialog; generated text is inserted at the captured cursor or over the captured selection only after explicit acceptance.
- Settings are grouped into Connection, Writing, AI assistance, and Advanced prompts tabs, with a reset-to-defaults option; the Connection tab can test the configured Ollama host/model and suggests how to install a missing model.
- Editor background, text, and selection colors follow the system palette.
- Application preferences are saved as YAML in the user's configuration directory (`settings.yaml`); existing `settings.json` preferences are loaded for compatibility.
- An in-memory Ollama diagnostics window for the current session.
- Unit tests using fake providers and mocks; tests do not require a running Ollama server.

### Known gaps and behavior to be aware of

- Automatic spellcheck now only presents validated underlines. Corrections require an explicit context-menu action and are undoable.
- `Auto` uses local script and common-word signals, and ambiguous or short text remains `Auto` for the model to infer.
- Files are currently read into memory as a whole; very large files may still use substantial memory even though reads and writes run off the GUI thread.
- The app currently supports UTF-8 files only. It rejects embedded NULs as likely binary input; broader binary detection is not implemented.
- The status bar reports encoding and line ending, but these are not currently user-selectable.
- The UI is minimal and has no toolbar or recent-file list.
- Recovery handles the supported snapshot cases without overwriting changed canonical files, but full repair and diagnosis workflows for partial or corrupt recovery data remain incomplete.
- Scheduled revision snapshots and revision-history deletion/restore controls are not yet available. Revision comparisons cover scene changes; broader project-structure and reference-note comparisons remain future work. Novel-aware AI currently covers project-outline setup, scene summaries, and continuity review; proposed-edit previews and acceptance are not implemented.

### Project format and local data

A project uses a version-1 UTF-8 YAML manifest named `utexteditor.yaml`. It stores `format_version`, a stable `project_id`, the title, ordered chapters and scenes, ungrouped scenes, reference-note IDs/types/titles, project-relative paths, and note links. Scene and note contents remain separate files under `manuscript/` and `notes/`. Manifest paths are validated against traversal and symlink escapes. Unknown manifest fields and unsupported versions are rejected rather than rewritten.

Word counts treat a word as a run of Unicode letters or digits, with internal apostrophes or dash variants allowed when surrounded by word characters. Missing or unreadable scene files produce an explicitly incomplete count. Reference notes are excluded from manuscript totals and exports.

Recovery data is stored locally in the operating system's UTextEditor application-data directory (on macOS, `~/Library/Application Support/UTextEditor/recovery`). It does not replace canonical files. Recovery is best-effort: edits since the latest snapshot and failures outside the captured snapshot interval may not be recoverable, and it is not a substitute for backups. Named revision snapshots are stored in `.utexteditor/revisions` inside the project and should be included in the author's own backup when they need to retain them; snapshot retention management is not yet exposed in the UI.

Exports use UTF-8 without a byte-order mark and normalize line endings to LF. Export and snapshot creation do not save source documents or clear their dirty state.

Writing-goal configuration and per-document daily progress are stored locally in `writing-goals.json` beside the application settings. The local system date defines the daily boundary; changing the timezone does not delete progress recorded under other dates.

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

## Technology and design

- Python 3.12+
- PySide6 / Qt 6
- Ollama for local AI requests
- pytest

The application separates document state and file handling (`app/document/`), AI services and the `AIProvider` abstraction (`app/ai/`), persistent settings (`app/settings/`), and Qt UI (`app/ui/`). The Ollama HTTP client is isolated in `app/ai/ollama_client.py`. GUI widgets do not make direct Ollama calls; the UI dispatches AI work to background workers and receives results on the GUI thread.

AI completions are suggestions and do not enter the document until accepted. Model responses are untrusted: spellcheck output is parsed and checked against the captured document snapshot before it is used. No cloud AI provider is configured.

## Product direction

The long-term goal is to make UTextEditor a focused novel-writing studio while keeping its plain-text editing roots. The project-workspace milestone and selected saving, recovery, export, and snapshot protections are implemented. Remaining work should continue in useful, author-controlled increments:

1. **Project workspace:** Organize a novel into chapters and scenes, let authors reorder them, and show manuscript word counts at scene, chapter, and project level. Start with ordinary text files in a project folder so manuscripts remain portable and easy to back up.
2. **Trustworthy writing workflow:** Strengthen autosave, crash recovery, writing goals, and distraction-free writing before adding complex assistance.
3. **Story reference material:** Add separate, linkable notes for characters, settings, timelines, and research; keep reference notes distinct from manuscript prose.
4. **Opt-in novel-aware AI:** Expand explicit tasks such as summarizing a chapter or checking continuity against author-provided notes. Present analysis and proposed edits separately, never silently rewrite prose, and keep processing local through the configured Ollama provider.
5. **Revision and sharing:** Add manuscript export and revision snapshots or comparisons so authors can share work and explore changes safely.

Full recovery repair, complete revision comparison/restore workflows, and proposed-edit AI preview/acceptance remain follow-on work. Broader editor improvements—batch spellcheck review, richer language detection, and robust large-file handling—also remain valuable. Any future AI or project features must preserve privacy, portability, and the author's control; avoid proprietary project formats or cloud services without a separate product decision.

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
