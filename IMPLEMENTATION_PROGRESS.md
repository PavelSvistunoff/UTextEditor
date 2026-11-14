## RAG-05 — manual completion pilot and source review

- COMPLETE: RAG-05 / RAG-05.V1 / RAG-05.V2; RAG parent remains OPEN.
- Previous completed task: RAG-04, commit a22429d; branch main.
- Opt-in command: AI > Review RAG Completion Context; ordinary/automatic paths unchanged.
- Requires a bound project scene and explicit token window; no model allocation guessed.
- Review shows exact prompt/role, actual provider host/model, budget and source manifest.
- Source exclusions require worker recapture; mandatory scene/associated characters retained.
- Open scene/note buffers override disk without index writes; coverage limitations disclosed.
- Worker checks source stamps before dispatch and after success/failure; stale generations discard.
- Cancellation retains manuscript/undo; suggestions still require explicit Tab acceptance or Esc rejection.
- Changed: app/ui/rag_completion.py, main_window.py, app/ai/captured_completion.py, UI tests/docs/catalogs.
- Focused: 104 passed, 1 native-only skip in 45.33s; /private/tmp/utexteditor-rag05-focused.log.
- Full offscreen: 1390 passed, 3 skipped (2 live-only + 1 native) in 213.29s; /private/tmp/utexteditor-rag05-final-full.log.
- Native Cocoa: 1 passed, 24 deselected in 0.68s; macOS 27.0.1 arm64 / Qt 6.11.2; /private/tmp/utexteditor-rag05-native.log.
- Native real-dialog keyboard automation uses a fake provider; no live Ollama, other-OS or screen-reader claims.
- Catalog: 1078 finished translations; 1065 extracted strings validated; git diff --check passed.
- Clean Code checklist reviewed in docs/rag-manual-completion.md; unrelated bytecode/DS_Store preserved.
- Resume: RAG-06; first record lexical baseline and measure embedding choices before model selection; parent OPEN.
- Command: QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

## RAG-04 — retrieval and budgeted context assembly

- COMPLETE: RAG-04 / RAG-04.V1; all six acceptance criteria and the offline gate passed.
- RAG-01–03 COMPLETE; preceding commit 49db4d6; RAG parent remains OPEN.
- Changed: app/project/rag_context.py, app/ai/context_prompt.py, rag_index.py, docs/backlog/tests.
- Explicit mandatory sources, target associations and existing scene character helper are retained.
- Read-only index lookup filters source scope/fingerprints before candidate ranking.
- Changed/uncached sources and unsaved buffers use current captured passages, without index writes.
- Deterministic weighted ranking, source diversity, overlap/dedup and exact prefix shortening implemented.
- Exclusions/earlier-scene policy apply before search; later/unplaced/ambiguous context is labeled.
- Full rendered prompt, response reserve and wrappers are checked against one explicit budget.
- Returned manifest records budget, query, source decisions/fingerprints and incomplete/unavailable states.
- Source/metadata changes and cancellation reject observed stale captures; no unknown source is trusted from cache.
- Focused: 132 passed in 1.62s; log /private/tmp/utexteditor-rag04-focused.log.
- Full offscreen: 1366 passed, 2 live-only skips in 174.61s; log /private/tmp/utexteditor-rag04-final-full.log.
- Existing model/UI calls remain unchanged; integration is RAG-05 and later workflow tickets.
- Clean Code checklist reviewed: intent, ownership, safety, errors, tests, diff, report.
- Branch main; git diff --check passed; unrelated bytecode/DS_Store preserved; no native/live claims.
- Resume: RAG-05 manual completion integration; parent remains OPEN and RAG-12 cross-workflow gates pending.
- Command: QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q

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
