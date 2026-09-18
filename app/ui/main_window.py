"""Main Qt window and application orchestration."""

from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStatusBar

from app.ai.completion_service import CompletionService, build_context
from app.ai.ollama_client import OllamaClient
from app.ai.spellcheck_service import SpellcheckService
from app.document.file_manager import FileManager
from app.settings.settings import AppSettings
from .find_replace import FindReplaceWidget
from .ai_debug_window import AIDebugWindow
from .settings_dialog import SettingsDialog
from .tab_widget import DocumentTabWidget
from .workers import FunctionWorker


class MainWindow(QMainWindow):
    ai_interaction = Signal(str, str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UTextEditor")
        self.resize(1000, 700)
        self.settings = AppSettings()
        self.file_manager = FileManager()
        self.tabs = DocumentTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.thread_pool = QThreadPool.globalInstance()
        self._debug_events: list[tuple[str, str, dict]] = []
        self._debug_window: AIDebugWindow | None = None
        self.ai_interaction.connect(self._record_ai_interaction, Qt.ConnectionType.QueuedConnection)
        self.provider = OllamaClient(
            self.settings.ollama_host,
            self.settings.ollama_model,
            interaction_observer=self._emit_ai_interaction,
        )
        self.completion_service = CompletionService(self.provider)
        self.spellcheck_service = SpellcheckService(self.provider)
        self._completion_generation = 0
        self._completion_worker = None
        self._completion_timer = QTimer(self)
        self._completion_timer.setSingleShot(True)
        self._completion_timer.timeout.connect(self.request_completion)
        self._build_actions()
        self._build_status_bar()
        self.tabs.editor_created.connect(self._wire_editor)
        self.tabs.document_changed.connect(self._update_status)
        self.tabs.close_requested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_active_document_changed)
        self.tabs.new_document()
        self._check_connection()

    def _build_actions(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        edit_menu = self.menuBar().addMenu("Edit")
        search_menu = self.menuBar().addMenu("Search")
        ai_menu = self.menuBar().addMenu("AI")
        actions = [
            (file_menu, "New", self.new_document, QKeySequence.StandardKey.New),
            (file_menu, "Open", self.open_document, QKeySequence.StandardKey.Open),
            (file_menu, "Save", self.save_document, QKeySequence.StandardKey.Save),
            (file_menu, "Save As", self.save_as, QKeySequence("Ctrl+Shift+S")),
            (edit_menu, "Undo", lambda: self._edit("undo"), QKeySequence.StandardKey.Undo),
            (edit_menu, "Redo", lambda: self._edit("redo"), QKeySequence.StandardKey.Redo),
            (edit_menu, "Copy", lambda: self._edit("copy"), QKeySequence.StandardKey.Copy),
            (edit_menu, "Cut", lambda: self._edit("cut"), QKeySequence.StandardKey.Cut),
            (edit_menu, "Paste", lambda: self._edit("paste"), QKeySequence.StandardKey.Paste),
            (edit_menu, "Select All", lambda: self._edit("selectAll"), QKeySequence.StandardKey.SelectAll),
            (search_menu, "Find / Replace", self.show_find_replace, QKeySequence("Ctrl+H")),
            (ai_menu, "Generate Completion", self.request_completion, QKeySequence("Ctrl+Space")),
            (ai_menu, "Check Spelling", self.check_spelling, QKeySequence("F7")),
            (ai_menu, "Accept Suggestion", self.accept_completion, QKeySequence()),
            (ai_menu, "Reject Suggestion", self.reject_completion, QKeySequence()),
            (ai_menu, "Ollama Debug", self.show_ai_debug, QKeySequence()),
            (ai_menu, "AI Settings…", self.show_settings, QKeySequence()),
        ]
        for menu, title, handler, shortcut in actions:
            action = QAction(title, self)
            if menu is ai_menu:
                # macOS otherwise promotes actions named "Settings" to the
                # application menu, hiding them from the AI menu.
                action.setMenuRole(QAction.MenuRole.NoRole)
            action.setShortcut(shortcut)
            action.triggered.connect(handler)
            menu.addAction(action)

    def _build_status_bar(self) -> None:
        self.status = QStatusBar(self)
        self.setStatusBar(self.status)
        self.ai_status = "AI: Connecting..."
        self._update_status()

    def _update_status(self) -> None:
        editor = self.tabs.current_editor()
        if editor is None:
            return
        document = editor.document_state
        cursor = editor.textCursor()
        self.status.showMessage(
            f"{document.encoding.upper()}    {document.line_ending}    "
            f"Ln {cursor.blockNumber() + 1}, Col {cursor.columnNumber() + 1}    {self.ai_status}"
        )

    def _wire_editor(self, editor) -> None:
        editor.content_changed.connect(self.schedule_completion)

    def _edit(self, method: str) -> None:
        editor = self.tabs.current_editor()
        if editor:
            getattr(editor, method)()

    def new_document(self) -> None:
        self.tabs.new_document()

    def open_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open file")
        if path:
            try:
                self.tabs.add_document(self.file_manager.open(path))
            except (OSError, UnicodeError, ValueError) as exc:
                QMessageBox.warning(self, "Open failed", str(exc))

    def save_document(self) -> None:
        editor = self.tabs.current_editor()
        if not editor:
            return
        document = editor.document_state
        try:
            document.update_text(editor.toPlainText())
            if document.path is None:
                self.save_as()
            else:
                self.file_manager.save(document)
                self.tabs._update_tab_title()
        except (OSError, UnicodeError, ValueError) as exc:
            QMessageBox.warning(self, "Save failed", str(exc))

    def save_as(self) -> None:
        editor = self.tabs.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save file")
        if path:
            try:
                editor.document_state.update_text(editor.toPlainText())
                self.file_manager.save(editor.document_state, path)
                self.tabs._update_tab_title()
            except (OSError, UnicodeError, ValueError) as exc:
                QMessageBox.warning(self, "Save failed", str(exc))

    def close_tab(self, index: int) -> None:
        editor = self.tabs.widget(index)
        if editor is None:
            return
        document = editor.document_state
        if document.dirty:
            self.tabs.setCurrentIndex(index)
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                f"Save changes to {document.display_name}?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save:
                self.save_document()
                if document.dirty:
                    return
        self.tabs.remove_tab(index)

    def show_find_replace(self) -> None:
        bar = FindReplaceWidget(self.tabs.current_editor, self)
        self.statusBar().addPermanentWidget(bar)
        bar.find_edit.setFocus()

    def accept_completion(self) -> None:
        editor = self.tabs.current_editor()
        if editor:
            editor.accept_completion()

    def reject_completion(self) -> None:
        editor = self.tabs.current_editor()
        if editor:
            editor.clear_completion()

    def show_settings(self) -> None:
        if SettingsDialog(self.settings, self).exec():
            self.provider.host = self.settings.ollama_host.rstrip("/")
            self.provider.model = self.settings.ollama_model
            self._check_connection()

    def show_ai_debug(self) -> None:
        if self._debug_window is None:
            self._debug_window = AIDebugWindow(self)
            self._debug_window.cleared.connect(self._debug_events.clear)
            for event, path, details in self._debug_events:
                self._debug_window.append_interaction(event, path, details)
        self._debug_window.show()
        self._debug_window.raise_()
        self._debug_window.activateWindow()

    def _emit_ai_interaction(self, event: str, path: str, details: dict) -> None:
        """Safely forward worker-thread diagnostics to the GUI thread."""
        self.ai_interaction.emit(event, path, details)

    def _record_ai_interaction(self, event: str, path: str, details: dict) -> None:
        self._debug_events.append((event, path, details))
        if len(self._debug_events) > 100:
            self._debug_events.pop(0)
        if self._debug_window is not None:
            self._debug_window.append_interaction(event, path, details)

    def _check_connection(self) -> None:
        worker = FunctionWorker(self.provider.check_connection)
        worker.signals.finished.connect(lambda ok: self._set_ai_status(ok), Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda _: self._set_ai_status(False), Qt.ConnectionType.QueuedConnection)
        self.thread_pool.start(worker)

    def _set_ai_status(self, connected: bool) -> None:
        self.ai_status = "AI: Connected" if connected else "AI: Offline"
        self._update_status()

    def request_completion(self) -> None:
        editor = self.tabs.current_editor()
        if not editor or not self.settings.ai_enabled or not self.settings.completion_enabled:
            return
        self._completion_timer.stop()
        self._completion_generation += 1
        generation = self._completion_generation
        if self._completion_worker:
            self._completion_worker.cancel()
        cursor = editor.textCursor()
        revision, position = editor.revision, cursor.position()
        context = build_context(editor.toPlainText(), position, maximum_characters=self.settings.context_size)
        self.ai_status = "AI: Generating..."
        self._update_status()
        worker = FunctionWorker(
            self.completion_service.complete,
            context,
            self.settings.language,
            role=self.settings.ai_role,
            template=self.settings.completion_template,
            maximum_tokens=self.settings.maximum_suggestion_length,
            temperature=self.settings.temperature,
        )
        self._completion_worker = worker
        worker.signals.finished.connect(lambda text: self._completion_finished(generation, editor, revision, position, text), Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda exc: self._completion_failed(exc), Qt.ConnectionType.QueuedConnection)
        self.thread_pool.start(worker)

    def schedule_completion(self) -> None:
        self._completion_timer.start(self.settings.completion_debounce_ms)

    def _on_active_document_changed(self, _: int) -> None:
        self._completion_generation += 1
        self._completion_timer.stop()
        if self._completion_worker:
            self._completion_worker.cancel()
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if editor:
                editor.clear_completion()

    def _apply_completion(self, generation, editor, revision, position, text) -> None:
        if generation == self._completion_generation and editor is self.tabs.current_editor() and editor.revision == revision and editor.textCursor().position() == position:
            editor.show_completion(text, revision, position)
            self.ai_status = "AI: Connected"
            self._update_status()

    def _completion_finished(self, generation, editor, revision, position, text) -> None:
        if not isinstance(text, str):
            self._completion_failed("Ollama returned an invalid completion")
            return
        if not text.strip():
            # Models may legitimately decide there is nothing useful to add.
            # Treat that as a completed request, not a connection failure.
            if generation == self._completion_generation:
                self.ai_status = "AI: Connected"
                self._update_status()
            return
        self._apply_completion(generation, editor, revision, position, text)

    def _completion_failed(self, error) -> None:
        self.ai_status = "AI: Error"
        self.status.showMessage(f"AI completion failed: {error}")

    def check_spelling(self) -> None:
        editor = self.tabs.current_editor()
        if not editor or not self.settings.ai_enabled or not self.settings.spellcheck_enabled:
            return
        text, revision = editor.toPlainText(), editor.revision
        worker = FunctionWorker(self.spellcheck_service.check, text, self.settings.language, revision)
        worker.signals.finished.connect(
            lambda suggestions: self._apply_spellcheck_results(editor, revision, suggestions),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.signals.failed.connect(lambda exc: self.status.showMessage(f"Spellcheck failed: {exc}"), Qt.ConnectionType.QueuedConnection)
        self.thread_pool.start(worker)

    def _apply_spellcheck_results(self, editor, revision: int, suggestions) -> None:
        if editor is not self.tabs.current_editor() or editor.revision != revision:
            return
        count = editor.apply_spell_suggestions(suggestions)
        self.status.showMessage(f"Applied {count} spelling correction{'s' if count != 1 else ''}.")

    def closeEvent(self, event) -> None:
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if not editor or not editor.document_state.dirty:
                continue
            self.tabs.setCurrentIndex(index)
            answer = QMessageBox.question(self, "Unsaved changes", f"Save changes to {editor.document_state.display_name}?", QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
            if answer == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            if answer == QMessageBox.StandardButton.Save:
                self.save_document()
                if editor.document_state.dirty:
                    event.ignore()
                    return
        event.accept()
