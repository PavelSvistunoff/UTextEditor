# Clean Code guidelines for Codex in UTextEditor

> **Origin and scope.** These are original, project-specific working instructions
> adapted from the general ideas of Robert C. Martin's *Clean Code: A Handbook
> of Agile Software Craftsmanship* (2008); this is **not a quotation** or a
> substitute for the book. Apply them to **new and directly touched code**.
> Correctness, manuscript safety, existing API contracts, Qt behavior, and the
> selected `TASKS.md` acceptance criteria take precedence over aesthetic cleanup.

## 1. Write code for the next maintainer

- Use **intention-revealing names**: a variable should say what it contains;
  a function should say what it does. Prefer `saved_disk_fingerprint` to
  `fp`, `discard_stale_completion` to `process_result`, and names that
  distinguish a saved document, a live buffer, and an external disk version.
- Match established Python conventions: `snake_case` for functions/variables,
  `PascalCase` for classes, `UPPER_SNAKE_CASE` for meaningful constants.
  Respect existing Qt signal naming where the local codebase already has it.
- Avoid obscure abbreviations, misleading negated booleans, unexplained
  numbers, and broad names such as `data`, `manager`, or `helper` when
  a specific responsibility can be named.
- Use names consistently across services, UI and tests for the same concept
  (scene, reference note, project ID, stale request, revision).

## 2. Make functions do one understandable job

- Prefer **one level of abstraction per function**. Separate capture,
  validation, computation, persistence and Qt presentation where practical.
  A GUI slot may coordinate these steps; it should not implement the domain rules.
- Prefer small, cohesive functions and **guard clauses** for invalid or stale
  states over deeply nested branches. Small does **not** mean enforcing an
  arbitrary line-count limit or fragmenting code into pointless wrappers.
- Minimize arguments. If several values belong to one captured request or
  domain concept, use an **existing** model or a small typed value object
  when that genuinely clarifies call sites. Avoid positional boolean flags
  that change behavior invisibly; prefer explicit operations or keyword arguments.
- Make side effects obvious from the function name and call site.
  Keep pure calculations independently testable. A query-like method should
  not unexpectedly mutate an editor, reset counts, send AI context or write files.

## 3. Give modules and classes a clear responsibility

- Maintain the separation of `app/ui/`, `app/document/`,
  `app/project/`, `app/ai/` and `app/settings/`.
- Put file conflict and transaction rules in the owning document/project
  services; do not grow `app/ui/main_window.py` with another copy of them.
- Keep Ollama payloads and parsing inside the provider/client boundary. Qt
  widgets should coordinate workers and show validated results, not own HTTP
  protocol details or cross-document state.
- Prefer composition and existing abstractions. Add a new interface or
  indirection only when it solves **present, demonstrable** duplication or
  coupling, not because an imagined future extension might need it.

## 4. Handle errors, boundaries and state explicitly

- Express preconditions and invariants near the operation. For async results,
  verify the captured editor, document revision, project identity, request
  generation and settings before applying anything.
- Fail visibly and safely: use meaningful exception types or structured
  results, preserve the original error context, and give the UI a useful
  explanation without leaking manuscript text or credentials.
- Avoid `except Exception: pass`, swallowed failures, magic sentinel values
  that hide distinct states, and `None` where the caller cannot tell why
  an operation failed.
- Keep destructive operations explicit and transactional; validate before
  changing the document, maintain rollback/failure behavior, and preserve
  dirty text and Qt undo.
- Treat external filesystem contents and AI output as untrusted, including
  malformed JSON, changed files, path aliases and outdated worker responses.
  Do not weaken a guard to simplify a function.

## 5. Remove duplication without creating abstraction noise

- Eliminate repeated **knowledge or business rules**, not every coincidentally
  similar line. Prefer a tested shared function if the same rule is currently
  duplicated in multiple workflows.
- Avoid speculative general-purpose frameworks, unneeded dependencies, wrapper
  classes that merely forward calls, and configuration options without a user
  requirement.
- Replace a meaningful magic number with a named constant near the rule
  (for example a byte or result limit), but do not wrap every literal.
- Leave a subsystem simpler after the change without reformatting or renaming
  unrelated code. Keep a separate task for broad refactors.

## 6. Comments explain decisions, tests explain behavior

- Make code self-explanatory where possible. Comments/docstrings should explain
  **why** a non-obvious limit, lock, stale-result rule or platform exception
  exists, as well as important input/output contracts. Do not narrate obvious
  statements or leave stale/commented-out code.
- For tricky concurrency or recovery behavior, document exactly what is and
  is **not** guaranteed. A fingerprint check plus atomic replace is not a
  cross-process compare-and-swap.
- Write deterministic tests with clear setup, action and expected outcome.
  Use scenario-revealing test names. Cover one coherent behavior per test,
  without an artificial one-assertion limit.
- Test both normal and failure cases: cancellation, stale asynchronous
  responses, unsaved buffers, Undo/Redo, Unicode, validation failures,
  save conflicts, and offline Ollama as applicable. A green test must verify
  the intended guarantee, not enshrine a known defect as success.

## 7. Incremental cleanup: the Boy Scout principle with boundaries

- Improve only code **already touched** by the selected ticket if the
  improvement is small, risk-free, covered by tests and makes the requested
  change easier to understand. Examples: rename a confusing local, extract
  a repeated condition, simplify a nested branch, remove an unused import.
- Do **not** make a separate function or module rewrite, change public APIs,
  migrate persisted YAML, discard undo history or add a formatter/linter as an
  incidental cleanup. Open a separate ticket for a larger improvement.
- Refactor **behind tests**. Keep observable behavior unchanged when a change
  is only a refactor; verify the behavior before and after.

## Practical Python / PySide6 examples

Make validation and side effects independently visible:

```python
def is_stale_revision(request_revision: int, current_revision: int) -> bool:
    return request_revision != current_revision


def should_show_completion(
    request_revision: int,
    current_revision: int,
    editor_is_active: bool,
) -> bool:
    return editor_is_active and not is_stale_revision(
        request_revision, current_revision
    )
```

This is illustrative only: **reuse the existing snapshot/generation guards**
instead of replacing a multi-field staleness check with the simplified example.

Prefer operations whose names disclose mutations:

```python
# Avoid a read-looking method that secretly clears progress:
# def get_daily_words(reset=True): ...

# Prefer separate, explicit operations if they are actually needed:
# words = tracker.daily_word_count()
# tracker.reset_daily_progress()
```

## Codex completion review (apply to each selected ticket)

- [ ] **Intent:** new or changed names reveal concepts; functions have clear
  responsibilities and side effects; abstractions add value.
- [ ] **Ownership:** domain, UI, persistence and Ollama logic remain in their
  established packages; no duplicated business rule is introduced.
- [ ] **Safety:** dirty buffers, undo, stable IDs, compatibility, transaction
  rollback, AI disclosure, stale-result and file-conflict checks are intact.
- [ ] **Errors:** meaningful failures are handled and diagnosed; no silent
  catch, data loss, sensitive logging or misleading success notification.
- [ ] **Tests:** focused normal/failure-path regressions ran, then full offline
  tests when practical; native-only checks remain explicitly unverified.
- [ ] **Diff:** no unrelated refactor or dependency, no stale comments or dead
  code, docs/translations updated when behavior or UI strings changed.
- [ ] **Report:** explain any conscious trade-off or rule not applicable, with
  test commands and results, without marking tests that did not run as passed.

The checklist is a **review aid**, not new feature scope or a replacement for
the parent task acceptance criteria.
