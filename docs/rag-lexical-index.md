# RAG-03 lexical index contract

RAG-01/02 are complete (commit `aab39ee`). This ticket adds cache maintenance,
not prompt retrieval. The SQLite FTS5 cache contains saved manuscript text and
character metadata and lives outside the project, under the application settings
directory. Unsaved overlays must never be persisted in this cache.

| Criterion | Preconditions | Failure / stale cases |
| --- | --- | --- |
| Scope and availability | FTS5 probe succeeds, validated project identity/root | Missing FTS5, copied project ID at another path, unwritable cache; existing editor/AI unaffected |
| Versions and refresh | Compatible schema/chunk policy, captured disk sources | Insert/edit/rename/delete, changed chunk policy, corruption, interrupted staging file, relocation |
| Publication | One captured generation, verified disk/manifest, worker current | Cancellation before/during staging, source change, old worker and concurrent readers |
| Controls | Open project, local-only maintenance dialog | Status/refresh/rebuild/delete, cancellation/close/project switch, no UI-thread filesystem work |

Each cache key includes both project ID and canonical root. Moving or copying a
project creates a new cache scope, leaving the old disposable cache separate.
Refresh copies a compatible committed database to a private staging file and
updates only changed source rows/chunks there; rebuild starts a new schema.
Unchanged sources are not re-tokenized. Publication replaces the cache file only
after the staging transaction closes, cancellation is checked and sources are
verified again. Readers open a committed generation, never staging files.

SQLite atomic replacement and process-local writer serialization protect cache
generations, not against arbitrary independent writers changing manuscripts
after the final check. Runtime SQLite/FTS5 support is probed, not inferred from
Python's version. A cache failure must not prevent ordinary editing or existing
AI operations. A partial source capture produces an explicitly incomplete index,
removing old passages for omitted/deleted sources rather than retaining stale hits.

Status describes the last indexed snapshot, not a guarantee that disk files
have not changed since indexing. Future RAG request assembly must verify actual
sources again. Delete removes only this scope's cache/staging files and cannot
touch manuscript files. Local cache deletion is not a secure-erasure guarantee.
Deletion also removes this cache's SQLite sidecars and interrupted staging files;
non-regular/symbolic-link targets are refused. A cancellation after deletion has
begun does not restore deleted disposable cache files; check status before retrying.

Protocol references: [SQLite FTS5](https://www.sqlite.org/fts5.html) and
[SQLite atomic commits](https://www.sqlite.org/atomiccommit.html).

## Completion evidence

- RAG-03 and RAG-03.V1: COMPLETE; RAG parent remains OPEN, next RAG-04.
- Tested runtime: Python 3.14.10, SQLite 3.54.1, FTS5 available. Other builds
  use the runtime probe; missing-feature behavior is covered with injected
  SQLite failures. No claim of testing every supported Python/platform build.
- Focused service/source/UI/i18n command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_rag_index.py tests/test_retrieval_index_ui.py tests/test_rag_sources.py tests/test_project_ui.py tests/test_i18n.py`:
  392 passed in 47.52s; log `/private/tmp/utexteditor-rag03-focused.log`.
- Final targeted run after the sidecar cleanup regression:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_rag_index.py tests/test_retrieval_index_ui.py tests/test_i18n.py`:
  60 passed in 9.15s; log `/private/tmp/utexteditor-rag03-final-focused.log`.
- Final full offscreen command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  1318 passed, 2 live-only skips in 164.65s;
  log `/private/tmp/utexteditor-rag03-final-full.log`.
- Translation validation passed against 1055 extracted strings; Ukrainian `.qm`
  regenerated with 1068 finished translations. `git diff --check` passed.
- Clean Code checklist: intent (explicit status and generation types);
  ownership (SQLite and source rules in project services, UI worker orchestration);
  safety (disk-only cache outside manuscripts, scope isolation, cancellation,
  stale-source checks, dirty-buffer/undo preservation); errors (visible failure
  and incomplete coverage); tests (normal/failure/concurrent/stale and full suite);
  diff (no dependency, unrelated refactor or manifest migration); report (cache
  snapshot freshness and server/native limits stated explicitly).
- No native accessibility or live-model evidence claimed. RAG-03 has only the
  offline V1 gate. Corrupt caches are disposable; explicit Rebuild can replace
  them even when ordinary SQLite page checks cannot detect an FTS-specific fault.
  Atomic replacement can fail on platforms that prevent replacing a file held
  by a reader; the prior generation is retained and the operation reports failure.
- UI controls operate locally; no retrieved passages are sent to models by this
  ticket. RAG-04/05 supply policy-aware retrieval and request integration.
