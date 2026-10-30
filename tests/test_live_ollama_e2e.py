"""Opt-in desktop-to-Ollama smoke test; uses synthetic text only."""

import os

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QApplication, QInputDialog

from app.settings.settings import AppSettings
from app.ui.generated_text_dialog import GeneratedTextDialog
from app.ui.main_window import MainWindow


pytestmark = [
    pytest.mark.live_ollama,
    pytest.mark.skipif(
        os.environ.get("UTEXTEDITOR_LIVE_AI") != "1",
        reason="Set UTEXTEDITOR_LIVE_AI=1 to run against the configured Ollama server",
    ),
]


def test_real_ollama_generation_is_reviewed_and_undoable(tmp_path, monkeypatch):
    """Send a synthetic prompt through the UI, worker, provider, and review dialog."""
    settings = AppSettings.load()
    settings.ai_enabled = True
    settings.completion_enabled = False
    settings.automatic_spellcheck = False
    settings.maximum_suggestion_length = 128
    settings.ui_language = "en"
    settings_path = tmp_path / "settings.yaml"
    settings.save(settings_path)
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: settings_path))
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.provider.timeout = 300
    editor = window.tabs.current_editor()
    editor.setPlainText("Synthetic test: ")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    original = editor.toPlainText()
    reviewed = []
    monkeypatch.setattr(
        QInputDialog, "getMultiLineText",
        lambda *_args: ("Write one short sentence about a red kite in the sky.", True),
    )
    original_exec = GeneratedTextDialog.exec

    def review(dialog):
        reviewed.append(dialog.output.toPlainText())
        assert editor.toPlainText() == original
        QTimer.singleShot(0, dialog.insert_button.click)
        return original_exec(dialog)

    monkeypatch.setattr(GeneratedTextDialog, "exec", review)
    try:
        window.generate_from_prompt()
        loop = QEventLoop()
        poll = QTimer()
        poll.timeout.connect(lambda: loop.quit() if window._generate_worker is None else None)
        deadline = QTimer()
        deadline.setSingleShot(True)
        deadline.timeout.connect(loop.quit)
        poll.start(20)
        deadline.start(305_000)
        if window._generate_worker is not None:
            loop.exec()
        poll.stop()
        assert window._generate_worker is None, "Ollama generation did not finish within 305 seconds"
        assert reviewed and reviewed[0].strip(), (
            f"No generated text reached review. AI status: {window.ai_status}; "
            f"message: {window.status.currentMessage()}"
        )
        assert editor.toPlainText() == original + reviewed[0]
        editor.undo()
        assert editor.toPlainText() == original
    finally:
        if window._generate_worker is not None:
            window.cancel_text_generation()
        editor.document_state.mark_saved()
        window.close()
