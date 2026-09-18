"""Document tabs and per-tab editor state."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabWidget

from app.document.document import Document
from .editor_widget import EditorWidget


class DocumentTabWidget(QTabWidget):
    document_changed = Signal()
    editor_created = Signal(object)
    close_requested = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_requested.emit)
        self.currentChanged.connect(lambda _: self.document_changed.emit())

    def add_document(self, document: Document) -> EditorWidget:
        editor = EditorWidget()
        editor.setPlainText(document.text)
        editor.document_state = document
        editor.content_changed.connect(lambda: self._update_tab_title(editor))
        index = self.addTab(editor, document.display_name)
        self.setCurrentIndex(index)
        self._update_tab_title()
        self.editor_created.emit(editor)
        return editor

    def new_document(self) -> EditorWidget:
        return self.add_document(Document())

    def current_editor(self) -> EditorWidget | None:
        widget = self.currentWidget()
        return widget if isinstance(widget, EditorWidget) else None

    def _update_tab_title(self, editor: EditorWidget | None = None) -> None:
        editor = editor or self.current_editor()
        if editor is None:
            return
        index = self.indexOf(editor)
        if index < 0:
            return
        document = editor.document_state
        document.update_text(editor.toPlainText())
        title = document.display_name + (" *" if document.dirty else "")
        self.setTabText(index, title)
        self.document_changed.emit()

    def remove_tab(self, index: int) -> None:
        widget = self.widget(index)
        if widget is not None:
            widget.deleteLater()
        self.removeTab(index)
