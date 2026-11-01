# Auto-writer draft review — TASK-024.V1

Reviewed 2026-11-01 from run_auto_writer, AutoWriterReviewDialog, MainWindow's
capture/review/commit callbacks and Project.replace_scenes_transactionally.

- .01–.02: generated scenes remain in an AutoWriterResult, separate from disk
  text, until review. The scene list uses title and stable ID; its read-only
  preview changes with the current row. Progress also shows completed drafts.
- .03: checkboxes select drafts; Apply uses only selected IDs. Cancel or an empty
  selection applies nothing. Existing keyboard/accessibility tests cover arrow
  navigation, Space toggling and exposed instructions.
- .04: later drafts may use earlier generated drafts as context, even when users
  subsequently reject those earlier drafts. The review explicitly warns about
  this; partial selection does not regenerate dependent drafts. The selected
  replacement set and expected-disk set are filtered together while all captured
  context checks remain. Selected changes are one transaction.
- .05: pre-run snapshots include source text (including open buffers). Captured
  project/settings/editor generations guard review and results; the domain
  transaction validates expected text/context and stages replacements before
  applying. Newer buffer edits are not overwritten by completion callbacks.

`test_auto_writer_review_applies_only_selected_and_rejects_stale` covers select,
cancel and edit-during-review and verifies both scene files. Existing setup tests
cover pre-run snapshots, only-empty-scene mode, associated-character context,
changed-disk rejection, line-ending-preserving all-target replacement, rollback
on late replace failure, staging cleanup and retained snapshot after generation
failure. `test_auto_writer_ui_refines_scene_and_updates_open_buffer` checks the
successful UI path. Fifteen focused Auto-writer/review tests pass; the unchanged
implementation is covered by the full 868-passed/2-skipped suite.

No behavior, strings or redundant tests changed; existing README accurate.
Numbered tickets/V1 verified. Parent/V2 remain partial for native shortcuts,
screen-reader and release-catalog verification; shared TASK-005 independent-writer
race and rollback/crash limitations remain. No claim of cross-process transaction
isolation or automatic consistency repair after partial draft acceptance.
