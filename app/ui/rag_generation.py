"""Explicit free-prompt project retrieval; all source I/O runs in workers."""

from dataclasses import replace
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QInputDialog, QMessageBox

from app.ai.captured_completion import generate_captured_completion
from app.ai.completion_service import STALE_PROJECT_CONTEXT
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.project.rag_context import CapturedContext, ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_index import LexicalIndex
from app.project.rag_sources import BufferText
from app.settings.settings import AppSettings
from .ai_activity import AIActivityPanel
from .generated_text_dialog import GeneratedTextDialog
from .rag_completion import RAGCompletionDialog
from .workers import FunctionWorker, StreamingWorker

if TYPE_CHECKING:
    from .main_window import MainWindow


def request_project_generation(window: "MainWindow") -> None:
    """Separate action: ordinary Generate remains strictly prompt-only."""
    editor, project = window.tabs.current_editor(), window.project
    if editor is None or not window.settings.ai_enabled:
        return
    if project is None or window.settings.ollama_context_length <= 0:
        window.statusBar().showMessage(RAGCompletionDialog.tr(
            "Project generation requires an open project and an explicit Ollama token window."
        ), 6000)
        return
    prompt, accepted = QInputDialog.getMultiLineText(window, RAGCompletionDialog.tr("Generate with Project Context…"),
        RAGCompletionDialog.tr("Describe what you want the AI to write:"), "")
    if not accepted or not prompt.strip():
        return
    target = None
    passage = ""
    binding = window._project_documents.get(editor)
    if binding is not None and binding.project is project and binding.kind == "scene":
        answer = QMessageBox.question(window, RAGCompletionDialog.tr("Current scene context"), RAGCompletionDialog.tr(
            "Include the selected text, or the whole current scene when nothing is selected, "
            "as required context? No uses only your prompt to search the project."
        ), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Cancel:
            return
        if answer == QMessageBox.StandardButton.Yes:
            cursor = editor.textCursor()
            passage = cursor.selectedText().replace("\u2029", "\n") if cursor.hasSelection() else editor.toPlainText()
            target = binding.item_id
    # Consent to generation is the exact role/prompt/source review below. This
    # action deliberately uses lexical retrieval and sends no embedding requests.
    window.cancel_text_generation()
    window._generate_generation += 1
    generation = window._generate_generation
    project_generation, settings_generation = window._project_generation, window._settings_generation
    revision = editor.revision
    cursor = editor.textCursor()
    position = cursor.position()
    selection = (cursor.selectionStart(), cursor.selectionEnd())
    provider, temperature = window.provider, window.settings.temperature
    streaming = window.settings.streaming_preview
    destination = provider.host + " / " + provider.model
    cache_root = AppSettings._default_settings_path().parent

    def open_buffers() -> dict[str, BufferText]:
        return {item.item_id: BufferText(tab.toPlainText(), tab.revision)
                for tab, item in window._project_documents.items()
                if item.project is project and item.kind in {"scene", "note"}
                and window.tabs.indexOf(tab) >= 0}

    buffers = open_buffers()

    def current() -> bool:
        if (generation != window._generate_generation or project is not window.project
                or project_generation != window._project_generation
                or settings_generation != window._settings_generation
                or editor is not window.tabs.current_editor() or editor.revision != revision):
            return False
        cursor = editor.textCursor()
        return (cursor.position() == position and (cursor.selectionStart(), cursor.selectionEnd()) == selection
                and open_buffers() == buffers)

    def idle() -> None:
        if generation == window._generate_generation:
            window.ai_status = "AI: Connected" if window._connected else "AI: Offline"
            window._update_status()

    def failed(error):
        if current():
            window._generation_failed(error, generation, settings_generation)
        else:
            idle()

    def start(function, ready, *, preview=False):
        def cancelled():
            return (worker.cancelled or generation != window._generate_generation
                    or project_generation != window._project_generation
                    or settings_generation != window._settings_generation or project is not window.project)

        if preview:
            worker = StreamingWorker(lambda **kwargs: function(cancelled, kwargs["on_chunk"]))
        else:
            worker = FunctionWorker(lambda: function(cancelled))
        window._generate_worker = worker
        window._track_worker(worker)
        window._track_ai_activity(worker, AIActivityPanel.tr("Text generation"),
                                  context=editor.document_state.display_name, current=current,
                                  cancel=lambda: window.cancel_text_generation()
                                  if window._generate_worker is worker else worker.cancel())
        worker.signals.done.connect(lambda: window._generation_worker_done(worker), Qt.ConnectionType.QueuedConnection)
        worker.signals.finished.connect(ready, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
        if window._generate_cancel_action is not None:
            window._generate_cancel_action.setEnabled(True)
        if preview:
            window._show_streaming_preview(worker, generation, editor, revision, position, selection, settings_generation)
        window.ai_status = "AI: Generating..."
        window._update_status()
        window.thread_pool.start(worker)

    def capture(request: ContextRequest) -> None:
        def work(cancelled):
            index = LexicalIndex(cache_root, project.root, project.manifest.project_id)
            return ProjectContextService(index).capture(project, request, open_buffers=buffers,
                                                       is_cancelled=cancelled)

        def review(captured: CapturedContext) -> None:
            idle()
            if not current():
                return
            dialog = RAGCompletionDialog(destination, captured, request.policy.excluded_source_ids, window)
            decision = dialog.exec()
            excluded = dialog.excluded_ids()
            dialog.deleteLater()
            if not current():
                return
            if decision == RAGCompletionDialog.REBUILD:
                capture(replace(request, policy=replace(request.policy, excluded_source_ids=excluded)))
            elif decision == QDialog.DialogCode.Accepted:
                generate(captured)

        start(work, review)

    def generate(captured: CapturedContext) -> None:
        stale = [False]

        def work(cancelled, on_chunk=None):
            result = generate_captured_completion(provider, captured, buffers, temperature=temperature,
                                                 is_cancelled=cancelled, on_chunk=on_chunk)
            stale[0] = result is STALE_PROJECT_CONTEXT
            return "" if stale[0] else result

        def ready(text):
            idle()
            if not current():
                return
            if stale[0]:
                failed(ValueError("Project sources changed; capture and review a new request."))
                return
            dialog = GeneratedTextDialog(text, window)
            decision = dialog.exec()
            dialog.deleteLater()
            if decision != QDialog.DialogCode.Accepted or not current():
                return

            def verify(cancelled):
                if cancelled():
                    return False
                captured.verify_current(buffers)
                return not cancelled()

            def insert(verified):
                idle()
                if not verified or not current():
                    return
                cursor = editor.textCursor()
                cursor.beginEditBlock()
                cursor.insertText(text)
                cursor.endEditBlock()

            # Review may stay open while a closed source changes on disk.
            # Reverify in a worker after Insert, before touching the manuscript.
            start(verify, insert)

        start(work, ready, preview=streaming)

    try:
        request = ContextRequest(ContextPrompt(window.settings.ai_role),
            ContextBudget(window.settings.ollama_context_length, window.settings.maximum_suggestion_length),
            mandatory_text=prompt.strip() + ("\n\nAuthor-selected scene context:\n" + passage if target else ""),
            author_request=prompt.strip(), current_passage=passage, target_scene_id=target,
            policy=RetrievalPolicy(chronology="earlier" if target else "all"))
    except ValueError as error:
        failed(error)
        return
    capture(request)
