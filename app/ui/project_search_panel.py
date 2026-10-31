"""Persistent controls and results for project-wide text search."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QVBoxLayout, QWidget


class ProjectSearchPanel(QWidget):
    search_requested = Signal(str)
    cancel_requested = Signal()
    result_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.query = QLineEdit(self)
        self.query.setPlaceholderText(self.tr("Search project text"))
        self.query.setAccessibleName(self.tr("Search project text"))
        self.query.setAccessibleDescription(self.tr("Press Down to move to search results."))
        self.search_button = QPushButton(self.tr("Search"), self)
        self.cancel_button = QPushButton(self.tr("Cancel"), self)
        self.cancel_button.setEnabled(False)
        row.addWidget(self.query)
        row.addWidget(self.search_button)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        self.status = QLabel(self)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        self.status_scroll = QScrollArea(self)
        self.status_scroll.setWidgetResizable(True)
        self.status_scroll.setMaximumHeight(120)
        self.status_scroll.setWidget(self.status)
        layout.addWidget(self.status_scroll)
        self.results = QListWidget(self)
        self.results.setAccessibleName(self.tr("Project search results"))
        self.results.setAccessibleDescription(self.tr("Use arrow keys to choose a result and Enter to open it."))
        layout.addWidget(self.results)
        self.query.returnPressed.connect(self._request)
        self.search_button.clicked.connect(self._request)
        self.cancel_button.clicked.connect(self.cancel_requested)
        self.results.itemActivated.connect(lambda item: self.result_requested.emit(item.data(Qt.ItemDataRole.UserRole)))
        down = QShortcut(QKeySequence(Qt.Key.Key_Down), self.query)
        down.setContext(Qt.ShortcutContext.WidgetShortcut)
        down.activated.connect(self._focus_results)
        for key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            shortcut = QShortcut(QKeySequence(key), self.results)
            shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
            shortcut.activated.connect(self._open_selected_result)

    def _request(self):
        self.search_requested.emit(self.query.text())

    def _focus_results(self):
        if self.results.count():
            if self.results.currentRow() < 0:
                self.results.setCurrentRow(0)
            self.results.setFocus()

    def _open_selected_result(self):
        item = self.results.currentItem()
        if item is not None:
            self.result_requested.emit(item.data(Qt.ItemDataRole.UserRole))

    def set_running(self, running: bool):
        self.cancel_button.setEnabled(running)

    def set_results(self, result):
        self.results.clear()
        for match in result.matches:
            kind = self.tr("Scene") if match.kind == "scene" else self.tr("Reference note")
            item = QListWidgetItem(f"{kind}: {match.title} — {match.line}:{match.column}\n{match.excerpt}")
            item.setData(Qt.ItemDataRole.UserRole, match)
            self.results.addItem(item)
        if result.cancelled:
            message = self.tr("Search cancelled.")
        elif result.limited:
            message = self.tr("Result limit reached.")
        else:
            message = self.tr("Search finished.")
        if result.errors:
            message += "\n" + "\n".join(result.errors)
        if result.omitted_errors:
            message += "\n" + self.tr("Additional unreadable files omitted: %1").replace("%1", str(result.omitted_errors))
        self.status.setText(message)
