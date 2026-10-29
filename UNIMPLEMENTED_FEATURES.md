# Remaining features and known limitations

This file lists work that is not currently implemented. Completed project,
document, AI, export, and character workflows are described in `README.md` and
are intentionally omitted here. The detailed product requirements and
acceptance guidance remain in `SPEC.md`.

## Character development and AI review

- **Proposed character updates:** AI workflows do not return structured
  character-state proposals with evidence and individual accept/reject
  controls. Generated or analyzed content must continue to leave profiles
  unchanged unless the author edits them directly.
- **Structured continuity findings:** continuity review is an AI-authored
  text analysis. It does not yet validate a structured result containing
  confidence, affected character and scene IDs, evidence references, and
  suggested resolutions.
- **Portraits:** character profiles do not manage or package portrait assets.

## Project and revision workflows

- **Recovery diagnosis:** recovery supports restore, inspection/comparison,
  project relocation, discard, and defer. Repair and diagnosis for partial or
  corrupt recovery sets remain limited.
- **Revision management:** scheduled snapshots, deletion, and restore with a
  preview are not available. Comparisons cover scenes and reference notes,
  but not all chapter, link, and project-structure changes.
- **Large documents and encodings:** files are read into memory as a whole;
  the editor supports UTF-8 only, and encoding and line-ending choices are not
  selectable in the status bar.
- **Standalone-document recency:** the Project menu tracks recent projects;
  there is no recent standalone-document list.

## Writing and language tools

- **Batch spellcheck review:** spelling and grammar suggestions are presented
  per finding; there is no dedicated batch review workflow.
- **Language detection:** automatic language choice uses local script and
  common-word signals, leaving ambiguous or short text to the model.
- **Project-wide search:** character profile search and scene search by a
  character's name or aliases are available. General full-text search across
  all manuscript and reference-note content is not.

## Interface localization

- **Complete UI translation:** English source text and Ukrainian Qt Linguist
  catalogs are available for the main menus, project navigation, settings,
  find/replace, and selected character, analysis, generation, writing-goal,
  and Auto-writer dialogs. Many MainWindow prompts, error paths, and less-used
  dialogs still fall back to English and need migration and translation.
- **Catalog audit tooling:** extraction and compilation are documented, but a
  dedicated automated check for missing translations and placeholder parity
  across all UI catalogs is not yet part of the developer workflow.

These gaps are independent of basic standalone editing, which remains usable
without a project or a running Ollama server.
