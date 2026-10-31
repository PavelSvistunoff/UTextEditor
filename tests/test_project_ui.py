import os
from pathlib import Path
from threading import Event
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QMessageBox, QInputDialog

from app.document.revisions import RevisionComparison, RevisionStore, SceneChange
from app.document.recovery import RecoveryComparisonLabels, RecoveryStore
from app.document.file_manager import FileManager, ExternalChangeError
from app.project import Project, ProjectError, WordCount
from app.document.export import ExportChapter, ExportScene
from app.ui.main_window import MainWindow
from app.ui.project_view import ProjectView
from app.ui.character_dialog import CharacterDialog
from app.ui.character_relationship_dialog import CharacterRelationshipDialog
from app.ui.revision_history_dialog import RevisionHistoryDialog
from app.ui.settings_dialog import SettingsDialog
from app.settings.settings import AppSettings


def test_recovery_comparison_formats_localized_errors_and_empty_results(tmp_path):
    store = RecoveryStore(tmp_path / "recovery")
    path = tmp_path / "invalid.txt"
    path.write_text("initial", encoding="utf-8")
    entry = store.save("doc", "draft", canonical_path=path)
    path.write_bytes(b"\xff")
    args = (RecoveryComparisonLabels(), "Без назви", "Помилка: {error}", "Немає копій")
    result = MainWindow._compare_recovery_entries((entry,), *args)
    assert str(path) in result and "Помилка:" in result
    assert MainWindow._compare_recovery_entries((), *args) == "Немає копій"


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.yaml"
    monkeypatch.setattr(
        AppSettings,
        "_default_settings_path",
        staticmethod(lambda: settings_path),
    )
    AppSettings(ui_language="en", ai_context_consent_host="http://localhost:11434").save(settings_path)


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


def test_recovery_can_restore_one_selected_older_snapshot(application, tmp_path, monkeypatch):
    store = RecoveryStore(tmp_path / "recovery")
    old = store.save("doc", "older draft")
    store.save("doc", "newer draft")
    store.save("another", "other draft")
    scan = store.scan()
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.recovery_store = store
    restored = []
    monkeypatch.setattr(window, "_recovery_restore_finished", restored.extend)
    monkeypatch.setattr(QInputDialog, "getItem", lambda _parent, _title, _prompt, labels, *_args:
                        (next(label for label in labels if old.snapshot_id in label), True))
    dialog = QMessageBox(window)
    window._handle_recovery_choice("select", scan, dialog)
    wait_until(lambda: bool(restored), application)
    assert len(restored) == 1
    assert restored[0][0].snapshot_id == old.snapshot_id
    assert restored[0][1].text == "older draft" and restored[0][1].dirty
    assert len(store.scan().entries) == 3
    window.recovery_store = None
    window.close()


def test_standalone_repeated_saves_update_disk_fingerprint_and_detect_external_edits(application, tmp_path, monkeypatch):
    path = tmp_path / "draft.txt"
    path.write_text("base", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._opened_document(FileManager().open(path))
    editor = window.tabs.current_editor()
    results = []
    editor.setPlainText("first save")
    window._save_editor(editor, callback=results.append)
    wait_until(lambda: len(results) == 1, application)
    editor.setPlainText("second save")
    window._save_editor(editor, callback=results.append)
    wait_until(lambda: len(results) == 2, application)
    assert results == [True, True]
    assert path.read_text(encoding="utf-8") == "second save"

    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    path.write_text("external edit", encoding="utf-8")
    editor.setPlainText("unsaved edit")
    window._save_editor(editor, callback=results.append)
    wait_until(lambda: len(results) == 3, application)
    assert results[-1] is False and warnings
    assert path.read_text(encoding="utf-8") == "external edit"
    assert editor.toPlainText() == "unsaved edit" and editor.document_state.dirty
    editor.document_state.mark_saved()
    window.close()


def test_save_as_tracks_new_destination_for_later_conflicts(application, tmp_path, monkeypatch):
    source = tmp_path / "source.txt"
    destination = tmp_path / "copy.txt"
    source.write_text("source", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._opened_document(FileManager().open(source))
    editor = window.tabs.current_editor()
    editor.setPlainText("my copy")
    results = []
    window._save_editor(editor, callback=results.append, target=destination)
    wait_until(lambda: results, application)
    assert results == [True]
    destination.write_text("external copy", encoding="utf-8")
    editor.setPlainText("my next edit")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    window._save_editor(editor, callback=results.append)
    wait_until(lambda: len(results) == 2, application)
    assert results == [True, False]
    assert destination.read_text(encoding="utf-8") == "external copy"
    assert source.read_text(encoding="utf-8") == "source"
    assert editor.toPlainText() == "my next edit" and editor.document_state.dirty
    editor.document_state.mark_saved()
    window.close()


@pytest.mark.parametrize("kind", ["standalone", "scene"])
def test_conflict_review_stages_merge_and_rechecks_disk_on_save(application, tmp_path, monkeypatch, kind):
    from PySide6.QtWidgets import QDialog
    if kind == "scene":
        project = Project.create(tmp_path / "novel", "Novel")
        scene = project.add_scene("Scene", content="one\ntwo\nthree\n")
        path = project.root / scene.path
    else:
        path = tmp_path / "draft.txt"
        path.write_text("one\ntwo\nthree\n", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    if kind == "scene":
        window._project_opened(project)
        window._open_project_document("scene", scene.id)
        wait_until(lambda: window.tabs.count() == 2, application)
    else:
        window._opened_document(FileManager().open(path))
    editor = window.tabs.current_editor()
    editor.setPlainText("ONE\ntwo\nthree\n")
    path.write_text("one\ntwo\nTHREE\n", encoding="utf-8")
    shown = []

    class Review:
        def __init__(self, base, disk, buffer, proposal, conflicts, parent):
            assert (base, disk, buffer, conflicts) == ("one\ntwo\nthree\n", "one\ntwo\nTHREE\n", "ONE\ntwo\nthree\n", 0)
            self.choice = "merge"
            self.merge = type("Merge", (), {"toPlainText": lambda self: proposal})()
            shown.append(True)

        def exec(self):
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.ConflictDialog", Review)
    window.review_external_changes()
    wait_until(lambda: editor.toPlainText() == "ONE\ntwo\nTHREE\n", application)
    assert shown and editor.document_state.dirty
    assert path.read_text(encoding="utf-8") == "one\ntwo\nTHREE\n"
    path.write_text("another external change", encoding="utf-8")
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    result = []
    window._save_editor(editor, callback=result.append)
    wait_until(lambda: result, application)
    assert result == [False]
    assert path.read_text(encoding="utf-8") == "another external change"
    assert editor.toPlainText() == "ONE\ntwo\nTHREE\n"
    editor.document_state.mark_saved()
    window.close()


def test_conflict_review_rejects_disk_change_during_review(application, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QDialog
    path = tmp_path / "draft.txt"
    path.write_text("base", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._opened_document(FileManager().open(path))
    editor = window.tabs.current_editor()
    editor.setPlainText("buffer")
    path.write_text("disk", encoding="utf-8")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    class Review:
        def __init__(self, *args):
            self.choice = "reload"
        def exec(self):
            path.write_text("changed again", encoding="utf-8")
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.ConflictDialog", Review)
    window.review_external_changes()
    wait_until(lambda: warnings, application)
    assert editor.toPlainText() == "buffer" and editor.document_state.dirty
    assert path.read_text(encoding="utf-8") == "changed again"
    editor.document_state.mark_saved()
    window.close()


@pytest.mark.parametrize("choice", ["cancel", "reload", "stale"])
def test_conflict_review_cancel_reload_and_stale_buffer(application, tmp_path, monkeypatch, choice):
    from PySide6.QtWidgets import QDialog
    path = tmp_path / "draft.txt"
    path.write_text("base", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._opened_document(FileManager().open(path))
    editor = window.tabs.current_editor()
    editor.setPlainText("buffer")
    path.write_text("disk", encoding="utf-8")
    shown = []

    class Review:
        def __init__(self, *args):
            self.choice = "reload"
        def exec(self):
            shown.append(True)
            if choice == "stale":
                editor.setPlainText("newer buffer")
            return QDialog.DialogCode.Rejected if choice == "cancel" else QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.ConflictDialog", Review)
    window.review_external_changes()
    wait_until(lambda: shown, application)
    if choice == "reload":
        wait_until(lambda: editor.toPlainText() == "disk", application)
        assert not editor.document_state.dirty
        editor.undo()
        assert editor.toPlainText() == "buffer" and editor.document_state.dirty
    else:
        assert editor.toPlainText() == ("newer buffer" if choice == "stale" else "buffer")
        assert editor.document_state.dirty
    assert path.read_text(encoding="utf-8") == "disk"
    editor.document_state.mark_saved()
    window.close()


def test_conflict_dialog_displays_versions_and_proposal(application):
    from app.ui.conflict_dialog import ConflictDialog
    dialog = ConflictDialog("base", "disk", "buffer", "proposal", 1)
    assert [dialog.tabs.widget(i).toPlainText() for i in range(4)] == ["base", "disk", "buffer", "proposal"]
    assert all(dialog.tabs.widget(i).isReadOnly() for i in range(3))
    assert not dialog.merge.isReadOnly()
    dialog.close()


@pytest.mark.parametrize("choice", ["elsewhere", "markers"])
def test_conflict_review_save_elsewhere_or_reject_unresolved_markers(application, tmp_path, monkeypatch, choice):
    from PySide6.QtWidgets import QDialog
    path = tmp_path / "draft.txt"
    copy = tmp_path / "copy.txt"
    path.write_text("base", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._opened_document(FileManager().open(path))
    editor = window.tabs.current_editor()
    editor.setPlainText("buffer")
    path.write_text("disk", encoding="utf-8")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(copy), ""))

    class Review:
        def __init__(self, base, disk, buffer, proposal, conflicts, parent):
            self.choice = "elsewhere" if choice == "elsewhere" else "merge"
            self.merge = type("Merge", (), {"toPlainText": lambda self: proposal})()
            assert conflicts == 1
        def exec(self):
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.ConflictDialog", Review)
    window.review_external_changes()
    if choice == "elsewhere":
        wait_until(copy.exists, application)
        wait_until(lambda: not editor.document_state.dirty, application)
        assert copy.read_text(encoding="utf-8") == "buffer"
    else:
        wait_until(lambda: warnings, application)
        assert editor.toPlainText() == "buffer" and editor.document_state.dirty
    assert path.read_text(encoding="utf-8") == "disk"
    editor.document_state.mark_saved()
    window.close()


def test_auto_writer_progress_ignores_older_request(application):
    from app.ui.auto_writer_dialog import AutoWriterProgressDialog

    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._auto_writer_progress_dialog = AutoWriterProgressDialog(window)
    window._auto_writer_worker = object()
    window._auto_writer_generation = 2
    try:
        window.auto_writer_progress.emit(1, "Old request")
        window.auto_writer_progress.emit(2, "Current request")
        application.processEvents()
        assert window._auto_writer_progress_dialog.status.text() == "Current request"
        window.auto_writer_progress.emit(1, "Late old request")
        application.processEvents()
        assert window._auto_writer_progress_dialog.status.text() == "Current request"
    finally:
        window._auto_writer_worker = None
        window._auto_writer_progress_dialog.finish("Finished")
        window.close()


def test_auto_writer_progress_and_failure_translate_details(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator
    from app.ui.auto_writer_dialog import AutoWriterProgressDialog

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._auto_writer_progress_dialog = AutoWriterProgressDialog(window)
    window._auto_writer_worker = object()
    application.installTranslator(translator)
    try:
        window._show_auto_writer_progress(window._auto_writer_generation,
                                          "Auto-writer generating scene 2 of 3: Місто")
        assert window._auto_writer_progress_dialog.status.text() == "Автоматичне написання створює сцену 2 з 3: Місто"
        messages = []
        monkeypatch.setattr(window, "_finish_auto_writer", lambda project, message, **kwargs: messages.append(message))
        window._auto_writer_failed(window._auto_writer_generation, window._settings_generation, None, "detail")
        assert "detail" in messages[0] and "Нічого не замінено" in messages[0]
        from unittest.mock import Mock
        window._auto_writer_worker = Mock()
        window.cancel_auto_writer()
        assert "Змін до сцен не застосовано" in messages[1]
    finally:
        window._auto_writer_worker = None
        window._auto_writer_progress_dialog.finish("Finished")
        application.removeTranslator(translator)
        window.close()


def test_project_search_results_are_keyboard_accessible(application):
    from PySide6.QtGui import QAccessible
    from PySide6.QtTest import QTest
    from app.project.search import SearchMatch, SearchResult
    from app.ui.project_search_panel import ProjectSearchPanel

    panel = ProjectSearchPanel()
    first = SearchMatch("scene", "1", "First", 0, 1, 1, "word", "digest")
    second = SearchMatch("note", "2", "Second", 0, 1, 1, "word", "digest")
    panel.set_results(SearchResult((first, second), (), False, False))
    opened = []
    panel.result_requested.connect(opened.append)
    panel.show()
    panel.query.setFocus()
    application.processEvents()
    QTest.keyClick(panel.query, Qt.Key.Key_Down)
    assert panel.results.hasFocus() and panel.results.currentRow() == 0
    QTest.keyClick(panel.results, Qt.Key.Key_Down)
    QTest.keyClick(panel.results, Qt.Key.Key_Return)
    assert opened == [second]
    interface = QAccessible.queryAccessibleInterface(panel.results)
    assert "Enter" in interface.text(QAccessible.Text.Description)
    query_interface = QAccessible.queryAccessibleInterface(panel.query)
    assert "Down" in query_interface.text(QAccessible.Text.Description)
    panel.close()


def test_project_search_finds_open_unsaved_text_and_navigates_only_current_matches(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="disk content")
    project.add_note("Note", content="other word")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("😀 unsaved word")
    window.show_project_search()
    panel = window._project_search_panel
    panel.search_requested.emit("word")
    wait_until(lambda: window._project_search_cancel is None, application)
    assert panel.results.count() == 2
    item = panel.results.item(0)
    panel.result_requested.emit(item.data(Qt.ItemDataRole.UserRole))
    assert editor.textCursor().selectedText() == "word"
    editor.setPlainText("changed word")
    editor.moveCursor(editor.textCursor().MoveOperation.End)
    before = editor.textCursor().position()
    panel.result_requested.emit(item.data(Qt.ItemDataRole.UserRole))
    assert editor.textCursor().position() == before
    assert "changed" in panel.status.text().lower()
    assert project.read_scene(scene.id) == "disk content"
    editor.document_state.mark_saved()
    window.close()


def test_navigation_history_restores_project_search_selections(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="original")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.settings.autosave_enabled = False
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("😀 word and word")
    window.show_project_search()
    panel = window._project_search_panel
    panel.search_requested.emit("word")
    wait_until(lambda: window._project_search_cancel is None, application)
    assert panel.results.count() == 2
    for index in (0, 1):
        panel.result_requested.emit(panel.results.item(index).data(Qt.ItemDataRole.UserRole))
        assert editor.textCursor().selectedText() == "word"
    second_position = editor.textCursor().selectionStart()
    window._navigate_history(-1)
    assert editor.textCursor().selectedText() == "word"
    assert editor.textCursor().selectionStart() < second_position
    window._navigate_history(1)
    assert editor.textCursor().selectionStart() == second_position
    assert editor.toPlainText() == "😀 word and word"
    assert editor.document_state.dirty
    assert project.read_scene(scene.id) == "original"
    editor.document_state.mark_saved()
    window.close()


@pytest.mark.parametrize("changed", [False, True])
def test_project_search_opens_closed_note_and_checks_disk_snapshot(application, tmp_path, changed):
    project = Project.create(tmp_path / "novel", "Novel")
    note = project.add_note("Note", content="😀 found text")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.show_project_search()
    panel = window._project_search_panel
    panel.search_requested.emit("found")
    wait_until(lambda: window._project_search_cancel is None, application)
    assert panel.results.count() == 1
    if changed:
        (project.root / note.path).write_text("different found", encoding="utf-8")
    panel.result_requested.emit(panel.results.item(0).data(Qt.ItemDataRole.UserRole))
    wait_until(lambda: window.tabs.count() == 2, application)
    if changed:
        wait_until(lambda: "changed" in panel.status.text().lower(), application)
        assert not window.tabs.current_editor().textCursor().hasSelection()
    else:
        wait_until(lambda: window.tabs.current_editor().textCursor().hasSelection(), application)
        assert window.tabs.current_editor().textCursor().selectedText() == "found"
    window.close()


def test_project_search_cancel_keeps_gui_responsive(application, tmp_path, monkeypatch):
    from app.project.search import SearchResult
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="word")
    started, release = Event(), Event()
    def search(root, documents, query, cancel, buffers):
        started.set()
        assert release.wait(3)
        return SearchResult((), (), cancel.is_set(), False)
    monkeypatch.setattr("app.ui.main_window.search_project", search)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.show_project_search()
    panel = window._project_search_panel
    panel.search_requested.emit("word")
    wait_until(started.is_set, application)
    panel.cancel_button.click()
    assert window._project_search_cancel.is_set()
    release.set()
    wait_until(lambda: window._project_search_cancel is None, application)
    assert "cancel" in panel.status.text().lower()
    window.close()


def test_project_search_panel_reports_omitted_errors(application):
    from app.project.search import SearchResult
    from app.ui.project_search_panel import ProjectSearchPanel

    panel = ProjectSearchPanel()
    panel.set_results(SearchResult((), ("Unreadable note",), False, False, 23))
    assert "Unreadable note" in panel.status.text()
    assert "Additional unreadable files omitted: 23" in panel.status.text()
    panel.close()


def test_project_search_long_error_report_is_scrollable(application):
    from app.project.search import SearchResult
    from app.ui.project_search_panel import ProjectSearchPanel

    panel = ProjectSearchPanel()
    panel.resize(450, 400)
    errors = tuple(f"Unreadable file {index}: failure" for index in range(100))
    panel.set_results(SearchResult((), errors, False, False, 12))
    panel.show()
    application.processEvents()
    assert panel.status_scroll.height() <= 120
    assert panel.status_scroll.verticalScrollBar().maximum() > 0
    assert panel.status.textFormat() == Qt.TextFormat.PlainText
    assert errors[-1] in panel.status.text()
    assert "Additional unreadable files omitted: 12" in panel.status.text()
    assert panel.results.height() > panel.status_scroll.height()
    panel.close()


def test_project_search_does_not_copy_certainly_oversized_buffer(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="disk word")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    window.settings.autosave_enabled = False
    editor.setPlainText("unsaved " + "x" * 50)
    monkeypatch.setattr("app.ui.main_window.MAX_DOCUMENT_BYTES", 10)
    monkeypatch.setattr(editor, "toPlainText", lambda: pytest.fail("oversized buffer copied"))
    window.show_project_search()
    panel = window._project_search_panel
    panel.search_requested.emit("word")
    wait_until(lambda: window._project_search_cancel is None, application)
    assert panel.results.count() == 0
    assert "size limit" in panel.status.text()
    editor.document_state.mark_saved()
    window.close()


def test_quick_open_filters_aliases_and_distinguishes_duplicate_names(application):
    from app.ui.quick_open_dialog import QuickOpenDialog, QuickOpenItem
    items = (QuickOpenItem("scene", "scene-1", "Shared", "Chapter One"),
             QuickOpenItem("scene", "scene-2", "Shared", "Chapter Two"),
             QuickOpenItem("character", "character-1", "Mara", aliases=("Night Fox",)))
    dialog = QuickOpenDialog(items)
    assert dialog.results.count() == 3
    assert "Chapter One" in dialog.results.item(0).text()
    assert "scene-2" in dialog.results.item(1).text()
    dialog.query.setText("night fox")
    assert dialog.results.count() == 1
    assert dialog.selected().id == "character-1"
    dialog.query.setText("not found")
    dialog._accept_selection()
    assert dialog.result() != dialog.DialogCode.Accepted
    dialog.close()


def test_quick_open_keyboard_selects_filtered_result(application):
    from PySide6.QtTest import QTest
    from app.ui.quick_open_dialog import QuickOpenDialog, QuickOpenItem
    dialog = QuickOpenDialog((QuickOpenItem("scene", "1", "First"), QuickOpenItem("note", "2", "Second")))
    dialog.show()
    dialog.query.setFocus()
    QTest.keyClicks(dialog.query, "second")
    QTest.keyClick(dialog.query, Qt.Key.Key_Return)
    assert dialog.result() == dialog.DialogCode.Accepted
    assert dialog.selected().id == "2"


def test_quick_open_arrow_keys_move_through_results(application):
    from PySide6.QtTest import QTest
    from app.ui.quick_open_dialog import QuickOpenDialog, QuickOpenItem
    dialog = QuickOpenDialog((QuickOpenItem("scene", "1", "First"), QuickOpenItem("note", "2", "Second")))
    dialog.show()
    dialog.query.setFocus()
    application.processEvents()
    QTest.keyClick(dialog.query, Qt.Key.Key_Down)
    assert dialog.results.hasFocus()
    QTest.keyClick(dialog.results, Qt.Key.Key_Down)
    assert dialog.results.currentRow() == 1
    QTest.keyClick(dialog.results, Qt.Key.Key_Return)
    assert dialog.result() == dialog.DialogCode.Accepted
    assert dialog.selected().id == "2"


def test_quick_open_uses_stable_id_and_preserves_unsaved_tabs(application, tmp_path, monkeypatch):
    from app.ui.quick_open_dialog import QuickOpenItem
    from PySide6.QtWidgets import QDialog
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    scene = project.add_scene("Scene", chapter_id=chapter.id, content="disk")
    note = project.add_note("Scene", content="note")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    original = window.tabs.current_editor()
    original.setPlainText("unsaved")
    class Picker:
        def __init__(self, items, parent):
            assert any(item.id == note.id and item.kind == "note" for item in items)
        def exec(self):
            return QDialog.DialogCode.Accepted
        def selected(self):
            return QuickOpenItem("note", note.id, note.title)
    monkeypatch.setattr("app.ui.main_window.QuickOpenDialog", Picker)
    window.quick_open_project_item()
    wait_until(lambda: window.tabs.count() == 3, application)
    assert window.tabs.current_editor().toPlainText() == "note"
    assert original.toPlainText() == "unsaved" and original.document_state.dirty
    original.document_state.mark_saved()
    window.close()


def test_quick_open_handles_deleted_item_and_shortcut_is_unique(application, tmp_path, monkeypatch):
    from app.ui.quick_open_dialog import QuickOpenItem
    from PySide6.QtGui import QKeySequence
    from PySide6.QtWidgets import QDialog
    project = Project.create(tmp_path / "novel", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    class Picker:
        def __init__(self, items, parent):
            pass
        def exec(self):
            return QDialog.DialogCode.Accepted
        def selected(self):
            return QuickOpenItem("note", "deleted", "Deleted")
    monkeypatch.setattr("app.ui.main_window.QuickOpenDialog", Picker)
    missing = []
    monkeypatch.setattr(window, "_project_item_no_longer_exists", lambda: missing.append(True))
    window.quick_open_project_item()
    assert missing == [True]
    actions = [action for menu_action in window.menuBar().actions() if menu_action.menu()
               for action in menu_action.menu().actions()]
    assert sum(action.shortcut() == QKeySequence("Ctrl+P") for action in actions) == 1
    window.close()


def test_quick_open_reveals_chapter_in_tree(application, tmp_path, monkeypatch):
    from app.ui.quick_open_dialog import QuickOpenItem
    from PySide6.QtWidgets import QDialog
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    class Picker:
        def __init__(self, items, parent):
            pass
        def exec(self):
            return QDialog.DialogCode.Accepted
        def selected(self):
            return QuickOpenItem("chapter", chapter.id, chapter.title)
    monkeypatch.setattr("app.ui.main_window.QuickOpenDialog", Picker)
    window.quick_open_project_item()
    assert window.project_view._item_key(window.project_view.currentItem()) == ("chapter", chapter.id)
    window.close()


def test_open_linked_item_navigates_from_scene_to_note_without_changing_links(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="draft")
    note = project.add_note("Reference", content="reference")
    project.link_note(note.id, scene.id)
    links = tuple(project.manifest.links)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("unsaved draft")
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    monkeypatch.setattr(QInputDialog, "getItem", lambda parent, title, label, items, *args: (items[0], True))
    window.open_linked_project_item()
    wait_until(lambda: window.tabs.count() == 3, application)
    assert window.tabs.current_editor().toPlainText() == "reference"
    assert editor.toPlainText() == "unsaved draft" and editor.document_state.dirty
    assert tuple(project.manifest.links) == links
    assert ("Open Linked Item…", "open_linked") in ProjectView.context_actions("scene")
    editor.document_state.mark_saved()
    window.close()


def test_link_navigation_rechecks_selected_link_and_project(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Book")
    scene = project.add_scene("Scene [draft]", content="text")
    note = project.add_note("Note", content="world")
    project.link_note(note.id, scene.id)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("note", note.id))
    opened = []
    monkeypatch.setattr(window, "_open_project_document", lambda *args: opened.append(args))
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    window.open_linked_project_item()
    assert opened == [("scene", scene.id)]

    def remove_link(*args):
        project.unlink_note(note.id, scene.id)
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", remove_link)
    window.open_linked_project_item()
    assert opened == [("scene", scene.id)]
    assert "no longer available" in window.statusBar().currentMessage()
    project.link_note(note.id, scene.id)

    def switch_project(*args):
        window.project = None
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", switch_project)
    window.open_linked_project_item()
    assert opened == [("scene", scene.id)]
    window.close()


def test_close_and_quit_use_translated_unsaved_prompt(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    editor.setPlainText("unsaved")
    messages = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: messages.append(args) or QMessageBox.StandardButton.Cancel)
    application.installTranslator(translator)
    try:
        window.close_tab(window.tabs.currentIndex())
        assert editor.document_state.dirty and window.tabs.indexOf(editor) >= 0
        assert window._ask_to_save_dirty_document(editor) == QMessageBox.StandardButton.Cancel
        assert len(messages) == 2
        for args in messages:
            assert args[1] == "Незбережені зміни"
            assert args[2] == "Зберегти зміни в документі Без назви?"
    finally:
        application.removeTranslator(translator)
        editor.document_state.mark_saved()
        window.close()


@pytest.mark.parametrize("label, expected", [
    ("Персонаж", "character"), ("Місце дії", "setting"), ("Хронологія", "timeline"),
    ("Дослідження", "research"), ("Загальне", "general"),
])
def test_translated_note_type_choice_preserves_manifest_type(application, tmp_path, monkeypatch, label, expected):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    called = []
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("My notes", True))

    def choose(*args):
        assert args[1] == "Тип довідкової нотатки"
        assert args[3] == ["Персонаж", "Місце дії", "Хронологія", "Дослідження", "Загальне"]
        return label, True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    monkeypatch.setattr(window, "_run_project_mutation", lambda operation, *args: called.append((operation, args)))
    application.installTranslator(translator)
    try:
        window.add_project_note()
        assert len(called) == 1 and called[0][1] == ("My notes", expected)
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_character_removal_cancel_keeps_profile(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("character", character.id))
    questions = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: questions.append(args) or QMessageBox.StandardButton.Cancel)
    application.installTranslator(translator)
    try:
        window.remove_project_item()
        assert questions[0][1] == "Видалити персонажа"
        assert "Mara" in questions[0][2] and "неможливо скасувати" in questions[0][2]
        assert project.get_character(character.id).full_name == "Mara"
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_link_picker_preserves_target_ids(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    note = project.add_note("Notes")
    scene = project.add_scene("Draft")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("note", note.id))
    called = []
    monkeypatch.setattr(window, "_run_project_mutation", lambda operation, *args: called.append((operation, args)))

    def choose(*args):
        assert args[3] == [f"Сцена: Draft [{scene.id[-8:]}]"]
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    application.installTranslator(translator)
    try:
        window.link_project_note()
        assert called[-1][1] == (note.id, scene.id)
        project.link_note(note.id, scene.id)
        window.unlink_project_note()
        assert called[-1][1] == (note.id, scene.id)
    finally:
        application.removeTranslator(translator)
        window.close()


@pytest.mark.parametrize("label, expected", [("присутній", "present"), ("згаданий", "mentioned")])
def test_translated_scene_presence_preserves_manifest_value(application, tmp_path, monkeypatch, label, expected):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    scene = project.add_scene("Draft")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    called = []
    monkeypatch.setattr(window, "_run_project_mutation", lambda operation, *args: called.append((operation, args)))

    def choose(*args):
        if args[1] == "Участь у сцені":
            assert args[3] == ["присутній", "згаданий"]
            return label, True
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("purpose", True))
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *args, **kwargs: ("", True))
    application.installTranslator(translator)
    try:
        window.associate_project_character()
        association = called[0][1][1]
        assert association.character_id == character.id and association.presence == expected
        assert association.purpose == "purpose"
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_relationship_action_removes_only_selected_direction(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator
    from app.project.model import CharacterRelationship

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    first, second = project.add_character("Mara"), project.add_character("Ivo")
    relation = CharacterRelationship("00000000-0000-4000-8000-000000000001", first.id, second.id)
    project.add_character_relationship(relation)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("character", first.id))
    called = []
    monkeypatch.setattr(window, "_run_project_mutation", lambda operation, *args: called.append((operation, args)))

    def choose(*args):
        if args[2] == "Дія:":
            assert args[3] == ["Редагувати стосунки", "Видалити стосунки"]
            return args[3][1], True
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    application.installTranslator(translator)
    try:
        window.manage_project_character_relationships()
        assert called[0][1] == (relation.id,)
        assert called[0][0].__name__ == "remove_character_relationship"
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_project_translation_confirmation_discloses_destination(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window.settings.ai_enabled = True
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kwargs: True)
    questions = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: questions.append(args) or QMessageBox.StandardButton.Cancel)
    application.installTranslator(translator)
    try:
        window.translate_project_to_ukrainian()
        assert questions[0][1] == "Перекласти проєкт"
        assert "англійська → українська" in questions[0][2]
        assert window.provider.host in questions[0][2] and window.provider.model in questions[0][2]
        assert not window._project_busy
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_autopilot_confirmation_discloses_automatic_changes(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator
    from app.ui.project_brief_dialog import ProjectBriefDialog

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window.settings.ai_enabled = True
    dialog = ProjectBriefDialog(window)
    window._project_setup_brief_dialog = dialog
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kwargs: True)
    questions = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: questions.append(args) or QMessageBox.StandardButton.Cancel)
    application.installTranslator(translator)
    try:
        window._start_project_autopilot(project, dialog, "Story")
        assert questions[0][1] == "Підтвердити автономний автопілот"
        assert "автоматично" in questions[0][2] and window.provider.host in questions[0][2]
        assert not window._project_busy and list(project.iter_scenes()) == []
    finally:
        application.removeTranslator(translator)
        dialog.reject()
        window.close()


def test_translated_project_analysis_confirmation_lists_captured_context(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    project = Project.create(tmp_path / "project", "Book")
    scene = project.add_scene("Draft", content="private text")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    window.project_view.setCurrentItem(window.project_view.topLevelItem(0).child(0).child(0))
    window.settings.ai_enabled = True
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kwargs: True)
    questions = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: questions.append(args) or QMessageBox.StandardButton.Cancel)
    application.installTranslator(translator)
    try:
        window.summarize_project_scene()
        assert questions[0][1] == "Підтвердити локальний аналіз проєкту"
        assert f"Сцена: Draft ({scene.id})" in questions[0][2]
        assert window.provider.host in questions[0][2]
        assert window._project_ai_worker is None and project.read_scene(scene.id) == "private text"
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_debug_warning_and_status_accessibility(application, tmp_path):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator
    from PySide6.QtWidgets import QLabel
    from app.ui.ai_debug_window import AIDebugWindow

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    application.installTranslator(translator)
    try:
        with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
            window = MainWindow()
        debug = AIDebugWindow(window)
        assert window._writing_goal_label.accessibleName() == "Поступ до щоденної цілі письма"
        assert window._exit_focus_button.accessibleName() == "Вийти з режиму без відволікань"
        assert "лише в пам’яті" in debug.findChild(QLabel).text()
        debug.close()
        window.close()
    finally:
        application.removeTranslator(translator)


def test_translated_whole_document_formatting_preserves_operation(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    editor.setPlainText("draft")

    def choose(*args):
        assert args[1] == "Форматувати весь документ"
        return args[3][1], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    application.installTranslator(translator)
    try:
        window._format_whole_document()
        assert editor.toPlainText() == "DRAFT"
        editor.undo()
        assert editor.toPlainText() == "draft"
    finally:
        application.removeTranslator(translator)
        editor.document_state.mark_saved()
        window.close()


def test_translated_recent_file_save_error_preserves_detail(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()

    def fail():
        raise OSError("disk error")

    monkeypatch.setattr(window.settings, "save", fail)
    application.installTranslator(translator)
    try:
        window._clear_recent_files()
        assert window.statusBar().currentMessage() == "Не вдалося зберегти список нещодавніх файлів: disk error"
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_open_project_dialog_title(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    titles = []
    monkeypatch.setattr("app.ui.main_window.QFileDialog.getExistingDirectory",
                        lambda _parent, title: titles.append(title) or "")
    application.installTranslator(translator)
    try:
        window.open_project()
        assert titles == ["Відкрити проєкт"]
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_spellcheck_feedback(application, tmp_path):
    import subprocess
    import sys
    from PySide6.QtCore import QCoreApplication, QTranslator

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    editor = window.tabs.current_editor()
    application.installTranslator(translator)
    try:
        window._spellcheck_failed("network detail", editor, editor.revision,
                                  window._settings_generation, window._active_document_generation,
                                  window._spellcheck_generation)
        assert window.status.currentMessage() == "Не вдалося перевірити правопис: network detail"
        window.ai_status = "AI: Connected"
        window._update_status()
        assert "ШІ: підключено" in window.status.currentMessage()
        assert window.ai_status == "AI: Connected"
        source = "Found %n spelling suggestions. Right-click an underline to review."
        for count, form in ((1, "пропозицію"), (2, "пропозиції"), (5, "пропозицій")):
            assert form in QCoreApplication.translate("MainWindow", source, None, count)
    finally:
        application.removeTranslator(translator)
        window.close()


def test_translated_project_translation_cancellation_progress(application, tmp_path, monkeypatch):
    import subprocess
    import sys
    from PySide6.QtCore import QTranslator
    from PySide6.QtWidgets import QProgressDialog

    compiler = Path(sys.executable).parent / "pyside6-lrelease"
    if not compiler.exists():
        pytest.skip("Qt Linguist compiler is unavailable")
    catalog = tmp_path / "uk.qm"
    subprocess.run([str(compiler), "translations/utexteditor_uk.ts", "-qm", str(catalog)],
                   check=True, capture_output=True)
    translator = QTranslator()
    assert translator.load(str(catalog))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_translation_worker = object()
    window._project_translation_progress_dialog = QProgressDialog(window)
    application.installTranslator(translator)
    try:
        window._show_project_translation_progress(
            window._project_translation_generation, "Translating Scene title 'Місто (старе)' (2 of 5)…"
        )
        assert window._project_translation_progress_dialog.labelText() == "Переклад: Назва сцени 'Місто (старе)' (2 з 5)…"
        window._show_project_translation_progress(
            window._project_translation_generation, "Translated text for scene-1 (3 of 5)."
        )
        assert window._project_translation_progress_dialog.labelText() == "Перекладено: текст для scene-1 (3 з 5)."
        window.cancel_project_translation()
        assert window._project_translation_progress_dialog.labelText() == "Скасування після поточного запиту до моделі…"
        messages = []
        monkeypatch.setattr(window, "_finish_project_translation",
                            lambda project, message, **kwargs: messages.append(message))
        window._project_translation_cancel_event = None
        window._project_translation_failed(window._project_translation_generation, None, "detail")
        assert messages == ["Не вдалося перекласти проєкт. Файли проєкту не змінено: detail"]
    finally:
        window._project_translation_worker = None
        application.removeTranslator(translator)
        window.close()


def test_native_tab_shortcuts_switch_without_discarding_changes(application):
    from PySide6.QtTest import QTest
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    first = window.tabs.current_editor()
    first.setPlainText("unsaved")
    second = window.tabs.new_document()
    window.tabs.setCurrentWidget(first)
    window.show()
    application.processEvents()
    QTest.keyClick(first, Qt.Key.Key_Tab, Qt.KeyboardModifier.ControlModifier)
    assert window.tabs.current_editor() is second
    QTest.keyClick(second, Qt.Key.Key_Tab, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
    assert window.tabs.current_editor() is first
    assert first.toPlainText() == "unsaved" and first.document_state.dirty
    first.document_state.mark_saved()
    window.close()


def test_open_tabs_picker_shows_modified_and_distinguishes_untitled_tabs(application, monkeypatch):
    from PySide6.QtWidgets import QDialog
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    first = window.tabs.current_editor()
    first.setPlainText("unsaved")
    second = window.tabs.new_document()
    class Picker:
        def __init__(self, items, parent, *, show_id):
            assert not show_id and items[0].title.endswith(" *")
            assert items[0].context != items[1].context
            self.item = items[0]
            self.query = type("Input", (), {"setPlaceholderText": lambda *a: None, "setAccessibleName": lambda *a: None})()
            self.results = type("Results", (), {"setAccessibleName": lambda *a: None})()
        def setWindowTitle(self, title):
            pass
        def exec(self):
            return QDialog.DialogCode.Accepted
        def selected(self):
            return self.item
    monkeypatch.setattr("app.ui.main_window.QuickOpenDialog", Picker)
    assert window.tabs.current_editor() is second
    window.select_open_tab()
    assert window.tabs.current_editor() is first and first.toPlainText() == "unsaved"
    first.document_state.mark_saved()
    window.close()


def test_recent_files_reopen_deduplicate_report_missing_and_clear(application, tmp_path, monkeypatch):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._open_document_path(str(first))
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("unsaved")
    window._open_document_path(str(second))
    wait_until(lambda: window.tabs.count() == 3, application)
    assert window.settings.recent_files == [str(second), str(first)]
    window._populate_recent_files_menu()
    next(action for action in window._recent_files_menu.actions() if action.data() == str(first)).trigger()
    assert window.tabs.count() == 3 and window.tabs.current_editor() is editor
    assert editor.toPlainText() == "unsaved" and editor.document_state.dirty
    assert window.settings.recent_files == [str(first), str(second)]
    window.close_tab(2)
    second.unlink()
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    window._open_document_path(str(second))
    wait_until(lambda: warnings, application)
    assert window.tabs.count() == 2 and editor.toPlainText() == "unsaved"
    window._clear_recent_files()
    assert window.settings.recent_files == []
    assert AppSettings.load().recent_files == []
    editor.document_state.mark_saved()
    window.close()


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
    assert root.childCount() == 3
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
    assert root.child(2).text(0) == "Characters (0)"
    window.close()


@pytest.mark.parametrize("kind", ["scene", "note"])
def test_reveal_current_project_document_uses_stable_id_and_preserves_other_branches(application, tmp_path, kind):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    scene = project.add_scene("Shared", chapter_id=chapter.id, content="draft")
    note = project.add_note("Shared", content="note")
    item = scene if kind == "scene" else note
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    wait_until(lambda: window.project_view is not None and window.project_view.topLevelItemCount() > 0, application)
    view = window.project_view
    root = view.topLevelItem(0)
    for child in (root, *(root.child(i) for i in range(root.childCount()))):
        child.setExpanded(False)
    unrelated = next(root.child(i) for i in range(root.childCount()) if root.child(i).data(0, Qt.ItemDataRole.UserRole + 1) == "characters")
    window._open_project_document(kind, item.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.insertPlainText(" unsaved")
    before = editor.toPlainText()
    window.reveal_current_project_document()
    selected = view.currentItem()
    assert view._item_key(selected) == (kind, item.id)
    assert root.isExpanded() and selected.parent().isExpanded()
    assert not unrelated.isExpanded()
    assert editor.toPlainText() == before
    editor.document_state.mark_saved()
    window.close()


def test_reveal_standalone_document_explains_unbound_state(application):
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.reveal_current_project_document()
    assert "not bound" in window.statusBar().currentMessage()
    window.close()


@pytest.mark.parametrize("kind", ["scene", "note"])
@pytest.mark.parametrize("legacy", [False, True])
def test_project_recovery_snapshot_restores_after_relocation(application, tmp_path, kind, legacy, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    item = (project.add_scene("Opening", content="saved") if kind == "scene"
            else project.add_note("Reference", content="saved"))
    store = RecoveryStore(tmp_path / "recovery")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow(recovery_store=store)
    window.project = project
    window._open_project_document(kind, item.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("unsaved recovery")
    payload, = window._recovery_payloads()
    assert payload.project_item_id == item.id and payload.project_item_kind == kind
    entries, failures = window._save_recovery_batch(store, (payload,))
    assert not failures
    entry = entries[0]
    if legacy:
        import json
        data = json.loads(entry.snapshot_path.read_text(encoding="utf-8"))
        del data["project_item_id"], data["project_item_kind"]
        entry.snapshot_path.write_text(json.dumps(data), encoding="utf-8")
    entry, = store.scan().entries
    relocated = tmp_path / "moved"
    project.root.rename(relocated)
    restored, = window._prepare_recovery_restore(store, (entry,), relocated)
    _, document, error = restored
    assert error is None
    assert document.path == relocated / item.path
    assert document.text == "unsaved recovery" and document.dirty
    assert (relocated / item.path).read_text(encoding="utf-8") == "saved"
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    window._recovery_restore_finished([restored])
    assert window.tabs.current_editor().toPlainText() == "unsaved recovery"
    for index in range(window.tabs.count()):
        window.tabs.widget(index).document_state.dirty = False
        window.tabs.widget(index).document().setModified(False)
    window.close()


@pytest.mark.parametrize("failure", ["changed", "missing_item", "wrong_project", "unavailable"])
def test_project_recovery_failures_preserve_text_as_untitled(tmp_path, failure):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="saved")
    store = RecoveryStore(tmp_path / "recovery")
    entry = store.save("recovery-id", "unsaved", canonical_path=project.root / scene.path,
                       project_path=project.root, project_id=project.manifest.project_id,
                       project_item_id=scene.id, project_item_kind="scene")
    located = None
    if failure == "changed":
        (project.root / scene.path).write_text("external", encoding="utf-8")
    elif failure == "missing_item":
        project.remove_scene(scene.id)
    elif failure == "wrong_project":
        project.root.rename(tmp_path / "original")
        located = Project.create(tmp_path / "other", "Other").root
    else:
        project.root.rename(tmp_path / "original")
    _, document, error = MainWindow._prepare_recovery_restore(store, (entry,), located)[0]
    assert error and document.path is None and document.text == "unsaved" and document.dirty
    assert entry.snapshot_path.exists()


@pytest.mark.parametrize("change", ["removed", "relinked"])
def test_project_open_discards_result_for_changed_item(application, tmp_path, change):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    path = project.root / scene.path
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    try:
        if change == "removed":
            project.remove_scene(scene.id)
        else:
            replacement = project.root / "replacement.md"
            replacement.write_text("replacement", encoding="utf-8")
            project.relink_scene(scene.id, "replacement.md")
        count = window.tabs.count()
        window._project_document_opened(project, "scene", scene.id, path, "original")
        assert window.tabs.count() == count
        assert not window._project_documents
    finally:
        window.close()


@pytest.mark.parametrize("route", ["existing", "duplicate"])
@pytest.mark.parametrize("change_timing", ["before_read", "while_pending"])
def test_binding_open_file_preserves_external_change_protection(application, tmp_path, route, change_timing):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    path = project.root / scene.path
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    editor = window.tabs.add_document(FileManager().open(path))
    editor.setPlainText("unsaved")
    if change_timing == "before_read":
        path.write_text("external", encoding="utf-8")
    raw = project.read_scene(scene.id)
    if change_timing == "while_pending":
        path.write_text("external", encoding="utf-8")
    if route == "existing":
        window._bind_existing_project_document(project, editor, "scene", scene.id, raw)
    else:
        window._project_document_opened(project, "scene", scene.id, path, raw)
    if change_timing == "before_read":
        assert editor not in window._project_documents
        with pytest.raises(ExternalChangeError):
            FileManager().save(editor.document_state)
    else:
        binding = window._project_documents[editor]
        with pytest.raises(ProjectError, match="changed"):
            window._save_project_document(binding, "unsaved", "LF")
    assert path.read_text(encoding="utf-8") == "external"
    editor.document_state.dirty = False
    editor.document().setModified(False)
    window.close()


def test_binding_ignores_editor_moved_while_project_read_pending(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="original")
    path = project.root / scene.path
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    editor = window.tabs.add_document(FileManager().open(path))
    raw = project.read_scene(scene.id)
    FileManager().save(editor.document_state, tmp_path / "saved-as.txt")
    window._bind_existing_project_document(project, editor, "scene", scene.id, raw)
    assert editor not in window._project_documents
    window.close()


def test_recovery_cleanup_waits_for_older_snapshot_and_preserves_newer_edits(application, tmp_path, monkeypatch):
    store = RecoveryStore(tmp_path / "recovery")
    entered, release = Event(), Event()
    real_save = store.save

    def delayed_save(*args, **kwargs):
        entered.set()
        assert release.wait(3)
        return real_save(*args, **kwargs)

    monkeypatch.setattr(store, "save", delayed_save)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow(recovery_store=store)
    editor = window.tabs.current_editor()
    editor.setPlainText("old unsaved")
    window._capture_recovery_snapshots()
    wait_until(entered.is_set, application)
    window._discard_recovery_for_editor(editor)
    release.set()
    wait_until(lambda: not window._recovery_pending, application)
    # Queue a newer snapshot after the cleanup; it must not be deleted by it.
    editor.setPlainText("new unsaved")
    window._capture_recovery_snapshots()
    wait_until(lambda: not window._recovery_pending, application)
    entries = store.scan().entries
    assert [entry.text for entry in entries] == ["new unsaved"]
    editor.document_state.dirty = False
    editor.document().setModified(False)
    window.close()
    wait_until(lambda: window._closing_confirmed, application)


def test_shutdown_waits_for_queued_recovery_cleanup(application, tmp_path, monkeypatch):
    store = RecoveryStore(tmp_path / "recovery")
    entered, release = Event(), Event()
    real_discard = store.discard_document

    def delayed_discard(document_id):
        entered.set()
        assert release.wait(3)
        real_discard(document_id)

    monkeypatch.setattr(store, "discard_document", delayed_discard)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow(recovery_store=store)
    editor = window.tabs.current_editor()
    editor._recovery_document_id = "document"
    store.save("document", "obsolete")
    window._discard_recovery_for_editor(editor)
    wait_until(entered.is_set, application)
    window.close()
    assert not window._closing_confirmed and window._shutdown_recovery_pending
    release.set()
    wait_until(lambda: window._closing_confirmed, application)
    assert not store.scan().entries


def test_project_tree_refresh_preserves_navigation_state(application, tmp_path):
    project = Project.create(tmp_path / "tree-state", "Novel")
    first = project.add_character("Mara")
    second = project.add_character("Ira")
    view = ProjectView()
    view.show_project(project, {}, {}, WordCount(0, True))
    root = view.topLevelItem(0)
    notes, characters = root.child(0), root.child(1)
    notes.setExpanded(False)
    view.setCurrentItem(characters.child(0))
    characters.child(1).setSelected(True)

    view.show_project(project, {}, {}, WordCount(1, True))

    root = view.topLevelItem(0)
    assert not root.child(0).isExpanded()
    assert root.child(1).isExpanded()
    assert {item.data(0, Qt.ItemDataRole.UserRole + 1) for item in view.selectedItems()} == {first.id, second.id}
    assert view.currentItem().data(0, Qt.ItemDataRole.UserRole + 1) == first.id

    view.filter_characters("Ira")
    project.remove_character(first.id)
    view.show_project(project, {}, {}, WordCount(1, True))
    characters = view.topLevelItem(0).child(1)
    assert characters.childCount() == 1
    assert not characters.child(0).isHidden()
    assert characters.child(0).data(0, Qt.ItemDataRole.UserRole + 1) == second.id


def test_activating_character_profile_opens_editor_instead_of_note_document(
    application, tmp_path, monkeypatch
):
    AppSettings(ui_language="en").save()
    project = Project.create(tmp_path / "character-project", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    opened = []
    monkeypatch.setattr(window, "_edit_character", opened.append)
    window.project = project
    view = ProjectView()
    view.open_requested.connect(window._open_project_document)
    view.show_project(project, {}, {}, WordCount(0, True))
    character_group = next(
        view.topLevelItem(0).child(index)
        for index in range(view.topLevelItem(0).childCount())
        if view.topLevelItem(0).child(index).text(0).startswith("Characters (")
    )

    view.itemActivated.emit(character_group.child(0), 0)

    assert len(opened) == 1
    assert opened[0].id == character.id
    assert window.tabs.count() == 1
    translator = window._ui_translator
    window.close()
    if translator is not None:
        application.removeTranslator(translator)


def test_stale_note_tree_item_is_ignored_and_project_tree_refreshed(
    application, tmp_path, monkeypatch
):
    AppSettings(ui_language="en").save()
    project = Project.create(tmp_path / "stale-project", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    refreshed = []
    monkeypatch.setattr(window, "_refresh_project_view", lambda: refreshed.append(True))
    window.project = project

    window._open_project_document("note", "removed-note-id")

    assert refreshed == [True]
    assert "no longer exists" in window.statusBar().currentMessage()
    assert not window._pending_project_opens
    translator = window._ui_translator
    window.close()
    if translator is not None:
        application.removeTranslator(translator)


def test_character_profile_dialog_keeps_edits_pending_until_save(application, monkeypatch):
    from app.project import Character

    character = Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara")
    dialog = CharacterDialog(character)
    dialog.full_name.setText("Mara Venn")
    dialog.motivation.setPlainText("Expose the council")
    dialog.goals.setPlainText("Find the ledger | active | 1 | before the trial")
    assert character.full_name == "Mara"
    dialog._accept()
    assert dialog.character.full_name == "Mara Venn"
    assert dialog.character.primary_motivation == "Expose the council"
    assert dialog.character.goals[0].status == "active"
    assert dialog.character.goals[0].priority == 1
    assert dialog.character.goals[0].notes == "before the trial"
    dialog.close()


def test_character_profile_long_forms_scroll_and_preserve_fields(application):
    from PySide6.QtWidgets import QScrollArea, QTabWidget
    from app.project import Character

    original = Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara")
    dialog = CharacterDialog(original)
    dialog.resize(400, 380)
    dialog.show()
    tabs = dialog.findChild(QTabWidget)
    tabs.setCurrentIndex(2)
    application.processEvents()
    story_scroll = tabs.currentWidget()
    assert isinstance(story_scroll, QScrollArea)
    assert story_scroll.verticalScrollBar().maximum() > 0
    dialog.conflicts.setPlainText("Trust versus loyalty")
    story_scroll.ensureWidgetVisible(dialog.conflicts)
    assert story_scroll.verticalScrollBar().value() > 0
    tabs.setCurrentIndex(3)
    application.processEvents()
    context_scroll = tabs.currentWidget()
    assert isinstance(context_scroll, QScrollArea)
    assert context_scroll.verticalScrollBar().maximum() > 0
    dialog.personality_fields["attitudes"].setPlainText("guarded")
    context_scroll.ensureWidgetVisible(dialog.personality_fields["attitudes"])
    assert context_scroll.verticalScrollBar().value() > 0
    dialog._accept()
    assert dialog.character.internal_conflicts == ["Trust versus loyalty"]
    assert dialog.character.personality["attitudes"] == ["guarded"]
    assert original.internal_conflicts == []


def test_character_ai_suggestions_require_review_and_leave_existing_fields(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    dialog = CharacterDialog(character)
    dialog.description.setPlainText("Existing description")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kwargs: '{"primary_motivation":"Find the key"}')
    monkeypatch.setattr("app.ui.main_window.GeneratedTextDialog.exec", lambda self: self.DialogCode.Accepted)
    window._suggest_character_profile(dialog, project)
    wait_until(lambda: dialog.ai_button.isEnabled(), application)
    assert dialog.motivation.toPlainText() == "Find the key"
    assert dialog.description.toPlainText() == "Existing description"
    assert project.get_character(character.id).primary_motivation == ""
    dialog.reject()
    window.close()


def test_character_ai_discards_result_if_profile_changes(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    dialog = CharacterDialog(character)
    started, release = Event(), Event()
    def generate(*args, **kwargs):
        started.set()
        release.wait(3)
        return '{"primary_motivation":"Generated"}'
    messages = []
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: messages.append(args))
    monkeypatch.setattr(window.provider, "generate_private", generate)
    window._suggest_character_profile(dialog, project)
    wait_until(started.is_set, application)
    dialog.motivation.setPlainText("My idea")
    release.set()
    wait_until(lambda: bool(messages), application)
    assert dialog.motivation.toPlainText() == "My idea"
    dialog.reject()
    window.close()


def test_character_profile_relationships_are_staged_and_saved_together(application, tmp_path, monkeypatch):
    from app.project import CharacterRelationship
    from uuid import uuid4

    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    relation = CharacterRelationship(str(uuid4()), ivo.id, mara.id, relationship_type="rival")
    project.add_character_relationship(relation)
    dialog = CharacterDialog(mara, project_characters=project.manifest.characters,
                             project_relationships=project.manifest.character_relationships)
    assert "← Ivo: rival" in dialog.relationship_list.item(0).text()
    dialog.relationship_list.setCurrentRow(0)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    dialog._remove_relationship()
    assert len(project.manifest.character_relationships) == 1
    dialog.full_name.setText("Mara Venn")
    dialog._accept()
    project.update_character_with_relationships(mara.id, dialog.character, dialog.relationships)
    reopened = Project.open(project.root)
    assert reopened.get_character(mara.id).full_name == "Mara Venn"
    assert reopened.manifest.character_relationships == []
    dialog.close()


def test_character_profile_adds_relationship_without_mutating_project(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    dialog = CharacterDialog(mara, project_characters=project.manifest.characters)
    monkeypatch.setattr(QInputDialog, "getItem", lambda *args: (args[3][0], True))
    monkeypatch.setattr(CharacterRelationshipDialog, "exec", lambda self: self.DialogCode.Accepted)
    dialog._add_relationship()
    assert len(dialog.relationships) == 1
    assert (dialog.relationships[0].source_id, dialog.relationships[0].target_id) == (mara.id, ivo.id)
    dialog.relationship_list.setCurrentRow(0)
    def edit_relationship(self):
        self.relationship.relationship_type = "ally"
        return self.DialogCode.Accepted
    monkeypatch.setattr(CharacterRelationshipDialog, "exec", edit_relationship)
    dialog._edit_relationship()
    assert dialog.relationships[0].relationship_type == "ally"
    assert not project.manifest.character_relationships
    dialog.reject()
    assert not Project.open(project.root).manifest.character_relationships


def test_profile_and_relationship_update_rolls_back_on_write_failure(tmp_path, monkeypatch):
    from app.project import CharacterRelationship
    from uuid import uuid4

    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara")
    ivo = project.add_character("Ivo")
    mara.full_name = "Changed"
    relationship = CharacterRelationship(str(uuid4()), mara.id, ivo.id, "ally")
    def fail_write():
        raise OSError("write failed")
    monkeypatch.setattr(project, "_write_manifest", fail_write)
    with pytest.raises(OSError, match="write failed"):
        project.update_character_with_relationships(mara.id, mara, [relationship])
    assert project.get_character(mara.id).full_name == "Mara"
    assert not project.manifest.character_relationships
    assert Project.open(project.root).get_character(mara.id).full_name == "Mara"


def test_character_profile_dialog_rejects_invalid_goal_status(application, monkeypatch):
    from app.project import Character

    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    dialog = CharacterDialog(Character(id="00000000-0000-4000-8000-000000000001", full_name="Mara"))
    dialog.goals.setPlainText("Find the ledger | unknown | 3")
    dialog._accept()
    assert dialog.result() == 0
    assert warnings
    dialog.close()


def test_character_profile_dialog_can_clear_existing_personality_fields(application):
    from app.project import Character

    character = Character(
        id="00000000-0000-4000-8000-000000000001",
        full_name="Mara",
        personality={"strengths": ["patient"], "fears": ["fire"]},
    )
    dialog = CharacterDialog(character)
    dialog.personality_fields["strengths"].clear()
    dialog.personality_fields["fears"].setPlainText("")

    dialog._accept()

    assert "strengths" not in dialog.character.personality
    assert "fears" not in dialog.character.personality
    assert character.personality == {"strengths": ["patient"], "fears": ["fire"]}
    dialog.close()


def test_character_relationship_dialog_edits_structured_fields_and_validates_trust(
    application, monkeypatch
):
    from uuid import uuid4

    from app.project import CharacterRelationship

    relationship = CharacterRelationship(str(uuid4()), str(uuid4()), str(uuid4()))
    dialog = CharacterRelationshipDialog(relationship)
    dialog.relationship_type.setText("reluctant ally")
    dialog.attitude.setText("wary")
    dialog.trust.setText("72")
    dialog.status.setText("strained")
    dialog.shared_secrets.setPlainText("They both hid the letter.")
    dialog._accept()

    assert dialog.relationship.relationship_type == "reluctant ally"
    assert dialog.relationship.attitude == "wary"
    assert dialog.relationship.trust == 72
    assert dialog.relationship.status == "strained"
    assert dialog.relationship.shared_secrets == "They both hid the letter."
    assert relationship.relationship_type == "unknown"
    dialog.close()

    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    invalid = CharacterRelationshipDialog(relationship)
    invalid.trust.setText("101")
    invalid._accept()
    assert invalid.result() == 0
    assert warnings
    invalid.close()


def test_scene_character_selector_disambiguates_duplicate_display_names(
    application, tmp_path, monkeypatch
):
    project = Project.create(tmp_path / "novel", "Novel")
    first = project.add_character("Alex")
    second = project.add_character("Alex")
    scene = project.add_scene("Meeting")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    choices = []

    def choose(_parent, _title, _label, items, *_args):
        choices.append(list(items))
        return items[1], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    monkeypatch.setattr(QInputDialog, "getText", lambda *_args, **_kwargs: ("purpose", True))
    monkeypatch.setattr(QInputDialog, "getMultiLineText", lambda *_args: ("", True))
    mutations = []
    monkeypatch.setattr(
        window, "_run_project_mutation", lambda operation, *args, **kwargs: mutations.append((operation, args))
    )

    window.associate_project_character()

    assert choices[0][0] != choices[0][1]
    association = mutations[0][1][1]
    assert association.character_id == second.id
    assert association.character_id != first.id
    window.close()


def test_reassociating_character_prefills_existing_scene_development_and_state(
    application, tmp_path, monkeypatch
):
    from app.project import CharacterStateChange, SceneCharacterAssociation

    project = Project.create(tmp_path / "novel", "Novel")
    character = project.add_character("Mara")
    scene = project.add_scene("Meeting")
    existing = SceneCharacterAssociation(
        character.id,
        presence="mentioned",
        purpose="warns Ivo",
        development_notes=["admits she is afraid"],
        state_changes=[
            CharacterStateChange("knowledge", "knows the code", "does not know", "reads the letter")
        ],
    )
    project.associate_character(scene.id, existing)
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("scene", scene.id))
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda _p, title, _l, items, index, _editable: (
            items[-1] if title == "Associate character" else items[index],
            True,
        ),
    )
    text_defaults = []

    def get_text(_parent, _title, _label, **kwargs):
        text_defaults.append(kwargs.get("text", ""))
        return kwargs.get("text", ""), True

    def get_multiline(_parent, _title, _label, default=""):
        text_defaults.append(default)
        return default, True

    monkeypatch.setattr(QInputDialog, "getText", get_text)
    monkeypatch.setattr(QInputDialog, "getMultiLineText", get_multiline)
    mutations = []
    monkeypatch.setattr(
        window,
        "_run_project_mutation",
        lambda operation, *args, **kwargs: mutations.append((operation, args)),
    )

    window.associate_project_character()

    updated = mutations[0][1][1]
    assert updated.presence == "mentioned"
    assert updated.purpose == "warns Ivo"
    assert updated.development_notes == ["admits she is afraid"]
    assert updated.state_changes == existing.state_changes
    assert text_defaults == [
        "warns Ivo",
        "admits she is afraid",
        "knowledge | knows the code | does not know | reads the letter",
    ]
    window.close()


def test_project_tree_character_filter_searches_profile_metadata(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    mara = project.add_character("Mara Venn")
    mara.role = "investigator"
    mara.primary_motivation = "Expose the council"
    project.update_character(mara.id, mara)
    project.add_character("Ivo")
    view = ProjectView()
    view.show_project(project, {}, {}, type("Count", (), {"count": 0, "complete": True})())
    view.filter_characters("council")
    group = view.topLevelItem(0).child(view.topLevelItem(0).childCount() - 1)
    assert group.childCount() == 2
    assert not group.child(0).isHidden()
    assert group.child(1).isHidden()
    view.close()


def test_character_context_menu_exposes_relationship_io_and_scene_search():
    action_ids = {
        action_id for _label, action_id in ProjectView.context_actions("character")
    }
    assert {
        "manage_relationships",
        "find_character_scenes",
        "open_associated_scene",
        "import_character",
        "export_character",
    } <= action_ids


def test_character_associated_scene_picker_uses_explicit_links_and_rechecks_them(application, tmp_path, monkeypatch):
    from app.project.model import SceneCharacterAssociation

    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    associated = project.add_scene("Scene", content="No mention")
    project.add_scene("Scene", content="Mara appears here")
    project.associate_character(associated.id, SceneCharacterAssociation(character.id))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    monkeypatch.setattr(window, "_selected_project_item", lambda: ("character", character.id))
    opened = []
    monkeypatch.setattr(window, "_open_project_document", lambda *args: opened.append(args))

    def choose(*args):
        labels = args[3]
        assert labels == [f"Scene [{associated.id}]"]
        return labels[0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    window.open_character_associated_scene()
    assert opened == [("scene", associated.id)]
    assert project.get_scene(associated.id).character_associations

    def remove_then_choose(*args):
        project.unassociate_character(associated.id, character.id)
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", remove_then_choose)
    window.open_character_associated_scene()
    assert opened == [("scene", associated.id)]
    window.close()


def test_profile_scene_navigation_preserves_staged_edits_and_returns(application, tmp_path, monkeypatch):
    from app.project.model import SceneCharacterAssociation

    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    scene = project.add_scene("Scene", content="original")
    project.add_scene("Mention only", content="Mara")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window.show()
    window._edit_character(character)
    dialog = window._active_character_dialog
    dialog.full_name.setText("Staged name")

    def choose(*args):
        assert args[3] == [f"Scene [{scene.id}]"]
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    dialog.scene_button.click()
    assert not dialog.isVisible()
    wait_until(lambda: any(binding.item_id == scene.id for binding in window._project_documents.values()), application)
    assert window.tabs.current_editor().toPlainText() == "original"
    assert project.get_character(character.id).full_name == "Mara"
    window._return_to_character_button.click()
    assert dialog.isVisible() and dialog.full_name.text() == "Staged name"
    dialog.scene_button.click()
    assert not dialog.isVisible()
    # Closing the window returns to the still-staged profile instead of losing it.
    window.close()
    assert dialog.isVisible() and dialog.full_name.text() == "Staged name"
    dialog._accept()
    wait_until(lambda: not window._project_busy, application)
    assert project.get_character(character.id).full_name == "Staged name"
    window.close()


def test_profile_save_refuses_changed_project_without_discarding_edits(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window._edit_character(character)
    dialog = window._active_character_dialog
    dialog.full_name.setText("Staged")
    changed = project.get_character(character.id)
    changed.full_name = "Changed elsewhere"
    project.update_character(character.id, changed)
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    dialog._accept()
    assert warnings and dialog.full_name.text() == "Staged"
    assert window._active_character_dialog is dialog
    assert project.get_character(character.id).full_name == "Changed elsewhere"
    dialog.reject()
    window.close()


def test_failed_profile_save_reopens_staged_edits(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window._edit_character(character)
    dialog = window._active_character_dialog
    dialog.full_name.setText("Staged")
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))

    def fail(*_args):
        raise ProjectError("Cannot save")

    monkeypatch.setattr(project, "update_character_with_relationships", fail)
    dialog._accept()
    wait_until(lambda: bool(warnings), application)
    assert dialog.isVisible() and dialog.full_name.text() == "Staged"
    assert project.get_character(character.id).full_name == "Mara"
    dialog.reject()
    window.close()


def test_profile_save_refuses_changed_directed_relationships(application, tmp_path, monkeypatch):
    from app.project.model import CharacterRelationship

    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    other = project.add_character("Alex")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window._edit_character(character)
    dialog = window._active_character_dialog
    dialog.full_name.setText("Staged")
    project.add_character_relationship(CharacterRelationship(
        "00000000-0000-4000-8000-000000000001", character.id, other.id,
    ))
    warnings = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: warnings.append(args))
    dialog._accept()
    assert warnings and dialog.full_name.text() == "Staged"
    assert len(project.manifest.character_relationships) == 1
    dialog.reject()
    window.close()


def test_profile_scene_selection_rechecks_association(application, tmp_path, monkeypatch):
    from app.project.model import SceneCharacterAssociation

    project = Project.create(tmp_path / "project", "Book")
    character = project.add_character("Mara")
    scene = project.add_scene("Scene", content="text")
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.project = project
    window._edit_character(character)
    dialog = window._active_character_dialog
    dialog.full_name.setText("Staged")
    opened = []
    monkeypatch.setattr(window, "_open_project_document", lambda *args: opened.append(args))

    def choose(*args):
        project.unassociate_character(scene.id, character.id)
        return args[3][0], True

    monkeypatch.setattr(QInputDialog, "getItem", choose)
    dialog.scene_button.click()
    assert not opened and dialog.isVisible() and dialog.full_name.text() == "Staged"
    dialog.reject()
    window.close()


@pytest.mark.parametrize("kind", ["", "project", "group", "character", "scene", "note", "chapter"])
def test_project_context_menu_offers_new_character(kind):
    assert ("New Character…", "new_character") in ProjectView.context_actions(kind)


def test_project_context_menu_creates_character(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args: ("Mara", True))
    window.project_view.context_action_requested.emit("new_character", "group", "")
    wait_until(lambda: any(c.full_name == "Mara" for c in project.manifest.characters) and not window._project_busy, application)
    assert Project.open(project.root).manifest.characters[0].full_name == "Mara"
    window.close()


def test_main_menus_group_project_and_ai_workflows(application, tmp_path):
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    menus = {action.text(): action.menu() for action in window.menuBar().actions()}
    project_actions = menus["Project"].actions()
    texts = [action.text() if not action.isSeparator() else "|" for action in project_actions]
    assert texts.index("Close Project") < texts.index("New Chapter…") < texts.index("Rename Selected…")
    assert texts.index("Move Items") < texts.index("Links") < texts.index("Revisions") < texts.index("Export") < texts.index("Project AI")
    for label in ("New Chapter…", "Rename Selected…"):
        assert texts[texts.index(label) - 1] == "|"
    grouped = {action.text(): action.menu() for action in project_actions if action.menu()}
    assert "Review Revision Snapshots…" in [action.text() for action in grouped["Revisions"].actions()]
    assert "Export Manuscript…" in [action.text() for action in grouped["Export"].actions()]
    assert "AI Project Setup…" in [action.text() for action in grouped["Project AI"].actions()]
    file_actions = [action.text() for action in menus["File"].actions()]
    assert file_actions.index("Inspect Recovery…") < file_actions.index("Quit")
    ai_actions = [action.text() if not action.isSeparator() else "|" for action in menus["AI"].actions()]
    assert ai_actions.index("Check Continuity Against Selected Notes") < ai_actions.index("Cancel Project Analysis") < ai_actions.index("Ollama Debug")
    assert not window._project_actions["New Character…"].isEnabled()
    assert "project" in window._project_actions["New Character…"].toolTip().lower()
    assert "selected" in window._project_actions["Move Scene Up"].toolTip().lower()
    project = Project.create(tmp_path / "novel", "Novel")
    window._project_opened(project)
    assert window._project_actions["New Character…"].isEnabled()
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


def test_export_workers_use_captured_scene_list(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Captured", content="saved text")
    captured = [ExportScene(scene.id, scene.title)]
    later = project.add_scene("Added later", content="not in snapshot")
    (project.root / later.path).unlink()
    unsaved = {scene.id: "unsaved text"}

    text_path = MainWindow._export_project_snapshot(
        project, [], captured, unsaved, tmp_path / "book.md", "markdown",
        False, None, True, True, "\n\n",
    )
    assert "unsaved text" in text_path.read_text(encoding="utf-8")
    assert "Added later" not in text_path.read_text(encoding="utf-8")

    pdf_path = MainWindow._compile_project_book_snapshot(
        project, "Book", [], captured, unsaved, tmp_path / "book.pdf", False,
    )
    pdf = QPdfDocument(application)
    pdf.load(str(pdf_path))
    text = " ".join(pdf.getAllText(page).text() for page in range(pdf.pageCount()))
    assert "unsaved text" in text
    assert "Added later" not in text
    assert project.read_scene(scene.id) == "saved text"
    pdf.close()


def test_export_workers_reject_project_source_destinations(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="keep scene")
    note = project.add_note("Note", content="keep note")
    scene_path = project.root / scene.path
    note_path = project.root / note.path
    hardlink = tmp_path / "linked.md"
    hardlink.hardlink_to(scene_path)
    symlink = tmp_path / "linked-note.md"
    symlink.symlink_to(note_path)
    for target in (scene_path, note_path, project.manifest_path, hardlink, symlink):
        before = target.read_bytes()
        with pytest.raises(ValueError, match="project source"):
            MainWindow._export_project_snapshot(project, [], [ExportScene(scene.id, scene.title)],
                {}, target, "markdown", True, None, True, True, "\n\n")
        with pytest.raises(ValueError, match="project source"):
            MainWindow._compile_project_book_snapshot(project, "Book", [],
                [ExportScene(scene.id, scene.title)], {}, target, True)
        assert target.read_bytes() == before


def test_export_does_not_replace_file_created_after_confirmation_check(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="manuscript")
    target = tmp_path / "export.md"
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: (str(target), "Markdown (*.md)"))
    def choose_options():
        target.write_text("created meanwhile", encoding="utf-8")
        return True, True, "\n\n"
    monkeypatch.setattr(window, "_ask_export_options", choose_options)
    errors = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: errors.append(_args[-1]))
    window.export_project()
    wait_until(lambda: bool(errors), application)
    assert target.read_text(encoding="utf-8") == "created meanwhile"
    window.close()


def test_export_uses_translated_plain_text_filter(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="manuscript")
    target = tmp_path / "export.txt"
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    monkeypatch.setattr(window, "tr", lambda source: "Звичайний текст (*.txt)" if source == "Plain text (*.txt)" else source)
    def choose_file(_parent, _title, _path, filters):
        assert "Звичайний текст (*.txt)" in filters
        return str(target), "Звичайний текст (*.txt)"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", choose_file)
    monkeypatch.setattr(window, "_ask_export_options", lambda: (True, True, "\n\n"))
    window.export_project()
    wait_until(target.exists, application)
    wait_until(lambda: not window._project_busy, application)
    text = target.read_text(encoding="utf-8")
    assert "Scene" in text and "manuscript" in text
    assert "# Scene" not in text
    window.close()


def test_export_ignores_unsaved_notes_and_unselected_scenes(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter")
    selected = project.add_scene("Selected", chapter_id=chapter.id, content="included")
    omitted = project.add_scene("Omitted", chapter_id=chapter.id, content="omitted")
    note = project.add_note("Note", content="reference")
    target = tmp_path / "export.md"
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.settings.ai_enabled = False
    window.settings.autosave_enabled = False
    window._project_opened(project)
    for kind, item in (("scene", omitted), ("note", note)):
        count = window.tabs.count()
        window._open_project_document(kind, item.id)
        wait_until(lambda: window.tabs.count() == count + 1, application)
        window.tabs.current_editor().setPlainText("unsaved excluded content")
    item = window.project_view.topLevelItem(0).child(0).child(0)
    assert item.data(0, Qt.ItemDataRole.UserRole + 1) == selected.id
    window.project_view.setCurrentItem(item)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: (str(target), "Markdown (*.md)"))
    monkeypatch.setattr(window, "_ask_export_options", lambda: (True, True, "\n\n"))
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: pytest.fail("excluded edits prompted for export"))
    window.export_project()
    wait_until(lambda: not window._project_busy, application)
    text = target.read_text(encoding="utf-8")
    assert "included" in text and "omitted" not in text and "unsaved excluded" not in text
    for editor in window._project_documents:
        editor.document_state.mark_saved()
    window.close()


@pytest.mark.parametrize("changed_dialog", ["destination", "overwrite", "options", "unsaved"])
def test_export_discards_selection_if_project_changes_during_dialog(
    application, tmp_path, monkeypatch, changed_dialog
):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="saved")
    target = tmp_path / "export.md"
    if changed_dialog == "overwrite":
        target.write_text("original", encoding="utf-8")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.settings.ai_enabled = False
    window.settings.autosave_enabled = False
    window._project_opened(project)
    if changed_dialog == "unsaved":
        window._open_project_document("scene", scene.id)
        wait_until(lambda: window.tabs.count() == 2, application)
        editor = window.tabs.current_editor()
        editor.setPlainText("unsaved")
    def change_generation(stage):
        if changed_dialog == stage:
            window._project_generation += 1
    def choose_file(*_args):
        change_generation("destination")
        return str(target), "Markdown (*.md)"
    def confirm(*_args):
        change_generation("overwrite" if target.exists() else "unsaved")
        return QMessageBox.StandardButton.Yes
    def options():
        change_generation("options")
        return True, True, "\n\n"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", choose_file)
    monkeypatch.setattr(QMessageBox, "question", confirm)
    monkeypatch.setattr(window, "_ask_export_options", options)
    monkeypatch.setattr(window.thread_pool, "start", lambda *_args: pytest.fail("stale export started"))
    window.export_project()
    if changed_dialog == "overwrite":
        assert target.read_text(encoding="utf-8") == "original"
    else:
        assert not target.exists()
    if changed_dialog == "unsaved":
        editor.document_state.mark_saved()
    window.close()


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


def test_revision_history_previews_all_snapshot_content_in_bounded_pages(application, tmp_path):
    store = RevisionStore(tmp_path / "revisions")
    snapshot = store.create("Draft", structure={}, scene_order=["scene"],
                            scene_titles={"scene": "Opening"},
                            documents={"scene": "draft " + "x" * 40000, "note": "unshown"})
    dialog = RevisionHistoryDialog()
    dialog.set_snapshots((snapshot,), ())
    dialog.snapshots.item(0).setSelected(True)
    preview = dialog.details.toPlainText()
    assert "Opening [scene]" in preview and "draft " in preview
    assert "unshown" not in preview
    assert not dialog.previous_page.isEnabled() and dialog.next_page.isEnabled()
    assert dialog.details.isReadOnly()
    dialog.next_page.click()
    assert "unshown" in dialog.details.toPlainText()
    assert dialog.previous_page.isEnabled() and not dialog.next_page.isEnabled()
    dialog.previous_page.click()
    assert dialog.details.toPlainText() == preview
    assert snapshot.documents["note"] == "unshown"
    dialog.close()


def test_stale_revision_comparison_does_not_replace_selected_preview(application, tmp_path):
    project = Project.create(tmp_path / "novel", "Novel")
    store = RevisionStore(project.root / ".utexteditor" / "revisions")
    snapshot = store.create("Draft", structure={}, scene_order=["scene"],
                            scene_titles={"scene": "Opening"}, documents={"scene": "Preview"})
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    dialog = RevisionHistoryDialog(window)
    dialog.show()
    dialog.set_snapshots((snapshot,), ())
    old_generation = dialog.selection_generation
    dialog.snapshots.item(0).setSelected(True)
    window._revision_comparison_finished(dialog, project, RevisionComparison(()), old_generation)
    assert "Preview" in dialog.details.toPlainText()
    dialog.close()
    window.close()


def test_revision_history_deletion_requires_confirmation(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Opening", content="Manuscript")
    store = RevisionStore(project.root / ".utexteditor" / "revisions")
    snapshot = store.create("Draft", structure={}, scene_order=[scene.id],
                            scene_titles={scene.id: "Opening"}, documents={scene.id: "Snapshot"})
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.review_revision_snapshots()
    dialog = window._revision_history_dialog
    wait_until(lambda: dialog.snapshots.count() == 1, application)
    dialog.snapshots.item(0).setSelected(True)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: QMessageBox.StandardButton.Cancel)
    dialog.delete_button.click()
    assert snapshot.snapshot_path.exists()
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args: QMessageBox.StandardButton.Yes)
    dialog.delete_button.click()
    wait_until(lambda: dialog.snapshots.count() == 0, application)
    assert not snapshot.snapshot_path.exists()
    assert (project.root / scene.path).read_text(encoding="utf-8") == "Manuscript"
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


def test_revision_history_dialog_labels_chapter_changes(application):
    dialog = RevisionHistoryDialog()
    dialog.show_comparison(RevisionComparison((
        SceneChange("chapter-id", "title-changed", "Old", "New", item_type="chapter"),
    )))
    assert "Chapter Title Changed: New" in dialog.details.toPlainText()
    dialog.close()


def test_revision_history_dialog_shows_scene_chapter_destination(application):
    dialog = RevisionHistoryDialog()
    dialog.show_comparison(RevisionComparison((
        SceneChange("scene-id", "chapter-changed", "Opening", "Opening",
                    old_chapter_id="chapter-id", new_chapter_id=None),
    )))
    assert "Chapter Changed: Opening" in dialog.details.toPlainText()
    assert "Chapter: chapter-id → Ungrouped" in dialog.details.toPlainText()
    dialog.close()


def test_revision_history_dialog_displays_path_and_project_title_changes(application):
    dialog = RevisionHistoryDialog()
    dialog.show_comparison(RevisionComparison((
        SceneChange("project", "title-changed", "Old", "New", item_type="project"),
        SceneChange("scene", "path-changed", "Opening", "Opening", old_path="old.txt", new_path="new.txt"),
    )))
    text = dialog.details.toPlainText()
    assert "Project Title Changed: New" in text and "Title: Old → New" in text
    assert "Path Changed: Opening" in text and "Path: old.txt → new.txt" in text
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
    monkeypatch.setattr("app.ui.main_window.ProjectTranslationReviewDialog.exec", lambda _dialog: QDialog.DialogCode.Accepted)
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
    project_ai = next(action.menu() for action in project_menu.actions() if action.text() == "Project AI")
    menu_actions = {action.text() for action in project_ai.actions()}
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
    assert any(item.name == "Project translation" and item.state == "completed" for item in window.ai_activity.activities)
    editor.document_state.mark_saved()
    window.close()


@pytest.mark.parametrize("decision", ["cancel", "edit"])
def test_project_translation_review_cancels_or_discards_changed_buffer(application, tmp_path, monkeypatch, decision):
    project = Project.create(tmp_path / "review-project", "Novel")
    scene = project.add_scene("Opening", content="Original scene")
    duplicate = project.add_scene("Opening", content="Another scene")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window.settings.autosave_enabled = False
    monkeypatch.setattr(QMessageBox, "question", lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "warning", lambda *_args, **_kwargs: QMessageBox.StandardButton.Ok)
    monkeypatch.setattr(window.provider, "generate_private", lambda *_args, **_kwargs: "Translated")
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2, application)
    editor = window.tabs.current_editor()
    editor.setPlainText("Unsaved source")
    seen = []

    def review(dialog):
        seen.extend(dialog.items)
        if decision == "edit":
            editor.setPlainText("Changed during review")
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr("app.ui.main_window.ProjectTranslationReviewDialog.exec", review)
    window.translate_project_to_ukrainian()
    wait_until(lambda: bool(seen) and not window._project_busy, application)
    assert any(original == "Unsaved source" and translated == "Translated" for _, original, translated in seen)
    assert any(scene.id in label and original == "Unsaved source" for label, original, _ in seen)
    assert any(duplicate.id in label and original == "Another scene" for label, original, _ in seen)
    assert project.read_scene(scene.id) == "Original scene"
    assert project.read_scene(duplicate.id) == "Another scene"
    assert project.manifest.title == "Novel"
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
    monkeypatch.setattr(MainWindow, "_ask_pdf_options", lambda _self, title: (title, "An Author", "A4", False, False, {scene.id}))
    project = Project.create(tmp_path / "novel", "Novel")
    chapter = project.add_chapter("Chapter One")
    scene = project.add_scene("Opening", chapter_id=chapter.id, content="saved text")
    omitted = project.add_scene("Omitted", chapter_id=chapter.id, content="not exported")
    (project.root / omitted.path).unlink()
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
    assert "An Author" in content
    assert "Opening" not in content
    assert "Chapter One" not in content
    assert "Omitted" not in content and "not exported" not in content
    assert pdf.pagePointSize(0).width() > 590
    assert "\r\nsaved text\r\n" not in content
    assert project.read_scene(scene.id) == "saved text"
    editor.document_state.mark_saved()
    window.close()


def test_pdf_selection_is_discarded_if_project_changes_during_options(application, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="text")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    def stale_options(_title):
        window._project_generation += 1
        return "Novel", "", "A5", True, {scene.id}
    monkeypatch.setattr(window, "_ask_pdf_options", stale_options)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *_args: pytest.fail("stale selection used"))
    window.compile_project_book()
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
            return '{"findings": []}'

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

    assert "No continuity findings" in result
    assert "scene text" in provider.prompt
    assert "selected reference" in provider.prompt
    assert "private unrelated note" not in provider.prompt
    assert other.id not in provider.prompt


def test_project_analysis_includes_only_associated_character_context(tmp_path):
    from app.project import CharacterKnowledge, SceneCharacterAssociation

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="scene text")
    selected = project.add_character("Mara")
    selected.primary_motivation = "Expose the council"
    selected.knowledge = [CharacterKnowledge("does_not_know", "The witness survived")]
    project.update_character(selected.id, selected)
    unrelated = project.add_character("Ivo")
    unrelated.primary_motivation = "Irrelevant plan"
    project.update_character(unrelated.id, unrelated)
    project.associate_character(scene.id, SceneCharacterAssociation(selected.id))

    class FakeProvider:
        prompt = None

        def generate_private(self, prompt, **_options):
            self.prompt = prompt
            return '{"findings": []}'

    provider = FakeProvider()
    MainWindow._run_project_analysis(provider, project, "continuity", scene.id, (), {}, 4000, "review", 100, 0.2)
    assert "Expose the council" in provider.prompt
    assert "The witness survived" in provider.prompt
    assert "Irrelevant plan" not in provider.prompt


def test_project_continuity_rejects_evidence_truncated_from_request(tmp_path):
    import json

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="start " + "x" * 300 + " hidden evidence")

    class FakeProvider:
        def generate_private(self, _prompt, **_options):
            return json.dumps({"findings": [{
                "confidence": "possible", "scene_id": scene.id, "character_ids": [],
                "concern": "Check this", "suggestion": "Review",
                "evidence": {"source_id": scene.id, "quote": "hidden evidence"},
            }]})

    with pytest.raises(ValueError, match="evidence"):
        MainWindow._run_project_analysis(FakeProvider(), project, "continuity", scene.id, (), {}, 120, "review", 100, 0.2)


def test_project_scene_completion_receives_notes_and_associated_characters(application, tmp_path, monkeypatch):
    from app.project import SceneCharacterAssociation
    from PySide6.QtGui import QTextCursor

    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="The beginning")
    note = project.add_note("World", content="A hidden door")
    character = project.add_character("Mara")
    character.primary_motivation = "Find the key"
    project.update_character(character.id, character)
    project.associate_character(scene.id, SceneCharacterAssociation(character.id))
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: any(b.item_id == scene.id for b in window._project_documents.values()), application)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window.settings.ai_enabled = True
    window.settings.completion_enabled = True
    received = []
    monkeypatch.setattr(window.completion_service, "complete", lambda context, language, **kw: (received.append(context) or " continues"))
    window.request_completion()
    wait_until(lambda: bool(received), application)
    assert "Find the key" in received[0]
    assert "A hidden door" in received[0]
    assert "The beginning" in received[0]
    window.close()


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
