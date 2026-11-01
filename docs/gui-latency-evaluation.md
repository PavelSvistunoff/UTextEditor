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
