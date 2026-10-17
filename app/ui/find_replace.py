"""Compact find/replace controls for the active editor."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FindReplaceWidget(QWidget):
    def __init__(self, editor_provider, parent=None) -> None:
        super().__init__(parent)
        self.editor_provider = editor_provider
        self.find_edit = QLineEdit(self)
        self.find_edit.setPlaceholderText("Find")
        self.find_edit.setAccessibleName("Find text")
        self.replace_edit = QLineEdit(self)
        self.replace_edit.setPlaceholderText("Replace with")
        self.replace_edit.setAccessibleName("Replace with")
        self.previous_button = QPushButton("Previous", self)
        self.next_button = QPushButton("Next", self)
        self.replace_button = QPushButton("Replace", self)
        self.replace_all_button = QPushButton("Replace All", self)
        self.close_button = QPushButton("Close", self)
        self.match_count = QLabel("0 matches", self)
        self.match_count.setAccessibleName("Find match count")
        self.message = QLabel(self)
        self.message.setAccessibleName("Find and replace status")

        self.previous_button.clicked.connect(self.find_previous)
        self.next_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_one)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.hide)
        self.find_edit.textChanged.connect(self._update_match_count)
        self.find_edit.returnPressed.connect(self.find_next)

        find_row = QHBoxLayout()
        for widget in (
            self.find_edit,
            self.previous_button,
            self.next_button,
            self.match_count,
            self.message,
            self.close_button,
        ):
            find_row.addWidget(widget)
        find_row.setStretchFactor(self.find_edit, 2)
        find_row.setStretchFactor(self.message, 1)

        replace_row = QHBoxLayout()
        replace_row.addWidget(self.replace_edit, 2)
        replace_row.addWidget(self.replace_button)
        replace_row.addWidget(self.replace_all_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addLayout(find_row)
        layout.addLayout(replace_row)

        for sequence, handler in (
            ("F3", self.find_next),
            ("Shift+F3", self.find_previous),
            ("Escape", self.hide),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(handler)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def find_next(self) -> bool:
        return self._find(backwards=False)

    def find_previous(self) -> bool:
        return self._find(backwards=True)

    def _find(self, *, backwards: bool) -> bool:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText("Enter text to find.")
            return False

        cursor = editor.textCursor()
        start = cursor.selectionStart() if backwards and cursor.hasSelection() else (
            cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        )
        cursor.setPosition(start)
        editor.setTextCursor(cursor)
        flags = QTextDocument.FindFlag.FindCaseSensitively
        if backwards:
            flags |= QTextDocument.FindFlag.FindBackward
        if editor.find(term, flags):
            self.message.clear()
            self._update_match_count()
            return True

        cursor = editor.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.End if backwards else QTextCursor.MoveOperation.Start
        )
        editor.setTextCursor(cursor)
        if editor.find(term, flags):
            self.message.setText("Wrapped to the end." if backwards else "Wrapped to the beginning.")
            self._update_match_count()
            return True
        self.message.setText("No match found.")
        self._update_match_count()
        return False

    def replace_one(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText("Enter text to find.")
            return

        cursor = editor.textCursor()
        if not (cursor.hasSelection() and cursor.selectedText() == term):
            if not self._find(backwards=False):
                return
            cursor = editor.textCursor()
        cursor.insertText(self.replace_edit.text())
        self._update_match_count()
        if self.find_next():
            self.message.setText("Replaced 1 match. Selected the next match.")
        else:
            self.message.setText("Replaced 1 match. No further matches.")

    def replace_all(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText("Enter text to find.")
            return
        original = editor.toPlainText()
        count = original.count(term)
        if count == 0:
            self.message.setText("No match found.")
            self._update_match_count()
            return
        updated = original.replace(term, self.replace_edit.text())
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(updated)
        cursor.endEditBlock()
        self.message.setText(f"Replaced {count} match{'es' if count != 1 else ''}.")
        self._update_match_count()

    def _update_match_count(self, _text: str | None = None) -> None:
        self.refresh()

    def refresh(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        count = editor.toPlainText().count(term) if editor is not None and term else 0
        self.match_count.setText(f"{count} match{'es' if count != 1 else ''}")
