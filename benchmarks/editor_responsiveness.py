"""Measure representative editor operations on the Qt GUI thread, offline.

Run with QT_QPA_PLATFORM=offscreen .venv/bin/python benchmarks/editor_responsiveness.py.
Results are descriptive, not portable pass/fail thresholds.
"""

import resource
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
    return max(samples)


def main():
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with patch.object(AppSettings, "_default_settings_path", return_value=root / "settings.yaml"), \
                patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
            window = MainWindow()
        window.settings.ai_enabled = False
        window.writing_goals.configure(1000, "new_words")
        for size in (100_000, 1_000_000):
            paragraph = "The archivist examined the papers and searched for a forgotten name.\n\n"
            text = (paragraph * (size // len(paragraph) + 1))[:size]
            path = root / f"{size}.txt"
            path.write_text(text, encoding="utf-8")
            opened = []
            read_ms = elapsed_ms(lambda: opened.append(window.file_manager.open(path)))
            ui_open_ms = elapsed_ms(lambda: window._opened_document(opened[0]))
            editor = window.tabs.current_editor()
            editor.moveCursor(QTextCursor.MoveOperation.End)
            typing_ms = elapsed_ms(lambda: editor.insertPlainText(" word"), 5)
            cursor_ms = elapsed_ms(lambda: editor.moveCursor(QTextCursor.MoveOperation.Left), 5)
            search_ms = elapsed_ms(lambda: editor.document().find("forgotten"), 5)
            words_ms = elapsed_ms(lambda: count_words(editor.toPlainText()), 5)
            context_ms = elapsed_ms(lambda: build_context(editor.toPlainText(), size // 2), 5)
            print(f"{size:,} characters: file read {read_ms:.2f} ms, GUI open {ui_open_ms:.2f} ms, "
                  f"typing {typing_ms:.2f} ms, cursor {cursor_ms:.2f} ms, search {search_ms:.2f} ms, "
                  f"word count {words_ms:.2f} ms, context {context_ms:.2f} ms; "
                  f"process peak RSS {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss} "
                  f"({'bytes' if sys.platform == 'darwin' else 'KiB'})")
            editor.document_state.mark_saved()
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
