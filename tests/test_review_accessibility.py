"""Test keyboard and accessible metadata for selection review dialogs."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAccessible
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.ai.models import Suggestion
from app.ui.auto_writer_review_dialog import AutoWriterReviewDialog
from app.ui.spellcheck_review_dialog import SpellcheckReviewDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("kind", ["draft", "finding"])
def test_review_lists_expose_instructions_and_support_keyboard_selection(app, kind):
    if kind == "draft":
        dialog = AutoWriterReviewDialog([("s1", "First", "Draft"), ("s2", "Second", "Later")])
        items = dialog.list
    else:
        dialog = SpellcheckReviewDialog([Suggestion(0, 3, "one"), Suggestion(4, 7, "two")], "eno owt")
        items = dialog.findings
    dialog.show()
    items.setFocus()
    items.setCurrentRow(0)
    app.processEvents()
    accessible = QAccessible.queryAccessibleInterface(items)
    assert accessible.text(QAccessible.Text.Name)
    assert "Space" in accessible.text(QAccessible.Text.Description)
    QTest.keyClick(items, Qt.Key.Key_Space)
    assert items.item(0).checkState() == Qt.CheckState.Unchecked
    QTest.keyClick(items, Qt.Key.Key_Down)
    assert items.currentRow() == 1
    QTest.keyClick(items, Qt.Key.Key_Space)
    assert items.item(1).checkState() == Qt.CheckState.Unchecked
    dialog.close()
