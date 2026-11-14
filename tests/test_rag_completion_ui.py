"""Offline manual RAG completion: exact review, stale state and acceptance."""
import os
from time import monotonic
from unittest.mock import patch

import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from app.project import Project
from app.project.rag_index import LexicalIndex, fts5_available
from app.project.rag_sources import capture_project_sources
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.rag_completion import RAGCompletionDialog, request_rag_completion


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def wait(predicate, application):
    deadline = monotonic() + 8
    while not predicate():
        application.processEvents()
        assert monotonic() < deadline, "RAG completion did not finish"
        QTest.qWait(5)


@pytest.fixture
def scene_window(application, tmp_path, monkeypatch):
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: tmp_path / "cache/settings.yaml"))
    project = Project.create(tmp_path / "novel", "Novel")
    scene = project.add_scene("Scene", content="The hidden door was there")
    note = project.add_note("Door", content="The hidden door leads into the garden.")
    with patch("app.ui.main_window.OllamaClient.check_connection", return_value=True):
        window = MainWindow()
    window.settings.automatic_spellcheck = False
    window.settings.completion_debounce_ms = 100000
    window.settings.autosave_enabled = False
    window.settings.ollama_context_length = 32768
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait(lambda: any(item.item_id == scene.id for item in window._project_documents.values()), application)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    if fts5_available():
        LexicalIndex(tmp_path / "cache", project.root, project.manifest.project_id).refresh(capture_project_sources(project))
    yield window, project, scene, note, editor
    window._completion_timer.stop()
    QThreadPool.globalInstance().waitForDone(5000)
    application.processEvents()
    for tab in (window.tabs.widget(i) for i in range(window.tabs.count())):
        tab.document_state.mark_saved()
        tab.document().setModified(False)
    window.close()


def test_review_rebuild_sends_exact_prompt_and_accepts_with_undo(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    reviews, requests = [], []
    def review(dialog):
        reviews.append(dialog.context.toPlainText())
        assert dialog.sources.accessibleName() == "Sources to exclude"
        if len(reviews) == 1:
            item = next(dialog.sources.item(i) for i in range(dialog.sources.count())
                        if dialog.sources.item(i).data(Qt.ItemDataRole.UserRole) == note.id)
            item.setCheckState(Qt.CheckState.Checked)
            assert not dialog.send_button.isEnabled()
            return dialog.REBUILD
        assert '"reason":"excluded"' in reviews[-1]
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (requests.append((prompt, kw)) or " beyond"))
    request_rag_completion(window)
    wait(lambda: bool(requests) and window._completion_worker is None, application)
    assert requests[0][0] == reviews[-1].split("\n\n--- SOURCE MANIFEST")[0]
    assert requests[0][1]["require_full_context"] is True
    assert requests[0][1]["maximum_tokens"] == window.settings.maximum_suggestion_length
    original = editor.toPlainText()
    assert original == project.read_scene(scene.id)
    window.accept_completion()
    assert editor.toPlainText() == original + " beyond"
    editor.undo()
    assert editor.toPlainText() == original


@pytest.mark.parametrize("change", ["disk", "buffer", "settings", "tab", "project", "cancel"])
def test_review_changes_prevent_dispatch(scene_window, monkeypatch, application, change):
    window, project, scene, note, editor = scene_window
    requests, reviewed = [], []
    def review(dialog):
        reviewed.append(True)
        if change == "disk":
            (project.root / note.path).write_text("changed", encoding="utf-8")
        elif change == "buffer":
            editor.insertPlainText(" changed")
        elif change == "settings":
            window._settings_generation += 1
        elif change == "tab":
            window.tabs.new_document()
        elif change == "project":
            window._project_generation += 1
        else:
            return QDialog.DialogCode.Rejected
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: requests.append(a))
    request_rag_completion(window)
    wait(lambda: bool(reviewed) and window._completion_worker is None, application)
    assert not requests


@pytest.mark.parametrize("failure", [False, True])
def test_disk_change_during_generation_discards_success_and_failure(scene_window, monkeypatch, application, failure):
    window, project, scene, note, editor = scene_window
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    def generate(*args, **kwargs):
        (project.root / note.path).write_text("changed externally", encoding="utf-8")
        if failure:
            raise RuntimeError("obsolete provider failure")
        return " must not appear"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    request_rag_completion(window)
    wait(lambda: window._completion_worker is None, application)
    window.accept_completion()
    assert editor.toPlainText() == project.read_scene(scene.id)
    assert "obsolete provider failure" not in window.statusBar().currentMessage()


def test_requires_explicit_window_and_project(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: pytest.fail("No review expected"))
    window.settings.ollama_context_length = 0
    request_rag_completion(window)
    assert "explicit Ollama token window" in window.statusBar().currentMessage()
    window._project_documents.pop(editor)
    request_rag_completion(window)
    assert "open project scene" in window.statusBar().currentMessage()


def test_unsaved_note_overlay_is_reviewed_and_sent(scene_window, monkeypatch, application):
    if not fts5_available():
        pytest.skip("Runtime SQLite has no FTS5")
    window, project, scene, note, editor = scene_window
    window._open_project_document("note", note.id)
    wait(lambda: window.tabs.current_editor() is not editor, application)
    note_editor = window.tabs.current_editor()
    note_editor.setPlainText("The hidden door has an unsaved emerald lock.")
    window.tabs.setCurrentWidget(editor)
    editor.moveCursor(QTextCursor.MoveOperation.End)
    reviewed, requests = [], []
    def review(dialog):
        reviewed.append(dialog.context.toPlainText())
        assert "unsaved emerald lock" in reviewed[0]
        assert f'"buffer_revision":{note_editor.revision}' in reviewed[0]
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (requests.append(prompt) or " beyond"))
    request_rag_completion(window)
    wait(lambda: bool(requests) and window._completion_worker is None, application)
    assert "unsaved emerald lock" in requests[0]
    assert "unsaved emerald lock" not in project.read_note(note.id)
    window.reject_completion()
    assert editor.toPlainText() == project.read_scene(scene.id)


@pytest.mark.parametrize("index_state", ["missing", "unavailable", "no_hits"])
def test_coverage_state_visible_without_blocking_review(scene_window, monkeypatch, application, index_state):
    from app.project.rag_index import IndexUnavailable
    window, project, scene, note, editor = scene_window
    if index_state == "missing":
        LexicalIndex(AppSettings._default_settings_path().parent, project.root, project.manifest.project_id).delete()
    elif index_state == "unavailable":
        def unavailable(*a, **kw):
            raise IndexUnavailable("FTS5 unavailable")
        monkeypatch.setattr(LexicalIndex, "lookup_capture", unavailable)
    else:
        if not fts5_available():
            pytest.skip("Runtime SQLite has no FTS5")
        (project.root / note.path).write_text("Unrelated vocabulary zebra", encoding="utf-8")
    reviewed = []
    def review(dialog):
        reviewed.append(dialog.context.toPlainText())
        assert ('"retrieval_state":"unavailable"' if index_state != "no_hits"
                else '"retrieval_state":"no_hits"') in reviewed[0]
        return QDialog.DialogCode.Rejected
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    request_rag_completion(window)
    wait(lambda: bool(reviewed) and window._completion_worker is None, application)


@pytest.mark.parametrize("change", ["cancel", "settings", "tab", "project", "buffer"])
@pytest.mark.parametrize("failure", [False, True])
def test_generation_changes_discard_result(scene_window, monkeypatch, application, change, failure):
    from threading import Event
    window, project, scene, note, editor = scene_window
    entered, release = Event(), Event()
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    def generate(*args, **kw):
        entered.set()
        assert release.wait(5)
        if failure:
            raise RuntimeError("obsolete failure")
        return " obsolete success"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    request_rag_completion(window)
    try:
        wait(entered.is_set, application)
        if change == "cancel":
            window._cancel_activity_completion(window._completion_worker)
        elif change == "settings":
            window._settings_generation += 1
        elif change == "tab":
            window.tabs.new_document()
        elif change == "project":
            window._project_generation += 1
        else:
            editor.insertPlainText(" edited")
    finally:
        release.set()
    wait(lambda: window._completion_worker is None, application)
    assert "obsolete failure" not in window.statusBar().currentMessage()
    assert "obsolete success" not in editor.toPlainText()


@pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") != "cocoa", reason="Direct macOS native walkthrough only")
def test_native_keyboard_review_cancel_send_accept(scene_window, monkeypatch, application, tmp_path):
    """Exercise real Cocoa dialogs and editor shortcuts, with an offline provider."""
    from PySide6.QtCore import QTimer
    window, project, scene, note, editor = scene_window
    window.show()
    window.activateWindow()
    requests, visited = [], []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (requests.append(prompt) or " beyond"))
    original = RAGCompletionDialog.exec
    errors = []
    def walkthrough(dialog):
        def keys():
            try:
                dialog.context.setFocus()
                QTest.keyClick(dialog.context, Qt.Key.Key_Tab)
                assert dialog.sources.hasFocus()
                QTest.keyClick(dialog.sources, Qt.Key.Key_Space)
                assert not dialog.send_button.isEnabled()
                QTest.keyClick(dialog.sources, Qt.Key.Key_Space)
                assert dialog.send_button.isEnabled()
                visited.append(True)
                if len(visited) == 1:
                    QTest.keyClick(dialog, Qt.Key.Key_Escape)
                else:
                    dialog.send_button.setFocus()
                    QTest.keyClick(dialog.send_button, Qt.Key.Key_Return)
            except BaseException as error:
                errors.append(error)
                dialog.reject()
        QTimer.singleShot(100, keys)
        return original(dialog)
    monkeypatch.setattr(RAGCompletionDialog, "exec", walkthrough)
    request_rag_completion(window)
    wait(lambda: (bool(errors) or len(visited) == 1) and window._completion_worker is None, application)
    assert not errors
    assert not requests
    request_rag_completion(window)
    wait(lambda: (bool(errors) or bool(requests)) and window._completion_worker is None, application)
    assert not errors
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    assert editor.toPlainText().endswith(" beyond")
    editor.undo()
    assert editor.toPlainText() == project.read_scene(scene.id)
