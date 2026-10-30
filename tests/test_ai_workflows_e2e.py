"""Offline Qt workflows using real workers and controlled fake AI responses."""

from threading import Event
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QInputDialog, QMessageBox

from app.ai.models import Suggestion
from app.project import Project, SceneCharacterAssociation
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow


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
        return "Check the key."

    monkeypatch.setattr(window.provider, "generate_private", analyze)
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    window.check_project_continuity()
    wait_until(lambda: bool(window._analysis_windows))
    assert "Mara opens the door" in prompts[0]
    assert "Find the key" in prompts[0]
    assert window._analysis_windows[-1].output.toPlainText() == "Check the key."
    assert project.read_scene(scene.id) == "Mara opens the door."
    window._analysis_windows[-1].close()
