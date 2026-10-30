"""Options and author instructions for whole-project Auto-writer runs."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)
from app.i18n import format_qt


class AutoWriterDialog(QDialog):
    def __init__(self, scene_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Auto-writer"))
        self.resize(600, 480)

        self.description = QLabel(
            format_qt(self.tr("This project currently has %1 scenes. Auto-writer uses the configured model, project outline, and reference notes. It first creates a complete local revision snapshot. All generated scene changes are applied together only after every result is ready."), scene_count),
            self,
        )
        self.description.setWordWrap(True)
        self.mode = QComboBox(self)
        self.mode.addItem(self.tr("Write empty scenes only"), "write_empty")
        self.mode.addItem(self.tr("Refine every scene"), "refine_all")
        self.instructions = QPlainTextEdit(self)
        self.instructions.setPlaceholderText(
            self.tr("Optional guidance: style, voice, point of view, pacing, or goals.")
        )
        self.instructions.setMaximumBlockCount(80)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Start Auto-writer"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        form = QFormLayout()
        form.addRow(self.tr("Task"), self.mode)
        form.addRow(self.tr("Writing instructions"), self.instructions)
        layout = QVBoxLayout(self)
        layout.addWidget(self.description)
        layout.addLayout(form)
        layout.addWidget(self.buttons)

    def values(self) -> tuple[str, str]:
        return str(self.mode.currentData()), self.instructions.toPlainText()


class AutoWriterProgressDialog(QDialog):
    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Auto-writer progress"))
        self.resize(680, 520)
        self._running = True

        self.status = QLabel(self.tr("Preparing the project snapshot…"), self)
        self.status.setWordWrap(True)
        self.output = QPlainTextEdit(self)
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(self.tr("Completed scene drafts will appear here."))
        self.output.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.output.setMaximumBlockCount(100000)
        self.cancel_button = QPushButton(self.tr("Cancel Auto-writer"), self)
        self.cancel_button.clicked.connect(self._handle_button)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                self.tr("Each draft appears as soon as it is complete. Drafts are applied to the project together only after every scene succeeds."),
                self,
            )
        )
        layout.addWidget(self.status)
        layout.addWidget(self.output)
        layout.addWidget(self.cancel_button)

    def append_scene(self, title: str, text: str, completed: int, total: int) -> None:
        self.status.setText(format_qt(self.tr("Completed scene %1 of %2: %3"), completed, total, title))
        self.output.appendPlainText(f"## {title}\n{text}\n")

    def set_status(self, message: str) -> None:
        self.status.setText(message)

    def set_applying(self, message: str) -> None:
        self.status.setText(message)
        self.cancel_button.setEnabled(False)

    def finish(self, message: str) -> None:
        self._running = False
        self.status.setText(message)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText(self.tr("Close"))

    def _handle_button(self) -> None:
        if self._running:
            self.cancel_requested.emit()
        else:
            self.close()
