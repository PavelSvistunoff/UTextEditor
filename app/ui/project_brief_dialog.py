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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Set up writing project")
        self.resize(680, 650)

        instructions = QLabel(
            "Edit this template with the details you know. Leave anything undecided "
            "as a prompt, or use Suggest to ask the configured local AI to propose "
            "ideas for gaps. Review suggestions before continuing.",
            self,
        )
        instructions.setWordWrap(True)
        self.editor = QPlainTextEdit(self)
        self.editor.setPlainText(PROJECT_BRIEF_TEMPLATE)
        self.status = QLabel(self)
        self.status.setWordWrap(True)

        self.suggest_button = QPushButton("Suggest", self)
        self.suggest_button.clicked.connect(
            lambda: self.suggest_requested.emit(self.editor.toPlainText())
        )
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continue to outline")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(instructions)
        layout.addWidget(self.editor)
        layout.addWidget(self.status)
        layout.addWidget(self.suggest_button)
        layout.addWidget(self.buttons)

    def brief(self) -> str:
        return self.editor.toPlainText()

    def set_suggesting(self, suggesting: bool, message: str = "") -> None:
        self.suggest_button.setEnabled(not suggesting)
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(not suggesting)
        self.status.setText(
            message or ("Asking the local model for suggestions…" if suggesting else "")
        )

    def apply_suggestion(self, text: str) -> None:
        self.editor.setPlainText(text)
        self.set_suggesting(
            False,
            "Suggestions added to the template. Review and edit them before continuing.",
        )
