"""Qt planning review dispatch, stale UI guards and additive application."""

from threading import Event, get_ident

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox, QLabel

from app.ui.project_brief_dialog import ProjectBriefDialog
from app.ui.project_setup_dialog import ProjectSetupDialog
from app.ui.rag_completion import RAGCompletionDialog
from tests.test_inline_retrieval_ui import wait
from tests.test_rag_completion_ui import application, scene_window
from tests.test_planning_retrieval import PLAN


@pytest.fixture
def planning(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    window.settings.completion_enabled = False
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kw: True)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    brief = ProjectBriefDialog(window)
    brief.editor.setPlainText("A story about the hidden door and copper key")
    brief.retrieval.setChecked(True)
    window._project_setup_brief_dialog = brief
    yield window, project, scene, note, editor, brief
    window.cancel_project_setup()
    window._project_setup_brief_dialog = None
    brief.close()


@pytest.mark.parametrize("mode", ["brief", "outline", "autopilot"])
def test_worker_source_reviews_run_on_gui_thread_and_record_exact_prompts(planning, monkeypatch, application, mode):
    window, project, scene, note, editor, brief = planning
    original = editor.toPlainText()
    gui = get_ident()
    reviews, sent = [], []
    answers = iter([PLAN, "Draft one.", "Draft two.", "Draft three."] if mode == "autopilot" else
                   ["# Proposed chapter\n- Proposed scene" if mode == "outline" else "[Suggestion: a mystery]"])

    def review(dialog):
        assert get_ident() == gui
        reviews.append(dialog.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0])
        assert any(window.provider.host in label.text() for label in dialog.findChildren(QLabel))
        return QDialog.DialogCode.Accepted

    def generate(prompt, **options):
        assert get_ident() != gui
        sent.append((prompt, options))
        return next(answers)

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", generate)
    monkeypatch.setattr(ProjectSetupDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    if mode == "brief":
        window._suggest_project_brief(project, brief, brief.brief())
        wait(lambda: brief.brief() == "[Suggestion: a mystery]", application)
        assert len(tuple(project.iter_scenes())) == 1
    elif mode == "outline":
        window._start_project_outline_request(project, brief.brief(), use_retrieval=True)
        wait(lambda: len(tuple(project.iter_scenes())) == 2 and not window._project_busy, application)
        added = next(item for item in project.iter_scenes() if item.id != scene.id)
        assert project.read_scene(added.id) == ""
    else:
        window._start_project_autopilot(project, brief, brief.brief())
        wait(lambda: len(tuple(project.iter_scenes())) == 4 and not window._project_busy, application)
        assert brief.autopilot_applied
        assert len(project.manifest.notes) == 2
        assert len(window._planning_retrieval_evidence) == 4
    assert [prompt for prompt, options in sent] == reviews
    assert all(options["require_full_context"] for prompt, options in sent)
    assert project.read_scene(scene.id) == original
    assert editor.toPlainText() == original


@pytest.mark.parametrize("change", ["buffer", "settings", "project", "brief", "cancel", "disk"])
def test_source_review_staleness_prevents_dispatch(planning, monkeypatch, application, change):
    window, project, scene, note, editor, brief = planning
    sent, reviews = [], []

    def review(dialog):
        reviews.append(True)
        if change == "buffer":
            editor.insertPlainText("author edit")
        elif change == "settings":
            window._settings_generation += 1
        elif change == "project":
            window._project_generation += 1
        elif change == "brief":
            brief.editor.insertPlainText("author brief edit")
        elif change == "cancel":
            window.cancel_project_setup()
        else:
            (project.root / note.path).write_text("Changed source", encoding="utf-8")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: (sent.append(True) or "Ideas"))
    window._suggest_project_brief(project, brief, brief.brief())
    wait(lambda: bool(reviews) and window._project_setup_worker is None, application)
    assert not sent
    assert len(tuple(project.iter_scenes())) == 1
    if change == "buffer":
        assert editor.toPlainText().endswith("author edit")


@pytest.mark.parametrize("change", ["buffer", "settings", "project", "cancel", "disk"])
@pytest.mark.parametrize("outcome", ["success", "failure"])
def test_stale_generation_or_late_error_keeps_manuscript_and_undo(planning, monkeypatch, application, change, outcome):
    window, project, scene, note, editor, brief = planning
    original = editor.toPlainText()
    editor.insertPlainText("author edit")
    entered, release = Event(), Event()
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda self: QDialog.DialogCode.Accepted)

    def generate(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        if outcome == "failure":
            raise RuntimeError("Late provider failure")
        return PLAN

    monkeypatch.setattr(window.provider, "generate_private", generate)
    window._start_project_autopilot(project, brief, brief.brief())
    wait(entered.is_set, application)
    if change == "buffer":
        editor.insertPlainText("more")
    elif change == "settings":
        window._settings_generation += 1
    elif change == "project":
        window._project_generation += 1
    elif change == "cancel":
        window.cancel_project_setup()
    else:
        (project.root / note.path).write_text("Changed source", encoding="utf-8")
    release.set()
    wait(lambda: window._project_setup_worker is None, application)
    assert len(tuple(project.iter_scenes())) == 1
    assert "Late provider failure" not in brief.status.text()
    editor.undo()
    assert editor.toPlainText() == original


@pytest.mark.parametrize("decision", ["reject", "disk", "buffer", "settings", "cancel"])
def test_outline_result_review_checks_sources_again_before_application(planning, monkeypatch, application, decision):
    window, project, scene, note, editor, brief = planning
    original = editor.toPlainText()
    reviewed = []
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda self: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: "# Proposed\n- Scene")

    def output_review(dialog):
        reviewed.append(True)
        if decision == "disk":
            (project.root / note.path).write_text("Changed during final review", encoding="utf-8")
        elif decision == "buffer":
            editor.insertPlainText("author edit")
        elif decision == "settings":
            window._settings_generation += 1
        elif decision == "cancel":
            window._project_setup_generation += 1
        return QDialog.DialogCode.Rejected if decision == "reject" else QDialog.DialogCode.Accepted

    monkeypatch.setattr(ProjectSetupDialog, "exec", output_review)
    window._start_project_outline_request(project, brief.brief(), use_retrieval=True)
    wait(lambda: bool(reviewed) and not window._project_busy, application)
    assert len(tuple(project.iter_scenes())) == 1
    assert project.read_scene(scene.id) == original
    if decision == "buffer":
        editor.undo()
        assert editor.toPlainText() == original


def test_no_explicit_window_refuses_before_source_capture(planning, monkeypatch):
    window, project, scene, note, editor, brief = planning
    window.settings.ollama_context_length = 0
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda *a: pytest.fail("Must refuse before review"))
    window._suggest_project_brief(project, brief, brief.brief())
    assert "explicit Ollama token window" in window.statusBar().currentMessage()
    assert window._project_setup_worker is None


def test_full_setup_stops_after_successful_autopilot_instead_of_generating_another_outline(planning, monkeypatch, application):
    window, project, scene, note, editor, brief = planning
    calls = []

    def outer_exec(dialog):
        dialog.autopilot_applied = True
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ProjectBriefDialog, "exec", outer_exec)
    monkeypatch.setattr(window, "_start_project_outline_request", lambda *a, **kw: calls.append(True))
    window.setup_project_with_ai()
    assert not calls


def test_rejecting_second_autopilot_source_review_applies_nothing(planning, monkeypatch, application):
    window, project, scene, note, editor, brief = planning
    reviews, sent = [], []

    def review(dialog):
        reviews.append(True)
        return QDialog.DialogCode.Accepted if len(reviews) == 1 else QDialog.DialogCode.Rejected

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: (sent.append(True) or PLAN))
    window._start_project_autopilot(project, brief, brief.brief())
    wait(lambda: len(reviews) == 2 and window._project_setup_worker is None, application)
    assert len(sent) == 1
    assert len(tuple(project.iter_scenes())) == 1 and len(project.manifest.notes) == 1
    assert not window._project_busy


def test_new_empty_project_without_index_can_plan_and_draft(planning, monkeypatch, application, tmp_path):
    from app.project import Project
    window, old_project, scene, note, editor, brief = planning
    project = Project.create(tmp_path / "new_project", "New project")
    window._project_opened(project)
    responses = iter([PLAN, "First scene.", "Second scene.", "Third scene."])
    reviews = []

    def review(dialog):
        reviews.append(dialog.context.toPlainText())
        assert '"retrieval_state":"no_hits"' in reviews[-1]
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: next(responses))
    window._start_project_autopilot(project, brief, brief.brief())
    wait(lambda: len(tuple(project.iter_scenes())) == 3 and not window._project_busy, application)
    assert len(reviews) == 4
    assert len(project.manifest.notes) == 1


def test_queued_old_result_cannot_reset_a_new_request_in_the_same_form(planning, monkeypatch, application):
    from PySide6.QtCore import QThreadPool
    from app.ui.workers import FunctionWorker
    window, project, scene, note, editor, brief = planning
    entered, release = Event(), Event()
    original = brief.brief()
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda self: QDialog.DialogCode.Accepted)

    def generate(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return "Old proposal"

    monkeypatch.setattr(window.provider, "generate_private", generate)
    window._suggest_project_brief(project, brief, original)
    wait(entered.is_set, application)
    release.set()
    assert QThreadPool.globalInstance().waitForDone(5000)
    # The old finished signal is queued, but a newer request now owns the form.
    window._project_setup_generation += 1
    replacement = FunctionWorker(lambda: None)
    window._project_setup_worker = replacement
    window._set_project_busy(True)
    brief.set_suggesting(True)
    application.processEvents()
    assert window._project_setup_worker is replacement and window._project_busy
    assert not brief.suggest_button.isEnabled()
    assert brief.brief() == original
