"""Accessible project navigation tree with manuscript word-count summaries."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeWidget, QTreeWidgetItem

from app.project import Project, WordCount


class ProjectView(QTreeWidget):
    open_requested = Signal(str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Project navigation")
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setExpandsOnDoubleClick(True)
        self.itemActivated.connect(self._activate_item)

    def show_project(
        self,
        project: Project,
        scene_counts: dict[str, WordCount],
        chapter_counts: dict[str, WordCount],
        project_count: WordCount,
        unavailable_ids: set[str] | None = None,
    ) -> None:
        self.clear()
        unavailable_ids = unavailable_ids or set()
        root = QTreeWidgetItem([self._count_label(project.manifest.title, project_count)])
        root.setData(0, Qt.ItemDataRole.UserRole, "project")
        self.addTopLevelItem(root)

        for chapter in project.manifest.chapters:
            chapter_count = chapter_counts[chapter.id]
            chapter_item = QTreeWidgetItem([self._count_label(chapter.title, chapter_count)])
            chapter_item.setData(0, Qt.ItemDataRole.UserRole, "chapter")
            chapter_item.setData(0, Qt.ItemDataRole.UserRole + 1, chapter.id)
            root.addChild(chapter_item)
            for scene in chapter.scenes:
                self._add_scene(chapter_item, scene.id, scene.title, scene_counts[scene.id], scene.id in unavailable_ids)

        if project.manifest.ungrouped_scenes:
            ungrouped = QTreeWidgetItem(["Ungrouped scenes"])
            ungrouped.setData(0, Qt.ItemDataRole.UserRole, "group")
            root.addChild(ungrouped)
            for scene in project.manifest.ungrouped_scenes:
                self._add_scene(ungrouped, scene.id, scene.title, scene_counts[scene.id], scene.id in unavailable_ids)

        notes = QTreeWidgetItem(["Reference notes"])
        notes.setData(0, Qt.ItemDataRole.UserRole, "group")
        root.addChild(notes)
        titles = {
            scene.id: scene.title for scene in project.iter_scenes()
        }
        titles.update({note.id: note.title for note in project.manifest.notes})
        for note in project.manifest.notes:
            prefix = "Unavailable — " if note.id in unavailable_ids else ""
            item = QTreeWidgetItem([f"{prefix}{note.title} ({note.type})"])
            item.setData(0, Qt.ItemDataRole.UserRole, "note")
            item.setData(0, Qt.ItemDataRole.UserRole + 1, note.id)
            linked = [
                f"→ {titles.get(link.target_id, 'Missing target ' + link.target_id)}"
                for link in project.links_from(note.id)
            ]
            linked.extend(
                f"← {titles.get(link.source_id, 'Missing source ' + link.source_id)}"
                for link in project.links_to(note.id)
            )
            if linked:
                item.setToolTip(0, "Links:\n" + "\n".join(linked))
            notes.addChild(item)
        root.setExpanded(True)
        self.expandAll()

    @staticmethod
    def _count_label(title: str, count: WordCount) -> str:
        return f"{title} — {'at least ' if not count.complete else ''}{count.count} words"

    def _add_scene(
        self, parent: QTreeWidgetItem, scene_id: str, title: str, count: WordCount, unavailable: bool
    ) -> None:
        prefix = "Unavailable — " if unavailable else ""
        item = QTreeWidgetItem([prefix + self._count_label(title, count)])
        item.setData(0, Qt.ItemDataRole.UserRole, "scene")
        item.setData(0, Qt.ItemDataRole.UserRole + 1, scene_id)
        parent.addChild(item)

    def _activate_item(self, item: QTreeWidgetItem, _column: int) -> None:
        kind = item.data(0, Qt.ItemDataRole.UserRole)
        identifier = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if kind in {"scene", "note"} and isinstance(identifier, str):
            self.open_requested.emit(kind, identifier)
