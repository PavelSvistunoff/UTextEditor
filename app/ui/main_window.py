"""Main Qt window and application orchestration."""

from pathlib import Path

from PySide6.QtCore import QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QTextCursor
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMainWindow, QMessageBox, QStatusBar

from app.ai.completion_service import CompletionService, build_context
from app.ai.ollama_client import OllamaClient
from app.ai.spellcheck_service import SpellcheckService
from app.document.file_manager import FileManager
from app.document.document import Document
from app.document.encoding import qt_position_to_python_index
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
        # Load persisted settings if available; fall back to defaults.
        self.settings = AppSettings.load()
        self.file_manager = FileManager()
        self.tabs = DocumentTabWidget(self)
        self.setCentralWidget(self.tabs)
        self.thread_pool = QThreadPool.globalInstance()
        self._workers: list[FunctionWorker] = []
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
        self._generate_generation = 0
        self._settings_generation = 0
        self._active_document_generation = 0
        self._find_bar = None
        self._connected = False
        self._spellcheck_generation = 0
        self._spellcheck_worker = None
        self._generate_worker = None
        self._saving_editors = set()
        self._quit_in_progress = False
        self._closing_confirmed = False
        self._quit_discards = {}
        self._completion_worker = None
        self._completion_timer = QTimer(self)
        self._completion_timer.setSingleShot(True)
        self._completion_timer.timeout.connect(self.request_completion)
        # Spellcheck timer for automatic spell checking on pause
        self._spellcheck_timer = QTimer(self)
        self._spellcheck_timer.setSingleShot(True)
        self._spellcheck_timer.timeout.connect(self.check_spelling)
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

        # Enable AI (checkable) — allows quick disabling of all AI features.
        enable_ai_action = QAction("Enable AI", self)
        enable_ai_action.setCheckable(True)
        enable_ai_action.setChecked(self.settings.ai_enabled)
        enable_ai_action.setMenuRole(QAction.MenuRole.NoRole)
        enable_ai_action.toggled.connect(self._toggle_ai)
        ai_menu.addAction(enable_ai_action)

        actions = [
            (file_menu, "New", self.new_document, QKeySequence.StandardKey.New),
            (file_menu, "Open", self.open_document, QKeySequence.StandardKey.Open),
            (file_menu, "Save", self.save_document, QKeySequence.StandardKey.Save),
            (file_menu, "Save As", self.save_as, QKeySequence.StandardKey.SaveAs),
            (file_menu, "Close Tab", lambda: self.close_tab(self.tabs.currentIndex()), QKeySequence.StandardKey.Close),
            (file_menu, "Quit", self.close, QKeySequence.StandardKey.Quit),
            (edit_menu, "Undo", lambda: self._edit("undo"), QKeySequence.StandardKey.Undo),
            (edit_menu, "Redo", lambda: self._edit("redo"), QKeySequence.StandardKey.Redo),
            (edit_menu, "Copy", lambda: self._edit("copy"), QKeySequence.StandardKey.Copy),
            (edit_menu, "Cut", lambda: self._edit("cut"), QKeySequence.StandardKey.Cut),
            (edit_menu, "Paste", lambda: self._edit("paste"), QKeySequence.StandardKey.Paste),
            (edit_menu, "Select All", lambda: self._edit("selectAll"), QKeySequence.StandardKey.SelectAll),
            (search_menu, "Find", self.show_find_replace, QKeySequence.StandardKey.Find),
            (search_menu, "Replace", self.show_find_replace, QKeySequence.StandardKey.Replace),
            (ai_menu, "Generate..", self.generate_from_prompt, QKeySequence()),
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
        # Reflect whether AI is enabled in the initial status message.
        self.ai_status = "AI: Disabled" if not self.settings.ai_enabled else "AI: Connecting..."
        self._update_status()

    def _toggle_ai(self, enabled: bool) -> None:
        """Enable or disable AI features at runtime.

        Disabling cancels in-flight work and clears visible suggestions so the
        editor behaves like a plain text editor until AI is re-enabled.
        """
        self.settings.ai_enabled = bool(enabled)
        self._settings_generation += 1
        if not self.settings.ai_enabled:
            self._cancel_pending_ai_requests()
            self._clear_editor_ai_state()
            self.ai_status = "AI: Disabled"
            self._update_status()
        else:
            self.ai_status = "AI: Connecting..."
            self._update_status()
            self._check_connection()
        try:
            self.settings.save()
        except OSError as exc:
            self.statusBar().showMessage(f"Could not save AI preference: {exc}")

    def _cancel_pending_ai_requests(self) -> None:
        self._completion_timer.stop()
        self._spellcheck_timer.stop()
        self._completion_generation += 1
        self._spellcheck_generation += 1
        if self._completion_worker:
            self._completion_worker.cancel()
        for worker in (self._spellcheck_worker, self._generate_worker):
            if worker is not None:
                worker.cancel()

    def _clear_editor_ai_state(self) -> None:
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if editor:
                editor.clear_completion()
                editor.set_spell_suggestions([])

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
        editor.apply_settings(self.settings)
        editor.content_changed.connect(self.schedule_completion)
        editor.cursorPositionChanged.connect(lambda: self._editor_cursor_changed(editor))
        editor.selectionChanged.connect(lambda: self._editor_cursor_changed(editor))
        editor.cursorPositionChanged.connect(self._update_status)
        # Automatic spellcheck scheduling when enabled
        editor.content_changed.connect(lambda: self.schedule_spellcheck(editor))

    def _editor_cursor_changed(self, editor) -> None:
        if editor is not self.tabs.current_editor():
            return
        if self._completion_timer.isActive() or self._completion_worker is not None:
            self._completion_timer.stop()
            self._completion_generation += 1
            if self._completion_worker is not None:
                self._completion_worker.cancel()
            if self.ai_status == "AI: Generating...":
                self.ai_status = "AI: Connected" if self._connected else "AI: Offline"

    def _edit(self, method: str) -> None:
        editor = self.tabs.current_editor()
        if editor:
            getattr(editor, method)()

    def new_document(self) -> None:
        self.tabs.new_document()

    def open_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open file")
        if not path:
            return
        resolved = Path(path).resolve()
        for index in range(self.tabs.count()):
            existing = self.tabs.widget(index)
            if existing and existing.document_state.path and existing.document_state.path.resolve() == resolved:
                self.tabs.setCurrentIndex(index)
                return
        worker = FunctionWorker(self.file_manager.open, path)
        self._track_worker(worker)
        worker.signals.finished.connect(self._opened_document, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda exc: QMessageBox.warning(self, "Open failed", str(exc)), Qt.ConnectionType.QueuedConnection)
        self.statusBar().showMessage("Opening file…")
        self.thread_pool.start(worker)

    def _opened_document(self, document) -> None:
        if self._closing_confirmed:
            return
        if document.path is not None:
            resolved = document.path.resolve()
            for index in range(self.tabs.count()):
                existing = self.tabs.widget(index)
                if existing and existing.document_state.path and existing.document_state.path.resolve() == resolved:
                    self.tabs.setCurrentIndex(index)
                    return
        self.tabs.add_document(document)

    def save_document(self) -> None:
        editor = self.tabs.current_editor()
        if not editor:
            return
        self._save_editor(editor)

    def _save_editor(self, editor, callback=None, target: Path | None = None) -> bool:
        if editor in self._saving_editors:
            return False
        document = editor.document_state
        if target is None:
            target = document.path
        if target is None:
            if editor is not self.tabs.current_editor():
                self.tabs.setCurrentWidget(editor)
            path, _ = QFileDialog.getSaveFileName(self, "Save file")
            if not path:
                if callback:
                    callback(False)
                return False
            target = Path(path)
        target = Path(target)
        resolved = target.resolve()
        for index in range(self.tabs.count()):
            other = self.tabs.widget(index)
            if other is not editor and other and other.document_state.path and other.document_state.path.resolve() == resolved:
                QMessageBox.warning(self, "Save failed", "That file is already open in another tab.")
                if callback:
                    callback(False)
                return False
        text = editor.toPlainText()
        snapshot = Document.from_text(text, target)
        snapshot.encoding = document.encoding
        snapshot.line_ending = document.line_ending
        worker = FunctionWorker(self.file_manager.save, snapshot, target)
        self._saving_editors.add(editor)
        self._track_worker(worker)
        worker.signals.finished.connect(
            lambda saved_path: self._saved_editor(editor, target, text, callback),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.signals.failed.connect(
            lambda error: self._save_failed(editor, error, callback),
            Qt.ConnectionType.QueuedConnection,
        )
        if editor is self.tabs.current_editor():
            self.statusBar().showMessage("Saving file…")
        self.thread_pool.start(worker)
        return True

    def _saved_editor(self, editor, target: Path, saved_text: str, callback=None) -> None:
        self._saving_editors.discard(editor)
        document = editor.document_state
        document.path = target
        document.mark_saved(saved_text)
        document.update_text(editor.toPlainText())
        self.tabs._update_tab_title(editor)
        if callback:
            callback(True)

    def _save_failed(self, editor, error, callback=None) -> None:
        self._saving_editors.discard(editor)
        if self.tabs.indexOf(editor) >= 0:
            QMessageBox.warning(self, "Save failed", str(error))
        if callback:
            callback(False)

    def save_as(self) -> None:
        editor = self.tabs.current_editor()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save file")
        if path:
            self._save_editor(editor, target=Path(path))

    def close_tab(self, index: int) -> None:
        editor = self.tabs.widget(index)
        if editor is None or editor in self._saving_editors:
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
                self._save_editor(editor, callback=lambda saved: self._close_tab_after_save(editor, saved))
                return
        self.tabs.remove_tab(index)

    def _close_tab_after_save(self, editor, saved: bool) -> None:
        if saved and not editor.document_state.dirty:
            index = self.tabs.indexOf(editor)
            if index >= 0:
                self.tabs.remove_tab(index)

    def show_find_replace(self) -> None:
        if self._find_bar is None:
            self._find_bar = FindReplaceWidget(lambda: self.tabs.current_editor(), self)
            self.statusBar().addPermanentWidget(self._find_bar)
        self._find_bar.show()
        self._find_bar.find_edit.setFocus()

    def accept_completion(self) -> None:
        editor = self.tabs.current_editor()
        if editor:
            editor.accept_completion()

    def reject_completion(self) -> None:
        editor = self.tabs.current_editor()
        if editor:
            editor.clear_completion()

    def generate_from_prompt(self) -> None:
        editor = self.tabs.current_editor()
        if not editor or not self.settings.ai_enabled:
            return
        prompt, accepted = QInputDialog.getMultiLineText(
            self,
            "Generate..",
            "Describe what you want the AI to write:",
            "",
        )
        if not accepted or not prompt.strip():
            return
        self._generate_generation += 1
        generation = self._generate_generation
        revision = editor.revision
        cursor = editor.textCursor()
        position = cursor.position()
        selection = (cursor.selectionStart(), cursor.selectionEnd()) if cursor.hasSelection() else (position, position)
        settings_generation = self._settings_generation
        self.ai_status = "AI: Generating..."
        self._update_status()
        worker = FunctionWorker(
            self.provider.generate,
            prompt.strip(),
            role=self.settings.ai_role,
            maximum_tokens=self.settings.maximum_suggestion_length,
            temperature=self.settings.temperature,
        )
        self._track_worker(worker)
        self._generate_worker = worker
        worker.signals.done.connect(lambda worker=worker: self._clear_worker_reference("_generate_worker", worker), Qt.ConnectionType.QueuedConnection)
        worker.signals.finished.connect(
            lambda result: self._apply_generated_text(generation, editor, result, revision, position, selection, settings_generation),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.signals.failed.connect(
            lambda exc: self._generation_failed(exc, generation, settings_generation),
            Qt.ConnectionType.QueuedConnection,
        )
        self.thread_pool.start(worker)

    def _apply_generated_text(self, generation: int, editor, text: str, revision=None, position=None, selection=None, settings_generation=None) -> None:
        if generation != self._generate_generation:
            return
        if editor is not self.tabs.current_editor():
            return
        cursor = editor.textCursor()
        current_selection = (cursor.selectionStart(), cursor.selectionEnd()) if cursor.hasSelection() else (cursor.position(), cursor.position())
        if revision is not None and (editor.revision != revision or cursor.position() != position or current_selection != selection):
            self.ai_status = "AI: Disabled" if not self.settings.ai_enabled else ("AI: Connected" if self._connected else "AI: Offline")
            self._update_status()
            return
        if settings_generation is not None and settings_generation != self._settings_generation:
            self.ai_status = "AI: Disabled" if not self.settings.ai_enabled else ("AI: Connected" if self._connected else "AI: Offline")
            self._update_status()
            return
        if not isinstance(text, str):
            self._generation_failed("Ollama returned an invalid response", generation, settings_generation)
            return
        self._connected = True
        if not text.strip():
            self.ai_status = "AI: Connected"
            self._update_status()
            return
        result = text
        if revision is not None:
            cursor.setPosition(selection[0])
            if selection[0] != selection[1]:
                cursor.setPosition(selection[1], QTextCursor.MoveMode.KeepAnchor)
        cursor.beginEditBlock()
        if cursor.hasSelection():
            cursor.removeSelectedText()
        cursor.insertText(result)
        cursor.endEditBlock()
        self._connected = True
        self.ai_status = "AI: Connected"
        self._update_status()

    def _generation_failed(self, error, generation=None, settings_generation=None) -> None:
        if generation is not None and generation != self._generate_generation:
            return
        if settings_generation is not None and settings_generation != self._settings_generation:
            return
        self.ai_status = "AI: Error"
        self.status.showMessage(f"AI generation failed: {error}")

    def show_settings(self) -> None:
        if SettingsDialog(self.settings, self).exec():
            self._settings_generation += 1
            self._completion_generation += 1
            self._completion_timer.stop()
            self._cancel_active_ai_workers()
            self._clear_editor_ai_state()
            try:
                self.settings.save()
            except OSError as exc:
                QMessageBox.warning(self, "Settings could not be saved", str(exc))
            self.provider.host = self.settings.ollama_host.rstrip("/")
            self.provider.model = self.settings.ollama_model
            self._apply_editor_settings()
            self.ai_status = "AI: Connecting..." if self.settings.ai_enabled else "AI: Disabled"
            self._update_status()
            self._check_connection()

    def _cancel_active_ai_workers(self) -> None:
        for worker in (self._completion_worker, self._spellcheck_worker, self._generate_worker):
            if worker is not None:
                worker.cancel()

    def _apply_editor_settings(self) -> None:
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if editor is not None:
                editor.apply_settings(self.settings)

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

    def _track_worker(self, worker: FunctionWorker) -> None:
        self._workers.append(worker)
        worker.signals.done.connect(lambda worker=worker: self._drop_worker(worker), Qt.ConnectionType.QueuedConnection)

    def _drop_worker(self, worker: FunctionWorker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    def _clear_worker_reference(self, attribute: str, worker: FunctionWorker) -> None:
        if getattr(self, attribute, None) is worker:
            setattr(self, attribute, None)

    def _check_connection(self) -> None:
        generation = self._settings_generation
        worker = FunctionWorker(self.provider.check_connection)
        self._track_worker(worker)
        worker.signals.finished.connect(lambda ok: self._set_ai_status(ok, generation), Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda _: self._set_ai_status(False, generation), Qt.ConnectionType.QueuedConnection)
        self.thread_pool.start(worker)

    def _set_ai_status(self, connected: bool, generation: int | None = None) -> None:
        if generation is not None and generation != self._settings_generation:
            return
        if not self.settings.ai_enabled:
            self.ai_status = "AI: Disabled"
            self._update_status()
            return
        self._connected = connected
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
        if cursor.hasSelection():
            editor.clear_completion()
            return
        revision, position = editor.revision, cursor.position()
        context = build_context(editor.toPlainText(), qt_position_to_python_index(editor.toPlainText(), position), maximum_characters=self.settings.context_size)
        if not context.strip():
            return
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
        self._track_worker(worker)
        worker.signals.done.connect(lambda worker=worker: self._clear_worker_reference("_completion_worker", worker), Qt.ConnectionType.QueuedConnection)
        selection = (cursor.selectionStart(), cursor.selectionEnd()) if cursor.hasSelection() else (position, position)
        settings_generation = self._settings_generation
        worker.signals.finished.connect(lambda text: self._completion_finished(generation, editor, revision, position, text, selection, settings_generation), Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(lambda exc: self._completion_failed(exc, generation, settings_generation), Qt.ConnectionType.QueuedConnection)
        self.thread_pool.start(worker)

    def schedule_completion(self) -> None:
        if self.settings.ai_enabled and self.settings.completion_enabled:
            self._completion_generation += 1
            if self._completion_worker:
                self._completion_worker.cancel()
            if self.ai_status == "AI: Generating...":
                self.ai_status = "AI: Connected" if self._connected else "AI: Offline"
            self._completion_timer.start(self.settings.completion_debounce_ms)

    def schedule_spellcheck(self, editor) -> None:
        """Schedule an automatic spellcheck after a short pause when enabled."""
        if not self.settings.ai_enabled or not self.settings.spellcheck_enabled or not self.settings.automatic_spellcheck:
            return
        # Use a slightly longer debounce for spellchecking to avoid excessive requests.
        delay = max(500, int(self.settings.completion_debounce_ms * 2))
        # Only schedule for the active editor to avoid unnecessary background checks.
        if editor is not self.tabs.current_editor():
            return
        self._spellcheck_timer.start(delay)

    def _on_active_document_changed(self, _: int) -> None:
        self._active_document_generation += 1
        self._generate_generation += 1
        self._completion_generation += 1
        self._completion_timer.stop()
        self._spellcheck_timer.stop()
        self._spellcheck_generation += 1
        if self.ai_status == "AI: Generating...":
            self.ai_status = "AI: Connected" if self._connected else "AI: Offline"
        if self._completion_worker:
            self._completion_worker.cancel()
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if editor:
                editor.clear_completion()

    def _apply_completion(self, generation, editor, revision, position, text, selection=None, settings_generation=None) -> None:
        cursor = editor.textCursor()
        current_selection = (cursor.selectionStart(), cursor.selectionEnd()) if cursor.hasSelection() else (cursor.position(), cursor.position())
        if (generation == self._completion_generation and editor is self.tabs.current_editor()
                and editor.revision == revision and cursor.position() == position
                and (selection is None or current_selection == selection)
                and (settings_generation is None or settings_generation == self._settings_generation)):
            editor.show_completion(text, revision, position)
            self.ai_status = "AI: Connected"
            self._update_status()

    def _completion_finished(self, generation, editor, revision, position, text, selection=None, settings_generation=None) -> None:
        if generation != self._completion_generation or (settings_generation is not None and settings_generation != self._settings_generation):
            return
        if not isinstance(text, str):
            self._completion_failed("Ollama returned an invalid completion", generation, settings_generation)
            return
        self._connected = True
        if not text.strip():
            # Models may legitimately decide there is nothing useful to add.
            # Treat that as a completed request, not a connection failure.
            self.ai_status = "AI: Connected"
            self._update_status()
            return
        self._apply_completion(generation, editor, revision, position, text, selection, settings_generation)

    def _completion_failed(self, error, generation=None, settings_generation=None) -> None:
        if generation is not None and generation != self._completion_generation:
            return
        if settings_generation is not None and settings_generation != self._settings_generation:
            return
        self.ai_status = "AI: Error"
        self.status.showMessage(f"AI completion failed: {error}")

    def check_spelling(self) -> None:
        editor = self.tabs.current_editor()
        if not editor or not self.settings.ai_enabled or not self.settings.spellcheck_enabled:
            return
        text, revision = editor.toPlainText(), editor.revision
        settings_generation = self._settings_generation
        active_generation = self._active_document_generation
        self._spellcheck_generation += 1
        spellcheck_generation = self._spellcheck_generation
        if self._spellcheck_worker is not None:
            self._spellcheck_worker.cancel()
        worker = FunctionWorker(self.spellcheck_service.check, text, self.settings.language, revision)
        self._spellcheck_worker = worker
        self._track_worker(worker)
        worker.signals.done.connect(lambda worker=worker: self._clear_worker_reference("_spellcheck_worker", worker), Qt.ConnectionType.QueuedConnection)
        worker.signals.finished.connect(
            lambda suggestions: self._apply_spellcheck_results(editor, revision, suggestions, settings_generation, active_generation, spellcheck_generation),
            Qt.ConnectionType.QueuedConnection,
        )
        worker.signals.failed.connect(
            lambda exc: self._spellcheck_failed(exc, editor, revision, settings_generation, active_generation, spellcheck_generation),
            Qt.ConnectionType.QueuedConnection,
        )
        self.thread_pool.start(worker)

    def _spellcheck_failed(self, error, editor, revision, settings_generation, active_generation, spellcheck_generation) -> None:
        if (editor is not self.tabs.current_editor() or editor.revision != revision
                or settings_generation != self._settings_generation
                or active_generation != self._active_document_generation
                or spellcheck_generation != self._spellcheck_generation):
            return
        self.status.showMessage(f"Spellcheck failed: {error}")

    def _apply_spellcheck_results(self, editor, revision: int, suggestions, settings_generation=None, active_generation=None, spellcheck_generation=None) -> None:
        if (not self.settings.ai_enabled or editor is not self.tabs.current_editor()
                or editor.revision != revision
                or (settings_generation is not None and settings_generation != self._settings_generation)
                or (active_generation is not None and active_generation != self._active_document_generation)
                or (spellcheck_generation is not None and spellcheck_generation != self._spellcheck_generation)):
            return
        editor.set_spell_suggestions(suggestions)
        self._connected = True
        self.ai_status = "AI: Connected"
        self._update_status()
        self.status.showMessage(f"Found {len(editor.spell_suggestions)} spelling suggestion{'s' if len(editor.spell_suggestions) != 1 else ''}. Right-click an underline to review.")

    def _cancel_pending_ai(self) -> None:
        self._completion_timer.stop()
        self._spellcheck_timer.stop()
        self._completion_generation += 1
        self._generate_generation += 1
        self._settings_generation += 1
        for worker in list(self._workers):
            worker.cancel()

    def closeEvent(self, event) -> None:
        if self._closing_confirmed:
            self._cancel_pending_ai()
            event.accept()
            return
        if self._saving_editors:
            event.ignore()
            self.statusBar().showMessage("Wait for the current save to finish before closing.")
            return
        if self._quit_in_progress:
            event.ignore()
            return
        event.ignore()
        self._quit_in_progress = True
        self._quit_discards = {}
        self._confirm_quit_documents()

    def _confirm_quit_documents(self) -> None:
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            if editor is None or not editor.document_state.dirty:
                continue
            if self._quit_discards.get(editor) == editor.document_state.revision:
                continue
            self.tabs.setCurrentIndex(index)
            answer = self._ask_to_save_dirty_document(editor)
            if answer == QMessageBox.StandardButton.Cancel:
                self._quit_in_progress = False
                self._quit_discards.clear()
                return
            if answer == QMessageBox.StandardButton.Discard:
                self._quit_discards[editor] = editor.document_state.revision
                return self._confirm_quit_documents()
            started = self._save_editor(
                editor,
                callback=lambda saved: self._continue_quit_after_save(saved),
            )
            if started:
                return
            self._quit_in_progress = False
            self._quit_discards.clear()
            return
        self._close_after_confirmed_quit()

    def _ask_to_save_dirty_document(self, editor) -> QMessageBox.StandardButton:
        return QMessageBox.question(
            self,
            "Unsaved changes",
            f"Save changes to {editor.document_state.display_name}?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )

    def _close_after_confirmed_quit(self) -> None:
        self._closing_confirmed = True
        self._quit_in_progress = False
        self.close()

    def _continue_quit_after_save(self, saved: bool) -> None:
        if not saved:
            self._quit_in_progress = False
            self._quit_discards.clear()
            return
        self._confirm_quit_documents()
