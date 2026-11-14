# Automatic inline retrieval (RAG-08)

## Predeclared workload and limits

Before implementation/tuning: measure 100 saved scenes of about 10 KiB each,
one open target buffer, 20 repeated captures and 20 distinct paragraph queries.
Warm lexical retrieval target: p95 below 250 ms on the development machine.
Report retrieval, verification/cache reuse, and generation/end-to-end timings
separately; a fake provider measures orchestration, not live-model throughput.
Unit tests use an injected clock and have no wall-clock performance assertions.

One automatic retrieval/generation worker may run per window. While it finishes,
retain only the newest debounced request. Retrieval has a cooperative 1 second
deadline and at most four optional passages. A timed-out retrieval is discarded;
recapture mandatory context with a separate 1 second deadline, or skip safely.
Synchronous HTTP calls cannot be preempted; embedding HTTP operations use a
250 ms socket timeout and results arriving beyond the deadline are discarded.
No index refresh or document-vector creation is allowed during automatic typing.
Hybrid mode may use existing saved vectors and embed the query only after its
separate session destination approval. Missing vectors use lexical fallback.

## Acceptance preconditions and failure cases

- Only automatic completion of a bound scene, with automatic project context
  and the separate retrieval opt-in enabled, takes this path. Unknown token
  windows skip with feedback. Standalone and ordinary manual completion retain
  their existing paths.
- A cache hit must verify all source bytes/metadata and current open buffers.
  Index generation, request policy, exclusions, embedding destination/model and
  vector-cache identity must invalidate reuse. No stale cache fallback.
- Typing/cursor/selection/tab/project/settings changes, cancellation, source
  changes and errors must preserve manuscript and Undo. Late requests cannot
  replace a newer suggestion. Timeout/index absence must be visible.
- Separate embedding consent must not block typing or repeat after declining.
  Inspection must show the exact frozen role/prompt/manifest used for the
  displayed suggestion, without sending another request.
- Native verification must exercise typing, switching, inspection, Tab/Esc and
  Undo. Offscreen tests alone cannot close RAG-08.V2.

## Implementation and operational limits

`InlineContextService` owns one memory entry. Its key includes root/project ID,
manifest, index generation/state, the complete frozen request (including query,
chronology, exclusions and budget), open-buffer text hashes/revisions, embedding
destination/installed identity and vector-file generation stamp. Every hit reads
and verifies source bytes and manifest again. Incomplete captures and hybrid
failures are not retained. The 16 MiB cache limit estimates stored prompt/source
UTF-8 bytes, not total Python memory. Existing source capture has its own bounds.

`InlineRetrieval` serializes worker execution and holds only the latest pending
intent. Existing typing debounce and cursor/selection/tab/project/settings
generations invalidate obsolete requests. All bound scene/note buffer stamps
participate, including background tabs. At most 1 Mi characters per open source
and 4 Mi characters across open project buffers are copied on the GUI thread;
larger buffers skip automatic retrieval. Source capture additionally enforces
UTF-8 byte limits and reports omissions. The current paragraph is bounded by
the existing excerpt setting, with at most 1,024 preceding characters. Language
is determined from author text before retrieval. No generated result is cached.

Generation consent retains the existing per-host disclosure. Hybrid uses the
separate embedding destination/model, approved once per settings session in a
non-modal dialog; declining or leaving the dialog pending keeps lexical mode.
Changing settings requires approval again. Automatic retrieval reuses only
current saved vectors; missing vectors or unsaved eligible sources cause visible
lexical fallback. Query embeddings remain request-local. No document vectors
are generated or rewritten by this path. Installed identity is checked before
reusing a hybrid result, and no alternate model/server is tried automatically.

The suggestion's inspection dialog sends nothing. It shows frozen role, exact
prompt, budget, coverage notices and manifest; source exclusions apply to future
suggestions and clear current work. Required sources cannot be excluded. The
existing reference-note exclusions are also honored. Exclusions are session
state for the current project object, not persisted manuscript metadata.

Source bytes are verified before and after generation. While a ghost is visible,
file/directory notifications and a one-second worker verification invalidate it.
Notifications are advisory: explicit Tab starts another worker verification
before insertion, without relying on notification delivery. Esc, edits and
navigation discard that acceptance intent. This is snapshot verification, not
an atomic lock against an arbitrary concurrent external writer. Ordinary manual
and standalone completion retain their synchronous acceptance behavior.

Deadlines are cooperative; individual bounded file reads/SQLite operations and
synchronous HTTP calls finish before cancellation is observed. A generation
call may occupy the sole worker until its provider timeout even after an edit,
but cannot enqueue an unbounded backlog or apply stale text. The retrieval
deadline excludes generation and the optional post-Tab verification. Deadline
fallback recaptures mandatory context; it never borrows an old optional passage.

## Measurements and native evidence

Run `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/inline_retrieval.py`.
The [raw report](evidence/rag08/performance.json) records macOS 27.0.1 arm64,
Python 3.14.10, Apple M5 Pro / 24 GiB. The measured workload is slightly larger
than the predeclared approximate 10 KiB scenes: 100 earlier scenes of
12,100–12,210 UTF-8 bytes (1,219,900 bytes total), one target/open buffer,
20 warm samples per mode, four optional passages, a 3,522,560-byte index.
The initial warm-up in each mode is excluded; no ranking or deadline tuning
was performed after measurement.

| Mode | Retrieval median / p95 | Fake-provider end-to-end median / p95 | Cache hits |
| --- | --- | --- | --- |
| Repeated query, verified cache | 33.06 / 34.22 ms | 72.08 / 76.76 ms | 20/20 |
| Distinct query, ready lexical index | 168.50 / 180.49 ms | 206.59 / 223.37 ms | 0/20 |

Both retrieval p95 values meet the 250 ms target on this machine. The separate
generation column in the raw report includes before/after source verification
and a fake provider returning immediately. This is not a live-model latency
measurement and excludes typing debounce, Qt rendering and post-Tab verification.
These synthetic timings are diagnostic, not portable performance guarantees.

Direct Cocoa test: real typing/debounce, real context inspection dismissed with
Esc, Tab after worker verification, Undo, Esc rejection, cursor movement and
tab switching while a fake provider is blocked. A queued GUI callback ran after
1.314 ms while that provider remained blocked. Typing-to-visible-suggestion
latency was 129.451 ms, including the 100 ms debounce and the Qt dispatch/render
path, with the immediate fake provider. [Native output](evidence/rag08/native.txt)
records 1 passed / 29 deselected in 0.68s. This is direct Qt/native automation,
not a human accessibility audit or live-model quality/latency evaluation.

## Gate coverage and reproduction

| Criterion | Regression evidence |
| --- | --- |
| Route only opted-in bound scenes; preserve standalone/manual | `test_non_opted_paths_keep_ordinary_completion`, unknown-window refusal |
| Debounce/coalesce/bound work | Real typing test; blocked provider retains only last pending intent; cached-only vector test; performance report |
| Verify cache scope/policy/current text | Query/exclusion/policy/buffer/disk/index/embedding invalidation, installed-digest replacement and incomplete-capture refusal |
| Deadline/unavailable/no-hit behavior | Injected clock on misses and hits; mandatory timeout skips; cancellation never downgrades; deleted index and empty query hits |
| Consent, exact inspection, exclusions | Non-modal remote decline/approval/settings invalidation; inspection compares exact sent prompt; future exclusion rebuild |
| All stale triggers and explicit acceptance | Edits, cursor, selection, tab, project, settings, disk, background scene/note buffers, cancel, late error and older-worker/newer-manual-request tests; Tab re-verification and Esc during pending acceptance; Undo |
| Native V2 | Real Cocoa walkthrough and separately reported callback/typing latency above |

Focused offline command:
`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_inline_context.py tests/test_inline_retrieval_ui.py tests/test_rag_embeddings.py tests/test_negative_scenarios.py tests/test_rag_completion_ui.py tests/test_settings.py tests/test_editor_widget.py tests/test_i18n.py`.

Full command: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`.
Native command: `QT_QPA_PLATFORM=cocoa PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -xqs tests/test_inline_retrieval_ui.py -k native`.

Final frozen-source results: focused 234 passed / 2 native-only skips in 54.01s;
full offscreen 1,515 passed / 7 expected skips in 278.08s (four live, three native).
Native RAG-08 is recorded separately above. Initial full runs found and resolved
English-catalog shadowing of Ukrainian translations and shutdown of a partially
initialized window; both regressions pass in the final full run. The English
catalog stays intentionally partial, with only this task's new strings added.

## Completion review

- Intent: bounded automatic capture, request cache and explicit acceptance have
  distinct names and ownership; no speculative provider abstraction was added.
- Ownership: project context/cache/deadline rules stay in project services;
  the UI captures widget state and queues workers; HTTP stays in OllamaClient.
- Safety: dirty buffers, source precedence, generation guards, consent, explicit
  acceptance and Qt Undo remain; no manuscript/index rebuild occurs while typing.
- Errors: deadline, missing index/vector, unavailable embedding and source-change
  states skip or disclose fallback; obsolete provider errors cannot apply text.
- Tests: deterministic clocks/providers cover cache/policy/source invalidation,
  bounded scheduling and late replies; native evidence is reported separately.
- Diff: changes are limited to RAG-08 owners, tests, translations and documentation;
  no dependency, formatter, unrelated bytecode or local settings are included.
- Report: benchmark and native scope are explicit; full-suite outcome is recorded
  in IMPLEMENTATION_PROGRESS.md; RAG-09 onward and the RAG parent remain open.
