# Project translation review — TASK-023.V1

Reviewed 2026-11-01 from project/translation.py, Project's transaction, MainWindow
translation capture/review/commit callbacks and ProjectTranslationReviewDialog.

- .01–.03: immutable review rows capture project/chapter/scene/note titles and
  scene/note text, using source buffers captured before generation. Side-by-side
  original/translated panes are read-only; selecting a row switches both panes.
  Scene/note labels include stable IDs to distinguish duplicate titles.
  `test_translation_review_navigates_original_and_translated_items` checks both
  panes; `test_project_translation_review_cancels_or_discards_changed_buffer`
  checks unsaved originals and duplicate-title IDs through the actual UI path.
- .04: explicit Apply commits the whole batch; Cancel returns before committing.
  There is no partial translation selection. The two UI cancellation/stale cases
  preserve source files and manifest title.
- .05: project/settings/generation/editor revision checks run before and after
  review. The commit service freshly loads and validates the manifest, exact
  expected document set, disk contents and manifest capture before staging;
  each target is rechecked before installation. The UI uses the existing worker
  pattern for model and transaction operations.

`test_translation_covers_project_titles_scene_and_note_text_and_snapshot` verifies
translated titles and text, pre-generation snapshot including unsaved source,
retained IDs/paths/links and CRLF. `test_failed_translation_does_not_modify_project`
and `test_translation_cancellation_stops_before_translating_next_field` verify
no partial model output is committed. `test_translation_commit_conflict_preserves_entire_project`
rejects external changes, and `test_translation_commit_rolls_back_files_if_late_install_fails`
checks byte-exact rollback of a late manifest-install failure and backup cleanup.
The UI refreshes only still-current captured buffers after commit.

Twelve focused translation tests pass; the unchanged implementation is covered
by the full 868-passed/2-skipped suite. No runtime behavior, strings or redundant
tests added for this audit; README already describes the workflow. All numbered
tickets/V1 verified; parent/V2 stay partial for native keyboard/screen-reader
and release-catalog checks. TASK-005's independent-process final-check race also
applies here. The tested transaction rollback is not a guarantee against process
crashes, rollback I/O failure or uncooperative concurrent writers.
