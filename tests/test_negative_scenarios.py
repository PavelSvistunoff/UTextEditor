import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from app.ai.completion_service import CompletionService
from app.ui.find_replace import FindReplaceWidget
from app.ui.main_window import MainWindow


class ExplodingProvider:
    def complete(self, context: str, language: str, **kwargs):
        raise RuntimeError("provider failure")

    def check_spelling(self, text: str, language: str):
        return []

    def check_connection(self):
        return False


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_completion_service_propagates_provider_exceptions():
    provider = ExplodingProvider()
    service = CompletionService(provider)

    with pytest.raises(RuntimeError):
        service.complete("ctx", "en")


def test_find_replace_widget_handles_no_editor_and_empty_find(application: QApplication):
    # Editor provider returns None
    widget = FindReplaceWidget(lambda: None, None)

    # Should not raise when invoked without an editor
    widget.find_next()
    widget.replace_one()
    widget.replace_all()

    # If no exception was raised the widget behaved safely for negative scenarios
    assert True


def test_main_window_cancels_pending_ai_on_close(application: QApplication):
    window = MainWindow.__new__(MainWindow)
    window._completion_timer = QTimer()
    window._spellcheck_timer = QTimer()

    class DummyWorker:
        def __init__(self):
            self.cancelled = False

        def cancel(self):
            self.cancelled = True

    worker = DummyWorker()
    window._workers = [worker]
    window._completion_generation = 0
    window._generate_generation = 0
    window._settings_generation = 0
    window._closing_confirmed = True

    window._completion_timer.start(500)
    window._spellcheck_timer.start(500)
    window.closeEvent(QCloseEvent())

    assert worker.cancelled is True
    assert not window._completion_timer.isActive()
    assert not window._spellcheck_timer.isActive()
