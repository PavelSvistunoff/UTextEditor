# UTextEditor — Product and Implementation Specification

This document expands on the product requirements in `README.md` with detailed behavior, implementation guidance, edge cases, and acceptance criteria. `README.md` remains the primary product specification and concise project guide. If a conflict appears, follow `README.md` and update this document to match; when implementation changes, keep both documents accurate.

## 1. Product intent

UTextEditor is a small native desktop application for writing and editing plain text. It supports both standalone documents and local manuscript projects with chapters, scenes, and separate story notes. Local AI is optional assistance, not the main event: users can write, search, open, and save documents without Ollama. The application should feel predictable, protect unsaved work, and avoid surprising edits.

The application targets people who need a straightforward multi-document text editor and want opt-in local suggestions and manuscript tools. It is not a code IDE, cloud editor, or general-purpose AI chat client.

### Product principles

- Local by default: AI requests go to the configured Ollama server. Do not add a cloud provider or telemetry without a separate product decision and explicit privacy controls.
- User-controlled: completions and corrections are proposals. They must not silently rewrite document text.
- Responsive: network, model inference, and potentially slow file work happen away from the GUI thread.
- Recoverable: destructive or bulk edits are undoable; unsaved changes are clearly identified and protected.
- Small and maintainable: keep components separate where that makes behavior easier to test; avoid abstraction layers that have no current use.

## 2. Release scope and status

The current application includes the original editor MVP and the project, recovery, writing-goal, export, snapshot, and local project-AI features listed in `README.md`. This document retains detailed requirements for the original editor workflows and ongoing edge cases; it is not an exhaustive status checklist. Where requirements here conflict with current behavior or documented scope, `README.md` and `UNIMPLEMENTED_FEATURES.md` take precedence.

The specification describes intended behavior, not a claim that every requirement is implemented. Remaining gaps include richer `Auto` language detection for mixed and short text, editor appearance settings, and memory-efficient large-file handling. Keep `README.md`'s known-gaps section synchronized with observed behavior.

## 3. Technology and platform

- Python 3.12 or newer, PySide6 / Qt 6, `pyproject.toml`, and pytest.
- `QPlainTextEdit` is the preferred MVP editor widget.
- Linux and macOS are MVP targets. Avoid choices that unnecessarily prevent Windows support.
- Ollama is the default AI backend, using `http://localhost:11434` and `gemma4:12b` by default.
- Do not introduce a dependency unless it solves a concrete requirement that is awkward or unsafe to solve with the standard library or Qt.

## 4. Application structure

Keep four responsibilities distinct:

```text
Qt UI (app/ui/) ── coordinates user actions and presents state
       │
       ├── document model and file manager (app/document/)
       ├── settings persistence (app/settings/)
       └── AI services ── AIProvider ── Ollama client (app/ai/)
```

The UI may call application services and schedule background work. It must not build HTTP requests or parse raw Ollama responses. `AIProvider` is the provider boundary; `OllamaClient` implements it in `app/ai/ollama_client.py`. Completion context and prompt construction belong in AI service/prompt modules, not in widgets. Document state and file encoding logic belong outside the Qt widgets.

The implementation currently uses synchronous provider methods inside `QThreadPool` workers. That is acceptable: the provider API does not need to be `async` just to keep the GUI responsive. Use one consistent background-work pattern and deliver results back to Qt objects through queued signals.

## 5. Main window and navigation

The main window contains a menu bar, tabbed document area, central editor, and status bar. A toolbar is optional. Keep AI status visible but unobtrusive; a connection failure must not disable ordinary editing.

Expected menus and actions:

- File: New, Open, Save, Save As, Close Tab, Quit.
- Edit: Undo, Redo, Cut, Copy, Paste, Select All.
- Search: Find, Replace.
- AI: Enable AI, Check Spelling, Generate Completion, Generate from Prompt, Settings. A session-only diagnostics view is optional.
- View: editor preferences such as wrapping or line numbers when those features are implemented.

Use Qt standard key sequences where possible so modifier keys adapt to the platform. Shortcuts should be shown beside their menu actions. `Ctrl/Cmd+F` should open find; `Ctrl/Cmd+H` should open find/replace. `Ctrl/Cmd+Space` may request a completion immediately. Avoid assigning one shortcut to conflicting actions.

## 6. Document model and lifecycle

Each tab owns one document/editor pair. A document stores at least text, optional path, encoding, line-ending convention, and dirty state. One tab's edits, cursor, spellcheck marks, and pending AI responses must not leak into another tab.

### New and open

- New creates an empty untitled document and selects it.
- Open uses a native file dialog. On success, create a new tab and select it; do not replace the current document.
- Opening a path already open should select the existing tab rather than create a duplicate.
- A failed open must leave all existing documents untouched and show a useful message.
- Open as text only. Detect decoding failures and explain that the file is not supported or offer an encoding choice; never silently replace undecodable bytes.

### Dirty state and save

- A document becomes dirty when its text differs from its last saved contents. Mark its tab title with `*` (or an equally clear marker).
- Saving a named document writes to its current path. Saving an untitled document opens Save As.
- Save As writes to the chosen path and updates the document path/title only after a successful write.
- Save uses the document's chosen encoding and line endings. Normalize editor-internal newlines to `\n`; convert to the selected on-disk line ending when saving.
- A failed save keeps the document dirty and retains its prior path.
- Save should use a safe write strategy where practical (write a temporary sibling then replace) so interruption is less likely to truncate the original. Preserve file permissions when feasible.

### Close and quit

When closing a dirty tab or quitting with dirty documents, ask for Save, Discard, or Cancel. Save must be confirmed successful before closing. Cancel aborts the close operation. For Quit, process dirty documents one by one and abort if any save fails or the user cancels. Do not discard any document until all required prompts succeed.

### Tabs

Every editor has independent text, undo history, cursor and selection, file metadata, and AI suggestion state. Switching tabs invalidates or cancels work that belongs only to the old active editor. Closing a tab must go through the dirty-state prompt before destroying its editor.

## 7. Text editing and search

Use the editor widget's native editing and undo facilities for typing, selection, navigation, clipboard operations, and standard edits. Ensure generated insertions and bulk replacements use the same undo stack.

Find/replace should provide a find field, replacement field, Find Next, Replace, and Replace All. Find Next starts from the current cursor, wraps at most once, and reports when there is no match. Replace changes the selected match only; if the current selection is not the match, first find the next match. Replace All is a single undoable operation and reports the number of replacements. Empty search text must be rejected without changing the document. MVP matching is literal and case-sensitive unless case controls are explicitly added.

## 8. File format, encoding, and status

The MVP reads and writes UTF-8 text. Internally, represent line breaks uniformly as `\n`. On open, detect CRLF, LF, or classic CR from the original content and retain the detected convention for saving. For mixed line endings, choose the most common convention; if counts tie, choose the convention whose first occurrence comes earliest. Normalize all line breaks to that convention on save.

The status bar shows encoding, line-ending style, one-based current line and column, and AI status. Cursor movement and document switching update the display. Encoding and line-ending indicators are informational in the MVP; selecting alternate encodings or line endings is future work unless separately implemented.

File dialogs should not imply that binary formats are supported. Reject embedded NUL characters as likely binary input; broader binary detection is future work. Open and save file contents in workers and apply document/UI changes only on the GUI thread. Files are currently read in full, so very large files can still use substantial memory. Never perform AI/network work in the GUI thread.

## 9. Settings and persistence

Use safe defaults when settings are missing or malformed. Store user settings as YAML in `settings.yaml` in the platform's standard per-user application configuration directory. Load legacy `settings.json` preferences when no YAML file exists. Persist only preferences and provider configuration, never document contents or AI conversation history.

AI settings include enabled state, provider (Ollama for MVP), host, model, completion enabled, debounce interval, context character limit, maximum suggestion length, temperature, spellcheck enabled, automatic-check enabled, language, and editable completion role/template where exposed. Validate values at the UI boundary and when loading older or malformed settings. Invalid optional settings fall back to defaults and should be recoverable without a crash.

Editor appearance settings are separate from AI controls: font, font size, tab/indent width, word wrap, and line numbers. Editor colors follow the operating system's palette rather than an app-specific theme override. Settings changes should take effect immediately where safe, and persist after an explicit dialog acceptance or another clearly defined save action.

## 10. AI provider and Ollama behavior

Define a provider-neutral interface for completion, text generation, spelling checks, and connectivity. Keep Ollama-specific paths, JSON payloads, and response parsing inside `OllamaClient`. Use bounded request timeouts and convert transport, HTTP, JSON, and model-shape failures into explicit provider errors.

On startup, check configured Ollama connectivity in a worker. Show `Connecting`, then `Connected` or `Offline` (reserve `Error` for a request failure if useful). Do not repeatedly probe in a tight loop. Editing remains available in every state. Re-check after the user changes host/model or re-enables AI.

The default host/model are `http://localhost:11434` and `gemma4:12b`. Do not assume the model exists merely because the server responds; show an actionable error when inference reports a missing model. A future provider may implement the same service boundary, but cloud providers are outside MVP scope.

## 11. AI request lifecycle and concurrency

All completion, generation, spelling, and connectivity calls run off the GUI thread. A request captures enough identity to decide whether its result still applies:

```text
request id, editor/document identity, document revision,
cursor position and selection (where relevant), settings generation
```

When a result arrives, compare its snapshot with current state before presenting or applying it. Discard results for closed documents, changed text, changed cursor/selection, changed settings, disabled AI, or a superseded request. This stale-result check is required even when cancellation is requested because a running HTTP call may not stop immediately.

Keep worker references alive until completion. Handle success and failure explicitly, release references, and avoid updating deleted widgets. Cancellation should be cooperative: queued work can be skipped; in-flight blocking requests may finish but their output must be ignored. Do not claim network cancellation unless the HTTP implementation actually supports it.

Limit concurrent work. At most one active inline completion request should be considered current; spelling work should be debounced and should not spawn unbounded requests. Disabling AI stops timers, invalidates outstanding request generations, clears visible suggestions, and prevents late results from being displayed.

## 12. Inline completion

After typing, wait for a configurable debounce (default 500 ms) before requesting a continuation. Do not trigger automatic completion for every cursor movement. Offer an explicit menu/shortcut request as well. Skip empty context and contexts where a completion cannot reasonably be placed (for example, while a selection is active unless selection replacement is an explicitly designed behavior).

Build bounded context near the cursor: include text before the cursor and enough nearby paragraph/sentence context to preserve meaning; do not send the full document by default. Include the selected language. A maximum character setting bounds request size. The context builder must be a pure, independently tested function.

The prompt asks for continuation only, in the same language, without restating the supplied text or adding explanations. Keep prompt construction centralized. Preserve leading whitespace because it may be necessary to join text correctly. Remove only clearly unwanted transport artifacts if this can be done without changing meaningful whitespace.

Render the result as visually distinct ghost text at the captured cursor. The ghost text is presentation state only: it must not change document text, revision, dirty state, selection, or undo history. It must never cover or replace existing document text. If rendering is clipped at a line boundary, keep the suggestion readable by another affordance or reject unsupported multiline suggestions; do not silently insert partial content.

### Accept and reject

- `Tab` accepts only when a completion is visible. Insert the complete suggestion at its captured location as one undoable edit and place the cursor after the inserted text.
- With no visible completion, `Tab` keeps normal editor behavior (indent or tab insertion as configured).
- `Esc` dismisses the visible completion and leaves document text unchanged.
- Typing, cursor movement, selection changes, document switching, settings changes, or newer requests invalidate the suggestion.
- Acceptance must re-check editor identity, revision, cursor, and selection immediately before insertion.

Completion requests are non-streaming in the MVP. Streaming can be added later if partial text remains presentation-only and cancellation/stale-result behavior is preserved.

## 13. Prompt-based generation

Prompt-based generation is a separate, explicit command, not inline completion. Ask the user for an instruction, run the request in a worker, and show a clear progress/error state. Capture the active editor, revision, cursor, and selection before sending. Before insertion, verify that the same editor is active and the captured document state still matches. If it changed, discard the output or ask the user to review it without applying.

Insert accepted output at the captured cursor or replace the captured selection as one undoable operation. The generated text must not be inserted automatically into a different tab or at a moved cursor. The MVP may treat opening the generation dialog as explicit intent to apply the eventual result, but cancellation and errors must leave the document unchanged.

## 14. Spellcheck and corrections

Spellcheck is an explicit or scheduled analysis that produces suggestions. It must not rewrite text in the background. Scheduled checks run only after a pause, use a longer debounce than completion, and analyze only the active document. A setting can disable automatic checks independently of explicit Check Spelling.

Send a snapshot of document text, language, document identity, and revision. Request structured suggestions containing at least `start`, `end`, `replacement`, `type`, and optional `explanation`/`original_text`. Offsets use Python Unicode code-point indices into the exact submitted string; document this convention in prompts and tests. If the model cannot provide trustworthy offsets, discard the questionable item rather than guessing.

Validate the whole response shape and each item. Reject negative, reversed, out-of-range, non-integer offsets and non-string replacements. Check that the captured document/revision still matches and, when supplied, that `original_text` matches the selected range. Ignore malformed items safely and cap the number of suggestions accepted from a response.

Present valid suggestions with subtle underlines. On right-click over a suggestion, offer Replace and Ignore. Replace changes only the referenced current text and is one undoable edit. Ignore removes that suggestion from the current result set without changing text. If several corrections are offered through a batch UI, require an explicit Apply action and apply non-overlapping corrections in one undo group. Never auto-apply a spellcheck response, including results from scheduled checks.

After a text edit, invalidate offsets from the old revision. Do not leave underlines attached to unrelated text. If the user manually edits while a check is running, discard its result.

## 15. Language support

The MVP offers `Auto`, `English`, and `Ukrainian`. Explicit selections are passed to completion and spellcheck prompts. `Auto` must either detect the language from the bounded context or clearly fall back to a documented model instruction; displaying `Auto` while passing the literal word as if it were a detected language is not language detection.

Language detection should be local, deterministic where feasible, and avoid extra dependencies unless justified. If confidence is low or the text is too short, preserve `Auto` and let the model infer language. Add tests for English, Ukrainian, mixed-language text, and short/ambiguous input. More languages are future work.

## 16. Error handling and user feedback

Failures must not crash the editor or alter documents. Show concise, actionable messages for file open/save failures, unavailable Ollama, missing model, timeouts, malformed responses, and rejected stale results where feedback is useful. Do not display raw tracebacks in normal UI. Log technical error details without document text.

An empty completion is a normal no-suggestion result. A failed request should transition out of `Generating` and leave editing usable. Avoid repeated modal dialogs for background failures; use status-bar messages or a non-blocking notification. Explicit file-operation failures should be visible and retain the user's unsaved content.

## 17. Privacy, safety, and diagnostics

AI output is untrusted text. Never execute it, interpret it as a command, or write it to files without user action. Validate offsets and revisions before editing. Requests may contain nearby document text; clearly disclose that text is sent to the configured local Ollama host. Do not send document text to cloud services.

Application logs may include operation name, provider, model, request duration, and error category. Do not log full document content or prompt text by default. An optional diagnostics window may display request/response payloads in memory for the current session because those may contain document excerpts. It must be clearly labeled, clearable, and never silently persisted.

## 18. Performance and accessibility

- No AI/network call runs in the GUI thread.
- Debounce completion and scheduled spellcheck; bound context and output length.
- Ignore stale results and avoid unbounded worker creation.
- Keep keyboard access for primary operations and provide visible menu actions.
- Keep ghost text and spelling marks distinguishable without relying only on color where practical.
- Do not sacrifice ordinary editing responsiveness to diagnostics or background AI status updates.

Large-file handling should be measured. If loading or saving blocks interaction for noticeable periods, move I/O to workers and show progress for long operations. Avoid loading entire files repeatedly for each cursor event or AI request.

## 19. Testing strategy

Use pytest. Unit tests must not require Ollama or internet access. Use fake providers and mocked HTTP responses. Keep pure logic (context construction, encoding conversion, parsing, and validation) independently testable.

Required coverage:

- document dirty state, saved state, revisions, and tab isolation;
- UTF-8 open/save, LF/CRLF/CR preservation, invalid UTF-8 handling, failed writes;
- find/replace behavior and undo grouping;
- settings defaults, persistence, malformed files, and validation;
- prompt construction, language handling, and bounded completion context;
- Ollama request/response handling, timeout, missing model, malformed JSON, and empty output;
- completion ghost text, acceptance, rejection, invalidation, and stale-response rejection;
- spellcheck parsing, invalid offsets, stale revisions, Replace/Ignore, and no background auto-application;
- prompt generation with changed tabs/cursor/document while the request is running;
- GUI remains usable when Ollama is offline.

Prefer focused unit tests. Add Qt integration tests for user-visible flows using an offscreen Qt platform where possible. Tests should not rely on arbitrary sleeps; wait on signals or use controlled fake workers.

## 20. MVP acceptance criteria

The MVP is ready when each item below is demonstrated manually or by a suitable automated test:

### Editor and files

- [ ] App starts as a native desktop application and can be used with AI disabled/offline.
- [ ] Create, open, save, Save As, and close documents without losing unsaved content.
- [ ] Multiple tabs preserve independent text, undo history, and metadata.
- [ ] Dirty state is visible; Save/Discard/Cancel behaves correctly for tab close and quit.
- [ ] UTF-8 text and supported line endings round-trip correctly; unsupported input gives a clear error.
- [ ] Find, Replace, and Replace All follow the behavior in Section 7 and remain undoable.
- [ ] Status bar reports encoding, line ending, line, column, and AI state accurately.

### AI

- [ ] Ollama defaults and settings work; startup check does not block the UI.
- [ ] Offline, missing-model, timeout, and malformed-response cases leave the editor usable.
- [ ] Completion appears as non-destructive ghost text and is accepted only by explicit `Tab`.
- [ ] `Esc` rejects it; stale results never appear or insert text.
- [ ] Prompt generation is explicit, runs off-thread, and inserts only into the captured unchanged document state.
- [ ] Spellcheck suggestions are validated, reviewable, individually replaceable/ignorable, and undoable.
- [ ] Scheduled spellcheck never changes document text without a user action.
- [ ] Local-only behavior and the text sent to Ollama are documented to the user.

### Quality

- [ ] Unit tests use fakes/mocks and run without a live Ollama service.
- [ ] `pytest` passes in the supported development environment.
- [ ] Relevant behavior and user-facing setup are reflected in README and this specification.
- [ ] The diff contains no unrelated changes or credentials.

## 21. Delivery order

Implement in dependency order, keeping each increment usable:

1. Document model, text editing, tabs, dirty state, and safe open/save/close flows.
2. Search/replace, keyboard actions, and status information.
3. Settings persistence and provider boundary; Ollama connectivity and errors.
4. Background request plumbing and stale-result identity checks.
5. Inline completion context, prompting, ghost rendering, accept/reject, and undo.
6. Spellcheck schema, validation, underlines, explicit Replace/Ignore, and safe scheduling.
7. Polish, accessibility, editor preferences, language detection, and large-file improvements.

Do not treat future work as MVP acceptance criteria unless scope is explicitly changed.

## 22. Future directions

The project workspace, chapter/scene organization, separate reference notes, word counts, recovery, writing goals, export, revision snapshots, and selected local AI analysis are implemented; see `README.md` for current behavior. Further work should improve these flows incrementally. Candidates include Markdown preview, recent files, richer encoding and language support, more complete recovery repair and revision comparison/management, proposed-edit previews, and more robust large-file handling. Prioritize author value and privacy; novel-aware AI must use configured local processing, and project features should preserve portability and author control. Avoid cloud services or proprietary formats without a separate product decision.

## 23. Definition of done

A feature is complete when its specified behavior is implemented, relevant tests cover normal and failure paths, the GUI remains responsive, errors preserve user data, docs reflect actual behavior, and the diff is limited to the feature. For AI features, verify both accepted and rejected/stale output paths. For file features, verify failure paths as well as successful round trips.

## 24. Detailed interaction and edge-case requirements

This section makes the preceding requirements concrete for common user flows. It does not expand MVP scope: behavior depending on a feature marked future work remains out of scope until that feature is adopted.

### 24.1 Startup and first use

- Startup creates a usable untitled document and accepts typing immediately. It must not wait for Ollama, settings migration, or a network timeout.
- Missing or unreadable optional settings must not prevent startup. Use validated defaults; show a warning only when the user needs to act.
- AI connectivity may be checked after the window is responsive. Progress and results must not take focus, open a modal dialog, or disable editing.
- When Ollama is unavailable, editing, local file operations, and search remain usable. AI actions explain the failure and how to reach settings.
- Before the first request containing document context, disclose that nearby text is sent to the configured Ollama host. Avoid repeated notices unless the destination materially changes.

### 24.2 File operation transaction boundaries

- Open transactionally: read and decode into temporary state, and add/select a tab only after success. A partial or invalid file must not replace a buffer.
- Save transactionally from the document's point of view: update path, title, saved snapshot, and clean state only after the write and final replace succeed. On failure retain the dirty buffer and prior path.
- Save As to a path already open must not silently leave two tabs claiming the same file. Ask for an explicit resolution or cancel while preserving both buffers.
- If an external program changes an opened file, never discard the in-memory buffer silently. If overwrite detection exists, explain the conflict and offer a deliberate resolution.
- A zero-byte file is valid empty text. Embedded NULs or likely binary data are unsupported unless the user chooses a future binary-safe workflow.
- A failed save during close keeps the tab open. A failed save or canceled prompt during Quit aborts quitting and leaves all documents available.

### 24.3 Editing, undo, and revision tracking

- Typing, deletion, paste, completion acceptance, generated insertion, replacement, and Replace All use the editor undo stack. A logical bulk action is one undo step.
- A no-op must not mark a document dirty. Returning text to the saved contents clears the dirty marker even when undo history remains.
- Text-changing edits, undo, and redo advance the document revision. Cursor movement does not change text revision, but invalidates cursor-sensitive completions.
- Cross-service text ranges use half-open `[start, end)` Unicode code-point offsets. Translate Qt cursor positions consistently, including around non-BMP characters such as emoji.
- Replacement leaves the cursor at a documented predictable location, normally after inserted text. Undo restores the prior text and a sensible cursor/selection state where supported.
- Disabled actions should communicate why they are unavailable, such as Copy without a selection or Undo with an empty undo stack.

### 24.4 Search behavior examples

- Find Next searches from the active cursor to the document end, then wraps from the beginning up to the original position at most once. A match at the current cursor may be selected; repeated Find Next must advance.
- Replace acts on a selection only if it exactly matches the search term under active matching rules. Otherwise it finds and selects the next match before replacing, avoiding accidental replacement of unrelated selected text.
- Replace All uses a stable snapshot and replaces non-overlapping matches; newly inserted replacement text is not searched recursively in the same operation.
- An empty query is rejected without changing text, cursor, selection, dirty state, or undo history. No-match feedback leaves the query available for editing.

### 24.5 Background work lifecycle

Each operation follows an explicit lifecycle equivalent to `queued → running → succeeded | failed | obsolete`. Every terminal path releases worker references and clears related progress state.

- Only the latest eligible completion for an editor can be shown. Typing, explicit re-request, editor switch/close, settings change, or AI disable invalidates older work immediately, even if its HTTP call continues.
- Coalesce spellcheck work: while one request runs, retain at most the latest pending snapshot per document or wait for the next debounce. Never build an unbounded queue of obsolete snapshots.
- Workers do not read or mutate widgets, cursors, selections, tabs, or painting state. Deliver results to the GUI thread through queued signals.
- Closing a document invalidates its request identities. Late results must be harmless even if associated UI objects were destroyed.
- Provider, host, model, prompt, language, and relevant limit changes advance a settings generation; results from older generations are stale.

### 24.6 Completion presentation edge cases

- A completion is valid only for the exact editor, text revision, cursor, and selection captured. Editing and returning to the same numeric cursor does not revive an old result.
- Whitespace-only output is no suggestion. Preserve meaningful leading whitespace and supported line breaks; remove only unambiguous transport wrappers.
- Do not show a completion that duplicates immediately following text. Remove a duplicate suffix only when unambiguous; otherwise discard the suggestion.
- Multiline output must be fully readable and accepted as a whole, or rejected. Never accept a visually clipped fragment.
- Tab is consumed only when a valid visible completion is accepted. Otherwise normal indentation/tab behavior applies. Esc dismisses the suggestion without changing text or unrelated selection state.
- Acceptance revalidates identity and state immediately before insertion and creates one undoable edit.

### 24.7 Spellcheck result edge cases

- Sort suggestions by start offset and detect overlap before display. Drop conflicting ranges conservatively unless conflict resolution is explicitly designed.
- Every underline belongs to the document and revision that produced it. On edits, clear or recompute marks; never reuse old offsets against changed text.
- Replace requires the marked range still to match its captured original. Ignore removes that item from the current result set only; it does not silently alter a persistent dictionary.
- Applying one correction creates one undo step and invalidates old offsets. Clear or revalidate remaining marks against the new revision.
- Malformed independent items may be skipped, but malformed top-level output must not be guessed into corrections. Bound response bytes, item count, replacement size, and explanation size.
- Automatic checks may update marks and status only. They never change text, dirty state, cursor, selection, or undo history.

### 24.8 Settings behavior and migration

- Parse persisted settings into validated application values once; widgets do not independently interpret raw persisted data.
- Missing keys use defaults; invalid values recover to defaults and are diagnosable. Ignore unknown keys for forward compatibility.
- Apply dialog edits only on its documented commit action. Cancel restores prior values and does not persist partial edits.
- Validate host URLs before connection attempts. Redact credentials from all errors and logs. Explain non-local destinations before sending document context when appropriate.
- Bound every numeric setting. Negative, excessive, NaN, or infinite values must not reach timers, prompt construction, or requests.
- Write settings atomically where practical; a failed write must preserve the prior usable file and must not be reported as success.

### 24.9 Accessibility and platform consistency

- Primary commands are reachable by menus and keyboard. Focus moves predictably among editor, search controls, dialogs, and tabs.
- Labels and status have text equivalents. AI state, completion availability, and spellcheck marks do not rely on color alone.
- Use platform-standard shortcuts and native dialogs. Dialogs have a clear default, explicit cancel path, keyboard navigation, and no accidental destructive default.
- Background status changes never steal focus. Spellcheck and completion results do not interrupt typing.

### 24.10 Diagnostics and support

- User messages state what failed and a practical next step. Technical details belong in diagnostics/logs.
- Logs may record operation, request id, provider/model, duration, and categorized error. Never log document text, selections, prompts, AI output, or spellcheck payloads by default; redact URL credentials.
- A diagnostics payload view is a deliberate disclosure surface because payloads can include excerpts. Label it, keep it session-only, and provide Clear All. Closing it does not change or cancel requests.
- Coalesce or rate-limit background failure notifications so automatic checks cannot flood the user. Explicit user-triggered actions still receive a clear outcome.

## 25. Requirement traceability

Use this mapping during review to find the owning requirements and failure cases. It is a review aid, not a second source of truth; update the owning section and acceptance criteria when behavior changes.

| User flow | Primary requirements | Failure and stale-state checks |
| --- | --- | --- |
| Start and edit offline | Sections 1, 2, 5, 16, 18 | Missing settings; Ollama offline; startup stays interactive |
| Open, save, close, quit | Sections 6, 8, 16, 19, 20 | Invalid encoding; failed write; canceled prompt; duplicate path |
| Search and replace | Sections 7, 19, 20, 24.4 | Empty query; wraparound; no match; one-step undo |
| Configure AI | Sections 9, 10, 16, 17, 24.8 | Malformed settings; invalid host; stale configuration |
| Request and accept completion | Sections 11, 12, 18, 19, 20 | Superseded request; changed cursor/revision; Tab fallback; Esc |
| Generate from prompt | Sections 13, 16, 19, 20 | Cancel; changed selection/tab; provider failure |
| Review spelling | Sections 14, 15, 16, 19, 20 | Invalid offsets; overlap; stale marks; scheduled non-mutation |
| Deliver a change | Sections 19, 20, 21, 23 | Tests, docs, diff scope, README compatibility |
