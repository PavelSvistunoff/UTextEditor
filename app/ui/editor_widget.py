"""QPlainTextEdit with non-destructive inline completions."""

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QKeySequence, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QTextEdit, QWidget

from app.ai.models import Suggestion
from app.ai.validation import valid_suggestion
from app.document.encoding import python_index_to_qt_position, qt_position_to_python_index


class LineNumberArea(QWidget):
    def __init__(self, editor: "EditorWidget") -> None:
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.palette().alternateBase())
        painter.setPen(self.palette().text().color())
        painter.setFont(self.editor.font())

        block = self.editor.firstVisibleBlock()
        if not block.isValid():
            painter.end()
            return

        block_number = block.blockNumber()
        top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and top >= event.rect().top():
                painter.drawText(
                    0,
                    top,
                    self.width() - 4,
                    self.editor.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    str(block_number + 1),
                )
            block = block.next()
            if not block.isValid():
                break
            block_number = block.blockNumber()
            top = int(self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top())
        painter.end()


class EditorWidget(QPlainTextEdit):
    completion_accepted = Signal(str)
    completion_rejected = Signal()
    content_changed = Signal()
    escape_pressed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._ghost_text = ""
        self._ghost_position = -1
        self._ghost_selection = (0, 0)
        self._ghost_revision = -1
        self._revision = 0
        self._history_action: str | None = None
        self._show_line_numbers = False
        self._line_number_area = LineNumberArea(self)
        self.spell_suggestions: list[Suggestion] = []
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._invalidate_completion)
        self.selectionChanged.connect(self._invalidate_completion)
        self.updateRequest.connect(lambda _rect, _dy: self._line_number_area.update())
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def apply_settings(self, settings) -> None:
        font = QFont(settings.font_family or "Monospace")
        font.setPointSize(settings.font_size)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * max(2, int(settings.tab_width)))
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth if bool(settings.word_wrap) else QPlainTextEdit.LineWrapMode.NoWrap)
        self._show_line_numbers = bool(settings.line_numbers)
        self._update_line_number_area()

    def line_number_area_width(self) -> int:
        if not self._show_line_numbers:
            return 0
        digits = max(1, len(str(max(1, self.blockCount()))))
        return 12 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_line_number_area(self) -> None:
        if self._show_line_numbers:
            self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
            self._line_number_area.show()
            self._line_number_area.setGeometry(QRect(0, 0, self.line_number_area_width(), self.height()))
        else:
            self.setViewportMargins(0, 0, 0, 0)
            self._line_number_area.hide()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._update_line_number_area()

    @property
    def revision(self) -> int:
        return self._revision

    def _on_text_changed(self) -> None:
        self._revision += 1
        self.clear_completion()
        self.set_spell_suggestions([])
        self.content_changed.emit()

    @staticmethod
    def _selection_bounds(cursor: QTextCursor) -> tuple[int, int]:
        if cursor.hasSelection():
            return cursor.selectionStart(), cursor.selectionEnd()
        return cursor.position(), cursor.position()

    def _invalidate_completion(self) -> None:
        if self._ghost_text:
            cursor = self.textCursor()
            selection = self._selection_bounds(cursor)
            if cursor.position() != self._ghost_position or selection != self._ghost_selection:
                self.clear_completion()

    @property
    def has_completion(self) -> bool:
        cursor = self.textCursor()
        selection = self._selection_bounds(cursor)
        return bool(self._ghost_text) and self._ghost_revision == self._revision and cursor.position() == self._ghost_position and selection == self._ghost_selection

    def show_completion(self, text: str, revision: int, position: int) -> None:
        cursor = self.textCursor()
        if not text.strip() or "\n" in text or "\r" in text or cursor.hasSelection() or revision != self._revision or position != cursor.position():
            return
        source = self.toPlainText()
        suffix = source[qt_position_to_python_index(source, position):]
        if suffix.startswith(text.strip()):
            return
        available = max(1, self.viewport().width() - self.cursorRect().left())
        if QFontMetrics(self.font()).horizontalAdvance(text) > available:
            return
        self._ghost_text = text
        self._ghost_position = position
        self._ghost_revision = revision
        self._ghost_selection = (position, position)
        self.viewport().update()

    def clear_completion(self) -> None:
        if self._ghost_text:
            self._ghost_text = ""
            self._ghost_position = -1
            self._ghost_revision = -1
            self._ghost_selection = (0, 0)
            self.viewport().update()

    def accept_completion(self) -> bool:
        if not self.has_completion:
            return False
        cursor = self.textCursor()
        text = self._completion_text_for_cursor(self._ghost_text, cursor)
        cursor.beginEditBlock()
        cursor.insertText(text)
        cursor.endEditBlock()
        self.clear_completion()
        self.completion_accepted.emit(text)
        return True

    @staticmethod
    def _completion_text_for_cursor(completion: str, cursor: QTextCursor) -> str:
        """Avoid joining the last typed word to a word-only completion."""
        if not completion or completion[0].isspace() or cursor.position() == 0:
            return completion
        document_text = cursor.document().toPlainText()
        python_position = qt_position_to_python_index(document_text, cursor.position())
        if python_position == 0:
            return completion
        previous = document_text[python_position - 1]
        if previous.isalnum() and completion[0].isalnum():
            return f" {completion}"
        return completion

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if not self.has_completion:
            return
        painter = QPainter(self.viewport())
        painter.setPen(QColor("#8a8a8a"))
        painter.setFont(self.font())
        rect = self.cursorRect()
        metrics = QFontMetrics(self.font())
        x, y = rect.left(), rect.top() + metrics.ascent()
        available = max(1, self.viewport().width() - x)
        # Ghost text is intentionally non-destructive: render only in the viewport and
        # never mutate the underlying document while the suggestion is visible.
        painter.drawText(QRect(x, y, available, metrics.height()), Qt.AlignmentFlag.AlignLeft, self._ghost_text)
        painter.end()

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Undo):
            self.undo()
            event.accept()
            return
        if event.matches(QKeySequence.StandardKey.Redo):
            self.redo()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Tab and self.accept_completion():
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.has_completion:
            self.clear_completion()
            self.completion_rejected.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape:
            self.escape_pressed.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def undo(self) -> None:
        self._history_action = "undo"
        try:
            super().undo()
        finally:
            self._history_action = None

    def redo(self) -> None:
        self._history_action = "redo"
        try:
            super().redo()
        finally:
            self._history_action = None

    def set_spell_suggestions(self, suggestions: list[Suggestion]) -> None:
        self.spell_suggestions = [
            suggestion for suggestion in suggestions
            if valid_suggestion(suggestion, self.toPlainText(), self.revision)
        ]
        selections = []
        for suggestion in self.spell_suggestions:
            cursor = self.textCursor()
            source = self.toPlainText()
            cursor.setPosition(python_index_to_qt_position(source, suggestion.start))
            cursor.setPosition(python_index_to_qt_position(source, suggestion.end), QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setUnderlineColor(QColor("#d55e5e"))
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = fmt
            selections.append(selection)
        self.setExtraSelections(selections)

    def apply_spell_suggestions(self, suggestions: list[Suggestion]) -> int:
        """Explicitly apply valid, non-overlapping corrections as one undo step."""
        source = self.toPlainText()
        valid = sorted((item for item in suggestions if valid_suggestion(item, source, self.revision)), key=lambda item: item.start)
        non_overlapping: list[Suggestion] = []
        for suggestion in valid:
            if non_overlapping and suggestion.start < non_overlapping[-1].end:
                continue
            non_overlapping.append(suggestion)
        if not non_overlapping:
            return 0

        cursor = self.textCursor()
        cursor.beginEditBlock()
        for suggestion in reversed(non_overlapping):
            start = python_index_to_qt_position(source, suggestion.start)
            end = python_index_to_qt_position(source, suggestion.end)
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            original = source[suggestion.start:suggestion.end]
            cursor.insertText(self._replacement_preserving_edge_whitespace(original, suggestion.replacement))
        cursor.endEditBlock()
        self.set_spell_suggestions([])
        return len(non_overlapping)

    def contextMenuEvent(self, event) -> None:
        qt_position = self.cursorForPosition(event.pos()).position()
        position = qt_position_to_python_index(self.toPlainText(), qt_position)
        suggestion = next((item for item in self.spell_suggestions if item.start <= position < item.end and valid_suggestion(item, self.toPlainText(), self.revision)), None)
        menu = self.createStandardContextMenu()
        if suggestion is not None:
            menu.addSeparator()
            replace = menu.addAction(f'Replace "{suggestion.original_text}" with "{suggestion.replacement}"')
            ignore = menu.addAction("Ignore")
            chosen = menu.exec(event.globalPos())
            if chosen is replace:
                self.replace_spell_suggestion(suggestion)
            elif chosen is ignore:
                self.spell_suggestions.remove(suggestion)
                self.set_spell_suggestions(self.spell_suggestions)
            return
        menu.exec(event.globalPos())

    def replace_spell_suggestion(self, suggestion: Suggestion) -> bool:
        """Replace one still-current suggestion as a single undoable edit."""
        if suggestion not in self.spell_suggestions or not valid_suggestion(suggestion, self.toPlainText(), self.revision):
            return False
        cursor = QTextCursor(self.document())
        source = self.toPlainText()
        cursor.setPosition(python_index_to_qt_position(source, suggestion.start))
        cursor.setPosition(python_index_to_qt_position(source, suggestion.end), QTextCursor.MoveMode.KeepAnchor)
        cursor.beginEditBlock()
        original = source[suggestion.start:suggestion.end]
        cursor.insertText(self._replacement_preserving_edge_whitespace(original, suggestion.replacement))
        cursor.endEditBlock()
        self.set_spell_suggestions([])
        return True

    @staticmethod
    def _replacement_preserving_edge_whitespace(original: str, replacement: str) -> str:
        leading = original[: len(original) - len(original.lstrip())]
        trailing = original[len(original.rstrip()):]
        if replacement.startswith(leading):
            leading = ""
        if replacement.endswith(trailing):
            trailing = ""
        return f"{leading}{replacement}{trailing}"
