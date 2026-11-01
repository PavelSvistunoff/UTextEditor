"""Read-only review of a captured manuscript export."""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout


class ExportPreviewDialog(QDialog):
    PREVIEW_LIMIT = 64 * 1024

    def __init__(self, content: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Preview manuscript export"))
        self.resize(760, 540)
        layout = QVBoxLayout(self)
        instructions = QLabel(self.tr("Review the captured export. Export writes this version without saving source documents."), self)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.preview = QPlainTextEdit(self)
        self.preview.setAccessibleName(self.tr("Captured manuscript export"))
        self.preview.setReadOnly(True)
        self.preview.setPlainText(content[:self.PREVIEW_LIMIT])
        layout.addWidget(self.preview)
        if len(content) > self.PREVIEW_LIMIT:
            notice = QLabel(self.tr("Only the beginning is displayed; export includes the entire captured manuscript."), self)
            notice.setWordWrap(True)
            layout.addWidget(notice)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        buttons.addButton(self.tr("Export"), QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
