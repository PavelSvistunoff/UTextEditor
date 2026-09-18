# UTextEditor

UTextEditor is a lightweight desktop text editor inspired by GEdit, with built-in local AI assistance powered by Ollama and the `gemma4:12b` model.

The application must remain fully usable as a normal text editor when AI functionality is unavailable.

The primary AI features are:

* spelling and basic grammar checking;
* inline text completion;
* keyboard-based completion acceptance;
* fully local AI processing through Ollama.

---

# 1. Project Goals

The first release is an MVP desktop text editor with the following capabilities:

1. Create, open, edit, and save text files.
2. Open multiple documents in tabs.
3. Provide standard text-editing functionality.
4. Search and replace text.
5. Connect to a local Ollama instance.
6. Use `gemma4:12b` as the default AI model.
7. Generate inline text completions.
8. Display completions as non-destructive ghost text.
9. Accept a completion using `Tab`.
10. Reject a completion using `Esc`.
11. Detect spelling and basic grammar errors.
12. Allow users to apply or ignore suggested corrections.
13. Keep the GUI responsive while AI requests are running.
14. Continue functioning normally when Ollama is unavailable.

---

# 2. Target Platforms

The MVP should target:

* Linux
* macOS

The architecture should not prevent future Windows support.

The application must be a native desktop application, not a web application.

---

# 3. Technology Stack

Use the following technology stack unless there is a strong technical reason to change it:

* Python 3.12+
* PySide6 / Qt 6
* Ollama
* pytest
* `pyproject.toml`
* Git

The preferred text widget for MVP is `QPlainTextEdit`.

The application should avoid unnecessary dependencies.

---

# 4. Design Principles

## 4.1 Local-first

All AI processing must happen locally through Ollama.

Default configuration:

```text
Provider: Ollama
Host: http://localhost:11434
Model: gemma4:12b
```

The application must not send document contents to external cloud services.

## 4.2 AI is assistive

AI functionality must never take control away from the user.

The editor must remain useful as a normal text editor when:

* AI is disabled;
* Ollama is unavailable;
* the model is unavailable;
* an AI request fails.

## 4.3 Responsive UI

No network or AI operation may block the Qt GUI thread.

The editor must remain responsive while:

* generating completions;
* checking spelling;
* communicating with Ollama;
* processing AI responses.

## 4.4 Clear separation of concerns

GUI code must not directly contain Ollama API logic.

AI functionality must be implemented behind an abstraction layer so that additional providers can be added later.

---

# 5. Application Layout

The main window should follow the general layout and interaction patterns of GEdit.

Expected layout:

```text
┌─────────────────────────────────────────────────────────┐
│ File  Edit  Search  View  AI  Help                     │
├─────────────────────────────────────────────────────────┤
│ New Open Save | Undo Redo | Find Replace               │
├─────────────────────────────────────────────────────────┤
│ file1.txt   │ file2.txt   │ +                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Text editor                                             │
│                                                         │
│ The quick brown fox...                                  │
│                                                         │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ UTF-8   LF   Ln 12, Col 8              AI: Connected   │
└─────────────────────────────────────────────────────────┘
```

The exact visual appearance does not need to be identical to GEdit.

The important characteristics are:

* menu bar;
* optional toolbar;
* tabbed documents;
* central text editor;
* status bar;
* unobtrusive AI indicators.

---

# 6. Document Management

The editor must support:

## New

Create a new empty document.

## Open

Open an existing text file.

## Save

Save the current document.

## Save As

Save the current document using a new file path.

## Close

Close the current document.

If the document contains unsaved changes, the application must ask the user whether to:

* Save
* Discard
* Cancel

## Multiple Documents

Each open document must have its own tab.

Example:

```text
document1.txt | document2.txt | notes.md
```

Modified documents should be visually marked:

```text
document1.txt *
```

The implementation must keep document state isolated between tabs.

---

# 7. Text Editing

The editor must support standard text-editing operations:

* typing;
* selection;
* copy;
* cut;
* paste;
* delete;
* undo;
* redo;
* select all;
* cursor navigation.

Expected keyboard shortcuts:

```text
Ctrl/Cmd + N       New
Ctrl/Cmd + O       Open
Ctrl/Cmd + S       Save
Ctrl/Cmd + Shift + S   Save As

Ctrl/Cmd + Z       Undo
Ctrl/Cmd + Shift + Z   Redo

Ctrl/Cmd + C       Copy
Ctrl/Cmd + X       Cut
Ctrl/Cmd + V       Paste
Ctrl/Cmd + A       Select All

Ctrl/Cmd + F       Find
Ctrl/Cmd + H       Replace
```

Use platform-appropriate modifier keys where required.

---

# 8. File Encoding

The MVP should use UTF-8 as the default encoding.

The implementation should keep encoding handling isolated so that additional encodings can be supported later.

The status bar should display at least:

* encoding;
* line ending style;
* current line;
* current column.

Example:

```text
UTF-8    LF    Ln 12, Col 8
```

---

# 9. AI Integration

AI integration must be implemented independently from the GUI.

Recommended interfaces:

```python
class AIProvider(Protocol):

    async def complete(
        self,
        context: str,
        language: str,
    ) -> str:
        ...

    async def check_spelling(
        self,
        text: str,
        language: str,
    ) -> list["Suggestion"]:
        ...
```

Ollama implementation:

```text
app/ai/ollama_client.py
```

Suggested services:

```text
app/ai/
├── ollama_client.py
├── completion_service.py
├── spellcheck_service.py
└── prompts.py
```

The GUI should communicate with `CompletionService` and `SpellcheckService`, not directly with `OllamaProvider`.

This architecture must make it possible to add future providers such as:

```text
OpenAIProvider
AnthropicProvider
LMStudioProvider
```

without rewriting the GUI.

---

# 10. Ollama Configuration

Default values:

```text
Host: http://localhost:11434
Model: gemma4:12b
```

The user must be able to change the Ollama host and model from application settings.

At startup, the application should check whether Ollama is reachable.

Possible states:

```text
AI: Connected
AI: Connecting...
AI: Offline
AI: Error
```

If Ollama is unavailable, the editor must remain fully functional.

---

# 11. AI Completion

Inline completion is the primary AI interaction.

When the user pauses after typing, the application should request a possible continuation from the AI model.

Example user text:

```text
Today I want to
```

Possible completion:

```text
write a short description of my project.
```

The completion must appear visually as ghost text:

```text
Today I want towrite a short description of my project.
             └────────────────────────────────────────┘
                         ghost text
```

The ghost text must not become part of the document until explicitly accepted.

---

# 12. Inline Suggestion Requirements

A completion suggestion must:

* be displayed at the current cursor position;
* visually differ from normal document text;
* not modify the underlying document;
* disappear when the relevant document state changes;
* be associated with the cursor position and document revision.

The completion must not overwrite or alter existing document content.

---

# 13. Accepting a Completion

Pressing:

```text
Tab
```

must accept the currently displayed inline completion.

After acceptance:

1. the suggested text becomes real document text;
2. the ghost text disappears;
3. the cursor moves to the end of the inserted text;
4. the change becomes part of the normal undo history.

If there is no active completion, `Tab` should behave according to the editor's normal tab/indent behavior.

---

# 14. Rejecting a Completion

Pressing:

```text
Esc
```

must reject the current completion.

After rejection:

* the suggestion disappears;
* the document remains unchanged.

A completion must also be invalidated when:

* the user changes the text;
* the cursor moves;
* the selection changes;
* the active document changes.

---

# 15. Completion Debounce

The editor must not send an Ollama request after every keystroke.

Use a short debounce interval.

Recommended initial value:

```text
300–800 ms
```

The exact default should be configurable.

Example flow:

```text
User types
    ↓
Debounce timer
    ↓
No new input
    ↓
Request completion
    ↓
Display result
```

---

# 16. Stale Completion Protection

Every document must maintain a revision identifier.

Example:

```text
Document revision = 154
```

When a completion request starts, the request records the current revision:

```text
Request revision = 154
```

If the document changes:

```text
Document revision = 155
```

and a response for revision `154` later arrives, that response must be discarded.

The application must never display an AI suggestion generated from stale document state.

---

# 17. Completion Context

The completion service must provide the model with relevant context around the cursor.

The context should include:

* text before the cursor;
* current paragraph;
* recent preceding sentences;
* optionally text after the cursor;
* document language.

Do not send the entire document on every request unless necessary.

The context-building logic must be isolated from the GUI.

---

# 18. Completion Prompt

Completion prompts should instruct the model to produce only the continuation.

Conceptually:

```text
You are an inline text completion engine.

Continue the user's text naturally.

Rules:
- Generate only the continuation.
- Do not repeat existing text.
- Do not explain the answer.
- Preserve the language of the document.
- Keep the continuation concise.
- Prefer a short continuation.
- Do not introduce unrelated content.
```

The implementation may refine this prompt during development.

Prompt construction should be centralized in:

```text
app/ai/prompts.py
```

---

# 19. Completion Length

Suggestions should remain short.

Recommended initial range:

```text
5–100 tokens
```

The default should favor short completions.

The maximum completion length should be configurable.

---

# 20. Streaming

The architecture should support streaming responses from Ollama.

For the MVP, either streaming or non-streaming completion is acceptable, provided that:

* the UI remains responsive;
* stale responses are ignored;
* partial responses cannot corrupt the document;
* only accepted text is inserted into the document.

---

# 21. Spell Checking

The editor should provide AI-assisted spelling and basic grammar checking.

Errors should be visually highlighted.

Example:

```text
This sentense contains a mistake.
     ~~~~~~~
```

The AI should return structured information rather than arbitrary explanatory text.

Example:

```json
{
  "start": 5,
  "end": 12,
  "replacement": "sentence",
  "type": "spelling",
  "explanation": "Possible spelling error."
}
```

The exact schema may be extended, but the response must remain machine-parseable.

---

# 22. Spellcheck Result Validation

AI responses must be validated before being used by the editor.

Invalid responses must be rejected safely.

The application must never:

* blindly execute model output;
* assume that offsets are valid;
* modify document text without validation.

Before applying a correction, verify that:

* the referenced document revision is still current;
* the specified text range is valid;
* the expected original text still matches the document.

---

# 23. Applying Corrections

When a spelling or grammar error is selected, the user must be able to:

* apply the suggested replacement;
* ignore the suggestion.

Suggested UX:

```text
Right click

Replace "sentense" with "sentence"
Ignore
```

Applying a correction must create a normal undoable editor operation.

---

# 24. Spellcheck Scheduling

Spellcheck must not run after every keystroke.

Possible triggers:

* short pause after editing;
* completion of a sentence;
* completion of a paragraph;
* switching focus;
* explicit `Check Spelling` command.

The implementation may choose an appropriate scheduling strategy for the MVP.

---

# 25. Supported Languages

The MVP should support:

* English
* Ukrainian

Language selection:

```text
Auto
English
Ukrainian
```

Automatic language detection may be used when `Auto` is selected.

The AI layer must pass the selected language to the relevant service.

The architecture should allow additional languages to be added later.

---

# 26. AI Menu

The `AI` menu should contain:

```text
AI
├── Enable AI
├── Check Spelling
├── Generate Completion
├── Accept Suggestion
├── Reject Suggestion
└── Settings
```

The exact menu layout may be adapted to Qt conventions.

---

# 27. AI Settings

The settings dialog should provide at least:

## Provider

```text
Provider:
Ollama
```

## Connection

```text
Host:
http://localhost:11434
```

## Model

```text
Model:
gemma4:12b
```

## Completion

```text
Completion enabled
Debounce delay
Maximum suggestion length
Temperature
Context size
```

## Spellcheck

```text
Spell checking enabled
Automatic spellcheck enabled
```

All settings should have safe defaults.

---

# 28. Editor Settings

The editor settings should include:

```text
Font
Font size
Tab width
Word wrap
Show line numbers
Theme / Dark mode
```

These settings should be independent of the AI settings.

---

# 29. Error Handling

AI failures must never crash the application.

Examples:

```text
Ollama is not available.
AI features are temporarily disabled.
```

Possible failure cases include:

* Ollama is not running;
* model is missing;
* connection timeout;
* malformed model response;
* invalid JSON;
* cancelled request;
* unexpected HTTP error.

All failures should be handled gracefully.

The editor must continue functioning.

---

# 30. Concurrency

All Ollama operations must execute outside the GUI thread.

The implementation may use:

* `QThread`;
* `QThreadPool`;
* `QtConcurrent`;
* asyncio integrated appropriately with Qt.

Choose one concurrency model and use it consistently.

Avoid mixing concurrency mechanisms without a clear reason.

---

# 31. Project Structure

A recommended initial structure:

```text
UTextEditor/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── editor_widget.py
│   │   ├── tab_widget.py
│   │   └── ...
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── ollama_client.py
│   │   ├── completion_service.py
│   │   ├── spellcheck_service.py
│   │   └── prompts.py
│   │
│   ├── document/
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── file_manager.py
│   │   └── encoding.py
│   │
│   └── settings/
│       ├── __init__.py
│       └── settings.py
│
└── tests/
    ├── test_document.py
    ├── test_file_manager.py
    ├── test_completion_service.py
    ├── test_spellcheck_service.py
    └── ...
```

The exact structure may evolve as implementation progresses.

Do not create unnecessary modules solely to match this example.

---

# 32. Testing Requirements

Use `pytest`.

Unit tests are required for:

* document state;
* dirty state;
* file operations;
* tab management;
* context generation;
* prompt generation;
* completion response parsing;
* spellcheck response parsing;
* validation of AI responses;
* stale response handling;
* suggestion acceptance;
* suggestion rejection.

Ollama should not be required for unit tests.

Use mocks or fake providers for AI-related tests.

---

# 33. Integration Testing

The architecture should allow integration testing with a fake Ollama server or mocked provider.

Integration tests should verify at least:

```text
Editor
  ↓
CompletionService
  ↓
AIProvider
  ↓
Completion
  ↓
Inline suggestion
  ↓
Tab
  ↓
Document update
```

and:

```text
Editor
  ↓
SpellcheckService
  ↓
AIProvider
  ↓
Structured result
  ↓
Validation
  ↓
Correction
```

---

# 34. Logging

Application logs should be written to:

```text
logs/utexteditor.log
```

Logs should include:

* timestamp;
* operation;
* provider;
* model;
* request identifier;
* request duration;
* error information.

Do not log full document contents by default.

Do not write secrets or credentials to logs.

---

# 35. Security and Privacy

The application must not execute arbitrary instructions returned by the AI model.

AI output is untrusted data.

The application must:

* validate structured AI responses;
* validate document revisions;
* validate text ranges before applying changes;
* avoid executing model-generated shell commands;
* avoid writing arbitrary model output to executable files automatically.

All AI requests should remain local by default.

---

# 36. UX Requirements for AI

AI functionality should be unobtrusive.

The normal interaction should feel like:

```text
Type → AI suggests → Tab accepts
```

The user must not be forced to interact with the AI.

The editor should not automatically:

* rewrite user text;
* insert completions;
* change spelling;
* change grammar;
* open AI dialogs while typing.

The user always controls whether generated content becomes part of the document.

---

# 37. Performance Requirements

The application should remain responsive during AI activity.

Requirements:

* no blocking AI calls on the GUI thread;
* debounce completion requests;
* discard stale responses;
* avoid unnecessary full-document processing;
* avoid sending the entire document on every keystroke;
* avoid excessive simultaneous AI requests.

Only the latest relevant completion request should normally be considered valid.

---

# 38. MVP Acceptance Criteria

The MVP is complete when all of the following are true.

## Basic Editor

* [ ] Application starts successfully.
* [ ] A new document can be created.
* [ ] Existing text files can be opened.
* [ ] Files can be saved.
* [ ] Save As works.
* [ ] Multiple documents can be open in tabs.
* [ ] Unsaved changes are clearly indicated.
* [ ] Undo and redo work.
* [ ] Copy, cut, paste, and select all work.
* [ ] Find and replace work.

## Ollama

* [ ] UTextEditor can connect to `http://localhost:11434`.
* [ ] `gemma4:12b` can be selected as the model.
* [ ] Ollama connection status is visible.
* [ ] Missing Ollama does not crash the editor.
* [ ] Missing AI does not prevent normal text editing.

## Completion

* [ ] Completion requests are triggered after a typing pause.
* [ ] Requests do not block the GUI.
* [ ] A completion is displayed as ghost text.
* [ ] Ghost text does not modify the document.
* [ ] `Tab` accepts the completion.
* [ ] `Esc` rejects the completion.
* [ ] Completion disappears when the document state changes.
* [ ] Stale responses are ignored.
* [ ] Accepted completion is undoable.

## Spellcheck

* [ ] Text can be checked for spelling errors.
* [ ] Errors are visually highlighted.
* [ ] Corrections are returned in a structured format.
* [ ] Invalid AI results are rejected safely.
* [ ] Users can apply corrections.
* [ ] Users can ignore corrections.
* [ ] Applied corrections are undoable.

## Responsiveness

* [ ] The application remains responsive during AI requests.
* [ ] The editor remains usable when Ollama is offline.
* [ ] AI errors do not crash the application.

## Testing

* [ ] Unit tests exist for core document logic.
* [ ] Unit tests exist for AI response validation.
* [ ] Unit tests do not require a live Ollama instance.
* [ ] `pytest` passes before an MVP release.

---

# 39. Definition of Done

A feature is considered complete only when:

1. The implementation matches this specification.
2. The code follows the project architecture.
3. Relevant tests have been added or updated.
4. Tests pass.
5. The GUI remains responsive.
6. AI failures are handled safely.
7. No unrelated files are modified.
8. Documentation is updated when project behavior changes.

---

# 40. Future Features

The architecture should leave room for future features such as:

* AI rewrite;
* AI translation;
* summarization;
* explain selected text;
* AI sidebar/chat;
* Markdown preview;
* syntax highlighting;
* multiple completion candidates;
* project-aware context;
* custom system prompts;
* additional AI providers;
* Windows support;
* plugin architecture.

These features are outside the MVP scope and should not be implemented unless explicitly requested.

---

# 41. Development Priority

Implement the project incrementally in this order:

## Phase 1 — Editor

Build the basic desktop editor:

* main window;
* menus;
* text editing;
* tabs;
* open/save;
* undo/redo;
* search/replace;
* status bar.

## Phase 2 — Ollama Integration

Implement:

* provider abstraction;
* Ollama client;
* connection checking;
* model configuration;
* error handling.

## Phase 3 — Completion

Implement:

* context extraction;
* prompt generation;
* async requests;
* debounce;
* stale request protection;
* ghost text rendering;
* `Tab` acceptance;
* `Esc` rejection.

## Phase 4 — Spellcheck

Implement:

* spellcheck service;
* structured response format;
* validation;
* highlighting;
* replacement;
* ignore action.

## Phase 5 — Polish

Implement:

* settings;
* themes;
* logging;
* improved error messages;
* additional tests;
* documentation updates.

---

# 42. Source of Truth

`README.md` is the primary product specification for UTextEditor.

`AGENTS.md` contains implementation instructions for coding agents.

When implementing a feature, use both documents:

```text
README.md
    ↓
What the application must do

AGENTS.md
    ↓
How the repository should be changed
```

If implementation details are ambiguous, prefer the simplest solution that satisfies the stated requirements without introducing unnecessary complexity.
