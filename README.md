# UTextEditor

UTextEditor is a native desktop text editor for people who want a simple place to write and edit plain text, with optional local AI assistance. It is inspired by GEdit and built with Python and Qt. The editor remains usable when AI is disabled or Ollama is unavailable.

The project aims to keep writing fast and predictable: documents stay under the user's control, AI suggestions are visible before use, and normal editing does not depend on a network service. AI requests use a local Ollama server by default; document text is not sent to a cloud AI provider.

## Project goals

- Provide a dependable, lightweight editor for everyday text files.
- Keep multiple documents and their modified state separate in tabs.
- Make common editing, search, and file operations easy to reach.
- Offer optional local completion and spelling assistance without freezing the interface.
- Keep AI integration replaceable and separate from the UI.
- Prefer explicit user control over generated or corrected text.

## Current status

The current implementation is an early, usable MVP. Implemented features include:

- Native PySide6 desktop window with File, Edit, Search, and AI menus.
- New, open, save, and Save As for UTF-8 text files; unsaved-change prompts on close.
- File reads and writes run in background workers; saves replace files atomically where supported.
- Multiple document tabs with per-document text, dirty state, and modified-tab markers.
- Standard editing through Qt, including undo, redo, clipboard actions, and select all.
- Find, replace, and replace all.
- Status display for UTF-8, detected line-ending style (LF, CRLF, or CR), cursor line and column, and AI connection state.
- Local Ollama connection using `http://localhost:11434` and `gemma4:12b` by default; host and model can be changed in AI Settings.
- Inline completions shown as non-destructive ghost text. `Tab` accepts a suggestion and `Esc` dismisses it. Suggestions are discarded when the relevant text, cursor, selection, or active document changes.
- Debounced completion requests with bounded context, background workers, and stale-result checks.
- AI-assisted spelling and grammar suggestions with underlines, context-menu replace/ignore actions, response validation, and undo support for edits.
- Prompt-based text generation inserted at the cursor or over the current selection.
- Settings for completion behavior, language choice, spellchecking, prompt customization, and editor appearance (font, size, tab width, wrapping, and line numbers).
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
- The UI is minimal and has no toolbar, recent-file list, or session restore.

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

The next work should strengthen the core writing experience before adding more AI features:

1. Add a batch review interface for spelling suggestions; current corrections are reviewed individually from the context menu.
2. Add editor preferences for typography, wrapping, indentation, and theme.
3. Improve `Auto` language detection for mixed and short text and make language support easy to extend.
4. Improve file handling with encoding selection/detection, clearer unsupported-file errors, and more memory-efficient large-file support.
5. Add recent files and session restore, with clear control over whether document contents are persisted.
6. Improve navigation and writing comfort with line numbers, configurable indentation, and optional word wrap.
7. Consider Markdown syntax highlighting and preview as opt-in writing tools.

These are product ideas, not promises or currently implemented features. Additional AI providers, cloud AI, project-aware indexing, plugins, and AI chat can be considered later if they support the local-first, user-controlled editor rather than making it more complex by default.

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
