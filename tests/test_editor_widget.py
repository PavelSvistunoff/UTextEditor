import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtWidgets import QApplication

from app.document.document import Document
from app.ai.models import Suggestion
from app.ai.ollama_client import OllamaClient
from app.settings.settings import AppSettings
from app.ui.ai_debug_window import AIDebugWindow
from app.ui.editor_widget import EditorWidget
from app.ui.main_window import MainWindow
from app.ui.tab_widget import DocumentTabWidget
from app.ui.workers import FunctionWorker


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_editor_widget_applies_editor_preferences(application: QApplication) -> None:
    editor = EditorWidget()
    settings = AppSettings(font_family="Courier", font_size=16, tab_width=2, word_wrap=True, show_line_numbers=False, dark_mode=True)

    editor.apply_settings(settings)

    assert editor.font().family() == "Courier"
    assert editor.font().pointSize() == 16
    assert editor.lineWrapMode() == editor.LineWrapMode.WidgetWidth
    assert editor.tabStopDistance() > 0
    assert editor.viewportMargins().left() == 0


def test_line_numbers_are_painted_in_the_editor_margin(application: QApplication, monkeypatch) -> None:
    editor = EditorWidget()
    editor.apply_settings(AppSettings(show_line_numbers=True, dark_mode=True))
    editor.setPlainText("one\ntwo\nthree")

    updates: list[bool] = []
    monkeypatch.setattr(editor._line_number_area, "update", lambda: updates.append(True))

    editor._paint_line_numbers()

    assert updates == [True]
    assert editor._line_number_area.width() > 0


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


def test_spell_suggestions_render_underlines_without_crashing(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("A sentense and eror.")
    suggestions = [
        Suggestion(2, 10, "sentence", original_text="sentense", revision=editor.revision),
        Suggestion(15, 19, "error", original_text="eror", revision=editor.revision),
    ]

    editor.set_spell_suggestions(suggestions)

    assert len(editor.extraSelections()) == 2


def test_spell_suggestions_preserve_adjacent_spaces(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("шоб шо")
    revision = editor.revision
    suggestions = [Suggestion(0, 4, "щоб", original_text="шоб ", revision=revision)]

    assert editor.apply_spell_suggestions(suggestions) == 1
    assert editor.toPlainText() == "щоб шо"


def test_spell_suggestions_expand_to_full_word_when_model_replaces_only_a_suffix(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("вітя вступив у слюб з оленою")
    revision = editor.revision
    suggestions = [Suggestion(15, 19, "шлюб", original_text="слюб", revision=revision)]

    assert editor.apply_spell_suggestions(suggestions) == 1
    assert editor.toPlainText() == "вітя вступив у шлюб з оленою"


def test_spell_suggestions_handle_space_padded_offsets_from_the_model(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Вітя вступив у слюб з Оленою.")
    revision = editor.revision
    suggestions = [Suggestion(14, 18, "шлюб", original_text=" слю", revision=revision)]

    assert editor.apply_spell_suggestions(suggestions) == 1
    assert editor.toPlainText() == "Вітя вступив у шлюб з Оленою."


def test_stale_ai_observer_does_not_crash_on_deleted_signal_source(application: QApplication) -> None:
    def stale_observer(*_args, **_kwargs) -> None:
        raise RuntimeError("Signal source has been deleted")

    client = OllamaClient(interaction_observer=stale_observer)

    client._observe("Request", "/api/chat", {"model": "test"})


def test_main_window_keeps_worker_references_until_signals_finish(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    worker = FunctionWorker(lambda: "done")
    window._track_worker(worker)

    assert worker in window._workers
    window._drop_worker(worker)
    assert worker not in window._workers
    window.close()


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


def test_generate_action_is_present_in_the_ai_menu(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    ai_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "AI")
    generate_action = next(action for action in ai_menu.actions() if action.text() == "Generate..")

    assert generate_action is not None
    window.close()


def test_generated_text_is_inserted_into_the_current_document(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Start")
    cursor = editor.textCursor()
    cursor.setPosition(5)
    editor.setTextCursor(cursor)
    window._generate_generation = 7
    window._apply_generated_text(7, editor, " text")

    assert editor.toPlainText() == "Start text"
    editor.document_state.dirty = False
    window.close()


def test_ai_settings_action_stays_in_the_ai_menu(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    ai_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "AI")
    settings = next(action for action in ai_menu.actions() if action.text() == "AI Settings…")

    assert settings.menuRole() == QAction.MenuRole.NoRole
    window.close()
