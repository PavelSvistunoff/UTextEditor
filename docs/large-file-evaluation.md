# Large-file evaluation — TASK-011.05

This completes the evaluation ticket, not the parent large-file safety gate.
There is no enforced standalone-file size limit or bounded-memory loading path.

## Reproduction

Run offline with temporary synthetic files and AI disabled:

```sh
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/editor_responsiveness.py --sizes 1000000 5000000 10000000 --repetitions 10
```

The benchmark enables new-word tracking, retains earlier tabs, times ten typing,
cursor, search, word-count and completion-context operations, and reads/opens/
saves each file once. Save output is checked byte-for-byte against the buffer.
It times calls on the GUI thread; production file operations use workers.

## Observations on the development machine

| Characters | Read ms | GUI open ms | Typing median/max ms | Word count median ms | Save ms | Cumulative peak RSS bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 1,000,000 | 39.78 | 29.93 | 3.56 / 3.70 | 14.13 | 2.62 | 151,552,000 |
| 5,000,000 | 198.09 | 181.30 | 10.07 / 10.57 | 72.49 | 10.26 | 320,929,792 |
| 10,000,000 | 393.13 | 399.06 | 17.98 / 19.08 | 144.89 | 19.37 | 601,669,632 |

Cursor medians stayed around 0.48 ms. Completion-context medians, including
editor-to-string conversion, were 0.62/3.09/6.16 ms. Search finds an early match;
it does not measure worst-case full-document or no-match search. RSS includes
Qt/native allocations and prior tabs, not isolated per-document memory. These
are single synthetic offscreen sessions, not portable thresholds or native
interaction guarantees. Real manuscripts, huge individual lines, non-ASCII
text, many tabs and long undo sessions may behave differently.

## Implementation review and decision

FileManager reads all raw bytes, decodes a complete string, normalizes line
endings and hashes the raw bytes. Saving allocates a normalized encoded payload
and reads existing content for conflict checks. Qt document construction and
required word counts remain synchronous. Worker-based file I/O alone therefore
does not bound memory or eliminate GUI stalls. New-word undo metadata is also
unbounded (TASK-001).

Keep the current UTF-8 behavior; do not infer a supported maximum from these
measurements. A subsequent implementation needs a documented file-size policy,
a preflight failure path that preserves tabs and unsaved content, and tests for
files growing after preflight. A warning alone is not a memory bound. Evaluate
chunked decoding and a cancellation/generation-checked load design before
claiming support beyond available memory. Avoid destructive OOM experiments
against the user's session.

Current offline tests verify decoding/encoding failures and preservation of
source bytes and dirty buffers. They do not prove safe behavior on exhaustion
of process memory. Native Windows/Linux/macOS interaction, worst-case searches,
multibyte corpora and memory-pressure testing remain follow-up verification.
