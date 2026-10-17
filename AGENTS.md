# UTextEditor — Codex Instructions

## Project

UTextEditor is a desktop text editor inspired by GEdit.

The complete product specification is documented in `README.md`.

Before implementing a feature, read `README.md` and follow its requirements.

`README.md` is the concise source of truth for current behavior and product
scope. `SPEC.md` contains detailed acceptance requirements, some of which
describe earlier or future scope; check the current status in `README.md` and
`UNIMPLEMENTED_FEATURES.md` before treating a specification section as an
implemented feature. Preserve explicit user control over manuscript changes.

## Repository map

| Location | Responsibility |
| --- | --- |
| `app/main.py` | Startup, logging, and application construction |
| `app/ui/` | Qt widgets, dialogs, window orchestration, and background workers |
| `app/document/` | Text/document state, encodings, file operations, recovery, revisions, and export |
| `app/project/` | Project model, validation, filesystem operations, and project workflows |
| `app/ai/` | `AIProvider`, prompt construction, response validation, and Ollama HTTP client |
| `app/settings/` | User settings persistence and defaults |
| `tests/` | Offline unit and UI tests using fake providers and mocked I/O |

Start tracing a behavior from its owning service/model, then follow the UI
caller and its tests. `app/ui/main_window.py` coordinates many workflows; keep
domain rules and persistence logic in their owning packages rather than adding
more business logic there.

## Change workflow

1. Read the relevant README requirements and the owning implementation/tests.
2. Search for an existing helper or workflow before adding another abstraction.
3. Keep changes scoped; preserve unrelated worktree changes and do not edit generated files.
4. For behavior changes, add a focused regression test and update README behavior
   or architecture notes when user-visible behavior changes.
5. Run the narrow test module first, then `python -m pytest` for a complete
   change. No formatter or linter is configured; do not introduce one just to
   validate a small patch.
6. Review `git diff --check` and the final diff before finishing.

Useful test targets:

| Area | Tests |
| --- | --- |
| Ollama requests and provider behavior | `tests/test_ollama_client.py` |
| AI prompt/context/validation | `tests/test_prompts.py`, `tests/test_completion_service.py`, `tests/test_spellcheck_service.py` |
| Editor and Qt window behavior | `tests/test_editor_widget.py`, `tests/test_project_ui.py` |
| Projects and AI-assisted project workflows | `tests/test_project_domain.py`, `tests/test_project_setup.py` |
| Files, recovery, revisions, and export | `tests/test_document.py`, `tests/test_recovery.py`, `tests/test_revisions.py`, `tests/test_export.py` |
| Settings and startup | `tests/test_settings.py`, `tests/test_main.py` |

Qt tests run headlessly with `QT_QPA_PLATFORM=offscreen`. Tests must not need
a running Ollama server; mock network calls or use a fake `AIProvider`.

## Technology

Use:

* Python 3.12+
* PySide6 / Qt 6
* Ollama
* `gemma4:12b`
* pytest
* pyproject.toml

The application must remain a native desktop application.

## Architecture

Keep UI, document management, and AI integration separated.

AI integration must use an abstraction layer:

```python
AIProvider
```

Ollama implementation should be isolated in:

```text
app/ai/ollama_client.py
```

Do not call Ollama directly from GUI widgets.

## Important implementation boundaries

- Provider methods are synchronous by design; invoke them only through the
  existing worker pattern (`FunctionWorker`/`QThreadPool`) from UI workflows.
  Return UI updates through queued Qt signals.
- Any asynchronous result that can affect an editor or project must be checked
  against its captured document/project/settings generation before applying.
- AI output is untrusted. Validate it at the service boundary, and never
  silently apply generated or corrected text. Bulk project updates must retain
  their snapshot, conflict checks, and transactional rollback behavior.
- `generate_private` means internal workflow generation, not private logging:
  Ollama requests and responses are visible in the in-memory AI debug window.
  Treat those diagnostics as potentially containing manuscript text.
- Keep Ollama HTTP payloads, endpoint handling, and raw response parsing inside
  `app/ai/ollama_client.py`; UI and project services use `AIProvider`.

## AI

Default provider:

```text
Ollama
http://localhost:11434
```

Default model:

```text
gemma4:12b
```

AI requests must never block the GUI thread.

Completion requests must support cancellation or stale-response detection.

Never insert an AI completion directly into the document without explicit user acceptance.

`Tab` accepts an inline completion.

`Esc` rejects an inline completion.

## Code Quality

Prefer simple, maintainable code over unnecessary abstraction.

Do not introduce dependencies unless they provide clear value.

Keep functions and classes reasonably small.

Use type hints.

Handle errors explicitly.

Do not silently swallow exceptions.

## Testing

Add or update tests when changing behavior.

Run:

```bash
pytest
```

after making changes.

Do not require a running Ollama instance for unit tests.

Use mocks for Ollama in tests.

## GUI

The GUI must remain responsive during:

* Ollama requests
* file operations
* spell checking
* completion generation

Do not perform blocking network or AI operations on the Qt GUI thread.

## Documentation

Update `README.md` when project behavior or architecture changes.

Do not put implementation details into `README.md` unless they are useful to developers or users.

## Git

Do not modify unrelated files.

Do not rewrite existing history.

Do not commit secrets, API keys, credentials, or local configuration.

Before considering a task complete:

1. Run relevant tests.
2. Check the resulting diff.
3. Verify that the implementation matches `README.md`.
