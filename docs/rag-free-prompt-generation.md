# RAG-09.1 — explicit free-prompt project generation

This bounded batch covers the first RAG-09 requirement. The parent and
RAG-09.V1 remain open: brief suggestions, outline planning and Auto-pilot still
need RAG-09.2–4. No native gate or live-model quality claim is closed here.

## Preconditions and behavior

The separate **AI > Generate with Project Context…** action requires AI enabled,
an open project, an editor and a positive explicit Ollama token window. Ordinary
**Generate..** remains prompt-only. A standalone editor can be the insertion
destination when a project is open; its text is not automatically attached.
Without a project this action reports its precondition; ordinary generation is
still available.

The author's prompt drives lexical retrieval. For a bound scene the author can
explicitly include the selection, or the complete scene when nothing is selected,
as mandatory context. This also anchors earlier-scene filtering and associated
character context. Without that choice, project-wide search can retrieve scenes
across manuscript order with the shared policy's chronology labels. The request
review lists the actual role, prompt, destination, source decisions, omitted
sources and conservative budget. Optional source exclusions require rebuilding.
Required author text is never shortened to fit. A missing index is visible and
uses the shared mandatory-only fallback. This action uses lexical retrieval;
it neither sends embeddings nor downloads models.

Source capture, lookup, generation and verification run in workers. GUI callbacks
check editor/revision/cursor/selection, project/settings/request generations and
all captured open scene/note buffers. Both output modes send identical frozen
role, prompt, output reserve and `require_full_context=True`. Ollama streaming
now supports the same `truncate:false` and `shift:false` contract as non-streaming
generation. Metadata/capacity checks retain their existing limits: this is not
proof of server runtime allocation or compliance.

Streaming chunks are provisional. The shared captured-generation service verifies
sources before and after generation, suppresses chunks after cancellation, rejects
non-text chunks/results and drops stale results or late failures. A final draft
requires explicit Insert. After that review, another worker verifies the source
snapshot before one Qt edit block replaces the captured selection or inserts at
the captured cursor. Rejecting a review preserves the author's existing Undo.
Snapshot verification does not lock out arbitrary concurrent external writers.

## Criterion-to-test review

| Criterion | Deterministic evidence |
| --- | --- |
| Same frozen context in either mode | `test_captured_generation.py::test_modes_send_identical_frozen_request`; `test_rag_generation.py::test_exact_reviewed_prompt_in_both_modes_and_undo` |
| Ollama full-context streaming payload | `test_ollama_client.py::test_full_context_stream_disables_truncation_without_changing_request_text` |
| Source/revision/settings/cancellation changes | `test_rag_generation.py::test_changed_context_cannot_insert` at source review, generation and output review |
| Closed source changes and late provider errors | `test_captured_generation.py::test_source_changes_drop_result_and_late_failure`; final Insert worker check in UI tests |
| Cancellation and malformed output | `test_captured_generation.py` cancellation, malformed chunk and current failure tests; existing streaming worker/client limits |
| Explicit source exclusions and missing index | `test_rag_generation.py` rebuild and missing-index tests |
| Explicit current selection, rejection and Undo | `test_rag_generation.py` selection/Undo and both review-rejection tests |
| No-project behavior | `test_rag_generation.py::test_no_project_refuses_without_dispatch` |
| Ordinary prompt-only path retained | Existing generation tests in the full offline suite; unchanged `generate_from_prompt` |

Run focused tests with:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_captured_generation.py tests/test_rag_generation.py tests/test_ollama_client.py
```

## Completion review

- Intent: one explicit action; ordinary generation retains its existing inputs.
- Ownership: UI orchestration is in `rag_generation.py`; capture/budget/policy
  stay in existing project services; HTTP changes stay in the provider.
- Safety: explicit source/result review, stale-source rechecks and one undoable
  insertion; no project writes or index mutation.
- Errors: current failures remain visible; stale results/failures do not insert.
- Tests: focused and full offline results are recorded in the progress checkpoint;
  no live server is required. Native and live-model behavior were not evaluated.
- Diff: no dependencies, broad refactors, local configuration or unrelated
  bytecode changes included; English/Ukrainian UI catalogs updated.
- Report: RAG-09.1 is separate from the still-open planning/Auto-pilot parent gate.
