# Spelling and grammar review — TASK-021.V1

Reviewed 2026-11-01 from SpellcheckService, validation helpers, the review dialog,
MainWindow result/review guards and EditorWidget's explicit apply operation.

- .01: provider calls run in FunctionWorker. The service accepts JSON or typed
  Suggestion lists, applies captured revision and source validation, orders valid
  ranges, removes overlap and retains at most 200 findings. Typed objects now
  validate field types and replacement/explanation limits before sorting, like
  JSON input: Python dataclass annotations alone did not enforce this contract.
  Fourteen malformed-object cases and a count/order/length/overlap boundary
  regression in test_spellcheck_service.py verify the correction.
- .02–.04: the dialog shows original/proposed text, type and explanation, with
  individually checkable findings. Cancel returns before application. Existing
  `test_review_lists_expose_instructions_and_support_keyboard_selection`
  verifies arrow/Space interaction and accessible instructions offscreen.
- .05: accepted results recheck editor identity, revision, captured findings,
  valid source and nonoverlap. Replacements run in reverse position order inside
  one Qt edit block. `test_batch_spelling_review_preserves_selection_and_undo`
  covers apply, selected-only, cancel, stale text and overlap, with emoji offsets
  and one-step undo. `test_spellcheck_worker_displays_suggestion_without_editing`
  verifies automatic findings do not edit the document.
- Existing worker regressions cover results arriving after edits, coalescing,
  cancellation and shutdown. Direct editor application also invokes the shared
  validation helper, so malformed typed objects cannot reach slicing/Qt edits.

Numbered subtasks/V1 are verified. No new controls or Qt strings were added;
existing English/Ukrainian review text remains. V2 release-catalog and native
keyboard/screen-reader checks are still pending; the parent remains partial.
Tests use fake providers and no Ollama server. Validation remains conservative
and does not establish that a model's proposed correction is linguistically right.
