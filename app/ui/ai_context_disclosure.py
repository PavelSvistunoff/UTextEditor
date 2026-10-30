"""Non-modal disclosure for the configured AI destination."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from app.i18n import format_qt


class AIContextDisclosure(QDialog):
    """Explain which information AI workflows may send before approval."""

    def __init__(self, destination: str, parent=None) -> None:
        super().__init__(parent)
        self.destination = destination
        self.setWindowTitle(self.tr("AI context and destination"))
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.message = QLabel(format_qt(self.tr(
            "AI requests can send document text, writing instructions, project outlines, "
            "reference notes, and associated character information to %1. "
            "The destination may be remote. Requests and responses may also appear "
            "in this session's AI diagnostics. Allow AI context to be sent to this destination?"
        ), destination), self)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setWordWrap(True)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No, self
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Yes).setText(self.tr("Allow"))
        self.buttons.button(QDialogButtonBox.StandardButton.No).setText(self.tr("Not now"))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.message)
        layout.addWidget(self.buttons)
