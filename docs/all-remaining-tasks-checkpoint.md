# All remaining tasks — final acceptance

The current TASKS.md backlog is complete. Six of the eight tickets present at
this run's start were completed; two were removed externally and are **not**
counted as completed. Repository-wide Clean Code refactoring is a separate,
ongoing effort; this report does not declare every repository module finished.

Environment: macOS 27.0.1 arm64, Qt 6.11.2, Cocoa, one native screen.
`AXIsProcessTrusted()` returned False. Unrelated staged bytecode and DS_Store
changes were preserved and excluded from scoped commits.

| Ticket | Outcome | Acceptance evidence |
| --- | --- | --- |
| TASK-030.03 | COMPLETE | Native keyboard traversal at 400x380; all staged profile fields survive scene return, Save/YAML reopen and Cancel. Five focused native cases passed. |
| TASK-032.01 | COMPLETE | All 35 UI modules reviewed, including helper-routed strings and dynamic service errors; ownership, reproduction and exclusions recorded in the localization inventory. |
| TASK-032.02 | COMPLETE | Inventoried wording migrated to owning Qt contexts; placeholders/IDs preserved; Ukrainian runtime tests, catalog parity and native standard controls verified. |
| TASK-032.04 | COMPLETE | Typed file/project/export/AI/recovery errors reviewed; localized categories retain original diagnostics and dirty data. Recovery messages captured before workers run. |
| TASK-034.02 | REMOVED EXTERNALLY | Actual VoiceOver spoken-label verification was not performed; removal does not establish acceptance. |
| TASK-034.03 | COMPLETE | All 24 standalone QDialog classes covered by native initial/return focus, Tab/back-Tab and keyboard cancellation matrix; 27 cases passed. Explicit consent Enter/Space acceptance retained. |
| TASK-034.04 | REMOVED EXTERNALLY | Actual OS light/dark/high-contrast transitions were not performed. Synthetic Qt palettes do not establish this gate. |
| TASK-034.06 | COMPLETE for reproduced barriers | Native Find/Replace minimum-width and clipped-status failures reproduced, fixed with separate rows, then retested and visually inspected at 420px. |

## Verification

- Full offscreen command: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest`:
  **1093 passed, 2 skipped in 124.43s**. Durable local result:
  `/private/tmp/utexteditor-final-native-translator/result.json` (returncode 0),
  with `pytest.log` beside it.
- The final missing-resource English-reset guard was then checked by the focused
  i18n/catalog/audit suite: **47 passed**.
- Actual native Cocoa expanded UI/editor/settings corpus: **392 passed**;
  dialog focus matrix: **27 passed**; final focus/localization subset:
  **44 passed, 311 deselected**. These are overlapping checks, not additive totals.
- Native profile/review subset: 31 passed; focused narrow profile: 5 passed;
  Find/Replace/context/review: final 25 passed after a reproduced layout failure.
- Extraction: **970 source strings**; Ukrainian validation passed against fresh
  extraction; compilation: **980 finished Ukrainian**, **28 finished English**.
  Ten audit candidates were individually reviewed as data/composed translated
  labels/autonyms; dispositions are in the inventory.
- `git diff --check` passed. Tests use fake providers; no live Ollama required.
- An intermediate full run using a Python translator override was stopped after
  observed slowdown/stall and is not a passing result. Translation lookup now
  uses native QTranslator instances; the successful full run above uses that design.

## Scope and review

See [source inventory](ui-localization-inventory.md) and
[localization/accessibility evidence](localization-accessibility-checkpoint.md).
Native widget captures remain temporarily under
`/private/tmp/utexteditor-native-acceptance/`; dark/contrast captures use synthetic
palettes. Global macOS menu visibility, VoiceOver speech and OS appearance modes
are not claimed verified. Manuscript data, AI prompts and original diagnostic
payloads remain unchanged; arbitrary user/generated text is not translated.

Clean Code completion review applied to each selected ticket:

- [x] Intent: focused message capture, explicit translator lifecycle and readable tests.
- [x] Ownership: UI orchestration and provider/domain boundaries preserved.
- [x] Safety: dirty buffers, undo, IDs, rollback, stale responses and explicit AI consent preserved.
- [x] Errors: translated categories retain diagnostics; missing catalogs reset to English.
- [x] Tests: focused, full offscreen and directly executed native evidence recorded above.
- [x] Diff: scoped changes, no new dependencies; catalogs and user documentation updated.
- [x] Report: removed gates and native verification limits explicitly distinguished.

No current backlog ticket remains to resume. For separately authorized repository
refactoring, inspect `git status --short`, `docs/refactoring-plan.md` and the latest
`docs/refactoring-progress.md` checkpoint before selecting another bounded change.
