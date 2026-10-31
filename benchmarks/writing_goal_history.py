"""Measure writing-goal history during separate Qt editing commands.

Run from the repository root with:
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 .venv/bin/python benchmarks/writing_goal_history.py

Measurements are diagnostic, not portable pass/fail thresholds. The session
uses synthetic prose, temporary settings, and no running AI service.
"""

import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication

from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow


def main() -> None:
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory() as directory:
        settings_path = Path(directory) / "settings.yaml"
        with patch.object(AppSettings, "_default_settings_path", return_value=settings_path), \
                patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
            window = MainWindow()
        window.settings.ai_enabled = False
        window.writing_goals.configure(1000, "new_words")
        editor = window.tabs.current_editor()
        document_id = window._goal_document_id(editor)
        tracemalloc.start()
        started = time.perf_counter()
        words = ("The", "writer", "opened", "the", "door", "and", "noticed", "a", "familiar", "voice")
        for command in range(1, 1001):
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.beginEditBlock()
            cursor.insertText(" " + words[(command - 1) % len(words)])
            cursor.endEditBlock()
            if command in (100, 500, 1000):
                states, _ = window.writing_goals._histories[document_id]
                current, peak = tracemalloc.get_traced_memory()
                print(f"{command} commands: {len(states)} tracked states; "
                      f"Qt undo steps {editor.document().availableUndoSteps()}; "
                      f"Python traced current {current:,} bytes, peak {peak:,} bytes; "
                      f"elapsed {time.perf_counter() - started:.3f} s")
        before = window.writing_goals.count_new_words({document_id})
        for _ in range(100):
            editor.undo()
        after_undo = window.writing_goals.count_new_words({document_id})
        for _ in range(100):
            editor.redo()
        after_redo = window.writing_goals.count_new_words({document_id})
        print(f"New-word counts: before undo {before}, after 100 undo {after_undo}, "
              f"after 100 redo {after_redo}")
        if (before, after_undo, after_redo) != (1000, 900, 1000):
            raise AssertionError("Writing-goal counts did not follow the editing history.")
        tracemalloc.stop()
        editor.document_state.mark_saved()
        window.close()
        app.processEvents()


if __name__ == "__main__":
    main()
