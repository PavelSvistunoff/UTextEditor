# Recent standalone files verification — TASK-017.V1

Reviewed 2026-11-01 from AppSettings validation/persistence, FileManager reads,
MainWindow's recent-file menu, common open worker, duplicate-tab checks and save
callback. This is separate from the recent-project list.

| Ticket / criterion | Evidence |
| --- | --- |
| .01 separate recent-file list | `recent_files` and `recent_projects` have independent settings fields. Paths are deduplicated, validated and capped at ten. `test_recent_files_are_separate_bounded_and_persisted` covers round trips, invalid values, whitespace-sensitive names and the bound. |
| .02 common open path and tab reuse | Menu actions call `_open_document_path`, which reuses existing tabs or invokes FileManager in a FunctionWorker. Completed reads also recheck duplicates. `test_recent_files_reopen_deduplicate_report_missing_and_clear` reopens a dirty tab and verifies it is reused unchanged. |
| .03 missing/moved or unverifiable paths | Missing files report the ordinary open failure; they are not silently replaced or remapped. The reopen test covers deletion. Four path-verification regressions cover OSError/RuntimeError for requested/existing paths during both initial and completed-open checks, preserving all source bytes and dirty text. |
| .04 clear history | Clear Recent Files empties/persists only `recent_files` and repopulates the menu. The reopen/clear test verifies persisted removal; settings tests verify independent recent-project data. |
| .05 paths only | Settings validation accepts only absolute nonempty path strings with bounded length and rejects NUL. `_remember_recent_file` adds only the resolved path on standalone open/save. No manuscript text or buffer content enters this list. |
| Useful failures and unsaved safety | Existing localized Open failed feedback now also handles errors resolving paths while checking duplicate tabs, including after the read worker finishes. The new regression checks two warnings, unchanged tab count/editor identity/dirty text and untouched source files for each case. |

The review found duplicate-tab path resolution outside the error handler in
the initial and completion paths. Both now report failures instead of letting
exceptions escape into Qt callbacks. No controls or new translation sources
were added; existing Open failed translations are reused. This conservative
failure path declines the new open when safe duplicate detection is impossible.

All numbered tickets and V1 are verified. Parent stays partial for V2 release
catalog and native keyboard/screen-reader review. Offline persistence and Qt
tests do not establish native menu usability or OS file-dialog behavior.
