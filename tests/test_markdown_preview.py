"""Offline tests for the bounded, presentation-only Markdown preview."""

from threading import Event

import pytest
from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from app.ui.editor_widget import EditorWidget
from app.ui.markdown_preview import MAX_MARKDOWN_CHARACTERS, MarkdownPreview, render_markdown


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def wait_until(predicate):
    loop = QEventLoop()
    poll = QTimer()
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start(5)
    deadline.start(3000)
    if not predicate():
        loop.exec()
    assert predicate()


def test_preview_updates_unsaved_buffer_without_modifying_it(app):
    editor = EditorWidget()
    editor.setPlainText("# Draft\n\n**unsaved**")
    revision = editor.revision
    panel = MarkdownPreview()
    panel.set_editor(editor)
    wait_until(lambda: "unsaved" in panel.browser.toPlainText())
    assert panel.browser.isReadOnly()
    assert editor.toPlainText() == "# Draft\n\n**unsaved**"
    assert editor.revision == revision
    assert panel.browser.loadResource(QTextDocument.ResourceType.ImageResource, QUrl("https://example.com/x")) is None
    assert panel.browser.loadResource(QTextDocument.ResourceType.ImageResource, QUrl("file:///private/x")) is None
    panel.close()


def test_large_document_renders_a_bounded_prefix_without_modifying_text(app, monkeypatch):
    editor = EditorWidget()
    source = "# Start\n\n" + "x" * (MAX_MARKDOWN_CHARACTERS - 10) + "😀END"
    editor.setPlainText(source)
    revision = editor.revision
    panel = MarkdownPreview()
    with monkeypatch.context() as bounded:
        bounded.setattr(editor, "toPlainText", lambda: pytest.fail("Preview copied the complete large document"))
        panel.set_editor(editor)
        wait_until(lambda: "only the beginning" in panel.status.text())
    assert "Start" in panel.browser.toPlainText()
    assert "END" not in panel.browser.toPlainText()
    assert editor.toPlainText() == source and editor.revision == revision
    panel.close()


def test_stale_render_is_discarded_after_editor_switch(app, monkeypatch):
    first, second = EditorWidget(), EditorWidget()
    first.setPlainText("old draft")
    second.setPlainText("new draft")
    started, release = Event(), Event()

    def slow_render(text):
        if text == "old draft":
            started.set()
            assert release.wait(3)
        return render_markdown(text)

    monkeypatch.setattr("app.ui.markdown_preview.render_markdown", slow_render)
    panel = MarkdownPreview()
    try:
        panel.set_editor(first)
        panel._render()
        wait_until(started.is_set)
        panel.set_editor(second)
        release.set()
        wait_until(lambda: "new draft" in panel.browser.toPlainText())
        assert "old draft" not in panel.browser.toPlainText()
    finally:
        release.set()
        panel.close()
