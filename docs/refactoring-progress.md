# Refactoring progress

## 2026-11-13 — initial checkpoint

- Scope: repository-wide Clean Code refactoring, separate from `TASKS.md` feature tickets.
- Status: **CHECKPOINT**; overall audit and refactoring are incomplete.
- Git started clean on `main` at `e1b577e`.
- Initial inventory: 123 tracked Python files; `app/ui/main_window.py` and
  `app/project/service.py` are large investigation targets, not proven defects.
- Examined: instructions, repository inventory and selected document helpers;
  no complete package audit has yet been performed.
- `app/document/encoding.py`: replaced repeated counting/manual scanning with
  one explicit line-ending matcher. Added tie, majority, empty and adjacent
  ending cases; pre-change focused test passed (38 passed).
- Baseline: `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`
  → 923 passed, 2 skipped; `python` itself is unavailable on PATH.
- After change: focused `tests/test_document.py` → 38 passed; full command
  above → 929 passed, 2 skipped. `git diff --check` passed.
- Remaining: audit every package and test against the plan; assess performance
  and safety before touching save, recovery, Qt undo or transactions.
- Native GUI, accessibility and live Ollama were not tested.
- Next: inspect `app/document/file_manager.py` and `tests/test_document.py`,
  then record concrete findings and choose the next bounded, tested batch.
- Resume: `git status --short && cat docs/refactoring-progress.md docs/refactoring-plan.md`
