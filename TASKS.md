# UTextEditor — open tasks

Repository-wide refactoring history remains in [docs/refactoring-progress.md](docs/refactoring-progress.md).

## RAG — project context retrieval for local AI

Parent status: OPEN. This is an implementation plan, not shipped behavior.
The current request authorizes recording the plan; implement only when selected
for execution. Inspect the current implementation before each batch.

### Scope and invariants

- Add local, project-scoped retrieval of manuscript passages and reference
  material; continue generating through `AIProvider` and Ollama.
- Make one shared context service available to every user-facing AI workflow,
  including automatic inline completion. Each workflow must explicitly choose
  a retrieval policy or a documented no-retrieval policy; availability does not
  mean attaching project passages to every request. Embedding, model listing,
  connectivity and warm-up calls must not recursively invoke retrieval.
- Keep mandatory context separate from retrieved supporting passages. Retrieval
  cannot establish that an absent fact does not exist in the project.
- Preserve explicit character associations, knowledge boundaries, author review,
  dirty buffers, undo, consent, snapshots and transactional application.
- Preserve the existing complete-reference contracts for Auto-writer and character
  profile generation. RAG must not silently replace or truncate their full notes
  and textual profiles. Initially augment Auto-writer with manuscript retrieval;
  any alternative reduced-reference mode requires a separate explicit decision.
- Do not change the version-1 manifest format or introduce a cloud service.
- Run indexing, retrieval, embeddings and filesystem verification in workers.
  Keep domain logic in `app/project/`, AI operations in `app/ai/`, persistence
  defaults in `app/settings/`, and UI orchestration in `app/ui/`.

### RAG-01 — context policy, budgets and provider capability contract

Status: OPEN. Dependencies: none.

- [ ] Document a workflow matrix covering manual/automatic inline completion,
  free-prompt generation (including streaming), spelling/grammar, summary,
  continuity, character suggestions/development, brief suggestions, outline
  planning, Auto-pilot, Auto-writer and translation. Assign every workflow an
  explicit policy and an integration ticket (RAG-05, RAG-07–11); include
  standalone/no-project operation and intermediate milestone behavior.
- [ ] Define mandatory sources, optional retrieval sources, chronology policy,
  source exclusions, no-hit behavior and explicit refusal conditions per workflow.
  Keep automatic project context opt-in and honor completion note exclusions.
- [ ] Distinguish character counts, UTF-8 bytes, input tokens and output tokens.
  Define one request budget including role, instructions, wrappers, mandatory
  content, retrieved passages, response reserve and a safety margin.
- [ ] Define configurable Ollama context length through the provider boundary;
  verify capability/unsupported-option handling without assuming a model name
  guarantees a usable window. Mark token estimates as estimates; do not call
  character-based heuristics exact token counts.
- [ ] Fix analysis allocation so long scene text cannot silently consume the
  entire budget before selected notes and associated profiles. Make incomplete
  coverage visible; refuse requests whose required evidence cannot fit.

Gate RAG-01.V1: offline tests for tiny/exact/overflow budgets, Ukrainian and
English text, instruction/output overhead, unsupported context controls,
long-scene source starvation and unchanged behavior outside selected workflows.

### RAG-02 — source capture, chunks and provenance

Status: OPEN. Dependencies: RAG-01.

- [ ] Reuse existing project captures/path validation. Capture scenes, notes and
  textual character metadata with project/source IDs, source type, title,
  content fingerprint, source offsets and manuscript order where applicable.
- [ ] Split prose at paragraph boundaries with bounded overlap; split profiles
  by semantic fields. Retain exact source text and deterministic chunk identities.
  Exclude portraits and application recovery/debug artifacts.
- [ ] Treat open buffers as authoritative for retrieval in that request. Overlay
  unsaved chunks without overwriting disk-derived cache entries; keep provenance
  sufficient to verify both buffer revisions and external disk changes.
- [ ] Define limits for chunk size/count and project indexing work; report
  incomplete coverage explicitly instead of silently treating a partial index
  as complete. Handle unreadable, invalid and removed sources safely.

Gate RAG-02.V1: deterministic Unicode/paragraph/overlap tests, exact quotations,
offsets, empty/oversized sources, duplicate titles with stable IDs, unsaved-buffer
precedence, external modification and cross-project isolation.

### RAG-03 — rebuildable local lexical index

Status: OPEN. Dependencies: RAG-02.

- [ ] Add a project-identity-scoped cache using SQLite FTS5, after checking its
  availability on supported Python installations. Provide a clear unavailable
  state without preventing ordinary editing or existing AI workflows.
- [ ] Version the index schema and chunking policy; incrementally refresh changed
  sources and remove deleted ones. Rebuild safely after corruption, version
  mismatch, relocation or interrupted indexing.
- [ ] Publish index updates atomically so requests cannot see partially replaced
  generations. Cancellation/project switches must discard obsolete work.
- [ ] Provide index status, rebuild and cache deletion controls. Explain that the
  local cache contains manuscript text and can be recreated from source files.

Gate RAG-03.V1: temporary-database tests for insert/update/delete/rename, reopened
projects, corrupt and unwritable caches, cancellation, interrupted transactions,
concurrent reads and stale workers. No index operation may write manuscripts.

### RAG-04 — deterministic retrieval and context assembly

Status: OPEN. Dependencies: RAG-01, RAG-03.

- [ ] Expose a shared context service returning a captured, budgeted context and
  source manifest from explicit workflow inputs. Keep project retrieval outside
  the HTTP provider; reuse the same assembly for streaming and non-streaming
  generation. Do not add implicit project access inside every provider method.
- [ ] Build bounded queries from the author request, current passage and explicit
  scene associations; support names/aliases and exact terminology without
  treating manuscript text as executable instructions.
- [ ] Rank lexical matches, deduplicate overlapping passages and limit per-source
  dominance. Keep mandatory context regardless of retrieval ranking.
- [ ] Apply exclusions and chronology filters before ranking/assembly. Distinguish
  earlier/current/later scenes and unrestricted reference notes; do not claim
  manuscript order alone proves the story's temporal order. Treat unplaced or
  ambiguous material explicitly, with conservative defaults for scene writing.
- [ ] Assemble labeled, data-delimited passages within the remaining budget;
  record included, omitted and shortened sources and the reason for each choice.
  A no-hit result must be explicit and must not imply project-wide consistency.

Gate RAG-04.V1: deterministic ranking/tie tests, distractors, aliases, exclusions,
repeated passages, source diversity, future/ambiguous scenes, budget exhaustion,
no hits, untrusted embedded instructions and reproducible source manifests.

### RAG-05 — manual completion pilot and source review

Status: OPEN. Dependencies: RAG-04.

- [ ] Add opt-in retrieval to manual project-scene completion, reusing existing
  captured-context review and activity/cancellation patterns.
- [ ] Show exact passages, source IDs/titles, buffer/disk provenance, budget units
  and incomplete-coverage notices. Let authors exclude sources and rebuild the
  request before sending it; disclose the actual generation destination.
- [ ] Bind the reviewed context to the sent request. Verify selected sources and
  document/project/settings generations before dispatch and after generation;
  discard stale successes and obsolete failures. Preserve explicit acceptance.
- [ ] Keep automatic completion on its existing path for this first release.
  This is an intermediate milestone; RAG-08 is required for parent completion.
  Update README, README.uk where applicable, UI translations and architecture notes.

Gate RAG-05.V1: offline UI tests for review/exclude/send, correct payload,
unsaved edits, disk changes during review/generation, tab/project/settings
switches, cancellation, index unavailable/no hits, acceptance/rejection and undo.
Gate RAG-05.V2: direct native walkthrough of source review, keyboard navigation,
cancel and acceptance on the tested platform. Without a native report: BLOCKED.

### RAG-06 — embeddings and hybrid retrieval

Status: OPEN. Dependencies: RAG-05.V1 and a recorded lexical baseline.

- [ ] Select an embedding model after measuring Ukrainian/English retrieval,
  resource requirements and deployment cost. Keep generation and embedding model
  settings separate; do not assume `gemma4:12b` exposes suitable embeddings.
- [ ] Add embedding operations behind an appropriate AI abstraction; keep Ollama
  endpoints/payloads/parsing in `app/ai/ollama_client.py`. Disclose the embedding
  destination separately, including any remote host, before transmitting text.
- [ ] Cache vectors by content, embedding model identity/version, dimensions and
  chunking policy. Invalidate incompatible entries; bound batch sizes, storage
  and memory. Choose a vector store only from measured needs, avoiding an
  unnecessary external database or dependency.
- [ ] Combine lexical and semantic rankings with deterministic tie handling.
  Define a visible lexical fallback for unavailable/failed embeddings; do not
  silently change the embedding destination or download a model.

Gate RAG-06.V1: fake-provider tests for ranking fusion, invalid/dimension-mismatched
vectors, model changes, partial batches, timeouts, cancellation, stale buffers,
cache invalidation and fallback. Normal tests remain offline.
Gate RAG-06.V2: explicitly invoked live embedding smoke against the configured
destination; record model/version, hardware, latency and limitations separately
from offline correctness. Without that evidence: CHECKPOINT, not live-verified.

### RAG-07 — evaluate and extend to Auto-writer

Status: OPEN. Dependencies: RAG-05, RAG-06.

- [ ] Build a versioned synthetic English/Ukrainian evaluation corpus with known
  relevant sources, aliases, distant plot facts, distractors, chronology traps
  and questions whose evidence is absent. Record expected source IDs.
- [ ] Compare current fixed context, lexical retrieval and hybrid retrieval on
  source recall/precision, chronology violations, latency, request size and cache
  cost. Set numerical acceptance thresholds before tuning on the evaluation set;
  include a held-out set and publish failures rather than claiming perfect recall.
- [ ] Add opt-in manuscript retrieval to Auto-writer while retaining all required
  notes/profiles, explicit associations and the full current scene for refinement.
  Preserve pre-generation snapshots, complete-reference limits, cancellation,
  captured-state verification and transactional application. Define how newly
  generated earlier drafts enter the in-memory retrieval corpus during a run.
- [ ] Validate retrieved evidence against the exact sent source snapshot before
  presenting source-backed findings. Integrate the remaining workflows through
  RAG-08–11; partial retrieval cannot justify a whole-project consistency claim.

Gate RAG-07.V1: evaluation report plus offline end-to-end tests for a relevant
distant scene, missing evidence, changed sources, sequential generated drafts,
budget refusal, generation failure and rollback. Document measured limits.
Gate RAG-07.V2: direct native Auto-writer/source-review walkthrough and explicitly
invoked live generation smoke; report native and live outcomes separately.

### RAG-08 — automatic inline completion

Status: OPEN. Dependencies: RAG-05, RAG-06.V1.

- [ ] Route automatic project-scene completion through the shared service when
  automatic project context and retrieval are enabled. Use the current paragraph
  ending at the cursor, explicit associations and bounded preceding context as
  retrieval inputs; retain standalone completion when no project is bound.
- [ ] Reuse the ready index and cached embeddings/results. Debounce typing,
  coalesce pending requests and bound worker concurrency, passage count and
  retrieval time. Do not rebuild the index or embed the whole project for each
  keystroke. Record a numerical latency target and representative workload
  before tuning; measure retrieval and end-to-end latency separately.
- [ ] Key caches by project/index generation, query, source fingerprints,
  embedding settings, chronology policy and exclusions. A cache hit must not
  bypass current-buffer precedence or source verification.
- [ ] Define visible timeout/unavailable-index behavior: omit optional retrieved
  passages and use valid mandatory context, or skip the suggestion if that
  cannot be captured safely. Never reuse stale passages as a fallback.
- [ ] Preserve destination consent and source exclusions without a modal review
  on every keystroke. Provide an on-demand view of the actual context used for
  the displayed suggestion. Changing retrieval settings invalidates pending work.
- [ ] Discard results after edits, cursor/selection movement, tab/project/settings
  changes, source edits or cancellation. Keep Tab acceptance, Esc rejection and
  undo intact; no generated text is inserted without author acceptance.

Gate RAG-08.V1: fake-clock/provider tests for rapid typing, cache invalidation,
bounded work, timeouts, empty hits, unsaved notes/scenes, remote embedding consent,
out-of-order replies, all stale triggers, exclusions and acceptance/undo; include
a reproducible performance report without timing-sensitive unit assertions.
Gate RAG-08.V2: direct native typing/cursor-switching walkthrough with retrieval
enabled, context inspection, Tab/Esc and undo; record responsiveness separately
from live-model latency. Without a native report: BLOCKED.

### RAG-09 — free-prompt generation, planning and Auto-pilot

Status: OPEN. Dependencies: RAG-05, RAG-06.V1.

- [ ] Add explicit project-context retrieval to free-prompt generation, using the
  author prompt and optional selected/current scene as the query. Preserve
  prompt-only operation; do not silently attach the active document or project.
  Streaming and non-streaming modes must send the same captured source context.
- [ ] Integrate brief suggestions and outline planning using the brief and
  existing mandatory motivation summary. Support new-project/no-index operation;
  distinguish retrieved established facts from proposed inventions.
- [ ] Integrate both Auto-pilot planning and scene drafting. Capture source
  provenance per step and include earlier newly generated drafts as transient
  sources where appropriate; never persist them in the canonical index before
  successful project application. Preserve additive/transactional behavior.
- [ ] Reuse review, budget, consent and stale-state handling; report fallback or
  insufficient context explicitly rather than claiming complete project access.

Gate RAG-09.V1: offline tests for prompt-only/project modes, streaming parity,
no project, planning facts versus suggestions, multi-step cancellation/failure,
transient drafts, stale sources and unchanged manuscript/undo on rejection.

### RAG-10 — analysis and character workflows

Status: OPEN. Dependencies: RAG-05, RAG-06.V1, RAG-07.V1.

- [ ] Add optional retrieval to scene summary and continuity analysis while
  retaining the selected scene, explicitly selected notes and associated
  profiles as mandatory sources. Label a scene-only versus contextual summary.
  Retrieved profiles do not establish physical presence or character knowledge.
- [ ] Require continuity findings to cite exact source IDs/quotations present in
  the sent snapshot; validate against those passages, including retrieved scene
  evidence. Report partial coverage and never equate no findings with a full
  project audit. Chronology restrictions remain task-specific and explicit.
- [ ] Add manuscript retrieval to empty-profile suggestions without replacing
  their complete-note context or changing empty-field-only application rules.
- [ ] Add optional supporting retrieval to character development while keeping
  the selected profile and scene excerpt mandatory. Arc-update evidence must
  still come from the selected scene; background hits alone cannot justify it.

Gate RAG-10.V1: tests for mandatory-source allocation, no hits/missing evidence,
invented or excluded citations, future facts, presence/knowledge boundaries,
full-note retention, profile edits during requests and explicit staged review.

### RAG-11 — translation, spelling and complete workflow coverage

Status: OPEN. Dependencies: RAG-09, RAG-10, RAG-08.V1.

- [ ] Build a captured project terminology/name glossary for translation and
  retrieve relevant usage examples per item through the shared service. Delimit
  reference examples from text to translate so they cannot be emitted as extra
  translation. Keep the entire target item and translation direction mandatory.
- [ ] Reuse glossary decisions across scenes, titles and character fields within
  a run; flag ambiguous terms for author review. Preserve translation snapshots,
  stale checks, cancellation and transactional application. Standalone/no-project
  translation must remain possible wherever currently supported.
- [ ] Give spelling/grammar an explicit shared-service policy: default to the
  target text only; optionally retrieve a bounded project dictionary of names
  and terms when enabled. Do not send unrelated manuscript passages or let
  dictionary matches silently suppress validated errors. Keep original-text
  offsets, evidence validation, underlines, author review and undo unchanged.
- [ ] Audit every user-facing AI call site, including retries and streaming,
  against the RAG-01 matrix. Require a tested explicit policy, correct consent,
  source exclusions and safe no-project/failure behavior at each site. Document
  infrastructure/embedding calls as intentionally outside retrieval.
- [ ] Update README, README.uk, settings descriptions and translations to explain
  workflow coverage, defaults, cache privacy, fallbacks and actual context review.

Gate RAG-11.V1: offline tests for consistent glossary use, ambiguous/no-match
terms, reference text not translated as output, spelling offsets/names, disabled
retrieval, cross-project isolation, all call-site policies and transactional
failure/stale cases. Publish the completed workflow coverage matrix.
Gate RAG-11.V2: native walkthrough of the added generation, planning, analysis,
character, translation and spelling controls, plus explicitly invoked live
hybrid-retrieval smoke for representative inline and multi-step workflows.
Report native and live evidence separately; do not infer either from mocks.

### Execution order and completion rules

- Execute RAG-01, then RAG-02–04, then RAG-05 as the first usable milestone;
  follow with RAG-06, then RAG-07–10 according to their dependencies, and RAG-11
  for final workflow coverage. Automatic inline completion (RAG-08) is required
  scope. Use one high-risk ticket or 1–4 related subtasks per checked batch.
  Dependencies require the relevant prior gates to pass.
- Before each ticket, write criterion-specific preconditions and normal,
  failure, cancellation and stale-state cases. Run focused tests, then
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest`
  for implementation changes; run translation checks when UI strings change.
- Review `git diff --check`, the final diff and the Clean Code completion
  checklist. Preserve unrelated worktree changes and all existing safety gates.
- Report each selected ID and gate as COMPLETE, CHECKPOINT or BLOCKED, separately
  from the parent. Prepend a 10–20-line checkpoint to IMPLEMENTATION_PROGRESS.md
  after implementation batches with exact resume IDs/command and evidence.
- Parent completion requires all RAG-01–11 acceptance criteria and gates, updated
  user/developer documentation, evaluation evidence and required native/live
  reports. Offscreen tests do not close native gates. Recording this plan does
  not complete any implementation ticket.

## FILE-NAME-01 — transliterate Ukrainian titles into project filenames

Status: OPEN. Independent of the RAG parent; this request records a task only.

Problem: `Project._slug_for_title` currently retains only ASCII letters and
digits. Ukrainian-only titles therefore produce `untitled.txt`,
`untitled-2.txt`, etc.; mixed titles lose their Ukrainian words.

Owning code: `app/project/service.py` (`_slug_for_title`, `_new_path`,
`_unique_new_path`). Trace all callers before implementation, including project
setup, scene/note creation, duplication, import and AI-generated project items.

Acceptance criteria:

- [ ] Define and document one deterministic Ukrainian-to-Latin transliteration
  policy, including case, word-initial/context-dependent letters, `зг`,
  `ґ/г`, `є/ї/й/ю/я`, soft signs and straight/typographic apostrophes.
  Normalize equivalent Unicode input before transliteration. Use a small local
  implementation unless a dependency has demonstrated value.
- [ ] Transliterate Ukrainian title text before the existing ASCII slug cleanup;
  lowercase the result, join word separators with single hyphens and remove
  leading/trailing hyphens. Preserve existing English/digit filename behavior.
  Required examples: `Ніч у Києві` → `nich-u-kyievi.txt`;
  `Розділ 2 — Повернення` → `rozdil-2-povernennia.txt`;
  `Scene 3: Зустріч` → `scene-3-zustrich.txt`.
- [ ] Use `untitled` only when the accepted title yields no usable letters or
  digits after normalization/transliteration (for example, punctuation/emoji
  only). Preserve current validation of blank/invalid titles. Document handling
  of unsupported scripts rather than claiming general transliteration support.
- [ ] Reuse the same slug rule for both filename allocation helpers and all
  applicable callers. Preserve numbered collision suffixes, reserved batch
  paths, existing on-disk files, safe path containment and no-overwrite behavior.
  Handle distinct titles that transliterate to the same slug deterministically.
- [ ] Bound the generated filename component for supported filesystem limits,
  retaining `.txt` and room for collision suffixes; test very long titles and
  reserved platform basenames. Do not weaken existing path validation.
- [ ] Preserve original Ukrainian display titles, stable IDs, links and scene
  associations. Apply the new rule when allocating new paths; opening/saving
  existing projects must not automatically rename `untitled*` or other files.
  Existing title-rename/path behavior must remain explicit and documented;
  bulk migration of existing filenames is outside this ticket.
- [ ] Add focused domain and workflow regressions; update README with the
  user-visible naming rule when implemented.

Gate FILE-NAME-01.V1: table-driven tests for the Ukrainian alphabet and contextual
rules, mixed Latin/Ukrainian/digits, punctuation/apostrophes, Unicode equivalence,
empty-slug fallback, long names, reserved names and repeated/transliteration
collisions. Exercise both allocation helpers, occupied disk paths and reserved
batch paths; verify file contents and original titles survive failures.

Gate FILE-NAME-01.V2: offline integration tests for manual scene/note creation
and AI-generated project setup/Auto-pilot, duplication/import where applicable;
verify legacy project reopen/save leaves existing paths unchanged and references
resolve correctly. Run focused tests, the full offscreen suite and
`git diff --check`; review the Clean Code completion checklist. No live Ollama
is required. Report this ticket separately from the RAG parent.
