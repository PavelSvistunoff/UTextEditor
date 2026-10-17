"""Editable review dialog for an AI-generated project outline."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
)

from app.project import ProjectError
from app.project.outline import parse_outline


class ProjectSetupDialog(QDialog):
    def __init__(self, outline: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Review AI project outline")
        self.resize(640, 560)

        self.instructions = QLabel(
            "Edit the outline before applying it. Use '# Chapter title' and "
            "'- Scene title' lines. Applying creates empty scene files only; "
            "the AI has not written manuscript prose.",
            self,
        )
        self.instructions.setWordWrap(True)
        self.editor = QPlainTextEdit(self)
        self.editor.setPlainText(outline)
        self.validation = QLabel(self)
        self.validation.setWordWrap(True)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        self.apply_button = self.buttons.button(QDialogButtonBox.StandardButton.Apply)
        self.buttons.accepted.connect(self.accept)
        self.apply_button.clicked.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.instructions)
        layout.addWidget(self.editor)
        layout.addWidget(self.validation)
        layout.addWidget(self.buttons)
        self.editor.textChanged.connect(self._validate)
        self._validate()

    def outline(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        return parse_outline(self.editor.toPlainText())

    def _validate(self) -> None:
        try:
            chapters = self.outline()
        except ProjectError as exc:
            self.validation.setText(str(exc))
            self.apply_button.setEnabled(False)
            return
        scene_count = sum(len(scenes) for _title, scenes in chapters)
        self.validation.setText(
            f"Valid outline: {len(chapters)} chapters, {scene_count} empty scenes."
        )
        self.apply_button.setEnabled(True)
