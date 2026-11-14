# RAG-09 — planning, Auto-pilot and workflow gate

RAG-09.1 is described in [free-prompt generation](rag-free-prompt-generation.md).
This report covers the remaining RAG-09.2–4 requirements and the offline
RAG-09.V1 gate. The RAG parent still includes unfinished RAG-10–12 work.

Status: RAG-09.1–4 and RAG-09.V1 COMPLETE. Final full offline verification:
1603 passed, 7 expected native/live skips in 330.45s. Focused final verification:
91 passed, 1 native skip in 2.48s. The 1107-source Ukrainian translation coverage
check and existing English catalog validation passed.

## Author controls and preconditions

The project setup form has a default-off **Review retrieved project context for
planning and Auto-pilot** checkbox. It applies to Suggest, Continue to outline
and Auto-pilot. Existing unchecked workflows retain their inputs and confirmations.
RAG requires an explicit Ollama token window. This mode uses lexical retrieval;
it neither invokes the separately configured embedding host nor downloads models.

Before each model request, the existing queued source-review bridge displays the
actual destination, role, fully rendered prompt, conservative token budget,
source fingerprints, passage decisions and coverage notices. Authors can exclude
optional scenes/notes and rebuild; Send remains disabled until the request matches
the exclusions. The brief, compact character motivations, complete outline title
metadata and provisional chain cannot be excluded or silently shortened.

Suggest still returns an editable template with `[Suggestion: ...]` instructions
for inventions. An outline remains a proposed structure that requires final
author approval. The role distinguishes retrieved project records, unsaved author
buffers, proposed plan/character ideas and generated drafts; none establishes
scene presence merely by retrieval. Planning uses the existing bounded compact
motivation/goal/relationship helper, not full character biographies. The review
explicitly reports this limit and partial retrieval is never a consistency proof.

An empty new project works without an index: no eligible sources means visible
`no_hits`/`not_queried` coverage. Missing or unavailable indexes use the shared
mandatory-only fallback with notices. The domain service also supports no-project
planning with explicit author-only coverage; the existing setup UI still requires
an open project. It does not scan neighboring files or unrelated tabs.

## Sequential Auto-pilot and provenance

Auto-pilot additionally requires upfront approval of automatic application of its
complete generated batch. It preserves the existing limits of eight chapters,
twelve scenes and eight character reference notes. It reviews the planning request
and then every scene request separately. Declining any review cancels the run.

`PlanningRetrievalRun` captures one baseline and verifies it between steps, after
reviews, around generation, on completion and immediately before application.
Auto-pilot refuses an incomplete baseline; a missing search index is different
from an unreadable source snapshot. The GUI checks project/settings/request
generations, the form's submitted brief and all open scene/note revision stamps.
Provider and source I/O stay in workers; GUI source reviews use queued signals.

The generated plan and all earlier completed drafts become **mandatory transient
source records** in later requests. Each record has a run-local ID, title, exact
full text, SHA256 digest and provisional status. They are carried in the captured
mandatory JSON, rather than inserted into the canonical retrieval corpus or its
SQLite/vector caches. This intentional choice preserves the entire dependency
chain and avoids pretending that a newly planned scene already exists on disk.
Oversized mandatory input refuses the run before transmission instead of dropping
old drafts, draft tails or required metadata. The existing compact planning
motivation summary is the only intentionally compact profile representation.

Successful model steps retain immutable `PlanningStepEvidence`: exact role/prompt,
manifest and validated optional passages plus the transient sources used by that
step. `AutopilotDraft.retrieval_steps` exposes this provenance to the caller; the
GUI retains the last successful run's records in memory. Per-request source
reviews expose these inputs before transmission. The accumulated estimated
request-evidence size is limited to 16 MiB; it is not a Python heap bound.
Nothing in this path writes an index. Explicit index maintenance after project
application remains separate.

All scenes and notes are generated before any additions. The final operation
reuses `Project.add_outline`/`add_autopilot_content` with their validation,
exclusive file creation, manifest transaction and rollback. A fresh source check
runs in that mutation worker, including after final outline review. Cancellation
or generation failure applies nothing; rejection preserves manuscript and Undo.
Existing file contents remain unchanged. Source checks do not provide an atomic
lock against arbitrary external writers. Once an approved transaction starts it
finishes through the existing commit/rollback behavior. After successful
Auto-pilot, the outer form returns without starting another outline request.

## Criterion-by-criterion verification

| Gate / precondition | Normal, failure and stale-state evidence |
| --- | --- |
| RAG-09.1 prompt-only/project mode and streaming parity | `test_rag_generation.py`, `test_captured_generation.py`, `test_ollama_client.py`; exact reviewed role/prompt/output reserve/full-context flags in both modes; no implicit ordinary-mode attachment; source/result rejection and Undo |
| RAG-09.2 brief plus mandatory compact motivations | `test_planning_retrieval.py::test_planning_preserves_mandatory_motivations_and_exact_source_review`; tests both Suggest and outline; verified source IDs, exact request and proposed-invention role boundaries |
| New project, no project, missing index | Domain coverage tests for all three scopes; `test_planning_retrieval_ui.py::test_new_empty_project_without_index_can_plan_and_draft`; four request reviews with explicit no-hit coverage |
| Source exclusions and rebuild | Domain exclusion tests and free-prompt UI rebuild tests; changed exclusions cannot be sent unchanged; only optional scene/note IDs accepted |
| Auto-pilot plan and every draft | Full sequential domain test and GUI-thread/request-identity test; source review before every generation; explicit autonomous confirmation |
| Transient provenance, full tails, no index writes | `test_autopilot_full_transient_sources_and_provenance_never_enter_index`; tail beyond 1600 characters survives into later prompts; all prior IDs/digests/status retained; exact index bytes unchanged before and after application |
| Mandatory metadata and budget | Full metadata JSON and >5000-character input tests; required transient overflow fails before review/provider; estimated run-evidence cap fails before provider; no smaller-context retry |
| Cancellation/failure at each sequential step | Domain parameterization over plan and three scene calls, both cancellation and provider error; no project additions; second GUI source-review rejection applies nothing |
| Stale disk/buffer/project/settings/brief/run | GUI changes during source review and blocked generation; late success/error discarded; closed-source changes before dispatch, between steps and before application invalidate the run |
| Queued callback ownership | `test_queued_old_result_cannot_reset_a_new_request_in_the_same_form`; an old queued result cannot re-enable the form or clear a newer worker/busy state |
| Final outline review | Rejection and disk/buffer/settings/run changes preserve the existing project; source verification happens again in the apply worker |
| Transaction and Undo | Injected manifest-write failure removes new files and retains original manifest; existing manuscript buffers/Undo survive rejected/stale suggestions; approved additions preserve existing file contents |
| Existing shared review behavior | Existing Auto-writer retrieval tests continue passing with their original defaults; bridge configuration adds planning labels/source kinds without changing Auto-writer policy |
| End of autonomous setup | Tests verify successful Auto-pilot sets its completion flag and the outer setup does not launch a second outline |

Focused commands:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_planning_retrieval.py tests/test_planning_retrieval_ui.py tests/test_project_setup.py tests/test_auto_writer_retrieval.py tests/test_auto_writer_retrieval_ui.py tests/test_rag_generation.py tests/test_captured_generation.py
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_planning_retrieval.py tests/test_planning_retrieval_ui.py tests/test_auto_writer_retrieval_ui.py tests/test_i18n.py
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q
```

The Auto-writer test wait helper now runs a short Qt event loop rather than
holding the GIL through `QTest.qWait`. An investigative faulthandler trace showed
the Python worker still executing lexical lookup while the test loop occupied
the GUI thread. The original timeout was retained; production timing/budgets were
not relaxed. Native-only checks remain skipped in the offscreen suite. This gate
requires offline tests and makes no native accessibility, live-model quality or
server runtime-allocation claim. Final results are in the progress checkpoint.

## Clean Code completion review — RAG-09.2, RAG-09.3, RAG-09.4

- Intent: a single explicit planning opt-in; transient drafts and established
  sources have separate names and provenance.
- Ownership: run/budget/provenance rules live in `app/project/planning_context.py`;
  prompt validation remains in existing AI services; Qt orchestration is separate;
  no UI code calls Ollama HTTP directly.
- Safety: baseline checks, author reviews, queued workers, stable IDs, open-buffer
  stamps, existing additive transactions, rollback and Undo are retained.
- Errors: current refusals are visible; stale late errors cannot overwrite author
  edits or apply partial batches; no silent reference truncation is introduced.
- Tests: deterministic normal/failure/stale regressions and full offline suite;
  native/live checks are explicitly outside the claim.
- Diff: no dependencies or unrelated production refactor; shared review bridge
  retains Auto-writer defaults; README/UK and catalogs describe the opt-in.
- Report: RAG-09 closure is independent of the still-open RAG parent and later
  scene-character/analysis/translation work.
