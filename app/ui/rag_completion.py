"""Manual, opt-in project completion review and worker orchestration."""

from dataclasses import replace
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QListWidget, QListWidgetItem, QLabel, QPlainTextEdit, QMessageBox

from app.i18n import format_qt

from app.ai.captured_completion import generate_captured_completion
from app.ai.completion_service import STALE_PROJECT_CONTEXT, build_context
from app.ai.context_budget import ContextBudget
from app.ai.context_prompt import ContextPrompt
from app.ai.prompts import detect_language
from app.ai.ollama_client import OllamaClient
from app.document.encoding import qt_position_to_python_index
from app.project.rag_context import CapturedContext, ContextRequest, ProjectContextService, RetrievalPolicy
from app.project.rag_index import LexicalIndex
from app.project.rag_embeddings import SemanticRetriever
from app.project.rag_sources import BufferText
from app.settings.settings import AppSettings
from .ai_activity import AIActivityPanel
from .completion_context_dialog import CompletionContextDialog
from .workers import FunctionWorker


if TYPE_CHECKING:
    from .main_window import MainWindow


class RAGCompletionDialog(CompletionContextDialog):
    REBUILD = 2

    def __init__(self, destination: str, captured: CapturedContext,
                 excluded: frozenset[str], parent=None) -> None:
        summary = self.tr(
            "Review the exact prompt and source manifest below. Buffer revisions identify open "
            "text; null revisions identify disk text. Budget values are conservative token "
            "estimates, not exact tokenizer counts. Coverage notices and omitted sources are "
            "listed in the manifest. Check sources to exclude, then rebuild before sending."
        )
        budget = captured.budget
        summary += "\n" + format_qt(self.tr(
            "Token budget: window %1; output reserve %2; safety %3; message overhead %4; estimated remaining %5."
        ), budget.context_tokens, budget.output_tokens, budget.safety_tokens,
            budget.message_overhead_tokens, captured.manifest.estimated_remaining_tokens)
        summary += "\n" + format_qt(self.tr("Retrieval mode: %1"), captured.manifest.retrieval_method)
        if captured.manifest.notices:
            summary += "\n" + "\n".join(captured.manifest.notices)
        super().__init__(destination, captured.prompt, summary, parent)
        role = QPlainTextEdit(captured.role, self)
        role.setReadOnly(True)
        role.setMaximumHeight(80)
        role.setAccessibleName(self.tr("Captured role instructions"))
        self.layout().insertWidget(2, role)
        self.context.setPlainText(captured.prompt + "\n\n"
                                  + self.tr("--- SOURCE MANIFEST (not sent) ---")
                                  + "\n" + captured.manifest.to_json())
        self.sources = QListWidget(self)
        self.sources.setAccessibleName(self.tr("Sources to exclude"))
        mandatory = {item.source_id for item in captured.manifest.decisions
                     if item.disposition == "mandatory"}
        for source in captured.source_capture.sources:
            if source.kind not in {"scene", "note"} or source.id in mandatory:
                continue
            item = QListWidgetItem(f"{source.title} [{source.id}]", self.sources)
            item.setData(Qt.ItemDataRole.UserRole, source.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if source.id in excluded else Qt.CheckState.Unchecked)
        self.layout().insertWidget(self.layout().count() - 1, QLabel(self.tr("Sources to exclude"), self))
        self.layout().insertWidget(self.layout().count() - 1, self.sources)
        buttons = self.findChild(QDialogButtonBox)
        self.send_button = next(button for button in buttons.buttons()
                                if buttons.buttonRole(button) == QDialogButtonBox.ButtonRole.AcceptRole)
        rebuild = buttons.addButton(self.tr("Rebuild context"), QDialogButtonBox.ButtonRole.ActionRole)
        rebuild.clicked.connect(lambda: self.done(self.REBUILD))
        self.sources.itemChanged.connect(lambda: self.send_button.setEnabled(self.excluded_ids() == excluded))
        self.setTabOrder(role, self.context)
        self.setTabOrder(self.context, self.sources)
        self.setTabOrder(self.sources, rebuild)
        self.setTabOrder(rebuild, self.send_button)
        self.resize(780, 720)

    def excluded_ids(self) -> frozenset[str]:
        return frozenset(self.sources.item(index).data(Qt.ItemDataRole.UserRole)
                         for index in range(self.sources.count())
                         if self.sources.item(index).checkState() == Qt.CheckState.Checked)


def request_rag_completion(window: "MainWindow") -> None:
    editor = window.tabs.current_editor()
    binding = window._project_documents.get(editor)
    if not editor or not window.settings.ai_enabled or not window.settings.completion_enabled:
        return
    if not binding or binding.project is not window.project or binding.kind != "scene":
        window.statusBar().showMessage(RAGCompletionDialog.tr("RAG completion requires an open project scene."), 6000)
        return
    if window.settings.ollama_context_length <= 0:
        window.statusBar().showMessage(RAGCompletionDialog.tr("Set an explicit Ollama token window in AI Settings before using RAG completion."), 6000)
        return
    cursor = editor.textCursor()
    if cursor.hasSelection():
        return
    text = editor.toPlainText()
    position, revision = cursor.position(), editor.revision
    passage = build_context(text, qt_position_to_python_index(text, position),
                            maximum_characters=window.settings.context_size)
    if not passage.strip():
        return
    embedding_provider = None
    if window.settings.rag_embeddings_enabled:
        host, model = window.settings.embedding_host, window.settings.embedding_model
        consent = QMessageBox.question(window, RAGCompletionDialog.tr("Embedding destination"),
            format_qt(RAGCompletionDialog.tr(
                "Send the query and eligible project passages (including unsaved text) to %1 using %2 "
                "for embeddings? This destination may be remote. Requests appear in AI diagnostics. "
                "Saved-source vectors are cached locally; unsaved vectors stay in memory. "
                "Rebuilding can send newly included sources. No model is downloaded. "
                "Generation requires its separate review afterwards."
            ), host, model), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if consent != QMessageBox.StandardButton.Yes:
            return
        embedding_provider = OllamaClient(host, model, interaction_observer=window._emit_ai_interaction)
    window._completion_timer.stop()
    window._completion_generation += 1
    generation = window._completion_generation
    if window._completion_worker:
        window._discard_ai_worker(window._completion_worker)
    editor.clear_completion()
    project = window.project
    project_generation = window._project_generation
    settings_generation = window._settings_generation
    provider = window.completion_service.provider
    temperature = window.settings.temperature
    destination = provider.host + " / " + provider.model
    cache_root = AppSettings._default_settings_path().parent

    def open_buffers() -> dict[str, BufferText]:
        return {item.item_id: BufferText(tab.toPlainText(), tab.revision)
                for tab, item in window._project_documents.items()
                if item.project is project and item.kind in {"scene", "note"}
                and window.tabs.indexOf(tab) >= 0}

    buffers = open_buffers()
    try:
        request = ContextRequest(
            layout=ContextPrompt(window.settings.ai_role, window.settings.completion_template,
                                 detect_language(passage) if window.settings.language == "Auto" else window.settings.language),
            budget=ContextBudget(window.settings.ollama_context_length, window.settings.maximum_suggestion_length),
            mandatory_text=passage, current_passage=passage, target_scene_id=binding.item_id,
            policy=RetrievalPolicy(excluded_source_ids=frozenset(window._completion_excluded_notes)),
        )
    except ValueError as error:
        window._completion_failed(error, generation, settings_generation)
        return

    def current() -> bool:
        cursor = editor.textCursor() if editor is window.tabs.current_editor() else None
        return (generation == window._completion_generation and cursor is not None
                and not cursor.hasSelection() and cursor.position() == position
                and editor.revision == revision and window.project is project
                and window._project_generation == project_generation
                and window._settings_generation == settings_generation and open_buffers() == buffers)

    def idle() -> None:
        if generation == window._completion_generation:
            window.ai_status = "AI: Connected" if window._connected else "AI: Offline"
            window._update_status()

    def failed(error):
        if current():
            window._completion_failed(error, generation, settings_generation)
        else:
            idle()

    def start(function, ready):
        # Worker predicates read captured/plain generations, never Qt widget state.
        def cancelled():
            return (worker.cancelled or generation != window._completion_generation
                    or settings_generation != window._settings_generation
                    or project_generation != window._project_generation
                    or window.project is not project)

        worker = FunctionWorker(lambda: function(cancelled))
        window._completion_worker = worker
        window._track_worker(worker)
        worker.signals.done.connect(lambda: window._clear_worker_reference("_completion_worker", worker), Qt.ConnectionType.QueuedConnection)
        worker.signals.finished.connect(ready, Qt.ConnectionType.QueuedConnection)
        worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
        window._track_ai_activity(worker, AIActivityPanel.tr("Text completion"),
                                 context=editor.document_state.display_name, current=current,
                                 cancel=lambda: window._cancel_activity_completion(worker))
        window.ai_status = "AI: Generating..."
        window._update_status()
        window.thread_pool.start(worker)

    def capture(request: ContextRequest) -> None:
        def work(cancelled):
            index = LexicalIndex(cache_root, project.root, project.manifest.project_id)
            semantic = SemanticRetriever(embedding_provider, index) if embedding_provider is not None else None
            return ProjectContextService(index, semantic=semantic).capture(project, request, open_buffers=buffers,
                                                        is_cancelled=cancelled)

        def review(captured: CapturedContext) -> None:
            if not current():
                idle()
                return
            idle()
            dialog = RAGCompletionDialog(destination, captured, request.policy.excluded_source_ids, window)
            result = dialog.exec()
            if not current():
                return
            if result == RAGCompletionDialog.REBUILD:
                capture(replace(request, policy=replace(request.policy, excluded_source_ids=dialog.excluded_ids())))
            elif result == dialog.DialogCode.Accepted:
                start(lambda cancelled: generate_captured_completion(
                    provider, captured, buffers, temperature=temperature, is_cancelled=cancelled), completed)

        start(work, review)

    def completed(result):
        if not current():
            idle()
            return
        if result is STALE_PROJECT_CONTEXT:
            idle()
            window.statusBar().showMessage(RAGCompletionDialog.tr("Project sources changed; review a new completion context."), 6000)
            return
        window._completion_finished(generation, editor, revision, position, result,
                                    (position, position), settings_generation)

    capture(request)
