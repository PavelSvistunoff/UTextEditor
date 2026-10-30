"""Session-only AI task status, without request or response content."""

from dataclasses import dataclass
from time import monotonic
from typing import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDockWidget, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QProgressBar, QPushButton,
                               QVBoxLayout, QWidget)

_ACTIVE = {"queued", "running", "cancelling"}
_HISTORY_LIMIT = 100


@dataclass
class Activity:
    name: str
    context: str
    cancel: Callable[[], None] | None
    show: Callable[[], None] | None = None
    retry: Callable[[], None] | None = None
    state: str = "queued"
    created: float = 0
    finished: float | None = None
    detail: str = ""
    was_running: bool = False


class AIActivityPanel(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(self.tr("AI activity"), parent)
        self.setObjectName("aiActivityDock")
        self.activities: list[Activity] = []
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel(self.tr("AI tasks for this session. Manuscript text is not shown.")))
        self.list = QListWidget(widget)
        self.list.setAccessibleName(self.tr("AI tasks"))
        layout.addWidget(self.list)
        buttons = QHBoxLayout()
        self.cancel_button = QPushButton(self.tr("Cancel task"), widget)
        self.cancel_button.clicked.connect(self._cancel_selected)
        self.cancel_button.setEnabled(False)
        buttons.addWidget(self.cancel_button)
        self.show_button = QPushButton(self.tr("Show progress"), widget)
        self.show_button.clicked.connect(self._show_selected)
        self.show_button.setEnabled(False)
        buttons.addWidget(self.show_button)
        self.retry_button = QPushButton(self.tr("Retry"), widget)
        self.retry_button.clicked.connect(self._retry_selected)
        self.retry_button.setEnabled(False)
        buttons.addWidget(self.retry_button)
        layout.addLayout(buttons)
        self.list.currentRowChanged.connect(self._selection_changed)
        self.setWidget(widget)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.status_button = QPushButton(self.tr("AI activity"), parent)
        self.status_button.setAccessibleName(self.tr("Show AI activity"))
        self.status_button.clicked.connect(self._toggle)
        self.busy = QProgressBar(parent)
        self.busy.setRange(0, 0)
        self.busy.setTextVisible(False)
        self.busy.setFixedWidth(30)
        self.busy.setAccessibleName(self.tr("AI tasks in progress"))
        self.busy.hide()

    def _toggle(self):
        self.setVisible(not self.isVisible())

    def add(self, name: str, context: str = "", cancel=None, show=None, retry=None) -> Activity:
        item = Activity(name, context, cancel, show, retry, created=monotonic())
        self.activities.append(item)
        self._trim()
        self.refresh()
        return item

    def set_state(self, item: Activity, state: str) -> None:
        if item.state not in _ACTIVE:
            return
        if item.state == "cancelling" and state == "running":
            return
        item.state = state
        if state == "running":
            item.was_running = True
        if state not in _ACTIVE:
            item.finished = monotonic()
            item.cancel = None
            item.show = None
            if state != "failed":
                item.retry = None
            self._trim()
        self.refresh()

    def _trim(self):
        while len(self.activities) > _HISTORY_LIMIT:
            old = next((a for a in self.activities if a.state not in _ACTIVE), None)
            if old is None:
                break
            self.activities.remove(old)

    def set_detail(self, item: Activity, detail: str) -> None:
        if item.state in _ACTIVE:
            item.detail = detail
            self.refresh()

    def refresh(self):
        selected = self.list.currentRow()
        scroll = self.list.verticalScrollBar().value()
        self.list.clear()
        names = {"queued": self.tr("Queued"), "running": self.tr("Running"),
                 "cancelling": self.tr("Cancelling…"),
                 "cancelled": self.tr("Cancelled"), "completed": self.tr("Completed"),
                 "failed": self.tr("Failed — check the workflow message"), "discarded": self.tr("Discarded: context changed")}
        for item in self.activities:
            seconds = max(0, int((item.finished or monotonic()) - item.created))
            context = f" — {item.context}" if item.context else ""
            detail = f" — {item.detail}" if item.detail and item.state in _ACTIVE else ""
            status = (self.tr("Cancelling after the current request…")
                      if item.state == "cancelling" and item.was_running else names[item.state])
            self.list.addItem(QListWidgetItem(f"{item.name}{context} — {status}{detail} ({seconds}s)"))
        if 0 <= selected < self.list.count():
            self.list.setCurrentRow(selected)
        self.list.verticalScrollBar().setValue(scroll)
        self._selection_changed()
        active = [item for item in self.activities if item.state in _ACTIVE]
        self.busy.setVisible(bool(active))
        label = active[0].name if len(active) == 1 else self.tr("AI activity")
        self.status_button.setText(label + (f" ({len(active)})" if len(active) > 1 else ""))

    def _selection_changed(self, *_args):
        row = self.list.currentRow()
        item = self.activities[row] if 0 <= row < len(self.activities) else None
        self.cancel_button.setEnabled(bool(item and item.cancel and item.state in {"queued", "running"}))
        self.show_button.setEnabled(bool(item and item.show and item.state in _ACTIVE))
        self.retry_button.setEnabled(bool(item and item.retry and item.state == "failed"))

    def _cancel_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.activities):
            item = self.activities[row]
            if item.cancel and item.state in {"queued", "running"}:
                self.set_state(item, "cancelling")
                item.cancel()

    def _show_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.activities):
            item = self.activities[row]
            if item.show and item.state in _ACTIVE:
                item.show()

    def _retry_selected(self):
        row = self.list.currentRow()
        if 0 <= row < len(self.activities):
            item = self.activities[row]
            if item.retry and item.state == "failed":
                item.retry()
