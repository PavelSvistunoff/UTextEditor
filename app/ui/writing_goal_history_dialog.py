"""Read-only view of locally stored new-word progress."""

from typing import Mapping

from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)


class WritingGoalHistoryDialog(QDialog):
    def __init__(self, progress: Mapping[str, Mapping[str, int]], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Writing goal history"))
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        explanation = QLabel(self.tr(
            "Approximate newly written words across stored document identities, by local date. "
            "Undo and redo can change counts; only an enabled, unpaused new-word goal records progress. "
            "Historical active-document and project word counts are not stored."
        ), self)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.table = QTableWidget(len(progress), 3, self)
        self.table.setHorizontalHeaderLabels((self.tr("Local date"), self.tr("Measure"), self.tr("Approximate words")))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAccessibleName(self.tr("Daily writing goal history"))
        for row, (day, counts) in enumerate(sorted(progress.items(), reverse=True)):
            for column, value in enumerate((day, self.tr("Newly written words"), str(sum(counts.values())))):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Close"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
