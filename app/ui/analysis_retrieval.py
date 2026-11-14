"""GUI capture and queued source review shared by analysis/character workflows."""

from collections.abc import Callable
from typing import TYPE_CHECKING

from app.project.analysis_context import AnalysisRetrieval
from app.project.service import Project
from app.project.rag_sources import BufferText
from app.settings.settings import AppSettings
from .auto_writer_context_review import AutoWriterContextReview

if TYPE_CHECKING:
    from .main_window import MainWindow


def create_analysis_retrieval(window: "MainWindow", project: Project, *, title: str,
                              current: Callable[[], bool], cancelled: Callable[[], bool],
                              cancel: Callable[[], None], scene_id: str | None = None,
                              mandatory_source_ids: frozenset[str] = frozenset()
                              ) -> tuple[AnalysisRetrieval, AutoWriterContextReview, Callable[[], bool]]:
    """Called on the GUI thread; returned predicates never read widgets in workers."""
    def stamps():
        return {editor: (binding.item_id, editor.revision)
                for editor, binding in window._project_documents.items()
                if binding.project is project and binding.kind in {"scene", "note"}
                and window.tabs.indexOf(editor) >= 0}

    captured_stamps = stamps()
    buffers = {source_id: BufferText(editor.toPlainText(), revision)
               for editor, (source_id, revision) in captured_stamps.items()}
    bridge = AutoWriterContextReview(window.provider.host + " / " + window.provider.model,
        is_current=lambda: current() and stamps() == captured_stamps,
        is_cancelled=cancelled, cancel=cancel, parent=window,
        excludable_kinds=frozenset({"scene", "note"}),
        review_title=AutoWriterContextReview.tr("Review analysis and character context"),
        extra_summary=AutoWriterContextReview.tr(
            "Required inputs cannot be excluded. Background coverage is partial. Earlier manuscript "
            "order does not prove story chronology; mentions do not establish presence or knowledge. "
            "Only the selected scene excerpt can support arc updates. No embeddings are sent."
        ))
    run = AnalysisRetrieval(project, AppSettings._default_settings_path().parent,
        window.settings.ollama_context_length, buffers, title=title, review=bridge.review,
        is_cancelled=cancelled, scene_id=scene_id, mandatory_source_ids=mandatory_source_ids)
    return run, bridge, lambda: stamps() == captured_stamps
