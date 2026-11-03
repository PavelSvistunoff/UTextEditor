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
| `app/project/character_context.py` | Bounded, scene-scoped character context for local AI workflows |
| `app/ai/` | `AIProvider`, prompt construction, response validation, and Ollama HTTP client |
| `app/settings/` | User settings persistence and defaults |
| `tests/` | Offline unit and UI tests using fake providers and mocked I/O |

Start tracing a behavior from its owning service/model, then follow the UI
caller and its tests. `app/ui/main_window.py` coordinates many workflows; keep
domain rules and persistence logic in their owning packages rather than adding
more business logic there.

Structured character profiles, directed relationships, and optional scene
associations are part of the version-1 YAML manifest. Scene-focused AI requests
must use `character_context.py` and include only explicitly associated
profiles; planning may use its compact project-level motivation summary.

## Logical task batches and continuation

When a user assigns work from `TASKS.md`, prefer **one bounded logical batch of 1–4 closely related atomic subtasks within a single parent TASK** per Codex run, unless the user explicitly requests a different scope. This replaces the default of exactly one atomic subtask per run; it does **not** authorize implementing the entire backlog or unrelated parent tasks. For high-risk data-integrity, migration, or cross-platform changes, use a smaller batch (often one subtask).

1. Before coding, read the parent TASK, the candidate subtasks, their dependencies and acceptance criteria, the latest checkpoint, relevant README sections, code and tests. Choose 1–4 subtasks that share context and can be verified within the available execution budget. Record the exact IDs and why they belong together. If scope is uncertain, choose the smaller batch.
2. Create a criterion-by-criterion checklist for **each selected subtask** and the relevant parent acceptance gate. Inspect existing implementation before assuming a checkbox represents missing code.
3. Implement and verify iteratively. Continue within the selected batch while safe, feasible work remains; do not stop merely because one implementation step or focused test passed. Diagnose failures and try reasonable alternatives without weakening manuscript safety guarantees.
4. Run focused tests after relevant changes. Run the full offscreen suite at the end of a logical batch when practical, and earlier when risk warrants. Never claim tests, native checks, or platform verification that were not actually performed.
5. Update each selected subtask status independently. Mark `[x]` only when its entire done-when gate is verified; otherwise retain `[~]`, `[ ]`, or `[?]` as appropriate. Mark the parent complete only when all child subtasks and its parent acceptance gate pass. Do not mark unselected subtasks complete without evidence.
6. Preserve unrelated worktree changes. Do not automatically move to another parent TASK or exceed the selected batch just because time remains.
7. Before ending, put a concise, resumable checkpoint at the top of `IMPLEMENTATION_PROGRESS.md` if any selected work remains incomplete or parent acceptance is still pending. Keep the checkpoint focused (roughly 10–20 lines where feasible); link to detailed evidence instead of copying long logs.
8. Report an outcome **for every selected subtask**: `COMPLETE`, `BLOCKED`, or `CHECKPOINT`, and report the parent status separately. A batch is `COMPLETE` only when every selected subtask is complete; this does not imply the parent is complete.

Stopping with an unfinished selected subtask is justified only by a specific external decision/dependency, missing tool/permission/platform, unacceptable data-safety risk, or exhausted execution/context budget. A difficult bug or failed test alone is not a blocker. On the next run for the same assignment, verify the checkpoint against the current branch and resume the unfinished selected subtask(s) before selecting new work, unless the user changes priorities.

### Minimal checkpoint fields

- Parent TASK, selected subtask IDs, per-subtask outcome, and separate parent status.
- Acceptance criteria satisfied, outstanding, or unverified, with brief evidence.
- Files changed and branch/commit if known; preserve unrelated work.
- Exact focused/full test commands and results; tests and manual checks not run.
- Concrete blocker (or `none`), next smallest safe action, and resume command.
- Whether to resume the current batch or await a newly assigned batch.

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
