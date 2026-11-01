# Localization and accessibility checkpoint — TASK-032/034.V1

Reviewed 2026-11-01 against the 879-passed/2-skipped offline suite. This is an
acceptance reconciliation, not a completed native localization/accessibility
audit. No generated release catalogs or unrelated staged artifacts were changed.

## TASK-032

- .01 partial: audit_ui_strings.py reports nine selected-Qt-API candidates. They
  are the application proper name; a status composition containing document
  data, stable encoding/line-ending abbreviations and translated position/status;
  a character-proposal composition containing raw field/value data and translated
  Evidence; pretranslated export filters; a filename/path composition; and four
  language autonyms. None is a newly confirmed unmarked static source in that
  narrow scope. This AST tool cannot establish that all runtime strings are
  translated, particularly dynamically assembled messages and service errors.
- .02/.04 partial: menus and common dialogs/status paths use Qt translation,
  including the new export preview. Raw service exception details still surface
  through str(error), e.g. file decoding/binary errors and project validation.
  Translating error titles is not a complete translation of those details.
  A broader service-error/localization design and workflow inventory remain.
- .03 partial: the Ukrainian source contains 956 message records. Source
  validation, extracted-source coverage, placeholder/plural checks and temporary
  compilation pass. This count includes catalog records and is not a claim that
  956 distinct current workflows were manually audited. Packaged release .qm
  updates and running the released Ukrainian UI on native platforms remain.
- .05 verified: existing translation-validation tests enforce placeholder and
  plural parity, reject malformed/missing entries, and compile selected runtime
  context checks. New export-review strings retain their exact Qt contexts.

`tests/test_translation_validation.py` and `tests/test_i18n.py` passed in the full
suite; the source validator passed independently. Document/AI data, paths and
manuscript strings are not implicitly translated. Existing README fallback
limitations remain accurate. V1 complete as a reconciliation; V2/parent partial.

## TASK-034

- .01 partial: offscreen Quick Open, tab navigation, Find/Replace, review-list
  arrow/Space and completion Tab/Esc regressions cover important keyboard paths.
  They do not establish native shortcut conflicts or every dialog workflow.
- .02 partial: navigation/review/preview widgets have explicit accessible labels;
  a read-only QAccessible probe found a nonempty name for every CharacterDialog
  profile widget through its Qt form labels. Names for the entire application
  and how native screen readers announce changes still require a full audit.
- .03 partial: existing Find/Replace focus-return tests and review keyboard tests
  exercise selected focus/modal behavior. Profile scroll tests at 400x380 prove
  sampled lower-field reachability; full keyboard traversal/reveal of every
  field, system fonts and modal nesting are not manually verified.
- .04 partial: editor system-palette tests and actual PDF dark-palette rendering
  tests pass. They do not verify every control, contrast state or native theme.
- .05 open: no native screen-reader run on macOS/Windows/Linux was performed.
- .06 partial: existing accessible labels, keyboard list toggles and scrollable
  forms address earlier barriers, with regression evidence above. Outstanding
  audit coverage prevents claiming all barriers are identified or fixed.

V1 is complete as an evidence/gap record; V2 and parent stay partial. The same
native/release-catalog limitations remain open in individual UI-task V2 tickets.
They cannot be marked N/A merely because offscreen tests pass. No runtime code,
controls or strings changed in this reconciliation; no redundant tests added.
