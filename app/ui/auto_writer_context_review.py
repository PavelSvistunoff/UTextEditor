"""Queued GUI source reviews requested by the sequential Auto-writer worker."""

from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Event

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QDialog

from app.project.auto_writer_context import ContextReviewDecision
from app.project.rag_context import CapturedContext
from .rag_completion import RAGCompletionDialog


@dataclass
class PendingContextReview:
    title: str
    captured: CapturedContext
    excluded: frozenset[str]
    ready: Event = field(default_factory=Event)
    decision: ContextReviewDecision = field(default_factory=lambda: ContextReviewDecision("cancel"))


class AutoWriterContextReview(QObject):
    requested = Signal(object)

    def __init__(self, destination: str, *, is_current: Callable[[], bool],
                 is_cancelled: Callable[[], bool], cancel: Callable[[], None], parent=None,
                 excludable_kinds: frozenset[str] = frozenset({"scene"}),
                 extra_summary: str | None = None, review_title: str | None = None) -> None:
        super().__init__(parent)
        self.destination = destination
        self.is_current = is_current
        self.is_cancelled = is_cancelled
        self.cancel = cancel
        self.excludable_kinds = excludable_kinds
        self.extra_summary = extra_summary
        self.review_title = review_title
        self.requested.connect(self._show_review, Qt.ConnectionType.QueuedConnection)

    def review(self, title: str, captured: CapturedContext, excluded: frozenset[str]) -> ContextReviewDecision:
        """Worker entry: emit immutable context; never access widgets on this thread."""
        if self.is_cancelled():
            return ContextReviewDecision("cancel")
        pending = PendingContextReview(title, captured, excluded)
        self.requested.emit(pending)
        while not pending.ready.wait(0.05):
            if self.is_cancelled():
                return ContextReviewDecision("cancel")
        return ContextReviewDecision("cancel") if self.is_cancelled() else pending.decision

    def _show_review(self, pending: PendingContextReview) -> None:
        dialog = None
        try:
            if not self.is_current() or self.is_cancelled():
                self.cancel()
                return
            dialog = RAGCompletionDialog(
                self.destination, pending.captured, pending.excluded, self.parent(),
                excludable_kinds=self.excludable_kinds,
                extra_summary=self.extra_summary if self.extra_summary is not None else self.tr(
                    "Auto-writer keeps all full reference notes, profiles and recorded development in the mandatory prompt. "
                    "The manifest describes optional manuscript retrieval; omitting a reference from that search does not remove it from the prompt. "
                    "Earlier generated drafts are provisional and may later be rejected."
                ),
            )
            dialog.setWindowTitle((self.review_title or self.tr("Review Auto-writer context")) + ": " + pending.title)
            watcher = QTimer(dialog)
            watcher.setInterval(50)
            watcher.timeout.connect(lambda: dialog.reject() if not self.is_current() or self.is_cancelled() else None)
            watcher.start()
            result = dialog.exec()
            watcher.stop()
            if not self.is_current() or self.is_cancelled():
                self.cancel()
            elif result == RAGCompletionDialog.REBUILD:
                pending.decision = ContextReviewDecision("rebuild", dialog.excluded_ids())
            elif result == QDialog.DialogCode.Accepted:
                pending.decision = ContextReviewDecision("send", dialog.excluded_ids())
            else:
                self.cancel()
        finally:
            if dialog is not None:
                dialog.deleteLater()
            pending.ready.set()
