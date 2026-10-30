"""Review and select validated spelling and grammar findings."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout


class SpellcheckReviewDialog(QDialog):
    def __init__(self, suggestions, source: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review spelling and grammar"))
        self.resize(680, 480)
        self.suggestions = tuple(suggestions)
        layout = QVBoxLayout(self)
        instructions = QLabel(self.tr("Select the corrections to apply. Cancel leaves the document unchanged."), self)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        self.findings = QListWidget(self)
        self.findings.setAccessibleName(self.tr("Spelling and grammar findings"))
        self.findings.setAccessibleDescription(self.tr("Use arrow keys to choose a finding and Space to include or exclude it."))
        for index, suggestion in enumerate(self.suggestions):
            original = source[suggestion.start:suggestion.end]
            label = f"{original} → {suggestion.replacement} ({suggestion.type})"
            if suggestion.explanation:
                label += f"\n{suggestion.explanation}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.findings.addItem(item)
        layout.addWidget(self.findings)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_suggestions(self):
        return [self.suggestions[self.findings.item(i).data(Qt.ItemDataRole.UserRole)]
                for i in range(self.findings.count())
                if self.findings.item(i).checkState() == Qt.CheckState.Checked]
