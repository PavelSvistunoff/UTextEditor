# Repository refactoring plan

Status: **COMPLETE**. The final audit covers 135 Python files across all six
planned inventories. Findings were resolved or explicitly retained with reasons;
completion does not mean that every class must be rewritten or shortened.
See [per-file audit and acceptance report](refactoring-audit.md) for dispositions,
verification and residual risks, and [progress](refactoring-progress.md) for the
sequential implementation checkpoints.

## Shared completion gates

- [x] Review responsibilities, duplication, names/side effects, nesting, coupling,
  UI/domain/file separation, errors, dead code and coverage in every package.
- [x] Preserve public call shapes, YAML/IDs, dirty text, Undo/Redo, conflict guards,
  transactional rollback, worker dispatch, stale-response and explicit AI consent.
- [x] Characterize risky changes before extraction; separate actual behavior fixes.
- [x] Run focused/full offline tests, direct native subset and diff review.
- [x] Record each module's disposition and accepted limitations; update README.

## Final package outcomes

| Batch / package | Outcome and acceptance |
| --- | --- |
| R1 `app/document/` | COMPLETE: revision categories and common positions separated; duplicate snapshot byte writes and Unicode token rule shared. Existing encoding/export/recovery/undo safeguards retained. Ordering and injected-write-failure regressions pass. |
| R2 `app/project/` | COMPLETE: project-bound saves, recovery identity resolution, summaries, captured export and project revision assembly moved to explicit owners. Goal/knowledge parsing clarified; manifest and distinct transactional policies retained deliberately. Stable-ID/YAML/conflict/rollback tests pass. |
| R2 `app/ai/` | COMPLETE: shared JSON fence and Ollama generation payload rules; planning and analysis removed from window. Strict schema/evidence validation, context limits, consent and provider protocol preserved; offline tests pass. |
| R3 `app/ui/` | COMPLETE: domain workers delegated through existing static APIs, terminal activity handlers named, confirmed unused imports removed. Widget-specific state, review, focus and generation guards stay in UI. Native focus/activity/new-tab acceptance passes. |
| R4 `app/settings/` | COMPLETE: persistence/defaults/host/recency policies reviewed with tests. Different file/project path normalization retained for compatibility; no speculative settings abstraction. |
| R4 `app/main.py`, i18n/logging | COMPLETE: composition-root and optional-setup diagnostics retained; native translator lifecycle already verified. Package/script startup behavior remains. |
| R4 tests/tools/benchmarks | COMPLETE: every Python test/support/tool inventoried, pure worker cases moved out of UI tests, new meaningful regressions added. All five standalone probes run; misleading zero-exit Qt traceback led to separate B1 fix. |

## Separate behavior fix

B1: tab selection can emit status callbacks before editor_created attaches goal
tracking. All three goal-scope regressions failed before the fix. Goal refresh
now waits for attachment without altering tab signals, undo or manuscript data.
This is isolated in commit `561aa49`, after the pure refactoring commits.

## Evidence and accepted risks

Final full offscreen: **1117 passed, 2 skipped** (live Ollama opt-in cases).
Final native Cocoa: **39 passed**. Catalog reference validation and
`git diff --check` pass. Benchmarks are small smoke workloads, not general
performance guarantees. Python 3.12/other OSes, VoiceOver speech and actual OS
appearance transitions were not executed in this run.

MainWindow remains an orchestration surface; Project remains a persistence
aggregate. Distinct write/transaction policies and reachable undo metadata are
retained for correctness. In-process conflict protection is not a guarantee
against arbitrary independent writers. These are argued dispositions, not
unreviewed queue items; details are in the final audit.

The unfinished TASKS.md backlog remains empty. New product proposals require a
separate selection; none were implicitly authorized by closing this refactoring.
