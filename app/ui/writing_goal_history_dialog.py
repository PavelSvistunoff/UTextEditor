"""Read-only view of locally stored new-word progress."""

from typing import Mapping

from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QLabel, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)


class WritingGoalHistoryDialog(QDialog):
    def __init__(self, progress: Mapping[str, Mapping[str, int]], parent=None, *,
                 scope_history: Mapping[str, Mapping[str, Mapping[str, int]]] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Writing goal history"))
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        explanation = QLabel(self.tr(
            "Approximate newly written words across stored document identities, by local date. "
            "Undo and redo can change counts; only an enabled, unpaused goal records progress. "
            "Document and project counts are the last complete observations for each local day; older observations may be unavailable."
        ), self)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        rows = [(day, self.tr("Newly written words"), self.tr("All stored documents"), sum(counts.values()))
                for day, counts in progress.items()]
        labels = {"active_scene": self.tr("Active document words"),
                  "project_manuscript": self.tr("Project manuscript words")}
        for day, scopes in (scope_history or {}).items():
            for scope, values in scopes.items():
                rows.extend((day, labels[scope], identity, count) for identity, count in values.items())
        rows.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
        self.table = QTableWidget(len(rows), 4, self)
        self.table.setHorizontalHeaderLabels((self.tr("Local date"), self.tr("Measure"), self.tr("Document or project"), self.tr("Words")))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAccessibleName(self.tr("Daily writing goal history"))
        for row, (day, measure, identity, count) in enumerate(rows):
            for column, value in enumerate((day, measure, identity, str(count))):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(self.tr("Close"))
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
