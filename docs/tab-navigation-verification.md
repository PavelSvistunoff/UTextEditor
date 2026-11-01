# Tab navigation verification — TASK-016.V1

Reviewed 2026-11-01 from DocumentTabWidget, MainWindow's Open Tabs capture and
picker path, and QuickOpenDialog's shared filter/keyboard behavior.

- .01 uses QTabWidget's existing next/previous shortcuts rather than adding
  competing actions. `test_native_tab_shortcuts_switch_without_discarding_changes`
  sends Ctrl+Tab/Ctrl+Shift+Tab to editors and verifies the dirty text survives.
  Its name refers to Qt's built-in behavior; it runs offscreen.
- .02 reuses the searchable Quick Open picker with tab-specific labels and
  accessible names. The Quick Open filter/arrow/Enter regressions already
  verify this shared picker; it is not a second search implementation.
- .03 and .04 label each tab with modified state, tab number, full path or
  Untitled, and project title when bound. Same basenames in different directories
  have different full paths; untitled tabs have distinct numbers. Selection
  resolves the editor object's session ID and verifies the tab still exists.
  `test_open_tabs_picker_shows_modified_and_distinguishes_untitled_tabs` checks
  the labels and switching without losing edits.
- Closing uses the existing close_requested signal and MainWindow save prompt.
  `test_tabs_keep_document_state_isolated_and_delegate_close` verifies the tab
  widget delegates closing and retains independent document state.

Three focused tests pass, and six shared Quick Open tests passed in the preceding
audit. Existing full offline tests exercise the same unchanged implementation.
No new UI, code, translations or redundant tests are introduced by this audit;
README already describes the current behavior.

.01–.04 and V1 are verified. .05 and V2 remain incomplete: actual native OS
shortcut conflicts, keyboard-only workflows and screen-reader behavior need
manual verification, together with release catalogs. Offscreen Qt behavior
does not establish those guarantees; the parent stays partial.
