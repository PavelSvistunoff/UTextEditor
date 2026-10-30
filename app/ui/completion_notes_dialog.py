"""Session-only selection of reference notes for scene completions."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout


class CompletionNotesDialog(QDialog):
    def __init__(self, notes, excluded: set[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Completion Reference Notes"))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.tr("Select reference notes to include in project-scene completions for this session.")))
        self.notes = QListWidget(self)
        self.notes.setAccessibleName(self.tr("Reference notes included in completions"))
        for note in notes:
            item = QListWidgetItem(f"{note.title} — {note.type} [{note.id}]")
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked if note.id in excluded else Qt.CheckState.Checked)
            self.notes.addItem(item)
        layout.addWidget(self.notes)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def excluded_ids(self) -> set[str]:
        return {self.notes.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.notes.count())
                if self.notes.item(i).checkState() == Qt.CheckState.Unchecked}
