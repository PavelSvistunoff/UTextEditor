# All remaining tasks — execution checkpoint

Status: **incomplete**. Every ticket present at the start was reviewed in this
run. Two were completed; the others retain unmet criteria. Automated native Qt
input is distinguished from human screen-reader/system-appearance verification.

Environment: macOS 27.0.1 arm64, Qt 6.11.2, Cocoa, one native screen.
`AXIsProcessTrusted()` returned **False**: process-level macOS Accessibility
automation permission is not granted. Existing
tracked bytecode changes were preserved and excluded from scoped commits.

| Ticket | Outcome | Evidence / remaining criterion |
| --- | --- | --- |
| TASK-030.03 | COMPLETE | Native all-field keyboard traversal at 400x380, exact staged values across associated scene return, Save/YAML reopen and Cancel. Five native cases passed; removed from TASKS.md. |
| TASK-032.01 | CHECKPOINT | Extended AST inventory detects concatenation, conditional, format/replace and custom wrappers. Found and fixed daily-goal/autosave/recovery text. Exhaustive dynamic/service workflow inventory remains. |
| TASK-032.02 | CHECKPOINT | Newly inventoried messages use owning MainWindow context and captured UI-language values; remaining inventory can still expose migrations. |
| TASK-032.04 | CHECKPOINT | Recovery explanations localized; original binary/UTF-8 diagnostic detail retained after a failing regression. Representative failure paths covered, broader service/error workflow review remains. |
| TASK-034.02 | BLOCKED (speech) | Native accessible-name review tests pass; actual VoiceOver speech cannot be observed through available tools. Full spoken-label audit remains. |
| TASK-034.03 | CHECKPOINT | Expanded native UI/editor/settings corpus: 392 passed. Initial/return focus, key and cancel paths have native coverage; complete dialog inventory and actual macOS global menu behavior remain unverified. |
| TASK-034.04 | BLOCKED (OS appearance matrix) | Inspected native widget grabs at 420px with current system, synthetic dark and synthetic contrast palettes. Actual OS light/dark/high-contrast transitions and full screenshot matrix were not performed. |
| TASK-034.06 | COMPLETE for reproduced barriers | Native Find/Replace width 429px at requested 420px and clipped status fixed with separate rows; geometry regression, native retest and inspected grabs pass. Removed from TASKS.md. Other unverifiable acceptance stays under .02/.03/.04. |

## Actual checks

- Native profile/review subset: 31 passed.
- Native narrow profile / structured values: 5 passed.
- Native Find/Replace/context/review subset: initially 24 passed, 1 failed;
  final 25 passed after layout correction.
- Expanded native project UI/editor/Find/Replace/context/review/settings:
  initially 391 passed, 1 embedded-menu assumption failed; after making that
  test's embedded-menu precondition explicit: **392 passed**. This does not
  establish macOS global-menu visibility.
- Native Ukrainian goal/autosave/recovery/open-error subset: **10 passed**.
- Expanded-audit/status/profile focused subset: **11 passed**.
- Recovery/UI/i18n/catalog focused suite: **368 passed**.
- Earlier full offscreen batch: 1056 passed, 2 skipped.
- Final full offscreen batch: **1059 passed, 2 skipped**.
- Source extraction: 957 strings; reference, placeholder and plural checks passed.
  English/Ukrainian compilation passed; Ukrainian package has 965 finished entries.
  Packaged source parity is covered by translation tests.
- `git diff --check` passed. No live Ollama service used.

Native widget grabs and reproduction script:
`/private/tmp/utexteditor-native-acceptance/` (`system.png`, `dark-test.png`,
`contrast-test.png`, `palette_probe.py`). These are temporary local artifacts;
the two test palettes are synthetic overrides, not OS accessibility modes.

## Concrete residual localization inventory

A supplemental walk of string constants outside tr() and f-string fragments,
including values routed through helper methods, found additional real UI cases:

| Owner | Reproduce | Outstanding string/data path |
| --- | --- | --- |
| ProjectBriefDialog.set_autopilot_running | Start project Auto-pilot | Running/default status about refining plan and Cancel |
| ProjectBriefDialog.apply_suggestion | Accept template suggestions | Suggestions added/review status |
| MainWindow project Auto-pilot result handler | Finish generation after context change | Project/settings changed status and generated batch applying count |
| MainWindow template suggestion result handler | Edit template while request runs | Template changed/edits kept status |
| ProjectView.show_project / _add_scene | Open a project containing missing scene/note | Unavailable prefix; orphan note target fallback |

This source inspection is broader than the selected-call AST heuristic, and is
why TASK-032.01/.02/.04 are not being falsely closed by extraction parity.
Prompt text, generated snapshot names, font names, AI debug/protocol strings and
stable manuscript metadata remain data rather than interface translations.

During this run TASK-034.02 and TASK-034.04 were removed from TASKS.md externally.
Their removal is preserved separately from this agent's commits and is not
counted as completion. The current backlog has four remaining tickets (.032.01,
.032.02, .032.04 and .034.03); the original eight-row table retains what was
actually checked and what was not verified.

## Continuation

Continue remaining TASK-032 dynamic/recovery/service workflow inventory. For
TASK-034, obtain actual VoiceOver spoken output and native OS appearance matrix,
then complete the dialog/focus inventory. Do not close these gates from the
current offscreen or synthetic-palette results.

`git status --short && cat IMPLEMENTATION_PROGRESS.md TASKS.md`
