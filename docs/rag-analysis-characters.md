# Reviewed retrieval for analysis and character workflows

**RAG-10: COMPLETE. RAG-10.V1: COMPLETE.**

The offline gate covers summary, continuity, empty-profile
suggestions and scene-based character development. Broader RAG work remains open.

## Author controls and preconditions

AI > Review retrieved context for scene analysis is a default-off session toggle.
A separate default-off checkbox in each character profile controls its two AI
operations. Ordinary workflows retain their existing inputs. Summary results
now explicitly identify scene-only excerpts or contextual scope.

Project/profile/selected-scene preconditions remain unchanged. A positive explicit
Ollama token window is required when retrieval is enabled. Generation uses the
configured destination, existing workers and AI diagnostics. No embeddings,
network index maintenance, model downloads or canonical source writes are added.

Every retrieved request uses the shared exact role/prompt, source, budget and
coverage review. Optional scenes/notes can be excluded; rebuilding is required
before Send. Required sources cannot be excluded. Missing/unavailable indexes
and no hits remain visible in the manifest and preserve mandatory input only.

## Required context and evidence

Analysis keeps the complete selected scene and selected notes, plus explicitly
associated profiles, mandatory before optional allocation. Both the existing
analysis character guard and the complete-request token budget may refuse the
request; retrieved summaries never silently shorten selected text. Associated
profile helper limits also refuse rather than silently omit evidence. Full
textual associated profiles are additionally recorded as required sources.

Empty-field suggestions keep the staged profile and every project note in full,
including unsaved note buffers. The existing 64 KiB complete-note guard, response
language resolution, JSON validation, five-minute timeout and empty-field-only
application rules remain. Required notes are protected in source review.

Development keeps the staged profile and explicitly selected associated scene
excerpt mandatory. Its existing excerpt limit is retained. The whole saved scene
is not substituted as arc evidence: each proposed arc change must quote the exact
selected excerpt, even when background or later text contains a convincing quote.

Optional scene retrieval is restricted to earlier manuscript order for anchored
analysis/development. This is not story chronology. Profile suggestions have no
scene anchor and may retrieve across the manuscript. Reference notes/global
profiles may contain later facts. The role and review explicitly explain these
boundaries; retrieved mentions establish neither physical presence nor knowledge.
Only explicit associations authorize character IDs in continuity findings.

Continuity accepts exact source IDs and nonempty quotations from selected inputs
or actually sent retrieved spans. Required character-source quotations are also
available. Excluded, future, invented, omitted and out-of-span citations fail
validation. Disjoint passages stay separate: a quote cannot cross an omitted gap.
Output is a partial review, never a whole-project audit or consistency guarantee.
Semantic truth, narrative chronology and the quality of the model's inference
remain matters for author review; exact quote matching cannot prove them.

## Snapshot, cancellation and staged application

`app/project/analysis_context.py` owns capture, budget, review decisions, immutable
request evidence, citation spans and source verification. AI services retain
response validation; `app/ui/analysis_retrieval.py` captures Qt buffers and reuses
the queued review bridge. Ollama payloads remain in its provider implementation.

All open project scene/note revisions are captured on the GUI thread and overlaid
without cache writes. Closed sources and manifest/associations are verified before
and after generation. Required text is compared against the later source capture
to reject a task-read/capture race. Source exclusions rebuild a new reviewed
request; no silent smaller retry exists.

Existing GUI guards retain project/settings/request generations, selected scene,
profile fields and open-buffer revisions. Additional source buffers are checked,
not just the selected target. A superseded development request cannot stage values
or reset a newer request's controls. Provider calls and file verification stay in
workers; review and staged updates return through queued Qt signals.

Analysis only displays a separate result panel. Character values require the
existing final proposal review, followed by worker source verification and a fresh
GUI guard before staging. Development checkboxes start unchecked. Reject, cancel,
stale success/error and changed files cannot stage proposals; profile Save remains
separate. Manuscripts and Undo are preserved. Fingerprint verification is not an
atomic lock against an arbitrary writer between verification and form staging.

## Offline criterion matrix

| Criterion | Tests/evidence |
| --- | --- |
| Mandatory allocation and refusal | Full scene/note/profile decisions; required source exclusion; character/token overflow refuses before dispatch |
| Exact reviewed request | All four UI workflows compare displayed prompt to provider prompt; provider thread differs from GUI; full-context option retained |
| Missing index/no hits | Explicit unavailable/no-hit manifest; required context retained; no whole-project audit claim |
| Citation validation | Included earlier-scene citation accepted; future, invented, excluded, unassociated and cross-gap citations rejected |
| Presence/knowledge/chronology | Role boundaries and earlier-scene filtering verified; explicit associations still restrict character IDs |
| Full notes | >10,000-character unsaved note tail retained; buffer revision 9; timeout/JSON mode retained; index bytes unchanged |
| Arc evidence | Selected excerpt accepted; retrieved-only quote rejected despite being sent as background |
| Stale sources | Changes in review, generation and final proposal review; task-read/capture race rejects old input |
| Stale GUI | Profile/buffer/settings/project/selection edits, rejected source review, and late success/error cannot apply |
| Explicit staging | Final rejection keeps form empty; accepted individual proposals stage after verification and leave saved profile unchanged |

Final verification on macOS with Qt offscreen:

- Full suite: **1656 passed, 7 expected native/live skips, 369.72s**.
  `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -xq`
  Log: `/private/tmp/utexteditor-rag10-final-full.log`.
- Final wider focused suite: **424 passed, 1 name-filter deselection, 64.64s**.
  Same environment, `pytest -xq tests/test_analysis_retrieval.py tests/test_analysis_retrieval_ui.py tests/test_project_analysis.py tests/test_character_development.py tests/test_character_profile_ai.py tests/test_i18n.py tests/test_project_ui.py -k 'not native'`.
  The deselected shortcut test also runs in the full offscreen suite; no native
  gate is inferred from its name. Log: `/private/tmp/utexteditor-rag10-final-wide.log`.
- New domain/UI cases: **21 + 32**. Focused analysis/character/i18n run:
  **130 passed in 2.26s**, before the final request-ownership guard; the final wider
  and full runs include that guard.
- Fresh `pyside6-lupdate app/ui/*.py` extraction: **1113** source messages.
  `tools/check_translations.py` passed for UK against that extraction and for the
  intentionally partial English catalog. UK QM rebuilt; runtime lookup of all
  three new control/review headings verified in Ukrainian. `git diff --check` passed.

An initial full run exposed an existing file-conflict test's uncontrolled
background spellcheck: its attempted provider call overwrote the save-failure
status. That test now disables unrelated automatic spelling and completion before
editing, so it measures file-conflict feedback without network or timing races.
The final full run above passed after this test isolation and all production
changes were frozen. No application behavior was changed for this test issue.

Native/live checks are not part of RAG-10.V1 and were not run; no model-quality,
native accessibility or measured server allocation claim follows from offline tests.

## Clean Code completion review

- [x] Intent: capture/review/evidence/verification have explicit owners and names.
- [x] Ownership: AI validates responses, project code owns source capture, Qt
  captures widget state and orchestrates workers; no HTTP added outside provider.
- [x] Safety: mandatory data, dirty buffers, staged fields, explicit Save, Undo,
  stable IDs, source conflicts and existing transactions remain protected.
- [x] Errors: cancellation and stale source failures are explicit; late obsolete
  provider failures cannot mutate a form or overwrite its current context.
- [x] Tests: deterministic fake-provider normal/failure regressions, focused
  suites and complete offscreen suite; native/live limitations stated separately.
- [x] Diff: no dependencies, generated source edits or unrelated refactoring;
  behavior docs and Ukrainian TS/QM updated; unrelated staged bytecode preserved.
- [x] Report: lexical-only policy, excerpt versus full-source contracts, partial
  coverage and arbitrary-writer verification limits are documented explicitly.
