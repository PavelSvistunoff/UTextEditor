"""Keyboard-accessible picker for project items."""

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout


@dataclass(frozen=True)
class QuickOpenItem:
    kind: str
    id: str
    title: str
    context: str = ""
    aliases: tuple[str, ...] = ()


class QuickOpenDialog(QDialog):
    def __init__(self, items: tuple[QuickOpenItem, ...], parent=None, *, show_id: bool = True):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Quick Open"))
        self.resize(650, 450)
        self.items = items
        self.show_id = show_id
        layout = QVBoxLayout(self)
        self.query = QLineEdit(self)
        self.query.setPlaceholderText(self.tr("Search project items"))
        self.query.setAccessibleName(self.tr("Search project items"))
        self.results = QListWidget(self)
        self.results.setAccessibleName(self.tr("Matching project items"))
        layout.addWidget(self.query)
        layout.addWidget(self.results)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.query.textChanged.connect(self._filter)
        self.query.returnPressed.connect(self._accept_selection)
        self.results.itemActivated.connect(lambda _: self._accept_selection())
        down = QShortcut(QKeySequence(Qt.Key.Key_Down), self.query)
        down.setContext(Qt.ShortcutContext.WidgetShortcut)
        down.activated.connect(self.results.setFocus)
        self._filter("")

    def _filter(self, query: str) -> None:
        self.results.clear()
        query = query.casefold().strip()
        types = {"scene": self.tr("Scene"), "chapter": self.tr("Chapter"),
                 "note": self.tr("Reference note"), "character": self.tr("Character"),
                 "tab": self.tr("Tab")}
        for entry in self.items:
            if query not in " ".join((entry.title, entry.context, *entry.aliases)).casefold():
                continue
            context = f" — {entry.context}" if entry.context else ""
            identifier = f" [{entry.id}]" if self.show_id else ""
            item = QListWidgetItem(f"{entry.title} — {types[entry.kind]}{context}{identifier}")
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.results.addItem(item)
        if self.results.count():
            self.results.setCurrentRow(0)

    def _accept_selection(self) -> None:
        if self.results.currentItem() is not None:
            self.accept()

    def selected(self) -> QuickOpenItem | None:
        item = self.results.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None
