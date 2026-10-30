"""Accessible project navigation tree with manuscript word-count summaries."""

from PySide6.QtCore import QItemSelectionModel, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QMenu, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator

from app.project import Project, WordCount


class ProjectView(QTreeWidget):
    open_requested = Signal(str, str)
    context_action_requested = Signal(str, str, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAccessibleName("Project navigation")
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setExpandsOnDoubleClick(True)
        self.itemActivated.connect(self._activate_item)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.character_filter = ""
        self._characters = ()
        self._project_root = None

    @staticmethod
    def _item_key(item: QTreeWidgetItem) -> tuple[str, str]:
        return (str(item.data(0, Qt.ItemDataRole.UserRole) or ""),
                str(item.data(0, Qt.ItemDataRole.UserRole + 1) or ""))

    def _items(self):
        iterator = QTreeWidgetItemIterator(self)
        while iterator.value() is not None:
            yield iterator.value()
            iterator += 1

    def show_project(
        self,
        project: Project,
        scene_counts: dict[str, WordCount],
        chapter_counts: dict[str, WordCount],
        project_count: WordCount,
        unavailable_ids: set[str] | None = None,
    ) -> None:
        same_project = self._project_root == project.root and self.topLevelItemCount() > 0
        old_items = list(self._items()) if same_project else []
        expanded = {self._item_key(item) for item in old_items if item.isExpanded()}
        known = {self._item_key(item) for item in old_items}
        selected = {self._item_key(item) for item in old_items if item.isSelected()}
        current = self._item_key(self.currentItem()) if same_project and self.currentItem() else None
        scroll = self.verticalScrollBar().value()
        self.clear()
        self._project_root = project.root
        self._characters = tuple(project.manifest.characters)
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
            ungrouped = QTreeWidgetItem([self.tr("Ungrouped scenes")])
            ungrouped.setData(0, Qt.ItemDataRole.UserRole, "group")
            ungrouped.setData(0, Qt.ItemDataRole.UserRole + 1, "ungrouped")
            root.addChild(ungrouped)
            for scene in project.manifest.ungrouped_scenes:
                self._add_scene(ungrouped, scene.id, scene.title, scene_counts[scene.id], scene.id in unavailable_ids)

        notes = QTreeWidgetItem([self.tr("Reference notes")])
        notes.setData(0, Qt.ItemDataRole.UserRole, "group")
        notes.setData(0, Qt.ItemDataRole.UserRole + 1, "notes")
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
        characters = QTreeWidgetItem([self.tr("Characters (%1)").replace("%1", str(len(project.manifest.characters)))])
        characters.setData(0, Qt.ItemDataRole.UserRole, "group")
        characters.setData(0, Qt.ItemDataRole.UserRole + 1, "characters")
        root.addChild(characters)
        for character in project.manifest.characters:
            item = QTreeWidgetItem([character.display_name or character.full_name])
            item.setData(0, Qt.ItemDataRole.UserRole, "character")
            item.setData(0, Qt.ItemDataRole.UserRole + 1, character.id)
            item.setToolTip(0, self.tr("%1 — %2").replace("%1", character.role).replace("%2", character.primary_motivation).strip(" —"))
            characters.addChild(item)
        if same_project:
            for item in self._items():
                key = self._item_key(item)
                item.setExpanded(key in expanded or key not in known)
                if key == current:
                    self.setCurrentItem(item, 0, QItemSelectionModel.SelectionFlag.NoUpdate)
                item.setSelected(key in selected)
        else:
            self.expandAll()
        self.filter_characters(self.character_filter)
        if same_project:
            self.verticalScrollBar().setValue(scroll)

    def filter_characters(self, query: str) -> None:
        """Filter the character section by identity and descriptive metadata."""
        self.character_filter = query.casefold().strip()
        root = self.topLevelItem(0)
        if root is None:
            return
        for index in range(root.childCount()):
            group = root.child(index)
            if group.data(0, Qt.ItemDataRole.UserRole + 1) == "characters":
                for child_index in range(group.childCount()):
                    item = group.child(child_index)
                    character = next((c for c in self._characters if c.id == item.data(0, Qt.ItemDataRole.UserRole + 1)), None)
                    searchable = " ".join((character.full_name, character.display_name, character.role, character.description, character.primary_motivation, *character.aliases)) if character else item.text(0)
                    item.setHidden(bool(self.character_filter) and self.character_filter not in searchable.casefold())
                group.setHidden(bool(self.character_filter) and not any(not group.child(i).isHidden() for i in range(group.childCount())))
                break

    def reveal_item(self, kind: str, identifier: str) -> bool:
        """Select a stable project item, opening only its ancestor branches."""
        item = next((item for item in self._items() if self._item_key(item) == (kind, identifier)), None)
        if item is None or item.isHidden():
            return False
        ancestor = item.parent()
        while ancestor is not None:
            ancestor.setExpanded(True)
            ancestor = ancestor.parent()
        self.clearSelection()
        self.setCurrentItem(item)
        self.scrollToItem(item)
        self.setFocus()
        return True

    def _count_label(self, title: str, count: WordCount) -> str:
        if count.complete:
            word_count = self.tr("%n words", None, count.count)
        else:
            word_count = self.tr("At least %n words", None, count.count)
        return f"{title} — {word_count}"

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
        if kind in {"scene", "note", "character"} and isinstance(identifier, str):
            self.open_requested.emit(kind, identifier)

    def contextMenuEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        if item is not None and not item.isSelected():
            self.clearSelection()
            self.setCurrentItem(item)

        kind = item.data(0, Qt.ItemDataRole.UserRole) if item is not None else None
        identifier = (
            item.data(0, Qt.ItemDataRole.UserRole + 1)
            if item is not None
            else ""
        )
        menu = QMenu(self)
        actions = self.context_actions(str(kind or ""))
        for index, (label, action_id) in enumerate(actions):
            if index == 4:
                menu.addSeparator()
            self._add_context_action(menu, self._translate_context_action(label), action_id)
        selected = menu.exec(event.globalPos())
        if selected is not None:
            self.context_action_requested.emit(
                str(selected.data()), str(kind or ""), str(identifier or "")
            )

    @staticmethod
    def context_actions(kind: str) -> tuple[tuple[str, str], ...]:
        actions = [
            ("New Chapter", "new_chapter"),
            ("New Scene", "new_scene"),
            ("New Reference Note", "new_note"),
            ("New Character…", "new_character"),
        ]
        if kind == "character":
            actions.extend((
                ("Open", "open"),
                ("Find Scenes Mentioning Character…", "find_character_scenes"),
                ("Import Character Profile…", "import_character"),
                ("Export Character Profile…", "export_character"),
                ("Add Relationship…", "add_relationship"),
                ("Manage Relationships…", "manage_relationships"),
                ("Duplicate", "duplicate"),
                ("Remove", "remove"),
            ))
        elif kind in {"scene", "note"}:
            actions.extend(
                (("Open", "open"), ("Rename", "rename"), ("Duplicate", "duplicate"))
            )
            if kind == "scene":
                actions.extend(
                    (
                        ("Move Up", "move_up"),
                        ("Move Down", "move_down"),
                        ("Move to Chapter…", "move_to_chapter"),
                        ("Summarize Scene…", "summarize"),
                        ("Associate Characters…", "associate_character"),
                    )
                )
            else:
                actions.extend(
                    (
                        ("Link Note…", "link_note"),
                        ("Unlink Note…", "unlink_note"),
                        ("Open Linked Item…", "open_linked"),
                        (
                            "Check Continuity with Selected Scene…",
                            "continuity",
                        ),
                    )
                )
            actions.append(("Remove", "remove"))
        elif kind == "chapter":
            actions.extend(
                (
                    ("Rename", "rename"),
                    ("Move Up", "move_up"),
                    ("Move Down", "move_down"),
                    ("Remove", "remove"),
                )
            )
        actions.append(("Import Scene…", "import_scene"))
        return tuple(actions)

    def _translate_context_action(self, label: str) -> str:
        labels = {
            "New Chapter": self.tr("New Chapter"),
            "New Scene": self.tr("New Scene"),
            "New Reference Note": self.tr("New Reference Note"),
            "New Character…": self.tr("New Character…"),
            "Open": self.tr("Open"),
            "Find Scenes Mentioning Character…": self.tr("Find Scenes Mentioning Character…"),
            "Import Character Profile…": self.tr("Import Character Profile…"),
            "Export Character Profile…": self.tr("Export Character Profile…"),
            "Add Relationship…": self.tr("Add Relationship…"),
            "Manage Relationships…": self.tr("Manage Relationships…"),
            "Duplicate": self.tr("Duplicate"),
            "Remove": self.tr("Remove"),
            "Rename": self.tr("Rename"),
            "Move Up": self.tr("Move Up"),
            "Move Down": self.tr("Move Down"),
            "Move to Chapter…": self.tr("Move to Chapter…"),
            "Summarize Scene…": self.tr("Summarize Scene…"),
            "Associate Characters…": self.tr("Associate Characters…"),
            "Link Note…": self.tr("Link Note…"),
            "Unlink Note…": self.tr("Unlink Note…"),
            "Open Linked Item…": self.tr("Open Linked Item…"),
            "Check Continuity with Selected Scene…": self.tr("Check Continuity with Selected Scene…"),
            "Import Scene…": self.tr("Import Scene…"),
        }
        return labels.get(label, label)

    @staticmethod
    def _add_context_action(menu: QMenu, label: str, action_id: str) -> None:
        action = menu.addAction(label)
        action.setData(action_id)
