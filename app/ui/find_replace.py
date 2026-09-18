"""Small find/replace bar used by the main window."""

from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


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
        layout = QHBoxLayout(self)
        for widget in (self.find_edit, self.replace_edit, find, replace, replace_all):
            layout.addWidget(widget)

    def find_next(self) -> None:
        editor = self.editor_provider()
        if editor:
            editor.find(self.find_edit.text())

    def replace_one(self) -> None:
        editor = self.editor_provider()
        if editor and editor.textCursor().hasSelection() and editor.textCursor().selectedText() == self.find_edit.text():
            editor.textCursor().insertText(self.replace_edit.text())
        self.find_next()

    def replace_all(self) -> None:
        editor = self.editor_provider()
        if not editor or not self.find_edit.text():
            return
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText(editor.toPlainText().replace(self.find_edit.text(), self.replace_edit.text()))
        cursor.endEditBlock()
