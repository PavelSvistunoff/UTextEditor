"""Compact find/replace controls for the active editor."""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QHBoxLayout,
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class FindReplaceWidget(QWidget):
    COUNT_BATCH_SIZE = 256

    def __init__(self, editor_provider, parent=None) -> None:
        super().__init__(parent)
        self.editor_provider = editor_provider
        self._count_timer = QTimer(self)
        self._count_timer.setSingleShot(True)
        self._count_timer.timeout.connect(self._count_batch)
        self._count_state = None
        self.find_edit = QLineEdit(self)
        self.find_edit.setPlaceholderText(self.tr("Find"))
        self.find_edit.setAccessibleName(self.tr("Find text"))
        self.replace_edit = QLineEdit(self)
        self.replace_edit.setPlaceholderText(self.tr("Replace with"))
        self.replace_edit.setAccessibleName(self.tr("Replace with"))
        self.previous_button = QPushButton(self.tr("Previous"), self)
        self.next_button = QPushButton(self.tr("Next"), self)
        self.replace_button = QPushButton(self.tr("Replace"), self)
        self.replace_all_button = QPushButton(self.tr("Replace All"), self)
        self.close_button = QPushButton(self.tr("Close"), self)
        self.case_sensitive = QCheckBox(self.tr("Match case"), self)
        self.case_sensitive.setChecked(True)
        self.whole_word = QCheckBox(self.tr("Whole words"), self)
        self.match_count = QLabel(self.tr("%n matches", None, 0), self)
        self.match_count.setAccessibleName(self.tr("Find match count"))
        self.message = QLabel(self)
        self.message.setAccessibleName(self.tr("Find and replace status"))
        self.message.setWordWrap(True)
        self.message.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.previous_button.clicked.connect(self.find_previous)
        self.next_button.clicked.connect(self.find_next)
        self.replace_button.clicked.connect(self.replace_one)
        self.replace_all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.close_find)
        self.case_sensitive.toggled.connect(self._update_match_count)
        self.whole_word.toggled.connect(self._update_match_count)
        self.find_edit.textChanged.connect(self._update_match_count)
        self.find_edit.returnPressed.connect(self.find_next)

        find_row = QHBoxLayout()
        for widget in (
            self.find_edit,
            self.previous_button,
            self.next_button,
            self.match_count,
            self.message,
            self.close_button,
        ):
            find_row.addWidget(widget)
        find_row.setStretchFactor(self.find_edit, 2)
        find_row.setStretchFactor(self.message, 1)

        replace_row = QHBoxLayout()
        replace_row.addWidget(self.replace_edit, 2)
        replace_row.addWidget(self.case_sensitive)
        replace_row.addWidget(self.whole_word)
        replace_row.addWidget(self.replace_button)
        replace_row.addWidget(self.replace_all_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addLayout(find_row)
        layout.addLayout(replace_row)

        for sequence, handler in (
            ("F3", self.find_next),
            ("Shift+F3", self.find_previous),
            ("Escape", self.close_find),
        ):
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(handler)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def hideEvent(self, event) -> None:
        self._count_timer.stop()
        self._count_state = None
        super().hideEvent(event)

    def find_next(self) -> bool:
        return self._find(backwards=False)

    def find_previous(self) -> bool:
        return self._find(backwards=True)

    def close_find(self) -> None:
        self.hide()
        editor = self.editor_provider()
        if editor is not None:
            editor.setFocus()

    def _flags(self, *, backwards: bool = False):
        flags = QTextDocument.FindFlag(0)
        if self.case_sensitive.isChecked():
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self.whole_word.isChecked():
            flags |= QTextDocument.FindFlag.FindWholeWords
        if backwards:
            flags |= QTextDocument.FindFlag.FindBackward
        return flags

    def _matches(self, editor, term: str) -> list[tuple[int, int]]:
        if not term:
            return []
        document = editor.document()
        position = 0
        matches = []
        while True:
            cursor = document.find(term, position, self._flags())
            if cursor.isNull():
                break
            start, end = cursor.selectionStart(), cursor.selectionEnd()
            if end <= position:
                break
            matches.append((start, end))
            position = end
        return matches

    def _find(self, *, backwards: bool) -> bool:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText(self.tr("Enter text to find."))
            return False

        cursor = editor.textCursor()
        original_cursor = QTextCursor(cursor)
        start = cursor.selectionStart() if backwards and cursor.hasSelection() else (
            cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        )
        cursor.setPosition(start)
        editor.setTextCursor(cursor)
        flags = self._flags(backwards=backwards)
        if editor.find(term, flags):
            self.message.clear()
            self._update_match_count()
            return True

        cursor = editor.textCursor()
        cursor.movePosition(
            QTextCursor.MoveOperation.End if backwards else QTextCursor.MoveOperation.Start
        )
        editor.setTextCursor(cursor)
        if editor.find(term, flags):
            self.message.setText(self.tr("Wrapped to the end.") if backwards else self.tr("Wrapped to the beginning."))
            self._update_match_count()
            return True
        editor.setTextCursor(original_cursor)
        self.message.setText(self.tr("No match found."))
        self._update_match_count()
        return False

    def replace_one(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText(self.tr("Enter text to find."))
            return

        cursor = editor.textCursor()
        current_match = editor.document().find(term, cursor.selectionStart(), self._flags())
        if not (cursor.hasSelection() and not current_match.isNull()
                and current_match.selectionStart() == cursor.selectionStart()
                and current_match.selectionEnd() == cursor.selectionEnd()):
            if not self._find(backwards=False):
                return
            cursor = editor.textCursor()
        cursor.insertText(self.replace_edit.text())
        self._update_match_count()
        if self.find_next():
            self.message.setText(self.tr("Replaced 1 match. Selected the next match."))
        else:
            self.message.setText(self.tr("Replaced 1 match. No further matches."))

    def replace_all(self) -> None:
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            self.message.setText(self.tr("Enter text to find."))
            return
        matches = self._matches(editor, term)
        count = len(matches)
        if count == 0:
            self.message.setText(self.tr("No match found."))
            self._update_match_count()
            return
        cursor = editor.textCursor()
        cursor.beginEditBlock()
        for start, end in reversed(matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            if cursor.selectedText() != self.replace_edit.text():
                cursor.insertText(self.replace_edit.text())
        cursor.endEditBlock()
        self.message.setText(self.tr("Replaced %n matches.", None, count))
        self._update_match_count()

    def _update_match_count(self, _text: str | bool | None = None) -> None:
        self.refresh()

    def refresh(self) -> None:
        self._count_timer.stop()
        self._count_state = None
        editor = self.editor_provider()
        term = self.find_edit.text()
        if editor is None or not term:
            count = 0
        elif self.case_sensitive.isChecked() and not self.whole_word.isChecked():
            count = editor.toPlainText().count(term)
        else:
            self._count_state = (editor, editor.revision, term, self._flags(), 0, 0)
            self._count_batch()
            return
        self.match_count.setText(self.tr("%n matches", None, count))

    def _count_batch(self) -> None:
        if self._count_state is None:
            return
        editor, revision, term, flags, position, count = self._count_state
        if editor is not self.editor_provider() or editor.revision != revision:
            self._count_state = None
            return
        document = editor.document()
        for _ in range(self.COUNT_BATCH_SIZE):
            cursor = document.find(term, position, flags)
            if cursor.isNull() or cursor.selectionEnd() <= position:
                self._count_state = None
                self.match_count.setText(self.tr("%n matches", None, count))
                return
            position = cursor.selectionEnd()
            count += 1
        self._count_state = (editor, revision, term, flags, position, count)
        self.match_count.setText(self.tr("Counting matches…"))
        self._count_timer.start(0)
