"""Review a captured completion context before sending it."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout

from app.i18n import format_qt


class CompletionContextDialog(QDialog):
    def __init__(self, destination: str, context: str, summary: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review completion context"))
        self.resize(680, 520)
        layout = QVBoxLayout(self)
        destination_label = QLabel(format_qt(self.tr("Destination: %1"), destination), self)
        destination_label.setTextFormat(Qt.TextFormat.PlainText)
        destination_label.setWordWrap(True)
        layout.addWidget(destination_label)
        summary_label = QLabel(summary, self)
        summary_label.setTextFormat(Qt.TextFormat.PlainText)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)
        self.context = QPlainTextEdit(self)
        self.context.setAccessibleName(self.tr("Captured completion context"))
        self.context.setPlainText(context)
        self.context.setReadOnly(True)
        layout.addWidget(self.context)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        buttons.addButton(self.tr("Send completion request"), QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
