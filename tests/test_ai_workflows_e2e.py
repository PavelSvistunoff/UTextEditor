"""Offline Qt workflows using real workers and controlled fake AI responses."""

import json
from threading import Event
from unittest.mock import patch

import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QInputDialog, QLabel, QMessageBox

from app.ai.models import Suggestion
from app.project import Project, SceneCharacterAssociation
from app.settings.settings import AppSettings
from app.ui.main_window import MainWindow
from app.ui.character_dialog import CharacterDialog
from app.ui.project_brief_dialog import ProjectBriefDialog
from app.ui.settings_dialog import SettingsDialog


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.setattr(AppSettings, "_default_settings_path", staticmethod(lambda: tmp_path / "settings.yaml"))
    AppSettings(ui_language="en", automatic_spellcheck=False, ai_context_consent_host="http://localhost:11434").save(tmp_path / "settings.yaml")
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


def test_automatic_project_context_can_be_disabled_without_changing_manual_requests(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "context-project", "Novel")
    scene = project.add_scene("Scene", content="The draft")
    project.add_note("Secret", content="private reference note")
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    window.settings.automatic_project_context = False
    calls = []
    monkeypatch.setattr(window.provider, "complete", lambda context, language, **options: calls.append(context) or "")
    window.request_completion(automatic=True)
    wait_until(lambda: len(calls) == 1)
    assert calls[0] == "The draft"
    wait_until(lambda: window._completion_worker is None)
    window.request_completion()
    wait_until(lambda: len(calls) == 2)
    assert "private reference note" in calls[1]
    assert "The draft" in calls[1]
    wait_until(lambda: window._completion_worker is None)


def test_completion_note_selection_excludes_notes_and_discards_pending_result(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "note-selection", "Novel")
    scene = project.add_scene("Scene", content="Draft")
    project.add_note("Keep", content="included reference")
    project.add_note("Exclude", content="excluded reference")
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    started, release = Event(), Event()
    calls = []

    def complete(context, language, **options):
        calls.append(context)
        if len(calls) == 1:
            started.set()
            release.wait(3)
        return " continuation"

    monkeypatch.setattr(window.provider, "complete", complete)
    window.request_completion()
    wait_until(started.is_set)

    def select():
        dialog = QApplication.activeModalWidget()
        dialog.notes.item(1).setCheckState(Qt.CheckState.Unchecked)
        dialog.accept()

    QTimer.singleShot(0, select)
    window.select_completion_notes()
    release.set()
    wait_until(lambda: window._completion_worker is None)
    assert not editor.has_completion
    window.request_completion()
    wait_until(lambda: len(calls) == 2)
    assert "included reference" in calls[1]
    assert "excluded reference" not in calls[1]
    wait_until(lambda: window._completion_worker is None)


def test_reviewed_completion_sends_exact_displayed_context(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "review-context", "Novel")
    scene = project.add_scene("Scene", content="Draft")
    project.add_note("Reference", content="A detail")
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    shown, calls = [], []
    monkeypatch.setattr(window.provider, "complete", lambda text, language, **options: calls.append(text) or "")

    def accept(dialog):
        shown.append(dialog.context.toPlainText())
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.CompletionContextDialog.exec", accept)
    window.request_completion(review=True)
    wait_until(lambda: bool(calls))
    assert calls == shown
    assert "A detail" in calls[0] and "Draft" in calls[0]
    wait_until(lambda: window._completion_worker is None)


def test_reviewed_completion_does_not_send_if_closed_note_changes(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "changed-note", "Novel")
    scene = project.add_scene("Scene", content="Draft")
    note = project.add_note("Reference", content="Old reference")
    window._project_opened(project)
    window._open_project_document("scene", scene.id)
    wait_until(lambda: window.tabs.count() == 2)
    editor = window.tabs.current_editor()
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    calls, reviewed = [], []
    monkeypatch.setattr(window.provider, "complete", lambda *args, **kwargs: calls.append(args) or "")

    def review(dialog):
        project.write_note(note.id, "New reference", expected_content="Old reference")
        reviewed.append(True)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.CompletionContextDialog.exec", review)
    window.request_completion(review=True)
    wait_until(lambda: bool(reviewed))
    wait_until(lambda: window._completion_worker is None)
    assert calls == []
    assert "reference note changed" in window.statusBar().currentMessage()


@pytest.mark.parametrize("change", ["cancel", "edit"])
def test_reviewed_completion_does_not_send_after_cancel_or_edit(window, monkeypatch, change):
    editor = window.tabs.current_editor()
    editor.setPlainText("Draft")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    calls, reviewed = [], []
    monkeypatch.setattr(window.provider, "complete", lambda *args, **kwargs: calls.append(args) or "")

    def review(dialog):
        reviewed.append(True)
        if change == "edit":
            editor.insertPlainText(" changed")
            window._completion_timer.stop()
            return QDialog.DialogCode.Accepted
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr("app.ui.main_window.CompletionContextDialog.exec", review)
    window.request_completion(review=True)
    wait_until(lambda: bool(reviewed))
    wait_until(lambda: window._completion_worker is None)
    assert calls == []


def test_review_identifies_omitted_document_prefix(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Old paragraph\n\nCurrent paragraph")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    summaries = []

    def review(dialog):
        summaries.extend(label.text() for label in dialog.findChildren(QLabel))
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr("app.ui.main_window.CompletionContextDialog.exec", review)
    window.request_completion(review=True)
    wait_until(lambda: bool(summaries))
    assert any("Only part of the text" in text for text in summaries)
    wait_until(lambda: window._completion_worker is None)


@pytest.mark.parametrize("decision", ["select", "cancel", "stale"])
def test_auto_writer_review_applies_only_selected_and_rejects_stale(window, tmp_path, monkeypatch, decision):
    project = Project.create(tmp_path / "draft-review", "Novel")
    first = project.add_scene("First", content="First original")
    second = project.add_scene("Second", content="Second original")
    window._project_opened(project)
    window._open_project_document("scene", first.id)
    wait_until(lambda: window.tabs.count() == 2)
    editor = window.tabs.current_editor()
    monkeypatch.setattr("app.ui.main_window.AutoWriterDialog.exec", lambda _: QDialog.DialogCode.Accepted)
    monkeypatch.setattr("app.ui.main_window.AutoWriterDialog.values", lambda _: ("refine_all", ""))
    monkeypatch.setattr(QMessageBox, "question", lambda *_args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(window.provider, "generate_private", lambda *_args, **_kwargs: "Draft text")
    reviewed = []

    def review(dialog):
        dialog.list.setCurrentRow(1)
        assert dialog.preview.toPlainText() == "Draft text"
        reviewed.append(True)
        if decision == "cancel":
            return QDialog.DialogCode.Rejected
        if decision == "stale":
            editor.setPlainText("Newer edit")
            window._completion_timer.stop()
        else:
            dialog.list.item(1).setCheckState(Qt.CheckState.Unchecked)
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.AutoWriterReviewDialog.exec", review)
    window.start_auto_writer()
    wait_until(lambda: bool(reviewed) and not window._project_busy)
    assert project.read_scene(first.id) == ("Draft text" if decision == "select" else "First original")
    assert project.read_scene(second.id) == "Second original"


@pytest.mark.parametrize("operation", ["completion", "spellcheck"])
def test_first_context_request_requires_remote_disclosure_and_consent(window, monkeypatch, operation):
    editor = window.tabs.current_editor()
    editor.setPlainText("Draft text")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    window.provider.host = "https://remote.example:11434"
    window.settings.ollama_host = window.provider.host
    window.settings.ai_context_consent_host = ""
    calls = []
    monkeypatch.setattr(window.provider, "complete", lambda *args, **kwargs: calls.append("completion") or "")
    monkeypatch.setattr(window.provider, "check_spelling", lambda *args, **kwargs: calls.append("spellcheck") or [])
    request = window.request_completion if operation == "completion" else window.check_spelling

    request(automatic=True)
    disclosure = window._ai_disclosure
    assert disclosure is not None and window.provider.host in disclosure.message.text()
    assert not calls
    disclosure.buttons.button(QDialogButtonBox.StandardButton.No).click()
    request(automatic=True)
    assert window._ai_disclosure is None and not calls
    assert editor.toPlainText() == "Draft text"

    request()
    window._ai_disclosure.buttons.button(QDialogButtonBox.StandardButton.Yes).click()
    wait_until(lambda: calls == [operation])
    assert AppSettings.load().has_ai_context_consent("https://remote.example:11434")
    assert editor.toPlainText() == "Draft text"


def test_disclosure_does_not_authorize_changed_destination(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Draft")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    window.settings.ai_context_consent_host = ""
    calls = []
    monkeypatch.setattr(window.provider, "complete", lambda *args, **kwargs: calls.append(True) or "")
    window.request_completion()
    disclosure = window._ai_disclosure
    window.provider.host = "https://new.example"
    disclosure.buttons.button(QDialogButtonBox.StandardButton.Yes).click()
    QApplication.processEvents()
    assert not calls
    assert not window.settings.has_ai_context_consent("https://new.example")
    window.request_completion()
    assert "https://new.example" in window._ai_disclosure.message.text()
    window._ai_disclosure.reject()


def test_consent_save_failure_does_not_send_context(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("Draft")
    editor.moveCursor(QTextCursor.MoveOperation.End)
    window._completion_timer.stop()
    window.settings.ai_context_consent_host = ""
    calls = []
    messages = []
    window.statusBar().messageChanged.connect(messages.append)
    monkeypatch.setattr(window.provider, "complete", lambda *a, **k: calls.append(True) or "")
    def fail_save(*_args, **_kwargs):
        raise OSError("disk full")
    monkeypatch.setattr(window.settings, "save", fail_save)
    window.request_completion()
    window._ai_disclosure.buttons.button(QDialogButtonBox.StandardButton.Yes).click()
    QApplication.processEvents()
    assert not calls
    assert not window.settings.ai_context_consent_host
    assert any("disk full" in message for message in messages)


def test_disclosure_remains_accessible_from_modal_workflow(window):
    window.settings.ai_context_consent_host = ""
    parent = QDialog(window)
    parent.setModal(True)
    parent.show()
    QApplication.processEvents()
    try:
        assert not window._ensure_ai_context_consent()
        assert window._ai_disclosure.parentWidget() is parent
        assert not window._ai_disclosure.isModal()
        window._ai_disclosure.reject()
        assert window._ai_disclosure is None
    finally:
        parent.close()


def test_changing_ai_host_does_not_redirect_existing_provider(window, monkeypatch):
    old_provider = window.provider
    old_host = old_provider.host
    monkeypatch.setattr(window, "_check_connection", lambda: None)

    def accept_settings(_dialog):
        window.settings.ollama_host = "https://new.example:11434"
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(SettingsDialog, "exec", accept_settings)
    window.show_settings()
    assert old_provider.host == old_host
    assert window.provider is not old_provider
    assert window.provider.host == "https://new.example:11434"
    assert window.completion_service.provider is window.provider
    assert window.spellcheck_service.provider is window.provider
    assert not window.settings.has_ai_context_consent(window.provider.host)


def test_all_explicit_context_workflows_require_disclosure(window, tmp_path, monkeypatch):
    project = Project.create(tmp_path / "consent-project", "Novel")
    project.add_scene("Opening", content="private scene")
    character = project.add_character("Mara")
    window._project_opened(project)
    window.settings.ai_context_consent_host = ""
    brief_dialog = ProjectBriefDialog(window)
    window._project_setup_brief_dialog = brief_dialog
    character_dialog = CharacterDialog(character, parent=window)
    calls = []
    monkeypatch.setattr(window.provider, "generate", lambda *a, **k: calls.append("generate") or "")
    monkeypatch.setattr(window.provider, "generate_private", lambda *a, **k: calls.append("private") or "")
    actions = [
        window.setup_project_with_ai,
        window.start_auto_writer,
        window.translate_project_to_ukrainian,
        lambda: window._start_project_outline_request(project, "brief"),
        lambda: window._suggest_project_brief(project, brief_dialog, "brief"),
        lambda: window._start_project_autopilot(project, brief_dialog, "brief"),
        lambda: window._suggest_scene_development(character_dialog, project),
        lambda: window._suggest_character_profile(character_dialog, project),
        window.generate_from_prompt,
        lambda: window._start_project_analysis("summary"),
    ]
    for action in actions:
        action()
        assert window._ai_disclosure is not None
        window._ai_disclosure.reject()
    QApplication.processEvents()
    assert not calls
    assert project.read_scene(next(project.iter_scenes()).id) == "private scene"
    brief_dialog.close()
    character_dialog.close()


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


@pytest.mark.parametrize("choice", ["apply", "select", "cancel", "stale", "overlap"])
def test_batch_spelling_review_preserves_selection_and_undo(window, monkeypatch, choice):
    editor = window.tabs.current_editor()
    editor.setPlainText("😀 teh kat")
    window._completion_timer.stop()
    source, revision = editor.toPlainText(), editor.revision
    first = Suggestion(2, 5, "the", "spelling", "Typo", "teh", revision, source)
    second = Suggestion(6, 9, "cat", "spelling", "Typo", "kat", revision, source)
    editor.set_spell_suggestions([first, second])

    def review(dialog):
        if choice == "cancel":
            return QDialog.DialogCode.Rejected
        if choice == "stale":
            editor.insertPlainText("!")
            window._completion_timer.stop()
        elif choice == "select":
            dialog.findings.item(1).setCheckState(Qt.CheckState.Unchecked)
        elif choice == "overlap":
            dialog.suggestions = (first, Suggestion(2, 5, "that", "grammar", "", "teh", revision, source))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr("app.ui.main_window.SpellcheckReviewDialog.exec", review)
    window.review_spellcheck()
    if choice in {"apply", "select"}:
        assert editor.toPlainText() == ("😀 the cat" if choice == "apply" else "😀 the kat")
        editor.undo()
        assert editor.toPlainText() == source
    elif choice in {"cancel", "overlap"}:
        assert editor.toPlainText() == source
    else:
        assert "the" not in editor.toPlainText()
        assert "check spelling again" in window.statusBar().currentMessage()


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


@pytest.mark.parametrize("first_fails", [False, True])
def test_slow_spellcheck_coalesces_to_latest_pending_document(window, monkeypatch, first_fails):
    editor = window.tabs.current_editor()
    editor.setPlainText("first")
    window._completion_timer.stop()
    started, release = Event(), Event()
    calls = []

    def check(text, _language):
        calls.append(text)
        if len(calls) == 1:
            started.set()
            assert release.wait(3)
            if first_fails:
                raise RuntimeError("first call failed")
        return []

    monkeypatch.setattr(window.provider, "check_spelling", check)
    try:
        window.check_spelling()
        wait_until(started.is_set)
        for text in ("second", "third", "last"):
            editor.setPlainText(text)
            window.check_spelling()
        assert calls == ["first"]
        release.set()
        wait_until(lambda: len(calls) == 2 and window._spellcheck_worker is None)
        assert calls == ["first", "last"]
        assert editor.toPlainText() == "last"
    finally:
        release.set()


def test_pending_spellcheck_is_discarded_when_document_changes(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("first")
    window._completion_timer.stop()
    started, release = Event(), Event()
    calls = []

    def check(text, _language):
        calls.append(text)
        started.set()
        assert release.wait(3)
        return []

    monkeypatch.setattr(window.provider, "check_spelling", check)
    try:
        window.check_spelling()
        wait_until(started.is_set)
        editor.setPlainText("pending")
        window.check_spelling()
        editor.setPlainText("changed again")
        release.set()
        wait_until(lambda: window._spellcheck_worker is None)
        assert calls == ["first"]
        assert not editor.spell_suggestions
    finally:
        release.set()


def test_cancelling_spellcheck_clears_pending_request_and_keeps_ui_responsive(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("first")
    window._completion_timer.stop()
    started, release = Event(), Event()
    calls = []
    timer_ran = []

    def check(text, _language):
        calls.append(text)
        started.set()
        assert release.wait(3)
        return []

    monkeypatch.setattr(window.provider, "check_spelling", check)
    try:
        window.check_spelling()
        wait_until(started.is_set)
        editor.setPlainText("pending")
        window.check_spelling()
        QTimer.singleShot(0, lambda: timer_ran.append(True))
        wait_until(lambda: bool(timer_ran))
        window._cancel_activity_spellcheck(window._spellcheck_worker)
        release.set()
        wait_until(lambda: window._spellcheck_worker is None)
        assert calls == ["first"]
        assert window._spellcheck_pending is None
    finally:
        release.set()


def test_shutdown_cancels_pending_spellcheck_without_starting_it(window, monkeypatch):
    editor = window.tabs.current_editor()
    editor.setPlainText("first")
    window._completion_timer.stop()
    started, release = Event(), Event()
    calls = []

    def check(text, _language):
        calls.append(text)
        started.set()
        assert release.wait(3)
        return []

    monkeypatch.setattr(window.provider, "check_spelling", check)
    try:
        window.check_spelling()
        wait_until(started.is_set)
        editor.setPlainText("pending")
        window.check_spelling()
        window._cancel_pending_ai()
        release.set()
        wait_until(lambda: window._spellcheck_worker is None)
        assert calls == ["first"]
        assert window._spellcheck_pending is None
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
