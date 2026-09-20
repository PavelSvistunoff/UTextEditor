"""Reusable QThreadPool worker with cooperative cancellation."""

from PySide6.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(object)


class FunctionWorker(QRunnable):
    def __init__(self, function, *args, **kwargs) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.cancelled = False

    def cancel(self) -> None:
        self.cancelled = True

    def run(self) -> None:
        if self.cancelled:
            return
        try:
            result = self.function(*self.args, **self.kwargs)
            if not self.cancelled:
                try:
                    self.signals.finished.emit(result)
                except RuntimeError as exc:
                    if "Signal source has been deleted" not in str(exc):
                        raise
        except Exception as exc:  # delivered to the GUI for explicit handling
            if not self.cancelled:
                try:
                    self.signals.failed.emit(exc)
                except RuntimeError as exc:
                    if "Signal source has been deleted" not in str(exc):
                        raise
