# Project translation review — TASK-023.V1

> **Evidence snapshot:** This document records an earlier investigation or verification, not a fresh test run or a second implementation queue. Check [active tickets](../TASKS.md) and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md) before using it to close a gate. Native GUI and screen-reader checks require real platform evidence.

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
checks byte-exact rollback of a late manifest-install failure and temporary file cleanup.
The UI refreshes only still-current captured buffers after commit.

Twelve focused translation tests pass; the unchanged implementation is covered
by the full 868-passed/2-skipped suite. No runtime behavior, strings or redundant
tests added for this audit; README already describes the workflow. All numbered
tickets/V1 verified; parent/V2 stay partial for native keyboard/screen-reader
and release-catalog checks. The independent-process final-check race also
applies here. The tested transaction rollback is not a guarantee against process
crashes, rollback I/O failure or uncooperative concurrent writers.


## Character-text extension — verified implementation

Whole-project translation now also captures every populated profile string/list
entry, relationship prose and scene-association prose. This includes goal notes,
knowledge statements, all background/personality/arc values, state values and
quotations. Character/relationship/scene IDs, dictionary keys, goal states,
knowledge kinds, presence, state-change field identifiers, priorities, trust and
portraits retain their original values. Empty strings and whitespace-only fields
remain unchanged and do not consume model requests or populated-field limits.

`character_translation.py` owns the field inventory and copy-based application.
Only paths captured from a validated manifest can be applied; missing/foreign
paths and invalid values are rejected. Generation captures the manifest deeply,
includes these fields in the existing 500-field / 32,000-character bounds and
creates the original full revision before requests. The translated manifest is
validated before review, then installed through the existing scene/note/manifest
transaction after fresh conflict checks. No independent profile write is added.

Consent discloses profile/relationship/scene-development text. Side-by-side rows
include stable IDs and translated field captions; explicit Apply commits the whole
batch, while Cancel and changed profiles preserve author data. Original snapshots
include all original character structure and text. Both translation directions
and both scene groupings are covered, as are error/cancellation during character
requests, malformed names, metadata injection, partial results, source edits,
blank fields/portraits, input bounds and late manifest-install rollback.

Executed focused suite: **387 passed**. Full offscreen: **1137 passed, 2 skipped
in 143.52s**; the skipped cases require a live Ollama server. Cocoa subset:
**4 passed**, using fake providers and simulated review decisions; this does not
establish manual keyboard or screen-reader behavior. Fresh extraction: **1028**
source messages; Ukrainian catalog compiles with **1039 finished** messages and
passes reference/placeholder validation. `git diff --check` passed. No live model
translation quality or arbitrary independent-writer safety claim is made.
