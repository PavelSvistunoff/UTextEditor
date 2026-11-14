# RAG-02 source capture contract

This ticket supplies a worker-only capture/chunking service, not an index or a
change to prompts. RAG-01 is complete. Source captures may be incomplete, but
must carry explicit diagnostics; callers must not present partial coverage as
complete. No source manuscript, manifest or disk index is written.

| Criterion | Preconditions | Failure and stale-state checks |
| --- | --- | --- |
| Provenance | Valid opened project, same manifest on disk, stable source IDs | Missing/unreadable/binary/escaping paths, changed manifest, duplicate titles, foreign buffers |
| Chunking | Positive bounded chunk size, overlap smaller than size | Empty/long paragraphs, English/Ukrainian, exact offsets, deterministic identities and coverage |
| Character fields | Existing validated textual profile | Field boundaries preserved, portrait excluded, relationships captured separately |
| Buffer authority | Explicit immutable text/revision captures | Overlay beats disk; oversize buffer never falls back to disk; buffer/disk changes invalidate capture |
| Resource limits | Explicit source, byte and chunk limits | Incomplete flag and explicit source omissions/counts; cancellation raises before publishing |

Scene/note offsets refer to the exact decoded source (including original line
breaks). Character offsets refer to a canonical textual snapshot rendered one
semantic field per section, not positions in YAML. Each chunk carries source ID,
project ID, source type/title/path, content and metadata fingerprints, manuscript
order and buffer revision through its source record. Manuscript order is not
proof of plot chronology. Association metadata stays attached to scene sources;
RAG-12 is responsible for making it mandatory in final provider payloads.

Disk snapshots remain separate from effective buffer-overlaid snapshots so a
future index writer cannot accidentally persist unsaved text. UI callers must
capture widget text/revisions on the GUI thread and pass plain values to workers;
verification accepts a fresh plain buffer map, never reads Qt widgets itself.

Default limits: 1 MiB per source, 16 MiB combined disk/overlay text, 10,000 sources,
20,000 chunks, 1,200 characters per chunk and up to 160 overlap characters.
Metadata also counts toward the total byte limit. Character fields and paragraph ends
are preferred boundaries; an oversized paragraph is split without normalizing
text. Partial coverage is recoverable by increasing explicit limits or reducing
the corpus, not by silently reporting success.

Project reopening retains existing path validation: escaping paths and
non-regular referenced files refuse the capture as a whole. Missing, oversized
or invalid-text sources otherwise produce explicit incomplete-coverage records.
The source-count cap reports the number of remaining omitted sources without
rendering their content. The chunk cap aborts a source before constructing
unbounded chunks. Cancellation aborts the whole capture even if signaled only
once. Default corpus limits do not claim bounded memory for the application's
existing manifest loading or for text the UI already holds.

## Completion evidence

- RAG-02 and RAG-02.V1: COMPLETE; the RAG parent remains OPEN.
- Focused command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_rag_sources.py tests/test_project_domain.py tests/test_project_setup.py tests/test_context_budget.py tests/test_project_analysis.py`:
  152 passed in 2.55s; log `/private/tmp/utexteditor-rag02-focused.log`.
- Full offscreen command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  1286 passed, 2 live-only skips in 167.28s; log
  `/private/tmp/utexteditor-rag02-full.log`.
- Tests cover exact Unicode/CRLF offsets, paragraph/field boundaries, duplicate
  titles, project isolation, disk versus buffer provenance, portrait exclusion,
  relationship direction, metadata-only invalidation, stale captures, missing/
  unreadable/invalid sources, path refusal, work limits and cancellation.
  The source test module has 38 passing cases.
- Clean Code checklist reviewed: intent (typed source/chunk/buffer captures);
  ownership (worker-only project service); safety (no manuscript/cache writes,
  authoritative buffers and path validation); errors (explicit partial coverage
  versus abort); tests (normal/failure/stale cases and full suite); diff (scoped
  foundation, no dependency or unrelated rewrite); report (no claim of delivered
  retrieval or live/native evidence). `git diff --check` passed.
- No UI behavior, live AI or native accessibility gate is introduced by this
  service-only ticket. Model payload association coverage remains RAG-12 work.
