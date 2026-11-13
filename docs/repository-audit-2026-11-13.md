# Repository documentation audit — 2026-11-13

> **Scope:** GitHub `main` at `57fdef0798c75f5e581e415f5e6f1ccb077254ec`, repository tree, provided Markdown snapshots, active root docs, selected implementation/evidence files. This is a **targeted static and documentation review**, **not** a full executed source audit. No current tests, live Ollama, or native OS/screen-reader checks were run during this cleanup.

## Findings

| Finding | Evidence | Documentation action |
| --- | --- | --- |
| Attached task list predates main | The attachment listed 35 implementation parents; main has an unfinished 20-parent queue and recent 2026-11-13 checkpoints. | Preserve live ticket IDs; replace generic `Done when` with exact gates and native verification scripts. |
| Codex ambiguity | 16 generic completion gates and repeated `.V2` text lacked specific workflows. | Add source/test entry points, dependencies, per-ticket outcomes and explicit native blockers to `TASKS.md` and `AGENTS.md`. |
| Historical progress mixed with active instructions | The previous `IMPLEMENTATION_PROGRESS.md` had 1188 lines of dated checkpoints and changing test totals. | Archive verbatim; keep a short current resume pointer. |
| Ukrainian README contradicted current implementation | A current summary was followed by legacy MVP chapters mentioning missing features already implemented, old async provider design and obsolete project tree. | Replace with current Ukrainian guide referring to `SPEC.md` for contracts and English `README.md` for exhaustive behavior. |
| Unimplemented inventory repeated task history | Old 315-test review numbers, legacy navigation proposals and outdated localization statements mixed risks with feature recommendations. | Keep one decision/risk inventory; redirect execution to `TASKS.md`. |

## Code and verification boundaries checked

- `app/document/write_lock.py` has a **process-local** `RLock`; [save-coordination](../docs/save-coordination.md) records a successfully reproduced independent-writer post-check overwrite. This is not a global concurrency fix.
- `app/document/writing_goals.py` has unbounded reachable Qt undo metadata according to the newest checkpoint. No safe pruning strategy should sacrifice reachable undo or exact daily progress.
- `app/project/service.py` and `app/ui/main_window.py` are large orchestration/integrity surfaces; future code changes need focused stale-state and transactional rollback tests.
- `tests/`, `benchmarks/`, `translations/`, `app/resources/translations/` and 21 dated `docs/` verification files exist in the repository. Offscreen results are not equivalent to native keyboard/screen-reader behavior.
- The most recent historical full-suite result was **923 passed, 2 skipped**; it was read from a checkpoint and **not rerun**. No claim of exhaustive source-code review or absence of other bugs is made.

## Out of scope

No Python implementation, settings, project files or generated Qt translation assets were changed in this Markdown-only cleanup. The remote tree also contains tracked `.DS_Store`, Python `__pycache__`, and `egg-info` files; removal would be a separate repository-hygiene change requiring ownership and regression review, so they were **not** deleted.

## Next owner action

Use [TASKS.md](../TASKS.md) with [AGENTS.md](../AGENTS.md) and the [current checkpoint](../IMPLEMENTATION_PROGRESS.md). Review each bounded ticket, execute tests, document native blockers, and avoid committing unrelated changes.
