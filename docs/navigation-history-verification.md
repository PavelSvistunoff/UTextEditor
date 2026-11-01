# Navigation history verification — TASK-019.V1

Reviewed 2026-11-01 from NavigationHistory and MainWindow recording/restoration
callers. This is session-local positional navigation, not document undo.

- .01: View menu Back/Forward actions delegate to a 100-entry history. Equal
  consecutive points are deduplicated; recording after Back removes the forward
  branch. `test_history_is_bounded_skips_stale_points_and_discards_forward_branch`
  verifies bounds, stale skipping and branch replacement.
- .02: explicit scene/note openings record the departing editor and destination;
  successful project-search jumps record the exact selection. Typing and cursor
  movement do not record points. No persistence serializer includes this history.
- .03: restoration uses Qt positions and anchors only when the original editor
  revision matches. `test_navigation_history_restores_project_search_selections`
  verifies emoji offsets, Back/Forward, selected text and preserved dirty text.
- .04: weak references, Qt object validity, open-tab membership, revision,
  project identity, binding, stable item lookup and current path are checked.
  OSError/RuntimeError during path resolution now skip the point. Two
  `test_navigation_history_skips_unverifiable_project_path` cases verify fallback
  to a valid earlier point while both buffers and source bytes remain intact.
  Four `test_navigation_history_skips_stale_targets_without_recording_typing`
  cases exercise edited, closed, removed and relinked targets; normal editing
  does not create entries, and original/replacement files remain unchanged.
- .05: one fresh history is created per MainWindow; editor references are weak
  and no manuscript strings are captured. Project objects are retained by points,
  bounded by the entry limit. There is no cross-session position restoration.

Eight focused tests pass. Numbered subtasks/V1 are verified; V2 and parent remain
partial for native shortcut conflicts, keyboard/screen-reader workflows and
release-catalog verification. No controls or Qt source strings changed; existing
translated unavailable-history feedback is retained. Native checks are not
inferred from offscreen test results.
