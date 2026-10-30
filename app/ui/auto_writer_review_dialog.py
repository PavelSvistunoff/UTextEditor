"""Review staged scene drafts and select a batch to apply."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit, QVBoxLayout


class AutoWriterReviewDialog(QDialog):
    def __init__(self, scenes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Review Auto-writer drafts"))
        self.resize(700, 560)
        self.scenes = tuple(scenes)
        layout = QVBoxLayout(self)
        label = QLabel(self.tr("Select drafts to apply together. Later drafts may depend on earlier drafts, including drafts you reject."), self)
        label.setWordWrap(True)
        layout.addWidget(label)
        self.list = QListWidget(self)
        self.list.setAccessibleName(self.tr("Scene drafts"))
        self.list.setAccessibleDescription(self.tr("Use arrow keys to choose a draft and Space to include or exclude it."))
        for scene_id, title, _text in self.scenes:
            item = QListWidgetItem(f"{title} [{scene_id}]")
            item.setData(Qt.ItemDataRole.UserRole, scene_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.list.addItem(item)
        layout.addWidget(self.list)
        self.preview = QPlainTextEdit(self)
        self.preview.setAccessibleName(self.tr("Draft preview"))
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.list.currentRowChanged.connect(self._show_draft)
        if self.scenes:
            self.list.setCurrentRow(0)

    def _show_draft(self, row: int) -> None:
        if 0 <= row < len(self.scenes):
            self.preview.setPlainText(self.scenes[row][2])

    def selected_ids(self) -> set[str]:
        return {self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())
                if self.list.item(i).checkState() == Qt.CheckState.Checked}
