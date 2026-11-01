# Inline completion display — TASK-026.V1

Reviewed 2026-11-01 from EditorWidget's presentation/invalidation/key handling
and MainWindow's captured-result guards.

## Presentation decision (.01–.03)

Retain a single-line, non-destructive ghost only at the end of the current text
block and only when its complete width fits the viewport. A wrapped/multiline
popup could show more text but would introduce another focus/selection surface
and require additional positioning and screen-reader design. Eliding the ghost
could hide text that Tab would insert. Keeping the complete visible suggestion
and rejecting unrepresentable output preserves predictable explicit acceptance.
No popup or multiline display is introduced solely to satisfy an investigation.

The block-end check now uses QTextCursor.atBlockEnd instead of copying the whole
editor string and its suffix. It also conservatively rejects positions before a
soft line break inside a Qt block. Long suggestions and suggestions containing
line breaks are rejected; a narrower resize dismisses a ghost that no longer
fits. These decisions are presentation limits, not a guarantee of broader
large-document typing latency (TASK-006).

## Acceptance evidence (.04–.05)

`test_completion_is_non_destructive_and_tab_accepts_it` verifies Tab acceptance;
existing tests cover multiline/empty rejection, mid-block text protection,
selection/text invalidation, word separation and small-window resize dismissal.
`test_escape_dismisses_completion_before_exiting_distraction_free_mode` retains
Esc precedence. The new
`test_completion_visibility_does_not_copy_the_entire_document` makes whole-buffer
capture fail during end/mid-block checks on a many-paragraph Unicode document,
verifying visibility changes leave the document/revision intact. Cursor/selection
changes invalidate the ghost before ordinary typing continues.

Eleven focused completion tests pass. Numbered tickets/V1 verified; parent/V2
remain partial for native keyboard/screen-reader, visual system-palette and
release-catalog verification. No new controls or translatable strings. Offscreen
regressions establish safe supported presentation, not OS-wide shortcut or
accessibility guarantees. README documents the retained display policy.
