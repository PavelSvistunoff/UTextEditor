# Optional streaming preview — TASK-025.V1

Reviewed 2026-11-01 from AIProvider/OllamaClient, StreamingWorker, MainWindow's
prompt-generation callbacks and StreamingPreviewDialog/GeneratedTextDialog.

- .01: the persisted streaming_preview setting selects AIProvider.generate_stream
  for explicit prompt generation; ordinary nonstreaming generation remains the
  default. Ollama endpoint/NDJSON/payload handling stays in OllamaClient.
- .02–.03: StreamingWorker runs synchronous provider code off the GUI thread.
  A locked chunk queue is drained by a 75 ms GUI timer; provisional read-only
  output has a separate dialog and never edits the manuscript. The final result
  still opens GeneratedTextDialog and requires Insert.
- .04: the worker tracks total emitted characters even after draining and rejects
  totals/final results above 256 Ki characters. Ollama additionally bounds the
  total NDJSON response to 16 MiB. These bound stored output, not total process
  RSS or arbitrary allocations inside a different provider implementation.
- .05: the GUI timer checks cancellation, request generation, editor identity,
  revision/cursor/selection and settings generation. Final application repeats
  captured-state checks. Closing the provisional dialog cancels the request.
  Provider polling cannot interrupt a currently blocked socket read; cancellation
  may wait for data/timeout, as already documented in README.

`test_streaming_preview_is_provisional_and_respects_cancellation` covers explicit
accept, reject, cancellation and stale edits with fake chunked output; acceptance
is undoable. `test_streaming_worker_bounds_total_output_even_after_draining`
verifies the cumulative bound. Ollama tests verify chunk delivery, NDJSON flags,
malformed/cancelled/oversized responses, and the separate nonstreaming request.
Nine focused streaming/nonstreaming tests pass. Full unchanged implementation:
868 passed, 2 skipped. No redundant tests or runtime/string changes in this audit.

Numbered tickets/V1 verified; parent/V2 remain partial for release-catalog and
native keyboard/screen-reader verification. Live Ollama compatibility is not
claimed by fake-response tests; no server is required for these offline checks.
