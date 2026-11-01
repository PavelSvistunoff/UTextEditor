# Project search verification — TASK-012.V1

Reviewed 2026-11-01 from `app/project/search.py`, its MainWindow callers,
`ProjectSearchPanel`, and offline service/UI tests. Search is literal and
case-sensitive; this audit does not add matching options or replacement.

| Ticket / criterion | Evidence |
| --- | --- |
| .01 scenes and reference notes | MainWindow captures grouped/ungrouped `iter_scenes()` and manifest notes. Chapters organize scenes and have no independent manuscript text. `test_search_prefers_open_buffer_and_reports_locations` covers both document kinds. |
| .02 unsaved buffers take precedence | MainWindow captures open buffers before the worker starts. `test_project_search_finds_open_unsaved_text_and_navigates_only_current_matches` covers unsaved scene text; `test_oversized_open_buffer_does_not_fall_back_to_disk` prevents silently searching stale disk content instead. |
| .03 persistent panel | The dock and controls are reused across searches. This is session persistence, not saved search results on restart. `test_project_search_cancel_keeps_gui_responsive` exercises the panel/worker path. |
| .04 title, excerpt, line and column | `test_search_prefers_open_buffer_and_reports_locations`, `test_multiline_query_counts_following_line_correctly`, and `test_search_bounds_long_query_excerpt` cover locations, Unicode and bounded excerpts. Panel items display document kind/title and location. |
| .05 correct navigation and stale-match rejection | `test_project_search_finds_open_unsaved_text_and_navigates_only_current_matches` covers emoji offsets and changed buffers; both cases of `test_project_search_opens_closed_note_and_checks_disk_snapshot` cover worker opening and later disk changes. IDs, project generations, query generations and text digests are checked before selecting a match. |
| .06 cancellation and resource usage | `test_large_project_stops_at_result_limit` searches 2,500 descriptors; `test_large_project_can_cancel_before_reading_remaining_files` cancels among 5,000. `test_search_limits_results_and_honours_cancellation` and `test_search_cancels_during_a_document_and_rejects_escaping_paths` cover cancellation within a file. UI cancellation is covered separately. See remaining limits below. |
| .07 unreadable files | `test_search_reports_missing_binary_and_oversized_documents`, `test_search_bounds_error_details_and_counts_omitted_files`, and `test_project_search_long_error_report_is_scrollable` cover continued search and bounded diagnostics. New binary-control cases verify the same heuristic as ordinary project reads; the FIFO regression verifies non-regular paths do not wait for a writer on POSIX. |
| Search preserves files and buffers | Service tests assert disk bytes are retained; the unsaved UI test checks search/navigation does not write the buffer to the scene. Search itself performs no writes. |

The review found two file-reading gaps and corrected them: search now rejects
the shared NUL/non-whitespace ASCII-control/DEL heuristic, and it opens disk
sources with nonblocking flags where available and verifies a regular file
before reading. Invalid disk files are reported while valid companion matches
remain available. Existing open buffers remain the source of truth; this is
not a content-validation pass over text the author is currently editing.

Limits are 4 MiB per disk read or searched open document, 1,000 matches,
100 error details, 1,024 characters per error and bounded excerpts. The worker
checks cancellation between documents and matches. It cannot interrupt an
already-blocked regular-file or network-filesystem read. POSIX nonblocking FIFO
handling is regression-tested; Windows/network filesystem semantics need native
verification.

The initial V1 audit found no aggregate open-text capture budget. That gap is
now fixed: MainWindow uses Qt's existing UTF-16 character counts before copying
each buffer, with a shared 8 Mi-unit allowance across tabs. Python string
payloads require at most four bytes per unit (up to 32 MiB across these copies,
excluding object/container overhead, the original editor buffers and worker
temporaries). An oversized or over-budget buffer is represented by an omission,
not a disk fallback. The worker reports its title/path and the reason while
continuing with other files. The service omission regression and both ASCII/
emoji cases of `test_project_search_bounds_total_open_buffer_capture` verify
no copy for omitted buffers, exact-budget inclusion, preserved unsaved text,
unchanged disk content and no stale-disk matches.
Oversized caller-supplied text is rejected by its existing length before UTF-8
encoding, avoiding an additional oversized allocation at the service boundary;
both descriptor and buffer input paths have a focused regression.

Descriptor/omission metadata still scales with project size and tab count;
this is a text-payload budget, not a fixed total process-memory or GUI-latency
guarantee. Capturing buffers remains synchronous and tab-order based. Earlier
tabs, including standalone files, can use the allowance before later project
tabs; those omissions are explicit. Search captures are transient, not persisted.

All numbered tickets and V1 are verified within the stated resource and
cooperative-cancellation boundaries. Parent acceptance remains partial for V2
release-catalog/native keyboard/screen-reader checks.
Offscreen arrow/Enter and Qt accessibility tests are useful evidence but do
not establish native assistive-technology behavior. No controls were added;
the new omission explanation has English/Ukrainian source strings. Existing
dynamic filesystem/error details retain their current localization limitations.
