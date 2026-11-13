# Repository refactoring — final audit and acceptance

Status: **COMPLETE for the repository refactoring plan**, with the explicit
retained designs and verification limits below. This closes the six package
inventories; it does not mean that code cannot benefit from future improvements.
No new product feature or unapproved proposal was added to TASKS.md.

## Audit method and scope

Reviewed the checked-out Python source inventory through module/import graphs,
class/function bodies and call-site structure, duplicate-body and unused-import
candidates, branch/exception paths, relevant source excerpts and owning tests.
Every Python module is listed below, including package exports, tools, benchmarks
and test support. Structural scans prioritize review; they do not establish
correctness or prove a callback is unused. Qt callbacks, protocol methods and
public re-exports were not deleted on reference-count evidence alone.

For each package, considered responsibility, duplicated rules, names/side effects,
nesting, coupling, UI/domain/persistence separation, error handling, dead code and
missing coverage. Kept normal/failure/stale-state behavior behind existing tests;
added characterization before risky extractions. A green suite alone was not used
to close the inventory: standalone probes also uncovered the separate B1 defect.

## Findings and disposition

| Finding | Priority / risk | Resolution |
| --- | --- | --- |
| Revision comparison mixes six item categories | High: ordering, legacy metadata, false moves | Pure category functions; shared common-position rule; cross-category order regression before extraction; verified reads preserved. |
| Identical recovery/revision durable byte staging | High: cleanup, fsync, replacement | One snapshot writer behind existing methods; four injected fsync/replace failures preserve prior snapshots and clean staging. |
| Duplicated Unicode word knowledge | Medium: goal/count drift | document/word_count.py owns tokens; project count_words import API retained; undo/redo semantics unchanged. |
| MainWindow contains project file/AI rules | High: data loss, stale workers | Planning, analysis, summary, recovery, bound save, export and snapshot services extracted; original static entry points retained. UI still owns capture, consent, worker dispatch and generation guards. |
| Repeated captured export text selection | High: unsaved text and unwanted reads | Shared scene capture honors selected IDs/open buffers and validates destinations before reads; pure worker tests separated from UI suite. |
| Repeated AI fenced JSON handling and chat shape | Medium: parsing/protocol drift | Shared exact fence rule and Ollama payload builder; strict schema validation and tolerant spelling policy remain separate. Twelve pre-refactor boundary cases cover plain/fenced/prefixed responses. |
| Dense profile parsing and activity lambdas | Medium: diagnostic paths and terminal state | Named goal/knowledge records and terminal callbacks; stale results bypass result validators, discarded/cancelled states stay distinct. |
| Confirmed unused imports | Low | Removed only source-confirmed imports; intentional package exports retained. |
| B1: active goal reads new tab identity too early | Separate behavior fix | Editor smoke printed Qt AttributeError despite exit 0. Three scope regressions failed first; explicit initialization guard fixes callback ordering without changing tab signals or undo. Commit 561aa49. |

## Retained designs and residual risks

- MainWindow remains large because it coordinates many existing UI workflows.
  Domain/file/AI rules identified above have explicit owners. Remaining captures,
  modal review, queued signal wiring and operation-specific stale guards stay
  together rather than introducing mixins with hidden shared state. Function size
  is not a completion metric.
- Project remains a filesystem-backed aggregate. Manifest invariants, lock scope,
  transaction ordering, backup and rollback diagnostics stay explicit. Translation,
  selective scene replacement, profile export, PDF publication and settings writes
  have different guarantees; a universal transaction/writer abstraction would hide
  real differences and was deliberately rejected.
- Snapshot cleanup preserves the original failure if temporary unlink also fails.
  Existing project transactions report cleanup/rollback failures. No exception
  policy was silently broadened or changed as incidental cleanup.
- In-process locks plus fingerprint checks are not arbitrary concurrent-writer
  safety. Independent-writer races remain documented limitations.
- Reachable writing-goal metadata can grow with Qt editing history. Refactoring
  does not truncate Qt undo or resurrect the removed memory-growth ticket.
- Settings retain existing malformed-data fallback, defaults and recent-path
  compatibility. Changing these policies would be a behavior change, not cleanup.
- This machine uses Python 3.14.10 and Qt 6.11.2/macOS Cocoa. Python 3.12 and other
  OSes were not separately executed. VoiceOver speech and actual OS appearance
  transitions are not established by offscreen tests or this refactoring.
- Two live-Ollama cases remain intentionally skipped offline. No server/model
  quality or network performance claim is made.

## Verification

Baseline: 1093 passed, 2 skipped in 118.43s. Pure-refactor control: 1114 passed,
2 skipped in 124.94s. Final control after B1: **1117 passed, 2 skipped in 115.92s**. Log:
`/private/tmp/utexteditor-refactor-final-after-fix.log`.

Focused checks included: document/export/compiler/project/goals 268 passed;
revised comparison/recovery/goals/project 183 passed; project/AI 320 passed;
UI/E2E/setup/i18n 413 passed both before and after extraction; expanded UI 492
passed; AI/activity 228 passed; provider/project-worker/E2E/activity 89 passed;
settings/startup/catalog/domain group 127 passed. These overlap.

The six relocated domain-worker cases pass without QApplication, and importing
all extracted non-PDF services does not load PySide6. Native Cocoa dialog focus
and activity matrix: 36 passed before B1; final native acceptance after B1: **39 passed in 7.34s**, including
the all-dialog matrix, activity cases and all three goal scopes. Log:
`/private/tmp/utexteditor-refactor-native-acceptance.log`. No new dependency, formatter or generated-file update.

Fresh lupdate extraction: 970 source messages, Ukrainian reference validation
passed. Source/catalog tests passed. All five standalone benchmark tools ran:
completion context, 43-case language corpus, project search (6 scenes × 2 lines),
editor (10,000 characters, one repetition), writing history (30 mixed commands,
10 undo/redo). These are bounded smoke workloads, not general performance gates.
The initial editor smoke traceback was not counted as a clean result; its final
rerun after B1 has no traceback. `git diff --check` passed; unrelated staged pyc
and DS_Store files were excluded from every scoped commit.

## Completion review

- [x] Intent: focused names, named callbacks and explicit captured values.
- [x] Ownership: UI/domain/persistence/provider responsibilities have defined owners.
- [x] Safety: public call shapes, IDs, YAML, undo, dirty text, rollback and stale guards retained.
- [x] Errors: original diagnostics retained; separate B1 lifecycle fix reproduced first.
- [x] Tests: focused and full offline checks, directly executed native subset; exclusions stated.
- [x] Diff: no dependencies, unrelated worktree changes or speculative framework.
- [x] Report: all planned packages disposed below; deliberate trade-offs explained.

## Application module inventory

| Module | Review disposition |
| --- | --- |
| `app/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/ai/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/ai/character_development.py` | Changed: common complete-fence removal; field uniqueness, exact scene evidence and response bounds remain service-owned. |
| `app/ai/character_profile.py` | Changed: common complete-fence removal; empty-field-only validation, structured syntax and timeout retained. |
| `app/ai/completion_service.py` | Retained: bounded context, captured note provenance and before/after closed-note checks. Provider forwarding methods retained as API. |
| `app/ai/continuity.py` | Changed: common complete-fence removal; exact captured-source evidence and associated-character restrictions retained. |
| `app/ai/models.py` | Retained: immutable provider-neutral suggestion value; no widget or I/O responsibilities. |
| `app/ai/ollama_client.py` | Changed: one chat payload constructor for completion/generation/streaming. HTTP errors, observer order, response caps and raw whitespace preserved. |
| `app/ai/project_analysis.py` | Added: bounded scene analysis and evidence validation moved from UI without changing prompts or source capture order. |
| `app/ai/project_planning.py` | Added: planning prompts and response checks moved from UI; author review and worker dispatch remain caller responsibilities. |
| `app/ai/prompts.py` | Retained: deterministic local language inference and prompt rendering; corpus and bounded-context tests retained. |
| `app/ai/provider.py` | Retained: synchronous Protocol; UI continues to invoke through workers. Ellipsis methods are contracts, not dead implementations. |
| `app/ai/spellcheck_service.py` | Retained: provider normalization and revision/range/overlap validation; malformed independent items remain conservative no-suggestion outcomes. |
| `app/ai/validation.py` | Changed: one complete JSON-fence helper; tolerant spelling extraction is not generalized into strict character/continuity parsers. |
| `app/document/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/document/book_compiler.py` | Retained: Qt document layout and PDF painting are one output adapter; source validation is shared with text export. Keep PDF publication distinct from JSON snapshot writes. |
| `app/document/document.py` | Retained: compact text/saved-state model; no persistence or widget dependency. Revision and dirty transitions remain explicit. |
| `app/document/encoding.py` | Retained: pure encoding/newline/UTF-16 conversion rules; frequency tie handling already clarified in earlier batch. |
| `app/document/export.py` | Retained: pure rendering plus explicit publication; link/no-overwrite and source-alias checks differ from snapshot replacement and must stay distinct. |
| `app/document/file_manager.py` | Retained: pre-stage and pre-replace fingerprints intentionally both remain; cleanup preserves the original write error. Not a cross-process CAS. |
| `app/document/merge.py` | Retained: bounded conservative merge proposal, never an implicit save. Conflict grouping is deliberately conservative. |
| `app/document/recovery.py` | Changed: shared snapshot byte writer behind existing API; retention, malformed-data preservation and conflict policies stay local. |
| `app/document/revisions.py` | Changed: comparison split by item category; common-position policy shared, verified re-reads and result order preserved. |
| `app/document/snapshot_write.py` | Added: exact shared recovery/revision staging protocol; serialization, validation and retention remain with stores. |
| `app/document/text_formatting.py` | Retained: pure transformations; Unicode and line-ending behavior covered. No Qt undo responsibilities here. |
| `app/document/word_count.py` | Added: single Unicode word-token rule for manuscript counts and inserted-word tracking. |
| `app/document/write_lock.py` | Retained: one reentrant in-process write lock; no claim of independent-writer locking. |
| `app/document/writing_goals.py` | Changed: shared word token rule; immutable daily counts and reachable undo endpoints retained. Store stays separate from tracker. |
| `app/i18n.py` | Retained: native translator lifecycle and English/missing-resource reset were already fixed and verified in the prior batch. |
| `app/logging_config.py` | Retained: minimal logging configuration without manuscript persistence. |
| `app/main.py` | Retained: composition root with optional logging/icon fallbacks and package/script entry points. Broad optional-setup catches log diagnostics and preserve startup. |
| `app/project/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/project/auto_writer.py` | Retained: snapshot/generate/review-result sequence and callback ordering; target limits and preceding-scene context differ from translation. No generic generation pipeline added. |
| `app/project/autopilot.py` | Retained: additive-plan validation, duplicate-key rejection and cancellation. JSON policy intentionally stricter/different from spelling extraction. |
| `app/project/character_context.py` | Retained: one bounded context owner; explicit scene associations, knowledge limits and relationship direction preserved. |
| `app/project/character_export.py` | Retained: destination-first loading, captured profile and exclusive-link/replace policies. Do not replace it with manuscript or JSON-store publication. |
| `app/project/document_binding.py` | Added: captured binding value and conflict-aware scene/note save; UI API aliases remain available. |
| `app/project/manuscript.py` | Added: source protection, captured scene selection, preview/text/PDF worker operations; one buffer-precedence rule. Qt PDF dependency loads only for compilation. |
| `app/project/model.py` | Changed: named goal/knowledge parsing with indexed diagnostics. Model validation keeps one manifest invariant traversal and the v1 schema unchanged. |
| `app/project/outline.py` | Changed: bounded project outline metadata moved from UI alongside existing outline rules; parser behavior unchanged. |
| `app/project/paths.py` | Retained: filesystem resolution is distinct from lexical manifest validation; error type and symlink checks preserved. |
| `app/project/portrait.py` | Retained: portable base64/header/byte limits; pixel decoding remains with Qt image adapter. |
| `app/project/recovery.py` | Added: stable-ID/legacy relocation resolution and separate dirty recovery fallback; captured localized messages have no widget dependency. |
| `app/project/revisions.py` | Added: complete project snapshot assembly from buffers and missing disk documents; store remains document-owned. |
| `app/project/search.py` | Retained: bounded read/search lifecycle, omitted-buffer sentinel and cancellation checks. Read failure must never substitute disk for omitted unsaved text. |
| `app/project/service.py` | Changed: shared word counting and confirmed unused imports. Aggregate owns project persistence; existing staged transaction phases and lock boundaries deliberately retained. |
| `app/project/summary.py` | Added: captured-buffer counts and disk availability outside MainWindow; incomplete counts remain explicit. |
| `app/project/translation.py` | Retained: source snapshot, traversal, edge layout and whole-project transaction policies. These differ from selective Auto-writer updates. |
| `app/settings/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/settings/settings.py` | Retained: validated settings boundary and atomic replacement. Recent-project trim/truncate and recent-file exact-name preservation intentionally differ; do not merge their policies. |
| `app/ui/__init__.py` | Retained: package marker or intentional public exports; imports are not dead solely because this module does not call them. |
| `app/ui/ai_activity.py` | Changed: unused Qt import removed; terminal-state, retry and bounded history behavior retained. |
| `app/ui/ai_context_disclosure.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/ai_debug_window.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/analysis_window.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/auto_writer_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/auto_writer_review_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/character_dialog.py` | Retained: staged form adapter and untouched-field restoration. Form notation parsing differs intentionally from portable YAML and AI validation. |
| `app/ui/character_relationship_dialog.py` | Retained: local staged relationship form; cancel does not mutate source. Trust input diagnostics remain presentation-owned. |
| `app/ui/completion_context_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/completion_notes_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/conflict_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/editor_widget.py` | Changed: confirmed unused Qt imports removed. UTF-16 cursors, ghost paint, spelling validation and undo groups retained with editor tests. |
| `app/ui/export_preview_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/find_replace.py` | Retained: Qt text matching, batched counting, no-match cursor preservation and undo grouping belong to widget adapter. |
| `app/ui/font_utils.py` | Retained: cached installed-font lookup; platform/font fallback is actual Qt adapter behavior, not duplicated domain policy. |
| `app/ui/generated_text_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/main_window.py` | Changed: worker/domain operations extracted, static call APIs retained, activity callbacks named. Separate tab-goal lifecycle fix documented below. Remaining methods coordinate widgets, captures, guards and signals. |
| `app/ui/markdown_preview.py` | Retained: bounded offline Qt rendering and generation checks; resource loading stays disabled. |
| `app/ui/navigation_history.py` | Retained: bounded weak-reference session navigation; restore callback owns stale identity checks. |
| `app/ui/pdf_options_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/portrait.py` | Retained: bounded QImageReader decoding; portable byte validation stays in project/portrait.py. |
| `app/ui/project_brief_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/project_search_panel.py` | Retained: keyboard controls and result presentation; filesystem search remains a worker service. |
| `app/ui/project_setup_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/project_translation_review_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/project_view.py` | Retained: tree construction, stable-ID expansion/selection and context-menu presentation; project mutations stay outside the view. |
| `app/ui/quick_open_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/revision_history_dialog.py` | Retained: translated, paged comparison presentation; domain comparisons now live outside the store UI. Avoid generic label formatter that loses Qt extraction context. |
| `app/ui/settings_dialog.py` | Retained: staged settings controls and commit validation; persistence/default normalization stays in AppSettings. |
| `app/ui/spellcheck_review_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/tab_widget.py` | Changed: unused Path import removed; signal order and deferred widget deletion retained. |
| `app/ui/workers.py` | Retained: signal delivery, cooperative cancellation and terminal done cleanup; deleted-signal RuntimeError exceptions remain narrowly recognized. |
| `app/ui/writing_goal_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |
| `app/ui/writing_goal_history_dialog.py` | Retained: focused Qt dialog/view with staged or read-only state, local translation context and explicit accept/reject; keep view-specific keyboard and consent policies. |

## Tests and supporting Python inventory

Test bodies were structurally reviewed for assertions/expected failures, fixtures,
fake I/O/providers, waits and skip gates; high-risk source changes were traced to
the relevant tests. Existing large integration files keep their shared workflow
fixtures; only pure export/recovery cases were moved out of the UI module. No
blanket test splitting or duplicated fixture framework was introduced. Test counts
below are function definitions before parametrization, not pytest case totals.
Native QTest waits remain only in focus/debounce tests; worker tests use signals,
events and bounded polling. Live-network tests are explicit opt-in.

| File | Test functions / disposition |
| --- | --- |
| `tests/language_corpus.py` | Regression corpus data; retained. |
| `tests/test_ai.py` | 13; retained focused behavior/failure coverage. |
| `tests/test_ai_activity.py` | 7; retained focused behavior/failure coverage. |
| `tests/test_ai_workflows_e2e.py` | 42; retained focused behavior/failure coverage. |
| `tests/test_book_compiler.py` | 13; retained focused behavior/failure coverage. |
| `tests/test_character_development.py` | 3; retained focused behavior/failure coverage. |
| `tests/test_character_portrait.py` | 4; retained focused behavior/failure coverage. |
| `tests/test_character_profile_ai.py` | 3; retained focused behavior/failure coverage. |
| `tests/test_completion_context_dialog.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_completion_service.py` | 6; retained focused behavior/failure coverage. |
| `tests/test_continuity.py` | 3; retained focused behavior/failure coverage. |
| `tests/test_dialog_focus.py` | 2; retained focused behavior/failure coverage. |
| `tests/test_document.py` | 27; retained focused behavior/failure coverage. |
| `tests/test_editor_widget.py` | 67; retained focused behavior/failure coverage. |
| `tests/test_export.py` | 10; retained focused behavior/failure coverage. |
| `tests/test_find_replace.py` | 13; retained focused behavior/failure coverage. |
| `tests/test_i18n.py` | 18; retained focused behavior/failure coverage. |
| `tests/test_live_ollama_e2e.py` | 1; two parametrized live cases intentionally skipped offline. |
| `tests/test_logging_config.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_main.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_markdown_preview.py` | 3; retained focused behavior/failure coverage. |
| `tests/test_merge.py` | 6; retained focused behavior/failure coverage. |
| `tests/test_navigation_history.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_negative_scenarios.py` | 3; retained focused behavior/failure coverage. |
| `tests/test_ollama_client.py` | 13; retained focused behavior/failure coverage. |
| `tests/test_project_domain.py` | 43; retained focused behavior/failure coverage. |
| `tests/test_project_search.py` | 14; retained focused behavior/failure coverage. |
| `tests/test_project_setup.py` | 31; retained focused behavior/failure coverage. |
| `tests/test_project_translation.py` | 7; retained focused behavior/failure coverage. |
| `tests/test_project_translation_review_dialog.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_project_ui.py` | 152; retained focused behavior/failure coverage. |
| `tests/test_project_workers.py` | 3; moved pure export/recovery behavior here, no Qt application required. |
| `tests/test_prompts.py` | 8; retained focused behavior/failure coverage. |
| `tests/test_recovery.py` | 29; retained focused behavior/failure coverage. |
| `tests/test_review_accessibility.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_revisions.py` | 29; retained focused behavior/failure coverage. |
| `tests/test_settings.py` | 17; retained focused behavior/failure coverage. |
| `tests/test_spellcheck_service.py` | 5; retained focused behavior/failure coverage. |
| `tests/test_text_formatting.py` | 7; retained focused behavior/failure coverage. |
| `tests/test_translation_validation.py` | 11; retained focused behavior/failure coverage. |
| `tests/test_ui_string_audit.py` | 4; retained focused behavior/failure coverage. |
| `tests/test_writing_goal_benchmark.py` | 1; retained focused behavior/failure coverage. |
| `tests/test_writing_goals.py` | 33; retained focused behavior/failure coverage. |

| Tool / benchmark | Review disposition |
| --- | --- |
| `tools/audit_ui_strings.py` | Report likely unmarked UI literals for a human localization audit. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `tools/check_translations.py` | Validate Qt TS translations and optionally compare with an extracted catalog. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `benchmarks/completion_context.py` | Compare bounded completion context construction with the previous approach. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `benchmarks/editor_responsiveness.py` | Measure representative editor operations on the Qt GUI thread, offline. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `benchmarks/language_detection.py` | Evaluate the regression corpus against an always-Auto baseline, offline. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `benchmarks/project_search_responsiveness.py` | Measure project-search GUI latency offline with synthetic project files. Standalone bounded entry point retained; exercised by focused tests or smoke run. |
| `benchmarks/writing_goal_history.py` | Measure writing-goal history during separate Qt editing commands. Standalone bounded entry point retained; exercised by focused tests or smoke run. |

Inventory: 135 Python files: 85 app, 43 tests, 2 tools, 5 benchmarks.
