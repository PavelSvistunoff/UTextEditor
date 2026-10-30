"""Editable story brief form used before generating a project outline."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
)


PROJECT_BRIEF_TEMPLATE = """Story premise:
[Describe the core idea or situation]

Genre:
[For example: mystery, fantasy, literary fiction]

Intended audience:
[Who do you imagine reading this?]

Tone and style:
[For example: hopeful, suspenseful, humorous, spare]

Themes or questions:
[What ideas would you like the story to explore?]

Main character(s):
[Who is central to the story, and what do they want?]

Setting:
[Where and when does the story take place?]

Central conflict:
[What stands in the way of the character(s)?]

Important events or turning points:
[Any scenes or developments you already have in mind]

Ending or open questions:
[What kind of ending do you want, or what is undecided?]

Structure preferences:
[Approximate chapter count, pacing, point of view, or other preferences]
"""


class ProjectBriefDialog(QDialog):
    suggest_requested = Signal(str)
    autopilot_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Set up writing project"))
        self.resize(680, 650)

        instructions = QLabel(
            self.tr("Edit this template with the details you know. Leave anything undecided as a prompt, or use Suggest to ask the configured AI to propose ideas for gaps. Review suggestions before continuing."),
            self,
        )
        instructions.setWordWrap(True)
        self.editor = QPlainTextEdit(self)
        self.editor.setPlainText(PROJECT_BRIEF_TEMPLATE)
        self.status = QLabel(self)
        self.status.setWordWrap(True)

        self.suggest_button = QPushButton(self.tr("Suggest"), self)
        self.suggest_button.clicked.connect(
            lambda: self.suggest_requested.emit(self.editor.toPlainText())
        )
        self.autopilot_button = QPushButton(self.tr("Auto-pilot: refine plan and write"), self)
        self.autopilot_button.clicked.connect(
            lambda: self.autopilot_requested.emit(self.editor.toPlainText())
        )
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Continue to outline"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(instructions)
        layout.addWidget(self.editor)
        layout.addWidget(self.status)
        layout.addWidget(self.suggest_button)
        layout.addWidget(self.autopilot_button)
        layout.addWidget(self.buttons)

    def brief(self) -> str:
        return self.editor.toPlainText()

    def set_suggesting(self, suggesting: bool, message: str = "") -> None:
        self.suggest_button.setEnabled(not suggesting)
        self.autopilot_button.setEnabled(not suggesting)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not suggesting)
        self.status.setText(
            message or (self.tr("Asking the model for suggestions…") if suggesting else "")
        )

    def set_autopilot_running(self, running: bool, message: str = "") -> None:
        self.cancel_button.setEnabled(True)
        self.editor.setEnabled(not running)
        self.suggest_button.setEnabled(not running)
        self.autopilot_button.setEnabled(not running)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not running)
        self.status.setText(
            message
            or (
                "Auto-pilot is refining the plan and drafting new scenes. "
                "Cancel leaves project files unchanged…"
                if running
                else ""
            )
        )

    def set_applying(self, message: str) -> None:
        self.set_autopilot_running(True, message)
        self.cancel_button.setEnabled(False)

    def apply_suggestion(self, text: str) -> None:
        self.editor.setPlainText(text)
        self.set_suggesting(
            False,
            "Suggestions added to the template. Review and edit them before continuing.",
        )
