"""Reusable QThreadPool worker with cooperative cancellation."""

from threading import Lock

from PySide6.QtCore import QObject, QRunnable, Signal


class WorkerSignals(QObject):
    started = Signal()
    cancelling = Signal()
    finished = Signal(object)
    failed = Signal(object)
    done = Signal()


class FunctionWorker(QRunnable):
    def __init__(self, function, *args, **kwargs) -> None:
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.cancelled = False

    def cancel(self) -> None:
        if self.cancelled:
            return
        self.cancelled = True
        try:
            self.signals.cancelling.emit()
        except RuntimeError as exc:
            if "Signal source has been deleted" not in str(exc) and "already deleted" not in str(exc):
                raise

    def run(self) -> None:
        try:
            if self.cancelled:
                return
            self.signals.started.emit()
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
        finally:
            try:
                self.signals.done.emit()
            except RuntimeError as exc:
                if "Signal source has been deleted" not in str(exc):
                    raise


class StreamingWorker(FunctionWorker):
    """Collect provisional chunks for periodic GUI-thread draining."""

    MAX_OUTPUT_CHARS = 256 * 1024

    def __init__(self, function, *args, **kwargs) -> None:
        self._chunks: list[str] = []
        self._size = 0
        self._lock = Lock()
        def generate():
            result = function(*args, on_chunk=self._append,
                              is_cancelled=lambda: self.cancelled, **kwargs)
            if not isinstance(result, str) or len(result) > self.MAX_OUTPUT_CHARS:
                raise ValueError("Invalid or oversized streaming result")
            return result
        super().__init__(generate)

    def _append(self, chunk: str) -> None:
        if not isinstance(chunk, str):
            raise ValueError("Invalid streaming text")
        if not chunk:
            return
        with self._lock:
            self._size += len(chunk)
            if self._size > self.MAX_OUTPUT_CHARS:
                raise ValueError("Streaming output exceeded the preview limit")
            self._chunks.append(chunk)

    def take_chunks(self) -> str:
        with self._lock:
            chunks, self._chunks = self._chunks, []
        return "".join(chunks)
