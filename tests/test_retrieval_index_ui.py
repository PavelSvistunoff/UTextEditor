import os
from threading import Event, get_ident
from time import monotonic
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")
from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.project import Project
from app.project.rag_index import LexicalIndex, fts5_available
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.retrieval_index_dialog import RetrievalIndexDialog


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def wait_until(predicate, application):
    deadline = monotonic() + 5
    while not predicate():
        application.processEvents()
        if monotonic() > deadline:
            pytest.fail("Retrieval UI did not reach the expected state")
        QTest.qWait(5)


@pytest.fixture
def maintenance(application, tmp_path):
    if not fts5_available():
        pytest.skip("Runtime SQLite has no FTS5")
    project = Project.create(tmp_path / "novel", "Novel")
    project.add_scene("Scene", content="saved manuscript")
    current = [True]
    dialog = RetrievalIndexDialog(project, tmp_path / "cache", is_current=lambda: current[0])
    dialog.show()
    wait_until(lambda: "No index" in dialog.status.toPlainText() and dialog._worker is None, application)
    try:
        yield project, dialog, current
    finally:
        dialog.close()
        QThreadPool.globalInstance().waitForDone(5000)
        application.processEvents()


def test_controls_refresh_rebuild_and_delete_in_workers(application, maintenance, monkeypatch):
    project, dialog, _current = maintenance
    gui_thread = get_ident()
    thread_ids = []
    original = LexicalIndex._write_source

    def record_thread(self, connection, source, chunks):
        thread_ids.append(get_ident())
        original(self, connection, source, chunks)

    monkeypatch.setattr(LexicalIndex, "_write_source", record_thread)
    dialog.refresh_button.click()
    wait_until(lambda: dialog._worker is None, application)
    assert dialog.status.toPlainText().startswith("Ready:")
    assert thread_ids and all(value != gui_thread for value in thread_ids)
    index = LexicalIndex(dialog.cache_root, project.root, project.manifest.project_id)
    original_generation = index.status().generation
    index.path.write_bytes(b"damaged")
    dialog.status_button.click()
    wait_until(lambda: dialog._worker is None, application)
    assert "could not be read" in dialog.status.toPlainText()
    dialog.rebuild_button.click()
    wait_until(lambda: dialog._worker is None, application)
    assert index.status().generation != original_generation
    dialog.delete_button.click()
    wait_until(lambda: dialog._worker is None, application)
    assert "No index" in dialog.status.toPlainText()
    assert project.read_scene(next(project.iter_scenes()).id) == "saved manuscript"


@pytest.mark.parametrize("action", ["cancel", "stale", "stale_error", "close"])
def test_blocked_work_keeps_gui_responsive_and_discards_obsolete_results(
    application, maintenance, monkeypatch, action,
):
    project, dialog, current = maintenance
    entered, release = Event(), Event()
    original_write = LexicalIndex._write_source

    def paused_write(self, connection, source, chunks):
        original_write(self, connection, source, chunks)
        entered.set()
        if not release.wait(5):
            raise RuntimeError("Test did not release index writer")
        if action == "stale_error":
            raise RuntimeError("obsolete failure")

    monkeypatch.setattr(LexicalIndex, "_write_source", paused_write)
    ticks = []
    dialog.refresh_button.click()
    try:
        wait_until(entered.is_set, application)
        QTimer.singleShot(0, lambda: ticks.append("GUI callback ran"))
        wait_until(lambda: bool(ticks), application)
        assert not dialog.refresh_button.isEnabled() and dialog.cancel_button.isEnabled()
        if action == "cancel":
            dialog.cancel_button.click()
        elif action == "close":
            dialog.close()
        else:
            current[0] = False
    finally:
        release.set()
    wait_until(lambda: dialog._worker is None, application)
    index = LexicalIndex(dialog.cache_root, project.root, project.manifest.project_id)
    assert index.status().state == "missing"
    assert "obsolete failure" not in dialog.status.toPlainText()
    if action in {"stale", "stale_error"}:
        assert "Project changed" in dialog.status.toPlainText()
        assert not dialog.refresh_button.isEnabled()


def test_unavailable_fts_is_visible_without_disabling_normal_ui(application, maintenance, monkeypatch):
    project, dialog, _current = maintenance
    monkeypatch.setattr("app.project.rag_index.fts5_available", lambda: False)
    dialog.status_button.click()
    wait_until(lambda: dialog._worker is None, application)
    assert "FTS5 is unavailable" in dialog.status.toPlainText()
    assert dialog.delete_button.isEnabled()
    assert project.read_scene(next(project.iter_scenes()).id) == "saved manuscript"


def test_main_window_exposes_local_controls_with_ai_disabled_and_preserves_dirty_buffer(
    application, tmp_path, monkeypatch,
):
    settings_path = tmp_path / "settings.yaml"
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: settings_path))
    AppSettings(ai_enabled=False, ui_language="en").save(settings_path)
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="saved manuscript")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=False):
        window = MainWindow()
    try:
        window._project_opened(project)
        wait_until(lambda: not window._project_busy, application)
        assert window._project_actions["Retrieval Index…"].isEnabled()
        window._open_project_document("scene", scene.id)
        wait_until(lambda: window.tabs.count() == 2, application)
        editor = window.tabs.current_editor()
        editor.setPlainText("UNSAVED UNIQUE TEXT")
        revision = editor.revision
        window.show_retrieval_index()
        dialog = window._retrieval_index_dialog
        wait_until(lambda: "No index" in dialog.status.toPlainText() and dialog._worker is None, application)
        dialog.refresh_button.click()
        wait_until(lambda: dialog._worker is None, application)
        index = LexicalIndex(settings_path.parent, project.root, project.manifest.project_id)
        assert index.search_terms(("saved",))
        assert not index.search_terms(("UNSAVED",))
        assert editor.toPlainText() == "UNSAVED UNIQUE TEXT" and editor.revision == revision
        assert editor.document_state.dirty
        dialog.close()
        editor.document_state.mark_saved(editor.toPlainText())
    finally:
        for position in range(window.tabs.count()):
            window.tabs.widget(position).document_state.mark_saved()
        window.close()
        QThreadPool.globalInstance().waitForDone(5000)
