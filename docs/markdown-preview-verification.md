# Markdown preview verification — TASK-027.V1

Reviewed 2026-11-01 from MarkdownPreview and MainWindow's active-editor/content
signals. This workflow is offline and never invokes an AIProvider.

- .01–.02: the dock follows the active editor and its unsaved text. Existing
  `test_markdown_preview_tracks_active_unsaved_tab` verifies editor switching;
  `test_preview_updates_unsaved_buffer_without_modifying_it` checks read-only
  presentation, unchanged source text and revision.
- .03 (partial): a 300 ms debounce captures at most 64 Ki UTF-16 units through a
  QTextCursor when the document exceeds the limit. One render worker at a time
  parses Markdown; returned HTML above 1 Mi characters is rejected. Editor,
  generation and revision checks discard obsolete work and schedule the newest
  capture. `test_stale_render_is_discarded_after_editor_switch` exercises a slow
  renderer. The large-prefix test now fails on any whole-buffer toPlainText call
  during capture, and still verifies truncation notice and unchanged source.
  HTML installation, preview clearing and bounded-prefix capture run on the GUI
  thread. Representative native latency and pathological Markdown benchmarks
  remain needed before the no-freeze acceptance gate can be claimed complete.
- .04: the browser is read-only; rendering creates an independent QTextDocument.
- .05: both renderer and browser override resource loading to return None.
  Automatic/external link opening is disabled. The existing resource test
  checks remote and local image URLs without contacting them.

Four focused preview/workflow tests pass. .01/.02/.04/.05 and V1 verified;
.03 and parent remain partial. V2 native keyboard/screen-reader and release
catalog checks also remain. This audit adds no runtime/translated strings;
existing README describes the prefix/worker/offline behavior accurately.
