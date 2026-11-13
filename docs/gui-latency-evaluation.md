# Qt callback latency

> **Evidence snapshot:** This document records an earlier investigation or verification, not a fresh test run or a second implementation queue. Check [active tickets](../TASKS.md) and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md) before using it to close a gate. Native GUI and screen-reader checks require real platform evidence.

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
responsiveness guarantee; those broader checks remain unverified.
There are no new product strings or controls to localize or verify natively.

## Multilingual project search workload

The project-search probe accepts scene count, lines per scene and repetition
count. It creates temporary English, Ukrainian and French text with non-BMP
characters, verifies that source files are unchanged, and reports startup,
elapsed time, maximum 5 ms timer gap and displayed results. Reproduce with:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/project_search_responsiveness.py --scenes 2000 --lines 40 --repetitions 2
```

On the development machine, 2026-11-13, offscreen Qt: absent search took
111.0/121.1 ms with maximum timer gaps 5.8/5.9 ms; Ukrainian `книга` took
39.3/26.5 ms with 5.3/21.4 ms gaps; emoji `🌿` took 24.4/35.1 ms with 5.6/29.1 ms
gaps. Matching searches each reached the 1,000-result cap and did not traverse
the entire project; absent search traversed all files. Warm cache, synthetic
content and two samples limit comparisons. These values are diagnostic rather
than thresholds or native input/paint measurements.

A wider run with `--scenes 5000 --lines 10 --repetitions 2` on the same
machine on 2026-11-13 completed with unchanged source files: absent searches
took 252.2/247.9 ms (maximum timer gaps 5.7/5.7 ms); `книга` took 48.2/35.8 ms
(31.7/19.4 ms gaps); and `🌿` took 40.1/37.4 ms (23.8/21.6 ms gaps).
Matching searches again reached the result cap. These are offscreen synthetic
measurements, not native input or paint latency.
