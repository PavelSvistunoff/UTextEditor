"""Review the versions of a file that changed outside the editor."""

from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QPushButton,
    QTabWidget, QVBoxLayout,
)


class ConflictDialog(QDialog):
    def __init__(self, base: str, disk: str, buffer: str, proposal: str, conflicts: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review External Changes"))
        self.resize(850, 600)
        self.choice = "cancel"
        layout = QVBoxLayout(self)
        label = QLabel(self.tr("Review the versions and resolve any conflict markers before staging a merge. Nothing is saved until you save the document."), self)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.tabs = QTabWidget(self)
        for title, value in ((self.tr("Saved base"), base), (self.tr("Disk version"), disk), (self.tr("Open buffer"), buffer)):
            view = QPlainTextEdit(self)
            view.setAccessibleName(title)
            view.setPlainText(value)
            view.setReadOnly(True)
            self.tabs.addTab(view, title)
        self.merge = QPlainTextEdit(self)
        self.merge.setAccessibleName(self.tr("Proposed merge"))
        self.merge.setPlainText(proposal)
        self.tabs.addTab(self.merge, self.tr("Proposed merge"))
        self.tabs.setCurrentWidget(self.merge)
        layout.addWidget(self.tabs)
        if conflicts:
            layout.addWidget(QLabel(self.tr("Conflicting changes are marked in the proposed merge."), self))
        buttons = QDialogButtonBox(self)
        for title, choice in ((self.tr("Stage Merge"), "merge"), (self.tr("Reload Disk Version"), "reload"), (self.tr("Save Elsewhere…"), "elsewhere")):
            button = QPushButton(title, self)
            buttons.addButton(button, QDialogButtonBox.ButtonRole.ActionRole)
            button.clicked.connect(lambda checked=False, selected=choice: self._choose(selected))
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose(self, choice: str) -> None:
        self.choice = choice
        self.accept()
