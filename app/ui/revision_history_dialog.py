"""Review and compare local project revision snapshots."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.document.revisions import RevisionComparison, RevisionIssue, RevisionSnapshot
from app.i18n import format_qt


class RevisionHistoryDialog(QDialog):
    PREVIEW_LIMIT = 32768
    compare_requested = Signal(object, object)
    delete_requested = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.selection_generation = 0
        self.setWindowTitle(self.tr("Revision snapshots"))
        self.resize(760, 460)

        self.status = QLabel(self.tr("Loading revision snapshots…"), self)
        self.snapshots = QListWidget(self)
        self.snapshots.setAccessibleName(self.tr("Revision snapshots"))
        self.snapshots.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.snapshots.itemSelectionChanged.connect(self._selection_changed)
        self.compare_button = QPushButton(self.tr("Compare Selected"), self)
        self.compare_button.setEnabled(False)
        self.compare_button.clicked.connect(self._request_comparison)
        self.delete_button = QPushButton(self.tr("Delete Selected…"), self)
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self._request_deletion)
        self.previous_page = QPushButton(self.tr("Previous Page"), self)
        self.next_page = QPushButton(self.tr("Next Page"), self)
        self.previous_page.setEnabled(False)
        self.next_page.setEnabled(False)
        self.previous_page.clicked.connect(lambda: self._change_preview_page(-1))
        self.next_page.clicked.connect(lambda: self._change_preview_page(1))
        self._preview_page = 0
        self.details = QTextEdit(self)
        self.details.setAccessibleName(self.tr("Revision preview and comparison"))
        self.details.setReadOnly(True)

        content = QHBoxLayout()
        content.addWidget(self.snapshots, 1)
        content.addWidget(self.details, 2)
        controls = QHBoxLayout()
        controls.addWidget(self.status, 1)
        controls.addWidget(self.compare_button)
        controls.addWidget(self.delete_button)
        controls.addWidget(self.previous_page)
        controls.addWidget(self.next_page)
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
            self.details.setPlainText(self.tr("No chapter, scene, reference-note or link changes between these snapshots."))
            self.status.setText(self.tr("Snapshots compared; no changes found."))
            return

        sections: list[str] = []
        for change in comparison.changes:
            title = change.new_title or change.old_title or change.scene_id
            labels = {"added": self.tr("Added"), "removed": self.tr("Removed"),
                      "moved": self.tr("Moved"), "title-changed": self.tr("Title Changed"),
                      "text-changed": self.tr("Text Changed"), "type-changed": self.tr("Type Changed"),
                      "chapter-changed": self.tr("Chapter Changed"), "path-changed": self.tr("Path Changed"),
                      "metadata-changed": self.tr("Details Changed"),
                      "association-added": self.tr("Character Association Added"),
                      "association-removed": self.tr("Character Association Removed"),
                      "association-changed": self.tr("Character Association Changed")}
            change_label = labels.get(change.kind, change.kind)
            if change.item_type == "note":
                change_label = format_qt(self.tr("Reference Note %1"), change_label)
            elif change.item_type == "chapter":
                change_label = format_qt(self.tr("Chapter %1"), change_label)
            elif change.item_type == "link":
                change_label = format_qt(self.tr("Link %1"), change_label)
            elif change.item_type == "project":
                change_label = format_qt(self.tr("Project %1"), change_label)
            elif change.item_type == "character":
                change_label = format_qt(self.tr("Character %1"), change_label)
            elif change.item_type == "relationship":
                change_label = format_qt(self.tr("Relationship %1"), change_label)
            sections.append(f"{change_label}: {title}")
            if change.kind == "type-changed":
                sections.append(
                    format_qt(self.tr("Type: %1 → %2"),
                              change.old_note_type or self.tr("unknown"),
                              change.new_note_type or self.tr("unknown"))
                )
            if change.kind == "chapter-changed":
                sections.append(format_qt(self.tr("Chapter: %1 → %2"),
                                          change.old_chapter_id or self.tr("Ungrouped"),
                                          change.new_chapter_id or self.tr("Ungrouped")))
            if change.kind == "path-changed":
                sections.append(format_qt(self.tr("Path: %1 → %2"), change.old_path, change.new_path))
            if change.character_id is not None:
                sections.append(format_qt(self.tr("Character ID: %1"), change.character_id))
            if change.kind == "title-changed" and change.item_type == "project":
                sections.append(format_qt(self.tr("Title: %1 → %2"), change.old_title, change.new_title))
            if change.diff:
                sections.append(change.diff.rstrip())
        self.details.setPlainText("\n\n".join(sections))
        self.status.setText(format_qt(self.tr("%1 project item change(s) found."), len(comparison.changes)))

    def show_error(self, message: str) -> None:
        self._update_compare_enabled()
        self.status.setText(message)

    def _update_compare_enabled(self) -> None:
        self.compare_button.setEnabled(len(self.snapshots.selectedItems()) == 2)
        self.delete_button.setEnabled(len(self.snapshots.selectedItems()) == 1)

    def _selection_changed(self) -> None:
        self.selection_generation += 1
        self._update_compare_enabled()
        self._preview_page = 0
        self._show_preview()

    def _change_preview_page(self, direction: int) -> None:
        self._preview_page = max(0, self._preview_page + direction)
        self._show_preview()

    def _show_preview(self) -> None:
        selected = self.snapshots.selectedItems()
        if len(selected) != 1:
            self.previous_page.setEnabled(False)
            self.next_page.setEnabled(False)
            self.details.clear()
            return
        snapshot = selected[0].data(Qt.ItemDataRole.UserRole)
        parts = []
        skip = self._preview_page * self.PREVIEW_LIMIT
        remaining = self.PREVIEW_LIMIT + 1
        scene_ids = set(snapshot.scene_order)
        def sections():
            for item_id in snapshot.scene_order:
                yield snapshot.scene_titles.get(item_id, item_id)
                yield " ["
                yield item_id
                yield "]\n"
                yield snapshot.documents[item_id]
                yield "\n\n"
            for item_id, text in snapshot.documents.items():
                if item_id not in scene_ids:
                    yield item_id
                    yield " ["
                    yield item_id
                    yield "]\n"
                    yield text
                    yield "\n\n"

        for section in sections():
            if skip >= len(section):
                skip -= len(section)
                continue
            chunk = section[skip:skip + remaining]
            skip = 0
            parts.append(chunk)
            remaining -= len(chunk)
            if remaining == 0:
                break
        preview = "".join(parts)
        self.previous_page.setEnabled(self._preview_page > 0)
        self.next_page.setEnabled(len(preview) > self.PREVIEW_LIMIT)
        self.details.setPlainText(preview[:self.PREVIEW_LIMIT])

    def _request_deletion(self) -> None:
        selected = self.snapshots.selectedItems()
        if len(selected) != 1:
            return
        snapshot = selected[0].data(Qt.ItemDataRole.UserRole)
        answer = QMessageBox.warning(
            self, self.tr("Delete revision snapshot"),
            format_qt(self.tr("Delete snapshot ‘%1’ captured at %2? This cannot be undone."),
                      snapshot.name, snapshot.captured_at),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_button.setEnabled(False)
            self.delete_requested.emit(snapshot)

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
