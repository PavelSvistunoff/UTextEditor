"""Exact GUI review, stale results and explicit translation/spelling application."""

import json
import os
from threading import Event, get_ident

import pytest
from PySide6.QtWidgets import QDialog, QMessageBox

from app.project.translation_context import GlossaryTerm
from app.ui.project_translation_review_dialog import ProjectTranslationReviewDialog
from app.ui.rag_completion import RAGCompletionDialog
from app.ui.translation_glossary_dialog import TranslationGlossaryDialog
from tests.test_inline_retrieval_ui import wait
from tests.test_rag_completion_ui import application, scene_window


@pytest.fixture
def ready(scene_window, monkeypatch):
    window, project, scene, note, editor = scene_window
    window.settings.completion_enabled = False
    window.settings.spelling_project_dictionary = True
    window._translation_retrieval_action.setChecked(True)
    monkeypatch.setattr(window, "_ensure_ai_context_consent", lambda **kw: True)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)
    monkeypatch.setattr(TranslationGlossaryDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    return window, project, scene, note, editor


@pytest.mark.parametrize("mode", ["translation", "spelling"])
def test_context_review_on_gui_exact_prompt_offthread_final_application_explicit(ready, monkeypatch, application, mode):
    window, project, scene, note, editor = ready
    original = editor.toPlainText()
    gui, reviewed, calls, finals = get_ident(), [], [], []
    def review(dialog):
        assert get_ident() == gui
        reviewed.append(dialog.context.toPlainText().split("\n\n--- SOURCE MANIFEST")[0])
        return QDialog.DialogCode.Accepted
    def generate(prompt, **options):
        assert get_ident() != gui
        calls.append((prompt, options))
        return '{"translation":"Переклад"}' if mode == "translation" else '[{"start":4,"end":10,"replacement":"secret","original_text":"hidden"}]'
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", generate)
    monkeypatch.setattr(ProjectTranslationReviewDialog, "exec", lambda _: (finals.append(True) or QDialog.DialogCode.Rejected))
    if mode == "translation":
        window.translate_project_to_ukrainian()
        wait(lambda: bool(finals) and not window._project_busy, application)
    else:
        window.check_spelling()
        wait(lambda: bool(editor.spell_suggestions), application)
        assert editor.spell_suggestions[0].start == 4
        editor.apply_spell_suggestions(editor.spell_suggestions)
        assert editor.toPlainText() != original
        editor.undo()
    assert calls and [call[0] for call in calls] == reviewed
    assert all(call[1]["require_full_context"] for call in calls)
    assert editor.toPlainText() == original == project.read_scene(scene.id)


@pytest.mark.parametrize("mode", ["translation", "spelling"])
@pytest.mark.parametrize("change", ["buffer", "settings", "project", "reject", "disk"])
def test_source_review_change_or_rejection_prevents_send(ready, monkeypatch, application, mode, change):
    window, project, scene, note, editor = ready
    reviewed, calls = [], []
    def review(dialog):
        reviewed.append(True)
        if change == "buffer":
            editor.insertPlainText("Changed")
        elif change == "settings":
            window._settings_generation += 1
        elif change == "project":
            window._project_generation += 1
        elif change == "disk":
            (project.root / note.path).write_text("Changed", encoding="utf-8")
        return QDialog.DialogCode.Rejected if change == "reject" else QDialog.DialogCode.Accepted
    monkeypatch.setattr(RAGCompletionDialog, "exec", review)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: calls.append(True))
    if mode == "translation":
        window.translate_project_to_ukrainian()
        wait(lambda: bool(reviewed) and not window._project_busy, application)
    else:
        window.check_spelling()
        wait(lambda: bool(reviewed) and window._spellcheck_worker is None, application)
    assert not calls and not editor.spell_suggestions


@pytest.mark.parametrize("automatic,standalone,enabled", [(True, False, True), (False, True, True), (False, False, False)])
def test_automatic_standalone_disabled_checks_remain_target_only(ready, monkeypatch, application, automatic, standalone, enabled):
    window, project, scene, note, editor = ready
    window.settings.spelling_project_dictionary = enabled
    if standalone:
        editor = window.tabs.new_document()
        editor.setPlainText("Standalone")
    calls = []
    monkeypatch.setattr(window.provider, "check_spelling", lambda text, language: (calls.append(text) or []))
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: pytest.fail("Target-only check must not open source review"))
    window.check_spelling(automatic=automatic)
    wait(lambda: bool(calls) and window._spellcheck_worker is None, application)
    assert calls == [editor.toPlainText()]


def test_translation_accepts_all_items_together_and_final_disk_change_refuses(ready, monkeypatch, application):
    window, project, scene, note, editor = ready
    original = project.manifest_path.read_bytes()
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: '{"translation":"Переклад"}')
    def review(dialog):
        (project.root / note.path).write_text("Changed after final review", encoding="utf-8")
        return QDialog.DialogCode.Accepted
    monkeypatch.setattr(ProjectTranslationReviewDialog, "exec", review)
    window.translate_project_to_ukrainian()
    wait(lambda: not window._project_busy, application)
    assert project.manifest_path.read_bytes() == original
    assert project.read_scene(scene.id) == editor.toPlainText()


def test_glossary_editor_preserves_sources_and_exposes_ambiguity(application):
    dialog = TranslationGlossaryDialog((GlossaryTerm("Mara", "Mara", ("a", "b")),))
    assert dialog.table.item(0, 2).text() == "Ambiguous name"
    dialog.table.item(0, 1).setText("")
    dialog._approve()
    assert dialog.result() != QDialog.DialogCode.Accepted and dialog.error.text()
    dialog.table.item(0, 1).setText("Мара")
    dialog._approve()
    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.glossary() == (GlossaryTerm("Mara", "Мара", ("a", "b")),)


@pytest.mark.parametrize("mode", ["translation", "spelling"])
def test_explicit_window_required_before_dispatch(ready, monkeypatch, application, mode):
    window = ready[0]
    window.settings.ollama_context_length = 0
    calls = []
    monkeypatch.setattr(window.provider, "generate_private", lambda *args, **kw: calls.append(True))
    if mode == "translation":
        window.translate_project_to_ukrainian()
    else:
        window.check_spelling()
    assert not calls and window._spellcheck_worker is None and not window._project_busy


@pytest.mark.parametrize("mode", ["translation", "spelling"])
@pytest.mark.parametrize("failure", [False, True])
def test_late_success_or_failure_after_settings_change_cannot_apply(ready, monkeypatch, application, mode, failure):
    window, project, scene, note, editor = ready
    started, release = Event(), Event()
    final = []
    original = project.manifest_path.read_bytes()
    monkeypatch.setattr(RAGCompletionDialog, "exec", lambda _: QDialog.DialogCode.Accepted)
    monkeypatch.setattr(ProjectTranslationReviewDialog, "exec", lambda _: (final.append(True) or QDialog.DialogCode.Accepted))
    def generate(*args, **kw):
        started.set()
        release.wait(5)
        if failure:
            raise RuntimeError("Late provider error")
        return '{"translation":"Переклад"}' if mode == "translation" else '[{"start":4,"end":10,"replacement":"secret"}]'
    monkeypatch.setattr(window.provider, "generate_private", generate)
    try:
        if mode == "translation":
            window.translate_project_to_ukrainian()
        else:
            window.check_spelling()
        wait(started.is_set, application)
        window._settings_generation += 1
    finally:
        release.set()
    wait(lambda: window._spellcheck_worker is None and not window._project_busy, application)
    assert not final and not editor.spell_suggestions
    assert project.manifest_path.read_bytes() == original


def test_dictionary_setting_roundtrip_reset_and_cancel(application, tmp_path):
    from app.settings.settings import AppSettings
    from app.ui.settings_dialog import SettingsDialog
    settings = AppSettings()
    assert not settings.spelling_project_dictionary
    dialog = SettingsDialog(settings)
    dialog.spelling_project_dictionary.setChecked(True)
    dialog.reject()
    assert not settings.spelling_project_dictionary
    dialog = SettingsDialog(settings)
    dialog.spelling_project_dictionary.setChecked(True)
    dialog.accept()
    path = tmp_path / "settings.yaml"
    settings.save(path)
    assert AppSettings.load(path).spelling_project_dictionary
    invalid = AppSettings(spelling_project_dictionary="false").validated()
    assert invalid.spelling_project_dictionary is False
