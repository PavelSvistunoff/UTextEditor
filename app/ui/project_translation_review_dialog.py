"""Side-by-side review of a complete project translation."""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QPlainTextEdit, QVBoxLayout


class ProjectTranslationReviewDialog(QDialog):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review project translation"))
        self.resize(900, 600)
        self.items = tuple(items)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Review the complete translation. Apply commits all items together.")))
        self.list = QListWidget(self)
        self.list.setAccessibleName(self.tr("Translation items"))
        self.list.addItems([item[0] for item in self.items])
        layout.addWidget(self.list)
        columns = QHBoxLayout()
        self.original = QPlainTextEdit(self)
        self.original.setAccessibleName(self.tr("Original text"))
        self.original.setReadOnly(True)
        self.translated = QPlainTextEdit(self)
        self.translated.setAccessibleName(self.tr("Translated text"))
        self.translated.setReadOnly(True)
        for title, editor in ((self.tr("Original"), self.original), (self.tr("Translation"), self.translated)):
            column = QVBoxLayout()
            column.addWidget(QLabel(title))
            column.addWidget(editor)
            columns.addLayout(column)
        layout.addLayout(columns)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list.currentRowChanged.connect(self._show_item)
        if self.items:
            self.list.setCurrentRow(0)

    def _show_item(self, row: int) -> None:
        if 0 <= row < len(self.items):
            _, original, translated = self.items[row]
            self.original.setPlainText(original)
            self.translated.setPlainText(translated)
