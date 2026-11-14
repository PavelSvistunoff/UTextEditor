"""Debounced automatic retrieval orchestration; all file/network work is queued."""

from dataclasses import replace
from time import monotonic
from typing import TYPE_CHECKING

from PySide6.QtCore import QFileSystemWatcher, QObject, Qt, QTimer
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox

from app.ai.captured_completion import generate_captured_completion
from app.ai.completion_service import STALE_PROJECT_CONTEXT, build_context
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.ollama_client import OllamaClient
from app.ai.prompts import detect_language
from app.document.encoding import qt_position_to_python_index
from app.project.inline_context import InlineContextService
from app.project.rag_context import ContextRequest, RetrievalPolicy
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText, CaptureCancelled
from app.project.service import MANIFEST_NAME
from app.settings.settings import AppSettings
from .ai_activity import AIActivityPanel
from .rag_completion import RAGCompletionDialog
from .workers import FunctionWorker

if TYPE_CHECKING:
    from .main_window import MainWindow

MAX_OPEN_BUFFER_CHARACTERS = 4 * 1024 * 1024
MAX_SOURCE_CHARACTERS = 1024 * 1024
PRECEDING_CONTEXT_CHARACTERS = 1024
EMBEDDING_SOCKET_SECONDS = 0.25


class InlineRetrieval(QObject):
    """One active automatic worker and one coalesced latest intent per window."""

    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.service = InlineContextService()
        self.active: FunctionWorker | None = None
        self.pending: int | None = None
        self.displayed = None
        self.excluded = frozenset()
        self.scope = None
        self.embedding_approved = None
        self.embedding_declined = None
        self.disclosure = None
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self.invalidate_sources)
        self.watcher.directoryChanged.connect(self.invalidate_sources)
        self.poll = QTimer(self)
        self.poll.setInterval(1000)
        self.poll.timeout.connect(lambda: self.verify_displayed(accept=False))
        self.display_current = lambda: False
        self.display_cancelled = lambda: True
        self.display_buffers = {}
        self.accept_pending = False

    def invalidate_sources(self, *_args) -> None:
        window = self.window
        window._completion_generation += 1
        self.pending = None
        if self.active is not None:
            self.active.cancel()
        self.forget_display()

    def forget_display(self) -> None:
        self.poll.stop()
        self.accept_pending = False
        if self.displayed is not None:
            editor = self.displayed[0]
            if (self.window.tabs.indexOf(editor) >= 0
                    and editor.completion_accept_handler == self._accept_displayed):
                editor.clear_completion()
        self.displayed = None
        self.display_buffers = {}
        self.display_current = lambda: False
        self.display_cancelled = lambda: True
        paths = self.watcher.files() + self.watcher.directories()
        if paths:
            self.watcher.removePaths(paths)

    def _embedding_consent(self) -> bool:
        window = self.window
        key = (window.settings.embedding_host, window.settings.embedding_model,
               window._settings_generation)
        if key == self.embedding_approved:
            return True
        if key == self.embedding_declined or self.disclosure is not None:
            return False
        dialog = QMessageBox(window)
        dialog.setWindowTitle(self.tr("Automatic embedding destination"))
        dialog.setText(self.tr(
            "Allow automatic query embeddings at the destination below? Only existing saved-source "
            "vectors are reused; typing never creates document vectors. The query may include unsaved "
            "text and associated character names. This host may be remote; requests appear in AI "
            "diagnostics. Declining keeps lexical retrieval for this settings session. No model is downloaded."
        ) + "\n" + key[0] + " / " + key[1])
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.setWindowModality(Qt.WindowModality.NonModal)
        self.disclosure = dialog

        def finished(result):
            self.disclosure = None
            if result == QMessageBox.StandardButton.Yes:
                self.embedding_approved = key
            else:
                self.embedding_declined = key
            dialog.deleteLater()
            if (window.settings.ai_enabled and window.settings.automatic_retrieval
                    and window._settings_generation == key[2] and not window._closing_confirmed):
                window._completion_timer.start(window.settings.completion_debounce_ms)

        dialog.finished.connect(finished)
        dialog.show()
        return False

    def request(self) -> None:
        request_started = monotonic()
        window = self.window
        editor = window.tabs.current_editor()
        binding = window._project_documents.get(editor)
        if not binding or binding.project is not window.project or binding.kind != "scene":
            return
        window._completion_timer.stop()
        window._completion_generation += 1
        generation = window._completion_generation
        self.forget_display()
        editor.clear_completion()
        if self.active is not None:
            self.active.cancel()
            self.pending = generation
            return
        if window._completion_worker is not None:
            # A synchronous legacy/manual request must finish before this starts.
            old = window._completion_worker
            old.cancel()
            self.pending = generation
            self.active = old
            old.signals.done.connect(lambda: self._done(old), Qt.ConnectionType.QueuedConnection)
            return
        self.pending = None
        cursor = editor.textCursor()
        if cursor.hasSelection():
            return
        if window.settings.ollama_context_length <= 0:
            window.statusBar().showMessage(self.tr("Automatic retrieval needs an explicit Ollama token window; suggestion skipped."), 6000)
            return
        if not window._ensure_ai_context_consent(automatic=True, retry=lambda: window.request_completion(automatic=True)):
            return
        bound_editors = [tab for tab, item in window._project_documents.items()
                         if item.project is window.project and item.kind in {"scene", "note"}
                         and window.tabs.indexOf(tab) >= 0]
        sizes = [tab.document().characterCount() for tab in bound_editors]
        if any(size > MAX_SOURCE_CHARACTERS for size in sizes) or sum(sizes) > MAX_OPEN_BUFFER_CHARACTERS:
            window.statusBar().showMessage(self.tr("Open project buffers exceed automatic capture limits; suggestion skipped."), 6000)
            return
        position, revision = cursor.position(), editor.revision
        text = editor.toPlainText()
        python_position = qt_position_to_python_index(text, position)
        passage = build_context(text, python_position,
                                maximum_characters=window.settings.context_size)
        if not passage.strip():
            return
        paragraph_start = python_position - len(passage)
        preceding = text[max(0, paragraph_start - PRECEDING_CONTEXT_CHARACTERS):paragraph_start]
        query_passage = preceding + passage
        mandatory = (("Bounded preceding context:\n" + preceding + "\nCurrent paragraph:\n")
                     if preceding else "") + passage
        project = window.project
        if self.scope is not project:
            self.scope = project
            self.excluded = frozenset()
        project_generation = window._project_generation
        settings_generation = window._settings_generation
        buffers = {item.item_id: BufferText(tab.toPlainText(), tab.revision)
                   for tab, item in window._project_documents.items()
                   if item.project is project and item.kind in {"scene", "note"}
                   and window.tabs.indexOf(tab) >= 0}
        stamps = {tab: tab._revision for tab, item in window._project_documents.items()
                  if item.project is project and item.kind in {"scene", "note"}
                  and window.tabs.indexOf(tab) >= 0}
        binding_count = len(stamps)
        provider = window.completion_service.provider
        temperature = window.settings.temperature
        cache_root = AppSettings._default_settings_path().parent
        hybrid_requested = window.settings.rag_embeddings_enabled
        hybrid = hybrid_requested and self._embedding_consent()
        embedding_provider = (OllamaClient(window.settings.embedding_host, window.settings.embedding_model,
                              timeout=EMBEDDING_SOCKET_SECONDS, interaction_observer=window._emit_ai_interaction) if hybrid else None)
        try:
            request = ContextRequest(
                layout=ContextPrompt(window.settings.ai_role, window.settings.completion_template,
                    detect_language(passage) if window.settings.language == "Auto" else window.settings.language),
                budget=ContextBudget(window.settings.ollama_context_length, window.settings.maximum_suggestion_length),
                mandatory_text=mandatory, current_passage=query_passage, target_scene_id=binding.item_id,
                policy=RetrievalPolicy(maximum_passages=4,
                    excluded_source_ids=self.excluded | frozenset(window._completion_excluded_notes)),
            )
        except ValueError as error:
            window._completion_failed(error, generation, settings_generation)
            return

        def stale() -> bool:
            # Worker predicates read Python stamps only. Qt values are captured
            # on the GUI thread; no widget methods or file reads occur here.
            return (generation != window._completion_generation
                    or settings_generation != window._settings_generation
                    or project_generation != window._project_generation or window.project is not project
                    or any(tab._revision != stamp or tab not in window._project_documents
                           for tab, stamp in stamps.items())
                    or sum(1 for item in tuple(window._project_documents.values())
                           if item.project is project and item.kind in {"scene", "note"}) != binding_count)

        def current() -> bool:
            cursor = editor.textCursor() if editor is window.tabs.current_editor() else None
            return (not stale() and cursor is not None and not cursor.hasSelection()
                    and cursor.position() == position and editor.revision == revision)

        def work():
            started = monotonic()
            cancelled = lambda: worker.cancelled or stale()
            index = LexicalIndex(cache_root, project.root, project.manifest.project_id)
            semantic = SemanticRetriever(embedding_provider, index, cached_only=True) if hybrid else None
            result = self.service.capture(project, index, request, buffers, semantic=semantic,
                        embedding_key=(embedding_provider.host, embedding_provider.model) if hybrid else None,
                        is_cancelled=cancelled)
            if hybrid_requested and not hybrid:
                result = replace(result, captured=replace(result.captured, manifest=replace(
                    result.captured.manifest, notices=(*result.captured.manifest.notices,
                    "Automatic embeddings are not approved for this settings session; lexical retrieval used."))))
            generated = generate_captured_completion(provider, result.captured, buffers,
                        temperature=temperature, is_cancelled=cancelled)
            return result, generated, monotonic() - started

        def ready(result):
            if not current():
                return
            context_result, text, worker_seconds = result
            if text is STALE_PROJECT_CONTEXT:
                window.ai_status = "AI: Connected" if window._connected else "AI: Offline"
                window._update_status()
                window.statusBar().showMessage(self.tr("Project sources changed; automatic suggestion discarded."), 6000)
                return
            captured = context_result.captured
            window._completion_finished(generation, editor, revision, position, text,
                                        (position, position), settings_generation)
            if editor.has_completion:
                self.displayed = (editor, generation, captured, provider.host + " / " + provider.model)
                self.display_current = current
                self.display_cancelled = stale
                self.display_buffers = buffers
                editor.completion_accept_handler = self._accept_displayed
                self.poll.start()
                paths = self.watcher.files() + self.watcher.directories()
                if paths:
                    self.watcher.removePaths(paths)
                # Watch saved sources while the ghost is displayed. Atomic file
                # replacements also notify the parent directory. Worker-side
                # byte verification remains authoritative before/after generation.
                sources = captured.source_capture.disk_sources
                watched = {str(project.root / MANIFEST_NAME), str(project.root)}
                for source in sources:
                    if source.relative_path:
                        path = project.root / source.relative_path
                        watched.update((str(path), str(path.parent)))
                self.watcher.addPaths(sorted(watched))
                elapsed = monotonic() - request_started
                summary = (f"RAG: {captured.manifest.retrieval_state}; {captured.manifest.retrieval_method}; "
                           f"retrieval {context_result.retrieval_seconds * 1000:.0f} ms; request {elapsed * 1000:.0f} ms; "
                           f"worker {worker_seconds * 1000:.0f} ms; "
                           f"cache {'hit' if context_result.cache_hit else 'miss'}")
                if captured.manifest.notices:
                    summary += "; " + " ".join(captured.manifest.notices)
                window.statusBar().showMessage(summary, 10000)

        def failed(error):
            if current():
                if isinstance(error, CaptureCancelled):
                    window.ai_status = "AI: Connected" if window._connected else "AI: Offline"
                    window._update_status()
                    window.statusBar().showMessage(self.tr("Automatic context capture expired; suggestion skipped."), 6000)
                else:
                    window._completion_failed(error, generation, settings_generation)

        worker = FunctionWorker(work)
        self.active = worker
        window._completion_worker = worker
        window._track_worker(worker)
        worker.signals.finished.connect(ready, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
        worker.signals.done.connect(lambda: self._done(worker), Qt.ConnectionType.QueuedConnection)
        window._track_ai_activity(worker, AIActivityPanel.tr("Text completion"), current=current,
                                 cancel=lambda: window._cancel_activity_completion(worker))
        window.ai_status = "AI: Generating..."
        window._update_status()
        window.thread_pool.start(worker)

    def _done(self, worker: FunctionWorker) -> None:
        window = self.window
        if self.active is not worker:
            return
        self.active = None
        owns_completion_status = window._completion_worker is worker
        window._clear_worker_reference("_completion_worker", worker)
        pending, self.pending = self.pending, None
        if owns_completion_status and window.ai_status == "AI: Generating...":
            window.ai_status = "AI: Connected" if window._connected else "AI: Offline"
            window._update_status()
        if pending == window._completion_generation and window.settings.automatic_retrieval:
            QTimer.singleShot(0, lambda: window.request_completion(automatic=True)
                              if pending == window._completion_generation else None)
        elif self.accept_pending:
            self.accept_pending = False
            QTimer.singleShot(0, lambda: self.verify_displayed(accept=True))

    def _accept_displayed(self) -> None:
        self.verify_displayed(accept=True)

    def verify_displayed(self, *, accept: bool) -> None:
        """Byte verification on a worker also gates explicit Tab acceptance.

        Native file notifications are advisory (some platforms coalesce or miss
        them); polling and acceptance verification do not rely on their arrival.
        """
        if self.displayed is None:
            self.poll.stop()
            return
        editor, generation, captured, _destination = self.displayed
        current, stale = self.display_current, self.display_cancelled
        if not current() or not editor.has_completion:
            self.forget_display()
            return
        if self.active is not None:
            self.accept_pending = self.accept_pending or accept
            return
        window = self.window
        buffers = self.display_buffers

        def work():
            deadline = monotonic() + 1.0
            captured.source_capture.verify_current(buffers, is_cancelled=lambda:
                worker.cancelled or stale() or monotonic() >= deadline)

        def verified(_result):
            if not current() or not editor.has_completion:
                self.forget_display()
                return
            if accept:
                editor.completion_accept_handler = None
                editor.accept_completion()
                self.forget_display()

        def failed(_error):
            if generation == window._completion_generation:
                self.invalidate_sources()
                window.statusBar().showMessage(self.tr("Project sources changed; automatic suggestion discarded."), 6000)

        worker = FunctionWorker(work)
        self.active = worker
        window._completion_worker = worker
        window._track_worker(worker)
        worker.signals.finished.connect(verified, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
        worker.signals.done.connect(lambda: self._done(worker), Qt.ConnectionType.QueuedConnection)
        window.thread_pool.start(worker)

    def inspect(self) -> None:
        window = self.window
        if self.displayed is None:
            window.statusBar().showMessage(self.tr("No retrieved inline suggestion is displayed."), 6000)
            return
        editor, generation, captured, destination = self.displayed
        if editor is not window.tabs.current_editor() or not editor.has_completion or generation != window._completion_generation:
            self.displayed = None
            window.statusBar().showMessage(self.tr("No retrieved inline suggestion is displayed."), 6000)
            return
        dialog = RAGCompletionDialog(destination, captured,
                    self.excluded | frozenset(window._completion_excluded_notes), window)
        dialog.send_button.hide()
        buttons = dialog.findChild(QDialogButtonBox)
        for button in buttons.buttons():
            if buttons.buttonRole(button) == buttons.ButtonRole.ActionRole:
                button.setText(self.tr("Apply exclusions for future suggestions"))
        if dialog.exec() == dialog.REBUILD and window.project is self.scope:
            self.excluded = dialog.excluded_ids()
            self.invalidate_sources()
        dialog.deleteLater()
