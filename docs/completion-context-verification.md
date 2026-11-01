# Completion context verification — TASK-022.V1

Reviewed 2026-11-01 from completion_service.py, character_context.py, MainWindow's
capture/review/send paths and the context/reference-note dialogs.

- .01–.02: Review Completion Context displays the captured Ollama destination
  and exact bounded context before explicit Send. The worker captures closed
  notes and their digests; unsaved open-note strings are captured on the GUI
  thread. `test_reviewed_completion_sends_exact_displayed_context` compares the
  displayed string directly with the fake provider's received string.
- .03: summaries identify dirty source text, partial pre-cursor text, character
  detail limits, unsaved/truncated note buffers and the number of omitted notes.
  Existing `test_review_identifies_omitted_document_prefix` and
  `test_review_identifies_character_detail_limit` cover the first limits. New
  `test_review_labels_unsaved_truncated_and_omitted_notes_without_sending` checks
  real captured unsaved scene/note text, exact provenance labels, omitted text,
  cancellation, dirty-state retention and unchanged canonical scene/note files.
- .04: note selection uses stable IDs, is session-only and resets for a project.
  `test_completion_note_selection_excludes_notes_and_discards_pending_result`
  verifies both exclusion and invalidation of an already-running result.
- .05–.06: the persisted automatic-project-context setting omits project context
  for automatic requests while retaining it for explicit manual requests.
  `test_automatic_project_context_can_be_disabled_without_changing_manual_requests`
  verifies the actual outgoing contexts. Ordinary requests do not open the
  optional review dialog each time; first-destination consent remains required.

Captured editor revision/cursor, settings and project generations and note
editor revisions guard the preview and completion. Closed-note digests are
checked before provider invocation and after it returns.
`test_reviewed_completion_does_not_send_if_closed_note_changes` and
`test_reviewed_completion_does_not_send_after_cancel_or_edit` verify cancellation
and stale protection. `test_changed_closed_note_prevents_request_or_discards_result`
checks both service boundaries. `test_project_scene_completion_receives_notes_and_associated_characters`
and the project context tests verify that only explicitly associated profiles
are included. First-use disclosure, changed-destination and consent-save-failure
regressions cover transmission control. Diagnostics may contain sent prose.

Twenty focused context/disclosure tests pass. All numbered tickets/V1 verified;
parent/V2 remain partial for native keyboard/screen-reader and release-catalog
checks. No new runtime behavior or strings: existing README remains accurate.
The context preview is not a rendering of the full HTTP payload or instructions;
it shows the captured completion context sent to the provider abstraction.
