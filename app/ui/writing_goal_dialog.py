"""Configuration dialog for an optional local daily writing goal."""

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QSpinBox


class WritingGoalDialog(QDialog):
    _scopes = (
        ("Active scene/document words", "active_scene"),
        ("Project manuscript words", "project_manuscript"),
        ("Words newly written today", "new_words"),
    )

    def __init__(self, target: int, scope: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Daily writing goal"))
        self.target = QSpinBox(self)
        self.target.setRange(0, 1_000_000)
        self.target.setSpecialValueText(self.tr("Off"))
        self.target.setValue(target)
        self.scope = QComboBox(self)
        for label, value in self._scopes:
            self.scope.addItem(label, value)
        index = self.scope.findData(scope)
        self.scope.setCurrentIndex(max(0, index))
        form = QFormLayout(self)
        form.addRow(self.tr("Daily word goal"), self.target)
        form.addRow(self.tr("Measure"), self.scope)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("OK"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Cancel"))
        form.addRow(buttons)

    def values(self) -> tuple[int, str]:
        return self.target.value(), str(self.scope.currentData())
