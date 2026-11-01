# Menu organization verification — TASK-018.V1

Reviewed 2026-11-01 from MainWindow's menu/action construction and existing
menu, tab and Quick Open tests. Existing grouping is retained; this audit adds
no menu surface, actions or shortcuts.

- .01/.02: Project has Move Items, Links, Revisions, Export and Project AI
  groups. AI separates generation/completion/review, analysis, cancellation and
  diagnostics with separators. Recovery remains in File before Quit and AI
  Settings remains in Settings. `test_main_menus_group_project_and_ai_workflows`
  verifies group order, representative actions, separators and recovery placement.
- .03: use the implemented submenus. A new command picker is not selected;
  discoverability changes should follow native keyboard/accessibility feedback,
  as already documented in UNIMPLEMENTED_FEATURES. This ticket is an evaluation
  decision, not authorization to add another navigation surface.
- .04: action construction retains the existing handler/shortcut table and
  moves project actions into groups without cloning them. Standard editing
  shortcuts, Ctrl+Space and F7 remain. Existing Generate, Text Formatting and
  AI Settings menu tests verify those actions are reachable; preceding Quick
  Open and tab tests check Ctrl+P uniqueness and Qt next/previous tab behavior.
- .05: project-required actions get translated tooltips/status tips explaining
  the project or suitable selection requirement; project/submenus enable
  tooltip display. The grouping test checks disabled/enabled New Character
  and the project/selection explanations.

Four focused menu tests pass; the latest full suite covers this unchanged menu
implementation. README already describes the group organization. No redundant
tests, code changes or new translation strings are needed for reconciliation.

All numbered tickets and V1 are verified. Parent acceptance remains partial:
the required manual keyboard/screen-reader review is outstanding, including
native shortcut conflicts, disabled-action explanations and macOS menu roles.
V2 release catalogs are also outstanding. Source strings and offscreen action
tests do not establish native discoverability or accessibility.
