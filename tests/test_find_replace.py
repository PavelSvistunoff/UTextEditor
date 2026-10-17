import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from app.ui.editor_widget import EditorWidget
from app.ui.find_replace import FindReplaceWidget


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


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
