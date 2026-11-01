# Qt callback latency — TASK-006.03

The editor benchmark now measures delivery delay of a ready Qt zero-timer
callback, both with no intervening operation and with synchronous typing and
new-word tracking. Each sample queues the timer, performs the operation, and
enters a local event loop to deliver it. Deferred editor work may also run.
The typing probe is a separate batch of insertions after the operation timings;
save verification includes both batches. No network service is required.

Reproduce from the repository root:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/editor_responsiveness.py --sizes 100000 1000000 5000000 --repetitions 10
```

Results on the development machine, 2026-11-01, offscreen Qt:

| Characters | Idle callback median/max ms | Typing callback median/max ms | Direct typing median/max ms | Cumulative peak RSS bytes |
| --- | --- | --- | --- | --- |
| 100,000 | 0.00 / 0.78 | 2.15 / 2.22 | 2.14 / 2.31 | 130,023,424 |
| 1,000,000 | 0.00 / 0.08 | 3.67 / 3.86 | 3.63 / 3.77 | 151,977,984 |
| 5,000,000 | 0.00 / 0.12 | 10.30 / 10.62 | 10.49 / 11.05 | 321,372,160 |

Times below 0.005 ms round to 0.00. The ready callback waits through the entire
insertion call, including synchronous goal processing; the direct operation
and callback timings use different insertions. They are descriptive samples,
not a claim that callback delivery can be faster than its own insertion.

This supplies a repeatable event-loop baseline alongside existing operation
and memory measurements. It introduces no performance optimization, so it
does not claim a before/after improvement. The standalone workload uses
synthetic ASCII paragraphs, temporary settings, AI disabled and retained tabs.
RSS is a process-wide high-water mark, not current or per-document allocation.
The save assertion verifies exact output bytes; successful completion also
checks callback delivery for every requested sample. No time threshold test
is added because results depend on hardware, Qt, scheduling and system load.

The window is not shown. Native keyboard, paint, screen-reader and compositor
latency, realistic project traversal, huge lines, multibyte text, asynchronous
background contention and memory pressure remain unmeasured. A zero timer has
no specified ordering relative to all other event sources. These measurements
do not establish a supported file-size limit, bounded undo metadata or a
responsiveness guarantee. TASK-006 remains partial for those broader checks.
There are no new product strings or controls to localize or verify natively.

## Acceptance reconciliation — TASK-006.V1 / V2

Reviewed 2026-11-01 against all three benchmark scripts, completion context,
goal accounting/status refresh and their regression tests.

| Ticket / criterion | Verified evidence and boundary |
| --- | --- |
| .01 opening, typing, cursor, search and word counts | `editor_responsiveness.py` measures each operation. .01 is complete as an offline operation benchmark; early-match search and single open/read/save samples are explicit limitations. |
| .02 goals and context | The editor benchmark enables new-word tracking and measures context construction; `writing_goal_history.py` separately checks counts through independent commands, undo/redo and branching. .02 is complete; this does not establish bounded history. |
| .03 GUI latency and memory | Ready Qt callback samples and cumulative native-process RSS are recorded above; Python history allocation measurements are in IMPLEMENTATION_PROGRESS. Partial: native input/paint latency and memory-pressure behavior are unverified. |
| .04 repeatable representative sizes | CLI sizes/repetitions and 100K/1M/5M/10M character workloads are documented here and in `large-file-evaluation.md`. Partial: synthetic ASCII paragraphs are not representative of every language, line shape, project or long editing session. |
| .05 optimize confirmed bottlenecks | Bounded context construction, changed-span token scans and skipping unnecessary goal word counts are implemented. `test_context_clamps_cursor_and_honours_character_limit`, `test_context_honours_paragraph_boundaries_at_and_across_window_edge`, `test_bounded_token_scan_matches_full_scan_for_boundary_edits` and `test_goal_refresh_skips_unneeded_buffer_word_counts` guard correctness. Partial: reachable history and required GUI counting remain unbounded/synchronous. |
| Baseline and post-change measurements | `completion_context.py` retains the prior implementation, checks equal output for its sample and measures both approaches on five million characters. A fresh 100-call run measured prior/current 0.0581/0.0002 seconds and 2,504,082/4,041 peak Python-traced bytes. These isolate context construction, not overall GUI speed. Prior GUI/goal measurements and their limitations remain in IMPLEMENTATION_PROGRESS. |
| Detect regressions and preserve correctness | The repeatable workloads, timing/allocation reports and source-byte assertions provide diagnostics; offline context, goal, editor and file tests verify behavior. There is no portable timing pass/fail threshold or complete application responsiveness guarantee. |

V1 is complete as an acceptance reconciliation; it does not complete the
partial numbered tickets or parent. V2's release-catalog and native keyboard/
accessibility checks are N/A for this task's internal optimizations and benchmark
tooling: no UI controls or translation sources were added. Native performance
verification remains an explicit .03/.04 requirement, not an exemption obtained
by marking V2 N/A. TASK-001's reachable-history bound is still separate work.
