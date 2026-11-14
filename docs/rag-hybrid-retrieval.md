# RAG-06: optional hybrid retrieval

The manual RAG completion command can combine lexical and semantic passage
ranking. It stays opt-in and off by default. Generation uses its existing
host/model; embeddings have separate settings, defaulting to localhost and
`embeddinggemma`, selected after the measurements below. Other workflows retain
their existing context policies until their integration tickets.

| Criterion | Preconditions | Failure/stale coverage |
| --- | --- | --- |
| Model selection | Recorded lexical pilot and predeclared thresholds | Same versioned English/Ukrainian corpus, raw failures, resource/deployment measurements; no claim of held-out accuracy |
| Provider | Separately confirmed destination, installed embedding-capable model | Mutable tag/digest checks before/after batches; malformed vectors, dimensions, nonfinite/zero values, timeout, no automatic model pull or host switch |
| Saved cache | Current captured chunks, matching model identity and policy | Changed model/digest/host/dimensions/chunk policy regenerate; corrupt/nonregular/oversized cache falls back; unsaved vectors never persisted |
| Ranking | Eligibility/exclusions/chronology applied first | Deterministic RRF/ties/diversity, semantic-only hits, no-query/unavailable distinctions, visible lexical fallback |
| Async safety | Worker-only provider/cache operations | Cancellation, source/manifest/index changes, UI snapshot/generation checks, no partial cache publication, stale buffers/results/errors discarded |

## Provider and consent

`EmbeddingProvider` is separate from `AIProvider`; the Ollama implementation is
in `app/ai/ollama_client.py`. The server `/api/tags` inventory and `/api/show` metadata
must identify an installed model digest, embedding capability and native
embedding length. Generation models are never assumed to support embeddings.
`/api/embed` receives bounded batches with `truncate: false`. Returned model,
row count, dimensions and finite nonzero numeric vectors are validated; vectors
are normalized. Identity is rechecked around each batch and at the end of the
retrieval operation. There is no smaller-window retry, automatic pull or
alternate configured destination on failure.

The UI confirms the embedding host/model **before** capture sends query/source
text, including any eligible open unsaved text. This consent covers rebuilding
that same review session and any newly included eligible sources. Declining
cancels the command. Enabling the checkbox alone sends nothing. The generation
destination and exact captured role/prompt still need their separate source
review and Send action after retrieval. Embedding requests/responses remain in
AI diagnostics, just like generation; they can contain manuscript text. No
manuscript is sent by the benchmarks or offline tests.

Model-specific query/document formatting is versioned. EmbeddingGemma uses its
retrieval query/document prefixes; Qwen uses a retrieval instruction on queries
and raw document text. Other explicitly selected models receive raw text; their
quality is not established by this pilot. No input is silently shortened by the
embedding endpoint. The semantic query assembled from bounded author input,
nearest passage and associated names is capped at 4096 UTF-8 bytes, with a
manifest notice when limited; required generation context remains unchanged.

## Ranking and bounded cache

The lexical service remains authoritative for source scope and validated chunk
provenance. Eligible current chunks are checked against the captured project
before any embedding calls; excluded/current/future/unplaced scenes retain the
existing chronology policy. Explicit scene-character associations remain
mandatory; a semantic match cannot establish presence or knowledge.

Semantic candidates use normalized cosine similarity, minimum **0.35**, at most
20 candidates. Lexical and semantic rank lists combine with equal-weight
reciprocal-rank fusion, constant **60**. Ties use stable source/chunk IDs and
existing manuscript-source diversity, overlap removal and whole-request budget
logic. These values were fixed in the pilot corpus before either live model run;
they are not tuned on its answers. The review manifest identifies `hybrid` or
`lexical_fallback`, the actual embedding identity/digest, cache hit/new-vector
counts and failure notices. Hybrid selection records `hybrid_match` reasons.
No hits or similarity scores prove absence of evidence or project consistency.

The first release allows **512 eligible chunks**, native dimensions up to
**4096**, batches of **8**, input limits **8192 UTF-8 bytes per text / 32768 per
batch**, 30-second HTTP timeout in the UI, and **16 MiB per scoped vector cache**.
Over-limit captures/requests use the disclosed lexical fallback rather than
silently embedding a partial project. Missing/unavailable lexical indexes also
use the existing disclosed mandatory-only path, without embedding calls.

`app/project/rag_embeddings.py` maintains a sibling SQLite vector file under the
same outside-project `retrieval/` scope as the lexical index. Its metadata and
keys bind host, model/tag and weight digest, native dimensions, formatting
version, current chunk IDs/content/metadata and chunking policy. A different
identity invalidates cached entries. Only current saved-source vectors are
published; open-buffer vectors and query vectors remain request-local, even
when buffer text equals disk. No raw source text is stored in the vector file
(the separate lexical cache already contains saved text). Cache loss is harmless.

Publication writes a private SQLite file and atomically replaces the scoped
cache only after all batches, query embedding, identity checks and source/index
verification succeed. Cancelled/partial/invalid responses preserve the previous
cache. Writes and Delete Cache share the lexical scope lock. Delete Cache removes
both caches and scoped staging files, without touching project files; it is not
secure erasure. Refresh/Rebuild maintains the lexical cache; vectors rebuild
lazily on the next approved hybrid request. The cache retains only the current
bounded saved candidate set; changes in exclusions can regenerate vectors later.

Source verification includes all captured disk/manifest stamps and buffer
snapshots; the UI additionally checks fresh editor revisions and project/settings
and completion generations. Synchronous HTTP already in progress cannot be
interrupted; cancellation discards its eventual result. Fingerprint checks detect
observed changes rather than locking arbitrary external writers. A write after
the final check is outside that check's guarantee. Model metadata checks likewise
detect observed tag changes; they do not lock server model definitions. This does not change Undo,
save conflict behavior, explicit manuscript acceptance or transactions.

## Model-selection evidence (2026-11-14)

The [pilot corpus](../benchmarks/data/retrieval-pilot-v1.json) contains 16 short
synthetic reference sources, six positive queries per language (including
cross-language examples), and two absent-evidence queries per language. Stable
UUIDs derive from source keys. It is a **model-selection pilot**, not RAG-07's
held-out manuscript quality gate. Lexical baseline ran first. Preconditions in
the corpus were fixed before live comparison: recall@3 at least 0.75 per language,
warm-query p95 below 2 seconds and installed model below 1 GB. Selection ranks
mean recall@1, then recall@3, then warm latency and installed size. No thresholds
or corpus answers were changed after observing model results.

| Production ranking path | EN recall@1 / @3 | UK recall@1 / @3 | EN / UK precision (≤3 returned) | Absent queries with candidates | First query | Warm p95 |
| --- | --- | --- | --- | --- | --- | --- |
| Lexical | 0.50 / 0.50 | 0.50 / 0.50 | 0.417 / 0.417 | 0 / 4 | 13.5 ms | 13.6 ms |
| Hybrid EmbeddingGemma | 0.833 / 1.00 | 1.00 / 1.00 | 0.750 / 0.722 | 0 / 4 | 1.335 s | 128 ms |
| Hybrid Qwen3 0.6B | 0.833 / 0.833 | 0.833 / 1.00 | 0.417 / 0.417 | 4 / 4 | 3.965 s | 103 ms |

The raw `precision_at_3` metric divides by the number actually returned (up to
three), without padding missing candidates; it is not precision with three
fixed result slots. EmbeddingGemma wins the predeclared mean-recall priority.
Its English top-1 failure was query `en6`: the Night Fox guide ranked above
the relevant Grey Owl source, which was recovered in top-3. Qwen's top-3
failure was also `en6`, the cross-language Grey Owl query; its `uk3` warning
signal query recovered the correct source only in top-3. All per-query candidates, notices,
prompt byte counts and timings are preserved in the raw reports; this small
sample does not establish real-world recall or universal abstention.

Both models were downloaded only after explicit user approval. On this Apple
M5 Pro / Mac17,8 machine with 24 GiB RAM, macOS 27.0.1 arm64 and Ollama 0.40.13:

| Model / digest prefix | Native dimensions | Installed bytes | Observed Ollama loaded / VRAM bytes | Pilot vector cache |
| --- | --- | --- | --- | --- |
| embeddinggemma:latest / 85462619ee72 | 768 | 621,875,917 | 685,642,874 | 81,920 bytes |
| qwen3-embedding:0.6b / ac6da0dfba84 | 1024 | 639,150,858 | 2,749,754,245 | 90,112 bytes |

Full digests and runtime observations are in
[environment.json](evidence/rag06/environment.json). Loaded/VRAM values are
server observations on unified-memory hardware, not a portable RAM minimum or
process peak. Model-loading state and other running models affect latency;
first-query timing includes vectorization of all 16 sources, not generation.
The p95 is the nearest-rank statistic of the remaining 15 queries, not a
representative workload distribution. There is no monetary API charge assumed
for these localhost tests; storage, download and compute costs still apply.

The offline [resource probe](../benchmarks/vector_cache.py) measured 512 vectors
at 768 dimensions: 2,154,496-byte SQLite file, 29,289,208-byte traced Python peak
while constructing/writing/reading vectors, 11.5 ms median and 13.4 ms maximum
exact cosine scan over ten runs. This supports SQLite plus a bounded exact scan
for this initial scope; no ANN/vector-database dependency is justified by these
measurements. It is not a bound for 4096-dimensional models or whole-app memory.

Raw evidence:
[lexical](evidence/rag06/lexical.json),
[EmbeddingGemma](evidence/rag06/embeddinggemma.json),
[Qwen](evidence/rag06/qwen3-embedding-0.6b.json),
[vector resources](evidence/rag06/vector-resources.json).
Reproduce the offline baseline or explicitly invoke synthetic live comparisons:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_pilot.py --output /tmp/lexical.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_pilot.py --live --host http://localhost:11434 --model embeddinggemma --output /tmp/embeddinggemma.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_pilot.py --live --host http://localhost:11434 --model qwen3-embedding:0.6b --output /tmp/qwen.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/vector_cache.py
```

The opt-in live gate uses only temporary synthetic project sources and the
configured **embedding** host/model, without changing saved settings:

```bash
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 UTEXTEDITOR_LIVE_EMBEDDINGS=1 .venv/bin/python -m pytest -qs tests/test_live_embeddings.py
```

RAG-06.V2 passed on the selected model/digest above: **1 passed in 0.94s**;
initial capture/index/query 410 ms and warm repeat 73.3 ms, 24,576-byte cache.
The warm run reused two saved vectors without rewriting cache bytes. Log:
`/private/tmp/utexteditor-rag06-final-live.log`. This verifies the embedding endpoint,
bilingual retrieval and warm cache, not live generation or a native GUI gate.

API/format sources (primary documentation):
[Ollama embed contract](https://docs.ollama.com/api/embed),
[Google model card](https://huggingface.co/google/embeddinggemma-300m),
[Qwen model card](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B).

## Completion review

- [x] Intent: separate embedding identity, provider, semantic ranking and cache responsibilities.
- [x] Ownership: HTTP/payload parsing stays in OllamaClient, retrieval/cache in project services and Qt in UI.
- [x] Safety: no manuscript writes, explicit destinations, mandatory associations, immutable reviewed context, stale/cancel checks and Undo retained.
- [x] Errors: invalid/partial batches and cache failures disclose lexical fallback; cancellation remains cancellation; no silent model/destination substitution.
- [x] Tests: focused and full offline tests plus separately invoked live embedding gate; exact results in IMPLEMENTATION_PROGRESS.md.
- [x] Diff: scoped new code, no dependency, automatic download or unrelated refactor; documentation/catalogs updated.
- [x] Report: pilot failures, measurement conditions and filesystem/live/native limits stated; RAG parent remains open.

Final RAG-06 verification: focused 204 passed / 1 native-only skip (52.29s),
full offscreen 1443 passed / 4 expected skips (211.27s), separately invoked
live embedding smoke 1 passed (0.94s). Ukrainian catalog validation passed:
1085 finished entries, 1072 extracted source strings. `git diff --check` passed.
RAG-06, RAG-06.V1 and RAG-06.V2 are COMPLETE; the RAG parent remains OPEN.
