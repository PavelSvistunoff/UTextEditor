"""Background maintenance of the disposable saved-project retrieval cache."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer, Qt, Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from app.project.rag_index import IndexStatus, LexicalIndex
from app.project.rag_sources import CaptureCancelled, capture_project_sources
from app.project.service import Project
from .workers import FunctionWorker


class RetrievalIndexDialog(QDialog):
    worker_started = Signal(object)

    def __init__(self, project: Project, cache_root: Path, *,
                 is_current: Callable[[], bool], parent=None) -> None:
        super().__init__(parent)
        self.project = project
        self.cache_root = cache_root
        self._is_current = is_current
        self._closed = False
        self.destroyed.connect(lambda: setattr(self, "_closed", True))
        self._worker: FunctionWorker | None = None
        self.setWindowTitle(self.tr("Retrieval Index"))
        self.resize(660, 350)
        self.setModal(False)
        layout = QVBoxLayout(self)
        description = QLabel(self.tr(
            "This local cache contains saved manuscript and character text and can be rebuilt "
            "from project files. Unsaved edits are not stored. Index maintenance is local."
        ), self)
        description.setWordWrap(True)
        layout.addWidget(description)
        self.status = QPlainTextEdit(self.tr("Checking index…"), self)
        self.status.setReadOnly(True)
        self.status.setAccessibleName(self.tr("Retrieval index status"))
        layout.addWidget(self.status)
        location = QLabel(self.tr("Cache directory: {path}").format(path=cache_root / "retrieval"), self)
        location.setWordWrap(True)
        location.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(location)
        controls = QHBoxLayout()
        self.status_button = QPushButton(self.tr("Check Status"), self)
        self.refresh_button = QPushButton(self.tr("Refresh"), self)
        self.rebuild_button = QPushButton(self.tr("Rebuild"), self)
        self.delete_button = QPushButton(self.tr("Delete Cache"), self)
        self.cancel_button = QPushButton(self.tr("Cancel Operation"), self)
        self.close_button = QPushButton(self.tr("Close"), self)
        self._operation_buttons = (self.status_button, self.refresh_button, self.rebuild_button, self.delete_button)
        for button, operation in zip(self._operation_buttons, ("status", "refresh", "rebuild", "delete"), strict=True):
            button.clicked.connect(lambda _checked=False, operation=operation: self.start(operation))
            controls.addWidget(button)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setEnabled(False)
        controls.addWidget(self.cancel_button)
        layout.addLayout(controls)
        layout.addWidget(self.close_button)
        self.close_button.clicked.connect(self.reject)
        self.finished.connect(self._finished)
        QTimer.singleShot(0, lambda: self.start("status"))

    def _finished(self, _result: int) -> None:
        self._closed = True
        if self._worker is not None:
            self._worker.cancel()

    def cancel_operation(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self.status.setPlainText(self.tr("Cancelling…"))
            self.cancel_button.setEnabled(False)

    def start(self, operation: str) -> None:
        if self._closed or self._worker is not None:
            return
        if not self._is_current():
            self._invalidate()
            return
        if operation not in {"status", "refresh", "rebuild", "delete"}:
            raise ValueError("Unknown retrieval index operation.")

        # This predicate reads plain Python generation/identity values only.
        # The owning window must not inspect Qt widgets in its callback.
        def cancelled() -> bool:
            return worker.cancelled or self._closed or not self._is_current()

        def run() -> IndexStatus:
            if cancelled():
                raise CaptureCancelled("Retrieval maintenance became stale.")
            index = LexicalIndex(self.cache_root, self.project.root, self.project.manifest.project_id)
            if operation == "status":
                return index.status()
            if operation == "delete":
                return index.delete(is_cancelled=cancelled)
            capture = capture_project_sources(self.project, is_cancelled=cancelled)
            return index.refresh(capture, force=operation == "rebuild", is_cancelled=cancelled)

        worker = FunctionWorker(run)
        self._worker = worker
        for button in self._operation_buttons:
            button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.status.setPlainText(self.tr("Working…"))
        worker.signals.finished.connect(lambda result: self._completed(worker, result), Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda error: self._failed(worker, error), Qt.ConnectionType.QueuedConnection)
        worker.signals.done.connect(lambda: self._done(worker), Qt.ConnectionType.QueuedConnection)
        self.worker_started.emit(worker)
        QThreadPool.globalInstance().start(worker)

    def _current(self, worker: FunctionWorker) -> bool:
        return self._worker is worker and not self._closed and not worker.cancelled and self._is_current()

    def _completed(self, worker: FunctionWorker, result: IndexStatus) -> None:
        if not self._current(worker):
            return
        descriptions = {
            "ready": self.tr("Ready: {sources} sources, {chunks} passages. Refresh to check saved changes."),
            "incomplete": self.tr("Incomplete: {sources} sources, {chunks} passages. Some sources were omitted."),
            "missing": self.tr("No index. Refresh or rebuild to create it from saved project files."),
            "unavailable": self.tr("SQLite FTS5 is unavailable. Editing and existing AI workflows remain available."),
            "rebuild_required": self.tr("Index format changed. Refresh or rebuild before using it."),
            "error": self.tr("Index could not be read. Try rebuilding it."),
        }
        text = descriptions[result.state].format(sources=result.source_count, chunks=result.chunk_count)
        if result.diagnostics:
            text += "\n\n" + "\n".join(result.diagnostics[:10])
            if len(result.diagnostics) > 10:
                text += "\n" + self.tr("{count} additional source diagnostics.").format(count=len(result.diagnostics) - 10)
        self.status.setPlainText(text)

    def _failed(self, worker: FunctionWorker, error: Exception) -> None:
        if self._current(worker):
            self.status.setPlainText(self.tr("Index operation failed: {error}").format(error=error))

    def _done(self, worker: FunctionWorker) -> None:
        if self._worker is not worker:
            return
        self._worker = None
        if self._closed:
            return
        self.cancel_button.setEnabled(False)
        if not self._is_current():
            self._invalidate()
            return
        if worker.cancelled:
            self.status.setPlainText(self.tr("Operation cancelled. Check status before retrying."))
        for button in self._operation_buttons:
            button.setEnabled(True)

    def _invalidate(self) -> None:
        self.status.setPlainText(self.tr("Project changed. Close and reopen index maintenance."))
        for button in self._operation_buttons:
            button.setEnabled(False)
        self.cancel_button.setEnabled(False)
