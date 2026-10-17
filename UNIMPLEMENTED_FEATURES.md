# Detailed specification: future novel-writing features

This document turns the novel-writing direction in `README.md` and Section 22 of
`SPEC.md` into behavior and acceptance requirements. These features are not
implemented and are not part of the current MVP. This specification does not
change the MVP scope. If requirements conflict, `README.md` takes precedence;
update this document when a product decision changes the direction.

The requirements below define expected behavior for normal workflows and
important failure and edge cases. They are intended to make future
implementation and testing unambiguous, not to claim that every conceivable
environment failure can be predicted.

## 1. Product principles and boundaries

- Keep UTextEditor a native desktop application. Project management must not
  make ordinary standalone text editing depend on a project being open.
- Keep manuscript prose in ordinary UTF-8 text files in a user-visible project
  folder. A project must remain browsable, editable, and back-up-able with
  general-purpose file tools.
- Project metadata may describe ordering, titles, and links, but must not be
  the sole copy of manuscript or note content. Do not use a proprietary
  database as the canonical store.
- Keep reference notes distinct from manuscript prose. Linking a note to a
  scene must not insert or copy the note into that scene.
- Never silently discard, reorder, overwrite, or rewrite author content.
- Any AI feature is opt-in, runs through the configured local `AIProvider`
  (Ollama by default), runs off the GUI thread, and presents analysis or
  proposed text separately. AI output never changes a manuscript or note
  without explicit author acceptance.
- Continue to support projects with AI disabled or Ollama unavailable.
- Keep project/document services, file persistence, AI services, and Qt UI
  responsibilities separate. Workers must return results to the GUI thread;
  stale work must not apply to changed or closed content.

## 2. Terminology and project model

- **Project:** A directory selected by the author that contains one manuscript
  and its UTextEditor organization metadata.
- **Chapter:** An ordered grouping of scenes. A project may have zero or more
  chapters; empty chapters are allowed while planning.
- **Scene:** An ordered, independently editable text document belonging to a
  chapter, or an ungrouped scene in the project.
- **Manuscript:** The project's ordered sequence of scenes. Chapter titles and
  scene titles are organization metadata, not automatically part of scene
  prose.
- **Reference note:** A separate text document for a character, setting,
  timeline, research item, or general note. It may be linked to scenes and
  other notes.
- **Project view:** A navigation view of project structure and reference
  material. Opening a project must not replace or close unrelated standalone
  documents.

Project identifiers must be stable across rename and reorder operations. A
scene's file path is not its identity; metadata should refer to stable IDs so
reordering or renaming does not break links. IDs must be unique within a
project. Invalid or duplicate IDs must produce a recoverable project error,
not cause content to be silently merged or lost.

## 3. Project storage and portability

### 3.1 Files and metadata

Version 1 uses a UTF-8 YAML manifest named `utexteditor.yaml` in the project
root, with manuscript text under `manuscript/` and reference notes under
`notes/`. Scene and note filenames are generated from titles for readability,
but titles and paths are separate fields. Authors may import files from other
project-relative folders. The project root contains ordinary text files and
this documented, versioned manifest for structure. The manifest records at
least:

- format version and project identity;
- project title;
- ordered chapters and scenes, including stable IDs, display titles, and
  project-relative paths;
- ungrouped scenes, if any;
- reference-note IDs, types, titles, and project-relative paths;
- explicit links between notes and scenes or other notes.

The manifest is organization metadata only. Scene and note content stays in
their referenced files. Use a human-readable format, write it atomically, and
validate paths before access. No path in the manifest may escape the project
root, including through `..` segments or symlinks that resolve outside it.
Avoid absolute paths so a copied project remains usable at a different
location.

The version 1 manifest schema, including required/optional fields and
validation rules, must be documented and covered by fixtures before
implementation. A future version must either migrate a project safely or
explain how to open it read-only/export its content; it must never silently
reinterpret or discard project data.

### 3.2 Create and open

- **Create project:** The author chooses a new or existing empty directory and
  project title. Validate write access before reporting success. Create the
  manifest and initial project structure transactionally; if creation fails,
  report the failure and leave existing files untouched.
- **Existing non-empty directory:** Do not overwrite files. Offer to open it
  as a project only if it contains a valid project manifest; otherwise let the
  author choose another directory or cancel. Importing loose files is a
  separate explicit action.
- **Open project:** Validate the manifest and referenced paths before
  presenting the project. A failed or unsupported project open must leave
  the current project and all open documents untouched.
- **Already-open project:** Select its existing project view rather than
  opening a duplicate project instance.
- **Standalone file inside a project:** Opening it through the project view
  selects the corresponding scene/note. Opening it through the ordinary File
  > Open action may open it as a standalone document; it must not silently
  enroll it in project structure.
- **Close project:** Closing the project view does not delete files. If
  project documents are dirty, resolve their save/discard/cancel prompts
  before closing. Cancel leaves the project and documents open.
- Opening, creating, or closing a project must not silently close unrelated
  standalone tabs. If the UI has a single active project, switching projects
  must preserve or explicitly close the previous project according to the
  dirty-document rules above.

### 3.3 Manifest and filesystem discrepancies

On project open and refresh, distinguish these cases and give the author a
recoverable choice:

- Missing manifest: do not guess project structure or overwrite the directory.
- Unsupported manifest version: explain the version mismatch and do not write
  the project.
- Malformed manifest, invalid encoding, duplicate IDs, invalid references, or
  paths outside the root: report the specific issue; do not partially load
  structure in a way that risks writing over it.
- Referenced scene or note file missing: show the entry as missing, preserve
  its metadata and ordering, and offer locate, recreate empty, remove entry,
  or cancel. Recreate must require confirmation and must not overwrite a
  different file.
- Unreferenced text file in a project folder: do not automatically enroll or
  delete it. Offer an explicit import/add action.
- Referenced path now points to a directory, unsupported file, or unreadable
  file: retain the entry and report the problem without replacing its content.
- A file renamed or moved outside the application: provide a relink action;
  do not silently create an empty replacement.
- External changes while a document is open: compare the on-disk version with
  the last known saved version before saving. Offer reload, keep editor
  version, compare, or cancel. Never silently overwrite external edits.
- Read-only directory or permission failure: allow reading where possible,
  clearly mark project/document read-only, and explain which actions cannot
  persist.

## 4. Project workspace and manuscript organization

### 4.1 Navigation and selection

The project view presents chapters in manuscript order, scenes within each
chapter in scene order, ungrouped scenes if present, and a separate reference
notes section. It shows missing/unavailable entries distinctly from openable
ones. Selecting an entry opens or selects its document; selection alone does
not change manuscript content or order.

The active scene/document and its dirty state must be apparent. Switching
between scenes preserves each document's text, undo history for as long as
the document remains open, cursor/selection where practical, and independent
AI/spellcheck state. A response belonging to a previous scene must not appear
in the newly selected scene.

### 4.2 Add, rename, move, and remove

- **Add chapter:** Create a uniquely identified chapter with a validated
  title. It may begin empty.
- **Add scene:** Create a new UTF-8 text file with a safe generated name and
  add it at the selected location. If file creation or manifest update fails,
  roll back the incomplete operation or report exactly what remains for
  recovery; do not claim success.
- **Import scene:** Select an existing text file inside the project. Confirm
  before copying/moving a file from outside the project. Reject unsupported
  encoding with a clear explanation; never silently replace undecodable
  content. Duplicate imports must not create ambiguous entries.
- **Rename title:** Update the display title without changing prose. File
  renaming is a separate explicit choice because external links and tools may
  depend on the path.
- **Rename file:** Confirm the resulting path and collision behavior. Do not
  overwrite an existing file. Update metadata only after the move succeeds;
  on failure preserve the prior metadata and path.
- **Reorder:** Drag-and-drop and accessible Move Up/Move Down actions update
  chapter or scene ordering. Reordering must not rewrite scene files. Reject
  a drop into an invalid target and restore the original order. A scene may
  move between chapters or to/from the ungrouped list only by an explicit
  valid operation.
- **Remove from project:** Confirm whether the author means remove the
  structure entry only (leave the text file untouched) or delete the file.
  File deletion requires a second clear confirmation, must not delete files
  outside the project, and must respect open/dirty document prompts.
- **Delete chapter:** If it contains scenes, require an explicit destination
  (move scenes to another chapter/ungrouped) or explicit per-scene removal.
  Never cascade-delete manuscript files without a clear confirmation.
- **Duplicate scene:** Create a distinct scene ID and file. Preserve the
  original. Do not duplicate external links as though they point to the same
  scene; copied links must be confirmed or left out.
- **Invalid title or path collision:** Keep the prior valid state and explain
  what needs correction. Sanitize generated file names, but retain the exact
  user-facing title.

All organization changes are undoable where practical within the current
session or must offer a clear confirmation before applying. If undo cannot
reliably reverse a filesystem operation, use transactional operations and
state the limitation before the action. Saving metadata must be atomic.

### 4.3 Word counts

Show live word counts for each scene, chapter, and full manuscript, and update
them after edits, add/remove, reorder, and document save/reload. Project count
is the sum of included manuscript scenes, not reference notes, labels, or
chapter titles. A scene appears exactly once in that total.

Use one documented counting rule consistently: a word is a non-empty run of
letters or digits, allowing internal apostrophes and hyphens when surrounded
by word characters. Punctuation-only runs are not words. Keep counts local;
do not send manuscript text to a service to count it.

Handle empty scenes as zero words, whitespace-only content as zero, Unicode
letters as words, and pasted/newline text without double counting. Reordering
does not change totals. While a file is missing or unreadable, mark the
affected count incomplete instead of presenting a misleading zero. Identify
the count as approximate if the implementation uses a different documented
tokenization rule.

## 5. Saving, autosave, and crash recovery

### 5.1 Normal save and autosave

Retain the existing editor's explicit Save behavior. Autosave is a
supplementary protection mechanism, not a replacement for dirty-state
feedback or user-controlled file operations.

- Autosave only changed content, after a configurable idle interval; provide
  a default of two seconds after the last edit and allow disabling it.
- Save scene/note files using the same safe-write guarantees as ordinary
  documents. Update the saved revision and clear dirty state only after a
  successful replace.
- Show when a document has unsaved changes and when autosave is in progress
  or failed. Autosave failure leaves the document dirty and presents
  non-blocking, actionable feedback.
- Do not autosave over a file changed externally since the last known save.
  Invoke the external-change resolution flow.
- Project structural metadata is written atomically. If metadata saving fails,
  keep the in-memory structure and indicate unsaved project changes.
- Do not serialize undo history as part of autosave unless separately
  specified. Text and structure must remain recoverable.
- Autosave and recovery data must stay on the local machine. Document where it
  is stored and provide a way to inspect, restore, or remove recovery data.
- Recovery snapshots are captured at least every 30 seconds while a document
  is dirty and on orderly application shutdown. The configured autosave idle
  save may also refresh the recovery snapshot. Retention must be bounded and
  user-visible; prune only old snapshots that are not the latest recoverable
  version for a dirty document.

### 5.2 Crash and restart recovery

Maintain recoverable snapshots for dirty project documents and unsaved
structural changes. Recovery data must be isolated from canonical manuscript
files until the author chooses to restore it. Use safe, bounded retention;
never silently replace newer canonical files with a recovery snapshot.

At next startup:

- If no recovery data exists, start normally.
- If valid recovery data exists, show which project/documents have recoverable
  changes and their timestamps. Offer restore, inspect/compare, discard
  recovery data, or defer the decision.
- Restoring creates a recoverable editor state and marks it dirty until saved
  to the canonical path. If the canonical file changed after the snapshot,
  require compare/merge or Save As; do not overwrite automatically.
- If recovery data is corrupt or only partly readable, identify affected
  entries, recover readable documents independently, preserve the corrupt
  data for diagnosis until the author discards it, and do not block ordinary
  startup.
- If the project directory is unavailable, offer to locate it or defer
  recovery. Do not redirect recovery into a different project with a matching
  title.
- Discarding recovery data must not delete canonical project files.

Do not promise recovery from hardware failure or data outside the captured
snapshot interval. Communicate the autosave interval and that limitation.

## 6. Writing goals and distraction-free mode

These are follow-on writing workflow features and must remain independent of
project structure where possible.

### 6.1 Writing goals

Allow an author to set an optional daily word-count goal and choose its scope:
active scene, project manuscript, or words newly written during the day.
Define the daily reset using the system's local date and timezone. For a
"words newly written" goal, count word tokens added by typing or pasting in
the selected scope; deleting existing text does not reduce the count, while
undoing an insertion removes that insertion's contribution and redoing it
restores it. Other goal scopes use the selected content's current word count.

Display progress and completion without interrupting typing. Editing,
deleting, undoing, or moving between documents must recalculate the chosen
measure consistently. A timezone/date change must not erase stored progress.
When no goal is configured, show no nagging prompt. Authors can pause or reset
the goal; resetting affects goal tracking only and never changes manuscript
text. Do not upload goal or writing activity data.

### 6.2 Distraction-free mode

Provide an explicit View action and a reversible keyboard shortcut. Entering
the mode hides non-essential chrome while keeping the editor, active document
identity, and essential save/dirty feedback accessible. It must not disable
keyboard navigation, menus/actions needed to exit, accessibility tools, or
the ability to save.

- `Esc` or the visible exit action returns to the prior layout; if `Esc` is
  already reserved for dismissing an AI suggestion, dismiss that suggestion
  first and exit only on a subsequent action.
- Switching documents while in this mode does not unexpectedly exit it.
- Opening a modal dialog temporarily presents the required controls; closing
  it restores the mode.
- The mode does not alter text, wrapping, font, or other saved preferences
  unless the author separately changes those settings.
- Persist the preference only if the author explicitly chooses that behavior;
  otherwise return to the normal layout on restart.

## 7. Reference notes and links

Reference notes use separate ordinary text files and metadata entries. Initial
types are character, setting, timeline, research, and general. Authors can
create, rename, retype, edit, link, unlink, and remove notes. Deleting a note
must never delete a linked scene and must warn about affected links.

Notes and manuscript remain separate in navigation, word counts, and exports
unless an export option explicitly includes selected notes. Editing a note
uses the same dirty-state, save, external-change, autosave, and recovery
protections as a scene.

Links use stable project IDs, not titles or absolute paths. Display a note's
incoming/outgoing links and allow navigation in either direction. Renaming a
title must not break a link. If a target is missing or deleted, show an
orphaned-link state and offer relink/remove; do not silently retarget by
matching title. Duplicate notes receive new IDs; links are copied only by an
explicit author choice.

Linking and unlinking never changes prose. Search over notes is separate from
manuscript search unless the author selects a project-wide search scope.

## 8. Local, opt-in novel-aware AI

AI features are later work, not an implicit project-wide assistant. Initial
candidate actions are:

- summarize a selected scene, chapter, or manuscript range;
- check continuity against selected reference notes;
- return analysis, questions, or proposed changes for author review.

Before sending content, identify the selected source documents and notes and
the configured Ollama destination. Provide a clear confirmation/settings
path. Send only the selected bounded context and only the references required
for that task; never send every project file by default. No cloud fallback is
allowed.

Each request captures project/document IDs, revisions, selected range,
settings generation, and request identity. Run it in a worker, expose
progress/cancel where possible, and discard stale results after source
documents, selection, links, settings, or active project change. Cancellation
must prevent queued work; an in-flight request that cannot be stopped may
finish, but its result must not be applied as current.

Present summaries and continuity findings in a separate review panel with
source references where available. Treat model output as untrusted. It may
not modify files, reorder scenes, alter links, or insert prose by itself.
Any proposed text change must be shown as a diff or explicit replacement
preview and applied only after a separate author acceptance. Acceptance is
one undoable edit and must revalidate the source revision and target range.
If the source changed, require the author to review/regenerate; do not apply
by stale offsets.

If Ollama is offline, the configured model is missing, the request times out,
or the response is malformed, preserve all documents and show a concise,
actionable error. Empty results are not errors. Do not log prompts or full
manuscript excerpts. AI can be disabled globally and per operation.

## 9. Export and revision history

### 9.1 Manuscript export

Export is explicit and non-destructive. The author selects the project or a
subset, output format, destination, and whether to include chapter/scene
headings and separators. Initial formats should prioritize portable plain
text and Markdown; additional publishing formats require a separate
acceptance specification.

Export uses the current in-memory text and structure, including unsaved edits,
and leaves those edits dirty; the UI must identify when the export includes
unsaved content. Export follows current manuscript order, includes each selected scene once,
and excludes reference notes by default. Empty chapters/scenes follow the
author's heading/separator choice. Export must not alter source files,
metadata, dirty state, or undo history. If a destination exists, ask before
replacement; never overwrite without confirmation. On export failure retain
the existing destination where possible and report the error. Export must
handle Unicode and line endings predictably and document its output
encoding.

### 9.2 Revision snapshots and comparison

Allow explicit named snapshots and optionally scheduled snapshots only after
the author enables them. An explicit snapshot captures the current in-memory
text and structure, including unsaved edits, without clearing dirty state. A
snapshot records project structure and content state sufficiently to compare
or restore; store it locally and expose its storage/retention behavior. A
snapshot is not a substitute for external backups.

Comparison shows added, removed, moved, and changed scenes separately from
text changes. Text comparison identifies insertions and deletions without
changing either version. Restoring a snapshot is a new change, never a
destructive rewind: preserve the current version as recoverable history and
show a preview of files and structure that will change. Require confirmation,
respect dirty buffers and external modifications, and make the restore
undoable where feasible or provide an immediate rollback path.

If a snapshot is incomplete or corrupt, do not apply a partial restore.
Snapshot deletion requires confirmation and must not delete current project
files. Revision history remains local unless the author copies it as part of
a backup.

## 10. Cross-feature interactions and failure rules

- Switching projects, chapters, scenes, or notes never silently saves or
  discards dirty text. Use the common Save/Discard/Cancel flow.
- Reordering or renaming while an affected document is open preserves its
  editor buffer and identity. An in-progress save must finish or be
  invalidated safely before changing the underlying path.
- Deleting or removing an open document first resolves dirty state. Cancel
  aborts the entire deletion/removal transaction.
- Autosave, AI, word counts, export, and revisions must operate on a
  consistent document snapshot. If a document changes during a background
  operation, either use the captured snapshot and label it accordingly or
  discard stale output; never imply it reflects newer text.
- Project metadata and file changes that span multiple paths must have a
  recoverable transaction strategy. On partial failure, explain which
  operations succeeded and provide a safe retry/repair path.
- Errors must not destroy a valid prior manifest, manuscript, note, export,
  or snapshot. Use atomic replacement where applicable.
- Progress and background errors are non-blocking. No file, AI, recovery, or
  export work may freeze the GUI.
- Keyboard and screen-reader accessible controls must exist for core project
  actions; drag-and-drop cannot be the only way to reorder.
- Normal standalone editing remains available if a project manifest is
  unsupported, the project is read-only, recovery fails, or Ollama is
  unavailable.

## 11. Test and acceptance requirements

Future implementation must add automated tests for at least the following
cases. Use temporary directories, fake providers, and controlled workers;
tests must not require Ollama, network access, arbitrary sleeps, or user
configuration.

### Project and filesystem

- Create/open valid project; reject malformed and unsupported manifests
  without disturbing current state.
- Empty and non-empty directory behavior; duplicate project open.
- Create, import, rename, reorder, move, remove, duplicate, and delete chapter,
  scene, and note; cancellation and collision paths.
- Relative-path portability; traversal and symlink escape rejection.
- Missing, unreadable, read-only, externally renamed, externally modified,
  and unreferenced files.
- Failed file or manifest writes preserve prior content and report partial
  transaction state.
- Dirty document prompts on project switch/close/delete and each Save,
  Discard, Cancel outcome.
- Stable IDs and links survive title changes, file moves, and reorder; broken
  and duplicate IDs are recoverable.

### Counts and writing workflow

- Word-count rules for empty/whitespace-only text, Unicode, punctuation,
  apostrophes, hyphens, edits, reorder, repeated references, and unavailable
  files.
- Goal scope, daily boundary/timezone changes, goal disabled/paused/reset,
  edits and undo, and no-goal behavior.
- Distraction-free enter/exit, Escape precedence, dialog return, document
  switch, and unchanged manuscript/settings.

### Recovery, notes, AI, export, revisions

- Autosave success/failure, external conflict, disabled autosave, dirty-state
  retention, and atomic replacement.
- Startup recovery for valid, stale, missing-project, partial, and corrupt
  snapshots; restore never overwrites a changed canonical file automatically.
- Note CRUD, links in both directions, orphan handling, duplicate behavior,
  and notes excluded from manuscript totals/exports by default.
- AI opt-in/destination confirmation, bounded selected context, offline,
  timeout, missing model, malformed/empty output, cancellation, stale
  response, and accepted/rejected proposed edits.
- Export ordering, subset, headings/separators, Unicode, existing destination
  confirmation, failure preservation, and unchanged project state.
- Snapshot creation/comparison/deletion, incomplete snapshot, restore preview,
  dirty/external conflict, and rollback.
- GUI remains responsive during all background work; standalone editing
  continues when project or AI features fail.

### Feature acceptance checklist

- [ ] Project content is ordinary portable text; metadata is documented,
  versioned, safe, and recoverable.
- [ ] Chapter/scene organization, reordering, stable identity, and word counts
  work without changing prose unexpectedly.
- [ ] Save, autosave, crash recovery, and external-change handling preserve
  user content across success, cancellation, and failure.
- [ ] Notes remain separate, linkable reference documents.
- [ ] AI features are local, explicitly selected, background-only, stale-safe,
  and never silently edit content.
- [ ] Export and revision tools are explicit, non-destructive, and recoverable.
- [ ] All major workflows and failure paths above are covered by automated
  tests and relevant user documentation.
