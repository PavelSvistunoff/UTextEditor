"""Automatic inline retrieval stays serialized and never writes before Tab."""

from threading import Event
from time import monotonic
import os

import pytest
from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QMessageBox

from test_rag_completion_ui import application, scene_window
from app.ui.rag_completion import RAGCompletionDialog


def wait(predicate, application):
    deadline = monotonic() + 8
    while not predicate():
        application.processEvents()
        assert monotonic() < deadline, "Automatic retrieval did not finish"
        loop = QEventLoop()
        QTimer.singleShot(5, loop.quit)
        loop.exec()  # Release the GIL and dispatch native file notifications.


def enable(window):
    window.settings.automatic_retrieval = True
    window.settings.ai_context_consent_host = window.provider.host


def test_auto_exact_inspection_acceptance_rejection_and_undo(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    calls, reviews = [], []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (calls.append((prompt, kw)) or " beyond"))
    window.request_completion(automatic=True)
    wait(lambda: window._inline_retrieval.active is None, application)
    assert editor.has_completion, (window.ai_status, window.statusBar().currentMessage(), calls)
    assert editor.toPlainText() == project.read_scene(scene.id)
    def inspect(dialog):
        reviews.append(dialog.context.toPlainText())
        assert dialog.send_button.isHidden()
        return QDialog.DialogCode.Rejected
    monkeypatch.setattr(RAGCompletionDialog, "exec", inspect)
    window._inline_retrieval.inspect()
    assert reviews[0].split("\n\n--- SOURCE MANIFEST")[0] == calls[0][0]
    assert calls[0][1]["require_full_context"] is True
    original = editor.toPlainText()
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    wait(lambda: editor.toPlainText() != original, application)
    assert editor.toPlainText() == original + " beyond"
    editor.undo()
    assert editor.toPlainText() == original
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    assert not editor.has_completion and editor.toPlainText() == original


def test_rapid_typing_coalesces_until_running_provider_finishes(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    entered, release = Event(), Event()
    calls = []
    def generate(prompt, **kwargs):
        calls.append(prompt)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return " beyond"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    window.request_completion(automatic=True)
    wait(entered.is_set, application)
    try:
        for word in (" garden", " copper", " midnight"):
            editor.insertPlainText(word)
            window.request_completion(automatic=True)
        assert len(calls) == 1
        assert window._inline_retrieval.pending == window._completion_generation
    finally:
        release.set()
    wait(lambda: len(calls) == 2 and editor.has_completion, application)
    assert "midnight" in calls[-1]
    assert window._inline_retrieval.pending is None


@pytest.mark.parametrize("change", ["edit", "cursor", "selection", "tab", "settings", "project", "disk", "cancel"])
def test_late_generation_is_discarded(scene_window, monkeypatch, application, change):
    window, project, scene, note, editor = scene_window
    enable(window)
    entered, release = Event(), Event()
    def generate(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return " obsolete"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    window.request_completion(automatic=True)
    wait(entered.is_set, application)
    try:
        if change == "edit":
            editor.insertPlainText(" author")
        elif change == "cursor":
            editor.moveCursor(QTextCursor.MoveOperation.Start)
        elif change == "selection":
            editor.selectAll()
        elif change == "tab":
            window.tabs.new_document()
        elif change == "settings":
            window._settings_generation += 1
        elif change == "project":
            window._project_generation += 1
        elif change == "disk":
            (project.root / note.path).write_text("Changed source")
        else:
            window._cancel_activity_completion(window._completion_worker)
    finally:
        release.set()
    wait(lambda: window._inline_retrieval.active is None, application)
    assert not editor.has_completion
    assert "obsolete" not in editor.toPlainText()


def test_remote_embedding_decline_is_nonmodal_and_session_scoped(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    window.settings.rag_embeddings_enabled = True
    window.settings.embedding_host = "http://remote.invalid:11434"
    calls = []
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: (calls.append(True) or " beyond"))
    monkeypatch.setattr("app.ui.inline_retrieval.OllamaClient.embedding_identity",
                        lambda *_: pytest.fail("No embedding request before consent"))
    window.request_completion(automatic=True)
    dialog = window._inline_retrieval.disclosure
    assert dialog is not None and not dialog.isModal()
    dialog.done(QMessageBox.StandardButton.No)
    wait(lambda: editor.has_completion, application)
    window.request_completion(automatic=True)
    wait(lambda: len(calls) == 2 and editor.has_completion, application)
    assert window._inline_retrieval.disclosure is None


def test_inspection_exclusions_invalidate_and_apply_to_next_request(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    calls = []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (calls.append(prompt) or " beyond"))
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    def exclude(dialog):
        for i in range(dialog.sources.count()):
            item = dialog.sources.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == note.id:
                item.setCheckState(Qt.CheckState.Checked)
        return dialog.REBUILD
    monkeypatch.setattr(RAGCompletionDialog, "exec", exclude)
    window._inline_retrieval.inspect()
    assert not editor.has_completion
    window.request_completion(automatic=True)
    wait(lambda: len(calls) == 2 and editor.has_completion, application)
    assert "leads into the garden" not in calls[-1]


def test_saved_source_change_clears_displayed_suggestion(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: " beyond")
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    (project.root / note.path).write_text("Changed after display")
    wait(lambda: not editor.has_completion, application)


def test_unknown_window_skips_without_dispatch(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    enable(window)
    window.settings.ollama_context_length = 0
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: pytest.fail("Unknown budget"))
    window.request_completion(automatic=True)
    assert "explicit Ollama token window" in window.statusBar().currentMessage()


@pytest.mark.parametrize("mode", ["standalone", "manual", "disabled", "project_context_disabled"])
def test_non_opted_paths_keep_ordinary_completion(scene_window, monkeypatch, application, mode):
    window, project, scene, note, editor = scene_window
    enable(window)
    if mode == "standalone":
        editor = window.tabs.new_document()
        editor.insertPlainText("The ordinary paragraph")
    elif mode == "disabled":
        window.settings.automatic_retrieval = False
    elif mode == "project_context_disabled":
        window.settings.automatic_project_context = False
    calls = []
    monkeypatch.setattr(window.provider, "complete", lambda *a, **kw: (calls.append(a) or " beyond"))
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: pytest.fail("Must keep ordinary path"))
    window.request_completion(automatic=mode != "manual")
    wait(lambda: editor.has_completion, application)
    assert len(calls) == 1


def test_settings_controls_round_trip_and_reset(application):
    from app.settings.settings import AppSettings
    from app.ui.settings_dialog import SettingsDialog
    settings = AppSettings()
    dialog = SettingsDialog(settings)
    dialog.automatic_retrieval.setChecked(True)
    dialog.accept()
    assert settings.automatic_retrieval
    dialog = SettingsDialog(settings)
    dialog._reset_to_defaults()
    assert not dialog.automatic_retrieval.isChecked()
    dialog.reject()


def test_background_verification_cannot_clear_a_new_ordinary_ghost(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: " beyond")
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    editor.clear_completion()
    window._completion_generation += 1
    editor.show_completion(" ordinary", editor.revision, editor.textCursor().position())
    window._inline_retrieval.verify_displayed(accept=False)
    assert editor.has_completion
    assert editor._ghost_text == " ordinary"


def test_buffer_capture_limit_skips_before_copying_text(scene_window, monkeypatch):
    from app.ui.inline_retrieval import MAX_SOURCE_CHARACTERS
    window, project, scene, note, editor = scene_window
    enable(window)
    monkeypatch.setattr(editor.document(), "characterCount", lambda: MAX_SOURCE_CHARACTERS + 1)
    monkeypatch.setattr(editor, "toPlainText", lambda: pytest.fail("Oversized buffer must not be copied"))
    window.request_completion(automatic=True)
    assert "exceed automatic capture limits" in window.statusBar().currentMessage()


def test_remote_embedding_approval_rechecks_on_settings_change(scene_window, monkeypatch, application):
    from test_rag_embeddings import FakeEmbeddings
    window, project, scene, note, editor = scene_window
    enable(window)
    window.settings.rag_embeddings_enabled = True
    window.settings.embedding_host = "http://remote.invalid"
    fake = FakeEmbeddings()
    fake.host, fake.model = "http://remote.invalid", "fake"
    created = []
    def provider(*args, **kwargs):
        created.append((args, kwargs))
        return fake
    monkeypatch.setattr("app.ui.inline_retrieval.OllamaClient", provider)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: " beyond")
    window.request_completion(automatic=True)
    assert not created
    window._inline_retrieval.disclosure.done(QMessageBox.StandardButton.Yes)
    wait(lambda: window._inline_retrieval.active is None, application)
    window.request_completion(automatic=True)
    wait(lambda: bool(created) and window._inline_retrieval.active is None, application)
    assert created[0][0] == ("http://remote.invalid", window.settings.embedding_model)
    assert created[0][1]["timeout"] == .25
    assert fake.calls == []  # Source vectors are absent: disclosed lexical fallback.
    window._settings_generation += 1
    window.request_completion(automatic=True)
    assert window._inline_retrieval.disclosure is not None
    window._inline_retrieval.disclosure.done(QMessageBox.StandardButton.No)


def test_escape_rejects_while_tab_verification_is_pending(scene_window, monkeypatch, application):
    from app.project.rag_sources import ProjectSourceCapture
    window, project, scene, note, editor = scene_window
    enable(window)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: " beyond")
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion and window._inline_retrieval.active is None, application)
    original = editor.toPlainText()
    entered, release = Event(), Event()
    verify = ProjectSourceCapture.verify_current
    def blocked(self, *args, **kwargs):
        entered.set()
        assert release.wait(5)
        return verify(self, *args, **kwargs)
    monkeypatch.setattr(ProjectSourceCapture, "verify_current", blocked)
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    wait(entered.is_set, application)
    try:
        QTest.keyClick(editor, Qt.Key.Key_Escape)
        assert editor.toPlainText() == original
    finally:
        release.set()
    wait(lambda: window._inline_retrieval.active is None, application)
    assert editor.toPlainText() == original and not editor.has_completion


def test_late_provider_error_preserves_author_edit(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    entered, release = Event(), Event()
    def fail(*a, **kw):
        entered.set()
        assert release.wait(5)
        raise RuntimeError("obsolete provider error")
    monkeypatch.setattr(window.provider, "generate_private", fail)
    window.request_completion(automatic=True)
    wait(entered.is_set, application)
    try:
        editor.insertPlainText(" author edit")
    finally:
        release.set()
    wait(lambda: window._inline_retrieval.active is None, application)
    assert editor.toPlainText().endswith("author edit")
    assert "obsolete provider error" not in window.statusBar().currentMessage()
    editor.undo()
    assert editor.toPlainText() == project.read_scene(scene.id)


def test_old_auto_worker_does_not_reset_new_manual_request_status(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    auto_entered, auto_release, manual_entered, manual_release = Event(), Event(), Event(), Event()
    def automatic(*a, **kw):
        auto_entered.set()
        assert auto_release.wait(5)
        return " obsolete"
    def manual(*a, **kw):
        manual_entered.set()
        assert manual_release.wait(5)
        return " current"
    monkeypatch.setattr(window.provider, "generate_private", automatic)
    monkeypatch.setattr(window.provider, "complete", manual)
    window.request_completion(automatic=True)
    wait(auto_entered.is_set, application)
    try:
        window.request_completion()
        wait(manual_entered.is_set, application)
        auto_release.set()
        wait(lambda: window._inline_retrieval.active is None, application)
        assert window.ai_status == "AI: Generating..."
        assert window._completion_worker is not None
    finally:
        auto_release.set()
        manual_release.set()
    wait(lambda: editor.has_completion, application)
    assert editor._ghost_text == " current"


def test_real_typing_debounces_automatic_request(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    window.settings.completion_debounce_ms = 100
    calls = []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (calls.append(prompt) or " beyond"))
    QTest.keyClicks(editor, " copper")
    wait(lambda: editor.has_completion, application)
    assert len(calls) == 1


def test_tab_verifies_disk_even_before_file_notification(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **kw: " beyond")
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    original = editor.toPlainText()
    (project.root / note.path).write_text("Changed before Tab")
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    wait(lambda: not editor.has_completion, application)
    assert editor.toPlainText() == original


@pytest.mark.parametrize("kind", ["note", "scene"])
def test_unsaved_other_source_edit_discards_response(scene_window, monkeypatch, application, kind):
    window, project, scene, note, editor = scene_window
    source = note if kind == "note" else project.add_scene("Other", content="The hidden door other scene")
    window._open_project_document(kind, source.id)
    wait(lambda: any(item.item_id == source.id for item in window._project_documents.values()), application)
    other = next(tab for tab, item in window._project_documents.items() if item.item_id == source.id)
    window.tabs.setCurrentWidget(editor)
    enable(window)
    entered, release = Event(), Event()
    def generate(*a, **kw):
        entered.set()
        assert release.wait(5)
        return " obsolete"
    monkeypatch.setattr(window.provider, "generate_private", generate)
    window.request_completion(automatic=True)
    wait(entered.is_set, application)
    try:
        other.insertPlainText("Author unsaved change")
    finally:
        release.set()
    wait(lambda: window._inline_retrieval.active is None, application)
    assert not editor.has_completion
    assert "Author unsaved change" in other.toPlainText()


@pytest.mark.skipif(os.environ.get("QT_QPA_PLATFORM") != "cocoa", reason="Direct native Cocoa walkthrough only")
def test_native_typing_inspection_tab_escape_undo_and_cursor_switch(scene_window, monkeypatch, application):
    window, project, scene, note, editor = scene_window
    enable(window)
    window.show()
    window.activateWindow()
    editor.setFocus()
    window.settings.completion_debounce_ms = 100
    calls = []
    monkeypatch.setattr(window.provider, "generate_private", lambda prompt, **kw: (calls.append(prompt) or " beyond"))
    typing_started = monotonic()
    QTest.keyClicks(editor, " copper")
    wait(lambda: editor.has_completion, application)
    typing_to_suggestion_ms = (monotonic() - typing_started) * 1000
    original = editor.toPlainText()
    original_exec, inspected, errors = RAGCompletionDialog.exec, [], []
    def inspect(dialog):
        def keys():
            try:
                assert calls[-1] == dialog.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0]
                inspected.append(True)
                QTest.keyClick(dialog, Qt.Key.Key_Escape)
            except BaseException as error:
                errors.append(error)
                dialog.reject()
        QTimer.singleShot(50, keys)
        return original_exec(dialog)
    monkeypatch.setattr(RAGCompletionDialog, "exec", inspect)
    window._inline_retrieval.inspect()
    assert inspected and not errors
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_Tab)
    wait(lambda: editor.toPlainText() != original, application)
    assert editor.toPlainText() == original + " beyond"
    editor.undo()
    assert editor.toPlainText() == original
    window.request_completion(automatic=True)
    wait(lambda: editor.has_completion, application)
    QTest.keyClick(editor, Qt.Key.Key_Escape)
    assert not editor.has_completion
    entered, release = Event(), Event()
    def blocked(*a, **kw):
        entered.set()
        assert release.wait(5)
        return " obsolete"
    monkeypatch.setattr(window.provider, "generate_private", blocked)
    window.request_completion(automatic=True)
    wait(entered.is_set, application)
    responsive = []
    probe_started = monotonic()
    QTimer.singleShot(0, lambda: responsive.append((monotonic() - probe_started) * 1000))
    try:
        QTest.keyClick(editor, Qt.Key.Key_Left)
        window.tabs.new_document()
        wait(lambda: bool(responsive), application)
        assert not editor.has_completion
    finally:
        release.set()
    wait(lambda: window._inline_retrieval.active is None, application)
    assert "obsolete" not in editor.toPlainText()
    print(f"Native GUI callback while fake provider blocked: {responsive[0]:.3f} ms; no live-model latency measured.")
    print(f"Native fake-provider typing-to-visible suggestion including 100 ms debounce: {typing_to_suggestion_ms:.3f} ms.")
