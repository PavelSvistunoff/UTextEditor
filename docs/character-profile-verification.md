# Character profile verification — TASK-030.V1

Reviewed 2026-11-01 from CharacterDialog, MainWindow's staged profile lifecycle,
model serialization and existing associated-scene navigation.

- .01–.02: Identity, Portrait, Story, Background and personality, Relationships
  and Scene development group the form. Story and Background have independent
  resizable scroll areas. `test_character_profile_long_forms_scroll_and_preserve_fields`
  exercises both at 400x380, scrolls lower fields into view and verifies their
  staged values while leaving the source Character unchanged.
- .03 (partial): the offscreen scroll case establishes reachability of sampled
  lower fields, not native keyboard traversal of every field, screen-reader
  labels, focus reveal or all system font/palette combinations. Keep that gate
  and V2 open rather than inferring them from scrollbar ranges.
- .04: explicit associated-scene navigation hides the same dialog and offers a
  return control. Existing tests for staged edits/return, rechecked association,
  changed project/relationship and failed save are recorded in the related
  navigation audit and remain applicable; mention search does not infer links.
- .05: newly fixed untouched-field loss. The form records initial widget text
  and the captured profile. Save only reparses changed goals/knowledge/arc;
  unchanged fields/dictionary entries restore their exact captured values.
  Thus saving a name/motivation/background edit cannot silently trim other text,
  add/remove empty keys or flatten list entries with embedded line breaks or
  delimiters. Edited fields retain their existing parsing/validation rules.
  Portrait and directed-relationship actions retain their separate staged state.

Three new cases in
`test_profile_save_preserves_untouched_structured_values_exactly` validate model-
serializable input, no-edit Save, editing motivation and editing one background
field, preserving whitespace, empty keys/list entries, multiline list/knowledge/
arc values and a goal containing a delimiter. The original Character stays
unchanged; captured and saved mappings match exactly except explicitly edited
fields. Existing tests cover invalid entries, field clearing, directed relations,
failed-write rollback and staged edits across navigation. Focused character/
profile service/UI tests: 55 passed. No controls or translation strings changed.

.01/.02/.04/.05 and V1 verified; .03 and parent/V2 remain partial for native
keyboard, accessibility and release-catalog review. Exact preservation concerns
untouched values, not a new syntax for editing arbitrary multiline structured
entries. README documents the fix and retained form behavior.
