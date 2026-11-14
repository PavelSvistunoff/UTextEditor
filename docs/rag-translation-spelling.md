# RAG-11 — translation, spelling and workflow coverage

RAG-11, RAG-11.V1 and RAG-11.V2 are **COMPLETE**. Offline and native/live verification are recorded separately
below. This closes workflow integration, not RAG-12's structured association
contract or the separate global character-development audit.

## Preconditions and behavior

Translation retrieval is a default-off session action in Project > Project AI.
It requires a project, existing AI/destination consent and a positive configured
token window. Before dispatch, the author reviews character names, display names,
aliases and reference-note titles in an editable glossary. Unchanged targets mean
preserve spelling; shared owners and normalized case-equivalent names are flagged
as ambiguous. Approval covers those choices for this run, including intentionally
unchanged or ambiguous names. There is no automatic terminology inference from
all manuscript prose and no automatic resolution of ambiguous names.

The frozen glossary is used unchanged for project/chapter/scene/note titles,
scene/note contents and every textual character/relationship/development field.
Each item receives its complete target and translation direction as mandatory
JSON data. The shared service retrieves at most four optional lexical usage
passages across manuscript order. Exact role/prompt, destination, source decisions
and budget are reviewed through the queued GUI bridge before every dispatch.
Excluding an example requires rebuilding; exclusions persist across all subsequent
items. Excluding a source as an example does not remove its separately required
target text or approved glossary term.

The request distinguishes reference examples from the target. Responses must be
one JSON object containing exactly one string field `translation`; malformed,
extra and duplicate fields are rejected. Existing empty/NUL/length validation and
edge whitespace/CRLF preservation still apply. This prevents concatenating a
separate examples field into output; schema validation cannot prove that a model
has semantically translated correctly or followed every glossary choice. The
complete side-by-side author review remains necessary.

Glossary limits are 256 distinct terms and 16 KiB serialized UTF-8, with explicit
refusal instead of truncation. The run retains at most 16 MiB estimated request
evidence. Existing 500-field/32,000-character target limits remain. Missing indexes
or no matches leave the full mandatory target/glossary with coverage notices.
No additional models are downloaded, no embeddings are used, and no index is
refreshed by translation. There was no standalone translation entry point to
remove: project translation still requires a project.

Manual spelling dictionary retrieval is a separate persisted setting, default
off. It applies only to documents explicitly bound to the active project.
Automatic checks, standalone tabs and disabled mode always use the existing
target-only provider path. The shared-service dictionary request sets retrieval
disabled and allowed passage kinds empty. Only the complete target/language,
character names/aliases and note titles reach the provider; no note or scene prose
is transmitted. Local source capture can read those files to verify freshness.
The same dictionary limits apply, with refusal on oversized metadata.

The author reviews the exact dictionary request before Send. It has no optional
prose sources to exclude; turning the setting off omits the dictionary. Provider
JSON is parsed against the original Unicode target, never the wrapper or
dictionary. Existing range/original-text/replacement/type/revision validation,
200 non-overlapping findings, underlines, individual review and one-step Undo
are unchanged. A dictionary match never filters a validated finding. No-match
and empty dictionaries remain usable. Pending automatic checks retain their
automatic mode instead of unexpectedly opening a manual dictionary review.

## Ownership, cancellation and failure

`translation_context.py` owns terminology validation, run-wide decisions,
captured requests, exclusions and strict output extraction. `translation.py`
retains its original revision snapshot and transaction. Task-read disk/buffer
values must match the first and every subsequent capture. One baseline verifies
all sources between requests, around provider success/failure and again in the
commit worker after final review. A source change refuses the entire run.

`spelling_context.py` owns the no-prose dictionary policy. The existing
`SpellcheckService` retains all correction validation. UI code only captures
document/project/settings generations, shows controls and dispatches workers;
provider methods remain synchronous off the GUI thread. Review callbacks execute
on queued GUI signals and never read widgets from workers. Closed/reopened tabs,
changed revisions/settings/project, cancellation and changed source files prevent
dispatch/application. Dictionary callbacks additionally check the captured
project manifest. A stale failure cannot install underlines or translated text.

Glossaries, dictionaries, overlays and additional review evidence remain in
memory. Existing lexical caches contain saved project sources, outside the
project; vector privacy/defaults remain as previously documented. Original
translation snapshots remain in `.utexteditor/revisions`. The normal in-memory
AI debug window contains transmitted requests and responses. No context check
claims an atomic lock against arbitrary concurrent external writers.

## Completed workflow audit

The following policies apply to retries as well as initial requests. Activity
retries re-enter the owning workflow and capture current inputs/consent; they do
not replay an old accepted prompt. Streams share the frozen request where RAG
is enabled. `test_ai_workflow_policies.py` inventories 21 provider/bound-method
references in 19 policy records and checks that their behavior test modules
exist. Its AST tripwire recognizes the current provider/service receiver names;
manual inspection also traced the UI worker, retry and shared-service callers.
It is an inventory guard, not a proof for arbitrary dynamically named dispatch.

| Workflow / owners | Default and opt-in policy | Consent, exclusions, fallback | Behavior evidence |
| --- | --- | --- | --- |
| Manual completion / completion_service, main_window, rag_completion | Existing paragraph/project capture; explicit RAG action uses frozen context | Host disclosure; exact RAG Send, optional exclusions/rebuild; standalone paragraph; missing index mandatory only | test_completion_service, test_rag_completion_ui |
| Automatic inline / inline_retrieval, inline_context | Retrieval default off; bounded verified cached context when enabled | Host consent; separate query-embedding consent; inspection/session exclusions; deadline/cache/model failure visible fallback; standalone ordinary completion | test_inline_retrieval_ui, test_inline_context |
| Free generation / main_window, rag_generation | Ordinary Generate is author-prompt-only; separate project-RAG action; same frozen request for streaming | Exact source/destination Send in RAG; separate current-scene choice; exclusions/rebuild; ordinary no-project generation remains possible | test_ai_workflows_e2e, test_rag_generation, test_captured_generation |
| Brief and outline / project_planning, planning_context, planning_retrieval | Default-off form checkbox; author brief plus compact motivations; opt-in reviewed passages | Existing destination approval plus each exact Send; exclusions; empty project/absent index mandatory only; stale sources refuse application | test_planning_retrieval, test_planning_retrieval_ui |
| Auto-pilot / autopilot, planning_context | Same checkbox; full generated plan/prior drafts are mandatory provisional data | Explicit additive-run confirmation plus each source review; no canonical indexing of drafts; incomplete capture/overflow/cancel refuses transaction | test_planning_retrieval, test_planning_retrieval_ui |
| Auto-writer / auto_writer, auto_writer_context | Full notes/profiles/relationships; optional per-scene reviewed RAG | Existing destination approval, each Send, optional scene exclusions; separate embeddings approval; snapshots and final selected-draft transaction | test_auto_writer_retrieval, test_auto_writer_retrieval_ui |
| Summary and continuity / project_analysis, analysis_context | Explicit selected inputs; default-off RAG menu toggle | Existing destination confirmation and exact RAG review; optional scene/note exclusions; no-project unavailable, missing index mandatory only; exact sent citations | test_analysis_retrieval, test_analysis_retrieval_ui |
| Empty character fields / character_profile, character_suggestions, analysis_context | Staged fields plus all full notes; profile RAG checkbox default off | Destination approval then each exact review; mandatory notes protected; final author staging and fresh worker verification | test_analysis_retrieval, test_analysis_retrieval_ui |
| Scene development / character_development, analysis_context | Staged profile and selected associated excerpt; same checkbox | Background exclusions/review; only selected-excerpt evidence supports arc values; explicit individual selection, then separate Save | test_character_development, test_analysis_retrieval_ui |
| Translation / translation, translation_context | Full target/direction; new run glossary/examples opt-in | Host confirmation, glossary approval, each exact Send, persistent optional exclusions; missing index mandatory only; snapshot/final review/transaction | test_translation_retrieval, test_translation_spelling_retrieval_ui, test_project_translation |
| Spelling / spellcheck_service, spelling_context | Target-only default/automatic/standalone; manual project dictionary opt-in | Existing host consent, exact dictionary review; no prose/excludable passages; failure does not suppress findings or change text | test_spelling_dictionary, test_translation_spelling_retrieval_ui, test_spellcheck_service |
| Infrastructure / ollama_client, embedding provider | Connection, metadata/model identity, warm-up and vector calls never recursively retrieve | Installed models only; separate embedding consent in eligible workflows; failures use documented visible fallback | test_ollama_client, test_embeddings, test_rag_embeddings |

RAG-12 remains responsible for complete structured scene-character link payloads
and cross-workflow association-only invalidation. This audit does not mark that
future parent complete or claim that global profiles encode point-in-story state.

## Verification

All test projects and model prompts in this gate are synthetic.

| Selected criterion | Preconditions | Failure/stale-state evidence |
| --- | --- | --- |
| Captured terminology and usage examples | Approved bounded glossary, explicit token window, complete target/direction | Full unsaved target/CRLF, exact reviewed/sent prompt, missing index/no-match, malformed/duplicate/extra response fields, tiny window and source-read race |
| Reuse and translation safety | One run/project, same immutable glossary across every field | Ambiguous owners/case variants, persistent rebuilt exclusions, cross-project refusal, cancelled review, changes during review/generation/final review/commit, existing snapshot/conflict/rollback tests |
| Spelling dictionary policy | Separate setting; manual bound project document only | Original Unicode offsets and dictionary-name finding retained; no prose in prompt; automatic/standalone/disabled remain target-only; reject/cancel/disk/settings/project edits do not install findings; correction Undo |
| Complete call-site coverage | Enumerated ordinary/RAG dispatches, bound methods, streams and retry controllers | Inventory tripwire plus cited behavioral suites; reviewed prompts and legacy policies remain distinct; infrastructure intentionally outside RAG |
| Documentation/localization | Current shipped workflow defaults and actual consent | README/UK/settings help, fresh source/catalog checker, compiled catalog and runtime Ukrainian headings; native/live evidence explicitly separate |

- Focused final offline command: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -xq tests/test_translation_retrieval.py tests/test_spelling_dictionary.py tests/test_translation_spelling_retrieval_ui.py tests/test_ai_workflow_policies.py tests/test_project_translation.py tests/test_project_translation_review_dialog.py tests/test_translation_validation.py tests/test_spellcheck_service.py tests/test_settings.py tests/test_ai_workflows_e2e.py` — **196 passed in 5.00s**; `/private/tmp/utexteditor-rag11-final-focused.log`.
- Full offscreen suite: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -xq` — **1707 passed, 15 expected native/live skips in 380.07s**; `/private/tmp/utexteditor-rag11-full.log`.
- Fresh Qt extraction: **1129 source strings**; Ukrainian coverage/placeholder validation passed; official lrelease rebuilt **1143 finished translations**. English remains intentionally partial.
- Native V2: `QT_QPA_PLATFORM=cocoa PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -xqs tests/test_rag_workflow_native.py` — **7 passed in 2.89s**. Actual visible source dialogs use keyboard Space to Send; profile/planning/dictionary controls are toggled by keyboard, glossary approved through its real button, final generation/character/translation reviews rejected with Esc, spelling correction undone. Providers are fakes: this establishes native interaction, not model quality or comprehensive accessibility. `/private/tmp/utexteditor-rag11-native.log`.
- Separate live V2: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 UTEXTEDITOR_LIVE_RAG_WORKFLOWS=1 .venv/bin/python -m pytest -xqs tests/test_live_rag_workflows.py` — **1 passed in 6.66s** after explicitly granting access to the configured local Ollama. Uses real query/source embeddings and three real generation requests. `/private/tmp/utexteditor-rag11-live.log`.
- Live destination: generation `http://localhost:11434`, `gemma4:12b`, requested window **26000**; embeddings same host, `embeddinggemma:latest`, digest `85462619ee721b466c5927d109d4cb765861907d5417b9109caebc4e614679f1`, **768 dimensions**. No models were installed or settings changed.
- Live inline uses warmed saved vectors through cached-only `InlineContextService`, asserts hybrid ranking and frozen-prompt dispatch; retrieval **79.16 ms**, total **1.09s**, 32 output characters. Two-step Auto-writer asserts hybrid evidence at both steps, provisional earlier drafts, exact sent prompts and no application; **4.06s**, outputs 48/37 characters. These single synthetic smoke observations are not latency guarantees or an evaluation of literary/translation quality.

Initial focused verification deliberately failed until new Ukrainian messages
were added; all new strings are now covered. An initial new UI test used an
incorrect test-only `new_document` argument and was corrected. The first live
attempt hit the network sandbox; the same explicit smoke was rerun with approved
access. No production safety guard was weakened for any test.

## Clean Code completion review

- [x] Intent: terminology, examples, target and dictionary policies have explicit names; translation decisions are author-owned rather than inferred from model output.
- [x] Ownership: domain rules remain in project/AI services; Qt only captures state/reviews/coordinates workers; HTTP stays in OllamaClient.
- [x] Safety: full targets, dirty buffers, Unicode evidence, Undo, snapshots, stable IDs and transactional conflict/rollback contracts remain intact.
- [x] Errors: missing mandatory captures, bad/duplicate JSON, oversized glossary/evidence, cancelled reviews and stale sources refuse visibly; no silent truncation.
- [x] Tests: deterministic normal/failure/stale/cross-project cases plus existing transactional regressions; native and live commands are separately identified.
- [x] Diff: no new dependency, unrelated refactor or generated bytecode; user documentation and Ukrainian catalog updated; unrelated staged files preserved.
- [x] Report: schema checks do not establish semantic translation accuracy; source checks are not arbitrary-writer locks; RAG-12/global character audit remain open.
