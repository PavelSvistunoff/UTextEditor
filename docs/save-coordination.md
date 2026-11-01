# Save coordination evaluation — TASK-005.03

The supported guarantee remains process-local: a shared reentrant lock covers
fingerprint checks, staging and replacement for standalone/project text and
manifest saves. Independent writers can still change the destination after the
last fingerprint check. This evaluation does not close that race.

| Approach | Assessment |
| --- | --- |
| Shared in-process lock | Implemented; competing saves recheck after earlier saves complete. |
| POSIX advisory lock | Requires writer cooperation. The local subprocess regression writes successfully while an exclusive flock is held. |
| Cooperative sidecar lock | Candidate for multiple UTextEditor processes only. Other editors need not honor it; lock location, path aliases, stale locks and permissions need a defined protocol. |
| Windows byte-range lock | Different platform semantics; mapped-file writes are excluded from its coverage. Not a portable substitute for conditional path replacement. |
| Another hash immediately before replace | Narrows the window but cannot remove it; already implemented. |
| Atomic replacement alone | Keeps a replacement from being partially visible; it does not compare the destination against the captured base. |

## Evidence and decision

`test_posix_advisory_lock_does_not_exclude_uncooperative_writer` holds LOCK_EX
and launches a separate interpreter that overwrites the same temporary file.
It passes on the development POSIX filesystem and skips where fcntl is absent.
`test_separate_process_edit_after_final_check_exposes_save_race` independently
reproduces the current overwrite window. Existing threaded tests verify the
shared process-local guarantee; staging-race tests verify conflict detection.

Do not add advisory locks and describe the arbitrary-writer race as fixed.
Retain current process-local coordination and explicit residual-risk disclosure.
A future cooperative multi-instance protocol must cover canonical path aliases,
standalone/project overlap, manifests and bulk rollback, bounded acquisition,
worker cancellation and crash recovery. It must state explicitly that arbitrary
external writers remain outside its guarantee. Native Windows sharing/deletion
and mapped-file behavior and Linux/network filesystem behavior remain unverified.

Closing the independent-writer acceptance gate requires a separately demonstrated
platform guarantee or a product decision that preserves competing versions rather
than claiming conditional replacement. No additional platform dependency or
manuscript lock-file format is introduced by this evaluation.

## Primary API references

- [Python fcntl API](https://docs.python.org/3/library/fcntl.html): available
  locking primitives and platform availability.
- [Windows LockFileEx](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-lockfileex):
  byte-range exclusivity and the mapped-file exception.

The POSIX exclusion conclusion above comes from the repository's executable
experiment, not a claim of native verification on every supported platform.

## Acceptance reconciliation — TASK-005.V1 / V2

Reviewed 2026-11-01 against FileManager's locked save, Project's text and
manifest writers, and their shared `TEXT_WRITE_LOCK` (a reentrant process-local
lock). Numbered investigation/evaluation/disclosure tickets .01, .02, .03
and .05 are satisfied. Mitigation ticket .04 remains partial because the
independent-process window is still reproduced, even though process-local
serialization is implemented.

| Parent criterion | Evidence and remaining boundary |
| --- | --- |
| Detect or coordinate concurrent changes within the supported guarantee | `test_standalone_saves_serialize_check_and_replace_in_process`, `test_project_save_serializes_compare_and_replace`, `test_project_and_standalone_saves_coordinate_in_process`, and `test_manifest_and_standalone_saves_coordinate_in_process` verify competing application writers. The guarantee is limited to one process. |
| No silent overwrite in conflict scenarios | `test_file_manager_refuses_to_overwrite_external_changes` and the standalone/project/manifest `test_*save_detects_separate_process_edit_during_staging` tests preserve intervening edits. **Broader gate unsatisfied:** `test_separate_process_edit_after_final_check_exposes_save_race` asserts the known overwrite after the final check. A green suite includes that limitation, rather than proving it absent. |
| Atomic replacement and failure safety remain correct | `test_failed_atomic_save_keeps_original_file_and_document_dirty`, `test_text_saves_are_atomic_and_reject_stale_disk_snapshots`, and `test_scene_import_and_failed_manifest_update_roll_back_file` verify source/dirty-state preservation, stale-disk rejection, permissions and rollback. These are local filesystem tests, not crash-durability certification. |
| Residual risks documented | README and this evaluation describe independent writers, advisory locks and native filesystem verification gaps. |

No GUI, dialogs or translated strings were added by the coordination work;
V2's translation compilation and native keyboard/accessibility checks are
N/A for this task. This does **not** waive native filesystem verification:
Windows sharing/deletion/mapped-file behavior, Linux/network filesystems and
a defined multi-process guarantee remain open. TASK-005 stays partial and
TASK-007 retains the shared overwrite limitation. No redundant tests were
added for this documentation audit.
