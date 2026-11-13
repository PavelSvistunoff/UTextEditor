# Repository refactoring plan

Status: **in progress**. This is an initial, prioritized inventory, not a
claim that every source file and test has been reviewed. The repository has
123 tracked Python files. Review each remaining file and its tests before
deciding whether a change is warranted; add concrete findings here as they
are established. Avoid changes solely to satisfy a size metric.

## Shared completion gates

For each package, inspect every module and its callers/tests for responsibility,
duplication, naming, nesting, coupling, error handling, dead code and missing
coverage. Record findings or an explicit rationale for leaving code alone.
Before risky edits capture normal, failure and stale-state behavior in tests;
preserve APIs, data formats, dirty buffers, undo and transaction semantics.
Run focused tests, the full offline suite where practical, and `git diff --check`.
Review the Clean Code checklist in `docs/clean-code-codex.md`. Document native
checks separately; offscreen tests cannot establish native behavior.

## Priority and investigation queue

1. **Document** — `app/document/encoding.py`: repeated counting and manual
   character scanning obscure the line-ending tie rule; test mixed endings and
   preserve the first-occurrence tie break. Initial change completed in `be1cc15`.
   `file_manager.py`: duplicated digest checks now share a rule while retaining
   both checks and their distinct diagnostics; verify removed/changed sources,
   staging cleanup, dirty state and the documented independent-writer race.
   `export.py` and `book_compiler.py`: shared scene ID and text validation;
   selection and the distinct validation order are covered by regressions.
   `recovery.py`: save and snapshot parsing now use the same project-item
   identity predicate, with damaged snapshot preservation tested. Initial review
   of `revisions.py` confirmed that scanning a FIFO named `.json` blocks; a
   separate fix rejects non-regular revision files with a bounded regression.
   `writing_goals.py`: shared undo/redo checkpoint restoration without copying
   or truncating reachable history. Memory growth remains open under TASK-001.02.
   Audit `file_manager.py`, `recovery.py`, `revisions.py`, `writing_goals.py`,
   `merge.py`, export/compiler and remaining modules with their corresponding
   tests. Risk: external-write conflicts, rollback, data loss and undo; do not
   claim protection from arbitrary concurrent writers or prune Qt undo.
2. **Project** — inspect `service.py` (large transaction/orchestration surface),
   `model.py`, paths, search, translation, auto-writer and remaining modules.
   Character serialization mapping is now readable; inspect remaining model
   validation and establish responsibility and duplication findings before extraction.
   Gate: stable IDs/YAML compatibility, conflict checks and rollback tests.
   `translation.py` scene capture is shared while retaining traversal order.
   Auto-writer rollback previously suppressed temporary-file unlink errors;
   separate behavior fix reports remaining temporary files and preserves the
   rollback diagnostic, with failure injection.
3. **AI** — inspect provider, Ollama client, validation, prompts and services.
   Gate: offline tests, untrusted output validation, disclosure and unchanged
   provider protocol; retain worker-based invocation and stale-response guards.
4. **UI** — inspect `main_window.py` (large orchestration surface), workers,
   editor and each dialog, together with UI and end-to-end tests. Extract only
   cohesive responsibilities supported by tests. Risk: Qt lifetime, focus,
   asynchronous generations and undo; native accessibility remains unverified.
5. **Settings and startup** — inspect `settings/settings.py`, `main.py`,
   logging and i18n with their tests. Preserve defaults, persistence and startup
   diagnostics; distinguish confirmed dead code from external/public entry points.
6. **Tests and other Python modules** — inspect every test, benchmark and tool
   for misleading assertions, duplication and stale/dead code. Keep tests focused
   on observable behavior and preserve useful failure diagnostics.

Completion requires all six inventories, resolved or justified findings, and
documented checks. Existing backlog/native gates in `TASKS.md` remain separate;
this refactoring does not implicitly complete them or authorize new features.
