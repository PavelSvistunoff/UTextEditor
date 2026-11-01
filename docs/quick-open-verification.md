# Quick Open verification — TASK-013.V1

Reviewed 2026-11-01 from MainWindow's action/capture/open path and
`QuickOpenDialog`. All numbered tickets are implemented; this audit adds no
UI or product behavior.

| Ticket / criterion | Implementation and test evidence |
| --- | --- |
| .01 keyboard access | Search > Quick Open uses Ctrl+P. The query accepts Enter, Down moves into results, arrows navigate them, and Enter opens the selected item. `test_quick_open_keyboard_selects_filtered_result` and `test_quick_open_arrow_keys_move_through_results` exercise both routes. |
| .02 searchable names | MainWindow captures chapters, their scenes, ungrouped scenes, notes and characters. The picker casefolds titles/context/aliases. `test_quick_open_filters_aliases_and_distinguishes_duplicate_names` covers filtered selection and no-match rejection; the chapter test covers its separate tree destination. |
| .03 character aliases | Captured aliases include the character's full name and aliases, independently of the displayed name. The filter test searches `Night Fox` to find `Mara`. |
| .04 distinguish duplicates | Labels include localized type, chapter context and stable ID. The filter test checks same-title scenes in different chapters and distinct IDs. Scene/note destinations with the same title are exercised by `test_quick_open_uses_stable_id_and_preserves_unsaved_tabs`. |
| .05 stable destinations and missing items | Selection stores the complete immutable item descriptor in Qt UserRole. MainWindow opens by kind/ID and rechecks project identity/generation after the dialog. Chapters are revalidated and revealed in the tree. `test_quick_open_handles_deleted_item_and_shortcut_is_unique` verifies missing-item feedback and one Ctrl+P action; `test_quick_open_reveals_chapter_in_tree` verifies the chapter path. |
| Unsaved buffers survive | The stable-ID test opens a note while retaining a scene's dirty text. Opening reuses the common document workflow; Quick Open itself changes no manuscript text or metadata. |

All six focused Qt tests pass. Existing full offline and localization tests
cover the same unchanged implementation; no redundant implementation-mirroring
tests were added for this status audit. README already documents the current
behavior, so no behavior rewrite is needed.

All numbered tickets and V1 are complete. Parent status remains partial:
V2 requires release catalog verification and native keyboard/screen-reader
review. Offscreen key events and Qt accessibility names do not replace those
checks. No native shortcut or screen-reader guarantee is inferred from the
unique-shortcut assertion alone.
