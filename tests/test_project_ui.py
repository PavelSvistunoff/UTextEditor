import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.project import Project
from app.ui.main_window import MainWindow
from app.ui.project_view import ProjectView
from app.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def wait_until(predicate, application):
    if predicate():
        return
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)

    def check():
        if predicate():
            loop.quit()

    application.aboutToQuit.connect(loop.quit)
    timer.start(3000)
    while not predicate() and timer.isActive():
        QTimer.singleShot(10, check)
        loop.exec()
    assert predicate()


def test_project_tree_counts_and_project_scene_save_are_integrated(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene("Opening", chapter_id=chapter.id, content="hello world")
    project.add_note("Character", "character", content="not manuscript")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)

    root = window.project_view.topLevelItem(0)
    assert "2 words" in root.text(0)
    assert root.childCount() == 2
    chapter_item = root.child(0)
    assert "2 words" in chapter_item.text(0)
    scene_item = chapter_item.child(0)
    assert scene_item.data(0, Qt.ItemDataRole.UserRole + 1) == scene.id

    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    assert editor.toPlainText() == "hello world"
    editor.setPlainText("edited manuscript")
    result: list[bool] = []
    window._save_editor(editor, callback=result.append)
    wait_until(lambda: result, application)

    assert result == [True]
    assert project.read_scene(scene.id) == "edited manuscript"
    assert not editor.document_state.dirty
    window.close()


def test_project_tree_context_actions_route_to_selected_scene(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="A beginning.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(
        lambda: window.project_view is not None
        and window.project_view.topLevelItemCount() > 0,
        application,
    )

    item = window.project_view.topLevelItem(0).child(0).child(0)
    window.project_view.setCurrentItem(item)
    actions = dict(ProjectView.context_actions("scene"))
    assert "move_to_chapter" in actions.values()
    assert "summarize" in actions.values()
    called = []
    monkeypatch.setattr(
        window,
        "rename_project_item",
        lambda: called.append(window._selected_project_item()),
    )
    window.project_view.context_action_requested.emit("rename", "scene", scene.id)

    assert called == [("scene", scene.id)]
    window.close()


def test_settings_connection_test_runs_and_reports_result(application):
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    dialog = SettingsDialog(window.settings, window)

    window._test_settings_connection(
        dialog, "http://localhost:11434", "gemma4:12b"
    )
    wait_until(
        lambda: "Connected" in dialog.connection_status.text(),
        application,
    )

    assert "gemma4:12b" in dialog.connection_status.text()
    dialog.close()
    window.close()


def test_project_open_failure_keeps_previous_project_and_documents(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "working", "Working")
    bad_project = tmp_path / "bad"
    bad_project.mkdir()
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    original_editor = window.tabs.current_editor()
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: QMessageBox.StandardButton.Ok)

    window._open_project_worker(Project.open, bad_project)
    wait_until(lambda: not window._project_busy, application)

    assert window.project is project
    assert window.tabs.current_editor() is original_editor
    window.close()


def test_project_scene_autosaves_after_idle_and_can_be_disabled(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    window.settings.autosave_idle_ms = 250
    editor.setPlainText("autosaved words")

    timer = window._autosave_timers[editor]
    assert timer.isActive()
    assert timer.interval() == 250
    timer.timeout.emit()
    wait_until(
        lambda: project.read_scene(scene.id) == "autosaved words" and not editor.document_state.dirty,
        application,
    )

    window.settings.autosave_enabled = False
    editor.setPlainText("manual save required")
    assert not timer.isActive()
    window._autosave_project_document(editor)
    assert editor.document_state.dirty
    assert project.read_scene(scene.id) == "autosaved words"
    editor.document_state.mark_saved()
    window.close()


def test_project_scene_save_preserves_crlf_line_endings(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="first\nsecond\n")
    target = project.root / scene.path
    target.write_bytes(b"first\r\nsecond\r\n")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    assert editor.toPlainText() == "first\nsecond\n"
    assert editor.document_state.line_ending == "CRLF"
    editor.setPlainText("first\nchanged\n")
    result: list[bool] = []
    window._save_editor(editor, callback=result.append)
    wait_until(lambda: result, application)

    assert result == [True]
    assert target.read_bytes() == b"first\r\nchanged\r\n"
    editor.document_state.mark_saved()
    window.close()


def test_project_analysis_uses_only_explicit_scene_and_reference_context(tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="scene text")
    selected = project.add_note("Selected", "character", content="selected reference")
    other = project.add_note("Not selected", "research", content="private unrelated note")

    class FakeProvider:
        prompt = None

        def generate_private(self, prompt, **_options):
            self.prompt = prompt
            return ""

    provider = FakeProvider()
    result = MainWindow._run_project_analysis(
        provider,
        project,
        "continuity",
        scene.id,
        (selected.id,),
        {},
        2000,
        "review only",
        100,
        0.2,
    )

    assert result == ""
    assert "scene text" in provider.prompt
    assert "selected reference" in provider.prompt
    assert "private unrelated note" not in provider.prompt
    assert other.id not in provider.prompt


def test_scene_summary_requires_confirmation_and_never_modifies_source(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="original manuscript")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    scene_item = window.project_view.topLevelItem(0).child(0).child(0)
    window.project_view.setCurrentItem(scene_item)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args: QMessageBox.StandardButton.Yes,
    )
    received: list[str] = []
    monkeypatch.setattr(
        window.provider,
        "generate_private",
        lambda prompt, **_options: (received.append(prompt) or "A review summary."),
    )

    window.summarize_project_scene()
    wait_until(lambda: bool(window._analysis_windows), application)

    assert received and "original manuscript" in received[0]
    assert window._analysis_windows[0].output.toPlainText() == "A review summary."
    assert project.read_scene(scene.id) == "original manuscript"
    window.close()
