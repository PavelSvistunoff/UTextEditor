# RAG-04 context retrieval and assembly contract

RAG-01–03 are complete. This ticket supplies the shared worker service; existing
UI/AI requests remain unchanged until their integration tickets. Both streaming
and ordinary generation can consume the same immutable rendered prompt.

| Criterion | Preconditions | Failure / stale tests |
| --- | --- | --- |
| Shared assembly | Explicit prompt layout, mandatory input and positive complete-request budget | Mandatory overflow refuses; standalone never queries a project index; final rendered prompt fits |
| Scene authority | Captured target scene and explicit associated profiles | Exact association records independent of hits; mentioned presence; excluded/missing mandatory sources refuse |
| Query | Author request, current passage and associated names/aliases | Bounded Unicode terms; long input flagged; text cannot execute instructions or SQL |
| Ranking/diversity | Current source fingerprints and valid chunk provenance | Deterministic ties, stale cache rows, distractors, repeated text, overlap and per-source limits |
| Source policy | Explicit exclusions, kinds and chronology | Excluded/future/unplaced/ambiguous scenes filtered before candidate ranking; no top-result starvation |
| Budget/provenance | Required data reserved before optional passages | Exact UTF-8 slicing, shortened/omitted reasons, data delimiters, no-hit versus unavailable index |

The service requires an explicit `ContextBudget`; it never infers a model window
from its name or assumes a server-default allocation. A frozen prompt layout
accepts context/language placeholders, with a fixed language value. Fully rendered
instructions, repeated placeholders, labels and data wrappers consume budget.
Callers must place author instructions in the trusted prompt layout and pass
captured story text as data. The raw mandatory text is preserved; explicit
`mandatory_source_ids` additionally copy those sources in full. An implicit
target scene contributes metadata and associations, while its workflow decides
whether mandatory prose is a paragraph, excerpt or complete scene.

Default scene policy retrieves scene/note passages only, at most eight passages
and two per source. Grouped scenes earlier in manuscript order are eligible;
current/later, ungrouped and explicitly ambiguous scenes are excluded. An unplaced
or explicitly ambiguous target gets no earlier-scene retrieval. Notes remain
background references. An explicit all-scenes policy can retrieve later/unplaced
material with labels. Manuscript order never proves story time or character
knowledge. Optional character profiles in scene workflows must also be explicitly
associated; retrieval cannot establish scene presence.

Author query and nearest current-passage words are bounded, with reserved room
for explicitly associated names/aliases. Query text is data. Lexical matching is
not semantic recall, stemming or proof that a fact is absent.
There are at most 32 weighted terms (16 name/alias slots, eight author words,
eight nearest-passage words); duplicate terms keep their highest weight. Weights
are 4/2/1 respectively. Text inputs are bounded to 4096 characters; terms to 128.
NFC and NFD query forms are searched for Unicode interoperability. Title scoring
uses at most 4096 characters per source. These are deterministic baseline rules,
not measured real-world retrieval quality; RAG-07 supplies that evaluation.
Request fingerprints include bounded effective query text and original input
lengths, not unbounded copies of ignored query tails. They also bind the prompt
layout, mandatory input, budget, source policy and context-policy version. UI
generation/revision checks remain required; this fingerprint does not replace them.

The index is read in one generation. A request-local in-memory allowlist checks
source fingerprints before ranking, so excluded/stale high matches cannot crowd
out eligible sources. Only current captured chunk IDs, offsets and text can be
used. Uncached/changed sources and buffer overlays use bounded in-memory lexical
matching against the same query; no unsaved text is written to the cache. Missing
or unavailable indexes yield mandatory context with an explicit unavailable
status, rather than silently scanning a different project or claiming no hits.

Optional passages are scored consistently from weighted query coverage, then
ordered deterministically and interleaved across sources. Selected overlap is
removed; repeated passages are skipped. A passage may use its largest remaining
contiguous nonoverlapping span and a budget-fitting prefix, always with exact
original source offsets and an explicit shortening reason. Mandatory sources
are never shortened by this service. Source decisions and fingerprints are
returned for review, including no-match, filtered, duplicate and budget omissions.

Target association records, bounded `character_context.py` output and its limited
flag are mandatory. Requests requiring complete bounded character details refuse
if that helper reports limiting. Retrieved scene passages carry their own scene
metadata as background, not target presence. Full cross-workflow provider-payload
verification remains RAG-12 work.
Global profile state is guidance, not verified state at a particular scene or
cursor point. Development history/projection correctness remains CHAR-DEV-01
work; document-order filtering alone cannot resolve it.

Untrusted source strings are JSON-encoded with escaped markup delimiters inside
a fixed data wrapper. This reduces delimiter confusion, not a guarantee that a
model resists prompt injection. The UI integration must still require consent,
capture generations/revisions, show exact sources and explicitly accept output.
The returned capture can recheck disk/manifest and fresh buffer stamps before
dispatch and after generation/review; unrelated captured changes conservatively
invalidate it too. No manuscript, undo state or existing model request is changed.

## Completion evidence

- RAG-04 and RAG-04.V1: COMPLETE. RAG parent remains OPEN; next RAG-05.
- Implementation: `app/project/rag_context.py`, frozen prompt layout in
  `app/ai/context_prompt.py`, and snapshot-filtered read-only lookup in
  `app/project/rag_index.py`. No dependency, manifest migration or UI string change.
- Focused command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_rag_context.py tests/test_rag_index.py tests/test_context_budget.py tests/test_rag_sources.py tests/test_completion_service.py tests/test_project_analysis.py`:
  132 passed in 1.62s; log `/private/tmp/utexteditor-rag04-focused.log`.
- Final full offscreen command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  1366 passed, 2 live-only skips in 174.61s;
  log `/private/tmp/utexteditor-rag04-final-full.log`.
- Tests cover alias/Unicode queries, pre-ranking exclusions and scope filters,
  future/unplaced/ambiguous scenes, cache corruption and changed-source fallback,
  unsaved-buffer authority, source diversity, exact overlap/budget shortening,
  mandatory-source refusals with diagnostics, prompt delimiters, exact budget
  boundaries, deterministic manifests, missing FTS5 and query snapshot concurrency.
- Clean Code checklist: intent (typed request/policy/manifest, explicit units);
  ownership (project rules in project services, prompt layout in AI, no HTTP/Qt
  inside retrieval); safety (no model calls, index/manuscript writes or undo edits,
  required sources retained, scope and stale checks); errors (explicit coverage,
  preserved capture diagnostics and cancellation); tests (normal/failure/stale
  and complete offline suite); diff (scoped changes, no unrelated refactor);
  report (estimation, lexical recall and chronology limits stated).
  `git diff --check` passed.
- Native/live/model-comprehension verification is not claimed or a RAG-04 gate.
  The frozen prompt is reusable by both generation modes; actual provider/UI
  wiring and acceptance/undo tests remain RAG-05/08–11. Full association payload
  coverage across those integrations remains RAG-12, not closed by these unit tests.
