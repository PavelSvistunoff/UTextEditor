"""QPlainTextEdit with non-destructive inline completions."""

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QTextEdit

from app.ai.models import Suggestion
from app.ai.validation import valid_suggestion


class EditorWidget(QPlainTextEdit):
    completion_accepted = Signal(str)
    completion_rejected = Signal()
    content_changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._ghost_text = ""
        self._ghost_position = -1
        self._ghost_revision = -1
        self._revision = 0
        self.spell_suggestions: list[Suggestion] = []
        self.textChanged.connect(self._on_text_changed)
        self.cursorPositionChanged.connect(self._invalidate_completion)
        self.selectionChanged.connect(self._invalidate_completion)

    @property
    def revision(self) -> int:
        return self._revision

    def _on_text_changed(self) -> None:
        self._revision += 1
        self.clear_completion()
        self.content_changed.emit()

    def _invalidate_completion(self) -> None:
        if self.has_completion and self.textCursor().position() != self._ghost_position:
            self.clear_completion()

    @property
    def has_completion(self) -> bool:
        return bool(self._ghost_text) and self._ghost_revision == self._revision and self.textCursor().position() == self._ghost_position

    def show_completion(self, text: str, revision: int, position: int) -> None:
        if not text or revision != self._revision or position != self.textCursor().position():
            return
        self._ghost_text = text
        self._ghost_position = position
        self._ghost_revision = revision
        self.viewport().update()

    def clear_completion(self) -> None:
        if self._ghost_text:
            self._ghost_text = ""
            self._ghost_position = -1
            self._ghost_revision = -1
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
        previous = document_text[cursor.position() - 1]
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
        remaining = self._ghost_text
        line_height = metrics.height()
        while remaining:
            width = min(available, max(metrics.horizontalAdvance(remaining[:1]), available))
            # Keep the MVP renderer predictable; wrapped ghost text is clipped rather than inserted.
            painter.drawText(QRect(x, y, available, line_height), Qt.AlignmentFlag.AlignLeft, remaining)
            break
        painter.end()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Tab and self.accept_completion():
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.has_completion:
            self.clear_completion()
            self.completion_rejected.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def set_spell_suggestions(self, suggestions: list[Suggestion]) -> None:
        self.spell_suggestions = suggestions
        selections = []
        for suggestion in suggestions:
            cursor = self.textCursor()
            cursor.setPosition(suggestion.start)
            cursor.setPosition(suggestion.end, QTextCursor.MoveMode.KeepAnchor)
            fmt = QTextCharFormat()
            fmt.setUnderlineColor(QColor("#d55e5e"))
            fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = fmt
            selections.append(selection)
        self.setExtraSelections(selections)

    def apply_spell_suggestions(self, suggestions: list[Suggestion]) -> int:
        """Apply non-overlapping, current-revision corrections as one undo step."""
        source = self.toPlainText()
        valid = [item for item in suggestions if valid_suggestion(item, source, self.revision)]
        non_overlapping: list[tuple[int, int, Suggestion]] = []
        earliest_applied_end = len(source) + 1
        for suggestion in sorted(valid, key=lambda item: item.start, reverse=True):
            start, end = suggestion.start, suggestion.end
            while start < end and not source[start].isalnum():
                start += 1
            while end > start and not source[end - 1].isalnum():
                end -= 1
            if start > 0 and start < end and source[start].isalnum() and source[start - 1].isalnum():
                while start > 0 and source[start - 1].isalnum():
                    start -= 1
            if end < len(source) and start < end and source[end - 1].isalnum() and source[end].isalnum():
                while end < len(source) and source[end].isalnum():
                    end += 1
            if end <= earliest_applied_end and start < end:
                non_overlapping.append((start, end, suggestion))
                earliest_applied_end = start
        if not non_overlapping:
            return 0

        cursor = self.textCursor()
        cursor.beginEditBlock()
        for start, end, suggestion in non_overlapping:
            selected = source[start:end]
            replacement = suggestion.replacement
            if selected:
                leading = selected[: len(selected) - len(selected.lstrip())]
                trailing = selected[len(selected.rstrip()) :]
                if leading or trailing:
                    replacement = f"{leading}{suggestion.replacement}{trailing}"
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(replacement)
        cursor.endEditBlock()
        self.set_spell_suggestions([])
        return len(non_overlapping)

    def contextMenuEvent(self, event) -> None:
        position = self.cursorForPosition(event.pos()).position()
        suggestion = next((item for item in self.spell_suggestions if item.start <= position <= item.end), None)
        menu = self.createStandardContextMenu()
        if suggestion is not None:
            menu.addSeparator()
            replace = menu.addAction(f'Replace "{suggestion.original_text}" with "{suggestion.replacement}"')
            ignore = menu.addAction("Ignore")
            chosen = menu.exec(event.globalPos())
            if chosen is replace:
                cursor = self.textCursor()
                cursor.setPosition(suggestion.start)
                cursor.setPosition(suggestion.end, QTextCursor.MoveMode.KeepAnchor)
                cursor.beginEditBlock()
                cursor.insertText(suggestion.replacement)
                cursor.endEditBlock()
                self.spell_suggestions.remove(suggestion)
                self.set_spell_suggestions(self.spell_suggestions)
            elif chosen is ignore:
                self.spell_suggestions.remove(suggestion)
                self.set_spell_suggestions(self.spell_suggestions)
            return
        menu.exec(event.globalPos())
