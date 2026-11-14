# AI context policies and request budgets

RAG-01 contract, updated through RAG-11. The shared context service is integrated
into the opt-in workflows below; ordinary paths retain explicit bounded policies.
Infrastructure operations (model metadata/listing, connection, warm-up and
embeddings) never recursively retrieve project text.

## Verification preconditions and failure cases

Work from a captured project/document/settings generation; source content comes
from bound open buffers before disk. Closed sources must be rechecked where the
workflow supports snapshot verification. No background result may bypass the
existing stale/cancel/review checks. RAG integrations must extend those checks
to every included source and association, not just the target document.

RAG-01 tests exercise exact/one-over/tiny budgets, UTF-8 Ukrainian/English,
instructions and output overhead, invalid configuration, unknown/replaced model
metadata, unsupported options without fallback, analysis source starvation,
unsaved scene/note content, settings Cancel/Reset/Apply and provider replacement.
Existing default-path and stale-state tests remain regression gates. No live
model or native GUI behavior is inferred from these offline tests.

| RAG-01 criterion | Preconditions | Failure / stale-state verification |
| --- | --- | --- |
| Workflow matrix | Enumerate current UI/service provider call sites, including streaming and no-project paths | Matrix assigns explicit future integration and no-hit/no-project policy; no present RAG coverage claimed |
| Mandatory/optional policy | Capture selected scene/notes and explicit associated profiles | Long source starvation, limited profile details, unchanged summary scope; existing UI generation/source-revision guards remain exercised |
| Complete budget | Fully rendered role/prompt; positive token window/output reserve | Exact/one-over/tiny and Unicode tests, invalid units, long role/output overhead; no network call on estimated overflow |
| Provider configuration | Explicit saved window and architecture metadata from the configured destination | Unknown/malformed/replaced tags, requested capacity overflow, unsupported normal/streaming requests, cancellation during metadata, settings replacement without mutating old providers |
| Analysis allocation | Selected scene/notes/profiles fit character guard; open buffers override disk | Exact/one-over source boundaries, long scene cannot drop note/profile, evidence validation and stale analysis regression tests |

## Workflow matrix

Mandatory means the workflow's captured authoritative inputs, not an assertion
that every field of the whole project is transmitted. Future retrieval defaults
to disabled until explicitly enabled. Existing automatic-project-context settings
and note exclusions are retained; they are not consent to a new embedding host.
The current settings default for automatic project context remains unchanged.

| Workflow / integration | Mandatory input | Optional retrieval after integration | Chronology / exclusions | No-hit and no-project behavior |
| --- | --- | --- | --- | --- |
| Manual inline completion, RAG-05/12 | Current paragraph before cursor; explicit target associations and bounded profiles for project scenes | Earlier manuscript passages and allowed reference notes | Target scene presence only; completion note exclusions apply | Continue from captured mandatory context; standalone files use paragraph only |
| Automatic inline completion, RAG-08/12 | Same, subject to automatic project-context setting | Bounded cached passages | Same exclusions; never reuse stale metadata | Skip optional retrieval on timeout; skip suggestion if mandatory capture fails; no project means paragraph only |
| Free-prompt generation, streaming or not, RAG-09 | Author prompt and role | Explicitly enabled project sources; current scene/selection only if chosen | Task-specific scope, no implicit active-document attachment | Prompt-only generation remains available |
| Spelling/grammar, RAG-11 | Exact target text and language | Explicitly enabled names/terminology dictionary | No unrelated scene prose | Text-only checking; same offsets and validated corrections |
| Scene summary, RAG-10 | Retrieved mode: full selected scene/notes/associated profiles; ordinary mode: labeled scene excerpt | Reviewed earlier scene/note passages | Label contextual versus scene-only; required sources protected | Explicit mandatory-only fallback; project-bound scene required |
| Continuity, RAG-10/12 | Full selected scene, selected notes, associated bounded profiles; explicit links in RAG-12 | Additional evidence passages | Earlier facts for target-state claims; later comparisons must be explicitly labeled | Partial-coverage review, never a consistency guarantee; no project means unavailable |
| Empty character fields, RAG-10/12 | Current staged fields and **all** project notes | Relevant manuscript passages | Background evidence does not imply presence | Existing complete-note operation; requires project/profile |
| Scene-based character development, RAG-10/12 | Staged profile and selected associated scene excerpt | Supporting background passages | Only exact selected-scene evidence can support an arc update | Existing evidence-backed operation; requires project/profile/associated scene |
| Brief suggestions, RAG-09 | Author brief/template and compact motivation summary | Reviewed existing project scenes/notes | Separate source-backed records from marked inventions | Mandatory input only when no eligible facts/index exist |
| Outline planning, RAG-09 | Brief and existing compact motivation summary | Relevant project facts | Do not force background characters into scenes | Brief-only for a new project; existing summary remains bounded |
| Auto-pilot planning/drafting, RAG-09 | Brief, full outline metadata, compact characters, full generated plan and earlier transient drafts | Reviewed existing project passages | Proposed additions are not established facts; transient IDs/digests/text stay request-local and never enter the canonical index | Mandatory-only fallback with visible coverage; empty new projects supported; existing additive mode remains available |
| Auto-writer, RAG-07/12 | Instructions, bounded outline, **all** notes/textual profiles/relationships, target metadata, associations, current scene for refinement | Relevant earlier manuscript passages | Later development is not knowledge in an earlier scene | Retain existing full-reference operation; no silent reduced-reference fallback; project required |
| Translation, RAG-11 | Complete target item, direction and author-approved run-wide glossary | Reviewed lexical usage examples | Exclusions persist across items; examples are never extra output | Target/glossary only on no hits; current entry point requires a project |

Reviewed manual completion, Auto-writer, opt-in automatic retrieval and RAG-09
free-prompt/planning/Auto-pilot integration and opt-in RAG-10 analysis/character workflows are implemented. Ordinary free-prompt
generation remains prompt-only and unchecked planning retains its existing inputs.
The [RAG-09 gate report](rag-planning-autopilot.md) describes the explicit source
review, mandatory transient chain, budget refusal and pre-application checks.
[RAG-10 verification](rag-analysis-characters.md) covers exact sent continuity citations, full-note retention and selected-scene-only arc evidence.
Translation now optionally shares an approved glossary across the whole run and
reviews per-item usage examples. Manual spelling optionally reviews names and
note titles with a shared-service policy allowing no prose passages; automatic,
standalone and disabled dictionary checks remain target-only.
The [completed dispatch audit and RAG-11 gates](rag-translation-spelling.md)
list owning call sites, retries/streams, consent, exclusions and behavioral tests.
No project implies no scanning neighboring files, other tabs or other projects.
RAG-12 requires structured scene links independent of text/vector matches.
Actual plot time may differ from manuscript order; ambiguous chronology must be
labeled and handled conservatively by scene-writing policies.

## Refusal, coverage and authority

- All workflows refuse invalid/missing mandatory input, stale captures and
  unavailable required consent. Optional retrieval no-hit is not a failure by
  itself, but must be distinguishable from an unavailable or partial index.
- Selected-source continuity now refuses before provider invocation when its
  complete rendered source block exceeds `context_size` characters. Associated
  profiles use existing scene-scoped limits; if those cut details, continuity
  refuses rather than silently using an incomplete profile. This does not turn
  the bounded profile schema into a complete character biography.
- Ordinary summary uses a labeled excerpt; retrieved summary requires its full selected inputs and explicitly labels contextual scope. In ordinary mode, its truncation notice and the task
  instruction are extra prompt overhead, counted by the token budget when enabled.
- Other existing limits (10,000 completion-note characters, 5,000 scene-profile
  characters, complete-reference 64 KiB guard, scene/refinement limits) remain
  unchanged. Full-reference workflows refuse overflow instead of dropping notes.
- Enabling an explicit token window adds complete-request preflight to every
  chat path: completion, regular/private generation, streaming and spelling.
  Server-default mode intentionally has no local token-capacity assurance.
- No source can be silently omitted to satisfy a required-source contract.
  Retrieval may use only space left after mandatory content. Optional passages
  must carry source labels and coverage notices when integrated in RAG-04/12.

## Units and one complete-request budget

`context_size` is a Unicode character/code-point limit (64–65,536, default 2,048)
for selected workflow excerpts/source blocks. Reference-size guards measure
UTF-8 **bytes**, including serialized metadata where applicable. Neither is a
token count. `maximum_suggestion_length` and per-workflow output settings are
requested output **tokens**, not input context sizes.

`ollama_context_length` is the requested complete token window, configured in
AI Settings > Connection. Zero means server default. Positive values up to
1,048,576 are application-supported requests, not promised model capacity.

`ContextBudget` uses the fully rendered system role and user prompt, so author
instructions, XML-like delimiters, JSON profile text and retrieval labels all
consume budget. For the present two-message, text-only protocol:

```text
estimated input = UTF-8 bytes(system role) + UTF-8 bytes(rendered user prompt)
remaining = requested window - estimated input - 32 framing tokens
            - requested output tokens - 256 safety tokens
```

One token per UTF-8 byte is intentionally conservative for ordinary prose,
especially Ukrainian. This is an **estimate**, not a measured count or universal
tokenizer bound; custom chat templates/special tokens can exceed allowances.
Exact/zero remaining fits this estimate; negative remaining refuses without
trimming any prompt. Future retrieval must use this same remaining budget and
recheck the final assembled prompt. A tokenizer-aware replacement must report
its model/template identity and be independently verified before claiming exactness.

## Provider capability and runtime limits

With an explicit window, the worker checks `/api/show` for
`model_info.general.architecture` and that architecture's `.context_length`.
Unknown, malformed or insufficient capacity blocks generation; capacity is
never guessed from a model tag. Metadata is rechecked for each configured
request so replaced tags cannot reuse stale cached capacity.

The client then sends `options.num_ctx`, `truncate: false` and `shift: false`.
It never retries a rejected request with reduced context or silently removes
those controls. Metadata/HTTP errors are actionable but do not copy server
error bodies containing possible manuscript text. Streaming follows the same
budget/metadata/payload path; cancellation before or during preparation prevents
dispatch where observed. Existing UI generations discard late results.

These checks establish what was requested and advertised, **not** server
allocation, support for every control, exact tokenization or model comprehension.
A server may ignore options; metadata is architectural capacity, not available
memory. Native/live verification is separate. Inspect `ollama ps` when diagnosing
the allocated runtime context. Default connection testing remains a warm-up;
with an explicit window it checks reported capacity and sends that window in
the empty warm-up request. This can detect a rejected option, but does not
certify that a full manuscript request fits or that the server honored it.

Official protocol references: [chat API](https://docs.ollama.com/api/chat),
[model metadata schema](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml),
[context configuration and runtime inspection](https://docs.ollama.com/context-length).
RAG-01 verifies client behavior offline, not the implementation of a running server.

## RAG-01 completion evidence

- RAG-01 and RAG-01.V1: COMPLETE; RAG parent remains OPEN.
- Focused UI/AI/i18n suite: 471 passed. Final focused selection after review:
  120 passed, 289 deselected.
- Final complete command:
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`:
  1248 passed, 2 skipped in 155.93s. The skipped tests require live Ollama.
  Log: `/private/tmp/utexteditor-rag01-final-full.log`.
- Ukrainian catalog validation passed against 1031 extracted UI strings;
  regenerated catalog contains 1044 finished translations.
- Clean Code review: intent (explicit units and estimates); ownership (budget
  and HTTP rules in AI services, settings/UI as configuration); safety (no
  manuscript writes or undo changes, old workers keep their provider); errors
  (refusal without raw HTTP-body disclosure or reduced-window retry); tests
  (normal/failure/stale/default paths and full suite); diff (no dependency or
  unrelated refactor, translations/docs updated); report (server/native limits
  explicit). `git diff --check` passed.
- No native, live-server allocation or model-comprehension verification claimed;
  none is a required RAG-01 gate. Token-budget conservatism and continuity
  refusal are deliberate trade-offs, documented above.
