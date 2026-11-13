# UI localization inventory and disposition

This source audit covers all 35 Python modules directly under `app/ui/`, the
MainWindow worker-result paths, Qt built-in labels, and the catalog extraction.
It distinguishes interface wording from manuscript/project data, AI prompts,
protocol/diagnostic details and OS-owned dialog wording.

## Findings closed

| Owner | Reproduction | Disposition |
| --- | --- | --- |
| MainWindow._refresh_writing_goal | Enable/pause/complete goal; incomplete project counts | Translated progress, completion, incomplete-count and pause/resume templates |
| MainWindow._autosave_project_document | Autosave succeeds/fails | Translated callback statuses |
| MainWindow project/template AI handlers | Suggest, edit while pending, cancel, fail or apply Auto-pilot | Translated captured-context, cancellation, failure and generated-count messages; host/model/error values unchanged |
| ProjectBriefDialog | Start Auto-pilot / apply template suggestion | Translated default running and applied-review statuses |
| ProjectView.show_project/_add_scene | Missing scene/note or orphan link | Translated unavailable prefix, links header, missing target/source; titles/types/IDs remain data |
| MainWindow analysis completion | Scene summary / continuity | Translated captured timestamp/source heading; source labels/model result unchanged |
| MainWindow revision handlers | Create/load/compare invalid or unavailable snapshots | Translated categories/wrappers; stale/closed context suppressed |
| MainWindow open/save handlers | Missing/binary/invalid UTF-8 file, external-write conflict | Translated categories with original diagnostics and preserved dirty buffers |
| MainWindow project error presentation | Open/mutate/save profile/export/search with format/path errors | Shared typed presentation; system exception detail retained |
| MainWindow recovery restore | Unavailable/wrong/unidentified project | UI-captured immutable translated messages; English helper defaults preserve old callers |
| MainWindow character/profile and general AI failure handlers | Provider error, stale profile/scene/settings/project | Translated operation titles/wrappers; exact provider diagnostic retained; stale guards tested |
| Qt built-in controls | Standard Cancel/Close and context labels | Native app-wide qtbase catalog below the application catalog; English/missing-resource fallback resets standard controls |

## Exclusions reviewed

The expanded selected-call audit has ten candidates: application proper name;
AI activity label plus count; composed document/encoding/position/AI status;
character field/value plus translated Evidence; joined pretranslated file filters;
recent filename/path labels; four English/Ukrainian language autonyms. These
are not newly untranslated static interface wording.

A supplemental AST walk reviewed non-tr string constants and helper-call message
arguments in every UI module. Action-name lookup dictionaries are translated at
construction; stable scene/note/character IDs, note types, goal state syntax,
roles stored in profiles, page-size/font names, generated snapshot names and
editable planning template content are data. AI instructions, JSON/protocol/debug
markers and exact Python/provider/system exception strings are diagnostic/input
data, kept verbatim beneath localized categories. Recovery comparison defaults
are replaced by captured UI-language arguments in actual worker calls.
Native OS file panels and menu wording may follow the OS language; this source
migration does not change system language or claim VoiceOver/system-palette audit.

## Reproducible audit

- `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python tools/audit_ui_strings.py`
- `pyside6-lupdate app/ui/*.py -ts /private/tmp/utexteditor-complete-check.ts`
- `python tools/check_translations.py translations/utexteditor_uk.ts --reference /private/tmp/utexteditor-complete-check.ts`
- Supplementary inspection: AST constants outside `tr()`/f-strings plus owners of
  raw exception strings and dynamic helper arguments; dispositions are above.
- 970 extracted strings; 980 finished Ukrainian messages; both catalogs compile.
  Packaged/source parity and placeholder/plural checks pass.

TASK-032.01/.02/.04 are complete for this inventory and current acceptance wording,
validated by the full offscreen suite (1093 passed, 2 skipped), final focused fallback suite (47 passed), and native localization/focus subset (44 passed). Future interface additions
still need extraction/migration; data/diagnostic exclusions do not imply that
arbitrary runtime user text is translated.

## Dialog-class inventory for focus acceptance

The native focus matrix constructs all 24 standalone QDialog subclasses, checks
initial focus and forward/back Tab without text edits, keyboard rejection via
Enter on Cancel or Esc, and actual focus return to the owner. Additional consent
cases check initial Not now and explicit Enter/Space Allow. Full native core UI
regressions separately cover main-window workflows and staged profile return.

- `app/ui/ai_context_disclosure.py` — `AIContextDisclosure`
- `app/ui/ai_debug_window.py` — `AIDebugWindow`
- `app/ui/analysis_window.py` — `AnalysisWindow`
- `app/ui/auto_writer_dialog.py` — `AutoWriterDialog`
- `app/ui/auto_writer_dialog.py` — `AutoWriterProgressDialog`
- `app/ui/auto_writer_review_dialog.py` — `AutoWriterReviewDialog`
- `app/ui/character_dialog.py` — `CharacterDialog`
- `app/ui/character_relationship_dialog.py` — `CharacterRelationshipDialog`
- `app/ui/completion_context_dialog.py` — `CompletionContextDialog`
- `app/ui/completion_notes_dialog.py` — `CompletionNotesDialog`
- `app/ui/conflict_dialog.py` — `ConflictDialog`
- `app/ui/export_preview_dialog.py` — `ExportPreviewDialog`
- `app/ui/generated_text_dialog.py` — `GeneratedTextDialog`
- `app/ui/generated_text_dialog.py` — `StreamingPreviewDialog`
- `app/ui/pdf_options_dialog.py` — `PdfOptionsDialog`
- `app/ui/project_brief_dialog.py` — `ProjectBriefDialog`
- `app/ui/project_setup_dialog.py` — `ProjectSetupDialog`
- `app/ui/project_translation_review_dialog.py` — `ProjectTranslationReviewDialog`
- `app/ui/quick_open_dialog.py` — `QuickOpenDialog`
- `app/ui/revision_history_dialog.py` — `RevisionHistoryDialog`
- `app/ui/settings_dialog.py` — `SettingsDialog`
- `app/ui/spellcheck_review_dialog.py` — `SpellcheckReviewDialog`
- `app/ui/writing_goal_dialog.py` — `WritingGoalDialog`
- `app/ui/writing_goal_history_dialog.py` — `WritingGoalHistoryDialog`
