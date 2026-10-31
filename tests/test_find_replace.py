import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor

from app.i18n import install_translation
from app.ui.editor_widget import EditorWidget
from app.ui.find_replace import FindReplaceWidget


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication([])
    _, translator = install_translation(app, "en")
    yield app
    if translator is not None:
        app.removeTranslator(translator)


def make_find_bar(editor):
    widget = FindReplaceWidget(lambda: editor)
    widget.find_edit.setText("word")
    return widget


def test_find_bar_counts_matches_and_navigates_in_both_directions(application):
    editor = EditorWidget()
    editor.setPlainText("word one word two word")
    find_bar = make_find_bar(editor)

    assert find_bar.match_count.text() == "3 matches"
    assert find_bar.find_next()
    assert editor.textCursor().selectedText() == "word"
    assert find_bar.find_next()
    assert editor.textCursor().selectedText() == "word"
    assert find_bar.find_previous()
    assert editor.textCursor().selectionStart() == 0

    find_bar.hide()


def test_replace_replaces_next_match_and_selects_the_following_match(application):
    editor = EditorWidget()
    editor.setPlainText("word word")
    find_bar = make_find_bar(editor)
    find_bar.replace_edit.setText("line")

    find_bar.replace_one()

    assert editor.toPlainText() == "line word"
    assert editor.textCursor().selectedText() == "word"
    assert find_bar.match_count.text() == "1 match"
    assert "Selected the next match" in find_bar.message.text()

    find_bar.hide()


def test_replace_all_is_one_undoable_edit(application):
    editor = EditorWidget()
    editor.setPlainText("word word")
    find_bar = make_find_bar(editor)
    find_bar.replace_edit.setText("line")

    find_bar.replace_all()

    assert editor.toPlainText() == "line line"
    assert find_bar.message.text() == "Replaced 2 matches."
    editor.undo()
    assert editor.toPlainText() == "word word"

    find_bar.hide()


def test_case_and_whole_word_options_keep_counts_navigation_and_replacement_consistent(application):
    editor = EditorWidget()
    editor.setPlainText("😀 СЛОВО слово словом слово")
    bar = make_find_bar(editor)
    bar.find_edit.setText("слово")
    assert bar.match_count.text() == "3 matches"
    bar.case_sensitive.setChecked(False)
    assert bar.match_count.text() == "4 matches"
    bar.whole_word.setChecked(True)
    assert bar.match_count.text() == "3 matches"
    editor.moveCursor(QTextCursor.MoveOperation.Start)
    assert bar.find_next()
    assert editor.textCursor().selectedText() == "СЛОВО"
    bar.replace_edit.setText("текст")
    bar.replace_all()
    assert editor.toPlainText() == "😀 текст текст словом текст"
    editor.undo()
    assert editor.toPlainText() == "😀 СЛОВО слово словом слово"


def test_large_case_insensitive_count_yields_and_discards_old_query(application):
    editor = EditorWidget()
    editor.setPlainText("Word " * 3000)
    bar = make_find_bar(editor)
    bar.case_sensitive.setChecked(False)
    assert bar.match_count.text() == "Counting matches…"
    event = []
    QTimer.singleShot(0, lambda: event.append(True))
    for _ in range(100):
        application.processEvents()
        if bar.match_count.text() == "3000 matches":
            break
    assert event and bar.match_count.text() == "3000 matches"
    bar.find_edit.setText("Word")
    assert bar.match_count.text() == "Counting matches…"
    bar.find_edit.setText("missing")
    application.processEvents()
    assert bar.match_count.text() == "0 matches"
    assert editor.toPlainText() == "Word " * 3000


def test_large_count_is_replaced_when_active_editor_changes(application):
    first, second = EditorWidget(), EditorWidget()
    first.setPlainText("Word " * 3000)
    second.setPlainText("WORD")
    current = [first]
    bar = FindReplaceWidget(lambda: current[0])
    bar.case_sensitive.setChecked(False)
    bar.find_edit.setText("word")
    assert bar.match_count.text() == "Counting matches…"
    current[0] = second
    bar.refresh()
    application.processEvents()
    assert bar.match_count.text() == "1 match"


def test_whole_word_replace_does_not_replace_partial_selection(application):
    editor = EditorWidget()
    editor.setPlainText("wording word")
    bar = make_find_bar(editor)
    bar.whole_word.setChecked(True)
    cursor = editor.textCursor()
    cursor.setPosition(0)
    cursor.setPosition(4, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    bar.replace_edit.setText("line")
    bar.replace_one()
    assert editor.toPlainText() == "wording line"


def test_no_match_and_noop_replace_preserve_text_and_undo(application):
    editor = EditorWidget()
    editor.setPlainText("word")
    bar = make_find_bar(editor)
    bar.replace_edit.setText("word")
    bar.replace_all()
    assert editor.toPlainText() == "word"
    assert not editor.document().isUndoAvailable()
    bar.find_edit.setText("missing")
    bar.replace_all()
    assert editor.toPlainText() == "word"


def test_find_replace_focus_and_close_return_to_editor(application, monkeypatch, tmp_path):
    from unittest.mock import patch
    from app.settings.settings import AppSettings
    from app.ui.main_window import MainWindow
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: tmp_path / "settings.yaml"))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.show()
    search_menu = next(action.menu() for action in window.menuBar().actions() if action.text() == "Search")
    next(action for action in search_menu.actions() if action.text() == "Find").trigger()
    application.processEvents()
    assert window._find_bar.find_edit.hasFocus()
    next(action for action in search_menu.actions() if action.text() == "Replace").trigger()
    application.processEvents()
    assert window._find_bar.replace_edit.hasFocus()
    window._find_bar.close_find()
    application.processEvents()
    assert window.tabs.current_editor().hasFocus()
    window.close()


def test_status_message_does_not_force_find_bar_wider_than_small_window(application):
    editor = EditorWidget()
    bar = make_find_bar(editor)
    bar.message.setText("Replaced 1 match. Selected the next match.")
    bar.resize(420, 150)
    bar.show()
    application.processEvents()
    assert bar.width() <= 420
    assert bar.next_button.isVisible() and bar.replace_all_button.isVisible()
    bar.close()


@pytest.mark.parametrize("backwards", [False, True])
@pytest.mark.parametrize("anchor,position", [(1, 5), (5, 1), (3, 3)])
def test_failed_find_preserves_cursor_and_selection(application, backwards, anchor, position):
    editor = EditorWidget()
    editor.setPlainText("a😀bc def")
    cursor = editor.textCursor()
    cursor.setPosition(anchor)
    cursor.setPosition(position, QTextCursor.MoveMode.KeepAnchor)
    editor.setTextCursor(cursor)
    bar = make_find_bar(editor)
    bar.find_edit.setText("missing")

    assert not bar._find(backwards=backwards)
    assert (editor.textCursor().anchor(), editor.textCursor().position()) == (anchor, position)
