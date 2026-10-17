"""Review dialog for text generated from an explicit user prompt."""

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)


class GeneratedTextDialog(QDialog):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review generated text")
        self.resize(680, 520)
        instructions = QLabel(
            "Review the local model's draft. It will not enter your document unless "
            "you choose Insert."
        )
        instructions.setWordWrap(True)
        self.output = QPlainTextEdit(self)
        self.output.setAccessibleName("Generated text preview")
        self.output.setPlainText(text)
        self.output.setReadOnly(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.insert_button = buttons.addButton(
            "Insert into document", QDialogButtonBox.ButtonRole.AcceptRole
        )
        copy_button = buttons.addButton("Copy", QDialogButtonBox.ButtonRole.ActionRole)
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
