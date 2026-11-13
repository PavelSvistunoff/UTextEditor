# Complete reference context — Auto-writer and character suggestions

Scope: the explicit request to include every project note and character profile
in Auto-writer, and every project note in Fill Empty Fields with AI. Other scene
completion/analysis/development requests keep their associated-only profile scope;
planning and Auto-pilot behavior are not changed by this feature.

## Findings and changes

- Auto-writer previously sliced all reference notes at 10,000 characters and used
  a partial, associated-only character summary. A regression with a long first
  note and a final note failed before the change.
- Auto-writer now sends every note, all textual profile fields (including inactive
  goals and all knowledge categories), directed relationship details and recorded
  scene associations/development. Portrait bytes are excluded. Explicit scene
  associations still identify presence; the full cast is background. Each prompt
  identifies its target scene by title and stable ID and instructs chronological
  interpretation of recorded development.
- Character-field generation previously sent only the staged profile form. Its
  worker now captures all project notes, with bound open-note buffers taking
  precedence over disk. Note types/titles/IDs and complete text are included.
- Captured metadata and disk-note contents are checked before/after generation.
  After explicit character-suggestion review, another worker verifies closed notes
  before applying staged values, and the UI rechecks note editors/revisions,
  profile state, project/settings generations, cancellation and request identity.
- Auto-writer retains its complete revision snapshot, captured buffer revisions,
  note/scene conflict checks, selective draft review and transactional scene commit.
  No note or profile is silently edited by these context operations.

## Bounds and transport

The complete reference text is limited to 64 KiB UTF-8: notes plus profile
background in Auto-writer, all notes for character-field generation. Input exceeding
that limit fails rather than omitting later notes/profiles. Reads are bounded and
reject non-regular/binary/invalid UTF-8 sources. An oversized uncaptured open buffer
is an error, never permission to substitute older disk text. Qt captures bounded
buffers; filesystem work and model requests stay in workers.

These workflows request `truncate: false` and `shift: false` through AIProvider's
optional full-context contract; Ollama payload details remain in its client.
The native [Ollama ChatRequest contract](https://github.com/ollama/ollama/blob/main/api/types.go)
defines those controls. The server must support them and have a sufficiently large
context window; this feature does not silently increase memory/context allocation.
Context-window errors are reported without exposing note contents. No claim is
made that older/noncompliant servers honor these controls or that a model uses
all supplied facts correctly. AI diagnostics still have their separate display
length cap; a truncated debug event is not a truncated HTTP request.

## Verification scenarios

- Tail of a >10,000-character note and the last note reach every target-scene prompt.
- Unsaved bound-note text replaces disk text in model context without saving it.
- Exact profile mappings survive context serialization, excluding only portraits;
  tests include 26 profiles, >5 goals/facts, >8 traits/state changes, all background,
  personality/arc fields and full relationship history/secrets.
- Actual Ollama-client request serialization contains final note/profile markers,
  stable IDs and disabled truncation/shifting, using mocked HTTP transport.
- Missing, invalid UTF-8, oversized and uncaptured notes fail before model calls.
- Note/manifest changes during generation and closed/open-note edits during review
  discard suggestions. Cancellation during capture prevents later model dispatch.
- Existing profile fields and dirty note buffers remain intact; no automatic save.
- Full-cast Auto-writer policy test also confirms that unrelated characters remain
  absent from its separate associated-scene focus section.

No live Ollama model, new native keyboard or screen-reader test was run for this
context/payload change. Offline fake-provider and mocked-HTTP evidence verifies
capture, transport and lifecycle behavior, not model comprehension or atomic
protection from arbitrary concurrent filesystem writers.

## Results and completion review

Final focused corpus: **444 passed**. After adding explicit target-scene IDs and
matching assertions, the affected modules passed **351 tests**. Final complete
suite: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`
— **1190 passed, 2 skipped in 158.85s**. Log:
`/private/tmp/utexteditor-reference-final-control.log`.
Translation extraction/catalog validation passed (1028 source messages, 1041
compiled catalog messages). `git diff --check` passed.

Clean Code completion checklist: scope and README behavior reviewed; complete
capture deduplicated in the owning project service; Qt remains orchestration;
Ollama flags remain provider-owned; clear cancellation/stale/failure paths;
no new dependency or persistence/schema change; deterministic regression tests
cover full data, limits and review timing; user acceptance, dirty buffers and
transactional application remain preserved. Existing unrelated worktree changes
are excluded from this batch.
