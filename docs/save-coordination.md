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
