# Character profile verification — TASK-030.V1

> **Evidence snapshot:** This document records an earlier investigation or verification, not a fresh test run or a second implementation queue. Check [active tickets](../TASKS.md) and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md) before using it to close a gate. Native GUI and screen-reader checks require real platform evidence.

Reviewed 2026-11-01 from CharacterDialog, MainWindow's staged profile lifecycle,
model serialization and existing associated-scene navigation.

- .01–.02: Identity, Portrait, Story, Background and personality, Relationships
  and Scene development group the form. Story and Background have independent
  resizable scroll areas. `test_character_profile_long_forms_scroll_and_preserve_fields`
  exercises both at 400x380, scrolls lower fields into view and verifies their
  staged values while leaving the source Character unchanged.
- .03 (partial): `test_character_profile_narrow_form_keyboard_reaches_profile_fields`
  traverses every profile field with Tab at 400x380 offscreen and verifies Cancel
  leaves the original profile unchanged. Multiline profile fields now give Tab
  to focus navigation instead of inserting a tab character. The scroll case
  establishes reachability of sampled
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

## Direct native acceptance — TASK-030.03

macOS 27.0.1 arm64, Qt 6.11.2, Cocoa, one native screen. Direct native command:
`QT_QPA_PLATFORM=cocoa PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_project_ui.py -k "narrow_profile_all or narrow_form_keyboard or profile_save_preserves_untouched"`
produced **5 passed**. QTest traversed every profile field at 400x380. A full
staged-field case returned from a real associated-scene open, compared all widget
values exactly, saved and checked the reopened YAML model, then cancelled a new
edit without changing persisted data. Three structured-value cases retained exact
untouched values. This is native automated Qt input, not a human screen-reader
audit. TASK-030.03 is COMPLETE under its current criteria; speech/palette and
application-wide focus acceptance remain under TASK-034.


## Empty-field suggestion language resolution

The previous request passed literal `Language: Auto` and told the model to infer
language from the profile, independently of the interface locale. Four regression
cases reproduced that missing explicit language before the fix.

The service now resolves only English/Ukrainian before contacting the provider.
Explicit writing-language selection wins. Auto uses the existing conservative
local detector on human profile values; goal codes and knowledge/arc keys are
excluded. If recognized values are mixed, short, ambiguous or unsupported, the
captured active interface language is used. The UI passes its resolved `en`/`uk`
locale, including when the saved choice is System. Standalone service callers
have an English fallback unless they supply another supported fallback.

Both the prompt and system role explicitly request the resolved language and
instruct the model not to write Russian. Schema keys/codes remain English.
This is request-language resolution, not a guarantee that a live model always
obeys instructions; no speculative output-language classifier or automatic
translation/retry was added. Existing schema checks, worker dispatch, stale-state
checks and explicit review remain. Cancel still leaves profile/project values
unchanged. Offline tests inspect fake-provider requests and lifecycle behavior;
no live Ollama response-language or new native/screen-reader claim is made.

Focused offline suite: **501 passed**. Full offscreen: **1159 passed, 2 skipped
in 161.07s**. Log: `/private/tmp/utexteditor-character-language-full.log`.
Clean Code completion review: intent, ownership, safety, errors, tests, diff and
report checked; no new dependencies or changes to manuscript/undo/transactions.


## Observed model formatting deviations — targeted normalization

The supplied diagnostics showed `turnings_points` in both otherwise Ukrainian
responses, while the canonical schema requires `turning_points`. This caused the
whole proposal to fail the arc validator. Synthetic regressions reproducing both
reported formatting combinations failed before this fix; no manuscript/log text
was copied into the repository.

The service now canonicalizes only that explicitly known arc-key typo. Unknown
fields are not guessed, and aliases colliding with another canonical arc entry
are rejected. Knowledge records joined by semicolons are separated only where a
supported category token follows; ordinary prose semicolons remain. Flattened
goals split only into complete repeated four-part records with valid status and
priority. Other pipes in notes remain untouched. The existing schema and field
size checks still run after normalization, including a second size check for
canonical text. Prompt instructions now explicitly request one entry per line.

Normalization affects generated proposals only, before explicit review. An
integration test verifies the complete request → review → staged form → Save/YAML
path: original author description/name remain intact, arc keys persist canonically,
and distinct goals/knowledge entries are not hidden inside notes. No extra model
request, automatic retry, persistence bypass or language-policy change was added.

Focused offline suite: **571 passed**. Full offscreen: **1168 passed, 2 skipped
in 159.08s**. Log: `/private/tmp/utexteditor-character-format-full.log`.
Clean Code checklist reviewed: intent/ownership/safety/errors/tests/diff/report.
Supplied real model diagnostics identify the defect; no fresh live-model or
native/accessibility claim is made for this parsing-only change.


## Repeated exact arc key — reported 2026-11-13 response

The new diagnostic contains two `initial_state` lines with different prose.
The earlier validator rejected any repeated canonical field, discarding otherwise
valid suggestions. Synthetic regressions reproduced that refusal before the fix.

Exact repeated keys now retain every proposed value in order in a single
semicolon-separated field, for explicit author review. This does not infer that
the statements agree, select a preferred value, deduplicate prose or overwrite an
earlier suggestion. The prompt requests each arc key at most once. Unknown keys,
empty values, canonical/alias collisions and existing output limits still fail.
Normalization only affects generated suggestions; dirty fields, consent, stale
context verification and the explicit Save action remain unchanged.

Regression cases cover equal/different repeated values and an invalid empty
repeat. The Qt integration checks review → staging → explicit Save → YAML,
retaining both values and existing author text. Clean Code completion review:
intent, ownership, safety, errors, tests, diff and report checked; no dependency,
public API or manifest schema change. No live-model or native verification claimed.

Focused offline suite: **331 passed**. Full offscreen suite: **1193 passed,
2 skipped in 146.47s**. Logs: `/private/tmp/utexteditor-duplicate-arc-focused.log`
and `/private/tmp/utexteditor-duplicate-arc-full.log`. `git diff --check` passed.
