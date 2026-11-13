# UTextEditor — known gaps and product decisions

> **Not an execution queue.** See [TASKS.md](TASKS.md) for approved unfinished tickets and [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) for the latest resume checkpoint. This is an inventory of known limitations and **proposals**, not a request to implement every item. Current capabilities are documented in [README.md](README.md).

## Confirmed risks and incomplete guarantees

| Area | Current behavior and limitation | Evidence |
| --- | --- | --- |
| Writing-goal undo history | Reachable metadata can grow with separate Qt undo commands. Shared prior-day daily counts reduce some retention, but no measured universal bound is demonstrated. Preserve exact counts and Qt undo. | [history benchmark](docs/large-file-evaluation.md) and progress archive |
| Concurrent saves | Fingerprint checks, staged atomic replacement and a shared process-local `RLock` protect cooperating in-process saves. An **independent writer can still change content between the last check and replace**; no arbitrary-writer no-overwrite guarantee. | [save-coordination](docs/save-coordination.md) |
| Large documents | Standalone files are read into memory in full; the editor has no enforced safe size limit and some Qt callbacks are synchronous. Offscreen timings are diagnostic, not native latency promises. | [large-file](docs/large-file-evaluation.md), [GUI latency](docs/gui-latency-evaluation.md) |
| Text formats | UTF-8 only; line-ending and encoding indicators are not selectable. Binary detection rejects NUL and suspicious ASCII controls but is not exhaustive. | [encoding evaluation](docs/encoding-support.md) |
| Recovery | Recovery snapshots can be inspected and individually selected; partial/corrupt data repair and all diagnosis paths remain limited. Do not equate recovery with backup. | `app/document/recovery.py`, `tests/test_recovery.py` |
| Revisions | Named snapshots can be previewed, compared and deleted after confirmation. Selective restore, scheduled creation and retention controls are not implemented; comparison coverage is broader but not total. | `app/document/revisions.py`, `tests/test_revisions.py` |
| Localization and accessibility | Packaged catalogs and validation tests exist; the whole dynamic UI/service-error inventory, native screen-reader testing and cross-platform focus/palette checks are incomplete. | TASK-032/034; [checkpoint](docs/localization-accessibility-checkpoint.md) |
| AI inline display | Long/multiline/mid-line completions that cannot be fully represented are rejected conservatively. Prompt streaming preview is optional and does not auto-insert. | [completion verification](docs/inline-completion-verification.md), [streaming](docs/streaming-preview-verification.md) |
| Search and Markdown preview | Project search is literal/case-sensitive with bounded per-file and result limits. Markdown preview renders a labeled bounded prefix of very large buffers. Native responsiveness remains to be measured. | [search](docs/project-search-verification.md), [Markdown](docs/markdown-preview-verification.md) |

## Verification still required for existing features

These items are largely implemented and must **not** be treated as missing features. `TASKS.md` names the actual unfinished gates.

- Native Linux/macOS keyboard, focus, contrast and screen-reader tests for Quick Open, tabs, Back/Forward, linked items, Find/Replace, project search, AI context/spelling/translation/Auto-writer reviews, Markdown and export dialogs.
- End-to-end Ukrainian interface coverage, including typed service errors and released `.qm` catalogs in a native GUI. Catalog extraction and parity tests are useful but not a whole-app visual audit.
- Repeated native large-document/preview timing with realistic manuscript inputs and memory/Qt renderer observations, separately from offscreen synthetic benchmarks.

## Optional changes — not currently authorized

| Proposal | Decision / prerequisite |
| --- | --- |
| Recovery repair and portable project backups | Design integrity checks, missing-file reporting, selection, destinations and no-overwrite/restore rules first |
| Selective revision restore / automatic snapshots | Require preview, safety snapshot, rollback, unsaved-buffer handling and explicit retention policy |
| Alternative encodings and selectable newlines | Define round-trip, BOM, file identity, conflict and recovery migration behavior before implementation |
| Richer search, regular expressions and project-wide replace | Requires limits, cancellation, stale-result checks and a transactional replacement preview |
| Large-file architecture | Measure real workload; whole-buffer Qt operations and peak memory may require a separate design |
| Rich multiline ghost-text UI | Choose a fully readable, accessible non-destructive presentation; never accept invisible text |
| Additional writing/interface languages | Evaluate detection and plural forms and first complete current supported UI audit |
| Optional toolbar / appearance override | Defer pending native keyboard, focus, palette and maintainability review |
| Alternative AI providers | Defer pending provider contract, credentials, destination privacy disclosure and data-handling decision |

These proposals do **not** override the existing local-first, UTF-8 project portability and explicit-author-acceptance principles.

## Evidence boundaries

Historical test totals in older `docs/` notes and [the progress archive](docs/archive/implementation-progress-2026-11-13.md) are snapshots of earlier runs; they do not prove the current branch passes. The latest recorded execution checkpoint should be consulted before starting a Codex batch. No native screen-reader or external-writer guarantee may be inferred from offscreen tests.
