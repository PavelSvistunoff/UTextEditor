"""Review and compare local project revision snapshots."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.document.revisions import RevisionComparison, RevisionIssue, RevisionSnapshot
from app.i18n import format_qt


class RevisionHistoryDialog(QDialog):
    compare_requested = Signal(object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Revision snapshots"))
        self.resize(760, 460)

        self.status = QLabel(self.tr("Loading revision snapshots…"), self)
        self.snapshots = QListWidget(self)
        self.snapshots.setAccessibleName(self.tr("Revision snapshots"))
        self.snapshots.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.snapshots.itemSelectionChanged.connect(self._update_compare_enabled)
        self.compare_button = QPushButton(self.tr("Compare Selected"), self)
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._request_comparison)
        self.details = QTextEdit(self)
        self.details.setAccessibleName(self.tr("Revision comparison"))
        self.details.setReadOnly(True)

        content = QHBoxLayout()
        content.addWidget(self.snapshots, 1)
        content.addWidget(self.details, 2)
        controls = QHBoxLayout()
        controls.addWidget(self.status, 1)
        controls.addWidget(self.compare_button)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addLayout(content)
        layout.addLayout(controls)
        layout.addWidget(buttons)

    def set_snapshots(
        self,
        snapshots: tuple[RevisionSnapshot, ...],
        issues: tuple[RevisionIssue, ...],
    ) -> None:
        self.snapshots.clear()
        for snapshot in snapshots:
            note_count = len(set(snapshot.documents) - set(snapshot.scene_order))
            label = format_qt(self.tr("%1 — %2 (%3 scenes, %4 notes)"),
                              snapshot.name, snapshot.captured_at, len(snapshot.scene_order), note_count)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, snapshot)
            self.snapshots.addItem(item)

        issue_text = "\n".join(
            f"{issue.snapshot_path.name}: {issue.message}" for issue in issues
        )
        if snapshots:
            self.status.setText(
                format_qt(self.tr("%1 snapshot(s) loaded"), len(snapshots))
                + (format_qt(self.tr("; %1 unreadable"), len(issues)) if issues else "")
            )
        elif issues:
            self.status.setText(format_qt(self.tr("No valid snapshots; %1 unreadable"), len(issues)))
        else:
            self.status.setText(self.tr("No revision snapshots yet."))
        self.details.setPlainText(issue_text)
        self._update_compare_enabled()

    def show_comparison(self, comparison: RevisionComparison) -> None:
        self._update_compare_enabled()
        if not comparison.changes:
            self.details.setPlainText(self.tr("No scene or reference-note changes between these snapshots."))
            self.status.setText(self.tr("Snapshots compared; no changes found."))
            return

        sections: list[str] = []
        for change in comparison.changes:
            title = change.new_title or change.old_title or change.scene_id
            labels = {"added": self.tr("Added"), "removed": self.tr("Removed"),
                      "moved": self.tr("Moved"), "title-changed": self.tr("Title Changed"),
                      "text-changed": self.tr("Text Changed"), "type-changed": self.tr("Type Changed")}
            change_label = labels.get(change.kind, change.kind)
            if change.item_type == "note":
                change_label = format_qt(self.tr("Reference Note %1"), change_label)
            sections.append(f"{change_label}: {title}")
            if change.kind == "type-changed":
                sections.append(
                    format_qt(self.tr("Type: %1 → %2"),
                              change.old_note_type or self.tr("unknown"),
                              change.new_note_type or self.tr("unknown"))
                )
            if change.diff:
                sections.append(change.diff.rstrip())
        self.details.setPlainText("\n\n".join(sections))
        self.status.setText(format_qt(self.tr("%1 project item change(s) found."), len(comparison.changes)))

    def show_error(self, message: str) -> None:
        self._update_compare_enabled()
        self.status.setText(message)

    def _update_compare_enabled(self) -> None:
        self.compare_button.setEnabled(len(self.snapshots.selectedItems()) == 2)

    def _request_comparison(self) -> None:
        selected = self.snapshots.selectedItems()
        if len(selected) != 2:
            return
        snapshots = sorted(
            (
                selected[0].data(Qt.ItemDataRole.UserRole),
                selected[1].data(Qt.ItemDataRole.UserRole),
            ),
            key=lambda snapshot: snapshot.captured_at,
        )
        self.compare_button.setEnabled(False)
        self.status.setText(self.tr("Comparing snapshots…"))
        self.compare_requested.emit(snapshots[0], snapshots[1])
