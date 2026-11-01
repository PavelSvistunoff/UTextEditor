# Related-item navigation verification — TASK-015.V1

Reviewed 2026-11-01 from Project's directed links and explicit scene character
associations, MainWindow's navigation/profile lifecycle and CharacterDialog's
scene action. Existing behavior is verified; no new navigation UI is added.

| Ticket / criterion | Evidence |
| --- | --- |
| .01 linked notes/scenes | `open_linked_project_item` combines incoming/outgoing existing links, labels targets with stable IDs and rechecks the chosen link/project before opening. `test_open_linked_item_navigates_from_scene_to_note_without_changing_links` preserves dirty scene text and link metadata; `test_link_navigation_rechecks_selected_link_and_project` covers the reverse direction and stale selections. |
| .02 profiles to related scenes | The profile and project-tree actions enumerate scene character associations and use the common scene-opening workflow. `test_character_associated_scene_picker_uses_explicit_links_and_rechecks_them` and `test_profile_scene_selection_rechecks_association` verify destination selection and removal during review. |
| .03 associations versus mentions | The explicit picker reads `character_associations`; name/alias mention search is a separate action and worker. The picker test includes a same-title scene mentioning Mara without an association and verifies it is excluded. Navigation creates no associations. |
| .04 return path | A profile is hidden while its scene opens; a status-bar Return to Character Profile button shows the same staged dialog. `test_profile_scene_navigation_preserves_staged_edits_and_returns` checks returning, repeated navigation and closing the main window while a profile is hidden. Ordinary document jumps also use the separate session navigation history. |
| .05 protect staged edits | The profile remains unchanged in the manifest until Save. Save rechecks the captured character and directed relationships and refuses stale state without losing the form. `test_profile_save_refuses_changed_project_without_discarding_edits`, `test_profile_save_refuses_changed_directed_relationships` and `test_failed_profile_save_reopens_staged_edits` cover stale metadata and write failure. |

Eight focused offscreen tests pass; the latest full offline suite covers the
same unchanged implementation. Existing README describes the behavior. No
redundant tests or product changes are needed for this acceptance audit.

All numbered tickets and V1 are verified. Parent remains partial for V2:
release catalog and native keyboard/screen-reader checks have not been
performed. Automated dirty-buffer, stale-selection and staged-save tests do
not establish native usability of the return control or profile forms.
