## RAG-03 — local lexical index

- COMPLETE: RAG-03 / RAG-03.V1; all four criteria and required offline gate passed.
- RAG-01/02 committed as aab39ee; unrelated staged bytecode/DS_Store preserved.
- Added project-ID/root-scoped SQLite FTS5 cache outside project files.
- Runtime FTS5 probe reports unavailable support without affecting existing AI/editor.
- Schema/chunk policy versions and source fingerprints drive incremental refresh.
- Private staging databases publish atomically; unchanged sources are not re-tokenized.
- Corruption/version mismatch rebuilds from source; orphan staging is never read.
- Disk-only sources persist; partial captures remove stale omitted-source passages.
- Locks/cancellation and source rechecks prevent observed obsolete publications.
- Changed: app/project/rag_index.py, app/ui/retrieval_index_dialog.py, MainWindow wiring, docs/tests/catalog.
- Focused: 392 passed in 47.52s; final targeted: 60 passed in 9.15s.
- Full offscreen: 1318 passed, 2 live-only skips in 164.65s; log /private/tmp/utexteditor-rag03-final-full.log.
- Translations validated against 1055 extracted strings; 1068 compiled translations.
- Clean Code checklist reviewed: intent, ownership, safety, errors, tests, diff, report.
- Branch main; git diff --check passed; no native/live claims or RAG-03 native gate.
- Resume: RAG-04 context retrieval/assembly; RAG parent remains OPEN; index not yet used in AI requests.
- Command: QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

## RAG-02 — source capture and chunk provenance

- COMPLETE: RAG-02 and RAG-02.V1; all four acceptance criteria verified.
- RAG-01/V1 COMPLETE; RAG parent remains OPEN.
- Added worker-only app/project/rag_sources.py; no model requests or index writes.
- Exact offsets, stable chunk IDs and semantic character-field boundaries retained.
- Disk and authoritative unsaved-buffer snapshots/chunks remain separate.
- Captures retain scene association metadata, directed relationships and order.
- Portraits excluded; incomplete coverage carries explicit source diagnostics.
- Source/byte/chunk limits bound work; cancellation aborts rather than returning partial success.
- Project path validation reused; disk/manifest/buffer rechecks reject observed changes.
- Preconditions/failure matrix: docs/rag-source-capture.md; regression: tests/test_rag_sources.py.
- Focused: 152 passed in 2.55s; log /private/tmp/utexteditor-rag02-focused.log.
- Full offscreen: 1286 passed, 2 live-only skips in 167.28s; log /private/tmp/utexteditor-rag02-full.log.
- Clean Code checklist reviewed: intent, ownership, safety, errors, tests, diff, report.
- git diff --check passed; no native/live verification claimed or required by RAG-02.
- Unrelated DS_Store/bytecode changes preserved; no commit created.
- Resume: select RAG-03 local lexical index; no blocking dependency remains.
- Command: QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

## RAG-01 — context policy and budgets

- COMPLETE: RAG-01 and RAG-01.V1; all five criteria verified.
- RAG parent remains OPEN; no retrieval/index implementation is claimed.
- Workflow matrix and source/refusal/chronology rules: docs/ai-context-policy.md.
- Added explicit token-window setting, separate from existing character limits.
- Full rendered role/prompt, output reserve and framing/safety enter one estimate.
- UTF-8 estimates are approximate; server-default mode preserves prior behavior.
- Explicit windows check architecture metadata and send num_ctx without fallback.
- Continuity refuses source starvation and limited associated-character details.
- Summary excerpts and other existing source limits remain unchanged.
- Changed: AI budget/client/analysis/provider, settings/UI, docs and regressions.
- Focused UI/AI/i18n: 471 passed; final focused selection: 120 passed, 289 deselected.
- Final full offscreen: 1248 passed, 2 skipped in 155.93s; log /private/tmp/utexteditor-rag01-final-full.log.
- Translation validation passed against 1031 extracted strings; 1044 compiled entries.
- Clean Code checklist reviewed: intent, ownership, safety, errors, tests, diff, report.
- No live Ollama/native GUI evidence claimed; neither is a RAG-01 gate.
- Unrelated bytecode/DS_Store changes preserved; no commit created.
- Resume: RAG-02 source capture/chunking; parent remains OPEN, no blockers for RAG-02.
- Command: QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest
