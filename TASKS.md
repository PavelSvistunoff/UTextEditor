# UTextEditor — open tasks

Repository-wide refactoring history remains in [docs/refactoring-progress.md](docs/refactoring-progress.md).

## RAG — project context retrieval for local AI

Parent status: OPEN. Implementation is proceeding in sequential checked batches.
Completed tickets are marked below; remaining tickets describe planned behavior.
Inspect the current implementation before each batch.

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

Status: COMPLETE. Dependencies: none. Gate RAG-01.V1: COMPLETE.
Evidence: [context policy and verification](docs/ai-context-policy.md),
IMPLEMENTATION_PROGRESS.md; final full offscreen suite: 1248 passed, 2 skipped.

- [x] Document a workflow matrix covering manual/automatic inline completion,
  free-prompt generation (including streaming), spelling/grammar, summary,
  continuity, character suggestions/development, brief suggestions, outline
  planning, Auto-pilot, Auto-writer and translation. Assign every workflow an
  explicit policy and an integration ticket (RAG-05, RAG-07–11); include
  standalone/no-project operation and intermediate milestone behavior.
- [x] Define mandatory sources, optional retrieval sources, chronology policy,
  source exclusions, no-hit behavior and explicit refusal conditions per workflow.
  Keep automatic project context opt-in and honor completion note exclusions.
- [x] Distinguish character counts, UTF-8 bytes, input tokens and output tokens.
  Define one request budget including role, instructions, wrappers, mandatory
  content, retrieved passages, response reserve and a safety margin.
- [x] Define configurable Ollama context length through the provider boundary;
  verify capability/unsupported-option handling without assuming a model name
  guarantees a usable window. Mark token estimates as estimates; do not call
  character-based heuristics exact token counts.
- [x] Fix analysis allocation so long scene text cannot silently consume the
  entire budget before selected notes and associated profiles. Make incomplete
  coverage visible; refuse requests whose required evidence cannot fit.

Gate RAG-01.V1: offline tests for tiny/exact/overflow budgets, Ukrainian and
English text, instruction/output overhead, unsupported context controls,
long-scene source starvation and unchanged behavior outside selected workflows.

### RAG-02 — source capture, chunks and provenance

Status: COMPLETE. Dependencies: RAG-01. Gate RAG-02.V1: COMPLETE.
Evidence: [source capture verification](docs/rag-source-capture.md),
IMPLEMENTATION_PROGRESS.md; full offscreen suite: 1286 passed, 2 skipped.

- [x] Reuse existing project captures/path validation. Capture scenes, notes and
  textual character metadata with project/source IDs, source type, title,
  content fingerprint, source offsets and manuscript order where applicable.
- [x] Split prose at paragraph boundaries with bounded overlap; split profiles
  by semantic fields. Retain exact source text and deterministic chunk identities.
  Exclude portraits and application recovery/debug artifacts.
- [x] Treat open buffers as authoritative for retrieval in that request. Overlay
  unsaved chunks without overwriting disk-derived cache entries; keep provenance
  sufficient to verify both buffer revisions and external disk changes.
- [x] Define limits for chunk size/count and project indexing work; report
  incomplete coverage explicitly instead of silently treating a partial index
  as complete. Handle unreadable, invalid and removed sources safely.

Gate RAG-02.V1: deterministic Unicode/paragraph/overlap tests, exact quotations,
offsets, empty/oversized sources, duplicate titles with stable IDs, unsaved-buffer
precedence, external modification and cross-project isolation.

### RAG-03 — rebuildable local lexical index

Status: COMPLETE. Dependencies: RAG-02. Gate RAG-03.V1: COMPLETE.
Evidence: [lexical index verification](docs/rag-lexical-index.md),
IMPLEMENTATION_PROGRESS.md; final full offscreen suite: 1318 passed, 2 skipped.

- [x] Add a project-identity-scoped cache using SQLite FTS5, after checking its
  availability on supported Python installations. Provide a clear unavailable
  state without preventing ordinary editing or existing AI workflows.
- [x] Version the index schema and chunking policy; incrementally refresh changed
  sources and remove deleted ones. Rebuild safely after corruption, version
  mismatch, relocation or interrupted indexing.
- [x] Publish index updates atomically so requests cannot see partially replaced
  generations. Cancellation/project switches must discard obsolete work.
- [x] Provide index status, rebuild and cache deletion controls. Explain that the
  local cache contains manuscript text and can be recreated from source files.

Gate RAG-03.V1: temporary-database tests for insert/update/delete/rename, reopened
projects, corrupt and unwritable caches, cancellation, interrupted transactions,
concurrent reads and stale workers. No index operation may write manuscripts.

### RAG-04 — deterministic retrieval and context assembly

Status: COMPLETE. Dependencies: RAG-01, RAG-03. Gate RAG-04.V1: COMPLETE.
Evidence: [context assembly verification](docs/rag-context-assembly.md),
IMPLEMENTATION_PROGRESS.md; final full offscreen suite: 1366 passed, 2 skipped.
Cross-workflow provider-payload association verification remains RAG-12 scope.

- [x] Expose a shared context service returning a captured, budgeted context and
  source manifest from explicit workflow inputs. Keep project retrieval outside
  the HTTP provider; reuse the same assembly for streaming and non-streaming
  generation. Do not add implicit project access inside every provider method.
- [x] Include explicit scene-character associations as mandatory structured
  context for scene-based requests, independent of lexical/vector matches.
  Implement and verify the complete association contract in RAG-12; never
  substitute name mentions or retrieval similarity for explicit association.
- [x] Build bounded queries from the author request, current passage and explicit
  scene associations; support names/aliases and exact terminology without
  treating manuscript text as executable instructions.
- [x] Rank lexical matches, deduplicate overlapping passages and limit per-source
  dominance. Keep mandatory context regardless of retrieval ranking.
- [x] Apply exclusions and chronology filters before ranking/assembly. Distinguish
  earlier/current/later scenes and unrestricted reference notes; do not claim
  manuscript order alone proves the story's temporal order. Treat unplaced or
  ambiguous material explicitly, with conservative defaults for scene writing.
- [x] Assemble labeled, data-delimited passages within the remaining budget;
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
- Parent completion requires all RAG-01–12 acceptance criteria and gates, updated
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

## AI-SETUP — language-aware project setup with notes and characters

Parent status: OPEN. This section records implementation work; behavior has
not changed. Independent of RAG delivery; reuse its context service when ready.

Current evidence: `app/ai/project_planning.py` does not accept an explicit
writing language. `ProjectSetupDialog` reviews chapter/scene outline lines only;
`Project.add_outline` creates empty scenes. Auto-pilot's `characters` currently
become `Note(type="character")` through `add_autopilot_content`, rather than
structured character profiles. Inspect current callers/tests before each batch.

### AI-SETUP-01 — honor the selected writing language throughout setup

Status: OPEN. Dependencies: none.

- [ ] Capture the selected AI writing language for brief suggestions, outline
  generation, Auto-pilot planning and scene drafting. English/Ukrainian choices
  must explicitly control generated human-readable titles, suggestions, scene
  prose, notes and character fields, independently of prompt/schema language.
- [ ] Resolve Auto from author-provided brief prose using existing local language
  detection; ambiguous/short/mixed input falls back to the captured interface
  language. Exclude application-provided English template labels, placeholders
  and schema codes from detection. Show the resolved language before generation.
- [ ] Pass the captured language through service/provider inputs and explicitly
  name it in prompts. Keep schema keys/enums stable in English; preserve author
  text, proper names and deliberate quotations. Do not translate/rewrite existing
  project content as an incidental setup step or claim prompts guarantee language.
- [ ] Invalidate pending generation and reviewed proposals when language/settings,
  brief or project state changes; suppress obsolete errors. Keep workers,
  cancellation, destination disclosure and explicit author acceptance intact.
- [ ] Update user documentation and localized UI strings for the new behavior.

Gate AI-SETUP-01.V1: offline prompt/service/UI regressions for explicit Ukrainian
with an English interface/template, explicit English with a Ukrainian interface,
Auto in both languages, ambiguous/mixed/empty author input, unchanged schema
keys, all planning/drafting calls and language changes during requests/review.
Use fake providers; test propagated instructions rather than assuming model output
language is guaranteed. Run focused tests and the full offscreen suite.

### AI-SETUP-02 — generate and review notes and structured characters

Status: OPEN. Dependencies: AI-SETUP-01. Coordinate generated file paths with
FILE-NAME-01; its naming gate must pass before closing this ticket.

- [ ] Extend the setup proposal beyond chapter/scene titles to bounded typed
  reference notes and structured character profiles using the existing manifest
  model. In normal setup scenes remain empty; drafting prose remains Auto-pilot's
  explicit mode. Do not represent structured characters only as character notes.
- [ ] Require notes and characters for a normal fictional-story setup. Validate
  nonempty collections before application; if the brief cannot support useful
  proposals, request author clarification or show editable missing-content
  validation rather than silently claiming complete setup. Do not invent facts
  as established author decisions; generated content is a proposal for review.
- [ ] Define explicit maximum chapters/scenes/notes/characters, field/content sizes
  and total request/response budgets before implementation. Validate untrusted
  output at the service boundary, including types/enums, duplicates, required
  values and references. Reject malformed or incomplete responses visibly;
  never apply only the valid portion of a failed batch.
- [ ] Generate useful initial notes (for example setting, timeline or story
  background, according to the brief) and character identity, role, motivations,
  goals and available background/personality. Do not require unsupported fields
  or fill unknown facts merely to populate a schema. Reuse profile validation.
- [ ] Review/edit/select chapters, scenes, note contents and character fields
  before applying; display the resolved language and clearly mark generated
  proposals. Validate the selected set and any references after author edits.
  Permit explicit author deselection of notes/characters without treating it as
  a generation failure. Cancellation/rejection leaves the project unchanged.
- [ ] Allocate stable IDs at application and resolve proposal-local references
  safely. Relationships/scene associations may be proposed only with valid
  endpoints and explicit author review; do not infer physical presence from
  a profile's existence. Avoid duplicate profiles for existing characters;
  conflicts require review, never overwrite or silently merge existing records.
- [ ] Extend the owning project transaction to create scene/note files and
  structured profiles together. Preserve existing files, unsaved buffers,
  manifest conflict checks and rollback on any validation/write/save failure.
  For existing projects show an additive change summary; preserve the established
  snapshot policy and require a pre-application snapshot for this expanded batch.
- [ ] Bring Auto-pilot onto the same validated proposal/application path while
  preserving its explicit scene-drafting mode, cancellation and all-or-nothing
  application. Retain legacy character notes as existing data; do not silently
  migrate, remove or duplicate them into new structured profiles.
- [ ] Ensure Ukrainian titles produce transliterated filenames through the shared
  allocation helpers, while display titles and generated content stay Ukrainian.
  Update setup review wording, README/README.uk and translations to describe
  notes/profiles as well as empty scenes or explicitly requested drafts.

Gate AI-SETUP-02.V1: offline service/domain tests for complete Ukrainian/English
proposals, missing notes/characters, excessive/malformed/duplicate output,
invalid references, existing-profile conflicts, safe filename allocation,
manifest/disk changes, write failures and complete rollback. Verify saved YAML
contains real character profiles and note files retain their proposed contents.
Gate AI-SETUP-02.V2: offline UI integration tests for generate → review/edit/
deselect → apply → reopen, author rejection, stale brief/language/project/buffer
state, cancellation and late failures; exercise normal setup and Auto-pilot.
Run focused tests, the full offscreen suite and translation checks.
Gate AI-SETUP-02.V3: direct native walkthrough of Ukrainian setup, note/profile
review, application and reopen; optional live model evidence is reported
separately. Without native evidence: BLOCKED for this gate.

Completion: report AI-SETUP-01/02 and each gate separately; close the parent only
when both tickets and required gates pass. Review `git diff --check`, final diff
and the Clean Code completion checklist; record the implementation checkpoint
with exact resume IDs, test evidence and any blocked native checks.

## AI-SCENE-01 — generate or regenerate one selected scene

Status: OPEN. Independent of whole-project Auto-writer; integrate shared RAG
context when available without requiring completion of the entire RAG parent.
This is planned work, not shipped behavior.

Problem: authors need to draft an empty scene or replace the draft of one
selected existing scene without running generation across the whole project.
Regeneration means a new complete draft, distinct from Auto-writer refinement.

Owning code: inspect `app/project/auto_writer.py`, existing scene capture and
snapshot services, AI review dialogs and project-tree/MainWindow callers before
implementation. Reuse shared rules without routing a single-scene action through
an operation that can modify other scenes.

Acceptance criteria:

- [ ] Provide Generate Selected Scene and Regenerate Selected Scene actions for
  a valid project-tree scene and the active project-bound scene tab. Make the
  target ID/title explicit; do not silently substitute another scene when tree
  selection and active tab differ. Explain unavailable/non-scene selections.
- [ ] Generate targets an empty scene, considering authoritative unsaved buffer
  text. A nonempty scene requires the explicit regenerate workflow; never
  overwrite its contents through the empty-scene action.
- [ ] Let the author supply optional scene-specific instructions. Capture the
  selected writing language (reuse AI-SETUP-01 resolution), project outline,
  chapter/scene metadata, explicit character associations and relevant notes/
  prior events. Honor knowledge/presence boundaries, chronology, exclusions and
  the shared context budget; disclose actual sources and AI destination.
- [ ] For regeneration, offer an explicit choice to use the current scene as
  reference or generate a fresh draft from project context/instructions. Show
  the choice before sending; do not silently include/exclude existing prose.
  Preserve the original scene for review and rollback in either mode.
- [ ] Use the shared retrieval service when enabled, including authoritative
  unsaved source buffers. Before RAG is available/when disabled, use documented
  bounded explicit context with visible coverage limits. Never silently replace
  mandatory context or claim that retrieval sees the complete manuscript.
- [ ] Run capture, retrieval, generation and filesystem checks in workers with
  progress/cancellation. Track target editor revision, project/manifest state,
  source fingerprints, request/settings generations and language; discard stale
  successes and obsolete errors after relevant changes or target removal.
- [ ] Show the proposed full scene before application, with the existing text
  available for comparison. Allow reject/cancel, retry and explicit acceptance;
  a retry must not discard the current buffer or apply a previous proposal.
  Generated output must pass response type/size/content validation.
- [ ] Before accepting replacement of nonempty text, create a durable revision
  containing the exact original scene, including unsaved edits; failure blocks
  replacement. Recheck captured state after snapshot creation. Do not save or
  clear dirty flags merely to create the snapshot or request generation.
- [ ] Apply accepted text to the target editor as one undoable replacement and
  leave it dirty for explicit save. If the target was not open, open/reuse its
  captured editor safely before staging; do not write generated prose directly
  to disk. Preserve scene ID/title/path, links, associations and other scenes.
- [ ] Reuse existing save conflict checks for the eventual save. Generation,
  snapshot, validation or acceptance failures leave existing text/files intact;
  cancellation/rejection produces no manuscript changes. Keep explicit undo
  available after acceptance and preserve prior undo history.
- [ ] Update README/README.uk, action descriptions and translations to explain
  empty-scene generation, full regeneration, context choices, review and saving.

Gate AI-SCENE-01.V1: offline domain/service tests with fake providers for empty
and nonempty targets, both regeneration reference modes, Ukrainian/English
language, required character/source context, no-RAG/RAG paths, oversized/invalid
responses, missing/unreadable scenes and source changes during generation.

Gate AI-SCENE-01.V2: offline UI tests for tree versus active-tab targeting,
closed/open scenes, unsaved target/source text, review/reject/retry/accept,
single-step undo/redo, preserved prior undo and dirty state, snapshot failure,
post-snapshot edits, cancellation, out-of-order replies, project/settings/language
changes and target removal. Verify only the selected scene can change, its
original is recoverable and eventual save conflicts preserve staged text.

Gate AI-SCENE-01.V3: direct native walkthrough of selecting an empty scene,
generating/reviewing/accepting, then regenerating a nonempty scene and undoing
acceptance. Verify snapshot recovery and explicit-save behavior. Without native
evidence: BLOCKED for this gate; live model quality is separate evidence.

Completion: run focused tests, the full offscreen suite, translation checks and
`git diff --check`; review final diff and the Clean Code completion checklist.
Report the ticket/gates separately from RAG and AI-SETUP; record a short
implementation checkpoint with exact resume command and outstanding checks.

## BULK — scene movement and character assignment

Parent status: OPEN. Separate from RAG; coordinate metadata invalidation with
RAG-12. This request records planned work only.

### BULK-01 — move multiple selected scenes between chapters

Status: OPEN. Dependencies: none.

- [ ] Add project-tree multiple selection using native keyboard/range selection.
  Resolve scenes by stable ID; deduplicate selections and explain mixed
  chapter/note/character selections rather than silently moving extra scenes.
- [ ] Offer Move Selected Scenes with an explicit destination chapter or
  Ungrouped Scenes and insertion position. Show scene count, sources and target
  before application. Define ordering as existing manuscript order, independent
  of click order; preserve selected scenes' relative order across source chapters.
- [ ] Implement a single owning-domain batch operation reusing existing movement
  rules. Validate the entire source/destination set before mutation; publish one
  manifest transaction rather than repeated partially committed single moves.
  Define same-destination reordering, selected-anchor handling and no-op behavior.
- [ ] Preserve IDs, paths, contents, dirty tabs, undo history, scene links,
  character associations/development and unrelated chapter ordering. Do not
  rename or rewrite scene files as an incidental movement step.
- [ ] Capture/recheck project and manifest state across destination selection
  and background work. On removal, external conflict, cancellation or save
  failure, leave the complete original structure intact; report the reason.
- [ ] Refresh tree selection, counts and navigation coherently after success;
  invalidate captured AI context and index chronology/order metadata for all
  affected scenes, even when text fingerprints have not changed.

Gate BULK-01.V1: domain regressions for multiple source chapters, ungrouped
scenes, range/click order, duplicates, same-chapter anchors, no-op, missing
source/destination, manifest conflict and failed persistence with full rollback.
Gate BULK-01.V2: offline UI tests for multi-selection, mixed selection,
confirm/cancel, project switching, selected dirty tabs and preserved links/
associations. Verify resulting manifest order after reopening and no text writes.
Gate BULK-01.V3: native keyboard/range-selection and destination-dialog walkthrough
with multiple chapters; offscreen tests cannot close this gate.

### BULK-02 — assign one character to multiple scenes

Status: OPEN. Dependencies: BULK-01 multi-selection support; domain work may
proceed independently. Coordinate invalidation with RAG-12.

- [ ] Offer Assign Character to Selected Scenes from scene multi-selection and
  an Assign to Scenes picker from a character profile/tree action. Show the
  exact character, target scene IDs/titles and existing association statuses.
- [ ] Let the author explicitly choose association presence (including mentioned
  rather than physically present) and supported shared association fields.
  Describe associations as author assertions, not inferred name matches.
- [ ] Default to adding missing associations only. Existing associations must
  retain purpose, presence, relevant goals, development notes and state changes.
  Any updating of existing values requires an explicit reviewed option with
  field-level semantics; never replace the whole record with shared defaults.
- [ ] Validate character and every selected scene, deduplicate IDs and apply the
  entire batch in one manifest transaction. Repeated add-missing requests must
  be idempotent; distinguish added, unchanged and explicitly updated records.
- [ ] Preserve IDs, directed character relationships, manuscript files and dirty
  buffers. Recheck captured metadata after review; cancellation, stale project/
  profile/association state or persistence failure must leave all scenes intact.
- [ ] Refresh profile-associated scenes and project UI after success. Invalidate
  every affected scene's context/cache and pending AI result; association-only
  changes must take effect without requiring manuscript edits or full reindexing.

Gate BULK-02.V1: domain tests for new/existing/mixed associations, mentioned
presence, idempotence, duplicate IDs, metadata preservation, explicit field
updates, removed targets/character, external conflict and transactional rollback.
Gate BULK-02.V2: offline UI tests for both entry points, target review/cancel,
stale metadata, changed profiles and reopening saved associations. Verify no
scene text changes and context invalidation for each affected scene.
Gate BULK-02.V3: native multiple-scene assignment walkthrough, including existing
associations and profile navigation. Without native evidence: BLOCKED.

Completion: run focused tests, full offscreen tests, translations and
`git diff --check`; review final diff and the Clean Code completion checklist.
Report both tickets and gates separately; close this parent only when all pass.

## RAG-12 — preserve scene-character links in retrieved context

Status: OPEN. Part of the RAG parent despite placement after the bulk tickets.
Dependencies: RAG-02, RAG-04; validate integrations as RAG-05 and RAG-07–11 land.
Neither bulk implementation nor full hybrid retrieval is a prerequisite for
the core association contract.

- [ ] Capture explicit association records with stable scene/character IDs,
  display names, presence, purpose, relevant goals, development notes and
  scene-linked state changes/evidence. Keep provenance and chronology attached;
  do not discard links when prose is chunked or profiles are indexed separately.
- [ ] For scene-targeted workflows, include that scene's association records and
  applicable character context as mandatory data before allocating optional
  retrieval space. If required records cannot fit, refuse/report insufficient
  context rather than silently dropping characters or association fields.
- [ ] When another scene passage is retrieved, include or reference its own
  association metadata in the same captured request. Clearly distinguish target
  scene presence from background-scene presence. Metadata enrichment must be
  budgeted; exclude an optional passage if its required metadata cannot fit.
- [ ] Include directed character relationships relevant to associated characters
  with their source/target IDs and direction. Do not infer reverse relationships,
  transfer another scene's knowledge/state to the target or treat every retrieved
  profile as physically present. Preserve mentioned-only semantics.
- [ ] Record metadata fingerprints/generations in source manifests and cache
  keys alongside text/index versions. Moves, association additions/removals,
  presence changes, profile/relationship edits and character deletion must
  invalidate dependent contexts even when source text is identical.
- [ ] Show associations/relationships and their provenance in context review
  and the actual-sent manifest, including automatic inline inspection. Recheck
  captured metadata before dispatch and after generation using existing guards.
- [ ] Verify the full provider-bound payload for manual/automatic inline,
  single-scene generation, analysis, character workflows and Auto-writer;
  planning/translation/spelling use their explicit policies without silently
  acquiring all project associations. Reconcile the RAG-01 coverage matrix.

Gate RAG-12.V1: deterministic capture/assembly tests with zero, multiple and
mentioned-only associations, duplicate names/distinct IDs, directed relationships,
state evidence and retrieved background scenes. Assert exact association data
in the sent context, not merely in the local index; cover mandatory overflow.
Gate RAG-12.V2: fake-provider/UI regressions for association-only edits, bulk
assignment, scene movement/reordering, character deletion, stale cached hits and
late replies. Verify newly captured payloads reflect saved metadata and obsolete
results cannot be applied. Until BULK-01/02 land, those integration cases remain
CHECKPOINT and must be completed before closing this gate or the RAG parent.

Completion: apply normal RAG test/documentation/checkpoint rules. Extend the
RAG-07 evaluation corpus with association/presence/relationship-direction cases;
text-retrieval scores alone do not establish correct structured context.

## CHAR-DEV-01 — audit and correct character development end to end

Status: OPEN. Review existing behavior first; do not assume it is missing or
correct because an earlier checkpoint is complete. This request records a task;
no correctness conclusion or implementation completion is claimed yet.

Scope: manual scene-linked development, AI arc suggestions, profile staging/
saving, ordered development history, current-state projection and AI/RAG context.
Inspect README/SPEC contracts, `app/ai/character_development.py`, character
domain/history services, `app/project/character_context.py`, character dialogs,
MainWindow orchestration and existing tests before selecting a bounded fix.

- [ ] Build a criterion-by-criterion behavior matrix and reproducible synthetic
  project with multiple characters/scenes, mentioned-only associations, directed
  relationships, initial/current arc values and conflicting sequential changes.
  Record expected behavior before changing code; distinguish defects from open
  product decisions. Keep findings and verification evidence in `docs/`.
- [ ] Verify manual development notes and structured state changes round-trip
  through scene associations and YAML without losing field, value, previous
  value or evidence. Check add/edit/remove, empty/invalid values, duplicate
  records, character/scene deletion, duplication and reordering against existing
  contracts. Unrelated profile edits must preserve untouched data exactly.
- [ ] Verify history/projection order and precedence: baseline profile versus
  scene-linked events, repeated changes, removed/reordered scenes, ungrouped
  scenes and explicit previous-value conflicts. Define how ambiguous story
  chronology is presented; manuscript order alone must not be described as
  verified in-world chronology. Surface inconsistencies instead of silently
  choosing or overwriting author data.
- [ ] Verify AI scene-development eligibility, authoritative unsaved profile and
  selected scene text, resolved writing language and excerpt boundaries. Ensure
  current excerpt limits are visible and relevant evidence outside the excerpt
  is not implicitly claimed to have been analyzed. Background RAG evidence
  cannot replace required exact evidence from the selected scene.
- [ ] Check response validation for allowed arc fields, duplicate proposals,
  unsupported/oversized/empty values, malformed JSON and invented quotations.
  Require exact quotations from the captured scene excerpt; classify valid but
  weakly supported interpretations as proposals requiring author judgment.
- [ ] Trace each selected proposal through review, staging, Save and reopen.
  Confirm rejected/unselected suggestions do not change data; staging is not
  persistence. Document whether acceptance updates global arc fields, scene
  state changes or both, and verify that evidence/provenance is retained where
  the contract requires it. Any proposed persistence-semantic change needs
  explicit acceptance criteria before implementation, not an incidental refactor.
- [ ] Exercise stale/cancel/error paths after profile edits, scene edits,
  association changes, source deletion, project/settings/language switches,
  repeated requests and external manifest changes. Obsolete successes and errors
  must not affect newer forms; failed saves must retain staged author edits.
- [ ] Verify scene-specific AI context uses the correct associated character and
  that scene's development, preserving knowledge/secret and presence semantics.
  Check whether global current-state fields leak later developments into earlier
  scenes. Document/fix chronology defects in a bounded follow-up; coordinate
  full-link payload coverage and metadata invalidation with RAG-12.
- [ ] Reproduce confirmed defects with focused failing regression tests before
  fixes. Keep domain rules in owning services and UI as orchestration; preserve
  existing manuscript text, undo, stable IDs and transactional save behavior.
  Update README/README.uk and translations for any observable correction.

Gate CHAR-DEV-01.V1: written audit matrix with concrete expected/actual outcomes,
confirmed defects, unresolved decisions and exact regression commands. Existing
tests passing alone do not close the audit or prove narrative interpretation.
Gate CHAR-DEV-01.V2: deterministic offline domain/service/UI regressions for the
above normal/failure/stale cases, including proposal → selected staging → Save →
reopen and saved-history/context verification. Run focused tests, full offscreen
tests, applicable translation checks and `git diff --check`; review final diff
and the Clean Code completion checklist. Use fake AI providers.
Gate CHAR-DEV-01.V3: direct native walkthrough of manual development editing,
AI proposal review, partial selection/rejection, Save/Cancel, history/projection
and scene navigation. Without native evidence: BLOCKED for this gate. Optional
live-model quality evaluation remains separate from deterministic correctness.

Completion: report audit findings and fixes separately, and each gate as
COMPLETE/CHECKPOINT/BLOCKED. Coordinate identified dependencies with AI-SETUP-01,
BULK-02 and RAG-12 without waiting for unrelated parent completion. Record a
short implementation checkpoint with exact resume IDs and remaining evidence.
