"""Measure representative editor operations on the Qt GUI thread, offline.

Run with QT_QPA_PLATFORM=offscreen .venv/bin/python benchmarks/editor_responsiveness.py.
Results are descriptive, not portable pass/fail thresholds.
"""

import argparse
import statistics
try:
    import resource
except ImportError:
    resource = None
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from app.ai.completion_service import build_context
from app.project import count_words
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow


def elapsed_ms(operation, repetitions=1):
    samples = []
    for _ in range(repetitions):
        start = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - start) * 1000)
    return f"median {statistics.median(samples):.2f}/max {max(samples):.2f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=[100_000, 1_000_000])
    parser.add_argument("--repetitions", type=int, default=5)
    args = parser.parse_args()
    if args.repetitions < 1 or any(size < 1 for size in args.sizes):
        parser.error("sizes and repetitions must be positive")
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with patch.object(AppSettings, "_default_settings_path", return_value=root / "settings.yaml"), \
                patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
            window = MainWindow()
        window.settings.ai_enabled = False
        window.writing_goals.configure(1000, "new_words")
        for size in args.sizes:
            paragraph = "The archivist examined the papers and searched for a forgotten name.\n\n"
            text = (paragraph * (size // len(paragraph) + 1))[:size]
            path = root / f"{size}.txt"
            path.write_text(text, encoding="utf-8")
            opened = []
            read_ms = elapsed_ms(lambda: opened.append(window.file_manager.open(path)))
            ui_open_ms = elapsed_ms(lambda: window._opened_document(opened[0]))
            editor = window.tabs.current_editor()
            editor.moveCursor(QTextCursor.MoveOperation.End)
            typing_ms = elapsed_ms(lambda: editor.insertPlainText(" word"), args.repetitions)
            cursor_ms = elapsed_ms(lambda: editor.moveCursor(QTextCursor.MoveOperation.Left), args.repetitions)
            search_ms = elapsed_ms(lambda: editor.document().find("forgotten"), args.repetitions)
            words_ms = elapsed_ms(lambda: count_words(editor.toPlainText()), args.repetitions)
            context_ms = elapsed_ms(lambda: build_context(editor.toPlainText(), size // 2), args.repetitions)
            memory = (f"{resource.getrusage(resource.RUSAGE_SELF).ru_maxrss} "
                      f"({'bytes' if sys.platform == 'darwin' else 'KiB'})"
                      if resource is not None else "unavailable on this platform")
            print(f"{size:,} characters ({args.repetitions} samples for repeated operations): file read {read_ms} ms, GUI open {ui_open_ms} ms, "
                  f"typing {typing_ms} ms, cursor {cursor_ms} ms, search {search_ms} ms, "
                  f"word count {words_ms} ms, context {context_ms} ms; "
                  f"process peak RSS {memory}")
            editor.document_state.mark_saved()
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
