# RAG-05 manual completion pilot

The opt-in **AI > Review RAG Completion Context…** command operates only on an
open, project-bound scene. Ordinary/manual completion and automatic completion
continue using their existing paths; RAG-08 owns automatic retrieval integration.
An explicit positive Ollama token window is required, with no guessed allocation.
Refresh the local index through Project > Project AI > Retrieval Index first.
Missing/unsupported indexes are disclosed as unavailable rather than as no hits;
the author may send mandatory context after reviewing that limitation.

| Criterion | Preconditions | Failure/stale coverage |
| --- | --- | --- |
| Opt-in capture | Enabled completion, open project scene, positive window, nonempty unselected passage | Standalone/unknown window refuse; capture runs in worker; no automatic-path changes |
| Review | Frozen role/prompt, manifest, destination host/model | Exact source IDs, ranges, digests, buffer revisions, omission reasons and budget units displayed; exclusions disable Send until rebuilt |
| Dispatch | Explicit Send and matching editor/project/settings/buffer snapshots | Disk/manifest checks before provider; current generations checked before queuing and in worker; cancel suppresses dispatch/result |
| Generation | Captured provider, output reserve, temperature and role | Same prompt sent with full-context refusal; disk checks after success or failure; stale success/error discarded |
| Apply | Unchanged original editor/cursor/selection and project/buffer/settings generations | Existing ghost suggestion only; explicit Tab acceptance, Esc rejection and Undo preserved |

The UI coordinator lives in `app/ui/rag_completion.py`; the existing context
review widget supplies destination, read-only text and Send/Cancel controls.
The additional source checklist permits optional scene/note exclusions and a
worker recapture. The role is displayed separately; the source manifest appended
to the prompt preview is explicitly marked **not sent**. Fixed UI descriptions
are translated; source content, source codes and diagnostics remain original.
Mandatory scene metadata and associated character context cannot be unchecked.
The preceding passage remains bounded by the existing completion character
setting; RAG does not replace that author-input policy with a full-scene request.

`ProjectContextService` performs retrieval with current buffer overlays and
returns the frozen prompt. Language Auto is resolved from the author passage
before retrieval. No unsaved text is persisted in the index. The review is the
explicit destination consent for this separate command; it never sends text just
because the dialog was opened. Exclusion changes apply to this review session.
No embedding calls, model downloads or index refreshes occur in this workflow.

`app/ai/captured_completion.py` checks captured sources before dispatch and after
generation, including provider failures. It uses `AIProvider.generate_private`
with the already-rendered prompt, captured role/output reserve, and
`require_full_context=True`; it does not render the template a second time.
Requests/responses remain visible in the AI diagnostics window. A synchronous
provider call already in progress cannot be interrupted; cancellation discards
its eventual result. Capture and generation use existing worker/activity tracking.
Worker cancellation predicates read plain generation fields, never Qt widgets.
Fresh GUI buffer stamps are compared before presentation or acceptance.

Verification is deliberately conservative: a change to any captured source,
even an omitted source, invalidates a request. Filesystem fingerprints detect
observed changes and do not lock out arbitrary external writers; a change after
the final worker check is outside that check's guarantee. This is not an atomic
filesystem transaction or a proof of manuscript consistency. Existing bounded
character helper limitations remain disclosed. Full character development
correctness and all-workflow association testing remain CHAR-DEV-01/RAG-12 work.

## Verification evidence

The regression module is `tests/test_rag_completion_ui.py`. Its offline fake
provider tests cover review/rebuild/exact send, exclusions, unsaved note overlays,
disk changes during review/generation, buffer/tab/project/settings changes,
cancellation, unavailable/no-hit coverage, explicit acceptance, rejection and
Undo. It uses no live Ollama server.

The direct macOS Cocoa walkthrough runs a real visible window and modal source
review using Qt keyboard events: Tab into exclusions, Space to toggle, Send
availability, Esc cancellation, Return to send, Tab to accept in the editor,
and Undo. The provider is fake; the review's actual `QDialog.exec` runs. It checks
native widget behavior, not screen-reader accessibility or live model quality.
Run explicitly on macOS:

```bash
QT_QPA_PLATFORM=cocoa PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q tests/test_rag_completion_ui.py -k native_keyboard
```

Results and exact resume pointer are recorded in `IMPLEMENTATION_PROGRESS.md`.

Native report (2026-11-14): macOS 27.0.1 arm64, Qt 6.11.2, Cocoa platform.
The command above passed: **1 passed, 24 deselected in 0.68s**;
log `/private/tmp/utexteditor-rag05-native.log`. The added role preview initially
changed Tab ordering; the native check caught it, explicit tab order corrected
it, and the final walkthrough passed. RAG-05.V2 is COMPLETE on this platform;
other operating systems, screen readers and live Ollama are not verified here.

Completion review against `docs/clean-code-codex.md`:

- [x] Intent: captured completion and review operations have explicit names.
- [x] Ownership: domain capture stays in project services; provider invocation in
  AI service; Qt orchestration in a separate UI module.
- [x] Safety: source stamps/generations, buffer precedence, explicit Send and
  acceptance, cancellation and Undo are retained; no manuscript/index writes.
- [x] Errors: current failures remain visible; obsolete failures/results discard
  against their captured state; no truncated mandatory input is sent.
- [x] Tests: offline regression suite and direct native keyboard walkthrough;
  separate live provider verification is outside this ticket's gates.
- [x] Diff: scoped additions, no dependency or settings migration; README,
  Ukrainian overview and compiled translation catalog updated.
- [x] Report: native automation and filesystem/cancellation limits stated;
  exact full/focused results recorded in the progress checkpoint.
