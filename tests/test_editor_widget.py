import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtGui import QAction, QFontDatabase, QIcon, QPalette, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QPlainTextEdit

from app.document.document import Document
from app.document.text_formatting import indent_lines, outdent_lines
from app.ai.models import Suggestion
from app.ai.ollama_client import OllamaClient
from app.settings.settings import AppSettings
from app.ui.ai_debug_window import AIDebugWindow, MAX_DEBUG_EVENT_CHARS, MAX_DEBUG_EVENTS
from app.ui.editor_widget import EditorWidget
from app.ui.font_utils import configure_application_font, editor_font
from app.ui.main_window import MainWindow
from app.ui.settings_dialog import SettingsDialog
from app.ui.tab_widget import DocumentTabWidget
from app.ui.workers import FunctionWorker


@pytest.fixture(scope="module")
def application() -> QApplication:
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.yaml"
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    AppSettings(ui_language="en", ai_context_consent_host="http://localhost:11434").save(settings_path)


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


def test_closing_tab_releases_writing_goal_history(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    document_id = editor._writing_goal_document_id
    assert document_id in window.writing_goals._histories
    window.close_tab(window.tabs.currentIndex())
    assert document_id not in window.writing_goals._histories
    assert document_id not in window.writing_goals._current_text
    window.close()


def test_editor_colors_follow_the_system_palette(application: QApplication) -> None:
    editor = EditorWidget()
    editor.apply_settings(AppSettings())

    assert not editor.styleSheet()
    for role in (QPalette.ColorRole.Base, QPalette.ColorRole.Text):
        assert editor.palette().color(role) == application.palette().color(role)


def test_unavailable_editor_font_uses_installed_fixed_width_family(
    application: QApplication,
) -> None:
    font = editor_font("Monospace", 12)

    assert font.pointSize() == 12
    assert font.family().casefold() in {
        family.casefold() for family in QFontDatabase.families()
    }


def test_application_font_uses_an_installed_family_before_widgets_are_created(
    application: QApplication,
) -> None:
    configure_application_font(application)

    assert application.font().family().casefold() in {
        family.casefold() for family in QFontDatabase.families()
    }


def test_application_icon_loads_and_renders(application: QApplication) -> None:
    icon_path = Path(__file__).resolve().parents[1] / "app" / "resources" / "icon.svg"
    icon = QIcon(str(icon_path))

    assert not icon.isNull()
    assert not icon.pixmap(128, 128).isNull()


def test_completion_is_rejected_when_text_changes(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion(" world", editor.revision, editor.textCursor().position())

    editor.insertPlainText("!")

    assert not editor.has_completion
    assert editor.toPlainText() == "Hello!"


def test_completion_is_rejected_for_multiline_or_empty_suggestions(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)

    editor.show_completion("\nworld", editor.revision, editor.textCursor().position())
    assert not editor.has_completion

    editor.show_completion("   ", editor.revision, editor.textCursor().position())
    assert not editor.has_completion


def test_completion_does_not_cover_existing_text(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello world\nNext line")
    cursor = editor.textCursor()
    cursor.setPosition(5)
    editor.setTextCursor(cursor)
    editor.show_completion(" there", editor.revision, cursor.position())
    assert not editor.has_completion
    assert editor.toPlainText() == "Hello world\nNext line"

    cursor.setPosition(11)
    editor.setTextCursor(cursor)
    editor.show_completion(" there", editor.revision, cursor.position())
    assert editor.has_completion


def test_completion_is_invalidated_when_selection_changes_without_moving_cursor(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    position = editor.textCursor().position()
    editor.show_completion(" world", editor.revision, position)
    cursor = editor.textCursor()
    cursor.setPosition(position - 1)
    cursor.setPosition(position, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    assert not editor.has_completion


def test_accepting_a_word_completion_inserts_a_separating_space(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion("world", editor.revision, editor.textCursor().position())

    assert editor.accept_completion()
    assert editor.toPlainText() == "Hello world"


def test_completion_disappears_when_resizing_makes_it_unreadable(application: QApplication) -> None:
    editor = EditorWidget()
    editor.resize(700, 100)
    editor.show()
    application.processEvents()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion(" a fairly long suggestion", editor.revision, editor.textCursor().position())
    assert editor.has_completion
    editor.resize(70, 100)
    application.processEvents()
    assert not editor.has_completion
    assert editor.toPlainText() == "Hello"
    editor.close()


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


def test_spell_suggestions_change_text_only_after_explicit_replace(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("A sentense.")
    revision = editor.revision
    suggestion = Suggestion(2, 10, "sentence", original_text="sentense", revision=revision)

    editor.set_spell_suggestions([suggestion])

    assert editor.toPlainText() == "A sentense."
    assert editor.replace_spell_suggestion(suggestion)
    assert editor.toPlainText() == "A sentence."
    editor.undo()
    assert editor.toPlainText() == "A sentense."


def test_spellcheck_python_offsets_replace_correct_text_after_emoji(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("😀 sentense")
    suggestion = Suggestion(2, 10, "sentence", original_text="sentense", revision=editor.revision)
    editor.set_spell_suggestions([suggestion])

    assert editor.replace_spell_suggestion(suggestion)
    assert editor.toPlainText() == "😀 sentence"


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


def test_spell_suggestions_reject_offsets_inside_a_word(application: QApplication) -> None:
    editor = EditorWidget()
    editor.setPlainText("Вітя вступив у слюб з Оленою.")
    revision = editor.revision
    suggestions = [Suggestion(14, 18, "шлюб", original_text=" слю", revision=revision)]

    assert editor.apply_spell_suggestions(suggestions) == 0
    assert editor.toPlainText() == "Вітя вступив у слюб з Оленою."


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


def test_spellcheck_results_are_reviewed_without_automatic_edits(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("A sentense.")
    revision = editor.revision
    suggestion = Suggestion(2, 10, "sentence", original_text="sentense", revision=revision)

    window._apply_spellcheck_results(editor, revision, [suggestion])

    assert editor.toPlainText() == "A sentense."
    assert editor.spell_suggestions == [suggestion]
    editor.document_state.mark_saved()
    window.close()


def test_save_file_work_runs_in_worker_and_marks_saved_on_success(application: QApplication, tmp_path, monkeypatch) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    target = tmp_path / "draft.txt"
    editor.document_state.path = target
    editor.setPlainText("saved in background")
    loop = QEventLoop()
    results: list[bool] = []
    window._save_editor(editor, callback=lambda saved: (results.append(saved), loop.quit()))
    QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert results == [True]
    assert target.read_text(encoding="utf-8") == "saved in background"
    assert not editor.document_state.dirty
    window.close()


def test_open_file_work_runs_in_worker(application: QApplication, tmp_path, monkeypatch) -> None:
    target = tmp_path / "opened.txt"
    target.write_text("opened in background", encoding="utf-8")
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *_args: (str(target), ""))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    loop = QEventLoop()
    window.tabs.currentChanged.connect(lambda _index: loop.quit() if window.tabs.count() > 1 else None)
    window.open_document()
    QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert window.tabs.count() == 2
    assert window.tabs.current_editor().toPlainText() == "opened in background"
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


def test_cursor_movement_invalidates_a_debounced_completion_request(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Some text")
    window.ai_status = "AI: Generating..."
    window._completion_timer.start(1000)
    generation = window._completion_generation
    editor.moveCursor(QTextCursor.MoveOperation.End)

    assert not window._completion_timer.isActive()
    assert window._completion_generation > generation
    assert window.ai_status != "AI: Generating..."
    editor.document_state.mark_saved()
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


def test_debug_history_is_bounded_in_memory_and_in_open_window(application: QApplication) -> None:
    window = MainWindow()
    window.show_ai_debug()
    for index in range(MAX_DEBUG_EVENTS + 1):
        window._record_ai_interaction("Response", "/test", {"index": index, "text": "x" * (MAX_DEBUG_EVENT_CHARS + 10)})

    assert len(window._debug_events) == MAX_DEBUG_EVENTS
    assert all(len(entry) <= MAX_DEBUG_EVENT_CHARS for entry in window._debug_events)
    displayed = window._debug_window.output.toPlainText()
    assert displayed == "\n".join(window._debug_events)
    assert '"index": 0' not in displayed
    assert '"index": 100' in displayed
    assert "diagnostic event truncated" in displayed

    window._debug_window.clear()
    assert window._debug_events == []
    assert window._debug_window.output.toPlainText() == ""
    window._debug_window.close()
    window.show_ai_debug()
    assert window._debug_window.output.toPlainText() == ""
    window.close()


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
    with patch(
        "app.ui.main_window.GeneratedTextDialog.exec",
        return_value=QDialog.DialogCode.Accepted,
    ):
        window._apply_generated_text(7, editor, " text")

    assert editor.toPlainText() == "Start text"
    editor.document_state.dirty = False
    window.close()


def test_generated_text_is_not_inserted_without_explicit_acceptance(
    application: QApplication,
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Start")
    revision = editor.revision
    cursor = editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    editor.setTextCursor(cursor)
    window._generate_generation = 7
    with patch(
        "app.ui.main_window.GeneratedTextDialog.exec",
        return_value=QDialog.DialogCode.Rejected,
    ):
        window._apply_generated_text(
            7,
            editor,
            " generated",
            revision,
            cursor.position(),
            (cursor.position(), cursor.position()),
            window._settings_generation,
        )

    assert editor.toPlainText() == "Start"
    editor.document_state.mark_saved()
    window.close()


def test_prompt_generation_can_be_cancelled_from_the_ai_menu(
    application: QApplication,
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    class PendingWorker:
        cancelled = False

        def cancel(self):
            self.cancelled = True

    worker = PendingWorker()
    window._generate_worker = worker
    window._generate_generation = 3
    window.ai_status = "AI: Generating..."
    window._generate_cancel_action.setEnabled(True)

    window.cancel_text_generation()

    assert worker.cancelled
    assert window._generate_generation == 4
    assert not window._generate_cancel_action.isEnabled()
    assert window.ai_status == "AI: Offline"
    window._generate_worker = None
    window.close()


def test_settings_dialog_groups_preferences_and_checks_connection(application: QApplication) -> None:
    dialog = SettingsDialog(AppSettings())
    requests = []
    dialog.connection_test_requested.connect(
        lambda host, model: requests.append((host, model))
    )

    dialog.test_connection_button.click()
    dialog.set_connection_test_result(False, "example-model")

    assert requests == [("http://localhost:11434", "gemma4:12b")]
    assert "ollama pull example-model" in dialog.connection_status.text()
    dialog.font_size.setValue(18)
    dialog.reset_button.click()
    assert dialog.font_size.value() == AppSettings().font_size
    assert dialog.host.text() == AppSettings().ollama_host
    dialog.close()


def test_settings_dialog_saves_automatic_project_context_choice(application: QApplication) -> None:
    settings = AppSettings()
    dialog = SettingsDialog(settings)
    dialog.automatic_project_context.setChecked(False)
    dialog.accept()
    assert settings.automatic_project_context is False


def test_text_formatting_actions_transform_selected_text_undoably(
    application: QApplication,
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("keep this\nmake this upper")
    cursor = editor.textCursor()
    cursor.setPosition(10)
    cursor.setPosition(len(editor.toPlainText()), QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)

    window._format_text("upper")

    assert editor.toPlainText() == "keep this\nMAKE THIS UPPER"
    assert editor.textCursor().selectedText() == "MAKE THIS UPPER"
    editor.undo()
    assert editor.toPlainText() == "keep this\nmake this upper"
    editor.document_state.mark_saved()
    window.close()


def test_edit_menu_contains_plain_text_formatting_tools(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    edit_menu = next(
        action.menu()
        for action in window.menuBar().actions()
        if action.text() == "Edit"
    )
    formatting_menu = next(
        action.menu() for action in edit_menu.actions() if action.text() == "Text Formatting"
    )

    assert {
        action.text() for action in formatting_menu.actions()
    } == {
        "Format Whole Document…",
        "Uppercase",
        "lowercase",
        "Title Case",
        "Indent Lines",
        "Outdent Lines",
        "Trim Trailing Whitespace",
    }
    window.close()


def test_format_whole_document_uses_chosen_operation_and_is_undoable(
    application: QApplication, monkeypatch
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("first  \nsecond \n")
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda *_args, **_kwargs: ("Trim Trailing Whitespace", True),
    )

    window._format_whole_document()

    assert editor.toPlainText() == "first\nsecond\n"
    editor.undo()
    assert editor.toPlainText() == "first  \nsecond \n"
    editor.document_state.mark_saved()
    window.close()


def test_format_whole_document_like_book_indents_paragraphs_undoably(
    application: QApplication, monkeypatch
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Opening line\ncontinued line\n\nNext paragraph\n")

    choices = []

    def choose_book_style(_parent, _title, _label, operations, *_args, **_kwargs):
        choices.extend(operations)
        return "Like in the book", True

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        choose_book_style,
    )

    window._format_whole_document()

    assert "Like in the book" in choices
    assert editor.toPlainText() == (
        "    Opening line\ncontinued line\n\n    Next paragraph\n"
    )
    editor.undo()
    assert editor.toPlainText() == "Opening line\ncontinued line\n\nNext paragraph\n"
    editor.document_state.mark_saved()
    window.close()


def test_line_formatting_operates_on_current_line_and_is_undoable(
    application: QApplication,
) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("first\nsecond")

    window._format_lines(indent_lines)
    assert editor.toPlainText() == "    first\nsecond"
    editor.undo()
    assert editor.toPlainText() == "first\nsecond"

    window._format_lines(outdent_lines)
    assert editor.toPlainText() == "first\nsecond"
    editor.document_state.mark_saved()
    window.close()


def test_ai_settings_action_is_in_settings_menu(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True), patch.object(MainWindow, "show_settings") as show_settings:
        window = MainWindow()

    ai_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "AI")
    settings_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "Settings")
    settings = next(action for action in settings_menu.actions() if action.text() == "AI Settings…")

    assert all(action.text() != "AI Settings…" for action in ai_menu.actions())
    assert settings.menuRole() == QAction.MenuRole.NoRole
    settings.trigger()
    show_settings.assert_called_once()
    window.close()


def test_distraction_free_mode_can_be_exited_without_changing_document(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Draft text")
    before = editor.toPlainText()

    window._set_focus_mode(True)

    assert window.menuBar().isHidden()
    assert not window._exit_focus_button.isHidden()
    assert window.status.currentMessage().startswith("Untitled *")

    QTest.keyClick(editor, Qt.Key.Key_Escape)

    assert not window._focus_mode
    assert not window.menuBar().isHidden()
    assert window._exit_focus_button.isHidden()
    assert editor.toPlainText() == before
    editor.document_state.mark_saved()
    window.close()


def test_escape_dismisses_completion_before_exiting_distraction_free_mode(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Draft")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    editor.show_completion(" text", editor.revision, editor.textCursor().position())
    window._set_focus_mode(True)

    QTest.keyClick(editor, Qt.Key.Key_Escape)

    assert not editor.has_completion
    assert window._focus_mode

    QTest.keyClick(editor, Qt.Key.Key_Escape)

    assert not window._focus_mode
    editor.document_state.mark_saved()
    window.close()


def test_daily_new_words_goal_tracks_typing_undo_and_redo(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    assert editor is not None
    window.writing_goals.configure(3, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    editor.insertPlainText("Hello world")
    document_id = editor._writing_goal_document_id

    assert window.writing_goals.count_new_words({document_id}) == 2
    assert window._writing_goal_label.text().endswith("2/3")

    editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 0
    editor.redo()
    assert window.writing_goals.count_new_words({document_id}) == 2

    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()


def test_writing_goal_compacts_merged_qt_commands_and_keeps_undo_branches(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    window.writing_goals.configure(1000, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    document_id = editor._writing_goal_document_id
    for character in "one two three":
        editor.insertPlainText(character)
    assert len(window.writing_goals._histories[document_id][0]) == 2
    assert window.writing_goals.count_new_words({document_id}) == 3
    editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 0
    editor.redo()
    assert window.writing_goals.count_new_words({document_id}) == 3

    editor.moveCursor(QTextCursor.MoveOperation.Start)
    editor.insertPlainText("four ")
    assert window.writing_goals.count_new_words({document_id}) == 4
    editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 3
    editor.insertPlainText("five ")
    assert window.writing_goals.count_new_words({document_id}) == 4
    editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 3
    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()


def test_writing_goal_releases_states_when_qt_clears_undo_history(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    window.writing_goals.configure(100, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    document_id = editor._writing_goal_document_id
    editor.insertPlainText("one two")
    editor.setPlainText("replacement")
    states, index = window.writing_goals._histories[document_id]
    assert len(states) == 1 and index == 0
    assert not editor.document().isUndoAvailable()
    assert window.writing_goals.count_new_words({document_id}) == 3
    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()


def test_writing_goal_long_merged_typing_session_has_two_states(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    window.writing_goals.configure(1000, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    document_id = editor._writing_goal_document_id
    for _ in range(1200):
        editor.insertPlainText("x")
    assert len(window.writing_goals._histories[document_id][0]) == 2
    assert window.writing_goals.count_new_words({document_id}) == 1
    editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 0
    editor.redo()
    assert window.writing_goals.count_new_words({document_id}) == 1
    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()


def test_writing_goal_tracks_native_qt_undo_and_redo_slots(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    window.writing_goals.configure(10, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    document_id = editor._writing_goal_document_id
    editor.insertPlainText("one two")
    QPlainTextEdit.undo(editor)
    assert window.writing_goals.count_new_words({document_id}) == 0
    QPlainTextEdit.redo(editor)
    assert window.writing_goals.count_new_words({document_id}) == 2
    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()


def test_writing_goal_many_independent_commands_undo_and_redo(application: QApplication) -> None:
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    window.writing_goals.configure(1000, "new_words")
    window._attach_writing_goal_document(editor, reset_history=True)
    document_id = editor._writing_goal_document_id
    for _ in range(120):
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.insertText("word ")
        cursor.endEditBlock()
    assert window.writing_goals.count_new_words({document_id}) == 120
    for _ in range(120):
        editor.undo()
    assert window.writing_goals.count_new_words({document_id}) == 0
    for _ in range(120):
        editor.redo()
    assert window.writing_goals.count_new_words({document_id}) == 120
    editor.document_state.mark_saved()
    window._writing_goal_persist_timer.stop()
    window.close()
