import os
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from app.document.revisions import RevisionComparison, RevisionStore, SceneChange
from app.project import Project
from app.document.export import ExportChapter, ExportScene
from app.ui.main_window import MainWindow
from app.ui.project_view import ProjectView
from app.ui.revision_history_dialog import RevisionHistoryDialog
from app.ui.settings_dialog import SettingsDialog
from app.settings.settings import AppSettings


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: tmp_path / "settings.yaml"),
    )


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


def test_repeated_project_document_open_coalesces_pending_reads(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    read_started = Event()
    release_read = Event()
    read_calls = []
    original_read = project.read_scene

    def delayed_read(scene_id):
        read_calls.append(scene_id)
        read_started.set()
        if not release_read.wait(3):
            raise TimeoutError("Test did not release the project scene read.")
        return original_read(scene_id)

    monkeypatch.setattr(project, "read_scene", delayed_read)
    try:
        window._open_project_document("scene", scene.id)
        assert read_started.wait(2)
        window._open_project_document("scene", scene.id)
        assert read_calls == [scene.id]

        release_read.set()
        wait_until(lambda: window.tabs.count() == 2, application)

        path = project.root / scene.path
        window._project_document_opened(
            project, "scene", scene.id, path, "original"
        )
        window._open_project_document("scene", scene.id)
        assert window.tabs.count() == 2
        assert read_calls == [scene.id]
        assert sum(
            binding.item_id == scene.id
            for binding in window._project_documents.values()
        ) == 1
    finally:
        release_read.set()
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


def test_settings_connection_test_runs_and_reports_result(application, monkeypatch):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
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


def test_recent_projects_menu_tracks_successful_opens_and_routes_selection(
    application, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
    older = Project.create(tmp_path / "older-project", "Older")
    recent = Project.create(tmp_path / "recent-project", "Recent")
    window = MainWindow()
    window._project_opened(older)
    window._project_opened(recent)

    assert window.settings.recent_projects == [str(recent.root), str(older.root)]
    recent_menu = window._recent_projects_menu
    window._populate_recent_projects_menu()
    selected = next(
        action for action in recent_menu.actions()
        if action.data() == str(older.root)
    )
    assert "older-project" in selected.text()

    opened = []
    monkeypatch.setattr(
        window,
        "_open_project_worker",
        lambda operation, *args: opened.append((operation, args)),
    )
    selected.trigger()
    assert opened == [(Project.open, (str(older.root),))]

    clear_action = next(
        action for action in recent_menu.actions()
        if action.text() == "Clear Recent Projects"
    )
    clear_action.trigger()
    assert window.settings.recent_projects == []
    assert recent_menu.actions()[0].text() == "No Recent Projects"
    window.close()


def test_selected_scene_export_does_not_read_unselected_scene(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    included = project.add_scene("Included", chapter_id=chapter.id, content="Export this.")
    excluded = project.add_scene("Excluded", chapter_id=chapter.id, content="Unavailable.")
    (project.root / project.get_scene(excluded.id).path).unlink()

    output = MainWindow._export_project_snapshot(
        project,
        [ExportChapter("Chapter One", (
            ExportScene(included.id, "Included"),
            ExportScene(excluded.id, "Excluded"),
        ))],
        [],
        {},
        tmp_path / "selected.md",
        "markdown",
        False,
        {included.id},
        True,
        True,
        "\n\n",
    )

    assert output.read_text(encoding="utf-8") == (
        "# Chapter One\n\n## Included\n\nExport this."
    )


def test_revision_history_dialog_loads_and_compares_snapshots(
    application, tmp_path
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene_id = project.add_scene("Opening", content="First draft.").id
    store = RevisionStore(project.root / ".utexteditor" / "revisions")
    before = store.create(
        "Before",
        structure={},
        scene_order=[scene_id],
        scene_titles={scene_id: "Opening"},
        documents={scene_id: "First draft.\n"},
    )
    store.create(
        "After",
        structure={},
        scene_order=[scene_id],
        scene_titles={scene_id: "Opening"},
        documents={scene_id: "Second draft.\n"},
    )
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)

    window.review_revision_snapshots()
    wait_until(
        lambda: window._revision_history_dialog is not None
        and window._revision_history_dialog.snapshots.count() == 2,
        application,
    )
    dialog = window._revision_history_dialog
    assert dialog is not None
    dialog.snapshots.item(0).setSelected(True)
    dialog.snapshots.item(1).setSelected(True)
    dialog.compare_button.click()
    wait_until(
        lambda: "Second draft." in dialog.details.toPlainText(),
        application,
    )

    assert "Text Changed: Opening" in dialog.details.toPlainText()
    assert "-First draft." in dialog.details.toPlainText()
    assert "+Second draft." in dialog.details.toPlainText()
    dialog.snapshots.clearSelection()
    dialog.show_error("Comparison failed.")
    assert not dialog.compare_button.isEnabled()
    dialog.close()
    window.close()


def test_revision_history_dialog_labels_reference_note_changes(application):
    dialog = RevisionHistoryDialog()

    dialog.show_comparison(RevisionComparison((
        SceneChange(
            "character-id",
            "type-changed",
            old_title="Mira",
            new_title="Mira",
            item_type="note",
            old_note_type="character",
            new_note_type="research",
        ),
    )))

    assert "Reference Note Type Changed: Mira" in dialog.details.toPlainText()
    assert "Type: character → research" in dialog.details.toPlainText()
    assert "1 project item change" in dialog.status.text()
    dialog.close()


def test_project_translation_actions_translate_and_refresh_open_documents(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene(
        "Opening", chapter_id=chapter.id, content="Original scene."
    )
    note = project.add_note("Character", "character", content="Original note.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.settings.autosave_enabled = False
    confirmation_text = []

    def confirm_translation(_parent, _title, text, *_args, **_kwargs):
        confirmation_text.append(text)
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(
        QMessageBox,
        "question",
        confirm_translation,
    )
    prompts = []

    def translate(prompt, **_options):
        prompts.append(prompt)
        return f"Translated {len(prompts)}"

    monkeypatch.setattr(window.provider, "generate_private", translate)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("Unsaved scene text.")

    project_menu = next(
        action.menu()
        for action in window.menuBar().actions()
        if action.text() == "Project"
    )
    menu_actions = {action.text() for action in project_menu.actions()}
    assert "Translate Project to Ukrainian…" in menu_actions
    assert "Translate Project to English…" in menu_actions

    window.translate_project_to_ukrainian()
    assert confirmation_text and window.provider.host in confirmation_text[0]
    wait_until(
        lambda: not window._project_busy
        and window.project is not None
        and window.project.manifest.title == "Translated 1",
        application,
    )

    assert window.project is not None
    assert window.project.manifest.chapters[0].title == "Translated 2"
    assert window.project.get_scene(scene.id).title == "Translated 3"
    assert window.project.get_note(note.id).title == "Translated 4"
    assert window.project.read_scene(scene.id) == "Translated 5"
    assert window.project.read_note(note.id) == "Translated 6"
    assert editor.toPlainText() == "Translated 5"
    assert not editor.document_state.dirty
    assert any("Unsaved scene text." in prompt for prompt in prompts)
    editor.document_state.mark_saved()
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


def test_compile_book_uses_unsaved_scene_buffer_without_changing_project(
    application, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "app.ui.main_window.OllamaClient.check_connection", lambda _self: True
    )
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene("Opening", chapter_id=chapter.id, content="saved text")
    target = tmp_path / "compiled-book.pdf"
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(target), "PDF book (*.pdf)"),
    )
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    compile_errors = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *_args: compile_errors.append(_args[-1]),
    )
    window = MainWindow()
    # PDF compilation is independent of AI; keep the test offline and avoid
    # scheduling completion/spellcheck workers while editing the fixture.
    window.settings.ai_enabled = False
    window._project_opened(project)
    assert window._project_actions["Compile Book as PDF…"].isEnabled()
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    window.settings.autosave_enabled = False
    editor = window.tabs.current_editor()
    assert editor is not None
    editor.setPlainText("current unsaved text")

    window.compile_project_book()
    wait_until(
        lambda: (
            "Book PDF compiled" in window.statusBar().currentMessage()
            or bool(compile_errors)
        ),
        application,
    )
    assert not compile_errors, compile_errors

    pdf = QPdfDocument(application)
    pdf.load(str(target))
    content = "\n".join(
        pdf.getAllText(index).text() for index in range(pdf.pageCount())
    )
    assert "current unsaved text" in content
    assert "\r\nsaved text\r\n" not in content
    assert project.read_scene(scene.id) == "saved text"
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
