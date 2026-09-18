import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import QApplication

from app.document.document import Document
from app.ai.models import Suggestion
from app.ui.ai_debug_window import AIDebugWindow
from app.ui.editor_widget import EditorWidget
from app.ui.main_window import MainWindow
from app.ui.tab_widget import DocumentTabWidget


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_completion_is_non_destructive_and_tab_accepts_it(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion(" world", editor.revision, editor.textCursor().position())

    assert editor.has_completion
    assert editor.toPlainText() == "Hello"
    assert editor.accept_completion()
    assert editor.toPlainText() == "Hello world"
    assert not editor.has_completion


def test_completion_is_rejected_when_text_changes(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion(" world", editor.revision, editor.textCursor().position())

    editor.insertPlainText("!")

    assert not editor.has_completion
    assert editor.toPlainText() == "Hello!"


def test_accepting_a_word_completion_inserts_a_separating_space(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion("world", editor.revision, editor.textCursor().position())

    assert editor.accept_completion()
    assert editor.toPlainText() == "Hello world"


def test_spell_suggestions_apply_in_one_undoable_operation(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("A sentense and eror.")
    revision = editor.revision
    suggestions = [
        Suggestion(2, 10, "sentence", original_text="sentense", revision=revision),
        Suggestion(15, 19, "error", original_text="eror", revision=revision),
    ]

    assert editor.apply_spell_suggestions(suggestions) == 2
    assert editor.toPlainText() == "A sentence and error."
    editor.undo()
    assert editor.toPlainText() == "A sentense and eror."


def test_tabs_keep_document_state_isolated_and_delegate_close(application: QApplication) -> None:
    tabs = DocumentTabWidget()
    first = tabs.add_document(Document.from_text("first"))
    second = tabs.add_document(Document.from_text("second"))
    requested: list[int] = []
    tabs.close_requested.connect(requested.append)

    first.insertPlainText("!")
    tabs.tabCloseRequested.emit(0)

    assert first.document_state.text == "!first"
    assert second.document_state.text == "second"
    assert requested == [0]
    assert tabs.count() == 2


def test_empty_completion_returns_to_connected_without_an_error(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    window._completion_generation = 4
    window.ai_status = "AI: Generating..."

    window._completion_finished(4, editor, editor.revision, editor.textCursor().position(), "  \n")

    assert window.ai_status == "AI: Connected"
    assert "AI completion failed" not in window.status.currentMessage()
    window.close()


def test_ollama_debug_window_displays_in_memory_interactions(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    window._record_ai_interaction("Request", "/api/generate", {"model": "test"})
    window.show_ai_debug()

    assert window._debug_window is not None
    assert "Request /api/generate" in window._debug_window.output.toPlainText()
    assert '"model": "test"' in window._debug_window.output.toPlainText()
    window.close()


def test_ollama_debug_window_copies_its_content(application: QApplication) -> None:
    debug_window = AIDebugWindow()
    debug_window.append_interaction("Response", "/api/generate", {"response": "done"})

    debug_window.copy_to_clipboard()

    assert QApplication.clipboard().text() == debug_window.output.toPlainText()


def test_ai_settings_action_stays_in_the_ai_menu(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    ai_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "AI")
    settings = next(action for action in ai_menu.actions() if action.text() == "AI Settings…")

    assert settings.menuRole() == QAction.MenuRole.NoRole
    window.close()
