"""Offline Qt workflows using real workers and controlled fake AI responses."""

import json
from threading import Event
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QInputDialog, QMessageBox

from app.ai.models import Suggestion
from app.project import Project, SceneCharacterAssociation
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.character_dialog import CharacterDialog


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: tmp_path / "settings.yaml"))
    AppSettings(ui_language="en", automatic_spellcheck=False).save(tmp_path / "settings.yaml")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    yield window
    for index in range(window.tabs.count()):
        window.tabs.widget(index).document_state.mark_saved()
    window.close()


def wait_until(predicate):
    if predicate():
        return
    loop = QEventLoop()
    poll = QTimer()
    poll.timeout.connect(lambda: loop.quit() if predicate() else None)
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poll.start(5)
    deadline.start(3000)
    loop.exec()
    poll.stop()
    assert predicate(), "Timed out waiting for AI workflow"


def test_completion_worker_requires_tab_and_discards_stale_response(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    started, release = Event(), Event()

    def complete(_context, _language, **_kwargs):
        started.set()
        assert release.wait(3)
        return " world"

    monkeypatch.setattr(window.provider, "complete", complete)
    window.request_completion()
    wait_until(started.is_set)
    release.set()
    wait_until(lambda: editor.has_completion)
    assert editor.toPlainText() == "Hello"
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText() == "Hello world"
    editor.undo()
    assert editor.toPlainText() == "Hello"

    started.clear()
    release.clear()
    window._completion_timer.stop()
    window.request_completion()
    wait_until(started.is_set)
    editor.insertPlainText("!")
    window._completion_timer.stop()
    release.set()
    wait_until(lambda: window._completion_worker is None)
    wait_until(lambda: any(item.name == "Text completion" and item.state == "discarded" for item in window.ai_activity.activities))
    assert not editor.has_completion
    assert editor.toPlainText() == "Hello!"


def test_spellcheck_worker_displays_suggestion_without_editing(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("teh cat")
    window._completion_timer.stop()
    monkeypatch.setattr(window.provider, "check_spelling", lambda text, language: [
        Suggestion(0, 3, "the", "spelling", "", "teh", 0, text)
    ])
    window.check_spelling()
    wait_until(lambda: bool(editor.spell_suggestions))
    assert editor.toPlainText() == "teh cat"
    assert editor.replace_spell_suggestion(editor.spell_suggestions[0])
    assert editor.toPlainText() == "the cat"
    editor.undo()
    assert editor.toPlainText() == "teh cat"


def test_spellcheck_worker_discards_results_after_edit(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("teh cat")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    started, release = Event(), Event()

    def check(text, _language):
        started.set()
        assert release.wait(3)
        return [Suggestion(0, 3, "the", "spelling", "", "teh", 0, text)]

    monkeypatch.setattr(window.provider, "check_spelling", check)
    try:
        window.check_spelling()
        wait_until(started.is_set)
        editor.insertPlainText("!")
        window._completion_timer.stop()
        release.set()
        wait_until(lambda: window._spellcheck_worker is None)
        wait_until(lambda: any(item.name == "Spellcheck" and item.state == "discarded" for item in window.ai_activity.activities))
        assert editor.toPlainText() == "teh cat!"
        assert not editor.spell_suggestions
    finally:
        release.set()


def test_completion_worker_error_keeps_document_editable(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()

    def fail(*_args, **_kwargs):
        raise RuntimeError("model unavailable")

    monkeypatch.setattr(window.provider, "complete", fail)
    window.request_completion()
    wait_until(lambda: window._completion_worker is None)
    assert "model unavailable" in window.status.currentMessage()
    editor.insertPlainText("!")
    assert editor.toPlainText() == "Hello!"


def test_activity_panel_cancels_completion_without_inserting_text(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Hello")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    started, release = Event(), Event()

    def complete(*_args, **_kwargs):
        started.set()
        assert release.wait(3)
        return " world"

    monkeypatch.setattr(window.provider, "complete", complete)
    window.request_completion()
    wait_until(started.is_set)
    item = next(item for item in reversed(window.ai_activity.activities) if item.name == "Text completion")
    window.ai_activity.list.setCurrentRow(window.ai_activity.activities.index(item))
    window.ai_activity.cancel_button.click()
    assert item.state == "cancelling"
    release.set()
    wait_until(lambda: item.state == "cancelled")
    assert editor.toPlainText() == "Hello"
    assert not editor.has_completion


def test_overlapping_generation_keeps_new_request_cancellable(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Start")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    first_started, second_started = Event(), Event()
    first_release, second_release = Event(), Event()

    def generate(prompt, **_kwargs):
        started, release = (first_started, first_release) if prompt == "first" else (second_started, second_release)
        started.set()
        assert release.wait(3)
        return " generated"

    monkeypatch.setattr(window.provider, "generate", generate)
    prompts = iter([("first", True), ("second", True)])
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *_args: next(prompts))
    monkeypatch.setattr("app.ui.main_window.GeneratedTextDialog.exec", lambda _dialog: QDialog.DialogCode.Accepted)
    try:
        window.generate_from_prompt()
        wait_until(first_started.is_set)
        first_worker = window._generate_worker
        window.generate_from_prompt()
        wait_until(second_started.is_set)
        first_release.set()
        wait_until(lambda: first_worker not in window._workers)
        assert window._generate_cancel_action.isEnabled()
        window.cancel_text_generation()
        second_release.set()
        wait_until(lambda: window._generate_worker is None)
        assert editor.toPlainText() == "Start"
    finally:
        first_release.set()
        second_release.set()


def test_generation_discarded_after_switching_tabs_resets_status(window, monkeypatch):
    started, release = Event(), Event()

    def generate(_prompt, **_kwargs):
        started.set()
        assert release.wait(3)
        return " generated"

    monkeypatch.setattr(window.provider, "generate", generate)
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *_args: ("write", True))
    try:
        window.generate_from_prompt()
        wait_until(started.is_set)
        first = window.tabs.current_editor()
        window.new_document()
        release.set()
        wait_until(lambda: window._generate_worker is None)
        assert first.toPlainText() == ""
        assert window.ai_status != "AI: Generating..."
    finally:
        release.set()


@pytest.mark.parametrize("decision, expected", [
    (QDialog.DialogCode.Accepted, "Start generated"),
    (QDialog.DialogCode.Rejected, "Start"),
])
def test_generation_worker_requires_review(window, monkeypatch, decision, expected):
    editor = window.tabs.current_editor()
    editor.setPlainText("Start")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    monkeypatch.setattr(window.provider, "generate", lambda _prompt, **_kwargs: " generated")
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *_args: ("write", True))
    monkeypatch.setattr("app.ui.main_window.GeneratedTextDialog.exec", lambda _dialog: decision)
    window.generate_from_prompt()
    wait_until(lambda: window._generate_worker is None)
    assert editor.toPlainText() == expected
    if decision == QDialog.DialogCode.Accepted:
        editor.undo()
        assert editor.toPlainText() == "Start"


def test_project_analysis_cancel_action_works_in_ukrainian(app, tmp_path, monkeypatch):
    settings_path = tmp_path / "uk.yaml"
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: settings_path))
    AppSettings(ui_language="uk").save(settings_path)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    try:
        window._set_project_analysis_active(True)
        assert window._project_analysis_cancel_action.isEnabled()
        window._set_project_analysis_active(False)
        assert not window._project_analysis_cancel_action.isEnabled()
    finally:
        translator = window._ui_translator
        window.close()
        if translator is not None:
            app.removeTranslator(translator)


def test_continuity_analysis_worker_reviews_selected_scene_and_character(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="Mara opens the door.")
    character = project.add_character("Mara")
    character.primary_motivation = "Find the key"
    project.update_character(character.id, character)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0)
    root = window.project_view.topLevelItem(0)
    scene_item = root.child(0).child(0)
    assert scene_item.data(0, Qt.ItemDataRole.UserRole + 1) == scene.id
    scene_item.setSelected(True)
    prompts = []

    def analyze(prompt, **_kwargs):
        prompts.append(prompt)
        return json.dumps({"findings": [{
            "confidence": "possible", "scene_id": scene.id,
            "character_ids": [character.id], "concern": "Check the key.",
            "evidence": {"source_id": scene.id, "quote": "Mara opens the door."},
            "suggestion": "Review the scene.",
        }]})

    monkeypatch.setattr(window.provider, "generate_private", analyze)
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    window.check_project_continuity()
    wait_until(lambda: bool(window._analysis_windows))
    assert "Mara opens the door" in prompts[0]
    assert "Find the key" in prompts[0]
    assert "Check the key." in window._analysis_windows[-1].output.toPlainText()
    assert project.read_scene(scene.id) == "Mara opens the door."
    window._analysis_windows[-1].close()


def test_scene_development_stages_only_selected_proposal(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "development", "Novel")
    scene = project.add_scene("Opening", content="Mara opens the door.")
    character = project.add_character("Mara")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: any(binding.item_id == scene.id for binding in window._project_documents.values()))
    dialog = CharacterDialog(character, parent=window)
    response = {"proposals": [
        {"field": "current_state", "value": "Curious", "evidence": "opens the door"},
        {"field": "lessons", "value": "Be cautious", "evidence": "Mara opens"},
    ]}
    monkeypatch.setattr(window.provider, "generate_private", lambda *_args, **_kwargs: json.dumps(response))
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QInputDialog, "getItem", lambda _parent, _title, _label, choices, *_args: (choices[0], True))

    def review(dialog_box):
        checkboxes = dialog_box.findChildren(QCheckBox)
        assert len(checkboxes) == 2
        checkboxes[0].setChecked(True)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(QDialog, "exec", review)
    window._suggest_scene_development(dialog, project)
    wait_until(lambda: dialog.development_button.isEnabled())
    assert dialog.arc.toPlainText() == "current_state: Curious"
    assert project.get_character(character.id).arc == {}
    dialog._accept()
    project.update_character_with_relationships(character.id, dialog.character, dialog.relationships)
    assert Project.open(project.root).get_character(character.id).arc == {"current_state": "Curious"}


def test_scene_development_discards_result_when_scene_changes(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "stale-development", "Novel")
    scene = project.add_scene("Opening", content="Mara opens the door.")
    character = project.add_character("Mara")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: any(binding.item_id == scene.id for binding in window._project_documents.values()))
    editor = next(editor for editor, binding in window._project_documents.items() if binding.item_id == scene.id)
    dialog = CharacterDialog(character, parent=window)
    started, release = Event(), Event()

    def generate(*_args, **_kwargs):
        started.set()
        assert release.wait(3)
        return json.dumps({"proposals": [{"field": "current_state", "value": "Curious", "evidence": "opens the door"}]})

    notices = []
    monkeypatch.setattr(window.provider, "generate_private", generate)
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *_args: notices.append(_args))
    monkeypatch.setattr(QInputDialog, "getItem", lambda _parent, _title, _label, choices, *_args: (choices[0], True))
    window._suggest_scene_development(dialog, project)
    wait_until(started.is_set)
    editor.insertPlainText("Changed ")
    release.set()
    wait_until(lambda: bool(notices))
    assert not dialog.arc.toPlainText()
    assert project.get_character(character.id).arc == {}
    dialog.reject()


def test_portrait_load_is_staged_and_cancel_preserves_profile(window, tmp_path):
    project = Project.create(tmp_path / "portrait-project", "Novel")
    character = project.add_character("Mara")
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0xff884422)
    path = tmp_path / "portrait.png"
    assert image.save(str(path))
    dialog = CharacterDialog(character, parent=window)
    window._load_character_portrait(dialog, path=str(path))
    assert not dialog.save_button.isEnabled()
    wait_until(lambda: dialog.save_button.isEnabled())
    assert dialog.character.portrait
    assert not project.get_character(character.id).portrait
    dialog.reject()
    assert not Project.open(project.root).get_character(character.id).portrait


def test_portrait_can_be_saved_then_removed(window, tmp_path):
    project = Project.create(tmp_path / "portrait-save", "Novel")
    character = project.add_character("Mara")
    image = QImage(8, 8, QImage.Format.Format_RGB32)
    image.fill(0xff884422)
    path = tmp_path / "portrait.png"
    assert image.save(str(path))
    dialog = CharacterDialog(character, parent=window)
    window._load_character_portrait(dialog, path=str(path))
    wait_until(lambda: dialog.save_button.isEnabled())
    dialog._accept()
    project.update_character_with_relationships(character.id, dialog.character, dialog.relationships)
    saved = Project.open(project.root).get_character(character.id)
    assert saved.portrait
    dialog = CharacterDialog(saved, parent=window)
    dialog._remove_portrait()
    dialog._accept()
    project.update_character_with_relationships(character.id, dialog.character, dialog.relationships)
    assert not Project.open(project.root).get_character(character.id).portrait


def test_removing_portrait_discards_late_load(window, monkeypatch):
    from app.project.model import Character
    from uuid import uuid4

    dialog = CharacterDialog(Character(str(uuid4()), "Mara"), parent=window)
    started, release = Event(), Event()

    def delayed(**_kwargs):
        started.set()
        assert release.wait(3)
        return "late image", QImage(1, 1, QImage.Format.Format_RGB32)

    monkeypatch.setattr("app.ui.main_window.load_portrait", delayed)
    window._load_character_portrait(dialog, path="unused")
    wait_until(started.is_set)
    dialog._remove_portrait()
    release.set()
    wait_until(lambda: dialog.save_button.isEnabled())
    assert dialog.character.portrait == ""
    dialog.reject()
