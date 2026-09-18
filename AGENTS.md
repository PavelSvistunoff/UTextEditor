# UTextEditor — Codex Instructions

## Project

UTextEditor is a desktop text editor inspired by GEdit.

The complete product specification is documented in `README.md`.

Before implementing a feature, read `README.md` and follow its requirements.

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
