"""Small find/replace bar used by the main window."""

from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget


class FindReplaceWidget(QWidget):
    def __init__(self, editor_provider, parent=None) -> None:
        super().__init__(parent)
        self.editor_provider = editor_provider
        self.find_edit = QLineEdit()
        self.replace_edit = QLineEdit()
        find = QPushButton("Find")
        replace = QPushButton("Replace")
        replace_all = QPushButton("Replace All")
        find.clicked.connect(self.find_next)
        replace.clicked.connect(self.replace_one)
        replace_all.clicked.connect(self.replace_all)
        self.message = QLabel()
        layout = QHBoxLayout(self)
        for widget in (self.find_edit, self.replace_edit, find, replace, replace_all, self.message):
            layout.addWidget(widget)

    def find_next(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if not editor or not term:
            self.message.setText("Enter text to find.")
            return
        cursor = editor.textCursor()
        start = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        cursor.setPosition(start)
        editor.setTextCursor(cursor)
        if editor.find(term, QTextDocument.FindFlag.FindCaseSensitively):
            self.message.clear()
            return
        cursor = editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        editor.setTextCursor(cursor)
        if editor.find(term, QTextDocument.FindFlag.FindCaseSensitively):
            self.message.setText("Wrapped to the beginning.")
        else:
            self.message.setText("No match found.")

    def replace_one(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if not editor or not term:
            self.message.setText("Enter text to find.")
            return
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == term:
            cursor.insertText(self.replace_edit.text())
            self.message.setText("Replaced 1 match.")
        else:
            self.find_next()

    def replace_all(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if not editor or not term:
            self.message.setText("Enter text to find.")
            return
        original = editor.toPlainText()
        count = original.count(term)
        if count == 0:
            self.message.setText("No match found.")
            return
        updated = original.replace(term, self.replace_edit.text())
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.insertText(updated)
        cursor.endEditBlock()
        self.message.setText(f"Replaced {count} match{'es' if count != 1 else ''}.")
