"""Review dialog for text generated from an explicit user prompt."""

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)
from PySide6.QtGui import QTextCursor


class GeneratedTextDialog(QDialog):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review generated text"))
        self.resize(680, 520)
        instructions = QLabel(
            self.tr("Review the model's draft. It will not enter your document unless you choose Insert.")
        )
        instructions.setWordWrap(True)
        self.output = QPlainTextEdit(self)
        self.output.setAccessibleName(self.tr("Generated text preview"))
        self.output.setPlainText(text)
        self.output.setReadOnly(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.insert_button = buttons.addButton(
            self.tr("Insert into document"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        copy_button = buttons.addButton(self.tr("Copy"), QDialogButtonBox.ButtonRole.ActionRole)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        self.insert_button.setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        copy_button.clicked.connect(
            lambda: QApplication.clipboard().setText(self.output.toPlainText())
        )

        layout = QVBoxLayout(self)
        layout.addWidget(instructions)
        layout.addWidget(self.output)
        layout.addWidget(buttons)


class StreamingPreviewDialog(QDialog):
    """Display provisional output without modifying the document."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Generating text"))
        self.resize(680, 520)
        label = QLabel(self.tr("This preview is provisional. Review the finished draft before inserting it."))
        label.setWordWrap(True)
        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setAccessibleName(self.tr("Provisional generated text"))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.output)
        layout.addWidget(buttons)

    def append_text(self, text: str) -> None:
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
