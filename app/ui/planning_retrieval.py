"""Reviewed project planning orchestration; provider and file I/O stay in workers."""

from threading import Event
from typing import TYPE_CHECKING, Literal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox

from app.ai.project_planning import generate_project_outline, suggest_project_brief
from app.i18n import format_qt
from app.project import Project, ProjectError
from app.project.autopilot import run_autopilot
from app.project.character_context import project_planning_context
from app.project.planning_context import PlanningRetrievalRun
from app.project.rag_sources import BufferText
from app.settings.settings import AppSettings
from .ai_activity import AIActivityPanel
from .auto_writer_context_review import AutoWriterContextReview
from .project_brief_dialog import ProjectBriefDialog
from .project_setup_dialog import ProjectSetupDialog
from .workers import FunctionWorker

if TYPE_CHECKING:
    from .main_window import MainWindow


def start_planning_retrieval(window: "MainWindow", project: Project,
                             mode: Literal["brief", "outline", "autopilot"], brief: str,
                             dialog: ProjectBriefDialog | None = None) -> None:
    if project is not window.project or not window.settings.ai_enabled or window._project_busy:
        return
    if window.settings.ollama_context_length <= 0:
        window.statusBar().showMessage(ProjectBriefDialog.tr(
            "Set an explicit Ollama token window before using planning retrieval."
        ), 8000)
        return
    if mode == "autopilot":
        answer = QMessageBox.question(window, ProjectBriefDialog.tr("Confirm retrieved Auto-pilot"),
            ProjectBriefDialog.tr(
                "Auto-pilot will review project passages before planning and each new scene. "
                "After all requests succeed, it automatically appends the complete plan, scene drafts "
                "and character notes without a final draft approval. Existing files are preserved. "
                "Cancel or failure before application adds nothing. Continue?"
            ), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            return
        if project is not window.project or not window.settings.ai_enabled or window._project_busy:
            return
    window._project_setup_generation += 1
    generation = window._project_setup_generation
    settings_generation, project_generation = window._settings_generation, window._project_generation
    provider, temperature = window.provider, window.settings.temperature
    event = Event()

    def open_stamps():
        return {tab: (item.item_id, tab.revision) for tab, item in window._project_documents.items()
                if item.project is project and item.kind in {"scene", "note"}
                and window.tabs.indexOf(tab) >= 0}

    stamps = open_stamps()
    buffers = {item_id: BufferText(tab.toPlainText(), revision)
               for tab, (item_id, revision) in stamps.items()}

    def cancelled() -> bool:
        # Worker predicate: plain captured generations only, no Qt access.
        return (event.is_set() or generation != window._project_setup_generation
                or settings_generation != window._settings_generation
                or project_generation != window._project_generation or project is not window.project)

    def current() -> bool:
        return (not cancelled() and window.settings.ai_enabled and open_stamps() == stamps
                and (dialog is None or (dialog is window._project_setup_brief_dialog and dialog.brief() == brief)))

    def cancel() -> None:
        event.set()
        if generation == window._project_setup_generation:
            window.cancel_project_setup()

    bridge = AutoWriterContextReview(provider.host + " / " + provider.model,
        is_current=current, is_cancelled=cancelled, cancel=cancel, parent=window,
        excludable_kinds=frozenset({"scene", "note"}),
        review_title=ProjectBriefDialog.tr("Review planning context"),
        extra_summary=ProjectBriefDialog.tr(
            "The brief and compact character motivations are required. Retrieved passages are partial "
            "project records; invented plans and earlier generated drafts are provisional. "
            "No embeddings are sent. Source exclusions require rebuilding before Send."
        ))
    run = PlanningRetrievalRun(project, AppSettings._default_settings_path().parent,
        window.settings.ollama_context_length, brief, buffers, review=bridge.review,
        is_cancelled=cancelled, require_complete=mode == "autopilot")
    motivation = project_planning_context(project)
    outline = window._project_outline_metadata(project, complete=True)
    window._planning_retrieval_evidence = ()

    def work():
        if mode == "brief":
            result = suggest_project_brief(provider, brief, 1400, temperature, retrieval=run)
        elif mode == "outline":
            result = generate_project_outline(provider, brief, 1800, temperature,
                                               character_context=motivation, retrieval=run)
        else:
            result = run_autopilot(provider, brief, outline, character_context=motivation,
                maximum_tokens=900, temperature=temperature, is_cancelled=cancelled,
                progress=lambda completed, total, title: window.project_autopilot_progress.emit(
                    generation, completed, total, title), retrieval=run)
        run.verify()
        return result

    def finish() -> None:
        if generation != window._project_setup_generation:
            return
        window._project_setup_worker = None
        window._project_setup_cancel_event = None
        window._set_project_busy(False)
        if window._project_setup_cancel_action is not None:
            window._project_setup_cancel_action.setEnabled(False)

    def failed(error) -> None:
        valid = current()
        finish()
        if not valid:
            if (generation == window._project_setup_generation
                    and dialog is window._project_setup_brief_dialog and dialog is not None):
                dialog.set_autopilot_running(False)
            return
        message = format_qt(ProjectBriefDialog.tr(
            "Planning retrieval failed; no generated changes were applied: %1"
        ), error)
        if dialog is not None:
            dialog.set_autopilot_running(False, message)
        window.statusBar().showMessage(message, 12000)

    def completed(result) -> None:
        valid = current()
        finish()
        if not valid:
            if (generation == window._project_setup_generation
                    and dialog is window._project_setup_brief_dialog and dialog is not None):
                dialog.set_autopilot_running(False)
            return
        window._planning_retrieval_evidence = tuple(run.steps)
        if mode == "brief":
            dialog.apply_suggestion(result)
            return
        if mode == "autopilot":
            count = sum(len(scenes) for _, scenes in result.chapters)
            dialog.set_applying(ProjectBriefDialog.tr("Applying the complete retrieved Auto-pilot batch…"))
            window._run_project_mutation(run.apply_autopilot, result.chapters, result.characters,
                on_success=lambda: window._project_autopilot_applied(dialog, count), on_failure=failed)
            return
        review = ProjectSetupDialog(result, window)
        decision = review.exec()
        try:
            approved = review.outline() if decision == QDialog.DialogCode.Accepted else None
        except ProjectError as error:
            failed(error)
            return
        finally:
            review.deleteLater()
        if approved is None or not current():
            return
        window._run_project_mutation(run.apply_outline, approved,
            on_success=lambda: window.statusBar().showMessage(
                ProjectBriefDialog.tr("Approved retrieved outline added; existing manuscript text was preserved."), 8000),
            on_failure=failed)

    worker = FunctionWorker(work)
    window._project_setup_worker = worker
    if mode == "autopilot":
        window._project_setup_cancel_event = event
    window._track_worker(worker)
    activity_name = {"brief": AIActivityPanel.tr("Story suggestions"),
                     "outline": AIActivityPanel.tr("Project outline"),
                     "autopilot": AIActivityPanel.tr("Auto-pilot generation")}[mode]
    activity = window._track_ai_activity(worker, activity_name,
                                         context=project.manifest.title, current=current, cancel=cancel)
    if mode == "autopilot":
        window._autopilot_activity = activity
    worker.signals.finished.connect(completed, Qt.ConnectionType.QueuedConnection)
    worker.signals.failed.connect(failed, Qt.ConnectionType.QueuedConnection)
    worker.signals.done.connect(bridge.deleteLater, Qt.ConnectionType.QueuedConnection)
    window._set_project_busy(True)
    if dialog is not None:
        if mode == "autopilot":
            dialog.set_autopilot_running(True)
        else:
            dialog.set_suggesting(True)
    if window._project_setup_cancel_action is not None:
        window._project_setup_cancel_action.setEnabled(True)
    window.thread_pool.start(worker)
