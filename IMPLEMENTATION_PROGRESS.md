# Implementation progress

- **TASK-019.01–.05/V1 — verified; path failure fix (2026-11-01):**
  Back/Forward now skips OSError/RuntimeError while verifying a project path.
  Two path-failure regressions and four stale-target cases cover edited,
  closed, removed and relinked destinations, unchanged history during typing,
  retained dirty buffers and unchanged source files. Focused history tests:
  8 passed; full offline suite: 852 passed, 2 skipped. README/TASKS and
  docs/navigation-history-verification.md updated. Diff reviewed and whitespace
  check passed. Existing translated feedback reused; no new controls/strings.
  Parent remains partial for native shortcut/accessibility and release-catalog
  V2 checks. Revision-value comparison committed as `2c2a9c5`. Original staged
  artifacts preserved; no push attempted.

- **TASK-009.04 — captured metadata values (2026-11-01):** verified starting
  HEAD `d6f7d86` and original staged artifacts. Character, directed-relationship
  and scene-association comparisons now provide deterministic Unicode JSON
  diffs for additions/removals/changes through the existing read-only display.
  Missing keys differ from null; source snapshots and live projects are not
  changed. Extended domain/UI regressions plus one new Unicode/immutability
  regression pass: revision module 23 passed; revision/UI suite before the
  extra domain test 181 passed; full offline suite 846 passed, 2 skipped.
  README/TASKS updated; diff reviewed and whitespace check passed. No new UI
  controls or translatable strings; no catalog change required for raw manifest
  data. Native review and remaining structure/restore/scheduling requirements
  stay open; TASK-009.04 and parent remain partial. No push attempted.

- **TASK-018.01–.05/V1 — VERIFIED (2026-11-01):** reviewed Project/AI
  grouping, retained handler/shortcut table, disabled-action explanations and
  existing shared navigation. docs/menu-organization-verification.md records
  evidence and the decision to retain submenus without adding a command picker.
  Focused menu tests: 4 passed, 220 deselected; full offline suite on unchanged
  code: 845 passed, 2 skipped. README already accurate; no product/translation
  changes or redundant tests. Diff reviewed; whitespace check passed. All
  numbered tickets/V1 verified; parent remains partial for required manual
  accessibility/native shortcut review and release-catalog V2 checks.
  Recent-file fix/audit committed as `a6729b6`. No push attempted.

- **Latest continuation checkpoint (2026-11-01):** implementation is tested
  with 845 passed / 2 skipped; original staged `.DS_Store` and bytecode are
  preserved and excluded from every scoped commit. Subsequent navigation
  audits after the earlier checkpoint: Quick Open `5f8f797`, related-item
  navigation `e8776d8`, tab navigation `ab51d1f`, and recent files `a6729b6`.
  TASK-012, TASK-013, TASK-015, TASK-017 and TASK-018 numbered tickets are
  verified, but their parents retain V2 native/catalog requirements. TASK-016
  .05 is still partial. No native accessibility or cross-platform filesystem
  verification has been claimed. No generated release catalogs were changed.
  The overall backlog is still incomplete: earliest open work remains
  TASK-001's reachable-history bound/active-identity collision/stress gate;
  TASK-005/.007's independent-writer race; broader TASK-008 diagnosis;
  TASK-009 restore/safety snapshots/comparison/scheduling; TASK-010 backup;
  and TASK-011 encoding/line-ending/large-file safety. TASK-019 and later
  inherited UI tickets still need acceptance reconciliation or implementation
  as appropriate. Continue from these gaps, preserving completed evidence;
  do not truncate Qt undo, weaken conflict checks or promote native gates on
  offscreen tests. No requested implementation has been declared globally
  complete, and no push has been attempted.

- **TASK-017.01–.05/V1 — VERIFIED; path failure fix (2026-11-01):**
  reviewed separate ten-path settings list, common open worker/reuse, missing
  feedback, clear persistence and paths-only records. Initial/completed open
  handlers now catch path-resolution errors while checking duplicates instead
  of allowing exceptions to escape Qt callbacks. Four regressions cover
  OSError/RuntimeError for requested/existing paths at both stages, preserving
  dirty tabs and both source files. Focused recent-file/settings tests:
  7 passed, 169 deselected; full offline suite: 845 passed, 2 skipped.
  README/TASKS and docs/recent-files-verification.md updated; existing Open
  failed translations reused. Diff reviewed; whitespace check passed. All
  numbered tickets/V1 complete; parent remains partial for V2 release catalog
  and native checks. Tab audit committed as `ab51d1f`. No push attempted;
  unrelated staged artifacts preserved.

- **TASK-016.01–.04/V1 — VERIFIED (2026-11-01):** reviewed QTabWidget
  built-in navigation, shared searchable picker, modified/path/project labels,
  editor identity selection and delegated closing. Evidence is in
  docs/tab-navigation-verification.md. Focused Qt tests: 3 passed,
  217 deselected; preceding shared Quick Open tests: 6 passed; last full suite
  on unchanged code: 841 passed, 2 skipped. No behavior/strings changed;
  README already accurate. Diff reviewed; whitespace check passed. No redundant
  tests added. .05/V2 and parent remain partial: offscreen Ctrl+Tab tests are
  not native OS/accessibility verification. Related-navigation audit committed
  as `e8776d8`. No push attempted; staged artifacts preserved.

- **TASK-015.01–.05/V1 — VERIFIED (2026-11-01):** traced directed links,
  explicit scene associations, separate mention search, profile hide/return,
  and staged-save guards for character/relationship changes and write failures.
  docs/related-navigation-verification.md maps acceptance to named tests.
  Focused Qt tests: 8 passed, 147 deselected; full suite on unchanged code:
  841 passed, 2 skipped. No behavior/strings changed; existing README remains
  accurate. Documentation diff reviewed; whitespace check passed. No redundant
  tests added. Numbered tickets/V1 complete; parent remains partial for V2
  release-catalog/native checks. Quick Open audit committed as `5f8f797`.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-013.01–.05/V1 — VERIFIED (2026-11-01):** inspected Ctrl+P action,
  immutable item capture, casefold filtering, type/chapter/ID labels, aliases,
  stale project guard and shared document-opening path. Added named acceptance
  evidence to docs/quick-open-verification.md. Focused Quick Open Qt tests:
  6 passed, 149 deselected; full suite on unchanged implementation: 841 passed,
  2 skipped. No new behavior/strings; existing README is accurate. Diff reviewed
  and whitespace check passed; no redundant tests added for this audit.
  Numbered tickets/V1 complete; parent remains partial for V2 release catalog
  and native keyboard/screen-reader verification. Performance audit/checkpoint
  committed as `3332f66`. No push attempted; staged artifacts preserved.

- **TASK-006.V1 / V2 — DONE (2026-11-01 audit):** mapped numbered tickets
  and parent criteria to benchmark scripts, named correctness tests, measured
  evidence and native limitations in docs/gui-latency-evaluation.md. .01/.02
  remain complete; .03/.04/.05 and parent remain partial. Re-ran reproducible
  completion-context baseline: prior/current 0.0581/0.0002 seconds per 100
  calls, 2,504,082/4,041 peak traced bytes, with equal sample output. This is
  a microbenchmark, not overall application speed. Latest full offline suite
  on unchanged implementation: 841 passed, 2 skipped; earlier focused editor/
  goal suite: 96 passed. Documentation diff reviewed; whitespace check passed.
  UI/catalog checks N/A: no new controls or Qt strings. Native performance
  remains .03/.04, not waived. Search-budget checkpoint is `f805da5`.

- **Resume checkpoint (2026-11-01):** this run verified starting commit
  `39ae121`, then committed Qt-history pruning (`9ce6082`), callback-latency
  tooling (`9337b37`), save audit (`5dca14c`), recovery statuses (`1501132`),
  revision comparison chronology (`62a2553`), search safety/audit (`e8031f9`)
  and aggregate search capture bounds (`f805da5`). Current implementation has
  841 passing offline tests, 2 skipped live tests; Ukrainian source validation
  and temporary-catalog runtime/extraction checks pass. No push requested or
  attempted. Initial staged `.DS_Store` and bytecode changes remain untouched.
  The entire TASKS.md backlog is NOT complete. Earliest remaining work is
  TASK-001.02/.03/.05 (bound reachable metadata without truncating Qt undo,
  preserve actively tracked identity collisions, then stress validation).
  TASK-005/.007 still share the independent-writer final-check overwrite race;
  no broader guarantee may be claimed. Further feasible work includes broader
  TASK-008 diagnosis, TASK-009 selective/safety restore and richer metadata
  comparison/scheduling, TASK-010 backup, TASK-011 encoding/line-ending/large-
  file safety, and the remaining UI verification queue. Native screen-reader,
  filesystem and release-catalog checks remain explicitly open. TASK-012's
  numbered tickets are verified; its parent still awaits V2. Do not redo the
  completed investigations/benchmarks merely because their parents are partial.

- **TASK-012.06 — DONE within documented bounds (2026-11-01):** capped
  total open-buffer copies at 8 Mi UTF-16 units using Qt counts before copying.
  Omitted buffers carry a translated reason and never fall back to stale disk
  text. The service also rejects certainly oversized text before encoding it.
  Five new regressions cover descriptor/buffer allocation rejection, omission,
  exact budget boundaries for ASCII/emoji, preserved source files and unsaved
  buffers, and continuing other matches. Focused search/project UI/localization
  suites: 199 passed; full offline suite: 841 passed, 2 skipped. Ukrainian
  source validation passed; diff reviewed and whitespace check passed.
  README/TASKS/search verification updated. All numbered TASK-012 tickets
  verified; parent remains partial pending release-catalog/native V2 checks.
  Captured text is bounded, not total process memory: descriptor metadata scales
  with tabs/project size, capture remains synchronous and blocked regular-file
  reads are not interruptible. Earlier tabs can consume the allowance first;
  omissions are explicit. Prior search checkpoint committed as `e8031f9`.
  Ready for scoped budget commit. TASK-006 acceptance reconciliation text is
  drafted separately in docs/gui-latency-evaluation.md for the next checkpoint.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-012.01–.05/.07/V1 — VERIFIED; file-read fixes (2026-11-01):**
  traced service, dock, captured unsaved buffers and generation/digest-checked
  navigation. docs/project-search-verification.md maps acceptance to named
  service/UI tests. Search now shares binary-control detection with ordinary
  project reads and uses nonblocking opens plus regular-file verification to
  reject POSIX FIFOs rather than wait for a writer. Seven new regressions
  preserve good companion matches and source contents. Focused search/project
  UI suites: 170 passed; full offline suite: 836 passed, 2 skipped. Diff
  reviewed; whitespace check passed. README/TASKS updated. No controls or Qt
  source strings changed; dynamic errors retain existing localization limits.
  .06 remains partial: total captured open-buffer text is not budgeted and
  regular-filesystem reads are not interruptible. V2 release-catalog/native
  keyboard/screen-reader verification remains open. Revision chronology
  checkpoint committed as `62a2553`; ready for scoped search commit.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-009.01 — comparison chronology fix (2026-11-01):** domain listing
  already orders timezone-aware instants, but the dialog still ordered the
  two selected snapshots lexically. It now parses their validated timestamps
  before ordering, preserving before/after direction across differing offsets.
  Added signal-path regression for 12:00+02:00 versus 11:00Z. Focused revision/
  project UI suites: 175 passed; full offline suite: 829 passed, 2 skipped.
  Diff reviewed; whitespace check passed. README/TASKS updated. No strings or
  controls changed; catalog/native accessibility checks N/A for this ordering
  correction. Restore, richer comparison and scheduling remain open. Recovery
  checkpoint committed as `1501132`; ready for scoped chronology commit.
  No push attempted; unrelated staged artifacts preserved.

- **TASK-008.01 — DONE (2026-11-01):** recovery scans now capture per-snapshot
  canonical-file status in the worker: untitled, missing, appeared, unchanged,
  changed, unknown or unreadable. Chooser details show status and capture time
  using English/Ukrainian source strings. Diagnosis hashes regular files in
  1 MiB chunks; nonblocking POSIX opens avoid waiting on a replaced FIFO.
  Canonical read failures preserve valid snapshots. Eleven regressions cover
  states, permissions, non-regular paths, unknown digests, subsequent disk
  changes and temporary-catalog runtime labels; display uses captured status,
  with an explicit advisory notice and unchanged restore conflict checks.
  Focused recovery/project UI/localization suites: 213 passed; full offline
  suite: 828 passed, 2 skipped. Ukrainian catalog validation passed; diff
  reviewed and whitespace check passed. README/TASKS updated. Release compiled
  assets untouched; native keyboard/screen-reader review remains outstanding.
  Broader corrupt-data diagnosis/repair and parent acceptance remain open.
  Save audit checkpoint committed as `5dca14c`; ready for scoped recovery
  commit. Unrelated staged files preserved; no push attempted.

- **TASK-005.V1 / V2 — DONE (2026-11-01 audit):** reviewed shared RLock,
  standalone/project text and manifest save paths and named failure/concurrency
  tests. Added acceptance matrix to docs/save-coordination.md; .01/.02/.03/.05
  remain verified, .04 and parent remain partial. The green suite deliberately
  reproduces an independent writer's edit being overwritten after the final
  check; it must not be reported as cross-process safety. UI/catalog/native
  accessibility checks N/A: coordination introduces no UI/strings. Native
  filesystem/multi-process verification remains open. Focused document/project
  suite: 79 passed; last full suite on unchanged implementation: 817 passed,
  2 skipped. Documentation diff reviewed; whitespace check passed. No redundant
  tests added. Benchmark checkpoint committed as `9337b37`; ready for scoped
  audit commit. No push attempted; unrelated staged artifacts preserved.

- **TASK-006.03 — PARTIAL (2026-11-01):** added ready Qt callback delay
  probes during idle and typing with new-word tracking. Ten samples at
  100K/1M/5M characters completed, with byte-verified saves; typing callback
  maxima 2.22/3.86/10.62 ms and cumulative peak RSS
  130,023,424/151,977,984/321,372,160 bytes. Reproduction, workload and
  event-loop/native limitations are in docs/gui-latency-evaluation.md.
  Focused editor/goal suites: 96 passed; full offline suite: 817 passed,
  2 skipped. Diff reviewed and whitespace check passed. Direct benchmark
  assertions validate generated output; no hardware-sensitive timing test.
  No product UI/strings changed; native/catalog checks N/A for tooling.
  TASK-006 remains partial for native latency, project workloads and bounds.
  TASK-001.04 checkpoint committed as `9ce6082`; unrelated staged files
  remain preserved. Ready for scoped benchmark commit; no push attempted.

- **TASK-001.04 — DONE (2026-11-01):** verified last checkpoint
  `39ae121` with 32 document tests. Existing staged `.DS_Store` and bytecode
  changes are unrelated and preserved. Qt availability signals now schedule a
  coalesced, deferred pruning check; clearing either or both stacks or disabling
  undo releases only unreachable goal checkpoints even without a text change.
  Closed tabs are ignored. Six offscreen regressions cover both directions,
  preserved text/counts, subsequent edits, undo and redo. Focused goal/editor
  suites: 96 passed; full offline suite: 817 passed, 2 skipped. Diff reviewed;
  whitespace check passed. README/TASKS updated. No new UI strings or native
  UI changes; localization/native checks N/A for this internal lifecycle fix.
  Reachable history remains unbounded (TASK-001.02); identity collisions and
  long-session acceptance remain open. Ready for scoped commit.

- **TASK-005.03 — DONE (2026-10-31):** evaluated process-local locking,
  POSIX advisory locking, cooperative sidecars, Windows byte-range locking,
  repeat fingerprints and atomic replacement. Added subprocess regression
  test_posix_advisory_lock_does_not_exclude_uncooperative_writer: a separate
  interpreter writes successfully while LOCK_EX is held; skips without fcntl.
  docs/save-coordination.md records evidence, primary Python/Microsoft API
  references, the decision not to misrepresent advisory locking as a race fix,
  and native/cross-process follow-up requirements. Focused document suite:
  32 passed; full suite: 811 passed, 2 skipped; diff reviewed and whitespace
  check passed. README/TASKS updated. This completes evaluation only;
  TASK-005.04 and parent independent-writer acceptance remain incomplete.
  No product behavior or UI changed. Changes uncommitted; no push attempted.

- **TASK-011.05 — DONE (2026-10-31):** evaluated 1M/5M/10M-character
  sessions with ten samples per repeated operation, new-word tracking and AI
  disabled. Extended benchmark to time saves and verify exact saved buffer
  bytes. At 10M: GUI open 399.06 ms; typing median/max 17.98/19.08 ms;
  word count median 144.89 ms; save 19.37 ms; cumulative RSS 601,669,632
  bytes. docs/large-file-evaluation.md records all sizes, workload limitations,
  whole-buffer allocation review and follow-up safety requirements. README
  and TASKS updated. Document tests: 31 passed; full suite: 810 passed,
  2 skipped; diff reviewed and whitespace check passed. Evaluation complete;
  no safe maximum or native responsiveness guarantee claimed. Parent remains
  open: size policy/failure safety, encoding and line-ending selectors remain.
  No product change or new UI strings; benchmark save assertions supply direct
  validation without redundant implementation-mirroring tests. Uncommitted.

- **TASK-011.04 — DONE (2026-10-31):** added shared has_binary_controls
  detection for NUL, non-whitespace ASCII controls and DEL. Standalone reads,
  project reads/import/relink/save verification and conflict-version reads use
  it. Tab/LF/CR/vertical-tab/form-feed and Unicode prose/NEL remain allowed.
  Regex search avoids Python per-character scanning. Added five control-input
  cases, Unicode/whitespace acceptance and project read/import preservation
  regression. Focused document/project suites: 78 passed; full suite:
  810 passed, 2 skipped. Diff reviewed and whitespace check passed. README,
  UNIMPLEMENTED_FEATURES and TASKS updated. No new controls or UI strings;
  existing errors handle rejection. This conservative heuristic deliberately
  does not identify every binary format; encoding selection/large-file limits
  remain separate tickets. Changes uncommitted; no push attempted.

- **TASK-011.01 — DONE (2026-10-31):** inspected FileManager, Document,
  line-ending helpers and dependent conflict/recovery/project workflows.
  Added docs/encoding-support.md with standard-library codec experiment,
  ambiguity example, explicit-selection recommendation, BOM/endian policy,
  compatibility boundaries and follow-up acceptance requirements. UTF-8,
  UTF-16, UTF-16-LE, CP1251 and CP1252 synthetic samples round-trip; CP1251
  also decodes incorrectly but successfully as CP1252, ruling out decode
  success as an automatic selection rule. Added five FileManager regressions
  for unsupported opens and unrepresentable saves preserving source bytes,
  dirty text/digest and temporary-file cleanup. Document tests: 25 passed;
  full offline suite: 803 passed, 2 skipped; diff reviewed and whitespace
  check passed. README links design; TASKS updated. No new UI or dependencies.
  This investigation is complete; encoding selection, broader binary detection
  and large-file work remain separate TASK-011 tickets. Uncommitted, no push.

- **TASK-020.05 — DONE; .01–.04/V1 — verified (2026-10-31):** audited
  shared Qt matching flags, batched/stale-safe counting, current-match checks,
  replace-all edit blocks, focus shortcuts and MainWindow refresh connections.
  Added four Unicode case-insensitive replace-all regressions covering whole
  words/substrings, deletion/emoji replacement, counts and undo/redo. Existing
  tests cover navigation, default semantics, zero matches, focus and small
  windows. Focused suite: 21 passed; full offline suite: 798 passed, 2 skipped;
  diff reviewed and whitespace check passed. README already describes verified
  behavior; no product change or new strings. All numbered TASK-020 tickets
  complete. Parent deliberately remains partial: V2 native keyboard/screen-
  reader review and release-catalog verification remain outstanding and cannot
  be established by offscreen tests. No commits or pushes.

- **TASK-031 — COMPLETE (2026-10-31):** reviewed existing NFC normalization,
  script/common-word evidence, minimum alphabetic signal, distinct-word and
  ambiguous-language fallbacks. Existing tests/language_corpus.py has 43 cases:
  6 English, 8 Ukrainian, 29 intentionally Auto, including other languages,
  short/mixed text, decomposed Unicode and repeated/digit-heavy input. Added
  benchmarks/language_detection.py: current 43/43, always-Auto baseline 29/43,
  zero unsupported confident guesses. No algorithm change warranted by these
  cases; this is curated regression behavior, not population accuracy or an
  estimate against a historical detector. Added 86 explicit-override cases
  across both prompt types. Prompt suite: 135 passed; full offline suite:
  794 passed, 2 skipped; diff reviewed and whitespace check passed. README
  documents evaluation; all TASK-031 subtasks and acceptance checks reconciled.
  Native/catalog checks N/A: no UI behavior or strings changed. Uncommitted;
  no push attempted.

- **TASK-033 — COMPLETE (2026-10-31):** acceptance audit verified checker
  completeness, Qt/named/indexed placeholder parity, malformed/duplicate/empty
  and plural errors, extracted source coverage, CLI nonzero exit/reporting,
  compiled runtime lookup, README instructions and CI integration. Added three
  CLI regressions for unfinished translations, invalid root and missing context.
  Localization suite: 14 passed. Extracted coverage: 897 strings, passed.
  Temporary catalog compilation: English 28 and Ukrainian 903 finished entries,
  none unfinished; generated repository assets untouched. Full offline suite:
  708 passed, 2 skipped. Diff reviewed and whitespace check passed. All
  TASK-033 numbered tickets and V1/V2 reconciled; native UI checks N/A because
  this task changes tooling only. First hosted CI run remains unobserved;
  complete interface translation/native review remain TASK-032/TASK-034.
  Changes uncommitted; no push attempted.

- **TASK-033.04 — DONE (2026-10-31):** added
  .github/workflows/localization.yml for push, pull request and manual runs
  with read-only repository permissions, Python 3.12 and offscreen Qt. It
  installs project test tools and Linux Qt runtime libraries, validates the
  Ukrainian catalog, explicitly extracts/checks all marked UI sources, and
  runs existing localization regressions. Local extraction: 897 marked strings,
  coverage validation passed; localization suite: 11 passed; full offline
  suite: 705 passed, 2 skipped; diff reviewed and whitespace check passed.
  README/TASKS updated. Existing tests exercise malformed/missing translations,
  placeholders, plurals, compiled lookup and source coverage; no redundant
  workflow-mirroring unit test added. First hosted Ubuntu/Python 3.12 run
  remains unobserved until commit/push; no commits or pushes made. This
  completes workflow integration, not all localization/native acceptance.

- **TASK-009.01 — preview labels (2026-10-31):** revision snapshots expose
  captured document titles through the domain model; note previews now use
  captured titles alongside stable IDs. Legacy documents without title
  metadata fall back to IDs. Added Qt regression covering duplicate titles,
  distinct note identities and legacy metadata. Focused revision/UI suites:
  173 passed; full offline suite: 705 passed, 2 skipped; diff reviewed and
  whitespace check passed. README/TASKS updated; no new translated strings.
  Native verification and revision restore/scheduling remain open. Previous
  ordering comparison committed as e1bfe84; new work uncommitted.

- **TASK-009.04 — PARTIAL (2026-10-31):** revision comparison reports
  reference-note reordering among IDs present in both snapshots. Additions
  and removals do not generate false moves. Moved-item labels expose stable
  IDs, including duplicate titles, using existing translated strings. Added
  domain and Qt regressions. Focused revision/UI suites: 172 passed; full
  offline suite: 704 passed, 2 skipped; Ukrainian catalog validation and
  diff check passed. README/TASKS updated and diff reviewed. Broader metadata
  before/after values, restore/scheduling and native verification remain open.
  Previous listing fix committed as c655e9a; new changes uncommitted.

- **TASK-009.01 — listing/preview hardening (2026-10-31):** revision
  enumeration uses explicit directory listing so filesystem errors become
  diagnostics rather than an apparently empty history. Revision reads reject
  symbolic links, preserving valid companion entries and linked/external files.
  Added focused listing-failure and symlink regressions. Revision tests:
  21 passed; full offline suite: 702 passed, 2 skipped; diff reviewed and
  whitespace check passed. README/TASKS updated. This pre-read symlink check
  does not exclude concurrent path replacement. Native verification and
  broader revision restore/scheduling remain open. Prior chronology change
  committed as 67f8152; new work remains uncommitted.

- **TASK-009.01 — chronology hardening (2026-10-31):** revision reads
  validate timezone-aware capture timestamps and listing sorts by instant
  rather than timestamp text. Regression tests cover invalid and timezone-free
  timestamps (with valid integrity digests), preservation of invalid files and
  valid companion snapshots, plus differing timezone offsets. Revision suite:
  19 passed; full offline suite: 700 passed, 2 skipped; diff reviewed and
  whitespace check passed. README/TASKS updated. No new UI controls or strings;
  existing diagnostics show validation errors. Restore/scheduling and native
  verification remain open. Previous benchmark committed as b7aa90f; this
  change remains uncommitted.

- **TASK-006.01/.02 — DONE; .03/.04 — PARTIAL (2026-10-31):** editor
  benchmark accepts --sizes and --repetitions, reports median/max per repeated
  operation and handles missing Unix resource support. Ten samples at
  100,000/1,000,000 characters: typing median 2.13/3.56 ms (max 2.22/3.63),
  cursor median 0.48/0.48 ms, word count median 1.38/14.27 ms, context
  median 0.06/0.62 ms. Single GUI opens 4.39/29.78 ms; cumulative peak RSS
  129,794,048/151,715,840 bytes. Offline synthetic measurements on this
  machine; no portable threshold or native event-loop guarantee. Read/open
  remain single samples; Windows fallback is implemented but not natively
  verified. Benchmark run and full suite passed: 697 passed, 2 skipped;
  diff check passed. README/TASKS updated. Prior refresh change committed
  as f6e38f4; benchmark changes uncommitted.

- **TASK-006.05 — PARTIAL (2026-10-31):** goal status refresh no longer
  recounts active/open scene buffers for new-word goals or paused/disabled
  goals. Other scopes count only their required buffers. Three regressions
  reject unnecessary count_words calls and verify label state. Editor suite:
  59 passed; full suite: 697 passed, 2 skipped; after removing a redundant
  action-label update, goal UI regressions: 16 passed. README/TASKS updated,
  diff reviewed and whitespace check passed. Project membership traversal and
  required scope counts remain synchronous; no overall latency bound claimed.
  Previous token-scan optimization committed as 93b157f; new work uncommitted.

- **TASK-006.05 — PARTIAL (2026-10-31):** writing-goal token scanning
  now visits the changed span plus two surrounding characters, preserving
  internal apostrophe/dash boundaries. Added exhaustive small-edit comparison
  against the prior whole-document token scan over Unicode and punctuation
  examples. Goal tests: 31 passed; full suite: 694 passed, 2 skipped;
  diff reviewed and whitespace check passed. Microbenchmark on one million
  characters: 100 complete bounded credit calculations 0.0079 seconds versus
  2.1373 seconds for 100 whole-document token scans (different workloads;
  this isolates scan cost and is not GUI latency). README/TASKS updated.
  Long run completed: 10,000 commands retained 10,001 states and
  3,723,520 current traced bytes; insertion phase took 142.514 seconds versus
  the previous single run of 156.520 seconds. Counts 10,000 → 9,000 → 10,000
  and branch 9,001 passed. These single runs do not establish a stable GUI
  speedup. Memory remains unbounded and other GUI counting work
  still scans whole buffers. Prior benchmark committed as 981deb7; new work
  uncommitted.

- **TASK-001.05 — PARTIAL (2026-10-31 checkpoint):** configurable
  --commands/--undo history benchmark now checks a branch edit after undo
  as well as redo. Smoke run (100 commands/10 undo) passed: 101 states,
  58,624 current Python-traced bytes; counts 100 → 90 → 100, branch 91
  words/92 states. Focused goal/editor tests: 86 passed; full suite:
  693 passed, 2 skipped; diff check passed. README/TASKS updated.
  Long run completed: 1,001/5,001/10,001 states and
  422,181/1,898,691/3,723,574 current Python-traced bytes at
  1,000/5,000/10,000 commands (3.465/45.127/156.520 seconds).
  Counts 10,000 → 9,000 → 10,000; branch 9,001 words/9,002 states.
  This is synthetic and excludes native Qt allocations; no fixed bound
  is established. Prior accounting fix committed as 7663cc4; benchmark work
  remains uncommitted.

- **TASK-001.03 — PARTIAL (2026-10-31):** Save As to an identity with
  persisted progress now preserves source checkpoints when that destination
  is not actively tracked. Each checkpoint retains the larger daily count
  from source/destination, matching existing rekey semantics without allowing
  undo to erase prior destination contributions. Shared count snapshots remain
  shared during transfer. Added regression for undo/redo above and below the
  destination floor; updated existing larger-destination test. Goal tests:
  30 passed; full offline suite: 693 passed, 2 skipped; diff check passed.
  README/TASKS updated. Active destination collisions and bounded metadata
  remain open. Previous checkpoint committed as 59eebb6; new work uncommitted.

- **TASK-001.03 — PARTIAL (2026-10-31 resumed checkpoint):** verified the
  uncommitted identity-transfer change and continued with goal scope/enable
  transitions. Configuration no longer reattaches histories; inactive edits
  retain checkpoints but receive no new-word credit. Added three Qt regressions
  for disabling, active-scene scope and project scope, with edits and undo/redo
  across reconfiguration. Focused goal/editor suites: 85 passed; full offline
  suite: 692 passed, 2 skipped. README/TASKS updated and diff reviewed;
  whitespace check passed. Transient metadata is still unbounded, including
  inactive edits retained for undo correctness. Existing-destination identity
  collisions still reattach. No commits or pushes; unrelated generated-file
  worktree changes preserved. Next: address bounded metadata design and
  existing-destination accounting before marking TASK-001 complete.

- **TASK-001.03 — PARTIAL (2026-10-31):** rekeying a writing-goal document
  to an unused identity now transfers undo/redo checkpoints when text matches;
  rekeying to the same identity also preserves matching history. Regression
  tests cover daily counts over two dates through undo/redo, existing destination
  progress, and mismatched text. Existing destinations retain conservative
  reattachment rather than importing incompatible checkpoints. Writing-goal
  suite: 29 passed; full offline suite: 689 passed, 2 skipped; diff check passed.
  README/TASKS updated. Scope/enable transitions and bounded history remain
  outstanding. Changes are uncommitted; no push attempted.

- **TASK-008.03 — PARTIAL (2026-10-31):** recovery inspection now includes
  captured text for untitled snapshots and snapshots without a canonical file,
  using existing localized labels and the existing UI truncation notice.
  Updated localized comparison assertions and added
  test_recovery_inspection_includes_text_without_canonical_file (two cases).
  Focused recovery/domain/UI tests: 42 passed; full suite: 685 passed, 2 skipped.
  README and TASKS updated; diff check passed. No new UI strings. Pagination,
  damaged-content extraction and native verification remain open. Prior path
  validation fix committed as 6afc551; no push requested this turn.

- **TASK-008.03 — PARTIAL (2026-10-31):** empty and NUL-containing
  canonical/project paths in recovery snapshots now produce invalid-entry
  diagnostics. Automatic retention and cleanup preserve these damaged entries.
  Added test_invalid_recovery_paths_are_diagnosed_and_preserved with four
  path/field cases and a valid companion snapshot. Recovery tests: 27 passed;
  full offline suite: 683 passed, 2 skipped; diff check passed. README and
  TASKS updated. Damaged-content extraction and native checks remain open.
  Prior comparison notice committed as 2995d88; no push requested this turn.

- **TASK-008.03 — PARTIAL (2026-10-31):** recovery comparisons now label
  the existing 6,000-character per-entry truncation, with Ukrainian translation.
  Added test_recovery_comparison_labels_truncated_diff_without_changing_snapshot
  covering long and short comparisons and preservation of snapshot/source text.
  Focused recovery UI tests: 13 passed; full suite: 679 passed, 2 skipped.
  Ukrainian catalog validation and diff check passed. README/TASKS updated.
  Full comparison pagination, release catalog compilation and native checks
  remain outstanding. Prior fix committed as b75a4c4; push failed because
  GitHub HTTPS credentials are unavailable.

- **TASK-008.03 — PARTIAL (2026-10-31):** document-directory resolution
  errors now produce diagnostics without hiding other readable snapshots.
  Regression test_directory_resolution_failure_does_not_hide_valid_snapshots
  covers OSError and RuntimeError (including path-resolution loop failures).
  Recovery suite: 23 passed; full offline suite: 678 passed, 2 skipped.
  README and task notes updated; diff check passed. Broader diagnosis and
  native checks remain open. Previous symlink fix committed as f489b96;
  push failed because GitHub HTTPS credentials are unavailable.

- **TASK-008.03 — PARTIAL (2026-10-31):** symbolic-link snapshot files
  are now reported as invalid instead of being read as recovery entries.
  The shared validation also preserves them during retention and automatic
  saved-document cleanup. A regression verifies that explicit discard removes
  the link while leaving its external target intact. Recovery suite: 21 passed;
  full offline suite: 676 passed, 2 skipped; diff check passed. README and
  TASKS updated. This is a pre-read check, not protection against concurrent
  symlink replacement; native platform checks remain outstanding. Previous
  root diagnostic fix committed as feaed34; push failed due to unavailable
  GitHub HTTPS credentials.

- **TASK-008.03 — PARTIAL (2026-10-31):** failure to enumerate the recovery
  root now returns a root-level diagnostic instead of aborting the scan.
  Added test_unreadable_recovery_root_is_reported_without_deleting_data.
  Focused recovery suite: 20 passed; full offline suite: 675 passed, 2 skipped.
  README and TASKS updated; diff check passed. Broader recovery diagnosis and
  native verification remain outstanding. Previous directory scan fix committed
  as aaae439; push to origin/main failed because GitHub HTTPS credentials are
  unavailable.

- **TASK-008.03 — PARTIAL (2026-10-31):** recovery scanning reports a
  directory-listing failure and continues with other snapshot directories.
  Uses explicit directory enumeration because glob can suppress filesystem
  errors. Added test_unreadable_directory_does_not_hide_other_recovery_snapshots;
  recovery tests: 19 passed; full offline suite: 674 passed, 2 skipped.
  README and TASKS updated; diff whitespace check passed. Existing UI displays
  the diagnostic through its translated wrapper; OS error text remains as
  supplied by the filesystem. Broader diagnosis/native checks remain open.
  Prior conflict-resolution audit committed as b337586.

- **TASK-007.V1 — DONE (2026-10-31 audit):** reviewed FileManager.save,
  MainWindow.review_external_changes and merge_text. TASK-007.01–.04 are
  verified by test_conflict_dialog_displays_versions_and_proposal,
  test_conflict_review_stages_merge_and_rechecks_disk_on_save,
  test_conflict_review_cancel_reload_and_stale_buffer,
  test_conflict_review_save_elsewhere_or_reject_unresolved_markers and
  test_conflict_review_rejects_disk_change_during_review. Focused merge,
  document and project UI suites: 172 passed. No runtime changes in this audit;
  previous full suite: 673 passed, 2 skipped. TASK-007.05 remains partial:
  disk checks precede replacement but cannot exclude independent writers.
  Native keyboard/accessibility checks on supported platforms and release
  catalog compilation remain open. TASKS.md reconciled; no duplicate feature
  implementation. Manifest coordination committed as 5760925.

- **TASK-005.04 — PARTIAL (2026-10-31):** project manifest writes now use
  the shared document write lock. The lock is reentrant so bulk workflows
  can persist manifests while already holding it. Added
  `test_manifest_and_standalone_saves_coordinate_in_process`; focused document
  and project tests: 66 passed; full offline suite: 673 passed, 2 skipped.
  README updated; diff whitespace check passed. Independent-process races
  and native platform verification remain unresolved. No commits or pushes.

## Atomic-plan audit and recovery preservation (2026-10-31)

- **TASK-001.03 — PARTIAL:** changing the target of an active new-words goal
  no longer reattaches the tracker or discards undo checkpoints. Modified
  `app/ui/main_window.py`, `tests/test_editor_widget.py`, and `README.md`.
  Focused tests: 78 passed; full offline suite: 672 passed, 2 skipped.
  Scope changes and disabling/re-enabling tracking still reattach and can lose
  earlier checkpoints; bounded undo metadata remains outstanding.
- **TASK-001.03 — PARTIAL:** pausing no longer drops tracker checkpoints;
  paused edits add no new words, while undo/redo follows retained checkpoints.
  Reset removes today's counts from retained checkpoints instead of replacing
  the history. Modified `app/document/writing_goals.py`, `app/ui/main_window.py`,
  `tests/test_writing_goals.py`, `tests/test_editor_widget.py`, and `README.md`.
  Focused tests: 77 passed; full offline suite: 671 passed, 2 skipped.
  Reconfiguration can still discard checkpoints;
  complete cross-scope accounting and a bounded history remain outstanding.
- **TASK-001.03 — PARTIAL:** undo/redo to a checkpoint no longer retained by
  the tracker no longer credits restored text as newly written. Modified
  `app/document/writing_goals.py`, `tests/test_writing_goals.py`,
  `tests/test_editor_widget.py`, `README.md`, and `TASKS.md`. Focused tests:
  75 passed; full offline suite: 669 passed, 2 skipped. Earlier daily
  contributions cannot be reconstructed after history reattachment; complete
  pause/reset/undo accounting remains outstanding.
- **TASK-001.05 — PARTIAL:** added `benchmarks/writing_goal_history.py`, an
  offline Qt session with 1,000 separate synthetic word-insertion commands and
  100 undo/redo operations. On this machine it recorded 101/501/1,001 tracker
  states and 56,701/222,675/416,017 current Python-traced bytes after
  100/500/1,000 commands; counts were 1,000 → 900 → 1,000 across undo/redo.
  Modified the benchmark, `README.md`, and `TASKS.md`. Writing-goal tests:
  22 passed; full offline suite: 666 passed, 2 skipped. The measurement includes
  Python allocations beyond the tracker, excludes Qt native allocations, and
  is a single synthetic append-heavy run. Mixed edits, longer sessions and
  native memory measurements remain outstanding; this does not establish a
  bound or solve TASK-001.02.
- **TASK-009.04 — PARTIAL:** revision comparisons identify changed manifest
  fields for character profiles, directed relationships and scene-character
  associations, without displaying their values or portrait data. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 162 passed; full offline suite: 666 passed, 2 skipped; Ukrainian
  source catalog validation passed. Before-and-after metadata values, broader
  structure comparisons, native accessibility review and
  release catalog compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** the revision comparison now displays both old
  and new titles and stable IDs for renamed chapters, scenes and notes. Modified
  `app/ui/revision_history_dialog.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 162 passed; full offline suite: 666 passed, 2 skipped; Ukrainian
  source catalog validation passed. Metadata field-level differences, native
  accessibility checks and release catalog compilation
  remain outstanding.
- **TASK-005.04 — PARTIAL:** standalone saves and project text writes now
  share an in-process lock over fingerprint checks and replacement, including
  project bulk text updates. Threaded regressions cover two standalone saves
  and a project save racing a standalone save. Modified
  `app/document/file_manager.py`, `app/document/write_lock.py`,
  `app/project/service.py`, `tests/test_document.py`,
  `tests/test_project_domain.py`, and `README.md`. Focused document, project
  and translation suites: 71 passed; full offline suite: 665 passed, 2 skipped.
  Independent-process coordination remains outstanding, as does coordination
  with separate project manifest writes.
- **TASK-009.04 — PARTIAL:** revision comparisons now report added, removed
  and changed scene-character associations by stable character ID, ignoring
  association-list reordering. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `tests/test_revisions.py`,
  `tests/test_project_ui.py`, `translations/utexteditor_uk.ts`, and `README.md`.
  Focused revision and UI suites: 161 passed; full offline suite: 663 passed,
  2 skipped; Ukrainian source catalog validation passed. Field-level metadata
  differences and broader structure comparisons remain,
  as do native accessibility verification and release catalog compilation.
- **TASK-009.04 — PARTIAL:** revision comparisons now flag added, removed and
  changed character profiles and directed relationships by stable ID, without
  rendering profile data or portraits. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `tests/test_revisions.py`,
  `tests/test_project_ui.py`, `translations/utexteditor_uk.ts`, and `README.md`.
  Focused revision and UI suites: 159 passed; full offline suite: 661 passed,
  2 skipped; Ukrainian source catalog validation passed. Field-level
  differences, scene-character association changes, native
  accessibility checks and release catalog compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** comparisons now report project title changes
  and scene/reference-note path changes with before/after values. Missing path
  or title metadata in legacy structures does not produce inferred changes.
  Modified `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 157 passed; full offline suite: 659 passed, 2 skipped; Ukrainian
  source catalog validation passed. Other metadata and structure comparisons,
  native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** comparisons now identify a scene's chapter change,
  including moves to or from ungrouped, even when its flattened ordering does
  not change. Stable chapter IDs distinguish duplicate titles; legacy snapshot
  structures without scene-parent data do not generate inferred moves. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, and `README.md`. Focused revision and UI
  suites: 155 passed; full offline suite: 657 passed, 2 skipped; Ukrainian
  source catalog validation passed. Other structure and metadata comparisons,
  native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-009.04 — PARTIAL:** revision comparisons now report chapter
  additions, removals, title changes and reordering, avoiding false moves from
  insertions or removals. The review dialog labels chapter changes. Modified
  `app/document/revisions.py`, `app/ui/revision_history_dialog.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, `UNIMPLEMENTED_FEATURES.md`,
  and `TASKS.md`. Focused revision and project UI suites: 153 passed; full
  offline suite: 655 passed, 2 skipped. Ukrainian source catalog validation
  passed. Directed link additions and
  removals are also reported by stable IDs. Scene-parent and other
  structure comparisons, native accessibility checks and release catalog
  compilation remain outstanding.
- **TASK-009.01 — DONE:** snapshot previews now provide previous/next pages
  over all captured scene and note text, retaining a 32,768-character display
  bound per page. Selecting a different snapshot resets the page. Modified
  `app/ui/revision_history_dialog.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, and `TASKS.md`. Focused
  revision and project UI suites: 150 passed; full offline suite: 652 passed,
  2 skipped. Ukrainian source catalog validation passed. Native accessibility checks and release catalog
  compilation remain outstanding.
- **TASK-009.01 — PARTIAL:** selecting one revision shows a read-only preview
  of scene and note contents, capped at 32,768 characters and labeled when
  truncated. A selection generation prevents older asynchronous comparisons
  from replacing the current preview. Modified `app/ui/revision_history_dialog.py`,
  `app/ui/main_window.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, and `TASKS.md`. Focused
  revision and project UI suites: 150 passed; full offline suite: 652 passed,
  2 skipped. Ukrainian source catalog validation passed. Full access to
  content beyond the preview limit, native
  accessibility verification, and release catalog compilation remain.
- **TASK-009.02 — DONE:** the revision history dialog now offers confirmed
  deletion of a single selected snapshot in a worker. The store revalidates
  the captured digest and rejects symlinks before deletion; project text is
  untouched. Modified `app/document/revisions.py`,
  `app/ui/revision_history_dialog.py`, `app/ui/main_window.py`,
  `tests/test_revisions.py`, `tests/test_project_ui.py`,
  `translations/utexteditor_uk.ts`, `README.md`, `UNIMPLEMENTED_FEATURES.md`,
  and `TASKS.md`. Focused revision and project UI suites: 148 passed; full
  offline suite: 650 passed, 2 skipped. Ukrainian source catalog validation
  passed. A separate process could still
  replace the file between the final integrity check and unlink; native
  accessibility verification and release catalog compilation remain.
- **TASK-008.02 — DONE:** recovery scans now report unfinished atomic-write
  temporary files as well as malformed snapshots. The report says a write may
  still be in progress; automatic retention and document cleanup preserve
  these files, and confirmed discard removes them. Modified
  `app/document/recovery.py`, `app/ui/main_window.py`,
  `translations/utexteditor_uk.ts`, `tests/test_recovery.py`, `README.md`, and
  `TASKS.md`. Focused recovery and project UI suites: 155 passed; full offline
  suite: 648 passed, 2 skipped. Ukrainian source catalog validation passed.
  Incomplete files are diagnostic only;
  extracting intact content, native accessibility checks, and release catalog
  compilation remain outstanding.
- **TASK-005.02 — DONE:** added
  `test_separate_process_edit_after_final_check_exposes_save_race` in
  `tests/test_document.py`. A subprocess writes between the final check and
  replacement, demonstrating that its edit is currently overwritten. This
  assertion records a known defect and must change when coordination is fixed.
  Focused document and project-domain suites: 63 passed; full offline suite:
  646 passed, 2 skipped. Independent-process coordination remains outstanding.
- **TASK-008.04 — DONE:** the recovery dialog can restore one selected
  readable snapshot, including an older version, via the existing conflict-safe
  background restore. Updated `app/ui/main_window.py`,
  `translations/utexteditor_uk.ts`, `tests/test_project_ui.py`, `README.md`,
  `TASKS.md`, and `UNIMPLEMENTED_FEATURES.md`. Focused recovery and project UI
  suites: 154 passed; full offline suite: 647 passed, 2 skipped. Ukrainian
  source catalog validation passed. Invalid snapshots remain
  diagnostic only; release catalog compilation and native accessibility
  verification remain outstanding.
- **TASK-005.01 and TASK-005.05 — DONE (audit):** inspected
  `app/document/file_manager.py` and `app/project/service.py`. Both recheck
  after staging; project text writes also use a process-local lock. Separate
  process staging tests in `tests/test_document.py` and
  `tests/test_project_domain.py` cover conflicts. README documents the final
  check-to-replace race with independent writers. TASK-005.04 remains partial:
  those checks cannot prevent a change after the last check. No native
  cross-platform coordination verification was performed.
- **TASK-008.02 — PARTIAL:** recovery scan now reports malformed or
  timezone-free capture timestamps and orders valid timestamps by instant,
  preventing a damaged timestamp from selecting the wrong latest snapshot.
  The invalid file remains available for diagnosis, but its text cannot yet
  be selectively recovered in the UI. Modified `app/document/recovery.py`,
  `tests/test_recovery.py`, `README.md`, `TASKS.md`, and this file. Focused
  recovery and project UI suites: 153 passed. Full offline suite: 645 passed,
  2 skipped. Further incomplete-set diagnosis and selective recovery remain.
- **TASK-001.01 — DONE:** reviewed `WritingGoalTracker.record_text` and the
  Qt undo integration in `MainWindow._record_writing_goal_text` against
  `test_history_keeps_one_text_copy_and_tracks_undo_branch_across_days` and
  `test_compacted_command_preserves_daily_counts_through_reset_undo_and_redo`.
  Merged commands share an endpoint and cleared undo stacks are pruned, but
  separately reachable commands still each retain metadata. TASK-001.02 and
  .04 remain partial; bounding them safely needs a design that preserves Qt
  undo and redo semantics.
- **TASK-008.05 — DONE:** automatic retention and saved-document cleanup now
  preserve unreadable, invalid, and unsupported-version recovery snapshots;
  confirmed explicit discard can still remove them. Modified
  `app/document/recovery.py`, `tests/test_recovery.py`, `README.md`, and
  `TASKS.md`. `tests/test_recovery.py`: 14 passed; full offline suite: 642
  passed, 2 skipped. Damaged snapshots can
  accumulate until explicitly discarded; recovery diagnosis and selective
  recovery remain incomplete.
- **Audit queue:** complete the remaining atomic status audit; prioritize
  TASK-005 save coordination, TASK-007 conflict protection, TASK-008 recovery
  diagnosis, and TASK-009 safe revision management before performance and UX.
  Other inherited statuses remain unverified. Native screen-reader and
  platform checks require a suitable GUI environment.

This file was created because no earlier progress checkpoint was present in
the repository. The task statuses in `TASKS.md` remain authoritative.

- **TASK-001 — incomplete:** merged Qt undo commands are compacted, but
  metadata for separate undo commands remains unbounded. The documented
  benchmark covers tracker allocations, not a fixed bound. See
  `UNIMPLEMENTED_FEATURES.md` for details. Do not clear the author's undo
  stack merely to meet a memory bound.
- **TASK-002 — complete:** destination labeling was updated and local and
  remote hosts were covered by tests. The work remains in the existing
  uncommitted worktree.
- **TASK-003 — complete:** a non-modal English/Ukrainian disclosure gates
  completion, spellcheck, prompt generation, character assistance, project
  setup, Auto-pilot, Auto-writer, translation, and project analysis. Consent
  persists for the approved destination without document content; a changed
  host requires renewed consent. Automatic requests retry with fresh state
  after consent; explicit actions prompt the user to retry. Declined automatic
  requests do not repeatedly reopen the dialog. Workers retain the provider
  captured before settings changes. Tests cover all workflow gates, local and
  remote hosts, decline, destination changes, persistence failure, and a
  disclosure opened from a modal workflow. Full offline suite: 421 passed,
  2 skipped (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  .venv/bin/python -m pytest -q`).
- **TASK-004 — implemented:** spellcheck now waits for the active provider
  call to finish and retains only the latest pending request. A changed editor,
  settings change, cancellation, or shutdown discards pending work. Offline
  Qt tests exercise slow and failing calls, stale edits, cancellation, and UI
  event-loop responsiveness. The full offline suite passed: 409 passed,
  2 skipped (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1
  .venv/bin/python -m pytest -q`).
- **TASK-005 — in progress:** standalone saves, project text saves, and
  project manifest saves recheck the disk after staging. Separate-process
  regression tests cover edits during staging. A separate-process edit injected
  immediately after the last check is still overwritten: no portable atomic
  compare-and-replace or independent-editor lock is in place. Do not mark this
  task complete until a supported coordination guarantee is implemented and
  cross-platform verification is performed. The full offline suite after this
  mitigation passed: 424 passed, 2 skipped (`QT_QPA_PLATFORM=offscreen
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`).
- **TASK-006 — in progress:** bounded completion-context construction now
  searches only the requested window, avoiding a copy of the entire prefix.
  On this machine, `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python
  benchmarks/completion_context.py` measured 100 middle-of-document calls on
  five million characters: previous 0.0459 s and 2,504,082 peak Python bytes;
  current 0.0001 s and 4,041 bytes. These are microbenchmarks, not GUI latency
  or process memory measurements. An offscreen GUI baseline is now available
  via `benchmarks/editor_responsiveness.py`, with new-word tracking enabled.
  For 100,000/1,000,000 characters, before the tracker optimization, opening
  in Qt took 8.48/73.63 ms, typing 10.98/78.85 ms, cursor movement 1.91/14.83
  ms, word counting 1.40/14.33 ms, and cumulative peak RSS was 102/125 MB.
  Comparing unchanged edit spans in chunks reduced measured typing to
  8.68/67.20 ms in a subsequent run; Qt opening was 8.71/77.89 ms. These
  single-run, offscreen timings include GUI callbacks but exclude rendering
  and are not platform-independent thresholds. The one-million-character
  case remains slow; representative repeated measurements, GUI event-loop
  latency and further investigation are still needed. Do not mark complete.
- **TASK-007 — in progress:** fixed the standalone save callback to retain the
  newly written disk fingerprint, including after Save As. A Qt regression
  test exercises two saves followed by an external edit and verifies that the
  conflict preserves the buffer and disk. File > Review External Changes now
  presents saved, disk, and buffer versions alongside an editable conservative
  merge proposal for standalone and project files. Reload and merge are
  undoable, Save Elsewhere uses the existing save flow, and the disk is
  rechecked after review and on save. Tests cover cancellation, stale buffers
  and disk, unresolved markers, reload, Save Elsewhere, and project and
  standalone files. The Ukrainian source catalog has been updated; its
  compiled catalog remains to be rebuilt through the project's release
  process. The residual cross-process race means the no-silent-overwrite
  acceptance criterion is not yet fully met; do not mark this task complete.
  Full offline suite: 444 passed, 2 skipped.
- **TASK-012 — in progress:** added a bounded, cancellable literal search
  service for captured scene and note descriptors. Open buffer snapshots take
  precedence over disk, unreadable, binary, or oversized files are reported,
  and results carry stable IDs, locations, excerpts, and text fingerprints.
  Search > Search Project Text now opens a persistent results panel. Navigation
  checks captured project identity and document fingerprints before selecting
  a match, including newly opened items. Qt tests cover unsaved Unicode text,
  stale buffers and files, opening results, and cancellation. Ukrainian source
  strings are present but the compiled catalog remains to be rebuilt. Large
  projects still need GUI responsiveness measurements and more stress tests;
  path resolution now runs in the search worker. Do not mark complete until
  those issues and localization are verified. Full offline suite: 454 passed,
  2 skipped. A further 5,000-document regression verifies cancellation while
  reporting unreadable files and confirms that remaining files are not visited.
  Full offline suite: 542 passed, 2 skipped. GUI responsiveness measurements
  and compiled localization remain outstanding. Error reporting now retains
  at most 100 bounded details and counts additional unreadable files, avoiding
  an unbounded results label. Focused service and panel tests and Ukrainian
  catalog validation passed; full offline suite: 544 passed, 2 skipped. The
  new `benchmarks/project_search_responsiveness.py` measures a synthetic
  2,000-file project through the offscreen window. One run measured 0.7 ms
  startup, 100.8 ms total and a 5.7 ms maximum timer gap for no matches; a
  result-limited search measured 0.7 ms startup, 20.5 ms total and a 20.5 ms
  maximum timer gap for 1,000 matches. These are single-run measurements on
  this machine, not native rendering or portable guarantees. Broader native
  responsiveness and compiled localization remain outstanding. Project-open
  callbacks now discard a read if its item was removed or relinked while the
  read was pending, including opens initiated by search. Project UI regression
  tests cover both cases; full offline suite: 546 passed, 2 skipped. Capture
  now avoids copying open buffers whose Qt length proves they exceed the search
  size limit, and reports them without falling back to stale disk text. Result
  excerpts are also bounded for long search queries. Focused service and Qt
  tests and the full offline suite passed: 574 passed, 2 skipped. Native
  responsiveness and compiled localization remain outstanding. The search
  status and unreadable-file details now scroll within a bounded-height area,
  leaving room for results; an offscreen test covers 100 errors and the
  omitted-error count. Full offline suite: 636 passed, 2 skipped.
- **TASK-013 — in progress:** Search > Quick Open provides a keyboard-driven
  picker for scene, chapter, note and character names and character aliases,
  showing type, chapter context and stable IDs. It opens existing documents
  without closing unsaved tabs; chapters are revealed in the tree. Offline Qt
  tests cover filtering, duplicates, keyboard activation, unsaved tabs, deleted
  items, chapter reveal, and shortcut uniqueness. The Ukrainian source catalog
  needs compilation and the shortcut needs native-platform verification.
  Do not mark complete until those checks are performed. Full offline suite:
  459 passed, 2 skipped.
- **TASK-014 — implemented:** Project > Reveal Current Document in Project
  locates a bound scene or note by stable ID, expands only its ancestors and
  preserves other expansion state. Standalone and unavailable items report
  why they cannot be revealed. Offline Qt tests cover both item types,
  duplicate titles, unsaved text, and standalone documents; Ukrainian strings
  are in the catalog. The full offline suite passed: 414 passed, 2 skipped
  (`QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m
  pytest -q`).
- **TASK-015 — in progress:** existing linked-note navigation also works from
  a selected scene, and the scene context menu exposes the action. A Qt test
  verifies linked-note navigation preserves unsaved scene text and does not
  change links. Character-to-scene navigation, a return path that preserves
  staged character-profile edits, broader navigation tests, and compiled
  Ukrainian strings remain outstanding. Do not mark complete. Full offline
  suite: 460 passed, 2 skipped. The character tree menu now offers a separate
  picker for explicitly associated scenes, distinguished from mention search.
  It checks that the character and association still exist after the picker
  closes; a regression covers stale associations and duplicate scene titles.
  Profiles now open explicitly associated scenes and provide a status-bar
  return control while retaining staged fields and relationships. Closing the
  window returns to the profile, and stale profiles, changed relationships,
  stale associations and failed saves are handled without silently losing
  edits. Native keyboard/accessibility review and release catalog compilation
  remain outstanding; do not mark complete until verified. Full offline suite:
  592 passed, 2 skipped. Linked-item navigation also rechecks the project and
  link after selection, uses stable IDs even when titles contain brackets, and
  translates its picker and stale-link messages. Full offline suite after this
  follow-up: 597 passed, 2 skipped.
- **TASK-016 — in progress:** Qt's existing Ctrl+Tab and Ctrl+Shift+Tab
  behavior was verified with offscreen keyboard tests, and View > Open Tabs
  provides a searchable picker with modified markers, file/project context,
  and distinct labels for duplicate untitled tabs. Closing remains handled by
  the existing unsaved-change flow. Compiled Ukrainian strings and manual
  native-platform shortcut verification remain outstanding; do not mark
  complete until verified. Full offline suite: 462 passed, 2 skipped.
- **TASK-017 — in progress:** File > Open Recent File stores up to ten paths
  independently of recent projects, reuses existing tabs, handles missing
  files through the normal open-error path, and provides Clear Recent Files.
  Settings validation and Qt tests cover persistence, duplicates, unsaved
  buffers, missing files and clearing. Ukrainian source strings need compiling;
  settings persistence currently follows the existing synchronous recent-
  project pattern and needs a non-blocking, serialized persistence design.
  Do not mark complete until these issues are resolved. Full offline suite:
  464 passed, 2 skipped.
- **TASK-018 — in progress:** grouped Project movement, links, revisions,
  export and AI actions into submenus while retaining their existing action
  objects, and added project/selection requirement descriptions. AI menu
  separators and existing keyboard shortcuts remain in place. Automated tests
  cover grouping and action availability; native keyboard and accessibility
  review and compilation of Ukrainian source strings remain outstanding.
  Do not mark complete until manual review is performed. Full offline suite:
  464 passed, 2 skipped.
- **TASK-019 — in progress:** session-local Back and Forward actions now
  record explicit scene, note and project-search jumps in a bounded history.
  They restore positions in still-open, unchanged tabs and skip stale or
  removed destinations; tests cover branching, limits and unsaved buffers.
  Reopening closed destinations, broader search/navigation coverage, compiled
  translations and native keyboard verification remain outstanding. Do not
  mark complete. A further offscreen regression covers Back and Forward across
  two Unicode search-result selections in an unsaved scene and verifies that
  neither the buffer nor the disk is changed. Reopening closed destinations
  and native verification remain outstanding. History now also skips a tab
  when its scene or note has been relinked to a different path; an offscreen
  regression covers a relinked scene. Full offline suite: 618 passed, 2 skipped.
- **TASK-020 — in progress:** Find and Replace now offer case and whole-word
  controls while retaining case-sensitive literal defaults. Navigation,
  counts and replacement use the same Qt matching rules, replace-all remains a
  single undoable edit, and Find/Replace focus and close behavior are distinct.
  Tests cover Ukrainian case, Unicode positions, whole-word selections,
  no-op and no-match behavior, undo, focus and an offscreen small-width layout.
  Compiled Ukrainian strings and native small-window/keyboard verification
  remain outstanding. Case-insensitive and whole-word match counts now run in
  bounded event-loop batches; changing the query or active editor discards an
  unfinished count. Tests cover yielding and stale counts. Default literal
  counting now also uses Qt's batched matching path without copying the full
  buffer. An offscreen regression checks yielding, Unicode and no full-text
  copy. A single Qt search can still scan a large unmatched span on the GUI
  thread, and replace-all remains synchronous; broader performance and native
  verification remain outstanding. Full offline suite: 629 passed, 2 skipped.
- **TASK-021 — in progress:** AI > Review Spelling and Grammar presents
  current validated findings with explanations and selection controls. It
  rejects changed or overlapping selections, and applies selected corrections
  as one undoable edit. Tests cover cancellation, selection, Unicode, stale
  edits, overlapping ranges and undo. Compiled Ukrainian translations and
  native accessibility verification remain outstanding. Full offline suite:
  486 passed, 2 skipped.
- **TASK-022 — in progress:** AI Settings now offers a persisted option to
  exclude project characters and reference notes from automatic completions;
  explicit completions retain existing project context. Offline worker tests
  cover both modes and settings validation. Further preview validation and
  compiled Ukrainian translation remain outstanding. Do not mark complete.
  Full offline suite:
  472 passed, 2 skipped. Context construction now also returns an immutable
  capture with note provenance and truncation metadata for the future preview;
  the existing request path uses the same captured text. Full offline suite
  after this refactor: 473 passed, 2 skipped. AI > Completion Reference Notes
  now excludes selected notes for the project session and invalidates pending
  completions when the selection changes. A worker regression test covers
  selection and stale results. Full offline suite: 474 passed, 2 skipped. A
  read-only captured-context review dialog is available through an explicit
  AI action. It captures reference material in a worker, displays the exact
  context, destination, unsaved buffers and note truncation, and checks editor,
  project, settings and open-note state before sending and applying results.
  Tests cover exact context, cancellation and edits during review. Closed
  notes are now checked in the worker before sending and after generation;
  stale results are discarded. As with other filesystem checks, a change can
  still race the final check. The preview flags omitted
  document prefixes and character text cut by the length limit. It also flags
  character goals, traits, knowledge, scene goals, development notes and state
  changes omitted by per-field limits. Focused service and offscreen review
  tests cover these limits; compiled Ukrainian translations remain outstanding.
  Full offline suite: 557 passed, 2 skipped.
- **TASK-023 — in progress:** project translation now retains captured source
  contents and presents titles and texts side by side before explicit Apply or
  Cancel. It rechecks project, settings and all open project editors after
  review, then uses the existing transactional commit. Tests cover navigation,
  unsaved source, cancellation, changed buffers and the full apply path.
  Ukrainian catalog compilation and native accessibility review remain
  outstanding. Review labels now include stable chapter, scene and note IDs
  so duplicate titles are distinguishable. Tests cover duplicate scenes,
  unsaved source and cancellation or edits during review. Full offline suite:
  635 passed, 2 skipped.
- **TASK-024 — in progress:** after generation, Auto-writer presents a
  navigable, read-only per-scene review with individual selection. It warns
  that later drafts can depend on rejected drafts, rechecks open project
  buffers and applies selected scenes through the existing transaction.
  Tests cover selection, cancellation, stale edits and preview navigation.
  Compiled Ukrainian strings and native accessibility review remain
  outstanding. Auto-writer progress signals now carry the request generation,
  preventing delayed messages from an older request updating a newer progress
  window; a queued-signal regression covers both stale and current messages.
  Full offline suite: 640 passed, 2 skipped.
- **TASK-025 — in progress:** the provider protocol and Ollama client now
  support bounded NDJSON streaming with chunk callbacks, cooperative
  cancellation and explicit malformed/oversized response errors. Tests cover
  chunks, cancellation including the final chunk, malformed responses and the
  byte limit. An opt-in setting now enables a non-modal provisional preview
  for prompt generation, with bounded worker buffering, cancellation and stale
  editor checks; the final draft still requires explicit insertion. Offline
  tests cover incremental updates, cancellation, stale edits, undo and the
  output limit. Blocking reads remain subject to the configured network
  timeout; native accessibility review and compiled Ukrainian strings remain
  outstanding. Do not mark complete until those checks are performed. Full
  offline suite: 500 passed, 2 skipped; the additional final-review rejection
  case passed in the focused streaming tests.
- **TASK-026 — in progress:** inline completion rendering now shows any
  separating space that acceptance would insert, and discards a suggestion
  when resizing makes it too wide to display. An offscreen regression test
  covers resizing without modifying the document. Long, multiline and mid-line
  suggestions still need a safe, readable review affordance; native window
  and accessibility verification are also outstanding. Do not mark complete.
  Full offline suite: 502 passed, 2 skipped; focused completion tests also
  passed after the final rendering adjustment.
- **TASK-027 — in progress:** View > Markdown Preview renders the active
  unsaved buffer in a read-only dock, debounces changes, checks captured
  revisions, blocks resource loading, and renders in a worker. Input and
  rendered output are bounded; the initial version explicitly declined
  documents over 65,536 Qt text units. Tests cover stale renders, unsaved text, resource
  blocking and the input limit. Large-document preview and responsiveness,
  compiled translations, and native accessibility review remain outstanding;
  do not mark complete. Full offline suite: 506 passed, 2 skipped. Large
  documents now render a clearly labeled prefix captured without copying the
  entire buffer; the 65,536 Qt-unit input bound remains. A regression covers
  a Unicode cutoff and preservation of the source buffer. Full offline suite:
  568 passed, 2 skipped. Full-document preview, broader responsiveness and
  native accessibility verification remain outstanding.
- **TASK-028 — in progress:** PDF compilation now offers A5, A4 and Letter
  paper, an editable book title and an optional title-page author. Tests check
  actual page dimensions, author text, invalid sizes, and unsaved scene
  inclusion. An export preview, PDF scene/heading choices, broader pagination
  and layout checks, compiled translations and native review remain; do not
  mark complete. Full offline suite: 511 passed, 2 skipped. Markdown/text and
  PDF workers now use the captured scene list instead of enumerating the live
  manifest again. A regression covers later-added unreadable scenes and unsaved
  buffers. Closed scene contents are still read in the worker and a complete
  captured-content review remains outstanding. Full offline suite: 569 passed,
  2 skipped. PDF options now allow scene headings to be omitted from both the
  contents and manuscript, retaining them by default. PDF extraction and Qt
  workflow tests cover grouped and ungrouped scenes and unsaved text. Scene
  selection, chapter heading choices, preview, captured closed-scene contents,
  compiled translations and native PDF review remain outstanding. Full offline
  suite: 571 passed, 2 skipped. Both export workers now reject scene, note and
  manifest destinations, including symbolic and hard links. Text export retains
  the overwrite decision made at confirmation, so a destination created later
  is not replaced without approval. Tests cover both safeguards; filesystem
  changes can still race the source-path check. Full offline suite: 576 passed,
  2 skipped. PDF options now list scenes with chapter context and stable IDs;
  unchecked scenes are omitted without being read, and only selected unsaved
  buffers are included. A stale project generation cancels the selection.
  Tests cover duplicate labels, omitted unreadable scenes and stale options.
  PDF chapter headings can now also be omitted from the contents and body;
  section page breaks remain. Preview, captured closed-scene contents, compiled
  translations and native review remain outstanding. Do not mark complete.
  Full offline suite: 579 passed, 2 skipped; focused PDF tests also cover
  showing scene headings while chapter headings are hidden. Markdown/text
  export now also abandons a selection when the project generation changes
  during its destination, overwrite, options or unsaved-content dialogs; Qt
  regressions cover each dialog. Text export now captures and warns about only
  selected scene buffers, excluding unsaved notes and omitted scenes; an
  offscreen regression checks the resulting output. Full offline suite:
  585 passed, 2 skipped.
- **TASK-030 — in progress:** the long Story and Background and personality
  forms now scroll in smaller profile windows; an offscreen test covers access
  to their last fields and unchanged staged-save behavior. Character-to-scene
  navigation and a safe return path are now available as described under
  TASK-015. Native keyboard/accessibility verification and release catalog
  compilation remain outstanding. Do not mark complete. Full offline suite:
  592 passed, 2 skipped.
- **TASK-031 — in progress:** added a 20-case multilingual corpus and made
  short, unsupported-script and Russian-specific text fall back to Auto,
  requiring stronger common-word evidence for English or Ukrainian. The old
  detector matched 16/20 corpus expectations; the updated detector matched
  20/20, with explicit overrides covered. This is a small regression corpus,
  not a representative accuracy estimate; broader multilingual evaluation
  remains. Do not mark complete on that basis alone. Full offline suite: 533
  passed, 2 skipped. Shared Cyrillic words alone no longer classify text as
  Ukrainian: two Russian examples and an ambiguous Ukrainian example now fall
  back to Auto. The corpus contains 23 cases; broader evaluation remains.
  Full offline suite: 550 passed, 2 skipped. Detection now normalizes Unicode
  before inspecting scripts and treats remaining combining marks as ambiguous.
  An expanded 33-case corpus includes decomposed Ukrainian and accented or
  unsupported text: the previous detector matched 30 cases and the updated
  detector matched 33. This remains a small, nonrepresentative corpus; broader
  evaluation is still needed. The detector now requires at least eight letters
  and two distinct signal words, so digits and repeated words cannot turn a
  short fragment into a confident classification. On the expanded 43-case
  regression corpus the previous detector matched 35 expectations and the
  revised detector matched 43. This corpus remains nonrepresentative; broader
  multilingual evaluation is outstanding. Full offline suite: 628 passed,
  2 skipped.
- **TASK-033 — in progress:** added a command-line TS validator for missing,
  unfinished and malformed entries, Qt and named-format placeholder parity,
  and English/Ukrainian plural forms. It can compare against an independently
  extracted source catalog, exits nonzero on errors, and has offline tests.
  An earlier comparison against a fresh Qt extraction reported 57 gaps,
  including false contexts produced for calls such as `dialog.tr`.
  Extraction, validation and compilation are documented.
  Calls through character-dialog and AI-activity instances now use their widget
  classes for translation, so a fresh extraction uses the runtime contexts.
  The extracted marked strings match the Ukrainian source catalog, and an
  automated extraction comparison guards against regressions. This does not
  detect hardcoded, unmarked strings; the broader UI audit and compiled
  catalogs remain outstanding. Do not mark complete on extraction alone.
  Full offline suite: 547 passed, 2 skipped. Duplicate context/source/comment
  entries now fail validation instead of masking an earlier entry; one
  identical duplicate was removed from the Ukrainian source catalog. Focused
  validator tests and the full offline suite passed: 570 passed, 2 skipped.
  The validator now also checks plural flags against extracted source entries
  and rejects plural forms in non-plural messages; focused tests cover both
  mismatch directions. Python format-field detection now includes attribute
  and index lookups, with regression tests for changed fields and conversions.
  Full offline suite: 639 passed, 2 skipped.
- **TASK-033 audit extension:** `tools/audit_ui_strings.py` reports likely
  unmarked literals and f-strings in selected Qt UI calls, with an optional
  nonzero exit for findings and explicit parse-error handling. A current scan
  reports 148 candidates requiring human review; this heuristic neither
  covers every API nor proves each candidate is user-visible. Catalog
  compilation and the broader audit remain outstanding. Full offline suite:
  596 passed, 2 skipped. After reviewing that initial set, three candidates
  remain: the product name and two labels built from project or path data.
  The audit now also checks status messages, dialog buttons and file-dialog
  labels; the expanded scan reports 45 candidates for review. The scan now
  also covers tab, item, progress and dialog-detail labels. It found two
  untranslated project translation progress messages, now added to the
  Ukrainian catalog; other new candidates are language names. Runtime and
  audit tests pass. The heuristic still does not cover every UI API. Full
  offline suite: 631 passed, 2 skipped.
- **TASK-032 — in progress:** the Ukrainian source catalog now covers the
  previously missing character portrait and scene-development workflow labels,
  prompts and errors, plus the main-window open-error title. A full UI audit,
  extraction-context cleanup and compiled catalog remain outstanding. Do not
  mark complete. Temporary-catalog runtime translation tests passed; full
  offline suite: 539 passed, 2 skipped. Character profile state and scene
  history headings are now translated in the dialog's runtime context; a
  compiled temporary catalog test checks all three headings. The wider audit
  and release catalog compilation remain outstanding. Project-document opening
  and verification status/error messages now use translated strings with
  preserved dynamic details. Translation extraction and temporary-catalog
  tests pass; the full offline suite passed: 557 passed, 2 skipped. The editor's
  spelling context-menu Replace and Ignore actions now use translated labels,
  retaining the original and proposed words as placeholders. Standalone file
  open/save dialogs, status and error headings, and recovery-cleanup and
  autosave failure messages have also been marked and translated. PDF export
  dialogs, overwrite and unsaved-content prompts, and status/error headings
  now use Ukrainian catalog entries with tested path placeholders. The wider
  audit, including PDF document labels, and release catalog compilation
  remain outstanding. Markdown/plain-text export dialogs, options, prompts and
  status messages are now translated as well; a Qt regression verifies that a
  translated plain-text filter still selects plain-text output. The broader
  audit and release catalog compilation remain outstanding. The recovery
  chooser, inspection and discard messages now use Ukrainian catalog entries;
  temporary-catalog tests check dynamic recovery details. Further recovery
  flows and the wider audit remain outstanding. Recovery restore failure,
  comparison and attention headings, successful restore feedback, and the
  duplicate-open warning now also use Ukrainian catalog strings. Recovery
  comparison labels, status and read-error wrappers are now translated without
  translating document text. Underlying restore errors and the wider audit
  still need localization; release catalog compilation remains outstanding.
  Closing a tab and quitting now share translated unsaved-document prompts,
  including the untitled-document name; an offscreen test checks cancellation
  with a temporarily compiled Ukrainian catalog. Project creation, character
  filtering, project errors and chapter, scene, note and character creation
  prompts now use translated labels. Note-type choices retain their stable
  manifest values in both languages; offscreen tests cover all five types.
  Project-item removal choices and destructive confirmations are now translated,
  with cancellation and path placeholders covered by tests. Move, import,
  rename, duplicate and link-management prompts now use Ukrainian strings;
  an offscreen test checks that translated link choices retain their IDs.
  Scene-character association prompts are translated as well; tests verify
  that both localized presence choices preserve their stored values and that
  existing development details round-trip. Directed-relationship management
  and character-profile import/export messages are also translated; a Qt test
  checks the localized remove action targets the correct relationship. The
  AI project setup, Auto-writer and project translation confirmation messages
  now disclose their content and destination in Ukrainian; a cancellation test
  checks the translated destination and language labels. Template-suggestion
  and autonomous Auto-pilot disclosures now also show the destination and the
  automatic-application behavior in Ukrainian; a cancellation test checks that
  disclosure. Project-analysis confirmations now translate the selected scene,
  reference-note and associated-character labels, context limit and destination
  without changing the model prompt. Writing-goal feedback and accessibility
  names, character mention search, revision snapshots, settings validation and
  the AI diagnostics privacy warning are also translated. Whole-document
  formatting choices, outline validation, project navigation accessibility,
  AI setup and analysis errors, and connection-test feedback now use catalog
  strings. A Qt test checks that a translated formatting choice still performs
  the intended undoable operation. Recent-file and project persistence errors,
  writing-goal, recovery and shutdown status messages now use Ukrainian
  strings, with dynamic error details retained. The project-open dialog title
  and additional AI setup, generation and analysis status messages are now
  translated; an offscreen test checks the dialog title using a temporary
  compiled catalog. Further workflows still need auditing and release catalog
  compilation remains outstanding. Line and column labels, AI error details,
  and spellcheck feedback now use translated templates, including Ukrainian
  plural forms. AI connection states are also translated at display time while
  retaining their internal values. Runtime tests cover connection status,
  error details and plural selection. Project translation success, failure,
  cancellation and stale-state messages now use Ukrainian templates while
  preserving paths and error details; runtime catalog tests cover feedback.
  Translation progress now localizes its status and field labels in the UI
  while preserving source titles and IDs and the service's progress API.
  Auto-writer progress, cancellation, stale-state, completion and failure
  feedback now also uses Ukrainian templates, preserving scene titles, error
  details and snapshot paths. Runtime tests cover progress and failure and
  cancellation messages. Full offline suite: 641 passed, 2 skipped.
- **TASK-034 — in progress:** the spelling and Auto-writer review lists now
  expose keyboard-selection instructions through their accessibility
  descriptions. Offscreen tests inspect the Qt accessible interface and use
  arrow and Space keys to select and reject items. Project search now moves
  focus from its query to the results with Down, exposes result navigation
  instructions, and opens a selected result with Enter. Quick Open's Down
  shortcut is limited to its query so arrow keys can navigate its results.
  Offscreen keyboard tests cover both workflows. Native keyboard, screen
  reader and system-palette audits across core workflows, as well as compiled
  translations, remain outstanding. Do not mark complete. Full offline suite:
  635 passed, 2 skipped.
- **TASK-035 — complete:** documented independent scope and decisions for
  toolbar, appearance override, interface languages, writing languages and
  alternative providers in `UNIMPLEMENTED_FEATURES.md`. All are deferred for
  the stated usability, verification, maintenance or privacy reasons; no new
  extension is selected. Existing local-first behavior is unchanged. This is
  a documentation-only decision and needs no platform-specific verification.

The initial worktree included staged `.DS_Store` files and Python bytecode.
Preserve these unrelated changes. Earlier checkpoint implementation was
committed in `c5c2330`; the subsequent character AI fix is in `82b693f`.
The performance checkpoint is `b85cc21`; `780e44c` subsequently removed
several task definitions from `TASKS.md`. The save fingerprint checkpoint is
`437302c`.
