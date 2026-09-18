"""In-memory inspector for local Ollama interactions."""

import json
from datetime import datetime
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QVBoxLayout


class AIDebugWindow(QDialog):
    """Shows request and response data without persisting document contents."""

    cleared = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ollama Debug")
        self.resize(760, 520)
        self.output = QPlainTextEdit(readOnly=True)
        warning = QLabel("Requests can contain document text. This debug history is kept only in memory.")
        warning.setWordWrap(True)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        copy = buttons.addButton("Copy", QDialogButtonBox.ButtonRole.ActionRole)
        clear = buttons.addButton("Clear", QDialogButtonBox.ButtonRole.ResetRole)
        copy.clicked.connect(self.copy_to_clipboard)
        clear.clicked.connect(self.clear)
        buttons.rejected.connect(self.close)
        layout = QVBoxLayout(self)
        layout.addWidget(warning)
        layout.addWidget(self.output)
        layout.addWidget(buttons)

    def append_interaction(self, event: str, path: str, details: dict[str, Any]) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = json.dumps(details, ensure_ascii=False, indent=2, default=str)
        self.output.appendPlainText(f"[{timestamp}] {event} {path}\n{formatted}\n")

    def clear(self) -> None:
        self.output.clear()
        self.cleared.emit()

    def copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self.output.toPlainText())
