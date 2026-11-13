# Localization and accessibility checkpoint — TASK-032/034.V1

> **Evidence snapshot:** This document records an earlier investigation or verification, not a fresh test run or a second implementation queue. Check [active tickets](../TASKS.md) and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md) before using it to close a gate. Native GUI and screen-reader checks require real platform evidence.

Reviewed 2026-11-01 against the 879-passed/2-skipped offline suite. This is an
acceptance reconciliation, not a completed native localization/accessibility
audit. No generated release catalogs or unrelated staged artifacts were changed.

Update 2026-11-13: the packaged English and Ukrainian catalogs were rebuilt
from their current source files. The previous Ukrainian release catalog differed
from a fresh compilation on 579 non-plural source/context pairs. Automated
tests now compare packaged and freshly compiled translations for every source
entry and representative plural numbers. Native UI and screen-reader checks
remain outstanding; this update does not complete the localization audit.




## Backlog reconciliation — catalog build verification

TASK-032.03 is **COMPLETE** against the current TASKS.md wording and removed from
unfinished work. Fresh source extraction found 947 strings; reference coverage,
placeholders and plural validation passed. Both en/uk catalogs compiled to
scratch files (28/955 finished translations). `tests/test_i18n.py` and
`tests/test_translation_validation.py`: **42 passed**, including every packaged
source/context entry and representative numerus parity with fresh compilation.
Command: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_i18n.py tests/test_translation_validation.py`.
Extraction/compilation followed README commands with scratch output paths.

TASK-032 parent remains partial: .01/.02/.04 require broader dynamic/service
workflow inventory and migration. Passing compilation does not establish that
all visible text has been inventoried or native Ukrainian UI was verified.
TASK-016.05, TASK-027.03, TASK-030.03 and TASK-034.01/.02/.03/.04/.06 retain
unmet native, spoken-label, focus, palette or full-audit criteria in their evidence.
No other current ticket is confirmed complete; none is removed on test totals alone.

## TASK-032.04 — standalone save conflict (2026-11-13)

Manual save and autosave now show a translated category for typed external-change
conflicts while retaining the original diagnostic and filename. Regressions use
actual changed and removed files, check dirty text and external contents, and
exercise both UI paths. Project/AI errors and native Ukrainian workflows remain.

## TASK-032.04 — missing standalone file (2026-11-13)

A real `FileManager.open` failure now receives a translated missing-file category
while preserving the original system error and path, including `%1` in a filename.
The packaged Ukrainian catalog is covered by `test_missing_document_error_includes_translated_category_and_original_details`; existing recent-file tests cover dirty-buffer preservation. Other service errors and native Ukrainian workflows remain open.

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
  through str(error), especially project validation and other service paths; standalone invalid UTF-8/binary open errors were translated on 2026-11-13.
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

## Invalid project format — TASK-032.04

Opening a malformed manifest now shows a translated category and original detail.
`test_invalid_project_open_is_localized_and_preserves_active_project` reproduces
a model validation error and checks active project, dirty buffer and busy reset.
Native Ukrainian and remaining project/AI categories are still unverified.

## AI network failures — TASK-032.04

`test_ai_failure_localization_preserves_diagnostics_and_rejects_stale_results`
uses a real OllamaClient failure with mocked networking. Packaged Ukrainian
generation/completion messages preserve diagnostics, including `%1`, and dirty
manuscript text. Stale request and settings generations preserve prior UI status.
Other AI workflows and native Ukrainian operation remain to be audited.

## Project path failures — TASK-032.04

Opening and project mutation warnings share typed project-error formatting.
`test_project_path_error_is_localized_without_losing_diagnostics` exercises an
actual traversal rejection in both UI paths and preserves the diagnostic,
including `%1` in the rejected path. The earlier format-error test remains valid.
Native Ukrainian operation and remaining service error categories are still open.

## Profile save errors — TASK-032.04

The custom profile-save callback now uses shared project-error presentation.
`test_failed_profile_save_reopens_staged_edits` covers generic, format and path
errors with the packaged Ukrainian catalog, exact diagnostics and staged-name
preservation after failure. Project source profile remains unchanged. Other
custom callbacks, native runtime and accessibility remain open.

## Export errors — TASK-032.04

Text and PDF export share error presentation, preserving the localized source-file
protection and using typed project-format/path categories. Eight injected callback
cases cover both routes, exact diagnostic retention, generic system errors and
busy-state reset. Native export/localization review remains open.

## Character scene-search failures — TASK-032.04

`test_character_scene_search_failure_localization_and_stale_guards` covers
format, path and system errors for current, changed-project and changed-generation
results. Current typed errors use shared Ukrainian categories and preserve exact
diagnostics; stale results show no warning. Native UI review remains open.

## Character profile export — TASK-032.04

Six injected UI cases cover generic/format/path failures and overwrite confirm/
cancel. Typed categories use the packaged Ukrainian catalog; exact diagnostics
and existing destination content are preserved. Filesystem export now runs in a worker on a captured profile. Project/generation
changes suppress stale success/failure feedback. Native UI unverified.

## Character-development failure feedback — TASK-032.04

Five worker-based offline cases verify the packaged Ukrainian title and original
Ollama diagnostic for current failures, and no warning after scene/profile/settings/
project changes. Four stale cases failed before adding the existing context guard
to the failure callback. Button reset remains available; no proposal is staged.
Native Ukrainian runtime and accessibility remain unverified.

## Project-analysis context heading — TASK-032.01/.02/.03

Inventory finding: MainWindow._project_analysis_finished built the visible
“Captured local context at” heading outside tr(). Reproduce through Project AI
scene summary or continuity review; the AnalysisWindow sources label owns the
visible result. The caller now uses a single MainWindow translation template
with timestamp and joined source labels as arguments. Two packaged Ukrainian
regressions failed before the change and retain literal placeholder-like source
names and model output. Native UI verification remains open.

## Revision load/compare failures — TASK-032.01/.02/.03/.04

Inventory: MainWindow._revision_snapshots_failed and _revision_comparison_failed
passed unmarked f-strings to RevisionHistoryDialog.show_error. Reproduce by
opening revision history on an unreadable store or comparing an unavailable
snapshot. Both now format translated MainWindow templates. Eight injected UI
cases cover load/compare, visible/hidden dialog, project identity and selection
generation changes, preserving exact error details. Three untranslated cases
failed before change; stale checks already passed. Native UI remains open.

## Project-search failure feedback — TASK-032.01/.02/.04

Inventory: MainWindow._start_project_text_search failed callback displayed
str(error) directly in ProjectSearchPanel.status and did not validate captured
project context. Ten worker cases cover success/failure for current, changed
project/generation, closing and superseded requests. A translated failure wrapper
preserves exact diagnostics; shared completion logic prevents stale feedback or
clearing a newer request. Three baseline cases failed before the fix. Native UI
review remains open. Source extraction and packaged parity checks are recorded
in the current implementation checkpoint.

## Project document-open failure — TASK-032.01/.02/.04

MainWindow._project_document_open_failed now shares typed project error
presentation for both the warning and nonblocking binding-verification status.
Both worker connections capture project generation. Eight callback cases check
current/project/generation/closing states and dirty text; four real-worker cases
check new opens and existing-tab bindings across a generation change. Pending
keys are released even for stale failures. Original diagnostic details remain;
no new translation strings. Native runtime remains unverified.

## Revision creation — TASK-032.01/.02/.04

MainWindow._revision_snapshot_failed now uses shared typed project categories.
Success and failure share captured project/generation/closing checks and existing
busy-state cleanup. Eight worker cases check current/changed/closing feedback;
four name-prompt cases reject cancelled or changed project/generation/busy state.
Five baseline cases failed before the fix. No new strings; Ukrainian packaged
category and exact diagnostic placeholders are verified. Native UI unverified.

## All-remaining-task pass — native capability and findings

Direct Cocoa Qt is available (one screen), macOS 27.0.1 arm64 / Qt 6.11.2.
Native profile/review run: 31 passed. Narrow all-field/structured profile run:
5 passed; TASK-030.03 closed in profile evidence. Native Find/Replace/context/
review run: 24 passed, 1 failed: FindReplaceWidget minimum width 429 vs requested
420. This is a reproduced TASK-034.03/.06 defect, not a successful full audit.
Spoken VoiceOver labels cannot be observed with the available tools; TASK-034.02
remains BLOCKED for speech acceptance. System light/dark/high-contrast switching
and screenshot matrix not performed; TASK-034.04 remains BLOCKED for native matrix.

Expanded AST audit covers show_error, AnalysisWindow sources, concatenations,
format/replace wrappers and conditionals. It found writing-goal status/pause and
autosave feedback missed by the earlier heuristic; these are migrated to owning
MainWindow templates. Remaining ten candidates are compositions of translated
labels/data, application name, paths, filters and language autonyms. This is
still a heuristic; recovery-worker English explanations and broad raw-service
workflow inventory keep TASK-032.01/.02/.04 at CHECKPOINT rather than COMPLETE.

## Native narrow Find/Replace retest — TASK-034.03/.06

macOS 27.0.1 arm64, Qt 6.11.2 Cocoa: original native run had 24 passed and
1 failed (429px minimum width at 420px request). Options now occupy a separate
row; visual inspection then found clipped status text, so status also has its
own row. Regression checks a full word and wrapped-text height. Final focused
native run: **25 passed**; offscreen Find/Replace/review: **23 passed**.
Native widget grabs were inspected at 420px in current system, dark-test and
contrast-test palettes: `/private/tmp/utexteditor-native-acceptance/{system,dark-test,contrast-test}.png`.
The latter two are synthetic Qt palettes on Cocoa, not actual OS theme/high-contrast
transitions; they do not close TASK-034.04. VoiceOver speech was not captured.

Final expanded Cocoa run of project UI, editor, Find/Replace, context/review
dialogs and settings: **392 passed**. An earlier run found one test assuming an
embedded menu on Cocoa; the test now explicitly uses embedded menu mode. Actual
macOS global-menu restoration is not established by that test. Full offscreen:
**1056 passed, 2 skipped**. TASK-034.06 is COMPLETE for reproduced width/clipping
barriers and removed from backlog; .02 speech, .03 comprehensive focus inventory
and .04 actual OS palette matrix remain incomplete.

## Recovery explanations and retained open diagnostics

Recovery captures three UI-localized explanations in a frozen message value before
worker invocation. The static helper keeps English defaults for existing callers.
Three packaged Ukrainian cases keep dirty recovered text, original scene files and
recovery snapshots, even after removing the translator before worker work.
The binary/UTF-8 open wrapper now retains original diagnostics; the added assertion
failed before the fix. Final targeted Cocoa runtime: **10 passed**, covering these
paths and daily-goal/autosave labels. Broader service workflow inventory remains.

Final environment check: ApplicationServices `AXIsProcessTrusted()` returned
**False**. Native QTest events inside Qt were possible; broader OS accessibility
automation/speech/system-display matrix was not authorized for this process.
Final complete offscreen run after recovery/diagnostic changes: **1059 passed,
2 skipped**. Full outcome matrix: [all remaining tasks](all-remaining-tasks-checkpoint.md).

Supplemental non-tr() constant inspection also found still-untranslated template/
Auto-pilot helper statuses and unavailable/orphan target labels in ProjectView.
Concrete owners and reproduction paths are listed in
[the residual inventory](all-remaining-tasks-checkpoint.md#concrete-residual-localization-inventory).
Thus source/catalog parity alone does not close remaining TASK-032 work.

## TASK-034.03 — completed dialog focus acceptance

The constructor inventory contains all 24 standalone QDialog subclasses in the
current app/ui source. A modal-exec keyboard matrix verifies initial focus,
forward/back Tab without text mutation, Enter on Cancel or Esc rejection and
actual native focus return to the owner. Three additional consent cases verify
initial Not now, Enter rejection and explicit Enter/Space Allow. Final result:
**27 passed offscreen and 27 passed on Cocoa**. The broader earlier native UI
corpus passed 392 tests. Consent initially had no native focused control; explicit
Not now focus/default fixed that reproduced defect. Auto-deleting dialogs are
handled through finished signals/validity in the test harness.
TASK-034.03 is COMPLETE for these dialog criteria. Actual macOS global menu
restoration, VoiceOver speech and OS light/dark/high-contrast transitions are
not asserted by this acceptance; the latter tickets were removed separately.


## Final reconciliation — current backlog closed

TASK-032.01/.02/.04 and TASK-034.03 are COMPLETE for the current acceptance
criteria. This supersedes earlier partial inventories in this historical log.
All 35 UI modules and helper-routed messages were reviewed; findings, reproduction
paths and data/diagnostic exclusions are in [the final inventory](ui-localization-inventory.md).
Native app-wide qtbase and application catalogs use native QTranslator lookup;
English and missing-resource fallback clear the previous standard-control language.
Extraction found 970 messages; Ukrainian has 980 finished entries. Full offscreen:
1093 passed, 2 skipped; final focused fallback suite: 47 passed; native dialog
matrix: 27 passed; final native subset: 44 passed; earlier expanded native: 392 passed.
See [final acceptance](all-remaining-tasks-checkpoint.md) for exact scope and limits.
VoiceOver speech and actual OS appearance gates were removed externally, not
completed. Synthetic palettes and offscreen tests do not establish those checks.
