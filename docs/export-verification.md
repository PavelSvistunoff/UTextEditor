# Manuscript export and PDF verification — TASK-028.V1

Reviewed 2026-11-01 from document/export.py, book_compiler.py, PdfOptionsDialog,
ExportPreviewDialog and MainWindow capture/worker/review callbacks.

- .01: Markdown/plain-text options now offer Preview before exporting (off by
  default). Rendering runs in the existing export worker, using captured scene
  metadata/open buffers and closed-scene reads. Preview returns before any output
  write. A read-only plain-text dialog displays at most 65,536 Python characters;
  a notice explains when the tail is omitted from display. Explicit Export writes
  the entire captured string through the shared atomic UTF-8/LF writer in a worker,
  without rereading source text. Cancel leaves any existing destination intact.
  This is an output-text preview; it does not preview PDF page layout.
- .02–.04/.06: PDF options provide A5/A4/Letter, title and optional author,
  chapter/scene headings and stable-ID scene selection. Existing book tests
  parse actual generated PDFs with QtPdf to check paper sizes, title/author,
  section pagination, selected headings and prose. Dark-palette tests render
  pages and verify white paper/black text; prose indentation/alignment is tested.
- .05: existing Markdown/plain-text rendering, scene subsets, heading/separator
  choices, UTF-8/LF output and overwrite confirmation are retained. Unselected
  scenes and notes are not implicitly read/exported. Open dirty scene inclusion
  still requires confirmation; source documents remain dirty and unsaved.

The preview checks captured project identity/generation and the open-scene
editor/revision/binding map before showing and after acceptance. Newer scene
edits discard the pending export. Both capture and write reject manuscript,
note and manifest destinations, including hard-link aliases rechecked after
review. An existing destination still requires the earlier explicit replacement
confirmation. Independent writers/crash guarantees remain limited as elsewhere;
this does not add an atomic filesystem snapshot across independent processes.

Seven new cases verify exact captured output despite subsequent closed-file
changes, cancel, changed scene/project, a newly created hard link to a source,
bounded Unicode display and writing the entire captured tail beyond the display
limit. Existing export/PDF tests cover missing text, atomic failure preservation,
files created after a no-overwrite check, selected sources and stale option
dialogs. Focused export/PDF/catalog checks: 52 passed. Ukrainian source strings
are added for the checkbox, review and stale feedback; source validation and
extraction/temporary compilation pass. No generated release catalogs changed.

Numbered tickets/V1 verified. Parent/V2 remain partial for native keyboard,
screen-reader, release-catalog and cross-platform PDF visual/pagination review.
The source inventory records that a PDF page preview is still absent. Large
exports still retain the complete rendered output; only preview display is
bounded, not total document/process memory (TASK-006/TASK-011).
