"""Worker/GUI review boundaries and explicit profile staging for RAG-10."""

import json
from threading import Event, get_ident

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox, QInputDialog, QCheckBox, QLabel

from app.project import SceneCharacterAssociation
from app.ui.character_dialog import CharacterDialog
from app.ui.generated_text_dialog import GeneratedTextDialog
from app.ui.rag_completion import RAGCompletionDialog
from tests.test_inline_retrieval_ui import wait
from tests.test_rag_completion_ui import application, scene_window


@pytest.fixture
def character_window(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    character = project.add_character("Mara")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    window.settings.completion_enabled = False
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kw: True)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    dialog = CharacterDialog(character)
    dialog.retrieval.setChecked(True)
    yield window, project, scene, note, editor, dialog
    dialog.reject()


def select_scene(window, scene):
    window.project_view.clearSelection()
    def visit(item):
        if item.data(0, Qt.ItemDataRole.UserRole + 1) == scene.id:
            item.setSelected(True)
        for index in range(item.childCount()):
            visit(item.child(index))
    for index in range(window.project_view.topLevelItemCount()):
        visit(window.project_view.topLevelItem(index))


@pytest.mark.parametrize("mode", ["summary", "continuity", "profile", "development"])
def test_each_workflow_reviews_exact_prompt_offthread_and_keeps_explicit_staging(character_window, monkeypatch, application, mode):
    window, project, scene, note, editor, dialog = character_window
    gui = get_ident()
    reviews, sent, final = [], [], []
    original = editor.toPlainText()
    def review(preview):
        assert get_ident() == gui
        assert any(window.provider.host in label.text() for label in preview.findChildren(QLabel))
        reviews.append(preview.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0])
        return QDialog.DialogCode.Accepted
    def generate(prompt, **options):
        assert get_ident() != gui
        sent.append((prompt, options))
        if mode == "profile":
            return '{"primary_motivation":"Find the key"}'
        if mode == "development":
            return json.dumps({"proposals":[{"field":"current_state", "value":"Curious", "evidence":"hidden door"}]})
        return '{"findings":[]}' if mode == "continuity" else "A door scene"
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", generate)
    def final_review(preview):
        final.append(True)
        return QDialog.DialogCode.Rejected
    monkeypatch.setattr(GeneratedTextDialog, "exec", final_review)
    original_exec = QDialog.exec
    def dialog_exec(preview):
        if preview.windowTitle() == "Review character development":
            final.append(True)
            assert all(not checkbox.isChecked() for checkbox in preview.findChildren(QCheckBox))
            return QDialog.DialogCode.Rejected
        return original_exec(preview)
    monkeypatch.setattr(QDialog, "exec", dialog_exec)
    if mode in {"summary", "continuity"}:
        select_scene(window, scene)
        window._analysis_retrieval_action.setChecked(True)
        window._start_project_analysis(mode)
        wait(lambda: bool(window._analysis_windows), application)
        assert "contextual" in window._analysis_windows[-1].output.toPlainText().lower()
        for output in tuple(window._analysis_windows):
            output.reject()
    elif mode == "profile":
        window._suggest_character_profile(dialog, project)
        wait(lambda: bool(final), application)
    else:
        window._suggest_scene_development(dialog, project)
        wait(lambda: bool(final), application)
    assert sent[0][0] == reviews[0] and sent[0][1]["require_full_context"]
    assert project.get_character(dialog.character.id).primary_motivation == ""
    assert dialog.motivation.toPlainText() == ""
    assert editor.toPlainText() == original == project.read_scene(scene.id)


@pytest.mark.parametrize("mode", ["profile", "development"])
@pytest.mark.parametrize("change", ["profile", "buffer", "settings", "project", "reject", "disk"])
def test_source_review_changes_prevent_character_dispatch(character_window, monkeypatch, application, mode, change):
    window, project, scene, note, editor, dialog = character_window
    reviewed, sent = [], []
    def review(preview):
        reviewed.append(True)
        if change == "profile":
            dialog.motivation.setPlainText("Author edit")
        elif change == "buffer":
            editor.insertPlainText("author scene edit")
        elif change == "settings":
            window._settings_generation += 1
        elif change == "project":
            window._project_generation += 1
        elif change == "disk":
            (project.root / note.path).write_text("Changed note", encoding="utf-8")
        else:
            return QDialog.DialogCode.Rejected
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: (sent.append(True) or '{}'))
    if mode == "profile":
        window._suggest_character_profile(dialog, project)
    else:
        window._suggest_scene_development(dialog, project)
    wait(lambda: bool(reviewed), application)
    window.thread_pool.waitForDone(3000)
    application.processEvents()
    assert not sent
    assert (dialog.ai_button if mode == "profile" else dialog.development_button).isEnabled()
    assert project.get_character(dialog.character.id).primary_motivation == ""


@pytest.mark.parametrize("mode", ["profile", "development"])
@pytest.mark.parametrize("failure", [False, True])
def test_profile_edit_during_request_discards_success_and_late_failure(character_window, monkeypatch, application, mode, failure):
    window, project, scene, note, editor, dialog = character_window
    started, release = Event(), Event()
    warnings, finals = [], []
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(GeneratedTextDialog, "exec", lambda _: (finals.append(True) or QDialog.DialogCode.Accepted))
    def generate(*args, **options):
        started.set()
        release.wait(5)
        if failure:
            raise RuntimeError("obsolete failure")
        return '{"primary_motivation":"Generated"}' if mode == "profile" else '{"proposals":[]}'
    monkeypatch.setattr(window.provider, "generate_private", generate)
    if mode == "profile":
        window._suggest_character_profile(dialog, project)
    else:
        window._suggest_scene_development(dialog, project)
    try:
        wait(started.is_set, application)
        dialog.motivation.setPlainText("Author edit")
    finally:
        release.set()
    window.thread_pool.waitForDone(3000)
    application.processEvents()
    assert not finals and not warnings
    assert dialog.motivation.toPlainText() == "Author edit"
    assert project.get_character(dialog.character.id).primary_motivation == ""


@pytest.mark.parametrize("mode", ["profile", "development"])
def test_disk_change_in_final_review_prevents_profile_staging(character_window, monkeypatch, application, mode):
    window, project, scene, note, editor, dialog = character_window
    final = []
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    answer = '{"primary_motivation":"Generated"}' if mode == "profile" else json.dumps(
        {"proposals":[{"field":"current_state","value":"Curious","evidence":"hidden door"}]})
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **options: answer)
    def review(preview):
        final.append(True)
        (project.root / note.path).write_text("Changed after model", encoding="utf-8")
        for checkbox in preview.findChildren(QCheckBox):
            checkbox.setChecked(True)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(GeneratedTextDialog, "exec", review)
    original_exec = QDialog.exec
    monkeypatch.setattr(QDialog, "exec", lambda preview: review(preview) if preview.windowTitle() == "Review character development" else original_exec(preview))
    if mode == "profile":
        window._suggest_character_profile(dialog, project)
    else:
        window._suggest_scene_development(dialog, project)
    wait(lambda: bool(final), application)
    window.thread_pool.waitForDone(3000)
    application.processEvents()
    assert dialog.motivation.toPlainText() == ""
    assert "Curious" not in dialog.profile_fields()["arc"]


@pytest.mark.parametrize("mode", ["summary", "profile", "development"])
def test_explicit_window_required_before_dispatch(character_window, monkeypatch, mode):
    window, project, scene, note, editor, dialog = character_window
    window.settings.ollama_context_length = 0
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: pytest.fail("No review expected"))
    if mode == "summary":
        window._analysis_retrieval_action.setChecked(True)
        window._start_project_analysis(mode)
    elif mode == "profile":
        window._suggest_character_profile(dialog, project)
    else:
        window._suggest_scene_development(dialog, project)
    assert "explicit Ollama token window" in window.statusBar().currentMessage()


@pytest.mark.parametrize("mode", ["profile", "development"])
def test_accepted_values_are_staged_only_after_verification(character_window, monkeypatch, application, mode):
    window, project, scene, note, editor, dialog = character_window
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    answer = '{"primary_motivation":"Generated"}' if mode == "profile" else json.dumps(
        {"proposals":[{"field":"current_state","value":"Curious","evidence":"hidden door"}]})
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **options: answer)
    monkeypatch.setattr(GeneratedTextDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    original_exec = QDialog.exec
    def review(preview):
        if preview.windowTitle() != "Review character development":
            return original_exec(preview)
        assert "Curious" not in dialog.profile_fields()["arc"]
        for checkbox in preview.findChildren(QCheckBox):
            checkbox.setChecked(True)
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(QDialog, "exec", review)
    if mode == "profile":
        window._suggest_character_profile(dialog, project)
        wait(lambda: dialog.motivation.toPlainText() == "Generated", application)
    else:
        window._suggest_scene_development(dialog, project)
        wait(lambda: "Curious" in dialog.profile_fields()["arc"], application)
    assert project.get_character(dialog.character.id).primary_motivation == ""
    assert project.get_character(dialog.character.id).arc == {}


@pytest.mark.parametrize("change", ["buffer", "selection", "settings", "project", "reject"])
def test_analysis_source_review_stale_state_prevents_dispatch(character_window, monkeypatch, application, change):
    window, project, scene, note, editor, dialog = character_window
    reviewed, sent = [], []
    select_scene(window, scene)
    window._analysis_retrieval_action.setChecked(True)
    def review(preview):
        reviewed.append(True)
        if change == "buffer":
            editor.insertPlainText("author scene edit")
        elif change == "selection":
            window.project_view.clearSelection()
        elif change == "settings":
            window._settings_generation += 1
        elif change == "project":
            window._project_generation += 1
        else:
            return QDialog.DialogCode.Rejected
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: (sent.append(True) or 'Summary'))
    window._start_project_analysis("summary")
    wait(lambda: bool(reviewed), application)
    window.thread_pool.waitForDone(3000)
    application.processEvents()
    assert not sent and not window._analysis_windows
