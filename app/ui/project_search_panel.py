"""Persistent controls and results for project-wide text search."""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget


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
        self.search_button = QPushButton(self.tr("Search"), self)
        self.cancel_button = QPushButton(self.tr("Cancel"), self)
        self.cancel_button.setEnabled(False)
        row.addWidget(self.query)
        row.addWidget(self.search_button)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = QListWidget(self)
        self.results.setAccessibleName(self.tr("Project search results"))
        layout.addWidget(self.results)
        self.query.returnPressed.connect(self._request)
        self.search_button.clicked.connect(self._request)
        self.cancel_button.clicked.connect(self.cancel_requested)
        self.results.itemActivated.connect(lambda item: self.result_requested.emit(item.data(Qt.ItemDataRole.UserRole)))

    def _request(self):
        self.search_requested.emit(self.query.text())

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
