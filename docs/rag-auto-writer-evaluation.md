# RAG-07: evaluated manuscript retrieval for Auto-writer

Auto-writer now has an optional **Review retrieved manuscript passages before
each scene request** checkbox. It is off by default, requires an explicit
positive Ollama token window, and uses the existing project Retrieval Index.
Refresh that index first. A missing/unavailable index is disclosed in review
and does not silently select another project. Ordinary Auto-writer and the
remaining AI workflows retain their existing paths.

| Criterion | Preconditions | Failure/stale evidence |
| --- | --- | --- |
| Frozen evaluation | Versioned EN/UK facts, aliases, distractors, later/unplaced traps and absent-evidence questions | Corpus hash and numerical gates frozen before live evaluation; development and heldout reports separate |
| Complete required context | Existing complete-note/profile capture and 64 KiB limit, full refinement scene within existing 16,000-character limit | Oversized/missing references or request-budget overflow refuse without dropping required material; snapshot retained |
| Author review | One captured role/prompt/destination per target scene | Rebuild after optional scene exclusions; Cancel sends no generation; required references cannot be excluded |
| Sequential generation | Earlier generated scene drafts overlaid in memory | Full generated draft can supply distant passages beyond the old 1000-character prefix; provisional IDs/notice, no manuscript/index/vector persistence of drafts |
| Source-backed presentation | Exact snapshot offsets, digests, text and included manifest decisions | Quote/offset/manifest tampering and unsent source evidence reject; Unicode and CRLF preserved |
| Async and commit safety | Existing snapshot, editor/project/settings generations and worker pattern | Source changes before/during generation, obsolete errors, cancellation, generation failure and transaction rollback preserve author data |

## Workflow and ownership

The existing `run_auto_writer` still captures every required reference note in
full, all textual character profiles, directed relationships and recorded
scene development as background. Portraits stay excluded. The full current
scene remains mandatory in refine mode; the existing outline and preceding
excerpt limits are unchanged. Explicit target associations still establish
presence; other profiles and retrieved scenes are background, not proof that a
character is present or knows a fact. Global profile/history guidance is not a
verified projection at that story point; CHAR-DEV-01 and RAG-12 remain separate
work. The complete-reference 64 KiB refusal remains in force before generation.

After the pre-run revision snapshot is created, `AutoWriterRetrieval` constructs
a shared `ProjectContextService` request in the worker. The existing complete
Auto-writer prompt is retained as mandatory captured project data. The trusted
role states the writing/refinement task and author instructions outside that
data. The target title precedes style instructions in the bounded query so
lengthy generic guidance cannot crowd out the scene subject. Optional retrieval
uses only earlier **grouped manuscript** scenes; later, current and unplaced
scene passages are excluded. This is manuscript ordering, not proof of story
time; required global background and outline titles may still describe later
material. A zero-violation result below refers to optional retrieved passages.

`AutoWriterContextReview` bridges the synchronous worker to queued Qt source
reviews, waiting on a cancellable Event off the GUI thread. The review displays
the exact prompt and role, actual generation host/model, token estimates,
source decisions/ranges/digests, buffer revisions and coverage notices. Its
checklist excludes only optional scene sources. Full reference notes/profiles
remain in the mandatory prompt even though their optional-search decisions say
`source_kind`; the dialog states that distinction explicitly. Rebuild captures a
new request against the same pre-run disk baseline; changed baseline data
requires restarting the run. Cancelling or stale UI state rejects the review.
Dialogs/bridges are released after use; old callbacks cannot cancel a newer run.

The optional embeddings checkbox is independent of manual-completion settings
and defaults off. It has a separate host/model confirmation before sending
queries or eligible scene text, including unsaved/provisional draft text. No
model is downloaded. Declining aborts this run. The generation confirmation
specifically describes **generation**, and each source review is still required
before generation even if embeddings were previously authorized. Requests are
visible in AI diagnostics. Hybrid failures retain the existing visible lexical
fallback and resource limits from [RAG-06](rag-hybrid-retrieval.md).

Before every target, approved earlier generated scenes replace their original
scene text only in the request-local overlay corpus. The full draft is chunked,
not its old 1000-character preceding excerpt. Those source IDs are explicitly
marked provisional/unaccepted in mandatory input and source-review notices.
Their buffer revision is 1; captured author buffers use 0 within this worker
snapshot, while the UI independently retains actual editor revisions. Neither
lexical indexing nor vector publication persists these overlays. Ungrouped
working drafts remain ineligible under the default ordering policy. Later
requests may depend on earlier drafts that the author ultimately rejects; the
final selection dialog keeps that warning.

Captured disk sources must match the pre-run scene/note baseline, including
sources not selected as optional passages. Every source and the manifest are
verified after source review, before dispatch and after generation/error.
Editor revisions, bindings and project/settings/run generations guard the UI
and worker cancellation predicate. These predicates read only plain Python
state; widget access and dialog execution stay on the GUI thread. An in-flight
synchronous network call may finish after cancellation, but its result is
ignored. Obsolete provider failures after author edits are also discarded;
those edits and their Qt Undo history survive.

The final draft review shows verified passage records from the **exact sent
request**, rather than rereading a source and attributing different text to an
older request. `rag_evidence.py` checks sent ranges, original captured source
text/digests, chunk provenance and included/shortened decisions. `validate_quote`
additionally rejects finding quotations outside sent spans. Offsets are Python
Unicode code points in the original source text, including preserved CRLF.
This validates input evidence, not factual correctness or grounding of every
sentence the model generates. No project-wide consistency finding is inferred.

Only compact immutable role/prompt/manifest/verified-passage records survive for
final review; the entire source corpus is not retained separately for every
draft. A **16 MiB estimated serialized request-review budget per run** refuses
oversized staged reviews before another generation call. This is not a bound
on all Python/Qt memory. Required input is never cut to meet it. The existing
80-target, 16,000-character refinement and 30,000-character output limits remain.
RAG source-capture limits also apply. If an original disk baseline source cannot
be captured completely, retrieval mode refuses instead of mixing snapshots.

Final selection uses the unchanged transactional scene replacement, expected
scene/reference contents and rollback machinery. No staged draft is applied
if generation fails, context changes or the author cancels. Pre-run snapshots
remain available. Filesystem/metadata checks detect observed changes; they do
not lock out arbitrary external writers or provide a cross-process compare-and-
swap. A later external write after a final check lies outside that check's
guarantee. Snapshot/rollback safety is not a general arbitrary-writer save claim.

## Frozen evaluation protocol and results

The [version-1 corpus](../benchmarks/data/retrieval-evaluation-v1.json) has 20
queries: eight positive development queries, eight distinct positive heldout
queries and two absent-evidence queries per split, evenly divided EN/UK.
It contains 20 earlier scenes (including distractors and the last-two fixed
context), a target, two later chronology traps, an unplaced trap and two
associated alias profiles used by development cases. Expected source keys
are recorded per query; stable UUIDs derive from those keys. It is synthetic,
not a representative manuscript sample or a guarantee of general recall.

The [protocol/hash](evidence/rag07/protocol.json) was recorded before live model
runs. RAG-06 cosine >=0.35, top-20 semantic candidates and equal RRF60 stayed
unchanged. No ranking parameters or corpus labels were tuned after seeing
heldout results. Development ran first; the hybrid heldout set was evaluated
once. Heldout thresholds: recall@3 >=0.75 and fixed-three-slot precision@3 >=0.20
per language; no recall regression versus lexical; zero later/unplaced optional
passages; 100% validated sent passage records; absence warnings on every absent
query; warm-query p95 <=2 seconds; vector cache <=16 MiB. The
[gate checker](../benchmarks/check_retrieval_evaluation.py) passes all 19 checks
and rejects a simulated heldout recall regression in offline tests.

| Strategy | Development EN/UK recall@3 | Heldout EN/UK recall@1 and @3 | Heldout EN/UK precision@3 | Optional chronology violations | Heldout absent cases with candidates |
| --- | --- | --- | --- | --- | --- |
| Existing fixed last-two / first-1000 policy | 0 / 0 | 0 / 0 | 0 / 0 | 0 | 2 / 2 |
| Lexical | 1.00 / 1.00 | 1.00 / 1.00 | 0.333 / 0.333 | 0 | 2 / 2 |
| Hybrid EmbeddingGemma | 1.00 / 1.00 | 1.00 / 1.00 | 0.333 / 0.333 | 0 | 2 / 2 |

Each positive query has one relevant source; precision@3 uses three fixed slots,
unlike RAG-06's variable-return precision metric. Fixed context omits these
distant plot facts by construction. The fixed baseline has no structured sent-
passage validator (reported validated fraction 0 denotes absent instrumentation,
not that its literal excerpts are false). Both retrieval modes validate all
sent evidence and show the partial-retrieval warning for absent cases.

**Published failures:** heldout `h_absent_en` retrieves the unrelated development
guide `d_en_alias`; `h_absent_uk` retrieves `d_uk_alias`. Both lexical and hybrid
make these false candidate matches. Development absent queries return no
candidates. Thus this corpus demonstrates distant-context recovery and policy
filtering, with **no incremental recall benefit from hybrid over lexical here**;
it does not establish perfect recall or reliable absence detection. The smaller
[RAG-06 model-selection pilot](rag-hybrid-retrieval.md) measured different,
more paraphrased/cross-language cases. Further tuning needs a fresh heldout set.

| Measured context strategy | Warm heldout p95 EN / UK | Maximum heldout context prompt bytes EN / UK | Lexical cache | Vector cache |
| --- | --- | --- | --- | --- |
| Fixed | 0.12 / 0.09 ms | 207 / 207 | 0 | 0 |
| Lexical | 18.0 / 18.2 ms | 1762 / 1856 | 90,112 B | 0 |
| Hybrid | 103.8 / 108.0 ms | 1790 / 1884 | 90,112 B | 98,304 B |

Timings cover capture/ranking/verification in the minimal evaluation harness,
exclude generation and initial indexing, and omit the first cold query from
p95. The recorded byte metric is the rendered **manuscript context segment** in
this harness, excluding HTTP framing and the full production Auto-writer
outline/reference prompt. Full mandatory production material is verified in
separate end-to-end tests and charged to the complete request budget. These
small timings/sizes are not predictions for a full Auto-writer run. Reported
precision/recall are source-selection metrics, not narrative quality scores.

Hardware: Apple M5 Pro, 24 GiB, macOS 27.0.1 arm64; Ollama 0.40.13. Embedding
model `embeddinggemma:latest`, digest `85462619ee72…`, native 768 dimensions.
Complete IDs, raw per-query sources/times/request sizes/cache costs and gates:
[environment](evidence/rag07/environment.json),
[fixed](evidence/rag07/fixed.json), [lexical](evidence/rag07/lexical.json),
[hybrid development](evidence/rag07/hybrid-development.json),
[hybrid heldout](evidence/rag07/hybrid-heldout.json),
[gates](evidence/rag07/gates.json).

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_evaluation.py --mode fixed --split all --output /tmp/fixed.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_evaluation.py --mode lexical --split all --output /tmp/lexical.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_evaluation.py --mode hybrid --split development --live --output /tmp/development.json
# A heldout rerun is reproduction, not a fresh independent test after tuning:
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/retrieval_evaluation.py --mode hybrid --split heldout --live --output /tmp/heldout.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/check_retrieval_evaluation.py
```

## Separate native and live gates

The direct macOS Cocoa test executes real Auto-writer options, per-scene source
review and final selection dialogs using keyboard events. It checks Esc
cancellation without generation, optional-source Space toggles, disabled Send
until an actual Rebuild, Return to send and selective final Apply. A companion
native test checks the unchanged manual RAG Tab/Esc path. Providers are fake;
this is native widget automation, not screen-reader or live-model verification.

```bash
QT_QPA_PLATFORM=cocoa PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_auto_writer_retrieval_ui.py tests/test_rag_completion_ui.py -k native
```

The separately invoked live generation smoke uses the configured generation
host/model, a temporary synthetic project, lexical distant-scene retrieval,
pre-run snapshot, exact reviewed/sent request equality, staged results and
transactional application. It changes no saved settings. If the configured
window is server-default/unknown, only the test's provider explicitly requests
8192 tokens. It does not validate live hybrid generation through the GUI;
hybrid embedding behavior is separately measured above and integrated with
fake providers in offline Auto-writer tests.

```bash
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 UTEXTEDITOR_LIVE_RAG_AUTOWRITER=1 .venv/bin/python -m pytest -qs tests/test_live_auto_writer_retrieval.py
```

The live smoke passed: **1 passed in 4.14s**, Auto-writer run 4.06s, 25 output
characters, one validated distant source. Destination `http://localhost:11434`,
model `gemma4:12b`, digest `c7597fc90b86…`, requested 8192-token window. It first
caught the title-query starvation issue caused by long style instructions; title
priority was corrected and has an offline regression. It is a smoke test, not a
model-comprehension or output-quality guarantee. Log:
`/private/tmp/utexteditor-rag07-live.log`. Exact offline/native totals and resume
pointer are recorded in `IMPLEMENTATION_PROGRESS.md`.

## Completion review

- [x] Intent: source capture/review, provisional overlays and verified evidence have explicit names and responsibilities.
- [x] Ownership: domain rules/persistence stay in project services, Ollama protocol in its provider, queued dialogs in UI.
- [x] Safety: full mandatory context, snapshots, transactional rollback, dirty text/Undo, destination disclosure and stale/cancel checks preserved.
- [x] Errors: no silent truncation; invalid evidence and changed snapshots refuse; obsolete provider failures do not override newer author state.
- [x] Tests: focused/full offline, separate direct native and explicit live gates; failures and measurement limits published.
- [x] Diff: scoped changes, no dependency, no automatic model downloads, docs/English and Ukrainian overview/catalogs updated.
- [x] Report: evaluation is bounded synthetic evidence; RAG-08–12/CHAR-DEV-01 stay open and no whole-project consistency or arbitrary-writer safety claim is made.

Final verification: 1469 passed / 6 expected skips in the full offscreen suite
(262.69s), focused 127 passed / 2 native-only skips (101.50s), final domain/gates
19 passed (1.48s), UI/locale 36 passed / 1 native skip (23.00s). Final direct
Cocoa walkthrough: 2 passed / 35 deselected in 1.71s, with fake providers;
`/private/tmp/utexteditor-rag07-final-native.log`. The full suite log is
`/private/tmp/utexteditor-rag07-complete-full.log`. After closing the final RAG
review its context widgets are explicitly released; targeted UI/native checks
also cover this lifetime cleanup. Translation validation passed (1095 finished
entries, 1082 extracted strings), and `git diff --check` passed.
RAG-07 / RAG-07.V1 / RAG-07.V2 are COMPLETE; the RAG parent remains OPEN.
