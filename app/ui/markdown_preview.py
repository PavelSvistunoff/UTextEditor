"""Bounded, read-only Markdown preview for an editor buffer."""

from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtGui import QTextCursor, QTextDocument
from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from .workers import FunctionWorker


MAX_MARKDOWN_CHARACTERS = 64 * 1024
MAX_RENDERED_CHARACTERS = 1024 * 1024


class _OfflineDocument(QTextDocument):
    def loadResource(self, resource_type, name):
        return None


class _OfflineBrowser(QTextBrowser):
    def loadResource(self, resource_type, name):
        return None


def render_markdown(text: str) -> str:
    document = _OfflineDocument()
    document.setMarkdown(text)
    html = document.toHtml()
    if len(html) > MAX_RENDERED_CHARACTERS:
        raise ValueError("Rendered preview is too large")
    return html


class MarkdownPreview(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.editor = None
        self.generation = 0
        self.worker = None
        self.status = QLabel(self)
        self.status.setWordWrap(True)
        self.browser = _OfflineBrowser(self)
        self.browser.setAccessibleName(self.tr("Markdown preview"))
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        self.browser.setReadOnly(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addWidget(self.browser)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._render)

    def set_editor(self, editor) -> None:
        self.editor = editor
        self.changed()

    def changed(self) -> None:
        self.generation += 1
        self.timer.stop()
        self.browser.clear()
        if self.editor is None:
            self.status.setText(self.tr("No active document."))
            return
        self.status.setText(self.tr("Updating preview…"))
        self.timer.start(300)

    def _render(self) -> None:
        if self.worker is not None or self.editor is None:
            return
        editor = self.editor
        generation = self.generation
        revision = editor.revision
        truncated = editor.document().characterCount() - 1 > MAX_MARKDOWN_CHARACTERS
        if truncated:
            cursor = QTextCursor(editor.document())
            cursor.setPosition(MAX_MARKDOWN_CHARACTERS, QTextCursor.MoveMode.KeepAnchor)
            text = cursor.selectedText().replace("\u2029", "\n").replace("\u2028", "\n")
        else:
            text = editor.toPlainText()
        worker = FunctionWorker(render_markdown, text)
        self.worker = worker

        def ready(html):
            if self.editor is editor and self.generation == generation and editor.revision == revision:
                self.browser.setHtml(html)
                self.status.setText(
                    self.tr("Preview shows only the beginning of this document; external resources are disabled.")
                    if truncated else self.tr("Read-only preview; external resources are disabled.")
                )

        def failed(_error):
            if self.generation == generation:
                self.status.setText(self.tr("Could not render this Markdown preview."))

        def done():
            self.worker = None
            if self.generation != generation and self.editor is not None:
                self.timer.start(300)

        worker.signals.finished.connect(ready, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
        worker.signals.done.connect(done, Qt.ConnectionType.QueuedConnection)
        QThreadPool.globalInstance().start(worker)
